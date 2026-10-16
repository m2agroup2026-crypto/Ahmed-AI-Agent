export const voiceLocales = ["ar-EG", "en-US", "fr-FR"] as const;
export type VoiceLocale = typeof voiceLocales[number];
export type VoiceAction = "home" | "math_lessons" | "practice" | "progress" | "classrooms" | "teacher_classrooms";
export type VoiceCommand = { kind: "navigate"; action: VoiceAction } | { kind: "tutor"; question: string } | { kind: "unknown" };
export const MAX_TRANSCRIPT = 1000;
export const MAX_RECORDING_MS = 15_000;

export function normalizeCommand(text: string): string {
  return text.normalize("NFKC").replace(/[\u064B-\u065F\u0670\u0640]/g, "")
    .replace(/[أإآ]/g, "ا").replace(/ى/g, "ي").toLowerCase()
    .replace(/[،,؟?!。.]/g, " ").replace(/\s+/g, " ").trim()
    .replace(/^(?:يا اكليث|اكليث|hey aqlith|aqlith)\s*/, "").trim();
}
const aliases: Record<VoiceAction, readonly string[]> = {
  home: ["ارجع للصفحه الرئيسيه", "ارجع للصفحة الرئيسية", "افتح الرئيسية", "go home", "open home", "accueil"],
  math_lessons: ["افتح دروس الرياضيات", "open math lessons", "ouvre les cours de maths"],
  practice: ["افتح التدريبات", "open practice", "ouvre les exercices"],
  progress: ["وريني تقدمي", "show my progress", "montre mes progres", "montre mes progrès"],
  classrooms: ["افتح الفصل بتاعي", "open my classroom", "ouvre ma classe"],
  teacher_classrooms: ["افتح فصولي كمدرس", "open teacher classrooms", "ouvre mes classes enseignant"],
};
export function parseVoiceCommand(text: string): VoiceCommand {
  if (!text.trim() || text.length > MAX_TRANSCRIPT) return { kind: "unknown" };
  const normalized = normalizeCommand(text);
  for (const [action, phrases] of Object.entries(aliases)) {
    if (phrases.some(phrase => normalizeCommand(phrase) === normalized)) return { kind: "navigate", action: action as VoiceAction };
  }
  // Only an explicit question prefix enters Tutor. Preserve the exact mathematical text.
  if (/^(?:اشرحلي|اشرح لي|explain|explique)\s+\S/i.test(text.trim())) {
    return { kind: "tutor", question: text.trim() };
  }
  return { kind: "unknown" };
}
export function canExecute(command: VoiceCommand, verifiedRole: string | null): boolean {
  if (command.kind === "unknown") return false;
  return command.kind !== "navigate" || command.action !== "teacher_classrooms" || verifiedRole === "TEACHER";
}
