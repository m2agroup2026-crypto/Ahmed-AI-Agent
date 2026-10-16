import assert from "node:assert/strict";
import test from "node:test";
import { defaults, direction, palettes, parsePreferences, resolveAppearance, translate } from "../../packages/presentation/preferences.ts";
import { declaredText, contentDirection, mathRuns, isolateMath } from "../../packages/presentation/content.ts";
import { officialQuestion, officialAnswerLocale } from "../../apps/tutor-mobile/src/learning.ts";

test("Arabic and system are the defaults, including damaged storage", () => {
  for (const raw of [null, "bad JSON", "null", "[]", '"en"', '{"language":"fr","appearance":"evil"}']) {
    assert.deepEqual(parsePreferences(raw), defaults);
  }
});

test("language and appearance survive independent preference updates", () => {
  let value = parsePreferences('{"language":"en","appearance":"dark"}');
  value = parsePreferences(JSON.stringify({ ...value, language: "ar" }));
  assert.deepEqual(value, { language: "ar", appearance: "dark" });
  value = parsePreferences(JSON.stringify({ ...value, appearance: "system" }));
  assert.deepEqual(value, { language: "ar", appearance: "system" });
});

test("system changes affect system mode only", () => {
  for (const system of ["light", "dark"]) {
    assert.equal(resolveAppearance("system", system), system);
    assert.equal(resolveAppearance("light", system), "light");
    assert.equal(resolveAppearance("dark", system), "dark");
  }
  assert.equal(resolveAppearance("system", null), "light");
});

test("interface language selects labels and layout direction", () => {
  assert.equal(direction("ar"), "rtl"); assert.equal(direction("en"), "ltr");
  assert.equal(translate("ar", "دخول", "Sign in"), "دخول");
  assert.equal(translate("en", "دخول", "Sign in"), "Sign in");
});

test("official language is declared, never inferred from UI or alternate text", () => {
  assert.equal(declaredText("ar", "عربي", "English"), "عربي");
  assert.equal(declaredText("en", "عربي", "English"), "English");
  for (const language of [null, undefined, "fr"]) assert.equal(declaredText(language, "عربي", "English"), null);
  assert.equal(declaredText("ar", "", "English"), "");
  assert.equal(contentDirection(null), "auto");
});

test("math isolation preserves exact curriculum characters and operand order", () => {
  for (const text of ["احسب 17 - 26 = -9", "Solve 2x + 3 = 7", "الناتج ١٧ + ٢٦", "Plain text"]) {
    assert.equal(mathRuns(text).map(run => run.text).join(""), text);
    assert.equal(isolateMath(text).replace(/[\u2066\u2069]/g, ""), text);
  }
  assert(mathRuns("احسب 17 - 26").some(run => run.math && run.text === "17 - 26"));
  assert(mathRuns("شرح: 17 - 26 = -9.").some(run => run.math && run.text === "17 - 26 = -9"));
});

test("mobile choice identity and answer locale remain official during UI changes", () => {
  const question = { content_language: "en", prompt_en: "17 - 26", prompt_ar: "بديل",
    options_en: [{ id: "a", label: "-9" }], options_ar: [{ id: "a", label: "-٩" }] };
  for (const language of ["ar", "en"]) {
    translate(language, "إجابة", "Answer");
    assert.equal(officialQuestion(question).prompt, "17 - 26");
    assert.deepEqual(officialQuestion(question).choices, question.options_en);
    assert.equal(officialAnswerLocale(question), "en-US");
  }
  assert.equal(officialQuestion({ ...question, content_language: null }), null);
});

function luminance(hex) {
  const rgb = hex.slice(1).match(/../g).map(v => parseInt(v, 16) / 255)
    .map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
  return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
}
function contrast(a, b) {
  const values = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (values[0] + .05) / (values[1] + .05);
}
for (const [name, c] of Object.entries(palettes)) test(`${name}: semantic text meets WCAG AA contrast`, () => {
  for (const [foreground, background] of [[c.text, c.surface], [c.text, c.background], [c.muted, c.surface],
    [c.onPrimary, c.primary], [c.heroText, c.hero], [c.heroMuted, c.hero], [c.heroAccent, c.hero],
    [c.error, c.surface], [c.primary, c.surface], [c.text, c.successSurface], [c.primary, c.accentSurface]]) {
    assert(contrast(foreground, background) >= 4.5, `${name}: ${foreground} on ${background}`);
  }
  assert(contrast(c.focus, c.surface) >= 3);
});
