import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import chromadb

from database import get_db, engine, Base
import models

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Entropy Civil API")

# Add CORS so React frontend can fetch data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Since it's a local experiment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_CHROMA_DATA_PATH = os.path.join(os.path.dirname(__file__), "chroma_data")
try:
    chroma_client = chromadb.PersistentClient(path=_CHROMA_DATA_PATH)
    chroma_collection = chroma_client.get_or_create_collection(name="civilization_memories")
except Exception as e:
    print(f"Failed to initialize ChromaDB: {e}")
    chroma_collection = None

@app.get("/")
def read_root():
    return {"message": "Welcome to Entropy Civil API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/universe")
def get_universe_data():
    """Return vector data for 3D mapping"""
    if not chroma_collection:
        return {"error": "ChromaDB not connected", "data": []}
        
    try:
        # Get all entries for visualization (up to a limit)
        results = chroma_collection.get(limit=1000, include=["documents", "metadatas", "embeddings"])
        
        # Format for frontend 3D rendering
        particles = []
        if results and results.get("ids"):
            for i in range(len(results["ids"])):
                # We need XYZ coordinates. Assuming we have embeddings, we take first 3 dims.
                # If embeddings aren't returned or less than 3 dims, mock them defensively.
                emb = results["embeddings"][i] if results.get("embeddings") else None
                if emb and len(emb) >= 3:
                    pos = [emb[0]*10, emb[1]*10, emb[2]*10]  # Scale factor
                else:
                    # Fallback deterministic random based on hash for stable display
                    import hashlib
                    h = int(hashlib.sha256(results["ids"][i].encode()).hexdigest(), 16)
                    pos = [
                        (h % 100 - 50) * 1.5,
                        ((h // 100) % 100 - 50) * 1.5,
                        ((h // 10000) % 100 - 50) * 1.5
                    ]
                
                meta = results["metadatas"][i] or {}
                
                particles.append({
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "position": pos,
                    "importance": meta.get("importance", 0.5),
                    "isLegend": meta.get("entropy_level", 0.0) > 0.5,
                    "agent_id": meta.get("agent_id", "Unknown")
                })
        return {"data": particles}
    except Exception as e:
        return {"error": str(e), "data": []}

@app.get("/api/history")
def get_historical_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Return stream of recent simulation events"""
    logs = db.query(models.SimulationEvent).order_by(models.SimulationEvent.id.desc()).limit(limit).all()
    # Return in reverse so oldest is first in the output
    return {"logs": [{"id": l.id, "turn": l.turn, "type": l.event_type, "content": l.content} for l in reversed(logs)]}

@app.get("/api/epochs")
def get_historical_epochs(db: Session = Depends(get_db)):
    """Return timeline of epochs"""
    epochs = db.query(models.HistoricalEpoch).order_by(models.HistoricalEpoch.turn_start.asc()).all()
    return {"epochs": [{"id": e.id, "name": e.epoch_name, "turn_start": e.turn_start} for e in epochs]}

# Run with: uvicorn main:app --reload
