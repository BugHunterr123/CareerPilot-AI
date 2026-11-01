"""
Password hashing (bcrypt), login tokens (JWT) and the session cookie.

Flow: /api/auth/login checks the password -> sets an httpOnly cookie holding a
signed token (JavaScript cannot read it, so XSS cannot steal it) -> the browser
sends the cookie with every request -> get_current_user() verifies it.

API clients (and the tests) may also send "Authorization: Bearer <token>".
Changing the password bumps user.token_version, which invalidates old tokens.

CSRF: the cookie is SameSite=Lax, and every state-changing request made with the
cookie must carry the header "X-Requested-With: careerpilot" (a custom header a
foreign site cannot add without a CORS preflight we do not allow).
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User

ALGORITHM = "HS256"
CSRF_HEADER = "x-requested-with"
CSRF_VALUE = "careerpilot"
_bearer = HTTPBearer(auto_error=False)
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def hash_password(plain: str) -> str:
    # bcrypt only reads the first 72 bytes; we cap length in the schema too.
    return bcrypt.hashpw(plain.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode()[:72], hashed.encode())
    except ValueError:
        return False


def create_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": str(user.id), "tv": user.token_version or 0, "exp": exp},
                      settings.secret_key, algorithm=ALGORITHM)


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(settings.cookie_name, token, max_age=settings.jwt_expire_minutes * 60, httponly=True,
                        secure=settings.secure_cookies, samesite=settings.cookie_samesite, path="/")


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(settings.cookie_name, path="/", httponly=True, secure=settings.secure_cookies,
                           samesite=settings.cookie_samesite)


def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Dependency used by every protected endpoint. 401 if the session is missing/invalid."""
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Please log in again.")
    token = creds.credentials if creds else None
    via_cookie = False
    if not token:
        token = request.cookies.get(settings.cookie_name)
        via_cookie = True
    if not token:
        raise unauthorized
    if via_cookie and request.method not in SAFE_METHODS and request.headers.get(CSRF_HEADER) != CSRF_VALUE:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Request blocked (missing CSRF header). Please reload the page.")
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
        token_version = int(payload.get("tv", 0))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized
    user = db.get(User, user_id)
    if user is None or (user.token_version or 0) != token_version:
        raise unauthorized
    return user


def get_optional_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user, but returns None instead of raising (for "am I logged in?" checks)."""
    try:
        return get_current_user(request, creds, db)
    except HTTPException:
        return None
