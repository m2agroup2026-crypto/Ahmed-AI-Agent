# NEXORA AI Backend


## Overview

NEXORA AI Backend is the platform layer that connects users, organizations, and AI intelligence systems.


It provides:

- User management
- Workspaces
- Organizations
- AI agents
- Memory systems
- Knowledge management
- Subscriptions
- Usage tracking


---


## Architecture


NEXORA Backend connects:


Users

↓

Platform APIs

↓

AI Gateway

↓

Agent Orchestration

↓

Memory + Knowledge + Tools

↓

AI Response


---


## Development Phase


Current phase:

MVP Foundation


Goals:

- Build secure backend foundation.
- Connect existing AI engine.
- Enable user workspaces.
- Prepare SaaS architecture.


---


## Tutor foundation

The first product slice is Nexora Tutor for secondary learners. The Tutor API
is mounted under `/api/v1/tutor` and requires a bearer token from the shared
identity service. It currently provides:

- versioned curriculum lesson summaries;
- learner profile creation and retrieval;
- ownership-scoped learning sessions;
- curriculum-scoped message exchange with an explicit `needs_context` state.

Tutor tables are included in the Alembic migration chain. The mobile and web
shells live under `apps/tutor-mobile` and `apps/tutor-web` and consume the
shared contracts under `packages/contracts`.

The curriculum read path prefers published lessons imported from an active
official source with approved rights. Until the first approved bundle is
loaded, the three foundation lessons remain available as clearly marked
fixtures so the learner loop can be exercised without presenting them as
official material. Platform administrators can import a versioned bundle via
`POST /api/v1/tutor/curriculum/import` (protected by `dashboard.manage`).
Every lesson response and curriculum-grounded answer includes provenance when
it comes from an imported source.


---


## Main Modules


Future structure:


app/

├── identity

├── workspace

├── organization

├── agents

├── memory

├── knowledge

├── subscriptions

├── usage

└── billing


---


## Engineering Principles


NEXORA follows:


- Modular architecture.
- Security first.
- Documentation driven development.
- Mobile first product thinking.
- Scalable SaaS design.
