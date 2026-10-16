"""No SDK construction, network transport, credentials, or paid operations at import time."""
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import timedelta
from typing import Any


class ProviderUnavailable(Exception):
    pass


class UnsupportedCapability(Exception):
    pass


@dataclass(frozen=True)
class Capabilities:
    media: bool = False
    teacher_video: bool = False
    teacher_audio: bool = False
    screen_share: bool = False
    enforced_membership: bool = False
    moderated_audio: bool = False
    recording: bool = False
    metadata_preview: bool = False

    def public(self):
        return asdict(self)


class LiveClassProvider(ABC):
    name: str
    capabilities = Capabilities()

    @abstractmethod
    def start(self, session_id: str) -> str:
        """Return a server-private provider session reference."""

    @abstractmethod
    def admit(self, reference: str, user_id: int, role: str) -> None:
        """Enforce participant admission remotely, or reject before issuing credentials."""

    @abstractmethod
    def revoke(self, reference: str, user_id: int) -> None:
        pass

    @abstractmethod
    def end(self, reference: str) -> None:
        pass

    def moderate_audio(self, reference: str, user_id: int, allowed: bool) -> None:
        raise UnsupportedCapability("Provider cannot enforce student microphone permissions")

    def start_recording(self, reference: str) -> str:
        raise UnsupportedCapability("Recording is unavailable for this provider and scenario")

    def stop_recording(self, reference: str, recording_reference: str) -> None:
        raise UnsupportedCapability("Recording is unavailable for this provider and scenario")


class LocalPreviewProvider(LiveClassProvider):
    """Application presence and controls only; never simulates transmitted audio/video."""
    name = "local_preview"
    capabilities = Capabilities(metadata_preview=True)

    def start(self, session_id):
        return "preview:" + session_id

    def admit(self, reference, user_id, role):
        return None

    def revoke(self, reference, user_id):
        return None

    def end(self, reference):
        return None

    def moderate_audio(self, reference, user_id, allowed):
        # Updates application permission metadata only. capabilities.media is false.
        return None


@dataclass(frozen=True)
class IdentityToken:
    token: str = field(repr=False)
    expires_on: int


class AcsTeamsProvider(LiveClassProvider):
    """Teams-interoperability candidate, deliberately not a standalone Rooms integration.

    Identity operations match CommunicationIdentityClient's documented methods and
    accept an injected SDK client. No client is constructed and no environment
    setting can enable Azure calls. The application registry never injects a client.
    A real pilot also needs tenant-enforced admission, organizer moderation and
    remote termination/revocation; none is established by minting an ACS token.
    """
    name = "acs_teams"

    def __init__(self, identity_client: Any = None, *, external_calls_approved: bool = False):
        self._client = identity_client
        self._approved = external_calls_approved

    def _identity_client(self):
        if not self._approved or self._client is None:
            raise ProviderUnavailable("ACS identity operations are disabled pending a separately approved pilot")
        return self._client

    def issue_identity_token(self, identity) -> IdentityToken:
        # This is NOT a classroom grant or a room-scoped token. One hour is the
        # documented minimum ACS lifetime; AQLITH's five-minute grants are separate.
        token = self._identity_client().get_token(identity, scopes=["voip"],
                                                  token_expires_in=timedelta(hours=1))
        return IdentityToken(token.token, token.expires_on)

    def revoke_identity_tokens(self, identity):
        self._identity_client().revoke_tokens(identity)

    def start(self, session_id):
        raise ProviderUnavailable("ACS Teams media admission and organizer enforcement are not configured")

    def admit(self, reference, user_id, role):
        raise ProviderUnavailable("ACS classroom membership cannot yet be enforced remotely")

    def revoke(self, reference, user_id):
        raise ProviderUnavailable("ACS remote participant revocation is not configured")

    def end(self, reference):
        raise ProviderUnavailable("ACS remote meeting termination is not configured")


_PROVIDERS = {p.name: p for p in (LocalPreviewProvider(), AcsTeamsProvider())}


def get_provider(name: str) -> LiveClassProvider:
    if name not in _PROVIDERS:
        raise UnsupportedCapability("Unknown live classroom provider")
    return _PROVIDERS[name]


class PrivateRecordingStore(ABC):
    """Future encrypted store. Keys are server-only; playback must stream via auth."""
    encrypted = False

    @abstractmethod
    def stream(self, key: str):
        pass


def get_recording_store() -> PrivateRecordingStore:
    raise ProviderUnavailable("Encrypted private recording storage is not configured")
