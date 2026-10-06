from app.ai.intents.registry import INTENTS


KEYWORDS = {
    "VIEW_USERS": [
        "users",
        "user",
        "مستخدمين",
        "المستخدمين",
        "المستخدم",
        "المستخدمون"
    ],

    "VIEW_DASHBOARD": [
        "dashboard",
        "لوحة",
        "الداشبورد",
        "الرئيسية"
    ],

    "CHECK_SYSTEM_STATUS": [
        "status",
        "health",
        "حالة",
        "النظام",
        "السيرفر"
    ]
}


def normalize_text(text: str) -> str:

    text = text.lower().strip()

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ى": "ي"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return " ".join(text.split())


def build_result(
    intent: str,
    confidence: float,
    matched_keyword: str | None,
    reason: str
):

    return {
        "intent": intent,
        "definition": INTENTS[intent],
        "confidence": confidence,
        "matched_keyword": matched_keyword,
        "reason": reason
    }


def detect_intent(text: str):

    text = normalize_text(text)

    for intent, keywords in KEYWORDS.items():

        for keyword in keywords:

            normalized_keyword = normalize_text(keyword)

            if normalized_keyword in text:

                return build_result(
                    intent,
                    1.0,
                    keyword,
                    "keyword_match"
                )

    return build_result(
        "GENERAL_QUERY",
        0.0,
        None,
        "no_match"
    )
