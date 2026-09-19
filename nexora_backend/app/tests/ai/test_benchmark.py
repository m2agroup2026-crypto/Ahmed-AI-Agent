import time

from app.database.connection import SessionLocal
from app.ai.core.orchestrator import NexoraOrchestrator


def test_ai_benchmark_report():

    db = SessionLocal()

    runs = 50

    start = time.perf_counter()

    for _ in range(runs):
        NexoraOrchestrator().run(
            db,
            1,
            "اعرض المستخدمين"
        )

    end = time.perf_counter()

    total = end - start
    average = total / runs

    print("\n===== NEXORA BENCHMARK =====")
    print(f"Requests: {runs}")
    print(f"Total: {total:.4f}s")
    print(f"Average: {average:.6f}s")
    print("============================")

    assert average < 1

    db.close()
