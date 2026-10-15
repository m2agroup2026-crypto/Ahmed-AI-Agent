"use client";

import { useEffect, useState } from "react";
import type { Classroom, ClassroomAssignment, ClassroomAttempt, ClassroomIdentity, ClassroomProgress } from "@contracts/classroom";

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

  return <main className="shell classroom" dir="ltr">
    <header className="topbar"><div><span className="eyebrow">AQLITH / CLASSROOM</span><h1>Learn together</h1></div><a href="/">Curriculum</a><a href="/classroom/live">Live classes / الحصص المباشرة</a></header>
    <p>Teacher-led mathematics lessons and original timed assessments.</p>
    <p role="status" aria-live="polite">{busy ? "Saving…" : message}</p>
    {!identity ? <form className="lesson-card" onSubmit={(event) => {
      event.preventDefault(); const form = new FormData(event.currentTarget);
      void run(async () => {
        await request("session", "POST", { email: form.get("email"), password: form.get("password") });
        const person = await request<ClassroomIdentity>("me"); setIdentity(person); await refresh(person);
      });
    }}><h3>Sign in</h3><label>Email<input name="email" type="email" autoComplete="username" required /></label>
      <label>Password<input name="password" type="password" autoComplete="current-password" required /></label>
      <button disabled={busy}>Sign in</button><p>Use an existing account. Teacher access must be assigned by an administrator.</p></form>
    : <>
      <p>{identity.name} · {identity.role}</p>
      <button disabled={busy} onClick={() => void run(async () => {
        await request("session", "DELETE"); setIdentity(null); setClasses([]); setSelected(null);
        setActive(null); setAnswers({}); setProgress(null); setResults([]); setInvite(""); setAssignments([]);
        setQuestions([{ prompt: "", answer: "" }]);
      })}>Sign out</button>
      <form className="lesson-card" onSubmit={(event) => {
        event.preventDefault(); const form = new FormData(event.currentTarget);
        void run(async () => {
          if (teacher) {
            const created = await request<Classroom>("classes", "POST", { name: form.get("value") });
            await refresh(); await open(created); setInvite(created.invite ?? "");
          } else { await request("join", "POST", { invite: form.get("value") }); await refresh(); }
        });
      }}><label>{teacher ? "New classroom name" : "Classroom join code"}<input name="value" maxLength={teacher ? 120 : 128} required /></label>
        <button disabled={busy}>{teacher ? "Create classroom" : "Join classroom"}</button></form>
      <nav aria-label="Your classrooms">{classes.map((item) => <button key={item.id} disabled={busy} onClick={() => void run(() => open(item))}>
        {item.name}{item.archived ? " (archived)" : ""}</button>)}</nav>
      {progress && <section className="lesson-card"><h3>Your progress</h3><p>{progress.completed} completed · {progress.earned}/{progress.possible} points</p>
        {progress.attempts.map((a) => <p key={a.id}>{a.submitted_at ? `${a.score}/${a.total}` : "In progress or expired"} · assessment {a.assignment_id}</p>)}</section>}
      {selected && <section><h2>{selected.name}</h2>
        {teacher && <div className="lesson-card">
          <form onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); void run(async () => {
            const updated = await request<Classroom>(`classes/${selected.id}`, "PATCH", { name: form.get("name"), archived: form.get("archived") === "on" });
            await refresh(); await open(updated);
          }); }} key={selected.id + selected.name + selected.archived}>
            <label>Classroom name<input name="name" defaultValue={selected.name} required maxLength={120} /></label>
            <label><input name="archived" type="checkbox" defaultChecked={selected.archived} /> Archived (existing attempts keep their deadline)</label>
            <button disabled={busy}>Save classroom</button>
          </form>
          <button disabled={busy || selected.archived} onClick={() => void run(async () => setInvite((await request<{ invite: string }>(`classes/${selected.id}/invite`, "POST")).invite))}>Replace join code</button>
          {invite && <p>Share privately with your students: <code>{invite}</code></p>}
        </div>}
        {teacher && !selected.archived && <form className="lesson-card" onSubmit={(event) => {
          event.preventDefault(); const form = new FormData(event.currentTarget);
          void run(async () => {
            await request(`classes/${selected.id}/assignments`, "POST", { title: form.get("title"), lesson: form.get("lesson"), questions,
              duration_minutes: Number(form.get("duration")), original_content_confirmed: form.get("original") === "on" });
            await open(selected); setMessage("Assessment assigned.");
          });
        }}><h3>Assign a mathematics lesson</h3><label>Title<input name="title" required maxLength={160} /></label>
          <label>Original lesson<textarea name="lesson" required maxLength={10000} /></label>
          <label>Exam duration (minutes)<input name="duration" type="number" min={1} max={180} defaultValue={10} required /></label>
          {questions.map((q, i) => <fieldset key={i}><legend>Question {i + 1}</legend>
            <label>Original question<input value={q.prompt} maxLength={1000} required onChange={(e) => setQuestions(questions.map((v, j) => i === j ? { ...v, prompt: e.target.value } : v))} /></label>
            <label>Numeric answer<input value={q.answer} maxLength={64} required onChange={(e) => setQuestions(questions.map((v, j) => i === j ? { ...v, answer: e.target.value } : v))} /></label>
          </fieldset>)}
          <button type="button" disabled={questions.length >= 30} onClick={() => setQuestions([...questions, { prompt: "", answer: "" }])}>Add question</button>
          <label><input type="checkbox" name="original" required /> I authored this lesson and these questions. They are original content.</label>
          <button disabled={busy}>Assign assessment</button>
        </form>}
        {assignments.map((task) => <article className="lesson-card" key={task.id}><h3>{task.title}</h3><p style={{ whiteSpace: "pre-wrap" }}>{task.lesson}</p>
          <p>{task.question_count} questions · {task.duration_minutes} minutes · original teacher content</p>
          {!teacher && <button disabled={busy || selected.archived} onClick={() => void run(async () => {
            const attempt = await request<ClassroomAttempt>(`assignments/${task.id}/start`, "POST");
            setActive({ task: { ...task, questions: attempt.questions ?? [] }, attempt }); setAnswers({});
          })}>Start / resume exam</button>}</article>)}
        {active && <form className="lesson-card" onSubmit={(event) => { event.preventDefault(); void run(async () => {
          const attempt = await request<ClassroomAttempt>(`attempts/${active.attempt.id}/submit`, "POST", { answers });
          setActive({ ...active, attempt }); await refresh(); setMessage(`Result: ${attempt.score}/${attempt.total}`);
        }); }}><h3>{active.task.title}</h3><p>Time remaining: {Math.max(0, Math.ceil((Date.parse(active.attempt.deadline) - clock) / 1000))} seconds</p>
          {active.task.questions.map((q) => <label key={q.id}>{q.prompt}<input maxLength={64} required value={answers[q.id] ?? ""}
            disabled={!!active.attempt.submitted_at} onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })} /></label>)}
          {active.attempt.submitted_at ? <p>Result: {active.attempt.score}/{active.attempt.total}</p> : <button disabled={busy || Date.parse(active.attempt.deadline) <= clock}>Submit final answers</button>}
        </form>}
        {teacher && <section className="lesson-card"><h3>Student results</h3><button disabled={busy} onClick={() => void run(() => open(selected))}>Refresh results</button>
          <table><thead><tr><th>Student</th><th>Assessment</th><th>Result</th></tr></thead><tbody>{results.map((r) => <tr key={r.id}>
            <td>{r.student_name} (#{r.student_id})</td><td>{assignments.find((a) => a.id === r.assignment_id)?.title}</td>
            <td>{r.submitted_at ? `${r.score}/${r.total}` : "In progress or expired"}</td></tr>)}</tbody></table>
          {results.length === 0 && <p>No attempts yet.</p>}</section>}
      </section>}
    </>}
  </main>;
}
