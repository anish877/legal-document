# Legal AI Analyzer Backend

This repository contains the backend for a Legal Document Analyzer built with FastAPI, HuggingFace Transformers, PyTorch, spaCy, PyMuPDF, and Tesseract OCR.

## Features

- Upload PDF or text documents
- Detect scanned PDFs and run OCR
- Clean and split long legal documents
- Map-reduce summarization with BART
- Named entity extraction with spaCy and legal regex heuristics
- Clause detection for common agreement clauses
- Final verdict detection for court judgments
- Risk analysis for missing or unbalanced clauses
- React dashboard for upload, progress tracking, extracted text review, and AI insight panels

## Project structure

```text
backend/
  main.py
  routes/
  services/
  models/
  utils/
frontend/
  src/
  components/
  pages/
```

## Local setup

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install the spaCy English model:

```bash
python -m spacy download en_core_web_sm
```

4. Install Tesseract OCR and make sure it is available in your `PATH`.

5. Run the API:

```bash
uvicorn backend.main:app --reload
```

6. Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

7. The frontend targets `http://127.0.0.1:8000` by default. To change it, set:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

8. Open the API docs:

```text
http://127.0.0.1:8000/docs
```

## Notes

- The first request that uses BART or Legal-BERT may download model weights from Hugging Face.
- If model downloads are unavailable, the service falls back to heuristic outputs where possible.

## Deployment

### Recommended setup

- Deploy the frontend on Vercel from the `frontend/` directory.
- Deploy the FastAPI backend as a Docker service on Render or Railway from the repo root.
- Point the frontend to the backend with `VITE_API_BASE_URL`.

### Backend deploy

This repo includes a production Dockerfile that installs:

- Python dependencies from `requirements.txt`
- `tesseract-ocr` for scanned PDF OCR
- the spaCy model `en_core_web_sm`

For Render:

1. Create a new Web Service from this repo.
2. Choose `Docker` as the runtime.
3. Use the repo root as the service root.
4. Set these environment variables:

```text
PORT=8000
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
```

5. Deploy and verify:

```text
https://your-backend-domain.onrender.com/health
https://your-backend-domain.onrender.com/docs
```

### Frontend deploy

In Vercel, set:

```text
VITE_API_BASE_URL=https://your-backend-domain.onrender.com
```

Then redeploy the frontend so the built app uses the backend URL.

### Production notes

- Wildcard CORS is only used when `ALLOWED_ORIGINS` is not set.
- OCR requires Tesseract, so a plain serverless Python function is not a good fit here.
- The first requests may be slower while model assets warm up or download.
