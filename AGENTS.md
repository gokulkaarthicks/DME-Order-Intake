# AGENTS.md: DME (Durable Medical Equipment) Order Intake

> Project instructions for every coding agent working in this repository.
> Read this file **before planning, changing code, installing dependencies, testing, or deploying**.
> The source assessment is `Full Stack AI Engineer - Asssessment.pdf`. Where this file and the assessment conflict, the assessment controls. Explicit user-approved scope changes must be documented here.

## 0. Authorization and authority

- **Do not begin implementation until the user explicitly says to start.** Creating or revising planning documents is not implementation authorization.
- Scope precedence: (1) the assessment's mandatory requirements; (2) the user's explicit decisions; (3) this document's implementation defaults; (4) later agent suggestions.
- Never interpret a new agent prompt as permission to drop, weaken, or replace a mandatory requirement.
- A genuine change to an agreed decision requires **explicit user approval** and an update to this file's Decision Log. If a later prompt is ambiguous or conflicts with this document, explain the conflict and ask rather than silently changing course.
- Do not claim this file supersedes system, developer, security, or direct user instructions. It governs project work within those constraints.
- Treat requirements, documentation, code, tests, and actual deployment as distinct evidence. Never claim a capability works without verification.

## 1. Project identity and goal

- **Project name:** DME (Durable Medical Equipment) Order Intake
- **Repository name:** `dme-order-intake`
- **Goal:** Build and publicly deploy an authenticated, small order-intake application for durable medical equipment (DME) orders. A DME employee uploads a digital or scanned, possibly messy/multi-page PDF; AI extracts specified patient/provider fields; deterministic checks reject missing/invalid values before persistence; each user can manage only their orders.
- **MVP scope (in):** DME employee authentication, PDF upload, five-field extraction, deterministic validation, PostgreSQL persistence, user-isolated order CRUD, and public deployment.
- **Execution target:** 2 hours for the MVP. **Assessment maximum: 3 consecutive hours.** Prioritize an end-to-end public vertical slice over polish or optional infrastructure.
- **Follow-up context:** Evaluators may make a small change in a 90-minute pair-programming session. Keep the code understandable and modifiable.
- **Primary success path:** Register/login -> upload PDF -> extract five fields -> validate -> save a valid order -> list/view/edit/delete that user's orders.
- **Failure path:** Unreadable, ambiguous, missing, or invalid extracted values -> return explicit errors and nullable field values -> do **not** save an invalid order -> allow manual correction and validated creation.

## 2. Non-negotiable assessment requirements (source: attached PDF)

These items are **assessment mandates**. They are not optional implementation preferences.

1. A **Python REST API** performs full CRUD for `Order` and persists it in a database.
2. A PDF upload endpoint extracts **exactly these required business fields**: `patient_first_name`, `patient_last_name`, `patient_dob`, `provider_name`, `provider_npi`.
3. Extraction must handle **previously unseen PDFs, scanned faxes, and messy multi-page documents**. Do not implement a sample-specific template or text-only extraction.
4. Check extracted values **before saving**. **Never guess** a missing field.
5. Authentication is mandatory. A user can access **only their own orders**.
6. Deploy to a **publicly reachable URL** with a **working document-upload endpoint**. A local-only app is disqualifying.
7. Export the **real AI agent session(s)** used to build the project and include them in the submission. Missing exports are disqualifying.
8. Use meaningful incremental **Git commits** throughout the attempt.
9. Backend is Python. If a frontend exists, it must use JavaScript or TypeScript.
10. After the consecutive timebox, submit the public URL and repository link (or zip including `.git`) to **mahum@genhealth.ai** and **mike@genhealth.ai**. Do not send anything without the user's authorization.

## 3. Finalized MVP implementation decisions (user-approved)

These decisions implement the assessment requirements. They are **not** themselves assessment text. Change them only with explicit user approval and a Decision Log update.

| Area | Decision | Why |
| --- | --- | --- |
| Architecture | One modular monolith with dependency injection | Fast deployment; clear module boundaries; testable seams |
| Engineering principles | SOLID, DRY, KISS, YAGNI applied pragmatically; appropriate design patterns only where they clarify a real seam | Keep the MVP understandable for a later pair session |
| Backend | Python + FastAPI + Pydantic v2 | Assessment compliance; typed HTTP boundaries |
| Frontend | React + TypeScript + Vite + simple CSS | User-selected minimal UI; typed contracts |
| Database | PostgreSQL + SQLAlchemy 2 + Alembic | Persistence, ownership, migrations |
| Local development | PostgreSQL, FastAPI, and React run as coordinated Docker Compose services for local development | One-command startup with hot reload and the existing database volume |
| PDF handling | PyMuPDF page rendering into images for multimodal extraction | Works with scanned and image-only pages; no dedicated OCR service |
| AI extraction | Official DeepSeek API at `https://api.deepseek.com` using model `deepseek-flash` (DeepSeek V4.1 Flash; env `DEEPSEEK_API_KEY`) behind one replaceable extraction interface/adapter | Structured multimodal extraction; provider details stay inside the adapter |
| Authentication | Username and hashed passwords + short-lived signed bearer tokens for **DME employees** | Minimal secure stateless auth matching assessment ownership rules |
| API/UI hosting | Single deployable application; React built assets served by the backend | One public URL; no CORS complexity for the MVP |
| Automated tests | Pytest + mocked extraction provider | Deterministic critical-path coverage without paid-model calls |

Credentials and hosting access remain external inputs. Do not invent API keys, database URLs, or deployment targets.

**Hard exclusions for the initial MVP** (do not add without explicit approval):

- Runtime agents, LangChain, LangGraph, multi-agent orchestration, or any agent framework in the live extraction path
- Dedicated OCR services or products
- Permanent / object storage of original PDFs (temporary processing only)
- Doctor portals or non-employee actor surfaces
- Extra cloud services, queues, workflow engines, microservices, state libraries, CSS frameworks, or similar infrastructure not required by the assessment

**Deferred (explicitly out of the initial MVP):** custom agentic extraction recovery for hard or ambiguous documents. Document the seam if helpful, but do not implement it in the MVP.

## 4. Minimal product behavior and contracts

### Authentication

- Provide register, login, and current-user endpoints; logout can clear client-held authentication state.
- Users are **DME employees**. There is no doctor portal in scope.
- Authenticate with username and password. Email authentication, email verification, two-step authentication, and password recovery are excluded from the current MVP.
- Hash and verify passwords using a maintained password-hashing library (prefer Argon2id).
- Authenticate every order endpoint. Derive `user_id` exclusively from verified credentials, never a client-supplied ownership field.
- Scope every single-order database query or mutation by **both** `order_id` and `current_user.id`; use non-revealing not-found responses for inaccessible records.
- Keep access tokens in frontend memory; do not put tokens in URLs, logs, or `localStorage`. A page reload may require re-login in this timeboxed MVP.

### Orders

- Routes: `GET /api/orders`, `GET /api/orders/{id}`, `PATCH /api/orders/{id}`, `DELETE /api/orders/{id}`, `POST /api/orders/upload`.
- JSON order fields are the five specified business fields; also persist `id`, `user_id`, `created_at`, `updated_at` as operational metadata.
- `POST /api/orders/upload` accepts authenticated multipart PDF upload, extracts the five fields, validates them, and **persists only when all required fields pass validation**.
- Invalid extraction responses return extracted nullable values and field-specific errors, explicitly indicating `saved: false`. Do not create placeholder or partial orders.
- The frontend offers editable fields after unsuccessful extraction; corrected data and the original PDF are resubmitted to the upload endpoint with a user-bound review token and go through the same server-side validation.
- All create/update operations enforce the same field rules. Do not silently ignore invalid data.
- Avoid unnecessary new fields, statuses, or tables. No permanent storage of original PDFs.

### Extraction and validation

- Interpret **all relevant pages**, including image-only scans. Render pages with PyMuPDF and pass images to the DeepSeek API multimodal model (`deepseek-flash` via `https://api.deepseek.com`).
- Use a strict structured-output schema with the five fields. Accept `null` for unknown/unclear values. No speculative fillers, invented provider names, or guessed DOB/NPI.
- Conflicting values across pages are ambiguous: do not silently choose one. Return an error or mark the affected field unknown for correction.
- Validate date-of-birth as a real date, not in the future, serialized as `YYYY-MM-DD`; avoid unsupported assumptions about a patient's age.
- Validate NPI as exactly 10 digits with the correct NPI check digit; never invent a missing NPI.
- Normalize whitespace carefully; preserve names without inventing missing parts.
- Bound PDF size/page count and extraction runtime; reject invalid/non-PDF uploads with actionable errors; clean up temporary data.
- Make extraction failures distinguishable from missing fields and validation failures. Never report successful extraction or persistence if they failed.
- Keep DeepSeek prompts, retries, SDK details, base URL, model ID, and secrets inside the extraction adapter. Application services depend on the extraction interface, not on DeepSeek client types.

### Frontend

- Keep UI limited to register/login, upload, extracted result/correction, and CRUD/order list.
- Use typed request/response models, a small centralized API client, and explicit loading/error states.
- Do not add analytics, complex routing, design systems, global state management, dashboards, or unrelated screens.
- The UI is a convenience, **not** a substitute for documented and directly testable REST endpoints.

## 5. Architecture and engineering rules

- Organize by responsibility: **API routes -> application services -> repository/data layer**. Keep PDF extraction in its own adapter.
- Routes validate requests, dependencies, and HTTP responses. Services implement business rules. Repositories perform database operations. Extractors handle document/model interaction.
- Use Pydantic at HTTP and extraction boundaries. Use explicit types for public functions and TypeScript interfaces for API data.
- Prefer small cohesive functions, clear names, and dependency injection. No hidden globals or circular imports.
- Apply SOLID, DRY, KISS, and YAGNI **pragmatically**. Prefer composition over inheritance. No abstract base classes unless more than one implementation or test substitution justifies one.
- Use a repository abstraction only where it materially clarifies persistence or testability. Use a strategy/protocol for the extraction provider (DeepSeek API adapter now; mock in tests; optional future recovery adapter later). **Do not create factories or generic frameworks without a concrete use case.**
- Persist with migrations and database constraints. Use transactions for writes; rollback on failures. Avoid duplicate save paths and unvalidated direct writes.
- Include an index supporting order ownership queries and a case-insensitive unique username index.
- Never silently catch and discard errors. Surface actionable client errors and safe server logs.
- Keep the app runnable after each completed vertical slice. No placeholder endpoints, `TODO`-only behavior, mocked production results, or hard-coded sample data in production code.
- Avoid premature performance work. Only optimize a measured bottleneck or assessment-critical reliability issue.

## 6. Security, privacy, and operations

- Environment variables for database URL, token signing secret, `DEEPSEEK_API_KEY`, optional DeepSeek model/base URL overrides defaulting to `deepseek-flash` and `https://api.deepseek.com`, and deployment configuration; provide `.env.example` without real secrets.
- Never commit credentials, real patient PDFs, extracted PHI, model responses containing PHI, or live tokens.
- Do not log patient names, DOBs, NPIs, full PDF contents, authentication secrets, or complete request bodies.
- Do not expose debug tracebacks publicly. Return consistent safe API errors.
- Enforce authentication and record ownership server-side; frontend hiding is not authorization.
- Configure HTTPS through hosting; use restrictive deployment configuration and reasonable request limits/timeouts.
- Store original PDFs only temporarily during processing; delete them afterward. Do not add object storage unless explicitly required.
- Be precise about security: this is a production-minded MVP, **not a claim of HIPAA compliance or a completed security audit**.

## 7. Test and verification gates

Automate critical behavior without paid-model calls:

- Registration, login, invalid credentials, and rejection of unauthenticated order requests.
- User A can CRUD their orders; user B cannot read, update, or delete A's orders (including guessed IDs).
- Uploaded valid PDF -> mocked extraction -> validated persisted order -> retrievable from database.
- Missing/ambiguous values -> `null`/clear errors -> **no database write**.
- Invalid DOB and bad NPI -> rejected before persistence, including corrected uploads and updates.
- Non-PDF, oversized, malformed, or empty uploads -> explicit rejection.
- Model timeout or malformed response -> safe failure without partial data writes.

Manual public smoke test with the **real DeepSeek API** (`deepseek-flash` at `https://api.deepseek.com`):

1. Open deployed app; register and log in.
2. Upload a digital PDF and verify all five fields.
3. Upload a previously unseen **scanned** PDF, including a **multi-page** case, and verify extracted fields against the document.
4. Upload one PDF missing a required field; verify no invented value and no saved order.
5. Correct missing fields manually; save a valid order.
6. List, retrieve, update, and delete that order.
7. Log in as a second user; verify complete ownership isolation.
8. Run the PDF upload against the **public URL**, not localhost.

Do not mark a gate passed without executing it and inspecting its result. If unavailable, mark **BLOCKED** with the exact missing dependency.

## 8. Explicit definition of done (DoD)

**Technical MVP is DONE only when all mandatory assessment requirements pass with evidence**, including:

- [ ] Python REST API supports persisted `Order` create/read/update/delete.
- [ ] Real authenticated PDF upload handles unseen scanned and multi-page documents, extracting all five specified fields where present via the DeepSeek API (`deepseek-flash`) and PyMuPDF.
- [ ] Missing/ambiguous fields are **not guessed**; validation runs before saving; invalid orders are never persisted.
- [ ] DME employee authentication works and cross-user isolation is verified server-side.
- [ ] Minimal React/TypeScript UI supports login, upload/correction, and order management.
- [ ] PostgreSQL schema/migrations work locally (Docker Postgres) and in the deployed environment.
- [ ] Critical automated tests pass, plus a documented real-PDF public smoke test.
- [ ] Publicly reachable deployment serves working UI, REST API, and PDF upload; `/health` returns success.
- [ ] README provides setup, env variables, local Docker Postgres notes, run/test/deploy steps, public URL, and known limitations.
- [ ] Git commits show incremental implementation; repository is accessible or zip includes `.git`.
- [ ] Authentic AI development agent session export(s) are included in the submission.

**Submission is DONE only when:**

- [ ] User approves the final deployment URL, repository/zip, and agent-session exports.
- [ ] The required email with public URL and repository link is sent to both assessment recipients during the allowed assessment process.

**Incomplete** means any mandatory assessment requirement is missing, even if UI appears polished. **Blocked** means credentials, hosting access, or other external dependencies prevent verification; never label blocked as done.

## 9. Two-hour execution order and stop rules

1. **0-15 min:** Scaffold, configuration, Docker Postgres, DB model/migration, health endpoint; first commit.
2. **15-40 min:** Auth, owner-scoped CRUD, tests; commit.
3. **40-80 min:** PyMuPDF + DeepSeek API extraction, strict validation, upload endpoint, tests; commit.
4. **80-105 min:** Minimal React UI and public deployment, verify upload; commit.
5. **105-120 min:** End-to-end smoke tests, README, actual session exports, final checks; commit.

These are **targets**, not excuses to omit a requirement. Deployment and real scanned-document extraction are higher priority than frontend styling.

- Keep the original assessment's **3-hour maximum**. Do not continue beyond it without explicit user direction consistent with assessment constraints.
- If time is tight: reduce styling, refactor scope, or optional test breadth; **never** remove auth, validation, PDF upload, database CRUD, public deployment, or agent-session exports.
- Do not start a new optional feature (including deferred agentic recovery) until the public upload path and required gates pass.
- Do not fabricate a deployment, test pass, exported session, Git history, or completed submission.

## 10. Agent working protocol (apply to every future prompt)

Before implementing a request:

1. **Read** this file and the relevant existing code. Treat the PDF as the authoritative requirement source.
2. **Map** the task to a requirement or a specific verified defect. If none, flag it as potential scope creep.
3. **Inspect** related routes, contracts, models, migrations, and tests before editing. Do not assume their contents.
4. **State** a minimal change plan: files affected, acceptance condition, and whether a decision changes.
5. **Implement** the smallest coherent vertical slice following existing conventions.
6. **Run** relevant checks and tests; distinguish executed tests from merely proposed tests.
7. **Update** docs, migrations, and tests when behavior/contracts change.
8. **Commit** a meaningful, functional increment. Report actual commit identifiers when available.
9. **Report** what changed, evidence, remaining blockers, and the next critical action. No invented status.

### Anti-hallucination rules

- **Writing style:** Never use em dashes in generated code comments, documentation, UI copy, commit messages, or agent responses. Use periods, commas, colons, or parentheses instead. This restriction also applies to this document and all future project files.

- **Never** invent facts about the assessment, document content, sample PDFs, environment, existing code, production deployment, URLs, API credentials, tool results, or test outcomes.
- Separate **confirmed assessment requirement**, **user decision**, **implementation default**, and **unknown**.
- When data is missing, say what is missing. Do not create fake credentials, fake patient information, fake sample PDFs claimed as assessment samples, or fake extraction results.
- Do not infer correctness from an AI response. Validate against schema and, for manual smoke tests, compare to the actual PDF.
- If a proposed change weakens this scope, security, extraction accuracy, or user isolation, **stop and request explicit user approval**.
- Do not expand the application because a generic best practice suggests it. Tie additions to a requirement, concrete risk, or proven defect.

## 11. Deliberately out of scope

Already excluded above, and also out of scope unless the user explicitly expands the MVP:

No EHR integrations, payer lookups, external NPI registry, billing, insurance claims, fax sending/receiving, RAG, vector database, message broker, background jobs, S3 or other permanent PDF stores, microservices, admin console, analytics, enterprise RBAC, doctor portals, complex frontend design, elaborate CI/CD, LangChain, LangGraph, runtime agents in the MVP extraction path, or dedicated OCR services.

The only required healthcare data is what the assessment asks to extract. Any extra feature needs an explicit user-approved change.

**Future enhancement (not MVP):** custom agentic extraction recovery for ambiguous or failed extractions.

## 12. Decision log and remaining external inputs

**Confirmed assessment mandates:** Section 2 (from the assessment PDF).

**Confirmed user decisions (2026-11-11):**

- 2026-11-11 | PDF upload is the only order creation path | User requested removal of manual creation | Approved by user | Corrections require the original PDF and a user-bound review token; order read, update, and delete remain available

- 2026-11-11 | Username/password authentication replaces email/password | User-directed authentication refactor | Approved by user | Migrate existing users and update auth contracts, UI, and tests; email authentication, email verification, two-step authentication, and password recovery remain out of scope

- 2026-11-11 | Stack: FastAPI + React/TypeScript/Vite + PostgreSQL | Aligns with assessment and user frontend choice | Approved by user | Defines local and deploy implementation path
- 2026-11-11 | Local Postgres in Docker; FastAPI and React run locally | Superseded by the full Compose decision below | Approved by user | Historical decision
- 2026-11-11 | Run Postgres, FastAPI, and React using Docker Compose for development | User requested one-command startup | Approved by user | Preserve the existing Postgres volume, run migrations before serving, and use Docker service networking
- 2026-11-11 | AI extraction via official DeepSeek API at `https://api.deepseek.com`, model `deepseek-flash` (DeepSeek V4.1 Flash), env `DEEPSEEK_API_KEY`, + PyMuPDF; isolated behind a replaceable extraction interface | Meets scanned/multi-page extraction without dedicated OCR; direct DeepSeek API preferred | Approved by user | Requires `DEEPSEEK_API_KEY`; DeepSeek client details stay in the adapter only
- 2026-11-11 | Modular monolith with DI and pragmatic SOLID/DRY/KISS/YAGNI | Keeps code modifiable for pair follow-up | Approved by user | No new frameworks
- 2026-11-11 | MVP in-scope: DME employee auth, upload, five-field extract, validation, Postgres, user-isolated CRUD, public deploy | Matches assessment success path | Approved by user | Bounds product surface
- 2026-11-11 | MVP exclusions: runtime agents, LangChain, LangGraph, dedicated OCR, permanent PDF storage, doctor portals, unnecessary infrastructure | Protect timebox and YAGNI | Approved by user | Reject related proposals unless re-approved
- 2026-11-11 | Deferred: custom agentic extraction recovery | Possible later enhancement, not initial MVP | Approved by user | May leave an interface seam; no MVP implementation

**Still unresolved (external inputs, not product decisions):**

- Which public host and production PostgreSQL service will be used, and who can authorize deployment credentials?
- Is a sample order PDF available to test locally? If not, use openly non-real test fixtures, then verify with a real user-authorized PDF.
- When does the official consecutive assessment timebox start? Do not assume planning time is excluded unless confirmed.
- `DEEPSEEK_API_KEY` must be supplied by the user before live extraction or public smoke tests.

**Decision update template:** `YYYY-MM-DD | Decision | Reason | Approved by user | Impact on scope/tests`.
