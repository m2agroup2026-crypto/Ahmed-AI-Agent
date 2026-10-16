import type { LiveSession } from "@contracts/live";

export type ControlConnection = "idle" | "joining" | "control_connected" | "reconnecting" | "ended" | "revoked";

export function controlState(session: LiveSession, online: boolean): ControlConnection {
  if (["ended", "ending", "expired"].includes(session.state)) return "ended";
  if (session.participant?.revoked) return "revoked";
  if (!online) return "reconnecting";
  if (session.participant && !session.participant.left_at) return "control_connected";
  return "idle";
}

export function needsGrantRenewal(expiresAt: string, timestamp = Date.now()): boolean {
  const expires = Date.parse(expiresAt);
  return !Number.isFinite(expires) || expires - timestamp <= 30000;
}

export function mediaPermissions(session: LiveSession, teacher: boolean, adapterReady: boolean) {
  const caps = session.capabilities;
  const enabled = adapterReady && caps.media && caps.enforced_membership && caps.moderated_audio
    && session.state === "live" && !!session.participant && !session.participant.revoked && !session.participant.left_at;
  return {
    audio: enabled && (teacher ? caps.teacher_audio : !!session.participant?.can_speak),
    video: enabled && teacher && caps.teacher_video,
    screen: enabled && teacher && caps.screen_share,
  };
}
