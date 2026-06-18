# Deploy on Vercel — Settings Guide

Repository: https://github.com/Nauman-Irshad/Prompt-Injection-Security-Chatbot

## What to enter in Vercel dashboard

| Field | Enter this |
|-------|------------|
| **Root Directory** | `./` (leave default — project is repo root) |
| **Framework Preset** | **Other** |
| **Build Command** | *(leave empty)* |
| **Output Directory** | *(leave empty / N/A)* |
| **Install Command** | `pip install -r requirements-vercel.txt` |

## Environment Variables

**No env vars required** for basic demo.

You can leave `EXAMPLE_NAME` empty — delete it if Vercel shows a placeholder.

Optional (not needed):
| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.11` |

## Environments

Select: **Production** (and Preview if you want test URLs)

## Steps

1. Go to [vercel.com](https://vercel.com) → **Add New Project**
2. Import GitHub repo: `Nauman-Irshad/Prompt-Injection-Security-Chatbot`
3. Enter settings from table above
4. Click **Deploy**
5. Open your URL: `https://your-project.vercel.app`

## What works on Vercel

- Chatbot UI (`/`)
- Prompt scan API (`/api/scan`)
- Mirror Detector + P2SQL blocking
- Rule-based safe answers (no heavy LLM download)
- Research dashboard (`/dashboard`)

## What does NOT work on Vercel (serverless limits)

- Full PySpark / Hadoop (needs Java + big memory)
- `google/flan-t5-small` download (too large for serverless)
- ChromaDB RAG demos

For **full project with Spark + LLM**, run locally or use **Render** / **Railway** instead.

## Files added for Vercel

- `app.py` — Flask entrypoint (Vercel auto-detects this)
- `pyproject.toml` — points to `backend.chat_server:app`
- `vercel.json` — install command + function settings
- `requirements-vercel.txt` — lightweight packages only

If deploy fails, run locally first to test:

```bash
pip install -r requirements-vercel.txt
vercel dev
```
