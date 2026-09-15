# Ahmed AI Architecture v1.0

## Overview

Ahmed AI is a personal AI engineering assistant built by Ahmed Abdelkhalek.

The goal is to create a local intelligent agent that understands Ahmed's work, projects, preferences, and technical environment.

---

# System Architecture

## Core Layers

Ahmed AI consists of the following layers:

## 1. Identity Layer

Location:

identity/

Responsibilities:

- Define Ahmed AI identity.
- Separate Ahmed (user) from Ahmed AI (assistant).
- Maintain communication style and behavior rules.

Files:

- core_identity.md
- personality.md


---

## 2. Intent Layer

Location:

core/

Responsibilities:

- Handle deterministic requests.
- Answer identity questions directly.
- Prevent unnecessary LLM calls.

Examples:

- Who are you?
- Who is Ahmed?


---

## 3. Routing Layer

Location:

agents/

Responsibilities:

Classify user requests and select the correct specialist.

Current specialists:

- General
- Coding
- Research
- Creative


---

## 4. AI Models Layer

Current models:

General Assistant:

qwen2.5:3b

Used for:

- General conversation
- Fast responses


Coding Specialist:

qwen2.5-coder:7b

Used for:

- Programming
- Debugging
- Software architecture


---

## 5. Knowledge Layer

Location:

knowledge/

Responsibilities:

Store information about:

- Ahmed profile
- Projects
- Technical decisions


---

## 6. Tools Layer

Location:

tools/

Current tools:

- File reader
- Knowledge loader


Future tools:

- Web search
- Code analysis
- Document analysis
- Database access


---

## 7. Memory Layer

Location:

memory/

Purpose:

Long term memory system.

Planned:

- Personal memory
- Project memory
- Decision memory
- Preferences


---

# Future Architecture

Planned upgrades:

- RAG system
- Vector database
- Chat interface
- API server
- Tool calling
- Autonomous workflows


---

# Philosophy

Ahmed AI should work as a senior technical partner.

It should:

- Understand context.
- Remember important decisions.
- Provide practical solutions.
- Help build scalable systems.
