from unittest.mock import Mock

import pytest

from app.ai.gateway import ModelGateway


def test_model_gateway_delegates_to_provider():
    provider = Mock()
    provider.generate.return_value = "NEXORA response"

    gateway = ModelGateway(provider=provider)

    result = gateway.generate("Hello NEXORA")

    assert result == "NEXORA response"
    provider.generate.assert_called_once_with("Hello NEXORA")


def test_model_gateway_rejects_empty_prompt():
    provider = Mock()
    gateway = ModelGateway(provider=provider)

    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        gateway.generate("   ")

    provider.generate.assert_not_called()
