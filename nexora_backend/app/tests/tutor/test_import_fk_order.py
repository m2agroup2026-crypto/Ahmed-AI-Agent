from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models import User, Role, Permission, RolePermission
from app.products.tutor.importer import import_curriculum_bundle
from app.products.tutor.models import (
    CurriculumSource, CurriculumVersion,
    CurriculumSkill, CurriculumLesson, CurriculumQuestion,
)
from app.tests.tutor.test_tutor_content import _payload


def test_import_respects_real_foreign_keys():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            assert db.connection().exec_driver_sql(
                "PRAGMA foreign_keys"
            ).scalar() == 1

            payload = _payload()
            result = import_curriculum_bundle(db, payload)

            assert result.published_questions == 1
            assert db.query(CurriculumSource).count() == 1
            assert db.query(CurriculumVersion).count() == 1
            assert db.query(CurriculumSkill).count() == 1
            assert db.query(CurriculumLesson).count() == 1
            assert db.query(CurriculumQuestion).count() == 1

            import_curriculum_bundle(db, payload)
            assert db.query(CurriculumQuestion).count() == 1
    finally:
        engine.dispose()
