from datetime import UTC
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, StringConstraints, model_validator

from app.products.tutor.classroom.models import now
from app.products.tutor.classroom.schemas import Input


class Schedule(Input):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    provider: Literal["local_preview", "acs_teams"] = "local_preview"
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    recording_notice: bool = Field(strict=True, default=False)

    @model_validator(mode="after")
    def valid_window(self):
        # Normalize before SQLite (which discards offsets) or PostgreSQL persists
        # the schedule. A caller's timezone must never extend the access window.
        self.starts_at = self.starts_at.astimezone(UTC)
        self.ends_at = self.ends_at.astimezone(UTC)
        seconds = (self.ends_at - self.starts_at).total_seconds()
        if not 60 <= seconds <= 7200:
            raise ValueError("Sessions must last between one minute and two hours")
        if (self.starts_at - now()).total_seconds() < -300 or (self.starts_at - now()).days > 90:
            raise ValueError("Schedule within the next 90 days")
        return self


class Consent(Input):
    notice_version: int = Field(strict=True, ge=1)
    accepted: bool = Field(strict=True)


class GrantInput(Input):
    access_token: Annotated[str, StringConstraints(min_length=32, max_length=128)]


class HandRaise(GrantInput):
    raised: bool = Field(strict=True)


class Moderate(Input):
    allowed: bool = Field(strict=True)
