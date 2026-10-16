import test from "node:test";
import assert from "node:assert/strict";
import { parseVoiceCommand, canExecute, MAX_TRANSCRIPT, normalizeCommand } from "../../packages/voice/commands.ts";
import { VoiceEngine } from "../../packages/voice/engine.ts";

test("Egyptian Arabic commands map only to the explicit allowlist", () => {
  for (const [text, action] of [["يا أكليث، افتح دروس الرياضيات", "math_lessons"], ["افتح التدريبات", "practice"],
    ["وريني تقدمي", "progress"], ["ارجع للصفحة الرئيسية", "home"], ["افتح الفصل بتاعي", "classrooms"]]) {
    assert.deepEqual(parseVoiceCommand(text), { kind: "navigate", action });
  }
  assert.deepEqual(parseVoiceCommand("وَرِّيني تَقَدُّمي"), { kind: "navigate", action: "progress" });
});
test("English and French phrases are extensible and deterministic", () => {
  for (const phrase of ["open practice", "ouvre les exercices"]) assert.equal(parseVoiceCommand(phrase).action, "practice");
  assert.equal(normalizeCommand("HEY AQLITH, OPEN HOME!"), "open home");
});
test("math and numbers remain exactly as spoken or edited, never evaluated", () => {
  for (const text of ["اشرحلي المعادلة دي", "اشرحلي ٢س + ٣ = ٧", "اشرحلي 17 - 26 = -9", "explain 2x + 3 = 7", "اشرحلي اتنين سين زائد ثلاثة يساوي سبعة"]) {
    assert.deepEqual(parseVoiceCommand(text), { kind: "tutor", question: text });
  }
});
test("ambiguous, multiple, dangerous and injected navigation is rejected", () => {
  for (const text of ["", "افتح", "افتح الفصل", "افتح التدريبات ووريني تقدمي", "submit exam", "انشر المحتوى", "غير الدرجة", "modify permissions", "open home; fetch('/admin')", "x".repeat(MAX_TRANSCRIPT + 1)]) {
    assert.deepEqual(parseVoiceCommand(text), { kind: "unknown" });
  }
});
test("teacher navigation requires the verified role and unknown actions cannot run", () => {
  const command = parseVoiceCommand("افتح فصولي كمدرس");
  for (const role of [null, "STUDENT", "SUPER_ADMIN", "teacher"]) assert.equal(canExecute(command, role), false);
  assert.equal(canExecute(command, "TEACHER"), true);
  assert.equal(canExecute({ kind: "unknown" }, "TEACHER"), false);
});
test("permission denial and connection failure are errors; retry starts fresh", async () => {
  const events = [];
  let fail = true;
  const provider = { available: true, cancel() {}, stop() {}, async start(locale, emit) {
    if (fail) throw Error("network");
    emit({ type: "state", state: "recording" });
    emit({ type: "error", code: "not-allowed" });
  } };
  const engine = new VoiceEngine(provider, event => events.push(event));
  await engine.start("ar-EG");
  assert.deepEqual(events.at(-1), { type: "error", code: "unavailable" });
  fail = false;
  await engine.start("ar-EG");
  assert.deepEqual(events.at(-1), { type: "error", code: "not-allowed" });
});
test("cancel invalidates late recognition; stopping delegates without executing", async () => {
  let callback;
  let stopped = 0;
  const events = [];
  const engine = new VoiceEngine({ available: true, cancel() {}, stop() { stopped++; }, async start(locale, emit) { callback = emit; } }, event => events.push(event));
  await engine.start("ar-EG"); engine.stop(); assert.equal(stopped, 1);
  engine.cancel(); callback({ type: "transcript", text: "open home" });
  assert.deepEqual(events.at(-1), { type: "state", state: "idle" });
});
test("finishing canceled permission request cannot abort a newer recording", async () => {
  const pending = [];
  let cancels = 0;
  const engine = new VoiceEngine({ available: true, cancel() { cancels++; }, stop() {}, start() { return new Promise(resolve => pending.push(resolve)); } }, () => {});
  const first = engine.start("ar-EG"); const second = engine.start("en-US");
  const expected = cancels; pending[0](); await first;
  assert.equal(cancels, expected); pending[1](); await second;
});
