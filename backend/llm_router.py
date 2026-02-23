import random
import os
import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

class LLMRouter:
    def __init__(self):
        # Lightweight model for daily chatter
        self.fast_model = "llama3.2:latest"
        # Stronger model for reflection & myth-creation
        self.smart_model = "gemma2:9b"
        # Embedding model for vector extraction
        self.embed_model = "mxbai-embed-large:latest"

    def _call_ollama(self, model: str, prompt: str, temperature: float = 0.7) -> str:
        """Send a prompt to the local Ollama API and return the response text."""
        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": 120,  # Keep responses concise
                    }
                },
                timeout=60
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except Exception as e:
            print(f"[LLMRouter] Ollama call failed ({model}): {e}")
            return f"[FALLBACK] The agent pondered silently."

    def chat_daily(self, prompt: str) -> str:
        """
        Used for fast, cheap, local everyday conversations among agents.
        Uses llama3.2 for speed.
        """
        system_prompt = (
            "You are role-playing as a primitive villager in a small ancient community. "
            "Respond in 1-2 short sentences describing what you do today. "
            "Be creative and varied: gather food, explore, craft tools, talk to neighbors, "
            "observe nature, tell stories, etc. Do NOT always say the same thing."
        )
        full_prompt = f"{system_prompt}\n\nScenario: {prompt}\nYour action:"
        result = self._call_ollama(self.fast_model, full_prompt, temperature=0.9)
        return result

    def reflect_and_hallucinate(self, memories: list, entropy_factor: float) -> str:
        """
        Used for deep reflections at the end of the day.
        Uses gemma2:9b for richer, more creative output.
        Injects entropy to create myths and legends.
        """
        # Build a memory summary from the list
        memory_texts = []
        for m in memories:
            if hasattr(m, 'content'):
                memory_texts.append(m.content)
            elif isinstance(m, str):
                memory_texts.append(m)

        memory_summary = "; ".join(memory_texts[-5:]) if memory_texts else "Nothing notable happened."

        if random.random() < entropy_factor:
            # HALLUCINATION MODE: Exaggerate and mythologize
            system_prompt = (
                "You are the collective unconscious memory of an ancient village. "
                "Take the following mundane events and transform them into a dramatic myth or legend. "
                "Exaggerate wildly. Introduce gods, spirits, or supernatural forces. "
                "Write 2-3 sentences of the legend."
            )
        else:
            # FACTUAL MODE: Summarize plainly
            system_prompt = (
                "You are a village elder summarizing what happened today. "
                "Write a short, factual 1-2 sentence summary of the day's events."
            )

        full_prompt = f"{system_prompt}\n\nToday's events: {memory_summary}\nYour reflection:"
        result = self._call_ollama(self.smart_model, full_prompt, temperature=1.1)
        return result

    def extract_vector(self, text: str) -> list[float]:
        """
        Embed the text using Ollama's embedding model for ChromaDB / 3D visualization.
        Returns an embedding vector (truncated to 3D for visualization fallback).
        """
        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={
                    "model": self.embed_model,
                    "prompt": text,
                },
                timeout=30
            )
            resp.raise_for_status()
            embedding = resp.json().get("embedding", [])
            if len(embedding) >= 3:
                return embedding[:3]  # First 3 dims for quick 3D preview
            return [random.uniform(-1, 1) for _ in range(3)]
        except Exception as e:
            print(f"[LLMRouter] Embedding failed: {e}")
            return [random.uniform(-1, 1) for _ in range(3)]
