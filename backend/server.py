"""Minimal backend stub so supervisor can start.

This Live Astrology app is a single-page client-side React/Vite site with no
real backend. Supervisor still expects /app/backend to exist, so this file
provides a tiny FastAPI app that exposes only /api/health — useful for
future backend work (e.g. proxying a real geocoder) but doing nothing today.
"""
from fastapi import FastAPI

app = FastAPI(title="liveastrology backend (stub)")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
