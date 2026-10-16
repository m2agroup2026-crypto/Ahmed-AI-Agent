import AsyncStorage from "@react-native-async-storage/async-storage";
import { createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { ActivityIndicator, Platform, Pressable, useColorScheme, View } from "react-native";
import { Text } from "./typography";
import { SafeAreaView } from "react-native-safe-area-context";
import { defaults, direction, palettes, parsePreferences, preferenceKey, resolveAppearance, translate,
  type Appearance, type Language, type Palette, type Preferences } from "../../../packages/presentation/preferences";

type Context = Preferences & {
  theme: { colors: Palette; radius: number }; dark: boolean; rtl: boolean;
  setLanguage: (language: Language) => void; setAppearance: (appearance: Appearance) => void;
  t: (ar: string, en: string) => string;
};
const PreferencesContext = createContext<Context | null>(null);

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useState<Preferences>(defaults);
  const [ready, setReady] = useState(false);
  const [storageError, setStorageError] = useState(false);
  const writes = useRef(Promise.resolve());
  const system = useColorScheme();
  const dark = resolveAppearance(preferences.appearance, system) === "dark";
  const colors = palettes[dark ? "dark" : "light"];
  useEffect(() => {
    if (Platform.OS === "web" && typeof document !== "undefined") {
      document.documentElement.lang = preferences.language;
      document.documentElement.dir = direction(preferences.language);
      document.documentElement.style.colorScheme = dark ? "dark" : "light";
    }
  }, [preferences.language, dark]);
  useEffect(() => {
    let active = true;
    AsyncStorage.getItem(preferenceKey).then(raw => { if (active) setPreferences(parsePreferences(raw)); })
      .catch(() => { if (active) setStorageError(true); }).finally(() => { if (active) setReady(true); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (!ready) return;
    writes.current = writes.current.then(() => AsyncStorage.setItem(preferenceKey, JSON.stringify(preferences)))
      .then(() => setStorageError(false)).catch(() => setStorageError(true));
  }, [preferences, ready]);
  const value = useMemo<Context>(() => ({
    ...preferences, theme: { colors, radius: 18 }, dark, rtl: direction(preferences.language) === "rtl",
    setLanguage: language => setPreferences(previous => ({ ...previous, language })),
    setAppearance: appearance => setPreferences(previous => ({ ...previous, appearance })),
    t: (ar, en) => translate(preferences.language, ar, en),
  }), [preferences, colors, dark]);
  return <PreferencesContext.Provider value={value}>
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background, direction: "ltr" }}>
      {ready ? children : <ActivityIndicator accessibilityLabel="Loading preferences / تحميل التفضيلات" color={colors.primary} />}
      {storageError && <Text accessibilityRole="alert" style={{ color: colors.error, padding: 12 }}>{value.t("تعذر حفظ التفضيلات على الجهاز.", "Preferences could not be saved on this device.")}</Text>}
    </SafeAreaView>
  </PreferencesContext.Provider>;
}

export function usePreferences() {
  const value = useContext(PreferencesContext);
  if (!value) throw new Error("PreferencesProvider required");
  return value;
}

export function PreferenceControls() {
  const { language, appearance, setLanguage, setAppearance, theme: { colors }, rtl, t } = usePreferences();
  const control = (selected: boolean) => ({ minHeight: 44, minWidth: 44, paddingHorizontal: 12, paddingVertical: 12,
    borderRadius: 10, borderWidth: 1, borderColor: colors.border,
    backgroundColor: selected ? colors.primary : colors.surface });
  return <View style={{ padding: 12, gap: 8, backgroundColor: colors.background }}>
    <View accessibilityRole="radiogroup" accessibilityLabel={t("اللغة", "Language")} style={{ flexDirection: rtl ? "row-reverse" : "row", gap: 8, flexWrap: "wrap" }}>
      {(["ar", "en"] as const).map(item => <Pressable key={item} accessibilityRole="radio" accessibilityState={{ checked: language === item }} aria-checked={language === item}
        accessibilityLabel={item === "ar" ? "العربية / AR" : "English / EN"} style={control(language === item)} onPress={() => setLanguage(item)}>
        <Text style={{ color: language === item ? colors.onPrimary : colors.text }}>{item.toUpperCase()}</Text>
      </Pressable>)}
    </View>
    <View accessibilityRole="radiogroup" accessibilityLabel={t("المظهر", "Appearance")} style={{ flexDirection: rtl ? "row-reverse" : "row", gap: 8, flexWrap: "wrap" }}>
      {(["light", "dark", "system"] as const).map(item => <Pressable key={item} accessibilityRole="radio" accessibilityState={{ checked: appearance === item }} aria-checked={appearance === item}
        accessibilityLabel={item === "light" ? t("فاتح", "Light") : item === "dark" ? t("داكن", "Dark") : t("النظام", "System")}
        style={control(appearance === item)} onPress={() => setAppearance(item)}>
        <Text aria-hidden accessible={false} style={{ color: appearance === item ? colors.onPrimary : colors.text, fontSize: 20 }}>{item === "light" ? "☀" : item === "dark" ? "☾" : "▣"}</Text>
      </Pressable>)}
    </View>
  </View>;
}
