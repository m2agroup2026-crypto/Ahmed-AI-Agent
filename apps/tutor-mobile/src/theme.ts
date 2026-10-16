import { useMemo } from "react";
import type { Palette } from "../../../packages/presentation/preferences";
import { usePreferences } from "./preferences";

export type Theme = { colors: Palette; radius: number };
export function useThemedStyles<T>(factory: (theme: Theme, rtl: boolean) => T) {
  const { theme, rtl } = usePreferences();
  return useMemo(() => factory(theme, rtl), [factory, theme, rtl]);
}
