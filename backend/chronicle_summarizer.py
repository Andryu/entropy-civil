"""
Chronicle Summarizer - 長期観測用の定期ログ要約モジュール (Phase 5)

N ターンごとに DB のイベントログを読み取り、
- コンソールに「文明の年代記」として出力
- DB の SimulationEvent に CHRONICLE_SUMMARY タイプで保存

これにより長期観測後に「何が起きたか」を人間が後で読めるようになる。
"""
import os
import requests
from database import SessionLocal
import models

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHRONICLE_INTERVAL = 100  # 100ターンごとに年代記を生成


def _call_ollama(prompt: str) -> str:
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "gemma2:9b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.5, "num_predict": 200},
            },
            timeout=90,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[Chronicle] LLM call failed: {e}")
        return ""


def generate_chronicle(current_turn: int) -> bool:
    """
    Every CHRONICLE_INTERVAL turns, summarize recent events into a chronicle entry.
    Returns True if a chronicle was generated.
    """
    if current_turn % CHRONICLE_INTERVAL != 0 or current_turn == 0:
        return False

    db = SessionLocal()
    try:
        since_turn = current_turn - CHRONICLE_INTERVAL

        # Gather REFLECTIONs and DAILY_ACTIONs from the period
        events = (
            db.query(models.SimulationEvent)
            .filter(
                models.SimulationEvent.turn >= since_turn,
                models.SimulationEvent.turn < current_turn,
            )
            .order_by(models.SimulationEvent.turn.asc())
            .all()
        )

        if not events:
            return False

        # Separate reflections for richer context
        reflections = [e.content for e in events if e.event_type == "REFLECTION"]
        actions_sample = [e.content for e in events if e.event_type == "DAILY_ACTION"][:5]

        reflection_text = "\n".join(reflections[:8]) if reflections else "No reflections recorded."
        action_text = "\n".join(actions_sample) if actions_sample else "No actions recorded."

        prompt = (
            f"You are writing a chronicle of an ancient civilization.\n"
            f"Turns {since_turn} to {current_turn} have passed.\n\n"
            f"Daily activities (sample):\n{action_text}\n\n"
            f"Oral traditions and myths that emerged:\n{reflection_text}\n\n"
            f"Write a 3-4 sentence historical summary of this era in a dramatic, "
            f"ancient-chronicle style. Focus on the most interesting cultural developments."
        )

        summary = _call_ollama(prompt)
        if not summary:
            return False

        event = models.SimulationEvent(
            turn=current_turn,
            agent_id="SYSTEM",
            event_type="CHRONICLE_SUMMARY",
            content=f"[Chronicle T{since_turn}-{current_turn}] {summary}",
        )
        db.add(event)
        db.commit()

        print(f"\n{'═'*60}")
        print(f"📜 CHRONICLE (Turn {since_turn}–{current_turn})")
        print(f"{'═'*60}")
        print(summary)
        print(f"{'═'*60}\n")
        return True

    except Exception as e:
        db.rollback()
        print(f"[Chronicle] Error: {e}")
        return False
    finally:
        db.close()
