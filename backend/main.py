import os
import shutil
from typing import Optional, List
from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# Create static directory if it doesn't exist and mount it
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "curated_art"), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

_CHROMA_DATA_PATH = os.path.join(os.path.dirname(__file__), "chroma_data_v2")
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
                    "isLegend": meta.get("entropy_level", 0.0) > 0.5 or "[LEGEND]" in results["documents"][i],
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
    
    # Also look for images in static folder
    result = []
    for e in epochs:
        # Simple check for image: [epoch_id].jpg
        image_path_relative = f"/static/curated_art/{e.id}.jpg"
        image_path_absolute = os.path.join(static_dir, "curated_art", f"{e.id}.jpg")
        
        # Check if the image actually exists on the filesystem to prevent 404s
        image_url = image_path_relative if os.path.exists(image_path_absolute) else None
        
        result.append({
            "id": e.id, 
            "name": e.epoch_name, 
            "turn_start": e.turn_start,
            "master_prompt": e.master_prompt,
            "image_url": image_url
        })
    return {"epochs": result}

@app.get("/api/sandbox/state")
def get_sandbox_state():
    """Return current state of all agents for the sandbox view"""
    import json
    state_file = os.path.join(static_dir, "sandbox_state.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e), "data": {}}
    return {"error": "No state yet", "data": {}}

@app.post("/api/epochs/{epoch_id}/upload")
async def upload_epoch_image(epoch_id: int, file: UploadFile = File(...)):
    """Upload an image for a specific epoch"""
    if not file.content_type.startswith("image/"):
        return {"error": "File must be an image"}
        
    image_path = os.path.join(static_dir, "curated_art", f"{epoch_id}.jpg")
    
    try:
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"status": "success", "message": f"Image uploaded for epoch {epoch_id}"}
    except Exception as e:
        return {"error": str(e)}

# Run with: uvicorn main:app --reload --port 8002
