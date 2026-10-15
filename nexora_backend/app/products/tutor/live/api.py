from datetime import timedelta
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.api.auth.dependencies import get_current_user
from app.database.dependencies import get_db
from app.models.user import User
from app.products.tutor.classroom.api import accessible, owned, role_name, teacher, utc
from app.products.tutor.classroom.models import Classroom, now
from .models import LiveAuditEvent, LiveConsent, LiveGrant, LiveParticipant, LiveRecording, LiveSession
from .providers import (ProviderUnavailable, UnsupportedCapability, get_provider, get_recording_store)
from .schemas import Consent, GrantInput, HandRaise, Moderate, Schedule

router = APIRouter(prefix="/api/v1/classroom", tags=["Live classrooms"])
NOTICE = {
    "en": "Recording is planned for this session. Audio, video and shared content may be recorded. Explicit consent is required before joining. Screen capture by participants cannot be absolutely prevented.",
    "ar": "التسجيل مخطط لهذه الحصة وقد يشمل الصوت والفيديو والمحتوى المشترك. تلزم موافقة صريحة قبل الانضمام. لا يمكن منع التقاط الشاشة من المشاركين بشكل مطلق.",
}


def audit(db, item, actor, action, **details):
    # Only caller-controlled action names and scalar identifiers; never credentials.
    db.add(LiveAuditEvent(session_id=item.id, actor_id=actor.id, action=action, details=details))


def provider_call(db, item, user, action, operation):
    try:
        return operation()
    except UnsupportedCapability:
        audit(db, item, user, action + ".unsupported")
        db.commit()
        raise HTTPException(501, "Requested provider capability is not supported") from None
    except Exception:
        # Deliberately never expose/log provider exceptions, which can contain keys.
        audit(db, item, user, action + ".unavailable")
        db.commit()
        raise HTTPException(503, "Live provider operation unavailable; application access may be blocked") from None


def unsupported(db, item, user, action):
    audit(db, item, user, action + ".unsupported")
    db.commit()
    raise HTTPException(501, "Requested provider capability is not supported")


def session_access(db, session_id, user, owner=False):
    item = db.get(LiveSession, session_id)
    if not item:
        raise HTTPException(404, "Live session not found")
    if owner:
        owned(db, item.classroom_id, user)
    else:
        accessible(db, item.classroom_id, user)
    return item


def require_open(db, item):
    if db.get(Classroom, item.classroom_id).archived:
        raise HTTPException(409, "Classroom is archived")
    if item.state != "live" or utc(item.ends_at) <= now():
        raise HTTPException(409, "Live session is not active")


def participant_view(p):
    return {"user_id": p.user_id, "role": p.role, "joined_at": utc(p.joined_at),
            "last_seen_at": utc(p.last_seen_at), "left_at": utc(p.left_at),
            "revoked": p.revoked_at is not None, "hand_raised": p.hand_raised,
            "can_speak": p.can_speak, "presence_source": "application_heartbeat"}


def view(db, item, user):
    provider = get_provider(item.provider)
    participant = db.get(LiveParticipant, (item.id, user.id))
    recording = db.get(LiveRecording, item.id)
    consent = db.get(LiveConsent, (item.id, user.id))
    state = "expired" if item.state != "ended" and utc(item.ends_at) <= now() else item.state
    return {"id": item.id, "classroom_id": item.classroom_id, "title": item.title,
            "provider": item.provider, "capabilities": provider.capabilities.public(),
            "state": state, "starts_at": utc(item.starts_at), "ends_at": utc(item.ends_at),
            "recording_notice": NOTICE if item.recording_notice else None,
            "notice_version": item.notice_version,
            "consented": bool(consent and consent.accepted and consent.notice_version == item.notice_version),
            "recording_state": recording.state if recording else "not_started",
            "participant": participant_view(participant) if participant else None}


def revoke_grants(db, item, user_id=None):
    query = update(LiveGrant).where(LiveGrant.session_id == item.id, LiveGrant.revoked_at.is_(None))
    if user_id is not None:
        query = query.where(LiveGrant.user_id == user_id)
    db.execute(query.values(revoked_at=now()), execution_options={"synchronize_session": False})


def validate_grant(db, item, user, token):
    require_open(db, item)
    grant = db.get(LiveGrant, hashlib.sha256(token.encode()).hexdigest())
    participant = db.get(LiveParticipant, (item.id, user.id))
    if (not grant or grant.session_id != item.id or grant.user_id != user.id or grant.revoked_at
            or utc(grant.expires_at) <= now() or not participant or participant.revoked_at or participant.left_at):
        raise HTTPException(403, "Live access has expired or been revoked")
    return participant


@router.get("/live/capabilities")
def capabilities(user: User = Depends(get_current_user)):
    return [{"provider": name, **get_provider(name).capabilities.public()}
            for name in ("local_preview", "acs_teams")]


@router.post("/classes/{class_id}/live", status_code=201)
def schedule(class_id: str, data: Schedule, user: User = Depends(teacher), db: Session = Depends(get_db)):
    owned(db, class_id, user, active=True)
    get_provider(data.provider)
    item = LiveSession(classroom_id=class_id, **data.model_dump())
    db.add(item)
    db.flush()
    db.add(LiveRecording(session_id=item.id))
    audit(db, item, user, "scheduled")
    db.commit()
    return view(db, item, user)


@router.get("/classes/{class_id}/live")
def list_sessions(class_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accessible(db, class_id, user)
    return [view(db, item, user) for item in db.query(LiveSession).filter_by(classroom_id=class_id).order_by(LiveSession.starts_at).all()]


@router.get("/live/{session_id}")
def detail(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return view(db, session_access(db, session_id, user), user)


@router.post("/live/{session_id}/start")
def start(session_id: str, user: User = Depends(teacher), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user, owner=True)
    owned(db, item.classroom_id, user, active=True)
    if item.state == "live":
        require_open(db, item)
        return view(db, item, user)
    if item.state != "scheduled" or not utc(item.starts_at) <= now() < utc(item.ends_at):
        raise HTTPException(409, "Session cannot start outside its scheduled window")
    provider = get_provider(item.provider)
    # No provider with real media can activate until admission and moderation are enforced.
    if provider.capabilities.media and not (provider.capabilities.enforced_membership and provider.capabilities.moderated_audio):
        raise HTTPException(503, "Provider cannot enforce classroom permissions")
    item.provider_reference = provider_call(db, item, user, "start", lambda: provider.start(item.id))
    item.state = "live"
    audit(db, item, user, "started")
    db.commit()
    return view(db, item, user)


@router.post("/live/{session_id}/consent")
def consent(session_id: str, data: Consent, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user)
    if item.state == "ended" or utc(item.ends_at) <= now():
        raise HTTPException(409, "Live session has ended")
    if not item.recording_notice or data.notice_version != item.notice_version:
        raise HTTPException(409, "Recording notice is missing or has changed")
    participant = db.get(LiveParticipant, (item.id, user.id))
    if not data.accepted and participant and not participant.left_at and not participant.revoked_at:
        raise HTTPException(409, "Leave the session before withdrawing recording consent")
    receipt = db.get(LiveConsent, (item.id, user.id))
    if not receipt:
        receipt = LiveConsent(session_id=item.id, user_id=user.id)
        db.add(receipt)
    receipt.notice_version, receipt.accepted, receipt.recorded_at = data.notice_version, data.accepted, now()
    audit(db, item, user, "consent.accepted" if data.accepted else "consent.declined", notice_version=item.notice_version)
    db.commit()
    return {"accepted": receipt.accepted, "notice_version": receipt.notice_version}


@router.post("/live/{session_id}/join")
def join(session_id: str, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user)
    require_open(db, item)
    participant = db.get(LiveParticipant, (item.id, user.id))
    if participant and participant.revoked_at:
        raise HTTPException(403, "Participation has been revoked")
    receipt = db.get(LiveConsent, (item.id, user.id))
    if item.recording_notice and not (receipt and receipt.accepted and receipt.notice_version == item.notice_version):
        raise HTTPException(403, "Explicit consent to the current recording notice is required")
    role = "teacher" if role_name(user) == "TEACHER" else "student"
    provider = get_provider(item.provider)
    provider_call(db, item, user, "join", lambda: provider.admit(item.provider_reference, user.id, role))
    if not participant:
        participant = LiveParticipant(session_id=item.id, user_id=user.id, role=role, can_speak=role == "teacher")
        db.add(participant)
    if role == "teacher":
        participant.can_speak = True
    participant.left_at, participant.last_seen_at = None, now()
    revoke_grants(db, item, user.id)
    token = secrets.token_urlsafe(32)
    expires_at = min(now() + timedelta(minutes=5), utc(item.ends_at))
    db.add(LiveGrant(token_hash=hashlib.sha256(token.encode()).hexdigest(), session_id=item.id,
                     user_id=user.id, expires_at=expires_at))
    audit(db, item, user, "joined", role=role)
    db.commit()
    response.headers["Cache-Control"] = "no-store"
    return {"session": view(db, item, user), "access_token": token, "expires_at": expires_at,
            "token_purpose": "aqlith_application_presence_only", "media_credentials": None}


@router.post("/live/{session_id}/heartbeat")
def heartbeat(session_id: str, data: GrantInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user)
    participant = validate_grant(db, item, user, data.access_token)
    participant.last_seen_at = now()
    db.commit()
    return view(db, item, user)


@router.post("/live/{session_id}/hand")
def hand(session_id: str, data: HandRaise, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user)
    participant = validate_grant(db, item, user, data.access_token)
    if participant.role != "student":
        raise HTTPException(403, "Only students request microphone access")
    participant.hand_raised = data.raised
    audit(db, item, user, "hand.raised" if data.raised else "hand.lowered")
    db.commit()
    return participant_view(participant)


@router.get("/live/{session_id}/participants")
def participants(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user)
    query = db.query(LiveParticipant).filter_by(session_id=item.id)
    if role_name(user) != "TEACHER":
        query = query.filter_by(user_id=user.id)
    return [participant_view(p) for p in query.all()]


@router.post("/live/{session_id}/participants/{user_id}/audio")
def moderate(session_id: str, user_id: int, data: Moderate, user: User = Depends(teacher), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user, owner=True)
    require_open(db, item)
    participant = db.get(LiveParticipant, (item.id, user_id))
    target = db.get(User, user_id)
    if not participant or participant.revoked_at or participant.left_at or participant.role != "student":
        raise HTTPException(404, "Active student participant not found")
    if not target or not target.is_active or role_name(target) != "STUDENT":
        raise HTTPException(404, "Active student participant not found")
    accessible(db, item.classroom_id, target)
    if data.allowed and not participant.hand_raised:
        raise HTTPException(409, "Student must raise a hand first")
    if not data.allowed:
        participant.can_speak = False
    provider = get_provider(item.provider)
    provider_call(db, item, user, "audio", lambda: provider.moderate_audio(item.provider_reference, user_id, data.allowed))
    participant.can_speak, participant.hand_raised = data.allowed, False
    audit(db, item, user, "audio.allowed" if data.allowed else "audio.blocked", target_id=user_id)
    db.commit()
    return participant_view(participant)


def depart(db, item, participant, actor, revoke):
    if participant.role == "teacher" and revoke:
        raise HTTPException(409, "End the session to remove the teacher")
    participant.left_at, participant.can_speak, participant.hand_raised = now(), False, False
    if revoke:
        participant.revoked_at = now()
    revoke_grants(db, item, participant.user_id)
    provider = get_provider(item.provider)
    provider_call(db, item, actor, "revoke" if revoke else "leave",
                  lambda: provider.revoke(item.provider_reference, participant.user_id))
    audit(db, item, actor, "revoked" if revoke else "left", target_id=participant.user_id)
    db.commit()
    return {"revoked": revoke, "left": True}


@router.post("/live/{session_id}/participants/{user_id}/revoke")
def revoke(session_id: str, user_id: int, user: User = Depends(teacher), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user, owner=True)
    participant = db.get(LiveParticipant, (item.id, user_id))
    if not participant:
        raise HTTPException(404, "Participant not found")
    return depart(db, item, participant, user, True)


@router.post("/live/{session_id}/leave")
def leave(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user)
    participant = db.get(LiveParticipant, (item.id, user.id))
    if not participant:
        raise HTTPException(404, "Participant not found")
    return depart(db, item, participant, user, False)


@router.post("/live/{session_id}/end")
def end(session_id: str, user: User = Depends(teacher), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user, owner=True)
    if item.state == "ended":
        return view(db, item, user)
    provider = get_provider(item.provider)
    item.state = "ending"
    revoke_grants(db, item)
    if item.provider_reference:
        provider_call(db, item, user, "end", lambda: provider.end(item.provider_reference))
    item.state, item.ended_at = "ended", now()
    db.execute(update(LiveParticipant).where(LiveParticipant.session_id == item.id).values(
        left_at=now(), can_speak=False, hand_raised=False), execution_options={"synchronize_session": False})
    recording = db.get(LiveRecording, item.id)
    if recording.state == "recording":
        recording.state = "processing"
    audit(db, item, user, "ended")
    db.commit()
    return view(db, item, user)


@router.post("/live/{session_id}/recording/start")
def start_recording(session_id: str, user: User = Depends(teacher), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user, owner=True)
    require_open(db, item)
    provider = get_provider(item.provider)
    if not provider.capabilities.recording:
        unsupported(db, item, user, "recording.start")
    if not item.recording_notice:
        raise HTTPException(409, "Recording notice must be configured before the session")
    active = db.query(LiveParticipant).filter_by(session_id=item.id, left_at=None, revoked_at=None).all()
    if not active or not any(p.user_id == user.id for p in active):
        raise HTTPException(409, "Teacher must join and consent before recording")
    for participant in active:
        receipt = db.get(LiveConsent, (item.id, participant.user_id))
        if not receipt or not receipt.accepted or receipt.notice_version != item.notice_version:
            raise HTTPException(409, "Every active participant must explicitly consent")
    recording = db.get(LiveRecording, item.id)
    if recording.state == "recording":
        return {"state": recording.state}
    if recording.state != "not_started":
        raise HTTPException(409, "Recording has already been requested")
    recording.provider_reference = provider_call(db, item, user, "recording.start",
        lambda: provider.start_recording(item.provider_reference))
    recording.state = "recording"
    audit(db, item, user, "recording.started", notice_version=item.notice_version)
    db.commit()
    return {"state": recording.state}


@router.post("/live/{session_id}/recording/stop")
def stop_recording(session_id: str, user: User = Depends(teacher), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user, owner=True)
    provider = get_provider(item.provider)
    recording = db.get(LiveRecording, item.id)
    if not provider.capabilities.recording:
        unsupported(db, item, user, "recording.stop")
    if recording.state != "recording":
        raise HTTPException(409, "Recording is not active")
    provider_call(db, item, user, "recording.stop", lambda: provider.stop_recording(item.provider_reference, recording.provider_reference))
    recording.state = "processing"
    audit(db, item, user, "recording.stopped")
    db.commit()
    return {"state": recording.state}


@router.get("/live/{session_id}/recording/playback")
def playback(session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user)
    participant = db.get(LiveParticipant, (item.id, user.id))
    if role_name(user) != "TEACHER" and (not participant or participant.revoked_at):
        raise HTTPException(404, "Recording not found")
    recording = db.get(LiveRecording, item.id)
    if recording.state != "ready" or not recording.storage_key or not recording.encrypted:
        raise HTTPException(404, "Private recording is not available")
    try:
        store = get_recording_store()
        if not store.encrypted:
            raise ProviderUnavailable()
        stream = store.stream(recording.storage_key)
    except Exception:
        raise HTTPException(503, "Encrypted private recording storage is unavailable") from None
    audit(db, item, user, "recording.played")
    db.commit()
    return StreamingResponse(stream, media_type="video/mp4", headers={
        "Cache-Control": "private, no-store", "Content-Disposition": "inline",
        "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer"})


@router.get("/live/{session_id}/audit")
def events(session_id: str, user: User = Depends(teacher), db: Session = Depends(get_db)):
    item = session_access(db, session_id, user, owner=True)
    return [{"actor_id": e.actor_id, "action": e.action, "details": e.details, "created_at": utc(e.created_at)}
            for e in db.query(LiveAuditEvent).filter_by(session_id=item.id).order_by(LiveAuditEvent.created_at).all()]
