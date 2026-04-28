from fastapi import FastAPI, UploadFile, File, Form
import os
import time

app = FastAPI()

clients = {}
tasks = {}

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

# Upload file (Admin → Server)
@app.post("/upload")
async def upload(system_id: str = Form(...), file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, file.filename)

    with open(path, "wb") as f:
        f.write(await file.read())

    tasks[system_id] = file.filename
    return {"status": "uploaded"}

# Client checks if file available
@app.get("/task/{system_id}")
def get_task(system_id: str):
    if system_id in tasks:
        return {"file": tasks[system_id]}
    return {"file": None}

# Download file
@app.get("/download/{filename}")
def download(filename: str):
    return {"url": f"/files/{filename}"}
