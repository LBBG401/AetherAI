import os

SUPPORTED_EXTENSIONS = [
    ".py", ".js", ".ts", ".html", ".css", ".json",
    ".md", ".txt", ".sh", ".bat", ".c", ".cpp",
    ".java", ".go", ".rs", ".php", ".yaml", ".yml",
    ".toml", ".env", ".sql"
]

MAX_FILE_SIZE_KB = 100  # refuse les fichiers trop lourds

# ─────────────────────────────────────────
#  LECTURE DE FICHIER
# ─────────────────────────────────────────
def read_file(path: str) -> tuple[bool, str]:
    """
    Retourne (succès, contenu ou message d'erreur)
    """
    if not os.path.exists(path):
        return False, f"❌ Fichier introuvable : {path}"

    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"❌ Extension non supportée : {ext}\nSupportées : {', '.join(SUPPORTED_EXTENSIONS)}"

    size_kb = os.path.getsize(path) / 1024
    if size_kb > MAX_FILE_SIZE_KB:
        return False, f"❌ Fichier trop lourd ({size_kb:.1f} Ko). Maximum : {MAX_FILE_SIZE_KB} Ko"

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return True, content
    except Exception as e:
        return False, f"❌ Erreur de lecture : {e}"

# ─────────────────────────────────────────
#  LECTURE DE DOSSIER
# ─────────────────────────────────────────
def read_folder(path: str, max_files: int = 10) -> tuple[bool, dict]:
    """
    Lit tous les fichiers supportés d'un dossier.
    Retourne (succès, {nom_fichier: contenu})
    """
    if not os.path.isdir(path):
        return False, {}

    files = {}
    count = 0
    for root, dirs, filenames in os.walk(path):
        # Ignore les dossiers inutiles
        dirs[:] = [d for d in dirs if d not in ("venv", ".git", "node_modules", "__pycache__")]
        for filename in filenames:
            if count >= max_files:
                break
            ext = os.path.splitext(filename)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                full_path = os.path.join(root, filename)
                ok, content = read_file(full_path)
                if ok:
                    rel_path = os.path.relpath(full_path, path)
                    files[rel_path] = content
                    count += 1

    return True, files

# ─────────────────────────────────────────
#  FORMATTAGE POUR LE PROMPT
# ─────────────────────────────────────────
def format_file_for_prompt(path: str, content: str) -> str:
    ext = os.path.splitext(path)[1].lstrip(".")
    return f"Fichier : {path}\n```{ext}\n{content}\n```"

def format_folder_for_prompt(files: dict) -> str:
    parts = []
    for path, content in files.items():
        parts.append(format_file_for_prompt(path, content))
    return "\n\n".join(parts)

# ─────────────────────────────────────────
#  ÉCRITURE DE FICHIER (appliquer les modifs)
# ─────────────────────────────────────────
def write_file(path: str, content: str) -> tuple[bool, str]:
    try:
        # Crée les dossiers parents si besoin
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, f"✅ Fichier sauvegardé : {path}"
    except Exception as e:
        return False, f"❌ Erreur d'écriture : {e}"

if __name__ == "__main__":
    print("✅ Module cowork OK")
    print(f"   Extensions supportées : {', '.join(SUPPORTED_EXTENSIONS)}")
