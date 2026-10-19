# app/ui.py
import json, os, subprocess, sys, threading
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

ui = APIRouter()
RESULTS = os.path.join(os.environ.get("RESULTS_DIR", "/results"),
                       "emailserviceagent_fault_results.json")
ALL_MODES = ["NONE","FM_3_1","FM_2_2","FM_2_5","FM_1_2",
             "BL_SEND_SKIPPED","BL_DOUBLE_SEND","BL_CORRUPTED_BODY","BL_WRONG_CUSTOMER"]
_lock = threading.Lock()
_state = {"running": False, "log": ""}

def _run(modes):
    try:
        p = subprocess.run([sys.executable, "/srv/test_fault_injection.py", *modes],
                           capture_output=True, text=True, timeout=300)
        _state["log"] = p.stdout + p.stderr
    finally:
        _state["running"] = False

@ui.post("/ui/run")
def run(body: dict):
    modes = [m for m in body.get("modes", ALL_MODES) if m in ALL_MODES]
    with _lock:
        if _state["running"]:
            return {"status": "busy"}
        _state["running"] = True
    threading.Thread(target=_run, args=(modes,), daemon=True).start()
    return {"status": "started", "modes": modes}

@ui.get("/ui/status")
def status():
    return _state

@ui.get("/ui/results")
def results():
    try:
        return json.load(open(RESULTS))
    except FileNotFoundError:
        return {"results": []}

@ui.get("/ui", response_class=HTMLResponse)
def page():
    return open("/srv/app/ui.html").read()
