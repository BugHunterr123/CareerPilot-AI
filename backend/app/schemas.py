"""Pydantic models that validate what the frontend sends us."""
from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator

ROLE_KEY = r"^[a-z_]{3,60}$"


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=2, max_length=120)

    @field_validator("password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if v.isdigit() or v.isalpha():
            raise ValueError("Use at least one letter and one number.")
        return v


def _password_rule(v: str) -> str:
    if v.isdigit() or v.isalpha():
        raise ValueError("Use at least one letter and one number.")
    return v


class PasswordChangeIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        return _password_rule(v)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class ProfileIn(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=120)
    college: str | None = Field(None, max_length=200)
    degree: str | None = Field(None, max_length=80)
    branch: str | None = Field(None, max_length=120)
    graduation_year: int | None = Field(None, ge=2000, le=2040)
    cgpa: str | None = Field(None, max_length=10)
    interests: list[str] | None = None
    preferred_roles: list[str] | None = None
    preferred_locations: list[str] | None = None
    job_type: str | None = Field(None, pattern=r"^(internship|full-time|both|apprenticeship)$")
    weekly_hours: int | None = Field(None, ge=1, le=60)
    target_date: date | None = None
    certifications: list[str] | None = None
    achievements: list[str] | None = None


class LinkIn(BaseModel):
    kind: str = Field(pattern=r"^(github|linkedin|leetcode|portfolio|other)$")
    url: str = Field(min_length=4, max_length=500)
    consent: bool = False
    manual_details: str = Field("", max_length=4000)


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field("", max_length=3000)
    technologies: list[str] = Field(default_factory=list)


class EducationIn(BaseModel):
    degree: str = ""
    institution: str = ""
    year: str = ""
    score: str = ""


class ResumeReviewIn(BaseModel):
    skills: list[str] = Field(default_factory=list, max_length=150)
    projects: list[ProjectIn] = Field(default_factory=list, max_length=30)
    education: list[EducationIn] = Field(default_factory=list, max_length=10)
    certifications: list[str] = Field(default_factory=list, max_length=50)
    achievements: list[str] = Field(default_factory=list, max_length=50)


class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class SelectRoleIn(BaseModel):
    role_key: str = Field(pattern=ROLE_KEY)


class SelectCompanyIn(BaseModel):
    role_key: str | None = Field(None, pattern=ROLE_KEY)


class GapIn(BaseModel):
    role_key: str = Field(pattern=ROLE_KEY)
    company_id: int | None = None
    job_description: str = Field("", max_length=8000)


class RoadmapIn(BaseModel):
    role_key: str | None = Field(None, pattern=ROLE_KEY)
    company_id: int | None = None
    use_target_company: bool = True
    weekly_hours: int | None = Field(None, ge=1, le=60)
    target_date: date | None = None


class TaskPatch(BaseModel):
    status: str | None = Field(None, pattern=r"^(todo|done|skipped)$")
    due_date: date | None = None


class AttemptIn(BaseModel):
    response: str = Field("", max_length=8000)
    self_correct: bool | None = None  # for coding / short answers the student marks themselves


class InterviewIn(BaseModel):
    role_key: str | None = Field(None, pattern=ROLE_KEY)
    company_id: int | None = None
    itype: str = Field("mixed", pattern=r"^(technical|coding|project|hr|behavioural|mixed)$")
    difficulty: str = Field("medium", pattern=r"^(easy|medium|hard|mixed)$")
    duration_min: int = Field(15, ge=5, le=45)


class AnswerIn(BaseModel):
    answer: str = Field(min_length=1, max_length=6000)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class CodeRunIn(BaseModel):
    code: str = Field(min_length=1, max_length=20000)
    stdin: str | None = Field(None, max_length=20000)  # custom input; None = run the visible test cases


class PracticeTestIn(BaseModel):
    kind: str = Field("coding", pattern=r"^(coding|mcq)$")
    company_id: int | None = None
    difficulty: str = Field("mixed", pattern=r"^(easy|medium|hard|mixed)$")
    count: int = Field(3, ge=1, le=30)
    minutes: int | None = Field(None, ge=5, le=180)


class TestAnswerIn(BaseModel):
    question_id: int
    code: str | None = Field(None, max_length=20000)
    choice: str | None = Field(None, max_length=2000)


class ApplicationIn(BaseModel):
    company_name: str = Field(min_length=1, max_length=120)
    role: str = Field("", max_length=120)
    status: str = Field("applied", pattern=r"^(planning|applied|test|interview|offer|rejected|withdrawn)$")
    applied_on: date | None = None
    interview_date: date | None = None
    outcome: str = Field("", max_length=60)
    notes: str = Field("", max_length=2000)


class DeleteAccountIn(BaseModel):
    password: str = Field(min_length=1, max_length=72)
