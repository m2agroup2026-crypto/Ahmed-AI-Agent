"use client";

import { useEffect, useState } from "react";

import type { LessonSummary } from "@contracts/tutor";
import { usePreferences } from "./preferences";
import { declaredText, contentDirection } from "../../../packages/presentation/content";
import { MathText } from "./math-text";

export default function TutorWebHome() {
  const { language, t } = usePreferences();
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
        <a href="/classroom">{t("فصول المعلمين والطلاب", "Teacher & student classrooms")}</a>
        <div>
          <span className="eyebrow">AQLITH / LEARN</span>
          <h1>{t("مركز متابعة التعلم", "Learning companion")}</h1>
        </div>
        <span className="status">{t("محتوى منهجي", "Curriculum content")}</span>
      </header>

      <section className="hero">
        <div>
          <span className="eyebrow gold">{t("رفيق متابعة التعلم", "LEARNING COMPANION")}</span>
          <h2>{t("تعلم الطالب يبدأ من الهاتف، والمتابعة تبدأ من هنا.", "Learning starts on your phone. Follow your progress here.")}</h2>
          <p>{t("واجهة ويب هادئة لعرض المنهج المتاح وربط المتابعة بتقدم حقيقي بعد تسجيل الدخول.", "Browse available curriculum and follow real learning progress after signing in.")}</p>
        </div>
      </section>

      <section className="section">
        <div className="section-heading">
          <div>
            <span className="eyebrow teal">{t("المنهج", "CURRICULUM")}</span>
            <h3>{t("الدروس المتاحة", "Available lessons")}</h3>
          </div>
          <span className="hint">{t("المحتوى المتاح لحسابك", "Content available for your account")}</span>
        </div>

        {state === "signed_out" && <EmptyState text={t("سجّل الدخول لعرض منهج الطالب المرتبط بحسابك.", "Sign in to see the curriculum available for your account.")} />}
        {state === "loading" && <EmptyState text={t("جارٍ تحميل المنهج...", "Loading curriculum…")} />}
        {state === "error" && <EmptyState text={t("تعذر الوصول إلى المنهج حاليًا.", "Curriculum is currently unavailable.")} danger />}
        {state === "ready" && lessons.length === 0 && <EmptyState text={t("لا توجد دروس متاحة للحساب الحالي.", "No lessons are available for this account.")} />}
        {state === "ready" && lessons.length > 0 && (
          <div className="grid">
            {lessons.map((lesson) => (
              <article className="lesson-card" key={lesson.id}>
                <span className="subject">{subjectLabel(lesson.subject_code, language)}</span>
                <h4 dir={contentDirection(lesson.content_language)}><MathText text={declaredText(lesson.content_language, lesson.title_ar, lesson.title_en) ?? t("لغة المحتوى غير محددة", "Content language is not declared")} /></h4>
                <p dir={contentDirection(lesson.content_language)}><MathText text={declaredText(lesson.content_language, lesson.summary_ar, lesson.summary_en) ?? ""} /></p>
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

function subjectLabel(subject: LessonSummary["subject_code"], language: "ar" | "en") {
  return language === "ar" ? { mathematics: "رياضيات", physics: "فيزياء", english: "الإنجليزية" }[subject]
    : { mathematics: "Mathematics", physics: "Physics", english: "English" }[subject];
}
