export type TutorSubject = "mathematics" | "physics" | "english";

export interface TutorProfile {
  id: number;
  user_id: number;
  grade_level: string;
  locale: string;
  subject_codes: TutorSubject[];
  learning_preferences: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface LessonSummary {
  id: string;
  subject_code: TutorSubject;
  title_ar: string;
  title_en: string;
  summary_ar: string;
  summary_en: string;
  skill_codes: string[];
  curriculum_version: string;
  source_id?: string | null;
  source_name_ar?: string | null;
  source_name_en?: string | null;
  source_url?: string | null;
  source_locator?: string | null;
  source_status?: string | null;
}

export interface TutorSession {
  id: string;
  user_id: number;
  subject_code: TutorSubject;
  curriculum_version: string;
  status: "active" | "completed" | "paused";
  created_at: string;
  updated_at: string;
}

export interface TutorMessage {
  id: number;
  role: "learner" | "tutor";
  content: string;
  lesson_id: string | null;
  created_at: string;
}

export interface TutorMessageExchange {
  learner_message: TutorMessage;
  tutor_message: TutorMessage | null;
  answer: {
    status: "curriculum_context" | "needs_context";
    content: string;
    source_lesson_id: string | null;
    source_title: string | null;
    source_url?: string | null;
    source_locator?: string | null;
    adaptation_mode?: "standard" | "concise" | string;
    next_action?: "practice" | "continue" | string | null;
  };
}

export interface PracticeQuestion {
  id: string;
  lesson_id: string;
  subject_code: TutorSubject;
  skill_code: string | null;
  question_type: string;
  prompt_ar: string;
  prompt_en: string;
  choices_ar: string[];
  choices_en: string[];
  curriculum_version: string;
  source_url: string;
  source_locator: string;
  source_status: string;
}

export interface PracticeAttemptResult {
  attempt_id: string;
  question_id: string;
  is_correct: boolean;
  score: number;
  max_score: number;
  explanation_ar: string;
  explanation_en: string;
  source_url: string;
  source_locator: string;
  next_action: "continue" | "review" | string;
}

export interface ProgressSkill {
  skill_code: string;
  attempts: number;
  correct_answers: number;
  score: number;
  max_score: number;
  accuracy_percent: number;
}

export interface TutorProgress {
  curriculum_version: string | null;
  subject_code: TutorSubject | null;
  attempts: number;
  correct_answers: number;
  score: number;
  max_score: number;
  accuracy_percent: number;
  skills: ProgressSkill[];
  next_focus_skill: string | null;
  last_activity_at: string | null;
}

export type TutorSessionMessage = TutorMessage;
