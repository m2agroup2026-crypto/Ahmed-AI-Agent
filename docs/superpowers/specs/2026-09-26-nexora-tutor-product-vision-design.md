# NEXORA TUTOR — Product Vision and Launch Design

**Status:** Approved for product planning; implementation follows the review gates in this document.
**Date:** 2026-09-26
**Product:** NEXORA TUTOR
**Arabic descriptor:** نيكسورا — مدرسك الذكي
**Tagline:** افهم أسرع، اتدرّب بذكاء، واتقدّم بثقة.

## 1. Product decision

NEXORA TUTOR is the first student-facing product in the broader NEXORA AI ecosystem. It is a mobile-first AI learning companion for Egyptian secondary students. The first curriculum release covers Mathematics, Physics, and English, with Arabic-first interaction and English support.

NEXORA remains the platform brand. TUTOR is the education product. The product name is clear enough for students and guardians, while the platform boundary keeps later products such as enterprise and institutional offerings independent.

Before public registration or paid acquisition, the name must pass trademark, domain, application-store, and social-handle clearance in the target markets.

## 2. Product promise

The product behaves like a patient personal tutor rather than a generic answer box. It should:

- understand the learner's grade, subject, lesson, and current level;
- explain a concept step by step in Arabic, Egyptian Arabic, or English;
- ask guided questions instead of giving away every answer;
- generate validated practice and feedback;
- remember progress through explicit learning records;
- provide a useful progress view for an authorized guardian; and
- continue safely in text when voice, network, or a model provider is unavailable.

The product never invents grades, mastery, curriculum coverage, or progress numbers. Every displayed metric must come from a validated learning record.

## 3. Product boundaries

### In the first release

- Egyptian secondary students.
- Mathematics, Physics, and English.
- Student mobile application.
- Text tutoring and curriculum-scoped explanations.
- Short practice and assessment flow.
- Skill-level progress records.
- Guardian read-only progress view.
- Secure authentication, consent, rate limits, audit events, and usage controls.

### After the first release

- Voice input and spoken responses.
- Richer offline synchronization.
- Content authoring and review operations.
- Additional subjects and curricula.
- Optional avatar presentation layer.
- School and learning-center workspaces.
- Enterprise learning products built on the same NEXORA Core.

The avatar is a presentation layer. It must never become a dependency for the core learning loop.

## 4. Experience architecture

### Student mobile

1. Create an account and complete age, grade, language, and subject setup.
2. Complete a short diagnostic when the required content is available.
3. Land on a daily home view with continue, ask, and practice actions.
4. Start a subject session with a lesson or skill context.
5. Ask a question and receive a grounded explanation.
6. Practice the concept through a validated question.
7. See the next recommended action and the saved progress state.

The mobile app uses a small navigation model, large touch targets, Arabic RTL support, low-bandwidth states, and safe retry behavior.

### Guardian web companion

Guardians see only explicitly linked children and consented progress summaries. The default view includes:

- activity and completed learning units;
- strengths and skills needing attention;
- assessment outcomes;
- plan adherence; and
- clear data-backed alerts.

Raw private tutoring conversations are not exposed by default.

### Content operations

Content editors manage versioned curriculum, lessons, skills, examples, questions, answer keys, and publication state. A draft cannot become learner-visible without a review and publish action.

## 5. Technical architecture

The repository remains a modular product workspace:

```text
Ahmed-AI-Agent/
├── core/                         shared intelligence primitives
├── nexora_backend/               platform and product APIs
├── apps/tutor-mobile/            student mobile application
├── apps/tutor-web/               guardian and operations web companion
└── packages/contracts/           versioned shared contracts
```

Tutor code remains under `nexora_backend/app/products/tutor/`. The shared AI layer handles routing, provider abstraction, safety, usage, and audit. Tutor services own learner, curriculum, assessment, and progress rules.

The existing `/health`, `/auth/*`, and `/ai/execute` contracts remain compatible. Tutor APIs are versioned under `/api/v1/tutor`; guardian APIs use an explicit guardian namespace.

## 6. Domain records

The Tutor domain grows in controlled slices:

- `LearnerProfile`: grade, locale, subjects, and preferences.
- `CurriculumVersion`, `Lesson`, and `Skill`: approved learning content.
- `LearningSession` and `LearningMessage`: tutoring interaction records.
- `AssessmentAttempt`: validated answers and scores.
- `SkillMastery`: derived learner progress by skill.
- `GuardianLink` and `Consent`: relationship and minor-access policy.

The language model may produce explanations. It cannot write grades, mastery, or curriculum records directly. Deterministic services validate those writes.

## 7. Authorization and child safety

The initial product roles are:

| Role | Scope |
| --- | --- |
| Student | Own profile, sessions, assessments, and progress |
| Guardian | Explicitly linked children and approved progress summaries |
| Content Editor | Curriculum drafts and published content; no learner PII |
| Tutor Admin | Authorized cohorts and aggregate analytics |
| Platform Admin | Identity, workspaces, billing, configuration, and audit |

Every request derives identity from the access token. Relationship access is checked server-side. Consent, audit events, rate limits, provider timeouts, and retention rules are part of the product contract.

The tutor stays within approved curriculum context in the first release. Unrestricted browsing and unsupervised actions for minors are outside the launch scope.

## 8. Monetization model

The commercial model is staged:

1. Free entry with a diagnostic, limited daily usage, and selected lessons.
2. Student Plus with full tutoring, practice, and progress features.
3. Family with multiple learners and guardian reporting.
4. School and center plans after the learner loop is validated.

Pricing is an experiment to be measured during beta. The product will not hard-code a price decision into the architecture.

## 9. Delivery plan

The plan assumes a small focused team containing backend/AI, mobile/web, design/content, and QA capacity.

| Slice | Outcome | Duration |
| --- | --- | ---: |
| 1 | Product identity, content contract, privacy and consent decisions | 1 week |
| 2 | Curriculum, lesson, skill, and assessment records | 2 weeks |
| 3 | End-to-end learner loop with grounded provider integration | 2 weeks |
| 4 | Practice, validation, mastery, and progress | 2 weeks |
| 5 | Voice abstraction, low-bandwidth retry, and safe fallback | 2 weeks |
| 6 | Guardian linking and read-only progress portal | 2 weeks |
| 7 | Content operations, usage limits, and subscription flow | 2 weeks |
| 8 | Security, performance, observability, beta, and release hardening | 2 weeks |

From the current foundation, the target is a closed beta in 8–10 weeks and a commercial V1 in 14–16 weeks. A solo implementation should be planned at roughly 20–24 weeks. The full NEXORA education and enterprise ecosystem is a 9–12 month expansion and is not a prerequisite for the first Tutor launch.

## 10. Launch gates

The public V1 can launch after all of the following are true:

- curriculum content is reviewed and versioned;
- a student can authenticate, ask, practice, and see saved progress end to end;
- guardian access requires an explicit link and consent;
- model responses are grounded or clearly report missing context;
- offline, timeout, rate-limit, and duplicate-submit paths are tested;
- Android and iOS release candidates pass functional and accessibility checks;
- billing, privacy, terms, retention, and support flows are ready;
- metrics come from real events and contain no placeholder values; and
- beta feedback is resolved through a documented release checklist.

## 11. Immediate implementation order

The next engineering slice should implement the curriculum and learner records, then connect them to a real provider abstraction and validated practice flow. Voice, guardian reporting, subscriptions, and the avatar follow the verified text learning loop.

No new product-wide refactor is required. Existing identity, permission, AI gateway, agent fabric, migration, and contract foundations remain the base for the next slices.
