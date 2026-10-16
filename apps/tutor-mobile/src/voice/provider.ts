import { requireOptionalNativeModule } from "expo-modules-core";
import { Platform } from "react-native";
import { MAX_RECORDING_MS, MAX_TRANSCRIPT, type VoiceLocale } from "../../../../packages/voice/commands";
import type { RecognitionProvider, VoiceEvent } from "../../../../packages/voice/engine";
import type { ExpoSpeechRecognitionModuleType } from "expo-speech-recognition/build/ExpoSpeechRecognitionModule.types";

// A missing native module (Expo Go) must never crash the app or fabricate recognition.
type Listener = { remove(): void };
type BrowserSpeech = {
  lang: string; continuous: boolean; interimResults: boolean; maxAlternatives: number;
  onstart: (() => void) | null; onend: (() => void) | null; onaudioend: (() => void) | null;
  onresult: ((event: { results: { transcript: string }[][] }) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  start(): void; stop(): void; abort(): void;
};
export function createRecognitionProvider(): RecognitionProvider {
  const native = Platform.OS === "web" ? null : requireOptionalNativeModule<ExpoSpeechRecognitionModuleType>("ExpoSpeechRecognition");
  const browser = globalThis as typeof globalThis & { SpeechRecognition?: new () => BrowserSpeech; webkitSpeechRecognition?: new () => BrowserSpeech };
  const webConstructor = Platform.OS === "web" ? browser.SpeechRecognition ?? browser.webkitSpeechRecognition : null;
  let listeners: Listener[] = [];
  let web: BrowserSpeech | undefined;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let timeout: ReturnType<typeof setTimeout> | undefined;
  let epoch = 0;
  const clear = () => { clearTimeout(timer); clearTimeout(timeout); listeners.forEach(item => item.remove()); listeners = []; };
  const cancel = () => { epoch++; clear(); if (web) { web.onstart = web.onresult = web.onerror = web.onend = web.onaudioend = null; web.abort(); web = undefined; } native?.abort(); };
  return {
    available: Boolean(webConstructor || native?.isRecognitionAvailable()),
    async start(locale: VoiceLocale, emit) {
      cancel();
      const current = epoch;
      let heard = false;
      let failed = false;
      const send = (event: VoiceEvent) => { if (current === epoch) emit(event); };
      const error = (code: string) => { failed = true; send({ type: "error", code }); cancel(); };
      const result = (text: string) => {
        if (!text.trim()) return;
        if (text.length > MAX_TRANSCRIPT) { error("too-long"); return; }
        heard = true; send({ type: "transcript", text });
      };
      const end = () => { clear(); if (!failed) heard ? send({ type: "state", state: "review" }) : error("no-speech"); };
      const started = () => {
        send({ type: "state", state: "recording" });
        timer = setTimeout(() => { send({ type: "state", state: "processing" }); this.stop(); }, MAX_RECORDING_MS);
      };
      timeout = setTimeout(() => error("timeout"), MAX_RECORDING_MS + 15_000);
      if (Platform.OS === "web") {
        if (!webConstructor) { error("unavailable"); return; }
        web = new webConstructor();
        web.lang = locale; web.continuous = false; web.interimResults = false; web.maxAlternatives = 1;
        web.onstart = started;
        web.onresult = event => result(event.results[0]?.[0]?.transcript ?? "");
        web.onerror = event => error(event.error);
        web.onaudioend = () => send({ type: "state", state: "processing" });
        web.onend = end;
        web.start();
      } else {
        if (!native?.isRecognitionAvailable()) { error("unavailable"); return; }
        const permission = await native.requestPermissionsAsync();
        if (current !== epoch) return;
        if (!permission.granted) { error("not-allowed"); return; }
        listeners = [native.addListener("start", started), native.addListener("end", end), native.addListener("audioend", () => send({ type: "state", state: "processing" })),
          native.addListener("result", event => { if (event.isFinal) result(event.results[0]?.transcript ?? ""); }),
          native.addListener("error", event => error(event.error))];
        native.start({ lang: locale, interimResults: false, continuous: false, maxAlternatives: 1,
          recordingOptions: { persist: false } });
      }
    },
    stop() { clearTimeout(timer); if (web) web.stop(); else native?.stop(); },
    cancel,
  };
}
