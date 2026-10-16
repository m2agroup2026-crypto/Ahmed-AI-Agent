import { useEffect, useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { Text } from "../typography";

import type { LessonSummary, TutorProgress, TutorRecommendation, TutorSubject } from "@contracts/tutor";
import { TutorApi } from "../api/client";
import { useThemedStyles, type Theme } from "../theme";
import { usePreferences } from "../preferences";
import { officialText, readingStyle } from "../learning";
import { isolateMath } from "../../../../packages/presentation/content";
import { BrandLogo } from "../BrandLogo";

type Props = {
  api: TutorApi;
  onOpenLesson: (lesson: LessonSummary) => void;
  onOpenPractice: (recommendation: TutorRecommendation) => void;
};

export function HomeScreen({ api, onOpenLesson, onOpenPractice }: Props) {
  const { theme, t, language, rtl } = usePreferences();
  const styles = useThemedStyles(createStyles);
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
        <BrandLogo />
        <Text style={styles.title}>{t("اتعلم بفهم، خطوة بخطوة", "Learn with understanding, step by step")}</Text>
        <Text style={styles.subtitle}>{t("مساعدك الدراسي للثانوي في أي وقت ومن الموبايل.", "Your secondary school learning companion, wherever you are.")}</Text>
      </View>

      <View style={styles.sectionHeader}>
        <View>
          <Text style={styles.sectionTitle}>{t("دروسك المتاحة", "Available lessons")}</Text>
          <Text style={styles.sectionHint}>{t("المحتوى المتاح ومصدره", "Available content and its sources")}</Text>
        </View>
        <Text style={styles.liveLabel}>{t("المنهج", "CURRICULUM")}</Text>
      </View>

      {progress && (
        <View style={styles.progressCard}>
          <View style={styles.progressCopy}>
            <Text style={styles.progressLabel}>{t("تقدّمك الحقيقي", "Your progress")}</Text>
            <Text style={styles.progressTitle}>{t(`${progress.attempts} محاولات محفوظة`, `${progress.attempts} saved attempts`)}</Text>
            <Text style={styles.progressHint}>
              {progress.attempts > 0
                ? t(`دقة الإجابات ${progress.accuracy_percent}%`, `Answer accuracy ${progress.accuracy_percent}%`)
                : t("ابدأ أول تدريب ليظهر تقدّمك هنا", "Complete your first practice to see your progress")}
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
            <Text style={styles.recommendationLabel}>{t("الخطوة المقترحة لك", "Your next step")}</Text>
            <Text style={[styles.recommendationTitle, readingStyle(recommendation.question.content_language ?? language)]}>{isolateMath(officialText(recommendation.question.content_language, recommendation.question.prompt_ar, recommendation.question.prompt_en) ?? t("لغة المحتوى غير محددة", "Content language is not declared"))}</Text>
            <Text style={styles.recommendationHint}>{language === "ar" ? recommendation.message_ar : recommendation.message_en}</Text>
          </View>
          <Pressable accessibilityRole="button" style={styles.recommendationButton} onPress={() => onOpenPractice(recommendation)}>
            <Text style={styles.recommendationButtonText}>{t("ابدأ التدريب", "Start practice")}</Text>
          </Pressable>
        </View>
      )}

      {loading && <ActivityIndicator color={theme.colors.primary} size="large" />}
      {error && <Text accessibilityRole="alert" style={styles.error}>{t("تعذر تحميل الدروس. تحقق من الاتصال ثم أعد المحاولة.", "Lessons could not be loaded. Check your connection and retry.")}</Text>}
      {!loading && !error && lessons.length === 0 && (
        <Text style={styles.empty}>{t("لا توجد دروس متاحة لحسابك حاليًا.", "No lessons are available for your account yet.")}</Text>
      )}
      {lessons.map((lesson) => (
        <Pressable accessibilityRole="button" key={lesson.id} style={styles.card} onPress={() => onOpenLesson(lesson)}>
          <View style={styles.cardIcon}>
            <Text style={styles.cardIconText}>{subjectMark(lesson.subject_code)}</Text>
          </View>
          <View style={styles.cardBody}>
            <Text style={styles.cardSubject}>{subjectLabel(lesson.subject_code, language)}</Text>
            <Text style={[styles.cardTitle, readingStyle(lesson.content_language ?? language)]}>{officialText(lesson.content_language, lesson.title_ar, lesson.title_en) ?? t("لغة المحتوى غير محددة", "Content language is not declared")}</Text>
            <Text style={[styles.cardSummary, readingStyle(lesson.content_language ?? language)]}>{officialText(lesson.content_language, lesson.summary_ar, lesson.summary_en)}</Text>
          </View>
          <Text style={styles.arrow}>‹</Text>
        </Pressable>
      ))}
    </ScrollView>
  );
}

function subjectLabel(subject: TutorSubject, language: "ar" | "en") {
  return language === "ar" ? { mathematics: "رياضيات", physics: "فيزياء", english: "الإنجليزية" }[subject]
    : { mathematics: "Mathematics", physics: "Physics", english: "English" }[subject];
}

function subjectMark(subject: TutorSubject) {
  return { mathematics: "∑", physics: "ϕ", english: "A" }[subject];
}

const createStyles = (theme: Theme, rtl: boolean) => StyleSheet.create({
  container: { padding: 22, paddingBottom: 40, backgroundColor: theme.colors.background },
  hero: { backgroundColor: theme.colors.surface, borderRadius: 24, padding: 24, marginBottom: 28 },
  eyebrow: { color: theme.colors.heroAccent, fontSize: 12, fontWeight: "700", letterSpacing: 1.5 },
  title: { color: theme.colors.text, fontSize: 28, fontWeight: "800", textAlign: rtl ? "right" : "left", marginTop: 18 },
  subtitle: { color: theme.colors.muted, fontSize: 15, lineHeight: 24, textAlign: rtl ? "right" : "left", marginTop: 10 },
  sectionHeader: { flexDirection: rtl ? "row-reverse" : "row", flexWrap: "wrap", gap: 10, justifyContent: "space-between", alignItems: "flex-end", marginBottom: 14 },
  sectionTitle: { color: theme.colors.text, fontSize: 21, fontWeight: "800", textAlign: rtl ? "right" : "left" },
  sectionHint: { color: theme.colors.muted, fontSize: 13, textAlign: rtl ? "right" : "left", marginTop: 4 },
  liveLabel: { color: theme.colors.primary, fontSize: 10, fontWeight: "700", letterSpacing: 1 },
  card: { backgroundColor: theme.colors.surface, borderRadius: theme.radius, padding: 16, marginBottom: 12, flexDirection: rtl ? "row-reverse" : "row", alignItems: "center", shadowColor: theme.colors.shadow, shadowOpacity: 0.06, shadowRadius: 12, elevation: 2 },
  cardIcon: { width: 48, height: 48, borderRadius: 16, backgroundColor: theme.colors.accentSurface, justifyContent: "center", alignItems: "center", marginLeft: 14 },
  cardIconText: { color: theme.colors.primary, fontSize: 22, fontWeight: "800" },
  cardBody: { flex: 1 },
  cardSubject: { color: theme.colors.primary, fontSize: 12, fontWeight: "700", textAlign: rtl ? "right" : "left" },
  cardTitle: { color: theme.colors.text, fontSize: 18, fontWeight: "800", textAlign: rtl ? "right" : "left", marginTop: 4 },
  cardSummary: { color: theme.colors.muted, fontSize: 13, lineHeight: 20, textAlign: rtl ? "right" : "left", marginTop: 4 },
  arrow: { color: theme.colors.accent, fontSize: 28, marginHorizontal: 8, transform: [{ rotate: rtl ? "0deg" : "180deg" }] },
  error: { color: theme.colors.error, textAlign: rtl ? "right" : "left", lineHeight: 22 },
  empty: { color: theme.colors.muted, textAlign: rtl ? "right" : "left", paddingVertical: 30 },
  progressCard: { backgroundColor: theme.colors.successSurface, borderRadius: 22, padding: 18, marginBottom: 22, flexDirection: rtl ? "row-reverse" : "row", alignItems: "center" },
  progressCopy: { flex: 1 },
  progressLabel: { color: theme.colors.primary, fontSize: 12, fontWeight: "800", textAlign: rtl ? "right" : "left" },
  progressTitle: { color: theme.colors.text, fontSize: 18, fontWeight: "800", textAlign: rtl ? "right" : "left", marginTop: 5 },
  progressHint: { color: theme.colors.muted, fontSize: 13, textAlign: rtl ? "right" : "left", marginTop: 5 },
  progressRing: { width: 66, height: 66, borderRadius: 33, borderWidth: 6, borderColor: theme.colors.heroAccent, justifyContent: "center", alignItems: "center", marginLeft: 14 },
  progressValue: { color: theme.colors.text, fontSize: 15, fontWeight: "800" },
  recommendationCard: { backgroundColor: theme.colors.hero, borderRadius: 22, padding: 18, marginBottom: 22 },
  recommendationCopy: { marginBottom: 14 },
  recommendationLabel: { color: theme.colors.heroAccent, fontSize: 12, fontWeight: "800", textAlign: rtl ? "right" : "left" },
  recommendationTitle: { color: theme.colors.heroText, fontSize: 17, lineHeight: 25, fontWeight: "800", textAlign: rtl ? "right" : "left", marginTop: 7 },
  recommendationHint: { color: theme.colors.heroMuted, fontSize: 13, lineHeight: 21, textAlign: rtl ? "right" : "left", marginTop: 6 },
  recommendationButton: { backgroundColor: theme.colors.primary, borderRadius: 13, minHeight: 48, justifyContent: "center", alignItems: "center" },
  recommendationButtonText: { color: theme.colors.onPrimary, fontWeight: "800", fontSize: 15 },
});
