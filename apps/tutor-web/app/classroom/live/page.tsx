"use client";

import { useEffect, useState } from "react";
import type { Classroom, ClassroomIdentity } from "@contracts/classroom";
import type { LiveGrant, LiveParticipant, LiveSession } from "@contracts/live";
import { controlState, mediaPermissions, needsGrantRenewal, type ControlConnection } from "../../../lib/live-client";
import "./live.css";
import { usePreferences } from "../../preferences";

const copy = {
  en: {
    title: "Live classroom", back: "Classrooms and sign in", language: "العربية", classes: "Your classroom",
    preview: "Control preview only. No audio, video or screen content is transmitted. ACS media is disabled pending secure Teams integration.",
    schedule: "Schedule a session", sessionTitle: "Session title", start: "Start time", duration: "Duration (minutes)",
    provider: "Provider", local: "Local control preview", acs: "ACS Teams candidate (media disabled)", notice: "Plan recording notice and explicit consent",
    save: "Schedule", sessions: "Sessions", empty: "No sessions scheduled.", startSession: "Start control preview", end: "End session",
    join: "Join control preview", leave: "Leave", accept: "I explicitly consent", decline: "Decline", consented: "Consent saved for this notice version.",
    video: "Teacher camera", audio: "Teacher microphone", screen: "Share screen", unavailable: "Media controls are unavailable for this provider configuration.",
    listen: "Student listen-only by default. A microphone grant below changes preview metadata only.", hand: "Raise hand", lower: "Lower hand",
    people: "Application attendance", student: "Student", teacher: "Teacher", requested: "Hand raised", allow: "Allow microphone (preview)",
    block: "Block microphone (preview)", revoke: "Revoke access", lastSeen: "Last application heartbeat", revoked: "Revoked", left: "Left",
    recording: "Recording", record: "Start recording", stop: "Stop recording", unsupported: "Recording is unsupported here. Notices and consent are metadata prototypes; no paid recordings are created.",
    capture: "Private playback requires authorization. Screen capture cannot be absolutely prevented.",
    error: "Request failed. Check your access, consent and scheduled window, then retry.", signin: "Sign in on the classroom page first.",
    retry: "Retry", saving: "Saving…", states: { idle: "Not joined", joining: "Joining control preview…", control_connected: "Control panel connected; media unavailable",
      reconnecting: "Connection lost. Retrying…", ended: "Session ended or expired", revoked: "Access revoked or sign-in expired" },
    status: { scheduled: "Scheduled", live: "Control session active", ending: "Ending; access blocked", ended: "Ended", expired: "Expired" },
    recordingStates: { not_started: "Not started", recording: "Recording (test provider only)", processing: "Processing metadata", ready: "Private playback ready" },
  },
  ar: {
    title: "الفصل المباشر", back: "الفصول وتسجيل الدخول", language: "English", classes: "الفصل الدراسي",
    preview: "معاينة لوحة التحكم فقط. لا يتم إرسال صوت أو فيديو أو محتوى شاشة. وسائط ACS معطلة حتى اكتمال تكامل Teams الآمن.",
    schedule: "جدولة حصة", sessionTitle: "عنوان الحصة", start: "وقت البدء", duration: "المدة بالدقائق",
    provider: "مزود الخدمة", local: "معاينة محلية للتحكم", acs: "مرشح ACS Teams — الوسائط معطلة", notice: "إشعار التسجيل والموافقة الصريحة",
    save: "جدولة", sessions: "الحصص", empty: "لا توجد حصص مجدولة.", startSession: "بدء معاينة التحكم", end: "إنهاء الحصة",
    join: "الانضمام لمعاينة التحكم", leave: "مغادرة", accept: "أوافق صراحةً", decline: "رفض", consented: "تم حفظ الموافقة على هذا الإصدار من الإشعار.",
    video: "كاميرا المعلم", audio: "ميكروفون المعلم", screen: "مشاركة الشاشة", unavailable: "التحكم في الوسائط غير متاح لإعداد مزود الخدمة الحالي.",
    listen: "الطالب للاستماع فقط افتراضيًا. منح الميكروفون أدناه يغير بيانات المعاينة فقط.", hand: "رفع اليد", lower: "خفض اليد",
    people: "الحضور في التطبيق", student: "طالب", teacher: "معلم", requested: "اليد مرفوعة", allow: "السماح بالميكروفون — معاينة",
    block: "منع الميكروفون — معاينة", revoke: "إلغاء الوصول", lastSeen: "آخر اتصال بالتطبيق", revoked: "الوصول ملغى", left: "غادر",
    recording: "التسجيل", record: "بدء التسجيل", stop: "إيقاف التسجيل", unsupported: "التسجيل غير مدعوم هنا. الإشعارات والموافقات نموذج للبيانات فقط؛ لا يتم إنشاء تسجيلات مدفوعة.",
    capture: "يتطلب التشغيل الخاص صلاحية وصول. لا يمكن منع التقاط الشاشة بشكل مطلق.",
    error: "تعذر تنفيذ الطلب. تحقق من الصلاحيات والموافقة ووقت الحصة، ثم أعد المحاولة.", signin: "سجل الدخول أولًا من صفحة الفصول.",
    retry: "إعادة المحاولة", saving: "جارٍ الحفظ…", states: { idle: "لم تنضم بعد", joining: "جارٍ الانضمام للمعاينة…", control_connected: "لوحة التحكم متصلة؛ الوسائط غير متاحة",
      reconnecting: "انقطع الاتصال. جارٍ إعادة المحاولة…", ended: "انتهت الحصة أو مدتها", revoked: "ألغي الوصول أو انتهى تسجيل الدخول" },
    status: { scheduled: "مجدولة", live: "جلسة التحكم نشطة", ending: "جارٍ الإنهاء؛ الوصول محظور", ended: "منتهية", expired: "انتهت المدة" },
    recordingStates: { not_started: "لم يبدأ", recording: "جارٍ التسجيل — مزود اختباري فقط", processing: "معالجة البيانات", ready: "التشغيل الخاص جاهز" },
  },
};

class LiveApiError extends Error {
  constructor(readonly status: number) { super("Live request failed"); }
}

async function request<T>(path: string, method = "GET", data?: unknown): Promise<T> {
  const response = await fetch(`/api/classroom/${path}`, { method, cache: "no-store",
    headers: { "Content-Type": "application/json" }, body: data === undefined ? undefined : JSON.stringify(data) });
  if (!response.ok) throw new LiveApiError(response.status);
  return response.json() as Promise<T>;
}

function localTime() {
  const date = new Date();
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

export default function LiveClassroomPage() {
  const { language: locale, setLanguage: setLocale } = usePreferences();
  const t = copy[locale];
  const [identity, setIdentity] = useState<ClassroomIdentity | null>(null);
  const [classes, setClasses] = useState<Classroom[]>([]);
  const [classId, setClassId] = useState("");
  const [sessions, setSessions] = useState<LiveSession[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [session, setSession] = useState<LiveSession | null>(null);
  const [grant, setGrant] = useState<LiveGrant | null>(null);
  const [participants, setParticipants] = useState<LiveParticipant[]>([]);
  const [connection, setConnection] = useState<ControlConnection>("idle");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  const teacher = identity?.role === "TEACHER";
  // There is no installed/approved media transport. Capability metadata alone
  // must never turn on a microphone, capture a screen, or imply a video stream.
  const permissions = session ? mediaPermissions(session, teacher, false) : { audio: false, video: false, screen: false };

  async function run(action: () => Promise<void>) {
    setBusy(true); setError(false);
    try { await action(); } catch { setError(true); }
    finally { setBusy(false); }
  }
  async function refreshSessions(id = classId) {
    setSessions(await request<LiveSession[]>(`classes/${id}/live`));
  }
  async function leaveCurrent() {
    if (grant && selectedId) await request(`live/${selectedId}/leave`, "POST");
    setGrant(null); setConnection("idle");
  }
  async function chooseSession(item: LiveSession) {
    if (selectedId !== item.id) await leaveCurrent();
    setSelectedId(item.id); setSession(await request<LiveSession>(`live/${item.id}`)); setParticipants([]);
  }
  async function joinSession() {
    if (!selectedId) return;
    setConnection("joining");
    const next = await request<LiveGrant>(`live/${selectedId}/join`, "POST");
    setGrant(next); setSession(next.session); setConnection(controlState(next.session, true));
  }

  useEffect(() => {
    let active = true;
    void request<ClassroomIdentity>("me").then(async (person) => {
      const items = await request<Classroom[]>("classes");
      if (active) { setIdentity(person); setClasses(items); setClassId(items[0]?.id ?? ""); }
    }).catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    if (classId) void request<LiveSession[]>(`classes/${classId}/live`)
      .then((items) => { if (active) setSessions(items); }).catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [classId]);

  useEffect(() => {
    if (!selectedId) return;
    let active = true;
    let running = false;
    async function sync() {
      if (running) return;
      running = true;
      try {
        let latest = await request<LiveSession>(`live/${selectedId}`);
        if (!active) return;
        const state = controlState(latest, true);
        if (state === "ended" || state === "revoked") {
          setGrant(null); setConnection(state); setSession(latest); return;
        }
        if (grant) {
          if (needsGrantRenewal(grant.expires_at)) {
            const renewed = await request<LiveGrant>(`live/${selectedId}/join`, "POST");
            if (!active) return;
            setGrant(renewed); latest = renewed.session;
          } else {
            latest = await request<LiveSession>(`live/${selectedId}/heartbeat`, "POST", { access_token: grant.access_token });
          }
        }
        const roster = await request<LiveParticipant[]>(`live/${selectedId}/participants`);
        if (active) { setSession(latest); setParticipants(roster); setConnection(controlState(latest, true)); }
      } catch (reason) {
        if (!active) return;
        if (reason instanceof LiveApiError && [401, 403, 404].includes(reason.status)) {
          setGrant(null); setParticipants([]); setSession(null); setConnection("revoked");
        } else if (reason instanceof LiveApiError && reason.status === 409) {
          setGrant(null); setConnection("ended");
        } else setConnection("reconnecting");
      } finally { running = false; }
    }
    void sync();
    const timer = setInterval(() => void sync(), 10000);
    window.addEventListener("online", sync);
    const offline = () => setConnection("reconnecting");
    window.addEventListener("offline", offline);
    return () => { active = false; clearInterval(timer); window.removeEventListener("online", sync); window.removeEventListener("offline", offline); };
  }, [selectedId, grant?.access_token]);

  const consent = async (accepted: boolean) => {
    if (!session) return;
    await request(`live/${session.id}/consent`, "POST", { notice_version: session.notice_version, accepted });
    setSession(await request<LiveSession>(`live/${session.id}`));
  };

  return <main className="shell live-classroom" dir={locale === "ar" ? "rtl" : "ltr"} lang={locale}>
    <header className="topbar"><h1>{t.title}</h1><a href="/classroom">{t.back}</a>
      <button type="button" onClick={() => setLocale(locale === "ar" ? "en" : "ar")}>{t.language}</button></header>
    <p className="live-notice">{t.preview}</p>
    <div role="status" aria-live="polite">{busy ? t.saving : error ? t.error : selectedId ? t.states[connection] : ""}</div>
    {!identity ? <p>{t.signin}</p> : <>
      <p>{identity.name}</p>
      <label>{t.classes}<select value={classId} disabled={busy} onChange={(event) => {
        const id = event.target.value;
        if (id === classId) return;
        void run(async () => { await leaveCurrent(); setSelectedId(""); setSession(null); setParticipants([]); setSessions([]); setClassId(id); });
      }}><option value="">—</option>{classes.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      {teacher && classId && <form method="post" className="live-card" onSubmit={(event) => {
        event.preventDefault(); const data = new FormData(event.currentTarget);
        void run(async () => {
          const begins = new Date(String(data.get("starts")));
          const item = await request<LiveSession>(`classes/${classId}/live`, "POST", {
            title: data.get("title"), provider: data.get("provider"), starts_at: begins.toISOString(),
            ends_at: new Date(begins.getTime() + Number(data.get("duration")) * 60000).toISOString(), recording_notice: data.get("notice") === "on",
          });
          await refreshSessions(); await chooseSession(item);
        });
      }}><h2>{t.schedule}</h2>
        <label>{t.sessionTitle}<input name="title" required maxLength={160} /></label>
        <label>{t.start}<input name="starts" type="datetime-local" defaultValue={localTime()} required /></label>
        <label>{t.duration}<input name="duration" type="number" min={1} max={120} defaultValue={15} required /></label>
        <label>{t.provider}<select name="provider"><option value="local_preview">{t.local}</option><option value="acs_teams">{t.acs}</option></select></label>
        <label><input type="checkbox" name="notice" /> {t.notice}</label><button disabled={busy}>{t.save}</button>
      </form>}
      <section className="live-card"><h2>{t.sessions}</h2>
        {sessions.length === 0 && <p>{t.empty}</p>}
        {sessions.map((item) => <button key={item.id} disabled={busy} onClick={() => void run(() => chooseSession(item))}>
          {item.title} · {new Date(item.starts_at).toLocaleString(locale)} · {t.status[item.state]}</button>)}
      </section>
      {session && <section className="live-card"><h2>{session.title}</h2><p>{t.status[session.state]}</p>
        <p>{new Date(session.starts_at).toLocaleString(locale)} — {new Date(session.ends_at).toLocaleString(locale)}</p>
        {teacher && <div><button disabled={busy || session.state !== "scheduled"} onClick={() => void run(async () => {
          setSession(await request<LiveSession>(`live/${session.id}/start`, "POST")); await refreshSessions();
        })}>{t.startSession}</button><button disabled={busy || session.state === "ended"} onClick={() => void run(async () => {
          setSession(await request<LiveSession>(`live/${session.id}/end`, "POST")); setGrant(null); setConnection("ended"); await refreshSessions();
        })}>{t.end}</button></div>}
        {session.recording_notice && <div className="live-notice"><p>{session.recording_notice[locale]}</p>
          {session.consented ? <p>{t.consented}</p> : <div>
            <button disabled={busy} onClick={() => void run(() => consent(true))}>{t.accept}</button>
            <button disabled={busy} onClick={() => void run(() => consent(false))}>{t.decline}</button></div>}
        </div>}
        <button disabled={busy || session.state !== "live" || !!session.participant?.revoked || (!!session.recording_notice && !session.consented)}
          onClick={() => void run(joinSession)}>{t.join}</button>
        <button disabled={busy || !grant} onClick={() => void run(async () => { await leaveCurrent(); setSession(await request<LiveSession>(`live/${session.id}`)); })}>{t.leave}</button>
        {connection === "reconnecting" && <button disabled={busy} onClick={() => void run(joinSession)}>{t.retry}</button>}
        <div className="live-media"><p>{t.unavailable}</p><button disabled={!permissions.video}>{t.video}</button>
          <button disabled={!permissions.audio}>{t.audio}</button><button disabled={!permissions.screen}>{t.screen}</button></div>
        {!teacher && <div><p>{t.listen}</p><button disabled={busy || !grant || session.state !== "live"} onClick={() => void run(async () => {
          await request(`live/${session.id}/hand`, "POST", { access_token: grant?.access_token, raised: !session.participant?.hand_raised });
          setSession(await request<LiveSession>(`live/${session.id}`));
        })}>{session.participant?.hand_raised ? t.lower : t.hand}</button></div>}
        <section><h3>{t.people}</h3>{participants.map((p) => <article className="live-person" key={p.user_id}>
          <p>{p.role === "teacher" ? t.teacher : t.student} #{p.user_id} {p.hand_raised ? `· ${t.requested}` : ""} {p.revoked ? `· ${t.revoked}` : p.left_at ? `· ${t.left}` : ""}</p>
          <p>{t.lastSeen}: {new Date(p.last_seen_at).toLocaleString(locale)}</p>
          {teacher && p.role === "student" && !p.revoked && !p.left_at && <div>
            <button disabled={busy || (!p.can_speak && !p.hand_raised) || session.state !== "live"} onClick={() => void run(async () => {
              await request(`live/${session.id}/participants/${p.user_id}/audio`, "POST", { allowed: !p.can_speak });
              setParticipants(await request<LiveParticipant[]>(`live/${session.id}/participants`));
            })}>{p.can_speak ? t.block : t.allow}</button>
            <button disabled={busy} onClick={() => void run(async () => {
              await request(`live/${session.id}/participants/${p.user_id}/revoke`, "POST");
              setParticipants(await request<LiveParticipant[]>(`live/${session.id}/participants`));
            })}>{t.revoke}</button></div>}
        </article>)}</section>
        <section><h3>{t.recording}</h3><p>{t.recordingStates[session.recording_state as keyof typeof t.recordingStates] ?? session.recording_state}</p>
          <p>{t.unsupported}</p><p>{t.capture}</p>
          {teacher && <><button disabled={busy || !session.capabilities.recording || session.state !== "live"} onClick={() => void run(async () => {
            await request(`live/${session.id}/recording/start`, "POST"); setSession(await request<LiveSession>(`live/${session.id}`));
          })}>{t.record}</button><button disabled={busy || !session.capabilities.recording || session.recording_state !== "recording"} onClick={() => void run(async () => {
            await request(`live/${session.id}/recording/stop`, "POST"); setSession(await request<LiveSession>(`live/${session.id}`));
          })}>{t.stop}</button></>}
          {session.recording_state === "ready" && <video controls controlsList="nodownload" disablePictureInPicture preload="none"
            src={`/api/classroom/live/${session.id}/recording/playback`} aria-label={t.recording} />}
        </section>
      </section>}
    </>}
  </main>;
}
