import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AppState, Pressable, ScrollView, StyleSheet, Switch, View } from "react-native";
import { useIsFocused } from "@react-navigation/native";
import * as Speech from "expo-speech";
import type { LessonSummary, TutorRecommendation } from "@contracts/tutor";
import { parseVoiceCommand, canExecute, MAX_TRANSCRIPT, voiceLocales, type VoiceLocale } from "../../../../packages/voice/commands";
import { VoiceEngine, type VoiceState } from "../../../../packages/voice/engine";
import { TutorApi } from "../api/client";
import { createRecognitionProvider } from "../voice/provider";
import { usePreferences } from "../preferences";
import { Text, TextInput } from "../typography";
import { BrandLogo } from "../BrandLogo";
import { officialText } from "../learning";

type Props = { api: TutorApi; onHome(): void; onLesson(lesson: LessonSummary, question?: string): void; onPractice(item: TutorRecommendation): void };
export function VoiceScreen({ api, onHome, onLesson, onPractice }: Props) {
  const { theme: { colors }, t, rtl } = usePreferences();
  const [state, setState] = useState<VoiceState>("idle");
  const [text, setText] = useState("");
  const [locale, setLocale] = useState<VoiceLocale>("ar-EG");
  const [consent, setConsent] = useState(false);
  const [spoken, setSpoken] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [message, setMessage] = useState("");
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [question, setQuestion] = useState<string>();
  const [classes, setClasses] = useState<{ id: string; name: string }[]>([]);
  const [assignments, setAssignments] = useState<{ id: string; title: string }[]>([]);
  const focused = useIsFocused();
  const active = useRef(true);
  const operation = useRef(0);
  const inFlight = useRef(false);
  const cancelPendingCommand = useCallback(() => {
    operation.current++; inFlight.current = false; setBusy(false); setConfirm(false);
  }, []);
  const provider = useMemo(createRecognitionProvider, []);
  const engine = useMemo(() => new VoiceEngine(provider, event => {
    if (!active.current) return;
    if (event.type === "state") setState(event.state);
    if (event.type === "transcript") { setText(event.text); setConfirm(false); }
    if (event.type === "error") { setState("error"); setError(event.code); }
  }), [provider]);
  useEffect(() => {
    active.current = true;
    const subscription = AppState.addEventListener("change", value => {
      if (value !== "active") { engine.cancel(); void Speech.stop(); cancelPendingCommand(); }
    });
    return () => { active.current = false; operation.current++; inFlight.current = false; engine.cancel(); void Speech.stop(); subscription.remove(); };
  }, [engine, cancelPendingCommand]);
  useEffect(() => { if (!focused) { engine.cancel(); void Speech.stop(); cancelPendingCommand(); } }, [focused, engine, cancelPendingCommand]);
  const command = parseVoiceCommand(text);
  const recording = state === "recording";
  const locked = recording || state === "permission" || state === "processing" || busy;
  const say = (value: string) => { setMessage(value); if (spoken) { void Speech.stop(); Speech.speak(value, { language: locale }); } };
  async function execute() {
    if (inFlight.current || !confirm || locked) return;
    inFlight.current = true; setBusy(true); setConfirm(false); setError("");
    const current = ++operation.current;
    const valid = () => active.current && current === operation.current;
    try {
      // Never use recognized text, local preferences, JWT decoding, or a cached role as authority.
      const identity = await api.classroomIdentity();
      if (!valid()) return;
      if (!canExecute(command, identity.role)) { setError("forbidden"); return; }
      setLessons([]); setClasses([]); setAssignments([]); setMessage(""); setQuestion(undefined);
      if (command.kind === "navigate") {
        switch (command.action) {
          case "home": onHome(); break;
          case "practice": { const item = await api.recommendation(); if (valid()) onPractice(item); break; }
          case "math_lessons": { const items = await api.lessons("mathematics"); if (valid()) { setLessons(items); say(t("اختار الدرس", "Choose a lesson")); } break; }
          case "progress": { const value = await api.progress(); if (valid()) say(t(`${value.attempts} محاولة، الدقة ${value.accuracy_percent}%`, `${value.attempts} attempts, ${value.accuracy_percent}% accuracy`)); break; }
          case "classrooms": case "teacher_classrooms": { const items = await api.classrooms(); if (valid()) { setClasses(items); say(items.length ? t("فصولك", "Your classrooms") : t("لا توجد فصول متاحة", "No classrooms available")); } break; }
        }
      } else if (command.kind === "tutor") {
        const items = await api.lessons("mathematics");
        if (valid()) { setLessons(items); setQuestion(command.question); say(t("اختار الدرس لتراجع السؤال مع المعلم", "Choose the lesson to review your Tutor question")); }
      }
    } catch { if (valid()) setError("connection"); }
    finally { if (valid()) { inFlight.current = false; setBusy(false); } }
  }
  const label = (ar: string, en: string) => t(ar, en);
  const actionTitle = command.kind === "navigate" ? {
    home: label("الصفحة الرئيسية", "Home"), math_lessons: label("دروس الرياضيات", "Math lessons"),
    practice: label("التدريبات", "Practice"), progress: label("تقدمي", "My progress"),
    classrooms: label("فصولي", "My classrooms"), teacher_classrooms: label("فصول المدرس", "Teacher classrooms"),
  }[command.action] : label("اختيار درس للسؤال", "Choose a lesson for the question");
  const row = { flexDirection: rtl ? "row-reverse" as const : "row" as const };
  const button = (title: string, action: () => void, disabled = false, primary = false) => <Pressable accessibilityRole="button" accessibilityState={{ disabled }} disabled={disabled} onPress={action}
    style={[styles.button, { backgroundColor: primary ? colors.primary : colors.surface, borderColor: colors.border, opacity: disabled ? .45 : 1 }]}>
    <Text style={{ color: primary ? colors.onPrimary : colors.text, textAlign: "center", fontWeight: "700" }}>{title}</Text>
  </Pressable>;
  const copy = { color: colors.text, textAlign: rtl ? "right" as const : "left" as const };
  const status = { idle: label("الميكروفون مقفول", "Microphone off"), permission: label("بانتظار إذن الميكروفون", "Waiting for microphone permission"), recording: label("● بنسمعك — ١٥ ثانية بحد أقصى", "● Listening — 15 second maximum"), processing: label("جاري التعرف على الكلام", "Recognizing speech"), review: label("راجع الكلام قبل التنفيذ", "Review before executing"), error: label("تعذر التعرف على الكلام", "Recognition failed") }[state];
  return <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={[styles.container, { backgroundColor: colors.background }]}>
    <View style={[styles.hero, { backgroundColor: colors.hero }]}>
      <BrandLogo />
      <Text style={{ color: colors.heroText, fontSize: 28, fontWeight: "800", textAlign: copy.textAlign }}>{label("قولها لأكليث", "Say it to AQLITH")}</Text>
      <Text style={{ color: colors.heroMuted, textAlign: copy.textAlign }}>{label("صوتك يسهّل رحلتك في التعلّم", "Your voice, a simpler way to learn")}</Text>
    </View>
    {button(label("الصفحة الرئيسية", "Home"), onHome)}
    <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}>
      <Text style={[copy, { color: colors.muted }]}>{label("التسجيل يبدأ بطلبك فقط. خدمة الجهاز أو المتصفح قد ترسل الصوت لمزودها. أكليث لا يحتفظ بالصوت ولا يرفعه لخادمه.", "Listening starts only when you ask. Your device or browser speech service may send audio to its provider. AQLITH does not store audio or upload it to its server.")}</Text>
      <View style={[styles.row, row]}><Switch accessibilityLabel={label("الموافقة على استخدام خدمة التعرف على الكلام", "Consent to speech service processing")} value={consent} disabled={locked} onValueChange={setConsent} /><Text style={copy}>{label("أوافق على معالجة الصوت", "Allow speech processing")}</Text></View>
      <View style={[styles.row, { flexDirection: rtl ? "row-reverse" : "row", flexWrap: "wrap" }]}>{voiceLocales.map(item => <View key={item}>{button(item === locale ? `✓ ${item}` : item, () => setLocale(item), locked)}</View>)}</View>
      <Text accessibilityLiveRegion="polite" style={[copy, { color: recording ? colors.error : colors.primary, fontWeight: "700" }]}>{status}</Text>
      {!provider.available && <Text style={copy}>{label("التعرف غير متاح هنا. أندرويد يحتاج نسخة تطوير وخدمة كلام مثبتة. تقدر تكتب الأمر بالأسفل.", "Recognition is unavailable here. Android needs a development build and an installed speech service. Type a command below.")}</Text>}
      {button(recording ? label("■ إيقاف", "■ Stop") : label("● اضغط واتكلم", "● Tap to speak"), () => {
        if (recording) { setState("processing"); engine.stop(); }
        else { setText(""); setError(""); setConfirm(false); void Speech.stop(); void engine.start(locale); }
      }, recording ? false : locked || !consent || !provider.available, true)}
      {button(label("إلغاء", "Cancel"), () => { cancelPendingCommand(); engine.cancel(); void Speech.stop(); setText(""); setError(""); })}
    </View>
    <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}>
      <Text style={[copy, { fontSize: 19, fontWeight: "700" }]}>{label("راجع أو اكتب أمرك", "Review or type your command")}</Text>
      <TextInput accessibilityLabel={label("نص الأمر القابل للتعديل", "Editable command transcript")} value={text} editable={!locked} maxLength={MAX_TRANSCRIPT} multiline placeholder={label("مثال: وريني تقدمي", "Example: show my progress")} placeholderTextColor={colors.muted}
        onChangeText={value => { setText(value); setConfirm(false); setError(""); }} style={[styles.input, copy, { borderColor: colors.border, writingDirection: locale === "ar-EG" ? "rtl" : "ltr" }]} />
      <Text style={[copy, { color: colors.muted }]}>{label("راجع الأرقام والمعادلات. لا يتم إرسال امتحانات أو تغيير درجات أو صلاحيات بالصوت.", "Check numbers and equations. Voice cannot submit exams, change grades, or modify permissions.")}</Text>
      {button(busy ? label("جاري التحميل…", "Loading…") : label("مراجعة التنفيذ", "Review action"), () => setConfirm(true), locked || command.kind === "unknown", true)}
      {text.length > 0 && command.kind === "unknown" && <Text style={copy}>{label("الأمر غير واضح. اختار مثال أو عدّل النص.", "Command unclear. Choose an example or edit the text.")}</Text>}
      {confirm && <View accessibilityLiveRegion="polite" style={[styles.card, { borderColor: colors.border, backgroundColor: colors.accentSurface }]}>
        <Text style={copy}>{label("تأكيد تنفيذ الأمر الظاهر؟", "Execute the displayed command?")} {actionTitle}</Text>
        <Text style={copy}>{text}</Text>
        {button(label("تأكيد", "Confirm"), () => void execute(), locked, true)}
        {button(label("رجوع للتعديل", "Keep editing"), () => setConfirm(false))}
      </View>}
      <View style={[styles.row, row]}><Switch accessibilityLabel={label("ردود منطوقة اختيارية", "Optional spoken responses")} value={spoken} onValueChange={value => { setSpoken(value); if (!value) void Speech.stop(); }} /><Text style={copy}>{label("اقرأ الرد بصوت", "Read responses aloud")}</Text></View>
    </View>
    {error !== "" && <View accessibilityRole="alert" style={styles.card}><Text style={[copy, { color: colors.error }]}>{error === "forbidden" ? label("الأمر ده للمدرس فقط بحساب موثّق.", "This command requires a verified teacher account.") : error === "not-allowed" ? label("إذن الميكروفون مرفوض. غيّره من الإعدادات أو اكتب الأمر.", "Microphone permission denied. Change it in settings or type instead.") : label("تعذر إكمال الطلب. تحقق من الاتصال وخدمة الكلام وحاول تاني، أو استخدم الكتابة.", "Request failed. Check your connection and speech service, retry, or type instead.")}</Text>
      {button(label("حاول تاني", "Retry"), () => { setError(""); if (text.trim()) setConfirm(true); else if (consent && provider.available) void engine.start(locale); }, locked)}
    </View>}
    {message !== "" && <Text accessibilityLiveRegion="polite" style={[copy, { fontSize: 20 }]}>{message}</Text>}
    {lessons.map(lesson => <View key={lesson.id}>{button(officialText(lesson.content_language, lesson.title_ar, lesson.title_en) ?? label("لغة المحتوى غير محددة", "Content language is not declared"), () => onLesson(lesson, question))}</View>)}
    {classes.map(item => <View key={item.id}>{button(item.name, () => {
      const current = ++operation.current;
      void api.classroomAssignments(item.id).then(items => { if (active.current && current === operation.current) setAssignments(items); }).catch(() => { if (active.current && current === operation.current) setError("connection"); });
    })}</View>)}
    {assignments.map(item => <Text key={item.id} style={copy}>{item.title}</Text>)}
    <Text style={[copy, { fontSize: 18, fontWeight: "700" }]}>{label("جرّب تقول… أو اضغط", "Try saying… or tap")}</Text>
    {[["يا أكليث، افتح دروس الرياضيات", "open math lessons"], ["افتح التدريبات", "open practice"],
      ["وريني تقدمي", "show my progress"], ["اشرحلي المعادلة دي", "explain this equation"],
      ["ارجع للصفحة الرئيسية", "go home"], ["افتح الفصل بتاعي", "open my classroom"],
      ["افتح فصولي كمدرس", "open teacher classrooms"]].map(([ar, en]) => {
        const example = label(ar!, en!);
        return <View key={example}>{button(example, () => { setText(example); setConfirm(false); }, locked)}</View>;
      })}
  </ScrollView>;
}
const styles = StyleSheet.create({
  container: { padding: 20, paddingBottom: 48, gap: 14, width: "100%", maxWidth: 760, alignSelf: "center" },
  hero: { padding: 24, borderRadius: 24, gap: 12 },
  card: { padding: 18, borderRadius: 20, gap: 14, borderWidth: 1 },
  row: { flexDirection: "row", alignItems: "center", gap: 12 },
  button: { minHeight: 48, padding: 12, borderRadius: 14, borderWidth: 1, justifyContent: "center" },
  input: { minHeight: 110, padding: 14, borderWidth: 1, borderRadius: 14, fontSize: 17, textAlignVertical: "top" },
});
