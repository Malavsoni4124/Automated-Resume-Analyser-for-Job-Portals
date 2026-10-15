"""
Standalone FastAPI Resume Parser API Wrapper
Deliverable 3: Simple FastAPI script allowing a user to upload a file
via a local web server and receive the parsed JSON response.
"""
import os
import sys
import tempfile
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.parser import ResumeParser

app = FastAPI(
    title="Resume Parser API Engine",
    description="Deliverable 3: API Wrapper for Automated Resume Ingestion & Parsing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize single instance of parser
parser = ResumeParser()
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resume Parser API Wrapper</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }
            h1 { color: #1e293b; }
            .card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; margin-top: 20px; }
            input[type=file] { margin: 15px 0; }
            button { background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 15px; }
            button:hover { background: #1d4ed8; }
            pre { background: #0f172a; color: #f8fafc; padding: 16px; border-radius: 6px; overflow-x: auto; max-height: 400px; }
        </style>
    </head>
    <body>
        <h1>📄 Resume Parser API Wrapper</h1>
        <p>Upload a resume in <strong>PDF, DOCX, or TXT</strong> format to extract structured JSON data.</p>
        <div class="card">
            <h3>Test Upload Directly</h3>
            <input type="file" id="resumeFile" accept=".pdf,.docx,.doc,.txt" />
            <br>
            <button onclick="uploadResume()">Upload & Parse Resume</button>
            <h4>Parsed JSON Output:</h4>
            <pre id="output">Waiting for file upload...</pre>
        </div>
        <p><a href="/docs">View Interactive Swagger API Docs (/docs)</a></p>
        <script>
            async function uploadResume() {
                const fileInput = document.getElementById('resumeFile');
                if (!fileInput.files[0]) {
                    alert('Please select a resume file first!');
                    return;
                }
                const output = document.getElementById('output');
                output.textContent = 'Parsing resume... Please wait...';
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);

                try {
                    const res = await fetch('/parse', { method: 'POST', body: formData });
                    const json = await res.json();
                    output.textContent = JSON.stringify(json, null, 2);
                } catch (e) {
                    output.textContent = 'Error parsing resume: ' + e;
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/parse", summary="Upload resume and get parsed JSON")
async def parse_resume(file: UploadFile = File(...)):
    """Uploads a resume file (PDF, DOCX, TXT) and returns structured JSON output."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        parsed_dict = parser.parse_file(tmp_path)
        return JSONResponse(content=parsed_dict)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Resume Parser API on http://localhost:{port}")
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
