from app.ai.intents.registry import get_intent
from app.services.permission_service import has_permission


def authorize_ai_action(
    db,
    user_id: int,
    intent_name: str
):

    intent = get_intent(intent_name)

    if not intent:
        return {
            "allowed": False,
            "reason": "Unknown intent"
        }


    permission = intent.get(
        "permission"
    )


    if not permission:
        return {
            "allowed": True,
            "permission": None
        }


    allowed = has_permission(
        db,
        user_id,
        permission
    )


    return {
        "allowed": allowed,
        "permission": permission
    }
