from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class SimulationEvent(Base):
    __tablename__ = "simulation_events"

    id = Column(Integer, primary_key=True, index=True)
    turn = Column(Integer, index=True)
    agent_id = Column(String, index=True)
    event_type = Column(String)  # e.g., "LOCAL_CHAT", "CLOUD_SUMMARY", "ENTROPY"
    content = Column(Text)
    vector_hash = Column(String, nullable=True) # Link to ChromaDB if stored
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class HistoricalEpoch(Base):
    __tablename__ = "historical_epochs"

    id = Column(Integer, primary_key=True, index=True)
    turn_start = Column(Integer)
    turn_end = Column(Integer, nullable=True)
    epoch_name = Column(String)
    master_prompt = Column(Text, nullable=True)  # The generated prompt for this epoch
    summary_vector_hash = Column(String, nullable=True)  # Link to aggregate vector
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to manually curated art
    artworks = relationship("CuratedArtwork", back_populates="epoch")

class CuratedArtwork(Base):
    __tablename__ = "curated_artworks"

    id = Column(Integer, primary_key=True, index=True)
    epoch_id = Column(Integer, ForeignKey("historical_epochs.id"))
    image_path = Column(String) # Path to where the image is stored (e.g. static/uploads/)
    curator_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    epoch = relationship("HistoricalEpoch", back_populates="artworks")
