import type { ContentLanguage, CurriculumCatalogVersion, CurriculumUnit, LessonSummary, PracticeQuestion } from "@contracts/tutor";

export function copy(locale: string, ar: string, en: string) {
  return locale.startsWith("ar") ? ar : en;
}

export function readingStyle(locale: string) {
  return locale.startsWith("ar")
    ? { writingDirection: "rtl" as const, textAlign: "right" as const }
    : { writingDirection: "ltr" as const, textAlign: "left" as const };
}

// Official content follows its declared language, independently of UI locale.
export function officialText(language: ContentLanguage | null, ar: string, en: string) {
  return language === "ar" ? ar : language === "en" ? en : null;
}

export function officialQuestion(question: PracticeQuestion) {
  const language = question.content_language;
  if (language !== "ar" && language !== "en") return null;
  return { language, prompt: officialText(language, question.prompt_ar, question.prompt_en),
    choices: language === "ar" ? question.options_ar : question.options_en };
}

export function officialAnswerLocale(question: Pick<PracticeQuestion, "content_language">) {
  return question.content_language === "ar" ? "ar-EG" : question.content_language === "en" ? "en-US" : null;
}

export function officialUnitTitle(unit: CurriculumUnit) {
  return officialText(unit.content_language, unit.title_ar, unit.title_en);
}

export function officialCurriculumTitle(catalog: CurriculumCatalogVersion) {
  return officialText(catalog.content_language, catalog.title_ar, catalog.title_en) ?? catalog.code;
}

export function hasUndeclaredMathContent(lessons: LessonSummary[], version: string) {
  return lessons.some(lesson => lesson.subject_code === "mathematics" &&
    lesson.curriculum_version === version && !lesson.content_language);
}
