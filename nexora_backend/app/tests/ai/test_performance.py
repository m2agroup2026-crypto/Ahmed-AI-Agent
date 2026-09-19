import time

from app.database.connection import SessionLocal
from app.ai.core.orchestrator import NexoraOrchestrator


def test_ai_execution_speed():

    db = SessionLocal()

    start = time.perf_counter()

    NexoraOrchestrator().run(
        db,
        1,
        "اعرض المستخدمين"
    )

    end = time.perf_counter()

    execution_time = end - start

    print(
        f"NEXORA execution time: {execution_time:.4f}s"
    )

    assert execution_time < 1

    db.close()
