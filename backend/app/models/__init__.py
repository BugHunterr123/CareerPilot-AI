"""
All database tables. Importing this package registers every model on Base.metadata
(Alembic and the tests rely on that).
"""
from app.models.user import User, StudentProfile, ProfileLink  # noqa: F401
from app.models.resume import Resume, Skill, SkillEvidence, Project  # noqa: F401
from app.models.company import Company, JobRole, HiringStage, SourceRef, LearningResource  # noqa: F401
from app.models.prep import (  # noqa: F401
    CareerRecommendation, SkillGapReport, Roadmap, RoadmapTask,
    PracticeQuestion, QuestionAttempt, SavedQuestion, PracticeTest,
)
from app.models.activity import (  # noqa: F401
    MockInterview, InterviewResponse, FeedbackReport,
    ProgressEvent, JobApplication, ChatMessage,
)
