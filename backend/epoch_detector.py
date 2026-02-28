"""
Epoch Detector - 文明の節目（エポック）を自動検出するモジュール

エポック検出ロジック:
- 一定ターン数ごとに全REFLECTIONログをLLMに読ませ、「時代の変化」があったか判定
- 時代の変化があれば HistoricalEpoch テーブルに自動記録する
"""
import os
import requests
from database import SessionLocal
import models

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EPOCH_CHECK_INTERVAL = 50  # N ターンごとにエポック検出を実行


def _call_ollama(prompt: str) -> str:
    """Call Ollama for epoch analysis."""
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "gemma2:9b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 80},
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[EpochDetector] LLM call failed: {e}")
        return ""


def detect_and_record_epoch(current_turn: int) -> bool:
    """
    Checks if a new epoch should be recorded at the given turn.
    Returns True if a new epoch was created.
    """
    if current_turn % EPOCH_CHECK_INTERVAL != 0 or current_turn == 0:
        return False

    db = SessionLocal()
    try:
        # Gather recent REFLECTIONs from the last EPOCH_CHECK_INTERVAL turns
        since_turn = current_turn - EPOCH_CHECK_INTERVAL
        reflections = (
            db.query(models.SimulationEvent)
            .filter(
                models.SimulationEvent.event_type == "REFLECTION",
                models.SimulationEvent.turn >= since_turn,
                models.SimulationEvent.turn < current_turn,
            )
            .order_by(models.SimulationEvent.turn.asc())
            .all()
        )

        if not reflections:
            return False

        # Check if last epoch already covers this turn range
        last_epoch = (
            db.query(models.HistoricalEpoch)
            .order_by(models.HistoricalEpoch.turn_start.desc())
            .first()
        )
        if last_epoch and last_epoch.turn_start >= since_turn:
            return False  # Epoch already recorded for this period

        # Build summary for LLM judgement
        reflection_texts = "\n".join(
            [f"T-{r.turn}: {r.content}" for r in reflections[:10]]
        )

        # 1. Generate Era Name
        name_prompt = (
            "You are a historian analyzing an ancient civilization's memories.\n"
            "Based on the following reflections from turns "
            f"{since_turn} to {current_turn}, "
            "invent a short, evocative NAME for this era (5 words or less). "
            "Just output the era name, nothing else.\n\n"
            f"Reflections:\n{reflection_texts}\n\nEra Name:"
        )
        era_name = _call_ollama(name_prompt)
        if not era_name:
            era_name = f"The Era of Turn {since_turn}"
        era_name = era_name.strip().strip('"\'').split("\n")[0][:100]

        # 2. Generate Master Prompt for Image Generation (Midjourney style)
        art_prompt = (
            "You are a visionary prompt engineer. Based on the era ' " + era_name + " ' "
            "and these historical context symbols:\n" + reflection_texts + "\n\n"
            "Create a single, highly detailed, cinematic Midjourney prompt (in English) "
            "that visually represents the soul of this era. Format: [Subject], [Environment], "
            "[Atmosphere/Lighting], [Art Style], --ar 16:9 --v 6.0. "
            "Output ONLY the prompt text."
        )
        master_prompt = _call_ollama(art_prompt)
        if not master_prompt:
            master_prompt = f"A cinematic representation of the {era_name} era, ancient civilization style, hyper-realistic --ar 16:9"

        new_epoch = models.HistoricalEpoch(
            epoch_name=era_name,
            turn_start=since_turn,
            turn_end=current_turn,
            master_prompt=master_prompt
        )
        db.add(new_epoch)
        db.commit()
        print(f"[EpochDetector] ✦ New Epoch recorded: '{era_name}'")
        print(f"[EpochDetector] 🎨 Master Prompt: {master_prompt[:50]}...")
        return True

    except Exception as e:
        db.rollback()
        print(f"[EpochDetector] Error: {e}")
        return False
    finally:
        db.close()
