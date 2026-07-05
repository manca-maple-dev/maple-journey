"""MapleJourney API — FastAPI entrypoint.

Thin composition root: loads env, wires routers under /api, configures CORS,
and runs startup seeding. Domain logic lives in core/, models.py, services/, routers/.
"""
from dotenv import load_dotenv
from pathlib import Path
from pymongo.errors import PyMongoError
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import logging

from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import os
import time

from core.db import client
from services.seed import run_startup
from services.credits import ensure_indexes as ensure_credit_indexes
from services.update_pipeline import scheduler_loop
from services.notifications_briefing import schedule_morning_notifications
from services.research_agent import broadcast_research_insights
from services.proactive_triggers import initialize_scheduler
from routers import auth, wings, messaging, domain, chat, admin, payments, paystack, overview, webhooks, companion, companion_ops, jobs, community, messaging_channels, proactive_alerts, hybrid_llm, location_crisis, policy_feed, personalization, memory_layer, observability, benefits, telegram, telegram_monitor, automation, resume
from services.companion_memory import CompanionMemory
from services.telegram_monitor import TelegramMonitoringService
from routers.companion import ensure_webhook_indexes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("maplejourney")

_scheduler_task: asyncio.Task | None = None
_scheduler_stop_event: asyncio.Event | None = None
_notifications_task: asyncio.Task | None = None
_research_task: asyncio.Task | None = None


async def _init_telegram_services() -> None:
    """Initialize Telegram bot + monitoring independently of optional startup tasks."""
    telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    # Keep the web service stable: Telegram polling/monitoring are disabled here.
    # They can be run in a dedicated worker/service if needed.
    enable_polling = False
    enable_monitoring = False
    if telegram_bot_token:
        try:
            # Initialize Telegram collector
            telegram.telegram_collector.bot_token = telegram_bot_token
            app.telegram_app = await telegram.telegram_collector.initialize_app()

            await app.telegram_app.initialize()
            await app.telegram_app.start()
            if enable_polling and getattr(app.telegram_app, "updater", None):
                await app.telegram_app.updater.start_polling()
                logger.info("✅ Telegram bot initialized and polling started")
            else:
                logger.info("✅ Telegram bot initialized without polling")

            # Initialize monitoring only when explicitly enabled.
            if enable_monitoring:
                from core.db import db
                telegram_monitor_service = TelegramMonitoringService(db)
                asyncio.create_task(telegram_monitor_service.start_monitoring(interval_seconds=60))
                logger.info("✅ Telegram monitoring service started (60-second intervals)")
                app.state.telegram_monitor_service = telegram_monitor_service

            # Store for shutdown cleanup
            app.state.telegram_app = app.telegram_app

        except Exception as e:
            logger.error(f"❌ Failed to initialize Telegram bot: {e}", exc_info=True)
    else:
        logger.info("⚠️  TELEGRAM_BOT_TOKEN not configured. Telegram bot disabled.")
        logger.info("    To enable: Set TELEGRAM_BOT_TOKEN environment variable")

REQUIRED_ENV_VARS = [
    "MONGO_URL",
    "DB_NAME",
    "JWT_SECRET",
    "ADMIN_EMAIL",
    "ADMIN_PASSWORD",
]


def _validate_runtime_config() -> None:
    missing = [k for k in REQUIRED_ENV_VARS if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")


async def _validate_database() -> None:
    try:
        await client.admin.command("ping")
    except PyMongoError as e:
        raise RuntimeError(
            "Database connection failed. Ensure MongoDB is running and MONGO_URL is correct."
        ) from e

app = FastAPI(title="MapleJourney API — Newcomers in Canada Wingman")

FRONTEND_BUILD_DIR = ROOT_DIR.parent / "frontend" / "build"
FRONTEND_INDEX_FILE = FRONTEND_BUILD_DIR / "index.html"

if FRONTEND_BUILD_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_BUILD_DIR / "static"), name="static")

# All API routes live under /api for Kubernetes ingress routing.
api = APIRouter(prefix="/api")
api.include_router(auth.router)
api.include_router(wings.router)
api.include_router(messaging.router)
api.include_router(messaging_channels.router)
api.include_router(domain.router)
api.include_router(chat.router)
api.include_router(admin.router)
api.include_router(payments.router)
api.include_router(paystack.router)
api.include_router(benefits.router)
api.include_router(overview.router)
api.include_router(webhooks.router)
api.include_router(companion.router)
api.include_router(companion_ops.router)
api.include_router(jobs.router)
api.include_router(community.router)
api.include_router(proactive_alerts.router)
api.include_router(hybrid_llm.router)
api.include_router(location_crisis.router)
api.include_router(policy_feed.router)
api.include_router(personalization.router)
api.include_router(memory_layer.router)
api.include_router(observability.router)
api.include_router(telegram.router)
api.include_router(telegram_monitor.router)
api.include_router(automation.router)
api.include_router(resume.router)


@api.get("/")
async def root():
    return {"service": "MapleJourney API — Newcomers in Canada Wingman", "status": "ok", "engine": "Sovereign Intelligence v2.0"}


@api.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(api)


@app.get("/", include_in_schema=False)
async def frontend_root():
    if FRONTEND_INDEX_FILE.exists():
        return FileResponse(FRONTEND_INDEX_FILE)
    raise HTTPException(status_code=404, detail="Frontend build not found")


@app.get("/{path:path}", include_in_schema=False)
async def frontend_spa(path: str):
    if path.startswith("api"):
        raise HTTPException(status_code=404, detail="Not found")
    if FRONTEND_INDEX_FILE.exists():
        return FileResponse(FRONTEND_INDEX_FILE)
    raise HTTPException(status_code=404, detail="Frontend build not found")

_cors_origins = os.environ.get("CORS_ORIGINS", "*")
if _cors_origins == "*":
    _allow_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://maple-journey-app.vercel.app",
        "https://maplejourney.ca",
        "https://www.maplejourney.ca",
    ]
else:
    _allow_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_metrics_middleware(request, call_next):
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        metrics = getattr(app.state, "runtime_metrics", None)
        if metrics is not None:
            metrics["requests_total"] += 1
            metrics["latency_sum_ms"] += elapsed_ms
            metrics["latency_max_ms"] = max(metrics["latency_max_ms"], elapsed_ms)
            if status_code >= 500:
                metrics["errors_total"] += 1


@app.on_event("startup")
async def _startup():
    global _scheduler_task
    global _scheduler_stop_event
    global _notifications_task
    global _research_task
    app.state.started_at = time.time()
    app.state.runtime_metrics = {
        "requests_total": 0,
        "errors_total": 0,
        "latency_sum_ms": 0.0,
        "latency_max_ms": 0.0,
    }
    
    # Validate configuration (non-blocking for deployment)
    try:
        _validate_runtime_config()
        await _validate_database()
        await run_startup()
        await ensure_credit_indexes()
        
        # Initialize companion memory service
        from core.db import db
        companion_mem = CompanionMemory(db)
        await companion_mem.ensure_indexes()
        await ensure_webhook_indexes()

        # Initialize proactive deadline scheduler
        initialize_scheduler(db)
        logger.info("Proactive deadline scheduler initialized")

        _scheduler_stop_event = asyncio.Event()
        _scheduler_task = asyncio.create_task(
            scheduler_loop(
                db,
                interval_minutes=int(os.environ.get("UPDATE_PIPELINE_INTERVAL_MINUTES", "360")),
                stop_event=_scheduler_stop_event,
            )
        )
        logger.info("Companion memory service initialized")

        _notifications_task = asyncio.create_task(schedule_morning_notifications())
        logger.info("Morning notifications scheduler started")

        _research_task = asyncio.create_task(broadcast_research_insights())
        logger.info("Research insights broadcaster started")

    except Exception as e:
        logger.warning(f"Startup warning: {e}. Service will start in limited mode.")
        logger.info("Service started in limited mode. Add required env vars for full functionality.")
    finally:
        # Telegram should still come up even when optional startup tasks fail.
        await _init_telegram_services()


@app.on_event("shutdown")
async def _shutdown():
    global _research_task
    global _notifications_task
    logger.info("Shutting down...")
    
    # Cleanup Telegram bot
    if hasattr(app.state, 'telegram_app'):
        try:
            if getattr(app.state.telegram_app, "updater", None):
                await app.state.telegram_app.updater.stop()
            await app.state.telegram_app.stop()
            await app.state.telegram_app.shutdown()
            logger.info("✅ Telegram bot stopped")
        except Exception as e:
            logger.warning(f"Error stopping Telegram bot: {e}")
    
    if _scheduler_stop_event is not None:
        _scheduler_stop_event.set()
    if _scheduler_task is not None:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
    if _research_task is not None:
        _research_task.cancel()
        try:
            await _research_task
        except asyncio.CancelledError:
            pass
    if _notifications_task is not None:
        _notifications_task.cancel()
        try:
            await _notifications_task
        except asyncio.CancelledError:
            pass
    client.close()


if __name__ == "__main__":
    import uvicorn

    os.chdir(ROOT_DIR)
    uvicorn.run(
        "server:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
