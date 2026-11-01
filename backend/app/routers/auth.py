"""Sign up, log in, log out, the current user and password change."""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import StudentProfile, User
from app.models.common import utcnow
from app.ratelimit import limiter
from app.schemas import LoginIn, PasswordChangeIn, RegisterIn
from app.security import (get_optional_user, clear_session_cookie, create_token, get_current_user, hash_password,
                          set_session_cookie, verify_password)
from app.serializers import user_out

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=201, dependencies=[Depends(limiter("auth"))])
def register(body: RegisterIn, response: Response, db: Session = Depends(get_db)):
    """Create a new account. Every new account starts with an empty workspace."""
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists. Try logging in.")
    user = User(email=email, password_hash=hash_password(body.password), full_name=body.full_name.strip(),
                last_login_at=utcnow())
    user.profile = StudentProfile()
    db.add(user)
    db.commit()
    token = create_token(user)
    set_session_cookie(response, token)
    return {"token": token, "user": user_out(user)}


@router.post("/login", dependencies=[Depends(limiter("auth"))])
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    user.last_login_at = utcnow()
    db.commit()
    token = create_token(user)
    set_session_cookie(response, token)
    return {"token": token, "user": user_out(user)}


@router.post("/logout", status_code=204)
def logout(response: Response):
    """Clears the session cookie. Works even if the session already expired."""
    clear_session_cookie(response)
    response.status_code = 204
    return response


@router.get("/session")
def session(user: User | None = Depends(get_optional_user)):
    """Always 200: lets the pages check the login state without a 401 in the browser console."""
    return {"authenticated": user is not None, "user": user_out(user) if user else None}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_out(user)


@router.post("/password", dependencies=[Depends(limiter("auth"))])
def change_password(body: PasswordChangeIn, response: Response, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """Change password. All other sessions are signed out; this one gets a fresh cookie."""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "Your current password is not correct.")
    if body.current_password == body.new_password:
        raise HTTPException(400, "The new password must be different from the current one.")
    user.password_hash = hash_password(body.new_password)
    user.token_version = (user.token_version or 0) + 1
    db.commit()
    set_session_cookie(response, create_token(user))
    return {"ok": True, "message": "Password changed. Other devices have been signed out."}
