"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { BrandLogo } from "./brand-logo";
import { defaults, direction, palettes, parsePreferences, preferenceKey, resolveAppearance, translate,
  type Appearance, type Language, type Preferences } from "../../../packages/presentation/preferences";

type Context = Preferences & { setLanguage: (language: Language) => void; setAppearance: (appearance: Appearance) => void;
  t: (ar: string, en: string) => string };
const PreferencesContext = createContext<Context | null>(null);

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useState<Preferences>(defaults);
  const [ready, setReady] = useState(false);
  const [storageError, setStorageError] = useState(false);
  useEffect(() => {
    try { setPreferences(parsePreferences(localStorage.getItem(preferenceKey))); } catch { setStorageError(true); }
    setReady(true);
    const sync = (event: StorageEvent) => { if (event.key === preferenceKey) setPreferences(parsePreferences(event.newValue)); };
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);
  useEffect(() => {
    if (!ready) return;
    const root = document.documentElement;
    const media = matchMedia("(prefers-color-scheme: dark)");
    const update = () => {
      const resolved = resolveAppearance(preferences.appearance, media.matches ? "dark" : "light");
      root.dataset.theme = resolved;
      root.dataset.appearance = preferences.appearance;
      root.style.colorScheme = resolved;
      for (const [key, value] of Object.entries(palettes[resolved])) root.style.setProperty(`--${key}`, value);
    };
    root.lang = preferences.language; root.dir = direction(preferences.language);
    update(); media.addEventListener("change", update);
    try { localStorage.setItem(preferenceKey, JSON.stringify(preferences)); setStorageError(false); } catch { setStorageError(true); }
    return () => media.removeEventListener("change", update);
  }, [preferences, ready]);
  const value: Context = { ...preferences,
    setLanguage: language => setPreferences(previous => ({ ...previous, language })),
    setAppearance: appearance => setPreferences(previous => ({ ...previous, appearance })),
    t: (ar, en) => translate(preferences.language, ar, en) };
  return <PreferencesContext.Provider value={value}>
    <PreferenceControls />
    {storageError && <p role="status" className="preference-error">{value.t("تعذر حفظ التفضيلات في هذا المتصفح.", "Preferences could not be saved in this browser.")}</p>}
    {children}
  </PreferencesContext.Provider>;
}

export function usePreferences() {
  const value = useContext(PreferencesContext);
  if (!value) throw new Error("PreferencesProvider required");
  return value;
}

function PreferenceControls() {
  const { language, appearance, setLanguage, setAppearance, t } = usePreferences();
  return <aside className="preferences" aria-label={t("تفضيلات العرض", "Display preferences")}>
    <a className="brand-link" href="/" aria-label="AQLITH Learn"><BrandLogo /></a>
    <div role="group" aria-label={t("اللغة", "Language")}>
      <button type="button" lang="ar" aria-label="العربية / AR" aria-pressed={language === "ar"} onClick={() => setLanguage("ar")}>AR</button>
      <button type="button" lang="en" aria-label="English / EN" aria-pressed={language === "en"} onClick={() => setLanguage("en")}>EN</button>
    </div>
    <div role="group" aria-label="Appearance / المظهر">
      {(["light", "dark", "system"] as const).map(item => {
        const label = item === "light" ? t("فاتح", "Light") : item === "dark" ? t("داكن", "Dark") : t("النظام", "System");
        return <button key={item} type="button" aria-label={label} title={label} aria-pressed={appearance === item} onClick={() => setAppearance(item)}>
          <span aria-hidden="true">{item === "light" ? "☀" : item === "dark" ? "☾" : "▣"}</span>
        </button>;
      })}
    </div>
  </aside>;
}
