import type { Metadata } from "next";
import localFont from "next/font/local";
import type { CSSProperties } from "react";
import "./globals.css";
import { PreferencesProvider } from "./preferences";
import { palettes, preferenceKey } from "../../../packages/presentation/preferences";
import { brandBackgrounds } from "../../../packages/presentation/brand";

const cairo = localFont({
  src: [
    { path: "./fonts/cairo/Cairo_400Regular.ttf", weight: "400" },
    { path: "./fonts/cairo/Cairo_600SemiBold.ttf", weight: "600" },
    { path: "./fonts/cairo/Cairo_700Bold.ttf", weight: "700" },
    { path: "./fonts/cairo/Cairo_800ExtraBold.ttf", weight: "800" },
  ],
  variable: "--font-cairo", display: "swap", fallback: ["Arial", "sans-serif"],
});

// Only fixed, validated preference values are applied; no user HTML is injected.
const bootstrap = `try{const p=JSON.parse(localStorage.getItem(${JSON.stringify(preferenceKey)})||'null')||{};const r=document.documentElement;const a=p.appearance==='light'||p.appearance==='dark'?p.appearance:'system';const s=a==='system'?(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):a;r.lang=p.language==='en'?'en':'ar';r.dir=r.lang==='ar'?'rtl':'ltr';r.dataset.theme=s;r.style.colorScheme=s;const c=${JSON.stringify(palettes)}[s];for(const k in c)r.style.setProperty('--'+k,c[k]);}catch{}`;

export const metadata: Metadata = {
  title: "AQLITH Learn",
  description: "Guardian and curriculum companion for AQLITH Learn",
  icons: { icon: "/brand/aqlith-app-icon.png", apple: "/brand/aqlith-app-icon.png" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ar" dir="rtl" suppressHydrationWarning style={{ ...Object.fromEntries(Object.entries(palettes.light).map(([key, value]) => [`--${key}`, value])), "--brand-light": brandBackgrounds.light, "--brand-dark": brandBackgrounds.dark } as CSSProperties}>
      <head><script dangerouslySetInnerHTML={{ __html: bootstrap }} /></head>
      <body className={cairo.variable}><PreferencesProvider>{children}</PreferencesProvider></body>
    </html>
  );
}
