from app.ai.intents.detector import detect_intent
from app.ai.assistant.security import authorize_ai_action
from app.ai.billing.action_mapper import map_action
from app.ai.billing.action_costs import get_action_cost
from app.ai.middleware.billing_middleware import BillingMiddleware
from app.ai.decision.engine import DecisionEngine
from app.ai.memory.events import EventLogger, AIEvent


class AgentPipeline:

    def __init__(
        self,
        billing_middleware=None
    ):

        self.decision_engine = DecisionEngine()
        self.event_logger = EventLogger()

        self.billing = (
            billing_middleware
            or BillingMiddleware()
        )

    def run(
        self,
        state,
        db
    ):

        intent_result = detect_intent(
            state.input_text
        )

        state.intent = intent_result["intent"]

        state.permission = (
            intent_result["definition"]["permission"]
        )

        authorization = authorize_ai_action(
            db,
            state.user_id,
            state.intent
        )

        decision = self.decision_engine.evaluate(
            authorization["allowed"],
            authorization["permission"]
        )

        self.event_logger.log(
            AIEvent(
                "AI_DECISION",
                state.user_id,
                state.intent,
                decision.status
            )
        )

        state.status = decision.status

        if not authorization["allowed"]:
            return {
                "state": state,
                "decision": decision,
                "events": self.event_logger.all()
            }

        action = map_action(
            state.intent
        )

        credits = get_action_cost(
            action
        )

        if credits > 0:
            billing_result = self.billing.charge(
                state.user_id,
                action,
                credits
            )
        else:
            billing_result = None

        return {
            "state": state,
            "decision": decision,
            "billing": billing_result,
            "events": self.event_logger.all()
        }
