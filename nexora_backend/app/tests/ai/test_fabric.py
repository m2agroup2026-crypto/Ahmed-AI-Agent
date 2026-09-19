from app.ai.core.fabric import IntelligenceFabric


def test_fabric_process():

    fabric = IntelligenceFabric()

    result = {
        "state": type(
            "State",
            (),
            {
                "user_id": 1,
                "intent": "VIEW_USERS"
            }
        )(),
        "decision": type(
            "Decision",
            (),
            {
                "decision": "ALLOW",
                "reason": "users.manage"
            }
        )()
    }

    output = fabric.process(result)

    assert "result" in output

    assert "audit" in output

    assert output["audit"].decision == "ALLOW"
