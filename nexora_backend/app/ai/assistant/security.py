from app.ai.intents.registry import get_intent
from app.services.permission_service import has_permission


# Explicitly authenticated-only intents that intentionally require
# no RBAC permission. Everything else defaults to DENY.
AUTHENTICATED_ONLY_INTENTS = {
    "GENERAL_QUERY",
}


def authorize_ai_action(
    db,
    user_id: int,
    intent_name: str,
):

    intent = get_intent(intent_name)

    if not intent:
        return {
            "allowed": False,
            "permission": None,
            "reason": "Unknown intent",
        }

    permission = intent.get("permission")

    if permission:
        allowed = has_permission(
            db,
            user_id,
            permission,
        )

        return {
            "allowed": allowed,
            "permission": permission,
            "reason": (
                "Permission validated"
                if allowed
                else "Permission denied"
            ),
        }

    if intent_name in AUTHENTICATED_ONLY_INTENTS:
        return {
            "allowed": True,
            "permission": None,
            "reason": "Authenticated intent allowed",
        }

    return {
        "allowed": False,
        "permission": None,
        "reason": "No explicit authorization policy",
    }
