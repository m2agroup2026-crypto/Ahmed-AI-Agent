export type Classroom = { id: string; name: string; archived: boolean; invite?: string };
export type ClassroomIdentity = { id: number; name: string; role: string };
export type ClassroomAssignment = {
  id: string; classroom_id: string; title: string; lesson: string;
  duration_minutes: number; provenance: string;
  question_count: number;
  questions: { id: string; prompt: string }[];
};
export type ClassroomAttempt = {
  id: string; assignment_id: string; student_id: number; student_name?: string;
  started_at: string; deadline: string; submitted_at: string | null;
  score: number | null; total: number;
  questions?: { id: string; prompt: string }[];
};
export type ClassroomProgress = {
  attempts: ClassroomAttempt[]; completed: number; earned: number; possible: number;
};
