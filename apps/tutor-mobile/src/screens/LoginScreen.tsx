import { useState } from "react";
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { Text, TextInput } from "../typography";

import { useThemedStyles, type Theme } from "../theme";
import { usePreferences } from "../preferences";
import { BrandLogo } from "../BrandLogo";

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

type Props = { onLogin: (token: string) => void };

export function LoginScreen({ onLogin }: Props) {
  const { theme, t } = usePreferences();
  const styles = useThemedStyles(createStyles);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function login() {
    if (!email.trim() || !password) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const body = await response.json().catch(() => null);
      if (!response.ok || !body?.access_token) {
        throw new Error(body?.detail ?? "تعذر تسجيل الدخول");
      }
      onLogin(body.access_token);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "تعذر تسجيل الدخول");
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView style={styles.screen} behavior={Platform.OS === "ios" ? "padding" : undefined}>
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <View style={styles.brand}>
        <BrandLogo />
        <Text style={styles.title}>{t("ابدأ رحلة التعلم", "Start your learning journey")}</Text>
        <Text style={styles.subtitle}>{t("سجّل الدخول للوصول إلى دروسك وجلساتك.", "Sign in to access your lessons and sessions.")}</Text>
      </View>
      <View style={styles.form}>
        <TextInput
          value={email}
          onChangeText={setEmail}
          placeholder={t("البريد الإلكتروني", "Email")}
          accessibilityLabel={t("البريد الإلكتروني", "Email")}
          placeholderTextColor={theme.colors.muted}
          autoCapitalize="none"
          keyboardType="email-address"
          textAlign="left"
          autoComplete="email"
          style={styles.input}
        />
        <TextInput
          value={password}
          onChangeText={setPassword}
          placeholder={t("كلمة المرور", "Password")}
          accessibilityLabel={t("كلمة المرور", "Password")}
          placeholderTextColor={theme.colors.muted}
          secureTextEntry
          textAlign="left"
          autoComplete="current-password"
          style={styles.input}
        />
        {error && <Text accessibilityRole="alert" style={styles.error}>{t("تعذر تسجيل الدخول. تحقق من البيانات والاتصال ثم أعد المحاولة.", "Sign-in failed. Check your details and connection, then retry.")}</Text>}
        <Pressable accessibilityRole="button" style={styles.button} onPress={login} disabled={loading}>
          {loading ? <ActivityIndicator color={theme.colors.onPrimary} /> : <Text style={styles.buttonText}>{t("دخول", "Sign in")}</Text>}
        </Pressable>
      </View>
    </ScrollView></KeyboardAvoidingView>
  );
}

const createStyles = (theme: Theme, rtl: boolean) => StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.colors.background },
  content: { flexGrow: 1, padding: 24, justifyContent: "center" },
  brand: { backgroundColor: theme.colors.surface, borderRadius: 24, padding: 26, marginBottom: 18 },
  eyebrow: { color: theme.colors.heroAccent, fontSize: 12, fontWeight: "800", letterSpacing: 1.4, textAlign: rtl ? "right" : "left" },
  title: { color: theme.colors.text, fontSize: 30, fontWeight: "800", textAlign: rtl ? "right" : "left", marginTop: 18 },
  subtitle: { color: theme.colors.muted, fontSize: 15, lineHeight: 24, textAlign: rtl ? "right" : "left", marginTop: 10 },
  form: { backgroundColor: theme.colors.surface, borderRadius: 22, padding: 18 },
  input: { backgroundColor: theme.colors.background, borderRadius: 14, paddingHorizontal: 14, minHeight: 52, color: theme.colors.text, marginBottom: 12, writingDirection: "ltr" },
  button: { backgroundColor: theme.colors.primary, borderRadius: 14, minHeight: 52, alignItems: "center", justifyContent: "center", marginTop: 4 },
  buttonText: { color: theme.colors.onPrimary, fontSize: 16, fontWeight: "800" },
  error: { color: theme.colors.error, textAlign: rtl ? "right" : "left", marginBottom: 10 },
});
