# Tutor Mobile Foundation — Design Specification

**Status:** Approved; foundation implementation in progress.
**Date:** 2026-09-26
**Product:** Nexora Tutor AI

## 1. Goal and scope

Nexora Tutor AI is the first student-facing Nexora product. The first release is a mobile-first learning companion for Egyptian secondary students. It starts with Mathematics, Physics, and English and provides guided explanations, practice, assessment, and progress memory.

The student experience is delivered by a React Native + Expo application. A web companion serves guardians, content operators, and authorized administrators. Nexora Core remains the shared platform for identity, workspaces, agents, memory, knowledge, usage, billing, and audit.

The MVP is intentionally bounded. It does not include a full agent marketplace, unrestricted web search, live human tutoring, multi-country curricula, or a custom 3D rendering engine.

## 2. Product boundaries

The repository remains a modular product workspace:

```text
Ahmed-AI-Agent/
├── core/                         Nexora intelligence primitives
├── nexora_backend/               shared platform API
├── apps/tutor-mobile/            student mobile application
├── apps/tutor-web/               guardian/admin web companion
└── packages/contracts/           versioned API and shared types
```

Tutor-specific backend code is isolated under `nexora_backend/app/products/tutor/` and does not move curriculum or learner rules into `nexora_backend/app/ai/`. The existing `/health`, `/auth/*`, and `/ai/execute` contracts remain compatible while Tutor endpoints are introduced incrementally.

## 3. Runtime flow

```text
Student mobile request
  → authenticated Tutor API
  → identity and product policy checks
  → Tutor service
  → curriculum retrieval + subject agent
  → deterministic tools for calculations and assessment
  → memory and progress update
  → text/audio response with optional avatar state
```

The mobile client never receives provider secrets. Voice uses a backend provider abstraction and a resumable session. The avatar is a presentation layer: if voice or 3D rendering is unavailable, the same session continues in text without data loss.

## 4. Domain data

Nexora owns the shared identity and platform records: `User`, `Workspace`, subscription, usage, and audit records. Tutor owns only the educational records needed for the first release:

- `LearnerProfile`: grade, language, selected subjects, and learning preferences.
- `CurriculumVersion`, `Lesson`, and `Skill`: approved, versioned content.
- `LearningSession` and `Message`: a learner’s learning interaction.
- `AssessmentAttempt` and `SkillMastery`: scored practice and mastery state.
- `GuardianLink` and `Consent`: authorized access to a minor’s progress.

The LLM may produce explanations and suggestions, but it cannot directly write grades, mastery, or curriculum records. Those updates pass through validated services and deterministic assessment tools.

## 5. API surface

Tutor APIs are versioned and authenticated. The current intended surface is:

- `GET /api/v1/tutor/profile`
- `GET /api/v1/tutor/lessons`
- `POST /api/v1/tutor/sessions`
- `POST /api/v1/tutor/sessions/{session_id}/messages`
- `POST /api/v1/tutor/sessions/{session_id}/voice`
- `POST /api/v1/tutor/assessments/{assessment_id}/attempts`
- `GET /api/v1/tutor/progress`
- `GET /api/v1/guardian/children/{child_id}/progress`

The server derives the caller from the access token. A client-supplied `user_id` is never used as an authorization source. Existing platform APIs are not removed or silently redefined.

## 6. Authorization and child safety

The first policy roles are:

| Role | Allowed scope |
| --- | --- |
| Student | Own profile, sessions, assessments, and progress |
| Guardian | Explicitly linked children and their progress summaries |
| Content Editor | Curriculum drafts and published versions; no learner PII |
| Tutor Admin | Authorized cohorts and aggregate analytics |
| Platform Admin | Identity, workspaces, billing, platform configuration, and audit |

Every learner and guardian request is checked against workspace and relationship scope. Consent is recorded before guardian access. Product analytics are permission-scoped and contain no invented KPIs.

The first release keeps the tutor within the approved curriculum. It does not provide unrestricted browsing or unsupervised actions to minors. Safety, rate limits, audit events, and provider timeouts are handled server-side.

## 7. User experience

### Student mobile

The home screen presents three primary actions: continue learning, ask Tutor, and practice. The conversation supports text and voice, with real actions for “explain step by step”, “quiz me”, and “give me an example”. Each answer identifies the lesson or skill context when available. Progress is saved locally for the last active session and synchronized when connectivity returns.

### Guardian web

The web companion shows learning time, completed skills, weak areas, assessment results, and data-backed alerts. It does not expose unrestricted private conversation content by default.

### Content operations

The first curriculum can be imported and versioned from controlled content files. Authoring UI is a follow-up slice after the read-only learner loop is validated.

## 8. Failure handling

- Network loss: show the last synchronized state and queue safe progress events for retry.
- Voice provider timeout: keep the text response path available and allow retry.
- Missing curriculum context: explain that the lesson is unavailable instead of inventing an answer.
- Credit or rate limit exhaustion: return a clear recoverable state; never partially record a paid action.
- Duplicate submission: use request/session idempotency keys for assessment and progress writes.
- Unauthorized relationship: return a consistent denial without revealing whether another learner exists.

## 9. Acceptance and tests

The first implementation must prove:

1. A secondary student can authenticate, select a subject, ask a text question, and receive a curriculum-scoped answer.
2. The same session can accept voice input when the provider is available and fall back to text when it is not.
3. A deterministic practice attempt updates progress only after validation.
4. A guardian sees only explicitly linked child progress.
5. Student, guardian, content-editor, tutor-admin, and platform-admin permission tests pass.
6. No response or dashboard metric contains a hard-coded learner number.
7. Existing health, authentication, and compatibility tests continue to pass.
8. Mobile contract tests validate the shared API schemas and offline retry behavior.

Operational checks include structured audit events, latency/error metrics, and a production build for both mobile and web shells.

## 10. Delivery slices

1. Stabilize shared auth/permission contracts and mount the existing AI router without changing its public schema.
2. Add Tutor schemas, read-only curriculum fixtures, and authenticated profile/session APIs.
3. Build the student mobile shell and text learning loop.
4. Add deterministic practice/progress and offline synchronization.
5. Add voice provider abstraction and guardian web read-only progress.
6. Run security, contract, and mobile/web production checks before expanding curriculum.
