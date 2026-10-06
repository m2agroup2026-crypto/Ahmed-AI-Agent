import { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import type { LessonSummary } from "@contracts/tutor";
import { TutorApi } from "../api/client";
import { theme } from "../theme";

type Props = { api: TutorApi; lesson: LessonSummary; onBack: () => void; onPractice: () => void };

export function TutorSessionScreen({ api, lesson, onBack, onPractice }: Props) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function askTutor() {
    if (!question.trim() || sending) return;
    setSending(true);
    setError(null);
    try {
      const activeSession = sessionId
        ? { id: sessionId }
        : await api.startSession(lesson.subject_code);
      if (!sessionId) setSessionId(activeSession.id);
      const result = await api.sendMessage(activeSession.id, question.trim(), lesson.id);
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
        <Pressable onPress={onBack} accessibilityLabel="العودة">
          <Text style={styles.back}>›</Text>
        </Pressable>
        <View style={styles.headerCopy}>
          <Text style={styles.subject}>{lesson.title_ar}</Text>
          <Text style={styles.caption}>جلسة Tutor مرتبطة بالدرس</Text>
        </View>
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.lessonCard}>
          <Text style={styles.lessonLabel}>ملخص الدرس</Text>
          <Text style={styles.lessonText}>{lesson.summary_ar}</Text>
          <Pressable style={styles.practiceButton} onPress={onPractice}>
            <Text style={styles.practiceButtonText}>تدرّب على الدرس</Text>
          </Pressable>
        </View>
        {answer && (
          <View style={styles.answerCard}>
            <Text style={styles.answerLabel}>Tutor</Text>
            <Text style={styles.answer}>{answer}</Text>
          </View>
        )}
        {error && <Text style={styles.error}>{error}</Text>}
      </ScrollView>
      <View style={styles.composer}>
        <TextInput
          value={question}
          onChangeText={setQuestion}
          placeholder="اكتب سؤالك عن الدرس..."
          placeholderTextColor={theme.colors.muted}
          multiline
          style={styles.input}
          textAlign="right"
        />
        <Pressable style={styles.send} onPress={askTutor} disabled={sending}>
          {sending ? <ActivityIndicator color={theme.colors.white} /> : <Text style={styles.sendText}>اسأل</Text>}
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.colors.surface },
  header: { backgroundColor: theme.colors.navy, padding: 20, paddingTop: 58, flexDirection: "row", alignItems: "center" },
  back: { color: theme.colors.white, fontSize: 34, transform: [{ rotate: "180deg" }] },
  headerCopy: { flex: 1, marginLeft: 12 },
  subject: { color: theme.colors.white, fontSize: 20, fontWeight: "800", textAlign: "right" },
  caption: { color: "#c8d5e5", fontSize: 12, textAlign: "right", marginTop: 4 },
  content: { padding: 20, paddingBottom: 30 },
  lessonCard: { backgroundColor: theme.colors.white, borderRadius: theme.radius, padding: 20, marginBottom: 16 },
  lessonLabel: { color: theme.colors.teal, fontSize: 12, fontWeight: "700", textAlign: "right" },
  lessonText: { color: theme.colors.ink, fontSize: 16, lineHeight: 28, textAlign: "right", marginTop: 10 },
  answerCard: { backgroundColor: "#e7f5f2", borderRadius: theme.radius, padding: 20, marginBottom: 16 },
  answerLabel: { color: theme.colors.teal, fontSize: 12, fontWeight: "700", textAlign: "right" },
  answer: { color: theme.colors.ink, fontSize: 16, lineHeight: 28, textAlign: "right", marginTop: 10 },
  error: { color: theme.colors.danger, textAlign: "right", lineHeight: 22 },
  composer: { backgroundColor: theme.colors.white, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: "#d5dfe8", padding: 12, flexDirection: "row-reverse", alignItems: "flex-end" },
  input: { flex: 1, minHeight: 48, maxHeight: 110, backgroundColor: theme.colors.surface, borderRadius: 14, paddingHorizontal: 14, paddingVertical: 10, color: theme.colors.ink },
  send: { backgroundColor: theme.colors.teal, borderRadius: 14, minWidth: 64, height: 48, justifyContent: "center", alignItems: "center", marginRight: 8 },
  sendText: { color: theme.colors.white, fontWeight: "800" },
  practiceButton: { backgroundColor: theme.colors.navy, borderRadius: 14, minHeight: 48, alignItems: "center", justifyContent: "center", marginTop: 18 },
  practiceButtonText: { color: theme.colors.white, fontWeight: "800" },
});
