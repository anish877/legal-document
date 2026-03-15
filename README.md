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
