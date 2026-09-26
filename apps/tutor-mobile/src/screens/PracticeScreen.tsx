import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import type { PracticeAttemptResult, PracticeQuestion, TutorSubject } from "@contracts/tutor";
import { TutorApi } from "../api/client";
import { theme } from "../theme";

type Props = {
  api: TutorApi;
  subjectCode: TutorSubject;
  curriculumVersion: string;
  lessonId?: string;
  onBack: () => void;
};

export function PracticeScreen({ api, subjectCode, curriculumVersion, lessonId, onBack }: Props) {
  const [question, setQuestion] = useState<PracticeQuestion | null>(null);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<PracticeAttemptResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadQuestion = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setAnswer("");
    try {
      const next = await api.nextPracticeQuestion(subjectCode, curriculumVersion, lessonId);
      setQuestion(next);
    } catch (reason) {
      setQuestion(null);
      setError(reason instanceof Error ? reason.message : "تعذر تحميل السؤال");
    } finally {
      setLoading(false);
    }
  }, [api, curriculumVersion, lessonId, subjectCode]);

  useEffect(() => {
    void loadQuestion();
  }, [loadQuestion]);

  async function submit() {
    if (!question || !answer.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const submitted = await api.submitPracticeAttempt(question.id, answer.trim(), "ar-EG");
      setResult(submitted);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تعذر حفظ المحاولة");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <View style={styles.screen}>
      <View style={styles.header}>
        <Pressable onPress={onBack} accessibilityLabel="العودة">
          <Text style={styles.back}>›</Text>
        </Pressable>
        <View style={styles.headerCopy}>
          <Text style={styles.eyebrow}>NEXORA PRACTICE</Text>
          <Text style={styles.title}>تدرّب بفهم</Text>
        </View>
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        {loading && <ActivityIndicator color={theme.colors.teal} size="large" />}
        {error && <Text style={styles.error}>{error}</Text>}
        {!loading && question && (
          <View style={styles.questionCard}>
            <View style={styles.metaRow}>
              <Text style={styles.source}>محتوى موثّق من المنهج</Text>
              <Text style={styles.points}>{question.source_locator}</Text>
            </View>
            <Text style={styles.prompt}>{question.prompt_ar}</Text>
            {question.question_type === "single_choice" && question.choices_ar.length > 0 ? (
              question.choices_ar.map((choice, index) => {
                const selected = answer === choice;
                return (
                  <Pressable
                    key={`${choice}-${index}`}
                    style={[styles.choice, selected && styles.choiceSelected]}
                    onPress={() => setAnswer(choice)}
                    accessibilityRole="radio"
                    accessibilityState={{ selected }}
                  >
                    <Text style={[styles.choiceText, selected && styles.choiceTextSelected]}>{choice}</Text>
                  </Pressable>
                );
              })
            ) : (
              <TextInput
                value={answer}
                onChangeText={setAnswer}
                placeholder="اكتب إجابتك..."
                placeholderTextColor={theme.colors.muted}
                style={styles.input}
                textAlign="right"
              />
            )}
            {!result ? (
              <Pressable style={styles.submit} onPress={submit} disabled={!answer.trim() || submitting}>
                {submitting ? <ActivityIndicator color={theme.colors.white} /> : <Text style={styles.submitText}>تحقق من الإجابة</Text>}
              </Pressable>
            ) : (
              <View style={[styles.result, result.is_correct ? styles.resultCorrect : styles.resultReview]}>
                <Text style={styles.resultTitle}>{result.is_correct ? "إجابة صحيحة" : "نراجع الفكرة مرة أخرى"}</Text>
                <Text style={styles.resultText}>{result.explanation_ar}</Text>
                <Text style={styles.resultSource}>المصدر: {result.source_locator}</Text>
                <Pressable style={styles.next} onPress={() => void loadQuestion()}>
                  <Text style={styles.nextText}>سؤال آخر</Text>
                </Pressable>
              </View>
            )}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.colors.surface },
  header: { backgroundColor: theme.colors.navy, padding: 20, paddingTop: 58, flexDirection: "row", alignItems: "center" },
  back: { color: theme.colors.white, fontSize: 34, transform: [{ rotate: "180deg" }] },
  headerCopy: { flex: 1, marginLeft: 12 },
  eyebrow: { color: theme.colors.gold, fontSize: 11, fontWeight: "800", letterSpacing: 1.5, textAlign: "right" },
  title: { color: theme.colors.white, fontSize: 24, fontWeight: "800", textAlign: "right", marginTop: 4 },
  content: { padding: 20, paddingBottom: 40 },
  questionCard: { backgroundColor: theme.colors.white, borderRadius: 24, padding: 20 },
  metaRow: { flexDirection: "row-reverse", justifyContent: "space-between", alignItems: "center" },
  source: { color: theme.colors.teal, fontSize: 12, fontWeight: "800" },
  points: { color: theme.colors.muted, fontSize: 11 },
  prompt: { color: theme.colors.ink, fontSize: 21, lineHeight: 32, fontWeight: "800", textAlign: "right", marginVertical: 24 },
  choice: { borderWidth: 1, borderColor: "#d5dfe8", borderRadius: 14, padding: 15, marginBottom: 10 },
  choiceSelected: { borderColor: theme.colors.teal, backgroundColor: "#e7f5f2" },
  choiceText: { color: theme.colors.ink, fontSize: 16, textAlign: "right" },
  choiceTextSelected: { color: theme.colors.teal, fontWeight: "800" },
  input: { minHeight: 52, borderWidth: 1, borderColor: "#d5dfe8", borderRadius: 14, paddingHorizontal: 14, color: theme.colors.ink, marginBottom: 14 },
  submit: { backgroundColor: theme.colors.teal, borderRadius: 14, minHeight: 52, justifyContent: "center", alignItems: "center", marginTop: 8 },
  submitText: { color: theme.colors.white, fontWeight: "800", fontSize: 15 },
  result: { borderRadius: 16, padding: 16, marginTop: 14 },
  resultCorrect: { backgroundColor: "#e7f5f2" },
  resultReview: { backgroundColor: "#fff4df" },
  resultTitle: { color: theme.colors.ink, fontSize: 17, fontWeight: "800", textAlign: "right" },
  resultText: { color: theme.colors.ink, fontSize: 15, lineHeight: 25, textAlign: "right", marginTop: 7 },
  resultSource: { color: theme.colors.muted, fontSize: 11, textAlign: "right", marginTop: 9 },
  next: { backgroundColor: theme.colors.navy, borderRadius: 12, padding: 13, alignItems: "center", marginTop: 14 },
  nextText: { color: theme.colors.white, fontWeight: "800" },
  error: { color: theme.colors.danger, textAlign: "right", lineHeight: 22 },
});
