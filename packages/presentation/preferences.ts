export type Language = "ar" | "en";
export type Appearance = "light" | "dark" | "system";
export type Preferences = { language: Language; appearance: Appearance };
export const preferenceKey = "aqlith.preferences.v1";
export const defaults: Preferences = { language: "ar", appearance: "system" };

export function parsePreferences(raw: string | null): Preferences {
  try {
    const value: unknown = JSON.parse(raw ?? "null");
    if (!value || typeof value !== "object") return { ...defaults };
    const item = value as Record<string, unknown>;
    return {
      language: item.language === "en" ? "en" : "ar",
      appearance: item.appearance === "light" || item.appearance === "dark" ? item.appearance : "system",
    };
  } catch { return { ...defaults }; }
}

export function resolveAppearance(appearance: Appearance, system: string | null | undefined) {
  return appearance === "system" ? (system === "dark" ? "dark" : "light") : appearance;
}

export function direction(language: Language) { return language === "ar" ? "rtl" : "ltr"; }
export function translate(language: Language, ar: string, en: string) { return language === "ar" ? ar : en; }

export const palettes = {
  light: {
    text: "#10233f", muted: "#52647a", background: "#f5f8fb", surface: "#ffffff",
    primary: "#086963", onPrimary: "#ffffff", border: "#b9c8d8", accent: "#835b13",
    error: "#a52835", success: "#08634d", successSurface: "#e4f4ed", accentSurface: "#e0f2ef",
    hero: "#0b1d35", heroText: "#ffffff", heroMuted: "#c8d5e5", heroAccent: "#f0c66b",
    shadow: "#10233f", focus: "#086963",
  },
  dark: {
    text: "#edf3fb", muted: "#b4c4d6", background: "#091323", surface: "#14243a",
    primary: "#74dfce", onPrimary: "#082a27", border: "#63768d", accent: "#f0c66b",
    error: "#ffb3bb", success: "#91e3bd", successSurface: "#163e33", accentSurface: "#163c3a",
    hero: "#102039", heroText: "#ffffff", heroMuted: "#c8d5e5", heroAccent: "#f0c66b",
    shadow: "#000000", focus: "#74dfce",
  },
};
export type Palette = typeof palettes.light;
