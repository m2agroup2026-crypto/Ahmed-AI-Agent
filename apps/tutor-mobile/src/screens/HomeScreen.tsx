import { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import type { LessonSummary, TutorSubject } from "@contracts/tutor";
import { TutorApi } from "../api/client";
import { theme } from "../theme";

type Props = {
  api: TutorApi;
  onOpenLesson: (lesson: LessonSummary) => void;
};

export function HomeScreen({ api, onOpenLesson }: Props) {
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .lessons()
      .then((items) => active && setLessons(items))
      .catch((reason: Error) => active && setError(reason.message))
      .finally(() => active && setLoading(false));
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
});
