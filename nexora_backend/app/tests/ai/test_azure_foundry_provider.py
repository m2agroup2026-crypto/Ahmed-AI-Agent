from unittest.mock import Mock

from app.ai.providers.azure_foundry import AzureFoundryProvider


def test_azure_foundry_provider_generate():
    client = Mock()

    response = Mock()
    response.output_text = "NEXORA Foundry is ready"

    client.responses.create.return_value = response

    provider = AzureFoundryProvider(client=client)

    result = provider.generate("Hello NEXORA")

    assert result == "NEXORA Foundry is ready"

    client.responses.create.assert_called_once_with(
        model="gpt-5-mini",
        input="Hello NEXORA",
    )
