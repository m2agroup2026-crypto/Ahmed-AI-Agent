import assert from "node:assert/strict";
import test from "node:test";
import { controlState, needsGrantRenewal, mediaPermissions } from "../lib/live-client.ts";

const session = {
  state: "live", participant: { left_at: null, revoked: false, can_speak: false },
  capabilities: { media: false, teacher_audio: false, teacher_video: false, screen_share: false,
    enforced_membership: false, moderated_audio: false, metadata_preview: true },
};

test("ending and revocation override reconnecting", () => {
  for (const state of ["ending", "ended", "expired"]) {
    assert.equal(controlState({ ...session, state }, false), "ended");
  }
  assert.equal(controlState({ ...session, participant: { ...session.participant, revoked: true } }, false), "revoked");
});

test("network recovery reflects application presence only", () => {
  assert.equal(controlState(session, false), "reconnecting");
  assert.equal(controlState(session, true), "control_connected");
  assert.equal(controlState({ ...session, participant: null }, true), "idle");
  assert.equal(controlState({ ...session, participant: { ...session.participant, left_at: "2026-10-15" } }, true), "idle");
});

test("expiry is renewed early and malformed expiry fails closed", () => {
  assert.equal(needsGrantRenewal(new Date(60000).toISOString(), 0), false);
  assert.equal(needsGrantRenewal(new Date(30000).toISOString(), 0), true);
  assert.equal(needsGrantRenewal("invalid", 0), true);
});

test("metadata permissions never enable actual microphones or cameras", () => {
  assert.deepEqual(mediaPermissions(session, true, true), { audio: false, video: false, screen: false });
  const allowed = { ...session, participant: { ...session.participant, can_speak: true } };
  assert.equal(mediaPermissions(allowed, false, true).audio, false);
});

test("future media still requires adapter, remote enforcement and role approval", () => {
  const supported = { ...session, capabilities: { media: true, teacher_audio: true, teacher_video: true,
    screen_share: true, enforced_membership: true, moderated_audio: true } };
  assert.deepEqual(mediaPermissions(supported, true, false), { audio: false, video: false, screen: false });
  assert.deepEqual(mediaPermissions(supported, true, true), { audio: true, video: true, screen: true });
  assert.deepEqual(mediaPermissions(supported, false, true), { audio: false, video: false, screen: false });
  assert.equal(mediaPermissions({ ...supported, participant: { ...session.participant, can_speak: true } }, false, true).audio, true);
  assert.equal(mediaPermissions({ ...supported, state: "ended" }, true, true).audio, false);
  assert.equal(mediaPermissions({ ...supported, participant: null }, true, true).audio, false);
  assert.equal(mediaPermissions({ ...supported, participant: { ...session.participant, revoked: true } }, true, true).video, false);
  assert.equal(mediaPermissions({ ...supported, participant: { ...session.participant, left_at: "2026-10-15" } }, true, true).screen, false);
});
