# AIRSPACE

## Technical Requirements Specification — MVP

Vent and Decompress  
Web Application · Render Deployment · MVP Pitch: 4 November 2026

## 1. Document Purpose

This document defines the technical requirements for the AirSpace MVP to be demonstrated and pitched on 4 November 2026. It specifies the smallest credible working web application that demonstrates AirSpace's core value: private expression, structured decompression, and a simple before/after reset. It is not a specification for the eventual full platform.

## 2. MVP Product Definition

AirSpace is a private web application where a user can get what is in their head out, process it, and leave with greater clarity.

- Air It Out — free-form text-based expression.
- Decompress & Reframe — guided/AI-assisted reflection on the user's entry.
- Track Your Reset — simple before/after emotional check-in.

AirSpace is not a therapy platform, diagnostic tool, emergency service, or replacement for professional care.

## 3. Delivery Constraints

| Constraint   | Decision                                      |
| ------------ | --------------------------------------------- |
| Target       | Working MVP for 4 November 2026               |
| Platform     | Responsive web application                    |
| Hosting      | Render                                        |
| Architecture | Modular monolith                              |
| Backend      | Python + FastAPI                              |
| Database     | PostgreSQL                                    |
| AI           | One focused AI use case: Decompress & Reframe |
| Priority     | Complete core flow over feature breadth       |

## 4. MVP Scope

| Feature                | MVP                  | Later                              |
| ---------------------- | -------------------- | ---------------------------------- |
| Responsive web UI      | YES                  | Native mobile apps                 |
| Authentication         | YES                  | Social/advanced identity providers |
| Text Air It Out        | YES                  | Expanded media                     |
| Session history        | YES                  | Advanced search/filtering          |
| Decompress & Reframe   | YES                  | Advanced personalization           |
| Before/after check-in  | YES                  | Advanced analytics                 |
| AI assistance          | YES, limited         | Multi-model orchestration          |
| Audio                  | Only if time permits | Full audio pipeline                |
| Social/community       | NO                   | Later                              |
| Payments/subscriptions | NO                   | Later                              |
| Gamification           | NO                   | Later                              |
| Microservices          | NO                   | Only if scale requires it          |

## 5. System Architecture

For the November MVP, AirSpace should use one deployable application rather than multiple services. Internally, the code remains modular so components can be separated later if necessary.

- Browser frontend — responsive interface for landing, auth, dashboard, Air It Out, reflection, reset tracking, and history.
- FastAPI backend — API, authentication, authorization, validation, business logic, database access, and AI orchestration.
- PostgreSQL — users, sessions, check-ins, and reflections.
- AI provider — external model accessed through a small internal adapter/service.
- Render — production hosting and PostgreSQL deployment.

Core flow: Browser → FastAPI → PostgreSQL; FastAPI → AI provider when the user requests reframing.

## 6. Recommended Technology Stack

| Layer             | Technology                                   | Purpose                       |
| ----------------- | -------------------------------------------- | ----------------------------- |
| Frontend          | HTML/CSS/JavaScript or lightweight framework | Responsive browser UI         |
| Backend           | Python + FastAPI                             | Application/API layer         |
| Validation        | Pydantic                                     | Request/response validation   |
| Database          | PostgreSQL                                   | Persistent relational storage |
| ORM               | SQLModel or SQLAlchemy                       | Database access               |
| Server            | Uvicorn                                      | ASGI server                   |
| Password security | Argon2id                                     | Password hashing              |
| AI                | Provider API via adapter                     | Decompress & Reframe          |
| Deployment        | Render                                       | MVP hosting                   |
| Testing           | pytest + API/integration tests               | Regression protection         |
| Source control    | Git + GitHub                                 | Version control/deployment    |

## 7. Functional Requirements

### 7.1 Landing & Navigation

- FR-001 — The web application shall have a clear landing page explaining AirSpace.
- FR-002 — The landing page shall provide a clear route into the product.
- FR-003 — The interface shall be responsive on desktop and mobile browser sizes.

### 7.2 Authentication

- FR-010 — A user shall be able to register.
- FR-011 — A registered user shall be able to log in and log out.
- FR-012 — Protected content shall require authentication.
- FR-013 — Passwords shall be securely hashed and never stored in plaintext.

### 7.3 Air It Out

- FR-020 — An authenticated user shall be able to start an Air It Out session.
- FR-021 — The user shall be able to enter free-form text.
- FR-022 — The user shall be able to submit and save the session.
- FR-023 — Saved sessions shall have unique IDs and timestamps.
- FR-024 — The user shall be able to view their own sessions.
- FR-025 — The user shall be able to delete their own session.

### 7.4 Decompress & Reframe

- FR-030 — The user shall be able to request reflection for a selected session.
- FR-031 — The system shall send required content to the configured AI service.
- FR-032 — Generated content shall be displayed separately from the user's original writing.
- FR-033 — AI output shall never overwrite the original entry.
- FR-034 — AI failure shall not destroy the saved session.
- FR-035 — AI output shall not be presented as diagnosis or clinical determination.

### 7.5 Track Your Reset

- FR-040 — The user shall be able to record a before-session emotional state.
- FR-041 — The user shall be able to record an after-session emotional state.
- FR-042 — Check-ins shall belong to the correct session and user.
- FR-043 — The user shall be able to review their own check-ins.

### 7.6 Data Ownership

- FR-050 — Users shall only retrieve, modify, or delete resources they own.
- FR-051 — Knowing another user's resource ID shall not grant access.
- FR-052 — The MVP shall provide an appropriate account/data deletion path.

## 8. MVP Data Model

| Entity          | Core fields                                   | Purpose                  |
| --------------- | --------------------------------------------- | ------------------------ |
| User            | id, email/username, password_hash, created_at | Authentication/ownership |
| AirSpaceSession | id, user_id, content, created_at, updated_at  | Air It Out entries       |
| CheckIn         | id, session_id, stage, value, created_at      | Before/after reset       |
| Reflection      | id, session_id, content, created_at           | Saved AI reflection      |
| AudioAsset      | id, session_id, storage_key, status           | Optional future audio    |

Keep the MVP schema small. Do not create database structures for hypothetical features.

## 9. API Requirements

Use a versioned API prefix such as /api/v1.

- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/logout
- GET /api/v1/me
- POST /api/v1/sessions
- GET /api/v1/sessions
- GET /api/v1/sessions/{session_id}
- PATCH /api/v1/sessions/{session_id}
- DELETE /api/v1/sessions/{session_id}
- POST /api/v1/sessions/{session_id}/reflect
- POST /api/v1/sessions/{session_id}/check-ins
- GET /api/v1/sessions/{session_id}/check-ins
- DELETE /api/v1/account

## 10. Web Pages

| Page                 | Purpose                                 |
| -------------------- | --------------------------------------- |
| Landing              | Explain AirSpace and enter the product  |
| Register             | Create account                          |
| Login                | Authenticate                            |
| Dashboard            | Start a session and see recent activity |
| Air It Out           | Write and save thoughts                 |
| Decompress & Reframe | Process a selected entry                |
| Track Your Reset     | Before/after check-in                   |
| History              | Review previous sessions                |
| Session Detail       | Read session and reflection             |
| Settings             | Basic account/data controls             |

## 11. Render Deployment Requirements

- Deploy the FastAPI application as a Render web service.
- Use Render PostgreSQL for the production MVP database.
- Store secrets in Render environment variables, never in Git.
- Configure the production start command to run FastAPI through Uvicorn.
- Bind the application to Render's PORT environment variable.
- Run controlled database migrations during deployment.
- Use HTTPS in production.
- Expose a basic health endpoint.
- Keep development and production configuration separate.
- Verify the deployed service can connect to PostgreSQL before pitch day.

Minimum environment configuration:

- DATABASE_URL
- SECRET_KEY
- AI_PROVIDER_API_KEY
- ENVIRONMENT=production
- Required frontend/API origin configuration for CORS

## 12. Security Requirements

- HTTPS is required for the deployed application.
- Passwords must use Argon2id or an equivalent modern adaptive hash.
- Every private endpoint must enforce authorization server-side.
- Raw AirSpace entries must not be written to ordinary logs.
- Secrets must not be committed to GitHub.
- All incoming data must be validated.
- Authentication and AI endpoints should have basic rate limiting before public exposure.
- Only the content required for an AI operation should be transmitted to the AI provider.
- User data must not appear in URLs, debug pages, stack traces, or client-side secrets.
- Database credentials must remain private.

## 13. AI Requirements

AI is a focused feature of the MVP, not an entire AI platform.

- One AI use case is sufficient: Decompress & Reframe.
- The AI call shall live behind an internal service/adapter.
- The reframing prompt/instruction shall be versioned.
- The user must explicitly request the operation.
- Original user content remains untouched.
- Generated content must be labelled as AI-generated reflection.
- Provider timeout/error responses must be handled without losing saved content.
- Do not build RAG, vector databases, agents, model training, or multi-agent systems for this MVP unless a validated requirement appears.

## 14. Audio — Conditional Feature

Text is the required MVP input. Audio should not jeopardize the 4 November delivery.

- First make text Air It Out reliable.
- If time permits, add browser audio recording.
- Only then add storage/transcription.
- If audio threatens the delivery date, defer it.

## 15. Backend Project Structure

```text
app/
├── main.py
├── core/
│   ├── config.py
│   ├── security.py
│   └── logging.py
├── api/v1/
│   ├── auth.py
│   ├── users.py
│   ├── sessions.py
│   └── check_ins.py
├── models/
├── schemas/
├── services/
│   ├── auth.py
│   ├── sessions.py
│   ├── reflection.py
│   └── ai.py
├── repositories/
├── db/
│   ├── session.py
│   └── migrations/
└── tests/
```

## 16. Testing Requirements

- Registration/login tests.
- Authentication failure tests.
- Session CRUD tests.
- Cross-user authorization tests.
- Check-in tests.
- AI success/failure tests.
- Validation and error-response tests.
- Database integration tests.
- End-to-end core flow: Login → Air It Out → Save → Reframe → Track Reset → History.
- Responsive browser testing on desktop and mobile viewport sizes.

## 17. Pitch-Critical Acceptance Criteria

- AC-01 — The deployed Render URL opens successfully.
- AC-02 — A new user can register and log in.
- AC-03 — The user reaches the AirSpace dashboard after authentication.
- AC-04 — The user can write and save an Air It Out entry.
- AC-05 — The entry persists after browser refresh.
- AC-06 — The user can request Decompress & Reframe.
- AC-07 — AI output is separate from the original entry.
- AC-08 — The user can record before/after emotional states.
- AC-09 — The user can view previous sessions.
- AC-10 — The user can delete a session.
- AC-11 — Another user cannot access the first user's data.
- AC-12 — The interface works on a phone-sized browser viewport.
- AC-13 — AI/API failure does not destroy saved content.
- AC-14 — Production secrets are not exposed in the repository or frontend.

## 18. Build Order

1. Repository and project setup
2. FastAPI application/configuration
3. PostgreSQL + migrations
4. Authentication
5. Authorization
6. Air It Out database model + CRUD API
7. Responsive web UI
8. Dashboard + history
9. Decompress & Reframe AI service
10. Track Your Reset
11. Security/error handling
12. Automated tests
13. Render deployment
14. Production testing
15. Pitch/demo polish

## 19. Explicitly Out of Scope Before the Pitch

- Native Android/iOS applications
- Microservice architecture
- Social feeds and follower systems
- Subscriptions/payment processing
- Advanced mood prediction
- Complex analytics dashboards
- Large-scale gamification
- Enterprise administration
- Multi-agent AI
- RAG/vector databases unless specifically justified
- Internationalization
- Complex notification infrastructure

## 20. Engineering Principles

- Build for the November demonstration, not an imaginary million-user future.
- Keep the architecture simple but clean.
- Do not sacrifice security because this is an MVP.
- Do not add features merely because competitors have them.
- Protect the user's original expression.
- Treat privacy as an engineering requirement.
- Keep AI replaceable.
- Prioritize one complete working flow over many incomplete features.

## 21. Definition of Done

AirSpace MVP is ready for the 4 November pitch when the deployed Render application completes the core user journey end-to-end, persists data correctly, protects user ownership, handles AI failure safely, works responsively in a browser, and passes the core automated/API tests.

**Status:** Revised MVP engineering baseline — Web Application / Render / 4 November 2026
