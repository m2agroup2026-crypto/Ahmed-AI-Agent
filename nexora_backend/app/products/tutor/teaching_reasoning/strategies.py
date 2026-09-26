STRATEGIES = {
    "concept_gap": {
        "method": "simplify_concept",
        "description": "Explain the concept using simpler steps and examples.",
    },
    "practice_gap": {
        "method": "guided_practice",
        "description": "Provide a guided example followed by practice.",
    },
    "mastered": {
        "method": "advanced_challenge",
        "description": "Increase difficulty with deeper application.",
    },
}


def get_strategy(issue_type: str):

    return STRATEGIES.get(
        issue_type,
        {
            "method": "general_support",
            "description": "Provide supportive explanation.",
        },
    )
