from fastapi import FastAPI, Form
import uvicorn
import time

app = FastAPI()

# Store clients with last seen time
clients = {}

# ✅ Home route (fixes "Not Found")
@app.get("/")
def home():
    return {"message": "Server is running"}

# ✅ Client registration (heartbeat)
@app.post("/register")
def register(system_id: str = Form(...)):
    clients[system_id] = time.time()
    return {"status": "registered"}

# ✅ Get only ONLINE clients (last seen within 10 sec)
@app.get("/clients")
def get_clients():
    current_time = time.time()
    online_clients = {
        cid: "online"
        for cid, t in clients.items()
        if current_time - t < 10
    }
    return online_clients

# ✅ Optional: check specific client
@app.get("/client/{system_id}")
def check_client(system_id: str):
    if system_id in clients:
        return {"status": "online"}
    return {"status": "offline"}

# Render start
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
