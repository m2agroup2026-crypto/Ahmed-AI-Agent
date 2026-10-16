// Official content is selected exclusively by backend metadata, never UI locale.
export function declaredText(language: string | null | undefined, ar: string, en: string) {
  return language === "ar" ? ar : language === "en" ? en : null;
}

export function contentDirection(language: string | null | undefined) {
  return language === "ar" ? "rtl" : language === "en" ? "ltr" : "auto";
}

export function mathRuns(text: string): { text: string; math: boolean }[] {
  const pattern = /[+\-−]?[0-9٠-٩۰-۹A-Za-z]+(?:[.,][0-9٠-٩۰-۹]+)?(?:\s*[+\-−*/×÷=<>≤≥^]\s*[+\-−]?[0-9٠-٩۰-۹A-Za-z]+(?:[.,][0-9٠-٩۰-۹]+)?)+/g;
  const runs: { text: string; math: boolean }[] = [];
  let cursor = 0;
  for (const match of text.matchAll(pattern)) {
    const start = match.index;
    if (start > cursor) runs.push({ text: text.slice(cursor, start), math: false });
    runs.push({ text: match[0], math: true });
    cursor = start + match[0].length;
  }
  if (cursor < text.length) runs.push({ text: text.slice(cursor), math: false });
  return runs;
}

// Unicode LTR isolates affect presentation only; source strings are never mutated.
export function isolateMath(text: string) {
  return mathRuns(text).map(run => run.math ? `\u2066${run.text}\u2069` : run.text).join("");
}
