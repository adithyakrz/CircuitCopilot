from pathlib import Path
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from engine import analyze_circuit, CIRCUIT_PRESETS

app = FastAPI(title="CircuitCopilot Workstation")

HTML_PATH = Path("templates") / "index.html"

@app.get("/", response_class=HTMLResponse)
def index():
    if not HTML_PATH.exists():
        return HTMLResponse("<h1>Error: templates/index.html not found</h1>", status_code=500)
    return HTMLResponse(HTML_PATH.read_text(encoding="utf-8"))

@app.get("/api/health")
def health():
    return {
        "status": "ONLINE",
        "model": "muse-spark-1.3",
        "presets": list(CIRCUIT_PRESETS.keys())
    }

@app.post("/api/inspect")
async def inspect(image: UploadFile, preset: str = Form(...)):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a PNG, JPEG, or WebP circuit image.")
    try:
        contents = await image.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Uploaded image file is empty.")
        result = analyze_circuit(contents, preset)
        return JSONResponse(content=result)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "message": "Diagnostic engine execution failed."}
        )

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)