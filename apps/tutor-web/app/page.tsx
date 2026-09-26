"use client";

import { useEffect, useState } from "react";

import type { LessonSummary } from "@contracts/tutor";

export default function TutorWebHome() {
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "signed_out" | "error">("loading");

  useEffect(() => {
    fetch("/api/tutor/lessons")
      .then(async (response) => {
        if (response.status === 401) {
          setState("signed_out");
          return null;
        }
        if (!response.ok) throw new Error("Tutor API request failed");
        return response.json() as Promise<LessonSummary[]>;
      })
      .then((items) => {
        if (!items) return;
        setLessons(items);
        setState("ready");
      })
      .catch(() => setState("error"));
  }, []);

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <span className="eyebrow">NEXORA / TUTOR</span>
          <h1>مركز متابعة التعلم</h1>
        </div>
        <span className="status">محتوى منهجي</span>
      </header>

      <section className="hero">
        <div>
          <span className="eyebrow gold">GUARDIAN COMPANION</span>
          <h2>تعلم الطالب يبدأ من الهاتف، والمتابعة تبدأ من هنا.</h2>
          <p>واجهة ويب هادئة لعرض المنهج المتاح وربط المتابعة بتقدم حقيقي بعد تسجيل الدخول.</p>
        </div>
        <div className="hero-mark">N</div>
      </section>

      <section className="section">
        <div className="section-heading">
          <div>
            <span className="eyebrow teal">LIVE CURRICULUM</span>
            <h3>الدروس المتاحة</h3>
          </div>
          <span className="hint">تظهر من Tutor API فقط</span>
        </div>

        {state === "signed_out" && <EmptyState text="سجّل الدخول لعرض منهج الطالب المرتبط بحسابك." />}
        {state === "loading" && <EmptyState text="جارٍ تحميل المنهج..." />}
        {state === "error" && <EmptyState text="تعذر الوصول إلى Tutor API حاليًا." danger />}
        {state === "ready" && lessons.length === 0 && <EmptyState text="لا توجد دروس متاحة للحساب الحالي." />}
        {state === "ready" && lessons.length > 0 && (
          <div className="grid">
            {lessons.map((lesson) => (
              <article className="lesson-card" key={lesson.id}>
                <span className="subject">{subjectLabel(lesson.subject_code)}</span>
                <h4>{lesson.title_ar}</h4>
                <p>{lesson.summary_ar}</p>
                <span className="version">{lesson.curriculum_version}</span>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

function EmptyState({ text, danger = false }: { text: string; danger?: boolean }) {
  return <div className={`empty ${danger ? "danger" : ""}`}>{text}</div>;
}

function subjectLabel(subject: LessonSummary["subject_code"]) {
  return { mathematics: "رياضيات", physics: "فيزياء", english: "English" }[subject];
}
