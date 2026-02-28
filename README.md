# ✦ Entropy Civil

> A multi-agent civilization simulation that generates its own myths, legends, and history — powered by local LLMs running entirely on your machine.

---

## What is this?

**Entropy Civil** is a long-running simulation where AI agents live, act, and reflect on their lives in an ancient village. Over hundreds of turns, their mundane memories gradually distort and exaggerate — transforming into myths and legends through a process called **Entropy Injection**.

The resulting history is visualized in real-time through a cinematic web UI.

---

## Architecture

```
┌──────────────────────────────────────────────┐
│  FRONTEND (React + Vite + Three.js)          │
│  ├── Concept Universe  - 3D memory galaxy    │
│  ├── Code of History   - real-time log feed  │
│  └── Curatorial Gallery - curated AI art     │
└───────────────┬──────────────────────────────┘
                │  HTTP (port 8002)
┌───────────────▼──────────────────────────────┐
│  BACKEND (FastAPI, port 8002)                │
│  /api/history  /api/universe  /api/epochs    │
└──────┬──────────────────────┬────────────────┘
       │                      │
┌──────▼───────┐   ┌──────────▼────────────────┐
│  PostgreSQL  │   │ ChromaDB (local)           │
│  Event Logs  │   │ Agent Memory Vectors       │
└──────────────┘   └───────────────────────────┘
                               │
┌─────────────────────────────▼──────────────┐
│  Ollama (local LLM, port 11434)            │
│  ├── llama3.2    – daily agent chatter     │
│  ├── gemma2:9b   – reflections & myths     │
│  └── mxbai-embed-large – memory vectors   │
└────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/) (or Colima on Mac)
- [Ollama](https://ollama.com/) with the following models:
  ```bash
  ollama pull llama3.2
  ollama pull gemma2:9b
  ollama pull mxbai-embed-large
  ```
- Python 3.11+ and Node.js 20+

### 1. Start the databases

```bash
docker-compose up -d
```

### 2. Set up the Python backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the services

Open **2 separate terminals**:

```bash
# Terminal 1 – Backend & Simulation (using dev_runner)
source backend/.venv/bin/activate
python3 dev_runner.py

# Terminal 2 – Frontend
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173` (or the port shown by Vite) in your browser.

---

## How It Works

| Component | Description |
|---|---|
| `simulation.py` | Main loop — each "turn" = 1 day. Agents act, reflect, and mythologize. |
| `llm_router.py` | Routes prompts to the right local LLM (fast daily chat vs. deep reflection) |
| `epoch_detector.py` | Every 50 turns, names a new historical era using gemma2:9b |
| `chronicle_summarizer.py` | Every 100 turns, writes a dramatic chronicle and saves it to DB |
| `memory.py` | ChromaDB-backed long-term memory with semantic search |

### Entropy Injection

Every 5 turns, agents "reflect" on their recent memories. With a configurable probability (`entropy_factor`), the reflection exaggerates reality into myth:

> *"We went fishing today."* → *"The great river spirit gifted us its silver children, and we wept with gratitude."*

---

## NAS Deployment

A production-ready configuration is included for deploying to a home NAS (e.g., UGREEN):

```bash
# On your NAS
docker-compose -f docker-compose.nas.yml up -d
```

Set `OLLAMA_BASE_URL` in `.env` to point to your Ollama instance.

---

## Environment Variables

Create a `.env` file at the project root:

```env
DATABASE_URL=postgresql://civ_user:civ_password@localhost:5432/civ_timeline
CHROMA_DATA_PATH=./chroma_data_v2
OLLAMA_BASE_URL=http://localhost:11434
VITE_API_BASE_URL=http://localhost:8002
```

---

## License

MIT
