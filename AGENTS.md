# AGENTS.md — MapleJourney v2 AI Agent Guide

**MapleJourney v2** is a full-stack legal+career AI platform for Canadian newcomers. This guide helps AI agents quickly understand the architecture, conventions, and how to implement features effectively.

---

## 🚀 Quick Start

### Backend (FastAPI + MongoDB + RAG)
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
# Swagger docs: http://127.0.0.1:8000/docs
```

### Frontend (React 19 + Tailwind + Radix UI)
```bash
cd frontend
yarn start
# Runs on http://localhost:3000
```

### Testing
```powershell
cd backend
pytest                    # Run all tests (2 workers parallel)
pytest --pdb             # With debugger
pytest tests/test_profile_hub.py -v  # Specific file
```

---

## 📐 Architecture

```
MapleJourney/
├── backend/
│   ├── server.py              ← FastAPI app entry (thin composition root)
│   ├── routers/               ← 14 API endpoints (auth, jobs, chat, community, etc.)
│   ├── services/              ← Business logic (RAG, jobs, profiles, credits)
│   ├── models.py              ← Pydantic request/response schemas
│   ├── core/
│   │   ├── db.py              ← Motor MongoDB client (async)
│   │   ├── security.py        ← Password hashing (bcrypt), JWT validation
│   │   ├── crypto.py          ← Encryption for sensitive fields
│   │   └── config.py          ← Env vars, LLM config
│   └── tests/                 ← Pytest suite
├── frontend/
│   ├── src/pages/
│   │   ├── auth/              ← Login, signup, password reset
│   │   ├── app/               ← Main 5 pages (chat, jobs, profile, milestones, settings)
│   │   ├── admin/             ← Admin panel
│   │   └── marketing/         ← Public landing pages
│   ├── src/components/        ← Radix UI + Tailwind
│   └── src/services/          ← API client (axios + TanStack Query)
└── core/                      ← Shared utilities
```

---

## 🔐 Authentication & Authorization

**Pattern**: JWT (HS256) → `Depends(get_current_user)` on protected routes

```python
# Protected route example:
@router.get("/api/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["sub"], "role": current_user["role"]}
```

- **Roles**: `user`, `admin` (set at registration; stored in user doc)
- **Token expiry**: 24 hours (in `create_access_token`)
- **Header format**: `Authorization: Bearer <token>`
- **Sensitive fields**: Encrypted/decrypted via `core/crypto.py` (IRCC ID, visa numbers, etc.)

---

## 🧠 AI & Grounded RAG System

**Core Principle — "Grounded Integrity"**: Every response must cite an approved source or refuse to answer.

### RAG Pipeline
1. User question → embedded via OpenAI Ada-3
2. pgvector search against IRCC policy docs (in Supabase)
3. Top-K results + live web data → system prompt
4. LLM generates response → extract + validate citations
5. Append **IRPA s.91 legal disclosure** (not legal advice; representatives required for fees)

### Implementation ([services/rag_v2.py](backend/services/rag_v2.py))
```python
# Search embeddings
results = await vector_search(query, top_k=5)  # Returns docs with source URLs

# Extract & validate citations
citations = extract_citation_urls(llm_response)
for url in citations:
    assert url in APPROVED_DOMAINS  # canada.ca, laws-lois.justice.gc.ca, etc.
```

**Approved domains**: `canada.ca`, `laws-lois.justice.gc.ca`, `irb.gc.ca`, `college-ic.ca`, provincial legal aid sites.

**Citation format** (enforced): `[Source: {URL}, published {date}]`

### Key Services
- **[services/rag.py](backend/services/rag.py)** — v1 (functional, documents grounding principles)
- **[services/rag_v2.py](backend/services/rag_v2.py)** — v2 (vector search + pgvector)
- **[services/credits.py](backend/services/credits.py)** — Wallet/credit system (Free: 20 chats/day, Settler: 50, Citizen: unlimited)

---

## 📡 API Routes (14 Routers under `/api`)

| Router | Key Endpoints |
|--------|--------------|
| **[auth.py](backend/routers/auth.py)** | POST /register, /login, /password-reset, PUT /profile |
| **[jobs.py](backend/routers/jobs.py)** | GET /search?location=&days_posted=&limit= — 7-source dedup |
| **[chat.py](backend/routers/chat.py)** | POST /message (RAG-powered, grounded responses) |
| **[companion.py](backend/routers/companion.py)** | WhatsApp/iMessage async sessions |
| **[community.py](backend/routers/community.py)** | GET /resources?province=ON&city= — settlement resources |
| **[domain.py](backend/routers/domain.py)** | User milestones, documents, settlement timeline |
| **[overview.py](backend/routers/overview.py)** | Dashboard (weather, IRCC RSS, holidays, next steps) |
| **[payments.py](backend/routers/payments.py)** | Stripe checkout, subscription CRUD |
| **[admin.py](backend/routers/admin.py)** | Feature toggles, user management, content |
| **[wings.py](backend/routers/wings.py)** | Maple assistant settings (tone, goals, autonomy) |
| **[messaging.py](backend/routers/messaging.py)** | Phone OTP (Twilio Verify) |
| **[webhooks.py](backend/routers/webhooks.py)** | Stripe & Twilio callbacks |
| **[companion_ops.py](backend/routers/companion_ops.py)** | Async background tasks |

**Pattern**: Router → service layer → `core/db.py` (Motor async access)

---

## 💾 Database

### MongoDB (Motor async driver)
**Required env vars**: `MONGO_URL`, `DB_NAME`, `JWT_SECRET`

**Collections**:
- `users` — accounts, visa type, PR score, companion settings
- `chat_sessions` — conversation history
- `jobs` — cached listings (TTL auto-cleanup)
- `resources` — community orgs, legal aid (by province)
- `milestones` — settlement timeline
- `documents` — uploaded files, tracking
- `wallets` — credit balances (Free/Settler/Citizen tiers)
- `announcements` — admin broadcasts
- `companions` — WhatsApp/iMessage routing

**Access pattern**: `from core.db import db` → `await db.collection_name.find_one({"_id": id})`

### pgvector (Supabase for embeddings)
- Pre-seeded with IRCC policy doc embeddings
- Used for RAG vector search
- Source URL indexing for citation filtering

---

## 🏗️ Key Conventions

| Convention | Pattern | Example |
|-----------|---------|---------|
| **Routing** | All under `/api/*`; routers via APIRouter prefix | `POST /api/auth/login` |
| **Error Handling** | `HTTPException(status_code, detail)` | `raise HTTPException(400, "Invalid email")` |
| **Validation** | Pydantic models in [models.py](backend/models.py) | `class LoginRequest(BaseModel): email, password` |
| **Response Shape** | `{"key": value}` or `{"error": msg}` | `{"token": "...", "user_id": "..."}` |
| **Async DB** | `await db.collection.method(...)` (Motor) | `user = await db.users.find_one(...)` |
| **Encryption** | `encrypt(value)` / `decrypt(value)` from crypto.py | `ircc_id = decrypt(user["ircc_id"])` |
| **Service Layer** | Business logic in `services/`; routers delegate | See job search, credit deduction, RAG |
| **JWT in Headers** | `Authorization: Bearer <token>` | Extracted by `get_current_user` dependency |

---

## 🔧 Service Layer Essentials

**Key services to understand**:

- **[services/rag_v2.py](backend/services/rag_v2.py)** — Vector search + citation extraction
- **[services/jobs.py](backend/services/jobs.py)** — Live job search across 7 sources
- **[services/credits.py](backend/services/credits.py)** — Check balance, deduct credits
- **[services/profile.py](backend/services/profile.py)** — Visa type, PR score, expiry dates
- **[services/companion_memory.py](backend/services/companion_memory.py)** — WhatsApp/iMessage state
- **[services/email_service.py](backend/services/email_service.py)** — Email templates
- **[services/users.py](backend/services/users.py)** — User retrieval helpers

---

## 📋 Common Development Tasks

### Add a New API Route
1. Create endpoint in `routers/new_feature.py`
2. Import and mount in [server.py](backend/server.py) via `app.include_router(...)`
3. Add request/response models to [models.py](backend/models.py)
4. Implement business logic in `services/new_feature.py`
5. Add tests in `tests/test_new_feature.py`
6. Run `pytest tests/test_new_feature.py -v`

### Modify RAG Behavior
- Edit [services/rag_v2.py](backend/services/rag_v2.py) for search/citation logic
- Update IRPA disclosure in `LEGAL_DISCLAIMER` string
- Test with: `pytest tests/test_rag.py -v`

### Add Encryption for New Field
1. Use `encrypt(value)` when storing in DB
2. Use `decrypt(value)` when retrieving
3. Both from `core/crypto.py` (uses `ENCRYPTION_KEY` env var)

### Frontend Integration
- API calls via `axios` + **TanStack React Query** (cached, refetch on mount)
- Components from **Radix UI** (headless, styled with Tailwind)
- State management: React hooks + Query, no Redux
- Layout: Pages in `src/pages/`; components in `src/components/`

---

## 🧪 Testing

### Backend Tests
- Framework: **Pytest** with xdist (2 workers, loadscope distribution)
- Config: [pytest.ini](backend/pytest.ini)
- Files: All in `tests/` directory
- Key fixtures: Database mocking, JWT token generation (see test files)

### Run Tests
```powershell
pytest                              # All tests, parallel
pytest tests/test_auth.py -v        # Single file, verbose
pytest tests/test_auth.py::test_login -v  # Single test
pytest --pdb                        # Drop into debugger on failure
pytest -x                           # Stop on first failure
```

---

## 📖 Documentation

- **[QUICK_NAVIGATION.md](QUICK_NAVIGATION.md)** — File & command reference
- **[PHASE_1_COMPLETE.md](PHASE_1_COMPLETE.md)** — Full Phase 1 recap
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** — Roadmap (Phase 1–4)
- **Inline docstrings** — All key functions documented (RAG, security, DB patterns)

---

## ⚙️ Environment Setup

**Required `.env` vars** (backend):
```
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=maple_journey
JWT_SECRET=your-256-bit-secret
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=SecurePass123!
ENCRYPTION_KEY=32-byte-base64-key
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJ...
```

**Frontend**: Proxy backend at `http://127.0.0.1:8000` (dev); production via Kubernetes ingress.

---

## 💡 Tips for Agents

1. **Always run `pytest` before committing** — catches regressions early
2. **Check [core/config.py](core/config.py) for LLM config** — controls which model is used, max tokens, temperature
3. **RAG citations are mandatory** — never ship responses without `[Source: ...]` format or a valid refusal
4. **Use `Depends(get_current_user)` on any protected route** — no manual JWT parsing
5. **Encryption is automatic for sensitive fields** — always use `crypto.py` helpers
6. **Service layer is stateless** — no session memory between requests (use DB or companion memory service)
7. **Frontend: TanStack Query caches API results** — refetch strategy is configured per endpoint
8. **No TODOs in code** — all features are implemented per [PHASE_1_COMPLETE.md](PHASE_1_COMPLETE.md)

---

## 🎯 When You're Stuck

1. Check [QUICK_NAVIGATION.md](QUICK_NAVIGATION.md) for file location
2. Review the router or service file — most logic is self-documented
3. Run `pytest -v` to validate your changes
4. Check Swagger docs at `http://127.0.0.1:8000/docs` for API schema
5. Review existing tests for patterns (`tests/test_*.py`)

---

**Last Updated**: Phase 1 Complete (Vector RAG v2, Grounded Integrity, Credit System)
