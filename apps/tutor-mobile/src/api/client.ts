import type {
  LessonSummary,
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

  lessons(subjectCode?: TutorSubject) {
    const query = subjectCode ? `?subject_code=${encodeURIComponent(subjectCode)}` : "";
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

  startSession(subject_code: TutorSubject) {
    return this.request<TutorSession>("/api/v1/tutor/sessions", {
      method: "POST",
      body: JSON.stringify({ subject_code }),
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
