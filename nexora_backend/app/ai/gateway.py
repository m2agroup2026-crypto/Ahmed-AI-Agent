from app.ai.providers.azure_foundry import AzureFoundryProvider


class ModelGateway:
    """Provider-independent gateway for NEXORA model inference."""

    def __init__(self, provider=None):
        self.provider = provider or AzureFoundryProvider()

    def generate(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        return self.provider.generate(prompt)
