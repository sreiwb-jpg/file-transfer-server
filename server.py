from fastapi import FastAPI, Form

app = FastAPI()

clients = {}

@app.post("/register")
def register(system_id: str = Form(...)):
    clients[system_id] = "online"
    return {"status": "ok"}

@app.get("/clients")
def get_clients():
    return clients

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "1234":
        return {"status": "success"}
    return {"status": "fail"}
