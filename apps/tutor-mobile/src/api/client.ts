import type {
  LessonSummary,
  PracticeAttemptResult,
  PracticeQuestion,
  TutorMessageExchange,
  TutorSessionMessage,
  TutorProfile,
  TutorSession,
  TutorSubject,
} from "@contracts/tutor";

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

export class TutorApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
  }
}

export class TutorApi {
  constructor(private readonly token: string) {}

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.token}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      throw new TutorApiError(response.status, body?.detail ?? "Tutor request failed");
    }

    return response.json() as Promise<T>;
  }

  lessons(subjectCode?: TutorSubject, curriculumVersion?: string) {
    const params = new URLSearchParams();
    if (subjectCode) params.set("subject_code", subjectCode);
    if (curriculumVersion) params.set("curriculum_version", curriculumVersion);
    const query = params.toString() ? `?${params.toString()}` : "";
    return this.request<LessonSummary[]>(`/api/v1/tutor/lessons${query}`);
  }

  profile() {
    return this.request<TutorProfile>("/api/v1/tutor/profile");
  }

  saveProfile(payload: {
    grade_level: string;
    locale: string;
    subject_codes: TutorSubject[];
    learning_preferences?: Record<string, unknown>;
  }) {
    return this.request<TutorProfile>("/api/v1/tutor/profile", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  }

  startSession(subject_code: TutorSubject, curriculum_version = "egypt-secondary-2026") {
    return this.request<TutorSession>("/api/v1/tutor/sessions", {
      method: "POST",
      body: JSON.stringify({ subject_code, curriculum_version }),
    });
  }

  nextPracticeQuestion(
    subjectCode: TutorSubject,
    curriculumVersion = "egypt-secondary-2026",
    lessonId?: string,
    skillCode?: string,
  ) {
    const params = new URLSearchParams({
      subject_code: subjectCode,
      curriculum_version: curriculumVersion,
    });
    if (lessonId) params.set("lesson_id", lessonId);
    if (skillCode) params.set("skill_code", skillCode);
    return this.request<PracticeQuestion>(`/api/v1/tutor/practice/next?${params.toString()}`);
  }

  submitPracticeAttempt(
    questionId: string,
    submittedAnswer: string,
    locale = "ar-EG",
    sessionId?: string,
  ) {
    return this.request<PracticeAttemptResult>("/api/v1/tutor/practice/attempts", {
      method: "POST",
      body: JSON.stringify({
        question_id: questionId,
        submitted_answer: submittedAnswer,
        locale,
        session_id: sessionId,
      }),
    });
  }

  sendMessage(sessionId: string, content: string, lessonId?: string, locale = "ar-EG") {
    return this.request<TutorMessageExchange>(`/api/v1/tutor/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, lesson_id: lessonId, locale }),
    });
  }

  messages(sessionId: string) {
    return this.request<TutorSessionMessage[]>(`/api/v1/tutor/sessions/${sessionId}/messages`);
  }
}
