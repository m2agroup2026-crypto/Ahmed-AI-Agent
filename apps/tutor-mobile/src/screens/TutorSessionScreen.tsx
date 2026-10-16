import { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { Text, TextInput } from "../typography";

import type { LessonSummary } from "@contracts/tutor";
import { TutorApi } from "../api/client";
import { useThemedStyles, type Theme } from "../theme";
import { usePreferences } from "../preferences";
import { officialAnswerLocale, officialText, readingStyle } from "../learning";

type Props = { api: TutorApi; lesson: LessonSummary; initialQuestion?: string; onBack: () => void; onPractice: () => void };

export function TutorSessionScreen({ api, lesson, initialQuestion, onBack, onPractice }: Props) {
  const { theme, t, language, rtl } = usePreferences();
  const styles = useThemedStyles(createStyles);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState(initialQuestion ?? "");
  useEffect(() => { setQuestion(initialQuestion ?? ""); setSessionId(null); setAnswer(null); }, [lesson.id, initialQuestion]);
  const [answer, setAnswer] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const answerLocale = officialAnswerLocale(lesson);

  async function askTutor() {
    if (!question.trim() || sending || !answerLocale) return;
    setSending(true);
    setError(null);
    try {
      const activeSession = sessionId
        ? { id: sessionId }
        : await api.startSession(lesson.subject_code, lesson.curriculum_version);
      if (!sessionId) setSessionId(activeSession.id);
      const result = await api.sendMessage(activeSession.id, question.trim(), lesson.id, answerLocale);
      setAnswer(result.answer.content);
      setQuestion("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تعذر إرسال السؤال");
    } finally {
      setSending(false);
    }
  }

  return (
    <View style={styles.screen}>
      <View style={styles.header}>
        <Pressable onPress={onBack} accessibilityRole="button" accessibilityLabel={t("العودة", "Back")} style={{ minHeight: 44, minWidth: 44, alignItems: "center" }}>
          <Text style={styles.back}>›</Text>
        </Pressable>
        <View style={styles.headerCopy}>
          <Text style={[styles.subject, readingStyle(lesson.content_language ?? language)]}>{officialText(lesson.content_language, lesson.title_ar, lesson.title_en) ?? t("لغة المحتوى غير محددة", "Content language is not declared")}</Text>
          <Text style={styles.caption}>{t("جلسة Tutor مرتبطة بالدرس", "Tutor session for this lesson")}</Text>
        </View>
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.lessonCard}>
          <Text style={styles.lessonLabel}>{t("ملخص الدرس", "Lesson summary")}</Text>
          <Text style={[styles.lessonText, readingStyle(lesson.content_language ?? language)]}>{officialText(lesson.content_language, lesson.summary_ar, lesson.summary_en) ?? t("لغة المحتوى غير محددة", "Content language is not declared")}</Text>
          <Pressable accessibilityRole="button" style={styles.practiceButton} onPress={onPractice}>
            <Text style={styles.practiceButtonText}>{t("تدرّب على الدرس", "Practice this lesson")}</Text>
          </Pressable>
        </View>
        {answer && (
          <View style={styles.answerCard}>
            <Text style={styles.answerLabel}>Tutor</Text>
            <Text style={[styles.answer, readingStyle(lesson.content_language ?? language)]}>{answer}</Text>
          </View>
        )}
        {error && <Text accessibilityRole="alert" style={styles.error}>{t("تعذر إرسال السؤال. تحقق من الاتصال ثم أعد المحاولة.", "Your question could not be sent. Check your connection and retry.")}</Text>}
      </ScrollView>
      <View style={styles.composer}>
        {!answerLocale && <Text accessibilityRole="alert" style={styles.error}>{t("لغة الدرس الرسمية غير محددة. تعذر إرسال السؤال.", "The lesson's official language is undeclared. Your question cannot be sent.")}</Text>}
        <TextInput
          value={question}
          onChangeText={setQuestion}
          placeholder={t("اكتب سؤالك عن الدرس...", "Ask about this lesson...")}
          accessibilityLabel={t("سؤالك عن الدرس", "Your lesson question")}
          placeholderTextColor={theme.colors.muted}
          multiline
          style={styles.input}
          textAlign={rtl ? "right" : "left"}
        />
        <Pressable accessibilityRole="button" accessibilityState={{ disabled: sending || !answerLocale }} style={styles.send} onPress={askTutor} disabled={sending || !answerLocale}>
          {sending ? <ActivityIndicator color={theme.colors.onPrimary} /> : <Text style={styles.sendText}>{t("اسأل", "Ask")}</Text>}
        </Pressable>
      </View>
    </View>
  );
}

const createStyles = (theme: Theme, rtl: boolean) => StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.colors.background },
  header: { backgroundColor: theme.colors.hero, padding: 20, paddingTop: 58, flexDirection: rtl ? "row-reverse" : "row", alignItems: "center" },
  back: { color: theme.colors.heroText, fontSize: 34, transform: [{ rotate: rtl ? "0deg" : "180deg" }] },
  headerCopy: { flex: 1, marginLeft: 12 },
  subject: { color: theme.colors.heroText, fontSize: 20, fontWeight: "800", textAlign: rtl ? "right" : "left" },
  caption: { color: theme.colors.heroMuted, fontSize: 12, textAlign: rtl ? "right" : "left", marginTop: 4 },
  content: { padding: 20, paddingBottom: 30 },
  lessonCard: { backgroundColor: theme.colors.surface, borderRadius: theme.radius, padding: 20, marginBottom: 16 },
  lessonLabel: { color: theme.colors.primary, fontSize: 12, fontWeight: "700", textAlign: rtl ? "right" : "left" },
  lessonText: { color: theme.colors.text, fontSize: 16, lineHeight: 28, textAlign: rtl ? "right" : "left", marginTop: 10 },
  answerCard: { backgroundColor: theme.colors.successSurface, borderRadius: theme.radius, padding: 20, marginBottom: 16 },
  answerLabel: { color: theme.colors.primary, fontSize: 12, fontWeight: "700", textAlign: rtl ? "right" : "left" },
  answer: { color: theme.colors.text, fontSize: 16, lineHeight: 28, textAlign: rtl ? "right" : "left", marginTop: 10 },
  error: { color: theme.colors.error, textAlign: rtl ? "right" : "left", lineHeight: 22 },
  composer: { backgroundColor: theme.colors.surface, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: theme.colors.border, padding: 12, flexDirection: rtl ? "row-reverse" : "row", alignItems: "flex-end" },
  input: { flex: 1, minHeight: 48, maxHeight: 110, backgroundColor: theme.colors.background, borderRadius: 14, paddingHorizontal: 14, paddingVertical: 10, color: theme.colors.text },
  send: { backgroundColor: theme.colors.primary, borderRadius: 14, minWidth: 64, height: 48, justifyContent: "center", alignItems: "center", marginRight: 8 },
  sendText: { color: theme.colors.onPrimary, fontWeight: "800" },
  practiceButton: { backgroundColor: theme.colors.hero, borderRadius: 14, minHeight: 48, alignItems: "center", justifyContent: "center", marginTop: 18 },
  practiceButtonText: { color: theme.colors.heroText, fontWeight: "800" },
});
