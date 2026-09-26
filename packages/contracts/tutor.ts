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
  };
}

export type TutorSessionMessage = TutorMessage;
