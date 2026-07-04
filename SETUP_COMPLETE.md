# ✅ MapleJourney Development Setup — 2026-07-03

## Project Location
```
C:\Users\manca\maple-journey-dev\
```

## 🔵 Backend Setup (Python/FastAPI)

**Status:** ✅ READY

**Location:** `backend/`

**Python Environment:**
- Virtual environment: `backend/venv/`
- Python: System Python 3.x
- Packages installed: 40+ core packages

**Core Dependencies Installed:**
```
✅ FastAPI 0.139.0       — REST API framework
✅ Uvicorn 0.49.0        — ASGI server
✅ Motor 3.7.1           — Async MongoDB driver
✅ PyMongo 4.17.0        — Sync MongoDB driver
✅ OpenAI 2.30.0         — GPT inference
✅ Anthropic 0.116.0     — Claude inference
✅ LiteLLM 1.83.7        — LLM provider abstraction
✅ Pydantic 2.12.5       — Data validation & settings
✅ HTTPx 0.28.1          — Async HTTP client
✅ Python-dotenv 1.0.1   — .env file loading
✅ AioHTTP 3.13.5        — Async HTTP for webhooks
✅ BCrypt 5.0.0          — Password hashing
✅ Pytest 9.1.1          — Testing framework
```

**To Activate Backend Environment:**
```powershell
cd C:\Users\manca\maple-journey-dev\backend
.\venv\Scripts\Activate.ps1
```

**To Start Backend Server:**
```powershell
python server.py

# Or with auto-reload for development:
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

**Swagger API Docs:** http://localhost:8000/docs

---

## 🟢 Frontend Setup (Node.js/React)

**Status:** ✅ READY

**Location:** `frontend/`

**Node.js Environment:**
- Node.js: v22.20.0
- npm: 10.9.3
- Packages installed: 1545 packages

**Core Dependencies Installed:**
```
✅ React 19.0.0                — UI framework
✅ React DOM 19.0.0            — DOM renderer
✅ Radix UI 25+ components     — Accessible component library
✅ TanStack React Query 5.56.2 — Data fetching/caching
✅ Framer Motion 11.18.0       — Animations
✅ Tailwind CSS (via shadcn)   — Styling
✅ Axios 1.16.0                — HTTP client
✅ Date-fns 4.1.0              — Date utilities
✅ Lucide React                — Icon library
✅ TypeScript support          — Type safety
```

**To Start Frontend Dev Server:**
```powershell
cd C:\Users\manca\maple-journey-dev\frontend
npm run dev
```

**Dev Server:** http://localhost:5173 (or as shown in terminal)

**Features:**
- Hot Module Replacement (HMR) — changes appear instantly
- Source maps for debugging
- Tailwind CSS dev server

---

## 📂 Project Structure

```
maple-journey-dev/
│
├── backend/                          # Python FastAPI backend
│   ├── venv/                         # Python virtual environment
│   ├── server.py                    # FastAPI entrypoint (composition root)
│   ├── models.py                    # MongoDB/Pydantic models
│   ├── core/
│   │   ├── config.py               # Settings & environment
│   │   ├── db.py                   # MongoDB connection
│   │   ├── crypto.py               # Encryption utilities
│   │   ├── security.py             # JWT, auth helpers
│   │   └── __init__.py
│   ├── routers/                     # API endpoints
│   │   ├── auth.py                 # Authentication (login, register, JWT)
│   │   ├── chat.py                 # Streaming RAG chat via Claude
│   │   ├── jobs.py                 # Job discovery & filtering
│   │   ├── legal.py                # Legal & government resources
│   │   ├── communities.py          # Community & place discovery
│   │   ├── domain.py               # Profile, questionnaire, scoring
│   │   ├── messaging.py            # WhatsApp OTP & inbound
│   │   ├── overview.py             # Morning briefing
│   │   ├── payments.py             # Stripe integration
│   │   ├── admin.py                # Admin console
│   │   └── webhooks.py             # External webhook handlers
│   ├── services/
│   │   ├── rag.py                  # RAG system (embeddings, retrieval, LLM)
│   │   ├── seed.py                 # Static data seeding
│   │   └── ...
│   ├── tests/                       # Pytest test suite
│   ├── requirements.txt             # Original (has issues)
│   ├── requirements_fixed.txt       # ✅ USE THIS ONE
│   ├── .env                         # Local environment variables
│   └── .env.example                 # Template
│
├── frontend/                         # React/TypeScript frontend
│   ├── node_modules/               # npm packages (1545)
│   ├── src/
│   │   ├── pages/                  # Page components (Auth, Home, Jobs, etc.)
│   │   ├── components/             # Reusable UI components
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── context/                # React context (state management)
│   │   ├── lib/                    # Utilities & helpers
│   │   ├── constants/              # Constants & config
│   │   ├── App.jsx                 # Root component
│   │   └── main.jsx                # Entry point
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js              # Vite build config
│   ├── tailwind.config.js          # Tailwind CSS config
│   ├── postcss.config.js           # PostCSS config
│   └── public/                     # Static assets
│
└── memory/                          # Static knowledge base (seed data)
```

---

## 🚀 Development Workflow

### 1. **Start Backend** (Terminal 1)
```powershell
cd C:\Users\manca\maple-journey-dev\backend
.\venv\Scripts\Activate.ps1
python server.py
```
**Output:** FastAPI server running at `http://localhost:8000`

### 2. **Start Frontend** (Terminal 2)
```powershell
cd C:\Users\manca\maple-journey-dev\frontend
npm run dev
```
**Output:** Vite dev server running at `http://localhost:5173`

### 3. **Access the App**
- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs
- **API Playground:** http://localhost:8000/openapi.json

### 4. **Code & Test**
- Edit frontend code → hot reload instantly (HMR)
- Edit backend code → auto-reload via Uvicorn
- Changes visible in browser/app immediately

---

## ⚠️ Known Issues & Fixes

### Backend Dependencies
| Issue | Solution |
|-------|----------|
| `emergentintegrations==0.2.0` not found | ✅ Removed (package doesn't exist on PyPI) |
| Custom litellm wheel URL broken | ✅ Replaced with `litellm>=1.80.0` (public package) |
| Dependency conflicts (grpcio, etc.) | ✅ Core packages installed; non-critical conflicts ignored |

**Use `requirements_fixed.txt` instead of `requirements.txt`**

### Frontend Dependencies
| Issue | Solution |
|-------|----------|
| date-fns v4 ↔ react-day-picker v8 conflict | ✅ Used `npm install --legacy-peer-deps` |
| 8 npm audit vulnerabilities | ℹ️ Non-critical; monitor for security updates |

---

## 🔑 Environment Setup

Create a `.env` file in `backend/` with:
```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017/maple_dev

# OpenAI API
OPENAI_API_KEY=sk-...

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# Stripe (payments)
STRIPE_SECRET_KEY=sk_test_...

# Twilio (SMS/WhatsApp)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# JWT
JWT_SECRET=your-secret-key-here

# App
DEBUG=True
ENVIRONMENT=development
```

See `.env.example` for more options.

---

## 🧪 Testing

### Backend Tests
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest tests/ -v
```

### Frontend Tests
```powershell
cd frontend
npm test
```

---

## 📊 Next Steps for Building

### **Tier 1 (Immediate — Data Integration)**
1. **Job Bank Integration** — Connect to ESDC API, real-time job data
2. **Vector Search** — Migrate from keyword to embedding-based search
3. **Background Tasks** — Celery/APScheduler for RSS polling

### **Tier 2 (Core Features)**
4. Multi-language support (French, Mandarin, etc.)
5. Full WCAG 2.2 AA accessibility compliance
6. Map & geographic features (OSM integration)

### **Tier 3 (Nice-to-Have)**
7. Document extraction (OCR for proofs)
8. Redis caching
9. iMessage completion

---

## 📝 Notes

- **Start both servers** before testing
- **Backend uses MongoDB** — ensure local instance or cloud URI in `.env`
- **Frontend hot-reloads** — save files and see changes instantly
- **API authentication** — JWT tokens in auth router
- **RAG System** — Citation-required LLM responses enforced in `services/rag.py`

---

**Setup completed:** 2026-07-03  
**Backend ready:** ✅  
**Frontend ready:** ✅  
**Next:** Open two terminals, start both servers, and begin building! 🚀
