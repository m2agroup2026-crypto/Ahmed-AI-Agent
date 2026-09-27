RESPONSE_TEMPLATES = {

    "supportive": {
        "opening": "No worries, let's solve this together.",
        "style": "patient",
    },

    "encouraging": {
        "opening": "Good effort, let's improve your understanding step by step.",
        "style": "motivational",
    },

    "motivating": {
        "opening": "Excellent progress, you are ready for a bigger challenge.",
        "style": "challenging",
    },

    "positive": {
        "opening": "Let's keep building your knowledge.",
        "style": "adaptive",
    },
}


def get_template(
    emotional_tone: str,
):

    return RESPONSE_TEMPLATES.get(
        emotional_tone,
        RESPONSE_TEMPLATES["positive"],
    )
