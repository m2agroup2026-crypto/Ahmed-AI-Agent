import time

from app.database.connection import SessionLocal
from app.ai.core.orchestrator import NexoraOrchestrator


def test_ai_multiple_requests_speed():

    db = SessionLocal()

    start = time.perf_counter()

    for _ in range(10):
        NexoraOrchestrator().run(
            db,
            1,
            "اعرض المستخدمين"
        )

    end = time.perf_counter()

    total_time = end - start

    average_time = total_time / 10

    print(
        f"NEXORA 10 requests total: {total_time:.4f}s"
    )

    print(
        f"NEXORA average request: {average_time:.4f}s"
    )

    assert average_time < 1

    db.close()
