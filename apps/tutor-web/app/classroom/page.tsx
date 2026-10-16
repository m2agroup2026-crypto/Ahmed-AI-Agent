"use client";

import { useEffect, useState } from "react";
import type { Classroom, ClassroomAssignment, ClassroomAttempt, ClassroomIdentity, ClassroomProgress } from "@contracts/classroom";
import { usePreferences } from "../preferences";
import { MathText } from "../math-text";

async function request<T>(path: string, method = "GET", data?: unknown): Promise<T> {
  const response = await fetch(`/api/classroom/${path}`, {
    method, headers: { "Content-Type": "application/json" },
    body: data === undefined ? undefined : JSON.stringify(data), cache: "no-store",
  });
  const body = await response.json();
  if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Check the form and try again.");
  return body as T;
}

export default function ClassroomPage() {
  const { language, t } = usePreferences();
  const [identity, setIdentity] = useState<ClassroomIdentity | null>(null);
  const [classes, setClasses] = useState<Classroom[]>([]);
  const [selected, setSelected] = useState<Classroom | null>(null);
  const [assignments, setAssignments] = useState<ClassroomAssignment[]>([]);
  const [results, setResults] = useState<ClassroomAttempt[]>([]);
  const [progress, setProgress] = useState<ClassroomProgress | null>(null);
  const [active, setActive] = useState<{ task: ClassroomAssignment; attempt: ClassroomAttempt } | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [invite, setInvite] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [clock, setClock] = useState(Date.now());
  const [questions, setQuestions] = useState([{ prompt: "", answer: "" }]);
  const teacher = identity?.role === "TEACHER";

  async function refresh(person = identity) {
    if (!person) return;
    setClasses(await request<Classroom[]>("classes"));
    if (person.role === "STUDENT") setProgress(await request<ClassroomProgress>("progress"));
  }
  async function open(item: Classroom) {
    setSelected(item); setActive(null); setAnswers({}); setInvite(""); setResults([]);
    setAssignments(await request<ClassroomAssignment[]>(`classes/${item.id}/assignments`));
    if (teacher) setResults(await request<ClassroomAttempt[]>(`classes/${item.id}/results`));
  }
  async function run(action: () => Promise<void>) {
    setBusy(true); setMessage("");
    try { await action(); } catch (error) { setMessage(error instanceof Error ? error.message : "Request failed"); }
    finally { setBusy(false); }
  }
  useEffect(() => {
    request<ClassroomIdentity>("me").then(async (person) => { setIdentity(person); await refresh(person); })
      .catch((error: Error) => { if (error.message !== "Authentication required") setMessage(error.message); });
    const timer = setInterval(() => setClock(Date.now()), 1000);
    return () => clearInterval(timer);
    // Initial session is checked once; later refreshes follow explicit actions.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const status = message === "Assessment assigned." ? t("تم إسناد الاختبار.", message)
    : message.startsWith("Result:") ? `${t("النتيجة:", "Result:")} ${message.slice(7)}`
    : message ? t("تعذر تنفيذ الطلب. تحقق من البيانات والصلاحيات والاتصال ثم أعد المحاولة.", message) : "";
  return <main className="shell classroom" dir={language === "ar" ? "rtl" : "ltr"} lang={language}>
    <header className="topbar"><div><span className="eyebrow">AQLITH / CLASSROOM</span><h1>{t("نتعلم معًا", "Learn together")}</h1></div><a href="/">{t("المنهج", "Curriculum")}</a><a href="/classroom/live">{t("الحصص المباشرة", "Live classes")}</a></header>
    <p>{t("دروس رياضيات بإشراف المعلم واختبارات أصلية محددة الوقت.", "Teacher-led mathematics lessons and original timed assessments.")}</p>
    <p role="status" aria-live="polite">{busy ? t("جارٍ الحفظ…", "Saving…") : status}</p>
    {!identity ? <form method="post" className="lesson-card" onSubmit={(event) => {
      event.preventDefault(); const form = new FormData(event.currentTarget);
      void run(async () => {
        await request("session", "POST", { email: form.get("email"), password: form.get("password") });
        const person = await request<ClassroomIdentity>("me"); setIdentity(person); await refresh(person);
      });
    }}><h3>{t("تسجيل الدخول", "Sign in")}</h3><label>{t("البريد الإلكتروني", "Email")}<input dir="ltr" name="email" type="email" autoComplete="username" required /></label>
      <label>{t("كلمة المرور", "Password")}<input dir="ltr" name="password" type="password" autoComplete="current-password" required /></label>
      <button disabled={busy}>{t("تسجيل الدخول", "Sign in")}</button><p>{t("استخدم حسابًا موجودًا. يمنح المسؤول صلاحية المعلم.", "Use an existing account. Teacher access must be assigned by an administrator.")}</p></form>
    : <>
      <p><bdi>{identity.name}</bdi> · {teacher ? t("معلم", "TEACHER") : t("طالب", "STUDENT")}</p>
      <button disabled={busy} onClick={() => void run(async () => {
        await request("session", "DELETE"); setIdentity(null); setClasses([]); setSelected(null);
        setActive(null); setAnswers({}); setProgress(null); setResults([]); setInvite(""); setAssignments([]);
        setQuestions([{ prompt: "", answer: "" }]);
      })}>{t("تسجيل الخروج", "Sign out")}</button>
      <form method="post" className="lesson-card" onSubmit={(event) => {
        event.preventDefault(); const form = new FormData(event.currentTarget);
        void run(async () => {
          if (teacher) {
            const created = await request<Classroom>("classes", "POST", { name: form.get("value") });
            await refresh(); await open(created); setInvite(created.invite ?? "");
          } else { await request("join", "POST", { invite: form.get("value") }); await refresh(); }
        });
      }}><label>{teacher ? t("اسم الفصل الجديد", "New classroom name") : t("رمز الانضمام للفصل", "Classroom join code")}<input dir={teacher ? "auto" : "ltr"} name="value" maxLength={teacher ? 120 : 128} required /></label>
        <button disabled={busy}>{teacher ? t("إنشاء فصل", "Create classroom") : t("الانضمام للفصل", "Join classroom")}</button></form>
      <nav aria-label={t("فصولك", "Your classrooms")}>{classes.map((item) => <button key={item.id} disabled={busy} onClick={() => void run(() => open(item))}>
        <bdi>{item.name}</bdi>{item.archived ? t(" (مؤرشف)", " (archived)") : ""}</button>)}</nav>
      {progress && <section className="lesson-card"><h3>{t("تقدمك", "Your progress")}</h3><p>{t(`${progress.completed} مكتمل · ${progress.earned}/${progress.possible} نقطة`, `${progress.completed} completed · ${progress.earned}/${progress.possible} points`)}</p>
        {progress.attempts.map((a) => <p key={a.id}><bdi>{a.submitted_at ? `${a.score}/${a.total}` : t("قيد التنفيذ أو منتهي الوقت", "In progress or expired")}</bdi> · {t("الاختبار", "assessment")} <bdi>{a.assignment_id}</bdi></p>)}</section>}
      {selected && <section><h2 dir="auto">{selected.name}</h2>
        {teacher && <div className="lesson-card">
          <form method="post" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); void run(async () => {
            const updated = await request<Classroom>(`classes/${selected.id}`, "PATCH", { name: form.get("name"), archived: form.get("archived") === "on" });
            await refresh(); await open(updated);
          }); }} key={selected.id + selected.name + selected.archived}>
            <label>{t("اسم الفصل", "Classroom name")}<input dir="auto" name="name" defaultValue={selected.name} required maxLength={120} /></label>
            <label><input name="archived" type="checkbox" defaultChecked={selected.archived} /> {t("مؤرشف (تحتفظ المحاولات الحالية بموعدها النهائي)", "Archived (existing attempts keep their deadline)")}</label>
            <button disabled={busy}>{t("حفظ الفصل", "Save classroom")}</button>
          </form>
          <button disabled={busy || selected.archived} onClick={() => void run(async () => setInvite((await request<{ invite: string }>(`classes/${selected.id}/invite`, "POST")).invite))}>{t("استبدال رمز الانضمام", "Replace join code")}</button>
          {invite && <p>{t("شاركه مع طلابك بشكل خاص:", "Share privately with your students:")} <code dir="ltr">{invite}</code></p>}
        </div>}
        {teacher && !selected.archived && <form method="post" className="lesson-card" onSubmit={(event) => {
          event.preventDefault(); const form = new FormData(event.currentTarget);
          void run(async () => {
            await request(`classes/${selected.id}/assignments`, "POST", { title: form.get("title"), lesson: form.get("lesson"), questions,
              duration_minutes: Number(form.get("duration")), original_content_confirmed: form.get("original") === "on" });
            await open(selected); setMessage("Assessment assigned.");
          });
        }}><h3>{t("إسناد درس رياضيات", "Assign a mathematics lesson")}</h3><label>{t("العنوان", "Title")}<input dir="auto" name="title" required maxLength={160} /></label>
          <label>{t("الدرس الأصلي", "Original lesson")}<textarea dir="auto" name="lesson" required maxLength={10000} /></label>
          <label>{t("مدة الاختبار بالدقائق", "Exam duration (minutes)")}<input dir="ltr" name="duration" type="number" min={1} max={180} defaultValue={10} required /></label>
          {questions.map((q, i) => <fieldset key={i}><legend>{t("السؤال", "Question")} {i + 1}</legend>
            <label>{t("السؤال الأصلي", "Original question")}<input dir="auto" value={q.prompt} maxLength={1000} required onChange={(e) => setQuestions(questions.map((v, j) => i === j ? { ...v, prompt: e.target.value } : v))} /></label>
            <label>{t("الإجابة الرقمية", "Numeric answer")}<input dir="ltr" inputMode="decimal" value={q.answer} maxLength={64} required onChange={(e) => setQuestions(questions.map((v, j) => i === j ? { ...v, answer: e.target.value } : v))} /></label>
          </fieldset>)}
          <button type="button" disabled={questions.length >= 30} onClick={() => setQuestions([...questions, { prompt: "", answer: "" }])}>{t("إضافة سؤال", "Add question")}</button>
          <label><input type="checkbox" name="original" required /> {t("أنا مؤلف هذا الدرس وهذه الأسئلة. هذا محتوى أصلي.", "I authored this lesson and these questions. They are original content.")}</label>
          <button disabled={busy}>{t("إسناد الاختبار", "Assign assessment")}</button>
        </form>}
        {assignments.map((task) => <article className="lesson-card" key={task.id}><h3 dir="auto">{task.title}</h3><p dir="auto" style={{ whiteSpace: "pre-wrap" }}><MathText text={task.lesson} /></p>
          <p>{t(`${task.question_count} أسئلة · ${task.duration_minutes} دقائق · محتوى أصلي للمعلم`, `${task.question_count} questions · ${task.duration_minutes} minutes · original teacher content`)}</p>
          {!teacher && <button disabled={busy || selected.archived} onClick={() => void run(async () => {
            const attempt = await request<ClassroomAttempt>(`assignments/${task.id}/start`, "POST");
            setActive({ task: { ...task, questions: attempt.questions ?? [] }, attempt }); setAnswers({});
          })}>{t("بدء / استئناف الاختبار", "Start / resume exam")}</button>}</article>)}
        {active && <form method="post" className="lesson-card" onSubmit={(event) => { event.preventDefault(); void run(async () => {
          const attempt = await request<ClassroomAttempt>(`attempts/${active.attempt.id}/submit`, "POST", { answers });
          setActive({ ...active, attempt }); await refresh(); setMessage(`Result: ${attempt.score}/${attempt.total}`);
        }); }}><h3 dir="auto">{active.task.title}</h3><p>{t("الوقت المتبقي:", "Time remaining:")} <bdi>{Math.max(0, Math.ceil((Date.parse(active.attempt.deadline) - clock) / 1000))}</bdi> {t("ثانية", "seconds")}</p>
          {active.task.questions.map((q) => <label dir="auto" key={q.id}><MathText text={q.prompt} /><input dir="ltr" inputMode="decimal" maxLength={64} required value={answers[q.id] ?? ""}
            disabled={!!active.attempt.submitted_at} onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })} /></label>)}
          {active.attempt.submitted_at ? <p>{t("النتيجة:", "Result:")} <bdi>{active.attempt.score}/{active.attempt.total}</bdi></p> : <button disabled={busy || Date.parse(active.attempt.deadline) <= clock}>{t("إرسال الإجابات النهائية", "Submit final answers")}</button>}
        </form>}
        {teacher && <section className="lesson-card"><h3>{t("نتائج الطلاب", "Student results")}</h3><button disabled={busy} onClick={() => void run(() => open(selected))}>{t("تحديث النتائج", "Refresh results")}</button>
          <table><thead><tr><th>{t("الطالب", "Student")}</th><th>{t("الاختبار", "Assessment")}</th><th>{t("النتيجة", "Result")}</th></tr></thead><tbody>{results.map((r) => <tr key={r.id}>
            <td>{r.student_name} (#{r.student_id})</td><td>{assignments.find((a) => a.id === r.assignment_id)?.title}</td>
            <td><bdi>{r.submitted_at ? `${r.score}/${r.total}` : t("قيد التنفيذ أو منتهي الوقت", "In progress or expired")}</bdi></td></tr>)}</tbody></table>
          {results.length === 0 && <p>{t("لا توجد محاولات بعد.", "No attempts yet.")}</p>}</section>}
      </section>}
    </>}
  </main>;
}
