"""
Shared fault-injection UI endpoints for an agent pod.

Drop this file into <agent>/app/ui.py (same file for every agent) and add to main.py:

    from app.ui import ui
    app.include_router(ui)

Endpoints
    GET  /ui/modes     -> {"agent": "...", "modes": [...]}   (read from the test script, no import)
    POST /ui/run       -> body {"modes": [...]}               starts the test script in a subprocess
    GET  /ui/status    -> {"running": bool, "log": str, "started_at": ..., "finished_at": ..., "modes": [...]}
    GET  /ui/results   -> contents of the newest *_fault_results.json in RESULTS_DIR
    GET  /ui           -> standalone page (app/ui.html), optional

Environment
    RESULTS_DIR   where the test script writes its JSON (default /results)
    TEST_SCRIPT   path to the test script (default /srv/test_fault_injection.py)
    AGENT_NAME    label returned by /ui/modes (default: APP_NAME or "agent")
"""
import ast
import glob
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

ui = APIRouter()

RESULTS_DIR = os.environ.get("RESULTS_DIR", "/results")
TEST_SCRIPT = os.environ.get("TEST_SCRIPT", "/srv/test_fault_injection.py")
AGENT_NAME = os.environ.get("AGENT_NAME") or os.environ.get("APP_NAME") or "agent"
RUN_TIMEOUT_S = int(os.environ.get("RUN_TIMEOUT_S", "600"))

_lock = threading.Lock()
_state = {"running": False, "log": "", "started_at": None, "finished_at": None,
          "modes": [], "returncode": None}


def _read_all_modes():
    """Read ALL_MODES from the test script with ast.

    The test script stubs modules in sys.modules at import time (langgraph, grpc, ...),
    so importing it inside the web server would poison the running app.
    """
    try:
        tree = ast.parse(Path(TEST_SCRIPT).read_text())
    except (OSError, SyntaxError):
        return []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "ALL_MODES":
                    try:
                        return list(ast.literal_eval(node.value))
                    except ValueError:
                        return []
    return []


def _run(modes):
    try:
        env = dict(os.environ, RESULTS_DIR=RESULTS_DIR)
        p = subprocess.run([sys.executable, TEST_SCRIPT, *modes],
                           capture_output=True, text=True,
                           timeout=RUN_TIMEOUT_S, env=env)
        _state["log"] = (p.stdout or "") + (p.stderr or "")
        _state["returncode"] = p.returncode
    except subprocess.TimeoutExpired:
        _state["log"] = f"Timed out after {RUN_TIMEOUT_S}s"
        _state["returncode"] = -1
    except Exception as e:  # noqa: BLE001 - surface any failure to the UI
        _state["log"] = f"Failed to start test script: {e}"
        _state["returncode"] = -1
    finally:
        _state["finished_at"] = time.time()
        _state["running"] = False


@ui.get("/ui/modes")
def modes():
    return {"agent": AGENT_NAME, "modes": _read_all_modes()}


@ui.post("/ui/run")
def run(body: dict):
    allowed = _read_all_modes()
    if not allowed:
        return JSONResponse({"status": "error", "detail": f"no ALL_MODES found in {TEST_SCRIPT}"},
                            status_code=500)
    requested = body.get("modes") or allowed
    selected = [m for m in requested if m in allowed]
    if not selected:
        return JSONResponse({"status": "error", "detail": "no valid modes selected"}, status_code=400)
    with _lock:
        if _state["running"]:
            return {"status": "busy"}
        _state.update(running=True, log="", started_at=time.time(), finished_at=None,
                      modes=selected, returncode=None)
    threading.Thread(target=_run, args=(selected,), daemon=True).start()
    return {"status": "started", "modes": selected}


@ui.get("/ui/status")
def status():
    return _state


@ui.get("/ui/results")
def results():
    files = glob.glob(os.path.join(RESULTS_DIR, "*_fault_results.json"))
    if not files:
        return {"results": []}
    newest = max(files, key=os.path.getmtime)
    try:
        with open(newest) as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        return JSONResponse({"results": [], "error": str(e)}, status_code=500)
    data["file"] = os.path.basename(newest)
    data["file_mtime"] = os.path.getmtime(newest)
    return data


@ui.get("/ui", response_class=HTMLResponse)
def page():
    p = Path(__file__).with_name("ui.html")
    if p.exists():
        return p.read_text()
    return "<p>Standalone page not included. Use the dashboard, or see /ui/modes, /ui/status, /ui/results.</p>"
