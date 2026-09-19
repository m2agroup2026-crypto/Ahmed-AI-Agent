from app.ai.billing.action_mapper import map_action


def test_action_mapper():

    assert map_action(
        "VIEW_USERS"
    ) == "GENERAL_QUERY"


    assert map_action(
        "VIEW_DASHBOARD"
    ) == "ANALYTICS"


    assert map_action(
        "CHECK_SYSTEM_STATUS"
    ) == "GENERAL_QUERY"


    assert map_action(
        "UNKNOWN"
    ) == "GENERAL_QUERY"
