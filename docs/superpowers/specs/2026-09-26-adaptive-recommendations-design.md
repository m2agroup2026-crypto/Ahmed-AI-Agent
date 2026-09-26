# NEXORA Tutor Adaptive Recommendations

## Goal

Give each learner one next practice action derived from their persisted attempts and
currently published, rights-approved curriculum. The feature must never invent a
score, expose unpublished material, or silently use foundation fixtures as a
recommendation source.

## Architecture

The recommendation path is deliberately small and deterministic:

1. The authenticated user requests `/api/v1/tutor/recommendation`.
2. The service filters questions through the same published-content and source-
   approval rules used by the practice API.
3. The user's active progress is calculated from `AssessmentAttempt` rows.
4. The service selects an unattempted question in the weakest skill when one is
   known; otherwise it selects the first unattempted question in the requested
   subject/version. When all questions for the focus skill were attempted, the
   service returns a review recommendation for that same skill.
5. The response includes the question, curriculum/source provenance, and a stable
   reason code for bilingual clients.

No new permission, authentication, or database model is required. The existing
  authenticated-user boundary remains the source of truth.

## API contract

`GET /api/v1/tutor/recommendation?subject_code=&curriculum_version=`

- `subject_code` is optional; when omitted the learner profile's first configured
  subject is preferred, then the first available published subject.
- `curriculum_version` defaults to `egypt-secondary-2026`.
- `reason_code` is one of `start_learning`, `practice_focus_skill`,
  `review_focus_skill`, or `continue_curriculum`.
- `question` is the same safe practice question shape already used by
  `/practice/next`; accepted answers are never returned.
- No published question returns HTTP 404, matching the existing practice API.

## Mobile experience

The Home screen consumes the recommendation endpoint and shows a compact “next
step” card. The action opens the existing Practice screen with the recommended
subject, curriculum version, lesson, and skill. If the endpoint has no content or
is temporarily unavailable, the existing lessons and progress experience remains
usable.

## Safety and tests

Tests prove that recommendations are scoped to the authenticated learner, prefer
the weakest skill, never select draft/unapproved content, preserve provenance, and
fall back to review only after the focus skill's questions have been attempted.
The guardian view is intentionally not implemented in this increment because the
repository has no explicit guardian-to-learner relationship or consent model; any
future guardian endpoint must add that authorization boundary first.
