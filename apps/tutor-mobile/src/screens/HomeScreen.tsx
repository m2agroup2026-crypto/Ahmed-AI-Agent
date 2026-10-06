import { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import type { LessonSummary, TutorProgress, TutorRecommendation, TutorSubject } from "@contracts/tutor";
import { TutorApi } from "../api/client";
import { theme } from "../theme";

type Props = {
  api: TutorApi;
  onOpenLesson: (lesson: LessonSummary) => void;
  onOpenPractice: (recommendation: TutorRecommendation) => void;
};

export function HomeScreen({ api, onOpenLesson, onOpenPractice }: Props) {
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [progress, setProgress] = useState<TutorProgress | null>(null);
  const [recommendation, setRecommendation] = useState<TutorRecommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([api.lessons(), api.progress()])
      .then(([items, learnerProgress]) => {
        if (!active) return;
        setLessons(items);
        setProgress(learnerProgress);
      })
      .catch((reason: Error) => active && setError(reason.message))
      .finally(() => active && setLoading(false));
    api
      .recommendation()
      .then((next) => active && setRecommendation(next))
      .catch(() => active && setRecommendation(null));
    return () => {
      active = false;
    };
  }, [api]);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>NEXORA TUTOR</Text>
        <Text style={styles.title}>اتعلم بفهم، خطوة بخطوة</Text>
        <Text style={styles.subtitle}>مساعدك الدراسي للثانوي في أي وقت ومن الموبايل.</Text>
      </View>

      <View style={styles.sectionHeader}>
        <View>
          <Text style={styles.sectionTitle}>دروسك المتاحة</Text>
          <Text style={styles.sectionHint}>محتوى منهجي معتمد</Text>
        </View>
        <Text style={styles.liveLabel}>LIVE CURRICULUM</Text>
      </View>

      {progress && (
        <View style={styles.progressCard}>
          <View style={styles.progressCopy}>
            <Text style={styles.progressLabel}>تقدّمك الحقيقي</Text>
            <Text style={styles.progressTitle}>{progress.attempts} محاولات محفوظة</Text>
            <Text style={styles.progressHint}>
              {progress.attempts > 0
                ? `دقة الإجابات ${progress.accuracy_percent}%`
                : "ابدأ أول تدريب ليظهر تقدّمك هنا"}
            </Text>
          </View>
          <View style={styles.progressRing}>
            <Text style={styles.progressValue}>{Math.round(progress.accuracy_percent)}%</Text>
          </View>
        </View>
      )}

      {recommendation && (
        <View style={styles.recommendationCard}>
          <View style={styles.recommendationCopy}>
            <Text style={styles.recommendationLabel}>الخطوة المقترحة لك</Text>
            <Text style={styles.recommendationTitle}>{recommendation.question.prompt_ar}</Text>
            <Text style={styles.recommendationHint}>{recommendation.message_ar}</Text>
          </View>
          <Pressable style={styles.recommendationButton} onPress={() => onOpenPractice(recommendation)}>
            <Text style={styles.recommendationButtonText}>ابدأ التدريب</Text>
          </Pressable>
        </View>
      )}

      {loading && <ActivityIndicator color={theme.colors.teal} size="large" />}
      {error && <Text style={styles.error}>{error}</Text>}
      {!loading && !error && lessons.length === 0 && (
        <Text style={styles.empty}>لا توجد دروس متاحة لحسابك حاليًا.</Text>
      )}
      {lessons.map((lesson) => (
        <Pressable key={lesson.id} style={styles.card} onPress={() => onOpenLesson(lesson)}>
          <View style={styles.cardIcon}>
            <Text style={styles.cardIconText}>{subjectMark(lesson.subject_code)}</Text>
          </View>
          <View style={styles.cardBody}>
            <Text style={styles.cardSubject}>{subjectLabel(lesson.subject_code)}</Text>
            <Text style={styles.cardTitle}>{lesson.title_ar}</Text>
            <Text style={styles.cardSummary}>{lesson.summary_ar}</Text>
          </View>
          <Text style={styles.arrow}>‹</Text>
        </Pressable>
      ))}
    </ScrollView>
  );
}

function subjectLabel(subject: TutorSubject) {
  return { mathematics: "رياضيات", physics: "فيزياء", english: "English" }[subject];
}

function subjectMark(subject: TutorSubject) {
  return { mathematics: "∑", physics: "ϕ", english: "A" }[subject];
}

const styles = StyleSheet.create({
  container: { padding: 22, paddingBottom: 40, backgroundColor: theme.colors.surface },
  hero: { backgroundColor: theme.colors.navy, borderRadius: 24, padding: 24, marginBottom: 28 },
  eyebrow: { color: theme.colors.gold, fontSize: 12, fontWeight: "700", letterSpacing: 1.5 },
  title: { color: theme.colors.white, fontSize: 28, fontWeight: "800", textAlign: "right", marginTop: 18 },
  subtitle: { color: "#c8d5e5", fontSize: 15, lineHeight: 24, textAlign: "right", marginTop: 10 },
  sectionHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 14 },
  sectionTitle: { color: theme.colors.ink, fontSize: 21, fontWeight: "800", textAlign: "right" },
  sectionHint: { color: theme.colors.muted, fontSize: 13, textAlign: "right", marginTop: 4 },
  liveLabel: { color: theme.colors.teal, fontSize: 10, fontWeight: "700", letterSpacing: 1 },
  card: { backgroundColor: theme.colors.white, borderRadius: theme.radius, padding: 16, marginBottom: 12, flexDirection: "row-reverse", alignItems: "center", shadowColor: "#0b1d35", shadowOpacity: 0.06, shadowRadius: 12, elevation: 2 },
  cardIcon: { width: 48, height: 48, borderRadius: 16, backgroundColor: "#e4f4f1", justifyContent: "center", alignItems: "center", marginLeft: 14 },
  cardIconText: { color: theme.colors.teal, fontSize: 22, fontWeight: "800" },
  cardBody: { flex: 1 },
  cardSubject: { color: theme.colors.teal, fontSize: 12, fontWeight: "700", textAlign: "right" },
  cardTitle: { color: theme.colors.ink, fontSize: 18, fontWeight: "800", textAlign: "right", marginTop: 4 },
  cardSummary: { color: theme.colors.muted, fontSize: 13, lineHeight: 20, textAlign: "right", marginTop: 4 },
  arrow: { color: theme.colors.gold, fontSize: 28, marginLeft: 8 },
  error: { color: theme.colors.danger, textAlign: "right", lineHeight: 22 },
  empty: { color: theme.colors.muted, textAlign: "right", paddingVertical: 30 },
  progressCard: { backgroundColor: "#e7f5f2", borderRadius: 22, padding: 18, marginBottom: 22, flexDirection: "row-reverse", alignItems: "center" },
  progressCopy: { flex: 1 },
  progressLabel: { color: theme.colors.teal, fontSize: 12, fontWeight: "800", textAlign: "right" },
  progressTitle: { color: theme.colors.ink, fontSize: 18, fontWeight: "800", textAlign: "right", marginTop: 5 },
  progressHint: { color: theme.colors.muted, fontSize: 13, textAlign: "right", marginTop: 5 },
  progressRing: { width: 66, height: 66, borderRadius: 33, borderWidth: 6, borderColor: theme.colors.gold, justifyContent: "center", alignItems: "center", marginLeft: 14 },
  progressValue: { color: theme.colors.ink, fontSize: 15, fontWeight: "800" },
  recommendationCard: { backgroundColor: theme.colors.navy, borderRadius: 22, padding: 18, marginBottom: 22 },
  recommendationCopy: { marginBottom: 14 },
  recommendationLabel: { color: theme.colors.gold, fontSize: 12, fontWeight: "800", textAlign: "right" },
  recommendationTitle: { color: theme.colors.white, fontSize: 17, lineHeight: 25, fontWeight: "800", textAlign: "right", marginTop: 7 },
  recommendationHint: { color: "#c8d5e5", fontSize: 13, lineHeight: 21, textAlign: "right", marginTop: 6 },
  recommendationButton: { backgroundColor: theme.colors.teal, borderRadius: 13, minHeight: 48, justifyContent: "center", alignItems: "center" },
  recommendationButtonText: { color: theme.colors.white, fontWeight: "800", fontSize: 15 },
});
