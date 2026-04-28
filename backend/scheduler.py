"""Weekly horoscope dispatcher.

Exposes ``dispatch_weekly_horoscope()`` — renders template 06 with
generated content and sends to every confirmed subscriber. Also wires an
APScheduler cron that fires every Sunday 18:00 UTC inside the FastAPI
process.

The in-process scheduler is convenient for MVP but will not survive
container restarts across a firing window. For production reliability,
prefer an external cron hitting ``POST /api/admin/dispatch-weekly`` with
the ``ADMIN_SECRET`` bearer token.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import email_service
from content_generator import build_weekly_vars

logger = logging.getLogger("liveastrology.scheduler")

# Populated on startup by server.py
_scheduler: AsyncIOScheduler | None = None


def _unsub_url(token: str) -> str:
    origin = os.environ.get("APP_ORIGIN", "https://liveastrology.app").rstrip("/")
    return f"{origin}/api/unsubscribe?token={token}"


async def dispatch_weekly_horoscope(db) -> dict[str, Any]:
    """Render template 06 per-subscriber and send it. Returns a summary dict."""
    cursor = db.subscribers.find({"status": "confirmed"}, {"_id": 0})
    sent, failed = 0, 0
    recipients: list[str] = []

    async for sub in cursor:
        vars_ = build_weekly_vars(
            first_name=sub.get("first_name") or "there",
            unsubscribe_url=_unsub_url(sub["unsub_token"]),
        )
        vars_["email"] = sub["email"]
        result = await email_service.send_template(
            "weekly_horoscope",
            to=sub["email"],
            list_unsubscribe=_unsub_url(sub["unsub_token"]),
            **vars_,
        )
        recipients.append(sub["email"])
        if result is None:
            failed += 1
        else:
            sent += 1

    await db.weekly_dispatches.insert_one({
        "dispatched_at": datetime.now(timezone.utc),
        "sent": sent,
        "failed": failed,
        "total": sent + failed,
    })
    logger.info("weekly dispatch complete sent=%s failed=%s total=%s", sent, failed, sent + failed)
    return {"sent": sent, "failed": failed, "total": sent + failed, "recipients": recipients}


def start_scheduler(db) -> AsyncIOScheduler:
    """Start the APScheduler loop. Idempotent — returns the existing one if
    already running."""
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler

    scheduler = AsyncIOScheduler(timezone="UTC")
    # Sundays at 18:00 UTC — same Sunday-evening slot we advertise in the
    # welcome email ("every Sunday evening").
    scheduler.add_job(
        dispatch_weekly_horoscope,
        trigger=CronTrigger(day_of_week="sun", hour=18, minute=0),
        args=[db],
        id="weekly_horoscope",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("scheduler started — next weekly dispatch at %s", scheduler.get_job("weekly_horoscope").next_run_time)
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
