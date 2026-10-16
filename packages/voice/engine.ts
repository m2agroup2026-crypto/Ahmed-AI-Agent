import type { VoiceLocale } from "./commands.ts";
export type VoiceState = "idle" | "permission" | "recording" | "processing" | "review" | "error";
export type VoiceEvent = { type: "state"; state: VoiceState } | { type: "transcript"; text: string } | { type: "error"; code: string };
export interface RecognitionProvider {
  readonly available: boolean;
  start(locale: VoiceLocale, emit: (event: VoiceEvent) => void): Promise<void>;
  stop(): void;
  cancel(): void;
}
// Each run has an identity: callbacks from a canceled session cannot restore a transcript.
export class VoiceEngine {
  private generation = 0;
  constructor(private provider: RecognitionProvider, private emit: (event: VoiceEvent) => void) {}
  async start(locale: VoiceLocale) {
    this.cancel();
    const generation = this.generation;
    this.emit({ type: "state", state: "permission" });
    try {
      await this.provider.start(locale, event => { if (generation === this.generation) this.emit(event); });
    } catch {
      if (generation === this.generation) { this.provider.cancel(); this.emit({ type: "error", code: "unavailable" }); }
    }
  }
  stop() { this.provider.stop(); }
  cancel() { this.generation++; this.provider.cancel(); this.emit({ type: "state", state: "idle" }); }
}
