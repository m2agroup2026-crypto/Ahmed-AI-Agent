from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI

from app.config.settings import settings


class AzureFoundryProvider:
    """Microsoft Foundry model provider using Microsoft Entra ID authentication."""

    TOKEN_SCOPE = "https://ai.azure.com/.default"

    def __init__(self, credential=None, client=None):
        self.endpoint = settings.AZURE_FOUNDRY_ENDPOINT
        self.deployment = settings.AZURE_FOUNDRY_DEPLOYMENT

        if client is not None:
            self.client = client
            return

        credential = credential or DefaultAzureCredential()

        token_provider = get_bearer_token_provider(
            credential,
            self.TOKEN_SCOPE,
        )

        self.client = OpenAI(
            base_url=self.endpoint,
            api_key=token_provider,
        )

    def generate(self, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.deployment,
            input=prompt,
        )

        return response.output_text
