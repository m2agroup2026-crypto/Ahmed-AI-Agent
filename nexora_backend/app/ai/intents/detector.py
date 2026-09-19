from app.ai.intents.registry import INTENTS


KEYWORDS = {
    "VIEW_USERS": [
        "users",
        "user",
        "مستخدمين",
        "المستخدمين",
        "المستخدم"
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


def detect_intent(text: str):

    text = text.lower()

    for intent, keywords in KEYWORDS.items():

        for keyword in keywords:

            if keyword.lower() in text:
                return {
                    "intent": intent,
                    "definition": INTENTS[intent]
                }

    return {
        "intent": "GENERAL_QUERY",
        "definition": INTENTS["GENERAL_QUERY"]
    }
