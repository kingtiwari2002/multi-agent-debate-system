import queue
import threading

from src.orchestrator import DebateOrchestrator
from src.presets import build_agents

DONE_SENTINEL = {"type": "done"}


class RunManager:
    """Bridges the synchronous, blocking DebateOrchestrator (real LLM calls,
    runs in a worker thread) to the async FastAPI/WebSocket world via a plain
    thread-safe queue per active run."""

    def __init__(self):
        self._queues: dict[str, queue.Queue] = {}

    def start(self, run_id: str, topic: str, mode: str, rounds: int) -> None:
        q: queue.Queue = queue.Queue()
        self._queues[run_id] = q
        thread = threading.Thread(target=self._run, args=(run_id, topic, mode, rounds, q), daemon=True)
        thread.start()

    def queue_for(self, run_id: str) -> "queue.Queue | None":
        return self._queues.get(run_id)

    def discard(self, run_id: str) -> None:
        self._queues.pop(run_id, None)

    @staticmethod
    def _run(run_id: str, topic: str, mode: str, rounds: int, q: queue.Queue) -> None:
        def on_event(event: dict) -> None:
            q.put(event)

        try:
            agent_configs = build_agents(mode)
            orchestrator = DebateOrchestrator(
                topic=topic,
                agent_configs=agent_configs,
                max_rounds=rounds,
                mode=mode,
                on_event=on_event,
                run_id=run_id,
            )
            run = orchestrator.run()
            q.put({"type": "done", "run": run.to_dict()})
        except Exception as exc:  # surface backend errors to the connected client instead of hanging it
            q.put({"type": "error", "message": str(exc)})
            q.put({"type": "done"})


run_manager = RunManager()
