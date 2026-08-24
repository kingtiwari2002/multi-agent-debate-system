import asyncio
import json
import sys
import uuid
from pathlib import Path

# Allow `import src....` when this file is run directly (uvicorn web.backend.main:app
# from the project root already has this on sys.path, but keep it robust either way).
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from run_manager import run_manager

load_dotenv()

RUNS_DIR = PROJECT_ROOT / "runs"
FRONTEND_DIST = PROJECT_ROOT / "web" / "frontend" / "dist"

app = FastAPI(title="Multi-Agent Debate System API")

# Same-origin now that the built frontend is served from this app too, but
# harmless to leave open for local tooling (curl, alternate dev clients).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class StartDebateRequest(BaseModel):
    topic: str
    mode: str = "adversarial"
    rounds: int = 3


@app.post("/api/debates")
def start_debate(req: StartDebateRequest):
    if not req.topic.strip():
        raise HTTPException(400, "topic is required")
    if req.mode not in ("adversarial", "ensemble"):
        raise HTTPException(400, "mode must be 'adversarial' or 'ensemble'")
    if not (1 <= req.rounds <= 10):
        raise HTTPException(400, "rounds must be between 1 and 10")

    run_id = str(uuid.uuid4())[:8]
    run_manager.start(run_id, req.topic, req.mode, req.rounds)
    return {"run_id": run_id}


@app.websocket("/ws/debates/{run_id}")
async def stream_debate(websocket: WebSocket, run_id: str):
    await websocket.accept()
    q = run_manager.queue_for(run_id)
    if q is None:
        await websocket.send_json({"type": "error", "message": "unknown or already-finished run_id"})
        await websocket.close()
        return

    try:
        while True:
            event = await asyncio.to_thread(q.get)
            await websocket.send_json(event)
            if event.get("type") == "done":
                break
    except WebSocketDisconnect:
        pass
    finally:
        run_manager.discard(run_id)


@app.get("/api/debates")
def list_debates():
    if not RUNS_DIR.exists():
        return []
    summaries = []
    for path in sorted(RUNS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        summaries.append(
            {
                "run_id": data.get("run_id"),
                "topic": data.get("topic"),
                "mode": data.get("mode"),
                "final_winner": data.get("final_winner"),
                "judges_agreed": data.get("judges_agreed"),
                "total_llm_calls": data.get("total_llm_calls"),
                "created_at": data.get("created_at"),
            }
        )
    return summaries


@app.get("/api/debates/{run_id}")
def get_debate(run_id: str):
    path = RUNS_DIR / f"{run_id}.json"
    if not path.exists():
        raise HTTPException(404, "run not found")
    return json.loads(path.read_text(encoding="utf-8"))


# Mounted last so it never shadows the /api/* and /ws/* routes above — Starlette
# tries routes in registration order, so this catch-all only matches what
# nothing else claimed. Serves the built React app (run `npm run build` in
# web/frontend first) so the API and UI share this one port.
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=55786)
