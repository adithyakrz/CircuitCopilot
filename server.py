from pathlib import Path
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import HTMLResponse
import uvicorn
from engine import analyze_circuit

app = FastAPI()

HTML_PATH = Path("templates") / "index.html"

@app.get("/", response_class=HTMLResponse)
def index():
    if not HTML_PATH.exists():
        return HTMLResponse("<h1>Error: templates/index.html not found</h1>", status_code=500)
    return HTMLResponse(HTML_PATH.read_text(encoding="utf-8"))

@app.post("/api/inspect")
async def inspect(image: UploadFile, preset: str = Form(...)):
    contents = await image.read()
    return analyze_circuit(contents, preset)

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)