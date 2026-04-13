import json
import os
from datetime import datetime

MEMORY_FILE = "aether_memory.json"
MAX_MEMORIES = 100

def load_memory() -> list:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_memory(memories: list):
    # Garde seulement les MAX_MEMORIES derniers
    if len(memories) > MAX_MEMORIES:
        memories = memories[-MAX_MEMORIES:]
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memories, f, indent=2, ensure_ascii=False)

def add_memory(memories: list, role: str, content: str) -> list:
    memories.append({
        "role": role,
        "content": content,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    save_memory(memories)
    return memories

def format_for_prompt(memories: list) -> str:
    """Formate les souvenirs pour les injecter dans le prompt système."""
    if not memories:
        return ""
    lines = ["Voici un résumé des conversations précédentes avec l'utilisateur :"]
    for m in memories[-10:]:  # injecte seulement les 10 derniers pour pas surcharger
        lines.append(f"[{m['date']}] {m['role'].upper()} : {m['content'][:200]}")
    return "\n".join(lines)

def clear_memory():
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)

if __name__ == "__main__":
    print("✅ Module mémoire OK")
    print(f"   Fichier : {MEMORY_FILE}")
    mems = load_memory()
    print(f"   Souvenirs en mémoire : {len(mems)}")
