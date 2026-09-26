DIAGNOSIS_LEVELS = {
    "basic": "needs_foundation",
    "intermediate": "developing",
    "advanced": "ready_for_challenge",
}


def classify_accuracy(correct: int, total: int) -> str:

    if total == 0:
        return "unknown"

    ratio = correct / total

    if ratio < 0.5:
        return "basic"

    if ratio < 0.8:
        return "intermediate"

    return "advanced"
