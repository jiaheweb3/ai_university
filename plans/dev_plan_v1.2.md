# AetherVerse Multi-Agent Development Plan

> **Version**: v1.2
> **Date**: 2026-03-19
> **Role**: Caesar (PM / Architect / QA, no product code)
> **Goal**: Define multi-Agent isolation, contract management, and collaboration

---

## 1. Role Architecture

```
Caesar (PM / Architect / QA) -- no product code
  |-- Phase 0 contract definition (architecture design)
  |-- Code Review + quality gate
  |-- shared/ package maintenance
  |-- Integration test + joint debugging
  |-- Contract change coordination
  |-- DevOps / deployment
```

| Agent | Scope | Tech Stack | Directory |
|-------|-------|------------|-----------|
| **Agent A** | Backend (core + security + gateway + SQLAdmin) | Python FastAPI + PostgreSQL + Redis | `server/` |
| **Agent B** | AI Engine + agent orchestration + AAP | Python FastAPI + LLM SDK + RabbitMQ | `ai-engine/` |
| **Agent C** | Flutter user app | Flutter + Dart | `app/` |

### 1.1 Detailed Responsibilities

**Caesar -- PM / Architect / QA (no product code):**
- Phase 0 architecture (DB Schema / API Schema / protocol definitions)
- `shared/` package maintenance (Pydantic schemas / enums / error codes)
- `docs/contracts/` change management
- All Agent code Review + PR merge
- Integration test lead (Week 5 / Week 10)
- DevOps (Docker Compose / CI/CD / deploy scripts)
- Coordinate all Agents, ensure directory isolation, prevent conflicts

**Agent A -- Backend Full-Stack:**
- User system (register/login/DID/profile)
- Room system (CRUD/members/messages)
- Chat system (WebSocket/DM/message delivery/history)
- Credits & billing (recharge/consume/transaction model/reconciliation)
- Notification system (in-app messages)
- Security audit (3-layer pipeline/AIGC labeling/reports/sensitive words)
- Agent gateway (external Agent access/auth/sandbox/rate limiting)
- **Admin panel (SQLAdmin + custom views)**

**Agent B -- AI Engine:**
- AI model routing + agent orchestration (L1/L2)
- Memory system + persona consistency + system agents (5)
- Image generation/understanding + AI behavior control
- AAP protocol implementation + developer SDK + docs

**Agent C -- Flutter User App (no admin panel):**
- All user-facing pages + UI components
- State management + network layer + WebSocket client

> **Admin panel**: Phase 1 uses SQLAdmin (Agent A), Phase 2 uses Vue 3 + Element Plus.

---

## 2. Directory Structure & Isolation

```
ai_university/
+-- docs/
|   +-- contracts/               # Shared contracts (Phase 0 output)
|   |   +-- api-schema.yaml      #   OpenAPI 3.0
|   |   +-- db-schema.sql        #   Database DDL
|   |   +-- db-er.md             #   ER diagram (Mermaid)
|   |   +-- shared-types.dart    #   Flutter type definitions
|   |   +-- websocket-protocol.md#   WebSocket protocol
|   |   +-- ai-engine-api.yaml   #   AI Engine internal API
|   |   +-- agent-protocol.yaml  #   AAP protocol
|   |   +-- CHANGELOG.md         #   Contract changelog
+-- shared/                      # Shared Python package (Caesar maintains)
|   +-- schemas/                 #   Pydantic models
|   +-- constants/               #   Enums, error codes
|   +-- exceptions/              #   Custom exceptions
|   +-- utils/                   #   Utilities
|   +-- pyproject.toml
+-- server/                      # Agent A territory (Python FastAPI)
|   +-- app/
|   |   +-- api/                 #   REST routes
|   |   +-- ws/                  #   WebSocket handlers
|   |   +-- services/            #   Business logic
|   |   +-- models/              #   SQLAlchemy ORM
|   |   +-- core/                #   Config/security/DI
|   |   +-- gateway/             #   Agent gateway
|   +-- migrations/              #   Alembic migrations
|   +-- tests/
|   +-- pyproject.toml
+-- ai-engine/                   # Agent B territory (Python FastAPI)
|   +-- app/
|   |   +-- router/              #   Model routing
|   |   +-- orchestrator/        #   Orchestration
|   |   +-- memory/              #   Memory management
|   |   +-- persona/             #   Persona management
|   |   +-- safety/              #   AI behavior control
|   |   +-- aap/                 #   AAP protocol
|   |   +-- sdk/                 #   Developer SDK
|   +-- prompts/
|   +-- tests/
|   +-- pyproject.toml
+-- app/                         # Agent C territory (Flutter)
|   +-- lib/
|   +-- assets/
|   +-- pubspec.yaml
+-- infra/                       # Caesar (DevOps)
    +-- docker-compose.yml
    +-- k8s/
    +-- terraform/
```

### Isolation Rules

| Rule | Description |
|------|-------------|
| **Directory isolation** | Each Agent only modifies its own directory |
| **Read-only shared** | `docs/contracts/` and `shared/` are read-only, changes via Caesar only |
| **API communication** | Agents communicate through API contracts, no direct code calls |
| **Independent builds** | Each module has its own `pyproject.toml` or `pubspec.yaml` |
| **Git branches** | Each Agent works on feature branches, PR merged by Caesar |

### Git Branch Strategy

```
main                              # Protected, PR merge only
+-- develop                       # Development mainline
|   +-- feature/agent-a/xxx
|   +-- feature/agent-b/xxx
|   +-- feature/agent-c/xxx
+-- release/v1.0
```

---

## 3. Contract Change Management

```
Need to change contract
  -> Agent tells Caesar
  -> Caesar evaluates impact, notifies all Agents
  -> Caesar updates docs/contracts/ + CHANGELOG.md
  -> All Agents pull latest contracts, update their code
  -> Integration test
```

### CHANGELOG.md Format

```markdown
## [Date] - Description

### Changed
- `POST /api/v1/rooms` added `max_members` field

### Impact
- Agent A: Update room creation API
- Agent C: Update room creation form
- Agent B: No impact

### Status
- [x] Agent A adapted
- [ ] Agent C pending
```

---

## 4. Phase 0 -- Contract & Architecture (1-2 weeks)

> **Executor**: Caesar (single Agent, serial)
> **Goal**: Define all contracts before multi-Agent parallel begins

| # | Output | File | Description |
|---|--------|------|-------------|
| 1 | API Schema | `docs/contracts/api-schema.yaml` | All REST endpoints (OpenAPI 3.0) |
| 2 | DB Schema | `docs/contracts/db-schema.sql` | All table DDL |
| 3 | ER Diagram | `docs/contracts/db-er.md` | Mermaid format |
| 4 | WebSocket Protocol | `docs/contracts/websocket-protocol.md` | Message format, events, heartbeat |
| 5 | AI Engine API | `docs/contracts/ai-engine-api.yaml` | Backend-to-AI internal API |
| 6 | AAP Protocol | `docs/contracts/agent-protocol.yaml` | External Agent protocol |
| 7 | Shared Types | `shared/` + `shared-types.dart` | Pydantic schemas + Dart types |
| 8 | Changelog | `docs/contracts/CHANGELOG.md` | Contract change log |
| 9 | Scaffolding | `shared/` + `server/` + `ai-engine/` + `app/` | Module init |
| 10 | Local Dev | `infra/docker-compose.yml` | PostgreSQL + Redis + MinIO + RabbitMQ |
| 11 | CI/CD | `.github/workflows/` | lint + build + test pipeline |

### Phase 0 Schedule

```
Week 1:
+-- Day 1-2: DB Schema (all tables DDL + ER diagram)
+-- Day 3-4: API Schema (all REST endpoints OpenAPI)
+-- Day 5:   WebSocket protocol + AI Engine API + AAP protocol

Week 2:
+-- Day 1:   Shared type definitions (shared/ + Dart)
+-- Day 2:   Project scaffolding (all modules init)
+-- Day 3:   Docker Compose + CI/CD pipeline
+-- Day 4-5: Self-check + docs + finalize Agent startup instructions
```

---

## 5. Agent Startup Instructions

> Copy-paste these into each Agent's conversation window at Phase 1 start.

### 5.1 Agent A Startup

```
# Agent A -- Backend Full-Stack

## Who You Are
You are AetherVerse's backend full-stack developer, codename Agent A.

## Your Scope
- User system (register/login/DID/profile)
- Room system (CRUD/members)
- Chat system (WebSocket/DM/message delivery/history)
- Credits & billing (recharge/consume/transaction/reconciliation)
- Notification system (in-app messages)
- Security audit (3-layer pipeline/AIGC labeling/sensitive words)
- Agent gateway (external Agent access)
- Admin panel (SQLAdmin + custom audit/dashboard views)

## Work Rules
1. Only modify files under `server/`
2. `docs/contracts/` and `shared/` are READ-ONLY, tell Caesar if changes needed
3. Implement REST API per `docs/contracts/api-schema.yaml`
4. Implement WebSocket per `docs/contracts/websocket-protocol.md`
5. Create SQLAlchemy models per `docs/contracts/db-schema.sql`
6. Import Pydantic schemas from `shared/`, no duplicate type definitions
7. MANDATORY async: no sync blocking calls (see coding_conventions.md)
8. Git branch: `feature/agent-a/xxx` from develop
9. Check `docs/contracts/CHANGELOG.md` for contract changes

## Must-Read Files
- docs/contracts/api-schema.yaml
- docs/contracts/db-schema.sql
- docs/contracts/websocket-protocol.md
- docs/contracts/agent-protocol.yaml (gateway side)
- docs/Phase1_MVP_requirements.md
- context_memory/coding_conventions.md

## Schedule
- Week 3-4: User register/login + Room CRUD + WebSocket messaging
- Week 5-6: Credits + DM + notifications + DB migrations
- Week 5 end: Integration checkpoint (with Agent B/C)
- Week 7-9: 3-layer audit + AIGC labeling + Agent gateway + SQLAdmin
```

### 5.2 Agent B Startup

```
# Agent B -- AI Engine

## Who You Are
You are AetherVerse's AI engine developer, codename Agent B.

## Your Scope
- AI model routing (multi-provider/fallback/health check)
- Agent orchestration (L1 speech/L2 creation)
- Memory system (context/summary/expiry)
- Persona consistency + system agents (5 preset AIs)
- AI behavior control (impersonation/social engineering detection)
- Image generation/understanding
- AAP protocol (external Agent messaging/protocol conversion)
- Developer SDK + docs

## Work Rules
1. Only modify files under `ai-engine/`
2. `docs/contracts/` and `shared/` are READ-ONLY
3. Call backend via `docs/contracts/api-schema.yaml`
4. Receive requests via `docs/contracts/ai-engine-api.yaml`
5. Tech: Python FastAPI, import shared package directly
6. MANDATORY async: no sync blocking calls
7. Git branch: `feature/agent-b/xxx` from develop
8. Check CHANGELOG.md for contract changes

## Must-Read Files
- docs/contracts/ai-engine-api.yaml
- docs/contracts/api-schema.yaml
- docs/contracts/agent-protocol.yaml (AAP)
- docs/contracts/db-schema.sql
- docs/Phase1_MVP_requirements.md section 3
- plans/Phase1_landing_plan.md section 2.5
- context_memory/coding_conventions.md

## Schedule
- Week 3-4: LLM routing + Prompt templates + basic dialogue
- Week 5-6: Avatar creation, speech scheduling, memory system
- Week 5 end: Integration checkpoint
- Week 7-9: System AIs (5) + AI safety + image + AAP + SDK
```

### 5.3 Agent C Startup

```
# Agent C -- Flutter User App

## Who You Are
You are AetherVerse's Flutter user app developer, codename Agent C.

## Your Scope
- User app Flutter (iOS/Android)
- UI components (based on design specs)
- State management + network layer + local storage

Note: Admin panel is NOT your responsibility (Agent A handles with SQLAdmin)

## Work Rules
1. Only modify files under `app/`
2. `docs/contracts/` is READ-ONLY
3. Call backend API per `docs/contracts/api-schema.yaml`
4. Implement WebSocket per `docs/contracts/websocket-protocol.md`
5. Use shared types from `docs/contracts/shared-types.dart`
6. Week 3-4: design specs not ready, build framework layer first
7. Week 5+: design specs arrive, start UI implementation
8. Git branch: `feature/agent-c/xxx` from develop
9. Check CHANGELOG.md for contract changes

## Must-Read Files
- docs/contracts/api-schema.yaml
- docs/contracts/websocket-protocol.md
- docs/contracts/shared-types.dart
- docs/Phase1_MVP_requirements.md (modules 1-7)
- docs/prototype_mobile.html
- context_memory/coding_conventions.md

## Schedule
- Week 3-4: Routing + state management + network + WebSocket + theming
- Week 5: Integration checkpoint (login + rooms + basic messaging)
- Week 5-6: Core pages from design specs (login/register/chat/rooms)
- Week 7-9: Avatar/credits/profile/settings (100% user experience focus)
```

### 5.4 Caesar's Own Work (PM / Architect / QA)

```
Caesar (no product code):
- Phase 0: All contract definitions (architecture design)
- shared/ package maintenance (contract layer, not business code)
- docs/contracts/ change management
- Code Review + PR merge
- Integration test + joint debugging lead
- DevOps (infra/ deployment)
- Coordinate all Agents, ensure isolation, prevent conflicts
```

---

## 6. Integration Checkpoints

### 6.1 Week 5 -- Mid-Phase Verification

| Item | Agent A | Agent B | Agent C |
|------|---------|---------|---------|
| User login | Register/login API ready | -- | Login page works |
| Room list | Room CRUD API ready | -- | Room list displays |
| Basic messaging | WebSocket delivery | Basic LLM dialogue | Chat UI send/receive |
| AI speaking | Message bus connected | Trigger one AI reply | Show AI message + label |
| Credits | Credits query API | -- | Balance display |

**Method**: Caesar starts all 3 services in local Docker Compose, verify each item

### 6.2 Week 10 -- Full Integration Test

All 13 modules end-to-end.

---

## 7. Communication

### 7.1 Daily Collaboration

| Scenario | Action |
|----------|--------|
| Agent needs contract change | Tell Caesar in conversation |
| Caesar updated contract | Update CHANGELOG.md, remind Agents |
| Integration issue found | Caesar provides error logs/screenshots to relevant Agent |
| Emergency conflict | Caesar pauses all Agents, fixes, then resumes |

### 7.2 Founder (Zhiyuan) Role

| Task | Zhiyuan's Action |
|------|-----------------|
| **Create Agent conversations** | Open 3 new AI Agent windows (A, B, C) |
| **Send startup instructions** | Copy startup instructions into each Agent window |
| **Contract change notification** | Caesar tells Zhiyuan -> Zhiyuan relays to Agents |
| **Integration support** | Week 5/10 integration needs Zhiyuan to coordinate |
| **External affairs** | UI design outsourcing, App Store account, cloud servers |
| **Device testing** | Test Agent C's Flutter code on real devices |

---

## 8. Phase 0 Action Checklist

Caesar starts Phase 0 immediately:

1. [x] ~~Multi-Agent development plan~~ (this document)
2. [ ] Design DB Schema (all table DDL)
3. [ ] Draw ER diagram
4. [ ] Define REST API Schema (OpenAPI 3.0)
5. [ ] Define WebSocket protocol
6. [ ] Define AI Engine internal API
7. [ ] Define AAP external Agent protocol
8. [ ] Generate shared type definitions
9. [ ] Build project scaffolding (shared/ + server/ + ai-engine/ + app/)
10. [ ] Docker Compose local dev environment
11. [ ] CI/CD basic pipeline
12. [ ] Finalize Agent A/B/C startup instructions

**Phase 0 complete when**: All contracts ready + scaffolding builds + local env starts

After Phase 0, Zhiyuan creates Agent A, B, C conversation windows, pastes startup instructions, development begins.

---

## 9. Key Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Incomplete contracts | Agent rework | Thorough Phase 0, cover all MVP endpoints |
| Agent misunderstanding | Integration failure | Detailed startup instructions + Week 5 checkpoint |
| External Agent security | Security risk | Gateway control, Phase 1 invite-only |
| Design spec delay | Agent C blocked | Week 3-4 build framework first |
| Multi-Agent coordination overhead | Slow response | Zhiyuan relays + contracts-first reduces communication |

---

> **Next step**: Caesar begins Phase 0 Item 1 -- Database Schema design.
