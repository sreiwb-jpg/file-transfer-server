from fastapi import FastAPI, Request, Form
import time

app = FastAPI()

clients = {}

@app.get("/")
def home():
    return {"message": "Server running"}

@app.post("/register")
async def register(request: Request, system_id: str = Form(...)):
    ip = request.client.host
    clients[system_id] = {
        "ip": ip,
        "last_seen": time.time()
    }
    return {"status": "ok"}

@app.get("/clients")
def get_clients():
    current = time.time()
    return {
        cid: data["ip"]
        for cid, data in clients.items()
        if current - data["last_seen"] < 15
    }
