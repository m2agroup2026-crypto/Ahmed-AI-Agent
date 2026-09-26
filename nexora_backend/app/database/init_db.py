from app.database.base import Base
from app.database.connection import engine

from app.models import (
    User,
    Role,
    Permission,
    RolePermission,
)

# Register billing models with SQLAlchemy metadata
from app.billing.models import (
    Plan,
    Subscription,
    CreditTransaction,
    UsageRecord,
    Wallet,
)

# Register Tutor product models with SQLAlchemy metadata.
from app.products.tutor import (
    AssessmentAttempt,
    CurriculumContentChunk,
    CurriculumLesson,
    CurriculumQuestion,
    CurriculumSkill,
    CurriculumSource,
    CurriculumVersion,
    LearnerProfile,
    LearningMessage,
    LearningSession,
)


def create_tables():
    Base.metadata.create_all(
        bind=engine
    )


if __name__ == "__main__":
    create_tables()
