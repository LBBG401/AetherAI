#!/bin/bash
# ─────────────────────────────────────────
#  AetherAI — Script d'installation macOS
# ─────────────────────────────────────────

set -e

INSTALL_DIR="$HOME/AetherAI"
PYTHON_MIN="3.10"

echo ""
echo "=================================================="
echo "  AetherAI — Installation macOS"
echo "=================================================="
echo ""

# 1. Vérifie Python
echo "→ Vérification Python..."
if ! command -v python3 &>/dev/null; then
    echo "  Python3 non trouvé."
    if command -v brew &>/dev/null; then
        echo "  Installation via Homebrew..."
        brew install python3
    else
        echo "  Installe Python depuis https://www.python.org/downloads/"
        exit 1
    fi
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python $PYTHON_VERSION détecté."

# 2. Crée le dossier
echo "→ Création du dossier $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/aether_images"
mkdir -p "$INSTALL_DIR/aether_videos"

# 3. Copie les fichiers Python s'ils sont dans le même dossier
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "→ Copie des fichiers..."
for f in aether.py aether_tui.py first_run.py detect.py memory.py cowork.py \
          imagine.py imagine_video.py setup_local.py discord_bot.py requirements.txt; do
    if [ -f "$SCRIPT_DIR/$f" ]; then
        cp "$SCRIPT_DIR/$f" "$INSTALL_DIR/$f"
        echo "  Copié : $f"
    else
        echo "  Manquant : $f (à placer manuellement dans $INSTALL_DIR)"
    fi
done

# 4. Crée le venv
echo "→ Création de l'environnement virtuel..."
python3 -m venv "$INSTALL_DIR/venv"

# 5. Installe les dépendances
echo "→ Installation des dépendances..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# 6. Crée les launchers dans /usr/local/bin
echo "→ Création des commandes globales..."

cat > /tmp/aether_launch << LAUNCHER
#!/bin/bash
cd "$INSTALL_DIR"
"$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/aether.py"
LAUNCHER

cat > /tmp/aether_tui_launch << LAUNCHER
#!/bin/bash
cd "$INSTALL_DIR"
"$INSTALL_DIR/venv/bin/python" "$INSTALL_DIR/aether_tui.py"
LAUNCHER

chmod +x /tmp/aether_launch /tmp/aether_tui_launch

# Essaie d'installer globalement (peut nécessiter sudo)
if [ -w /usr/local/bin ]; then
    cp /tmp/aether_launch /usr/local/bin/aether
    cp /tmp/aether_tui_launch /usr/local/bin/aether-tui
    echo "  Commandes 'aether' et 'aether-tui' disponibles globalement."
else
    # Installe dans ~/.local/bin
    mkdir -p "$HOME/.local/bin"
    cp /tmp/aether_launch "$HOME/.local/bin/aether"
    cp /tmp/aether_tui_launch "$HOME/.local/bin/aether-tui"
    echo "  Commandes installées dans ~/.local/bin"
    echo "  Ajoute cette ligne à ton ~/.zshrc ou ~/.bashrc :"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
fi

# 7. Ajoute alias au shell
SHELL_RC="$HOME/.zshrc"
if [ ! -f "$SHELL_RC" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if ! grep -q "AetherAI" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# AetherAI" >> "$SHELL_RC"
    echo "alias launch-aether='cd $INSTALL_DIR && $INSTALL_DIR/venv/bin/python $INSTALL_DIR/aether.py'" >> "$SHELL_RC"
    echo "alias launch-aether-tui='cd $INSTALL_DIR && $INSTALL_DIR/venv/bin/python $INSTALL_DIR/aether_tui.py'" >> "$SHELL_RC"
    echo "  Alias ajoutés dans $SHELL_RC"
fi

echo ""
echo "=================================================="
echo "  Installation terminée !"
echo ""
echo "  Commandes disponibles :"
echo "  aether          → terminal classique"
echo "  aether-tui      → interface TUI"
echo "  launch-aether   → alias shell"
echo ""
echo "  Premier lancement : tes clés API seront demandées."
echo "=================================================="
echo ""
