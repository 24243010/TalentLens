# Intelligent Resume Analyzer (Pink & Cream)

Offline resume screening web app. No API key, no internet needed after install.

## Run
Windows: double-click `run.bat`  |  Mac/Linux: `bash run.sh`
Then open http://localhost:8501 and click **Try demo** (10 sample resumes).

## Features
PDF/DOCX/TXT resumes, JD paste or upload, match score, ranking, ATS score,
skill gap, strengths/weaknesses, interactive charts, HR report CSV download.

## Docker
    docker build -t resume-analyzer .
    docker run -p 8501:8501 resume-analyzer

## CI/CD
`Jenkinsfile`: checkout, pytest, docker build, push to Docker Hub
(Jenkins credential id: `dockerhub-creds`; set your username in `IMAGE`).

## Tests
    pip install pytest && pytest -q tests
