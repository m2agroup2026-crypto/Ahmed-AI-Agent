from app.products.tutor.diagnosis.engine import DiagnosisEngine
from app.products.tutor.diagnosis.rules import classify_accuracy


def test_diagnosis_engine():

    result = DiagnosisEngine().analyze(
        [
            {
                "skill": "algebra_basics",
                "correct": True,
            },
            {
                "skill": "equations",
                "correct": False,
            },
        ]
    )

    assert "algebra_basics" in result.strengths
    assert "equations" in result.weaknesses
    assert "equations" in result.recommended_topics


def test_accuracy_classification():

    assert classify_accuracy(2, 10) == "basic"
    assert classify_accuracy(6, 10) == "intermediate"
    assert classify_accuracy(9, 10) == "advanced"
