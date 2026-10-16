export type LiveCapabilities = {
  media: boolean; teacher_video: boolean; teacher_audio: boolean; screen_share: boolean;
  enforced_membership: boolean; moderated_audio: boolean; recording: boolean; metadata_preview: boolean;
};
export type LiveParticipant = {
  user_id: number; role: "teacher" | "student"; joined_at: string; last_seen_at: string;
  left_at: string | null; revoked: boolean; hand_raised: boolean; can_speak: boolean;
  presence_source: "application_heartbeat";
};
export type LiveSession = {
  id: string; classroom_id: string; title: string; provider: string;
  capabilities: LiveCapabilities; state: "scheduled" | "live" | "ending" | "ended" | "expired";
  starts_at: string; ends_at: string; recording_notice: { ar: string; en: string } | null;
  notice_version: number; consented: boolean; recording_state: string;
  participant: LiveParticipant | null;
};
export type LiveGrant = {
  session: LiveSession; access_token: string; expires_at: string;
  token_purpose: "aqlith_application_presence_only"; media_credentials: null;
};
// A future media adapter must bind these operations to SDK capability changes,
// tenant policy, remote revocation and call-ended events before enabling controls.
export interface LiveMediaClient {
  setAudio(enabled: boolean): Promise<void>;
  setVideo(enabled: boolean): Promise<void>;
  setScreenSharing(enabled: boolean): Promise<void>;
  reconnect(): Promise<void>;
  disconnect(): Promise<void>;
}
