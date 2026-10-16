import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { Text, TextInput } from "../typography";

import type { PracticeAttemptResult, PracticeQuestion, TutorSubject } from "@contracts/tutor";
import { TutorApi } from "../api/client";
import { useThemedStyles, type Theme } from "../theme";
import { usePreferences } from "../preferences";
import { officialAnswerLocale, officialQuestion, officialText, readingStyle } from "../learning";
import { isolateMath } from "../../../../packages/presentation/content";

type Props = {
  api: TutorApi;
  subjectCode: TutorSubject;
  curriculumVersion: string;
  lessonId?: string;
  skillCode?: string;
  onBack: () => void;
};

export function PracticeScreen({ api, subjectCode, curriculumVersion, lessonId, skillCode, onBack }: Props) {
  const { theme, t, language, rtl } = usePreferences();
  const styles = useThemedStyles(createStyles);
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
      const next = await api.nextPracticeQuestion(subjectCode, curriculumVersion, lessonId, skillCode);
      setQuestion(next);
    } catch (reason) {
      setQuestion(null);
      setError(reason instanceof Error ? reason.message : "تعذر تحميل السؤال");
    } finally {
      setLoading(false);
    }
  }, [api, curriculumVersion, lessonId, skillCode, subjectCode]);

  useEffect(() => {
    void loadQuestion();
  }, [loadQuestion]);

  async function submit() {
    if (!question || !answer.trim() || submitting) return;
    const locale = officialAnswerLocale(question);
    if (!locale) { setError("لغة المحتوى غير محددة؛ تعذر إرسال الإجابة."); return; }
    setSubmitting(true);
    setError(null);
    try {
      const submitted = await api.submitPracticeAttempt(question.id, answer.trim(), locale);
      setResult(submitted);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تعذر حفظ المحاولة");
    } finally {
      setSubmitting(false);
    }
  }

  const official = question ? officialQuestion(question) : null;
  const contentStyle = readingStyle(official?.language === "en" ? "en-US" : "ar-EG");
  return (
    <View style={styles.screen}>
      <View style={styles.header}>
        <Pressable onPress={onBack} accessibilityRole="button" accessibilityLabel={t("العودة", "Back")} style={{ minHeight: 44, minWidth: 44, alignItems: "center" }}>
          <Text style={styles.back}>›</Text>
        </Pressable>
        <View style={styles.headerCopy}>
          <Text style={styles.eyebrow}>AQLITH Learn Practice</Text>
          <Text style={styles.title}>{t("تدرّب بفهم", "Practice with understanding")}</Text>
        </View>
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        {loading && <ActivityIndicator color={theme.colors.primary} size="large" />}
        {error && <Text accessibilityRole="alert" style={styles.error}>{t("تعذر تنفيذ التدريب. تحقق من الاتصال والمنهج ثم أعد المحاولة.", "Practice could not be completed. Check your connection and curriculum, then retry.")}</Text>}
        {!loading && question && !official && <Text accessibilityRole="alert" style={styles.error}>{t("لغة المحتوى غير محددة؛ يرجى مراجعة المنهج.", "Content language is not declared. Please check the curriculum.")}</Text>}
        {!loading && question && official && (
          <View style={styles.questionCard}>
            <View style={styles.metaRow}>
              <Text style={styles.source}>{t("مصدر المنهج", "Curriculum source")}</Text>
              <Text style={styles.points}>{question.source_locator}</Text>
            </View>
            <Text style={[styles.prompt, contentStyle]}>{isolateMath(official.prompt ?? "")}</Text>
            {question.question_type === "single_choice" && official.choices.length > 0 ? (
              official.choices.map((choice) => {
                const selected = answer === choice.id;
                return (
                  <Pressable
                    key={choice.id}
                    style={[styles.choice, selected && styles.choiceSelected]}
                    onPress={() => setAnswer(choice.id)}
                    accessibilityRole="radio"
                    accessibilityState={{ selected }}
                  >
                    <Text style={[styles.choiceText, contentStyle, selected && styles.choiceTextSelected]}>{isolateMath(choice.label)}</Text>
                  </Pressable>
                );
              })
            ) : (
              <TextInput
                value={answer}
                onChangeText={setAnswer}
                placeholder={t("اكتب إجابتك...", "Enter your answer...")}
                accessibilityLabel={t("إجابتك", "Your answer")}
                placeholderTextColor={theme.colors.muted}
                style={styles.input}
                textAlign="left"
              />
            )}
            {!result ? (
              <Pressable accessibilityRole="button" style={styles.submit} onPress={submit} disabled={!answer.trim() || submitting}>
                {submitting ? <ActivityIndicator color={theme.colors.onPrimary} /> : <Text style={styles.submitText}>{t("تحقق من الإجابة", "Check answer")}</Text>}
              </Pressable>
            ) : (
              <View style={[styles.result, result.is_correct ? styles.resultCorrect : styles.resultReview]}>
                <Text style={styles.resultTitle}>{result.is_correct ? t("إجابة صحيحة", "Correct answer") : t("نراجع الفكرة مرة أخرى", "Let’s review the idea")}</Text>
                <Text style={[styles.resultText, readingStyle(result.content_language ?? language)]}>{isolateMath(officialText(result.content_language, result.explanation_ar, result.explanation_en) ?? t("لغة المحتوى غير محددة", "Content language is not declared"))}</Text>
                <Text style={styles.resultSource}>{t("المصدر:", "Source:")} {result.source_locator}</Text>
                <Pressable accessibilityRole="button" style={styles.next} onPress={() => void loadQuestion()}>
                  <Text style={styles.nextText}>{t("سؤال آخر", "Next question")}</Text>
                </Pressable>
              </View>
            )}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const createStyles = (theme: Theme, rtl: boolean) => StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.colors.background },
  header: { backgroundColor: theme.colors.hero, padding: 20, paddingTop: 58, flexDirection: rtl ? "row-reverse" : "row", alignItems: "center" },
  back: { color: theme.colors.heroText, fontSize: 34, transform: [{ rotate: rtl ? "0deg" : "180deg" }] },
  headerCopy: { flex: 1, marginLeft: 12 },
  eyebrow: { color: theme.colors.heroAccent, fontSize: 11, fontWeight: "800", letterSpacing: 1.5, textAlign: rtl ? "right" : "left" },
  title: { color: theme.colors.heroText, fontSize: 24, fontWeight: "800", textAlign: rtl ? "right" : "left", marginTop: 4 },
  content: { padding: 20, paddingBottom: 40 },
  questionCard: { backgroundColor: theme.colors.surface, borderRadius: 24, padding: 20 },
  metaRow: { flexDirection: rtl ? "row-reverse" : "row", flexWrap: "wrap", gap: 8, justifyContent: "space-between", alignItems: "center" },
  source: { color: theme.colors.primary, fontSize: 12, fontWeight: "800" },
  points: { color: theme.colors.muted, fontSize: 11 },
  prompt: { color: theme.colors.text, fontSize: 21, lineHeight: 32, fontWeight: "800", textAlign: rtl ? "right" : "left", marginVertical: 24 },
  choice: { minHeight: 48, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 14, padding: 15, marginBottom: 10 },
  choiceSelected: { borderColor: theme.colors.primary, backgroundColor: theme.colors.successSurface },
  choiceText: { color: theme.colors.text, fontSize: 16, textAlign: rtl ? "right" : "left" },
  choiceTextSelected: { color: theme.colors.primary, fontWeight: "800" },
  input: { minHeight: 52, borderWidth: 1, borderColor: theme.colors.border, borderRadius: 14, paddingHorizontal: 14, color: theme.colors.text, writingDirection: "ltr", marginBottom: 14 },
  submit: { backgroundColor: theme.colors.primary, borderRadius: 14, minHeight: 52, justifyContent: "center", alignItems: "center", marginTop: 8 },
  submitText: { color: theme.colors.onPrimary, fontWeight: "800", fontSize: 15 },
  result: { borderRadius: 16, padding: 16, marginTop: 14 },
  resultCorrect: { backgroundColor: theme.colors.successSurface },
  resultReview: { backgroundColor: theme.colors.accentSurface },
  resultTitle: { color: theme.colors.text, fontSize: 17, fontWeight: "800", textAlign: rtl ? "right" : "left" },
  resultText: { color: theme.colors.text, fontSize: 15, lineHeight: 25, textAlign: rtl ? "right" : "left", marginTop: 7 },
  resultSource: { color: theme.colors.muted, fontSize: 11, textAlign: rtl ? "right" : "left", marginTop: 9 },
  next: { backgroundColor: theme.colors.hero, borderRadius: 12, padding: 13, alignItems: "center", marginTop: 14 },
  nextText: { color: theme.colors.heroText, fontWeight: "800" },
  error: { color: theme.colors.error, textAlign: rtl ? "right" : "left", lineHeight: 22 },
});
