INTENTS = {
    "VIEW_USERS": {
        "description": "View platform users",
        "permission": "users.manage"
    },

    "VIEW_DASHBOARD": {
        "description": "View executive dashboard",
        "permission": "dashboard.manage"
    },

    "CHECK_SYSTEM_STATUS": {
        "description": "Check platform health",
        "permission": "dashboard.manage"
    },

    "GENERAL_QUERY": {
        "description": "General AI conversation",
        "permission": None
    }
}


def get_intent(intent_name: str):

    return INTENTS.get(intent_name)
