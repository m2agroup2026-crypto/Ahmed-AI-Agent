import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { theme } from "../theme";

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

type Props = { onLogin: (token: string) => void };

export function LoginScreen({ onLogin }: Props) {
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
    <View style={styles.screen}>
      <View style={styles.brand}>
        <Text style={styles.eyebrow}>NEXORA TUTOR</Text>
        <Text style={styles.title}>ابدأ رحلة التعلم</Text>
        <Text style={styles.subtitle}>سجّل الدخول للوصول إلى دروسك وجلساتك.</Text>
      </View>
      <View style={styles.form}>
        <TextInput
          value={email}
          onChangeText={setEmail}
          placeholder="البريد الإلكتروني"
          placeholderTextColor={theme.colors.muted}
          autoCapitalize="none"
          keyboardType="email-address"
          textAlign="right"
          style={styles.input}
        />
        <TextInput
          value={password}
          onChangeText={setPassword}
          placeholder="كلمة المرور"
          placeholderTextColor={theme.colors.muted}
          secureTextEntry
          textAlign="right"
          style={styles.input}
        />
        {error && <Text style={styles.error}>{error}</Text>}
        <Pressable style={styles.button} onPress={login} disabled={loading}>
          {loading ? <ActivityIndicator color={theme.colors.white} /> : <Text style={styles.buttonText}>دخول</Text>}
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.colors.surface, padding: 24, justifyContent: "center" },
  brand: { backgroundColor: theme.colors.navy, borderRadius: 24, padding: 26, marginBottom: 18 },
  eyebrow: { color: theme.colors.gold, fontSize: 12, fontWeight: "800", letterSpacing: 1.4, textAlign: "right" },
  title: { color: theme.colors.white, fontSize: 30, fontWeight: "800", textAlign: "right", marginTop: 18 },
  subtitle: { color: "#c8d5e5", fontSize: 15, lineHeight: 24, textAlign: "right", marginTop: 10 },
  form: { backgroundColor: theme.colors.white, borderRadius: 22, padding: 18 },
  input: { backgroundColor: theme.colors.surface, borderRadius: 14, paddingHorizontal: 14, height: 52, color: theme.colors.ink, marginBottom: 12 },
  button: { backgroundColor: theme.colors.teal, borderRadius: 14, height: 52, alignItems: "center", justifyContent: "center", marginTop: 4 },
  buttonText: { color: theme.colors.white, fontSize: 16, fontWeight: "800" },
  error: { color: theme.colors.danger, textAlign: "right", marginBottom: 10 },
});
