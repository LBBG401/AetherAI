from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog, Footer, Header, Static
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
from textual.reactive import reactive
from textual import work
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.text import Text
import os, subprocess, threading

# ─────────────────────────────────────────
#  CHARGEMENT CONFIG
# ─────────────────────────────────────────
from first_run import get_or_setup
_config = get_or_setup()

API_KEY          = _config.get("groq_key", "")
POLLINATIONS_KEY = _config.get("pollinations_key", "")
SEEDANCE_KEY     = _config.get("seedance_api_key", "")

from groq import Groq
from detect import get_config
from memory import load_memory, add_memory, format_for_prompt, clear_memory
from cowork import read_file, read_folder, format_file_for_prompt, format_folder_for_prompt, write_file
from imagine import generate_image, open_image
import imagine as _imagine_module
_imagine_module.POLLINATIONS_API_KEY = POLLINATIONS_KEY
from imagine_video import generate_video, open_file as open_video_file
import imagine_video as _video_module
_video_module.SEEDANCE_API_KEY = SEEDANCE_KEY
from setup_local import setup_ollama, ollama_running

OS_CONFIG      = get_config()
memories       = load_memory()
cowork_context = ""
current_mode   = "cloud"

MODEL_CLOUD = "llama-3.3-70b-versatile"
MODEL_LOCAL = "tinyllama"
OLLAMA_URL  = "http://localhost:11434/api/chat"

client  = Groq(api_key=API_KEY) if API_KEY else None
history = []

def build_system_prompt():
    mem = format_for_prompt(memories)
    cw  = f"\n\nCONTEXTE COWORK :\n{cowork_context}" if cowork_context else ""
    return (
        "Tu es AetherAI, l'assistant IA personnel de ton utilisateur.\n"
        "Tu parles comme un pote proche : detendu, direct, sans bullshit.\n"
        "Tu peux coder dans tous les langages, executer des commandes, generer des images/videos.\n\n"
        + OS_CONFIG['prompt'] + "\n\n"
        "- Pour executer une commande : [CMD] commande\n"
        "- Pour generer une image : [IMG] description en anglais\n"
        "- Pour generer une video : [VID] description en anglais\n"
        "- Si l'utilisateur demande une video, utilise TOUJOURS [VID]\n"
        "- Commandes disponibles : " + str(OS_CONFIG['commands']) + "\n"
        "- Commandes INTERDITES : " + str(OS_CONFIG['forbidden']) + "\n\n"
        + mem + cw
    )

def reset_history():
    global history
    history = [{"role": "system", "content": build_system_prompt()}]

reset_history()

# ─────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────
CSS = """
Screen {
    background: #0a0a0f;
    layout: vertical;
}

#chat-log {
    background: #0a0a0f;
    border: none;
    padding: 0 1;
    height: 1fr;
    scrollbar-color: #2a2a3a #0a0a0f;
}

#input-area {
    height: auto;
    background: #111118;
    border-top: solid #2a2a3a;
    padding: 0;
}

#mode-bar {
    height: 1;
    background: #111118;
    color: #8888aa;
    padding: 0 2;
    border-bottom: solid #2a2a3a;
}

#user-input {
    background: #1a1a24;
    border: solid #2a2a3a;
    color: #e8e8f0;
    padding: 0 1;
    margin: 1 1 0 1;
    height: 3;
}

#user-input:focus {
    border: solid #7c6aff;
}

#bottom-rule {
    height: 1;
    background: #111118;
    color: #2a2a3a;
    padding: 0 2;
}

#status-bar {
    height: 1;
    background: #0f0f1a;
    color: #555577;
    padding: 0 2;
    dock: bottom;
}
"""

# ─────────────────────────────────────────
#  APP
# ─────────────────────────────────────────
class AetherTUI(App):
    CSS = CSS
    TITLE = "AetherAI"

    BINDINGS = [
        Binding("escape", "cancel", "Annuler", show=True),
        Binding("ctrl+c", "quit", "Quitter", show=True),
        Binding("ctrl+l", "clear_log", "Effacer", show=True),
        Binding("ctrl+r", "reset_session", "Reset session", show=True),
    ]

    thinking = reactive(False)
    status_text = reactive("pret")

    def compose(self) -> ComposeResult:
        yield RichLog(id="chat-log", highlight=True, markup=True, wrap=True)
        yield Vertical(
            Static(self._mode_bar_text(), id="mode-bar"),
            Input(placeholder="Message AetherAI... (Entree pour envoyer)", id="user-input"),
            Static("─" * 200, id="bottom-rule"),
            id="input-area"
        )
        yield Static(self._status_text(), id="status-bar")

    def _mode_bar_text(self) -> str:
        mode_color = "cyan" if current_mode == "local" else "magenta"
        return f"[{mode_color}]{current_mode.upper()}[/{mode_color}]  OS: {OS_CONFIG['os']}  Souvenirs: {len(memories)}  [dim]Ctrl+C quitter · Esc annuler · Ctrl+L effacer · Ctrl+R reset[/dim]"

    def _status_text(self) -> str:
        if self.thinking:
            return " ⟳ AetherAI reflechit..."
        return f" ✓ {self.status_text}"

    def on_mount(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        log.write(Text.from_markup(
            f"\n[bold magenta]AetherAI[/bold magenta] — Ton assistant IA\n"
            f"[dim]Mode: {current_mode} · OS: {OS_CONFIG['os']} · Souvenirs: {len(memories)}[/dim]\n"
            f"[dim]Tape /help pour les commandes[/dim]\n"
        ))
        self.query_one("#user-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        self.query_one("#user-input", Input).value = ""

        log = self.query_one("#chat-log", RichLog)
        log.write(Text.from_markup(f"\n[bold white]Toi →[/bold white] {text}"))

        if self._handle_special(text, log):
            return

        if not self.thinking:
            self.thinking = True
            self._update_status("reflechit...")
            self._ask_async(text, log)

    def _update_status(self, text: str):
        self.status_text = text
        try:
            self.query_one("#status-bar", Static).update(self._status_text())
        except:
            pass

    def _update_mode_bar(self):
        try:
            self.query_one("#mode-bar", Static).update(self._mode_bar_text())
        except:
            pass

    def action_cancel(self) -> None:
        if self.thinking:
            self.thinking = False
            self._update_status("annule")
            log = self.query_one("#chat-log", RichLog)
            log.write(Text.from_markup("[dim]Generation annulee.[/dim]"))

    def action_clear_log(self) -> None:
        self.query_one("#chat-log", RichLog).clear()

    def action_reset_session(self) -> None:
        reset_history()
        log = self.query_one("#chat-log", RichLog)
        log.write(Text.from_markup("[bold yellow]Session reinitalisee.[/bold yellow]"))

    # ─────────────────────────────────────
    #  COMMANDES SPECIALES
    # ─────────────────────────────────────
    def _handle_special(self, text: str, log: RichLog) -> bool:
        global cowork_context, current_mode, memories

        cmd = text.strip().lower()
        raw = text.strip()

        if cmd == "/help":
            log.write(Text.from_markup(
                "\n[bold magenta]Commandes :[/bold magenta]\n"
                "  [cyan]/help[/cyan]                 → affiche cette aide\n"
                "  [cyan]/reset[/cyan]                → efface la session\n"
                "  [cyan]/memory[/cyan]               → derniers souvenirs\n"
                "  [cyan]/mode local[/cyan]           → bascule sur Ollama\n"
                "  [cyan]/mode cloud[/cyan]           → bascule sur Groq\n"
                "  [cyan]/run <cmd>[/cyan]            → execute une commande\n"
                "  [cyan]/imagine <desc>[/cyan]       → genere une image\n"
                "  [cyan]/video <desc>[/cyan]         → genere une video\n"
                "  [cyan]/load <fichier>[/cyan]       → cowork fichier\n"
                "  [cyan]/load folder <dir>[/cyan]    → cowork dossier\n"
                "  [cyan]/save <fichier>[/cyan]       → sauvegarde dernier code\n"
                "  [cyan]/cowork[/cyan]               → etat cowork\n"
                "  [cyan]/cowork stop[/cyan]          → desactive cowork\n"
                "  [cyan]Ctrl+C[/cyan]                → quitte\n"
                "  [cyan]Esc[/cyan]                   → annule la generation\n"
            ))
            return True

        if cmd == "/reset":
            reset_history()
            log.write(Text.from_markup("[bold yellow]Session reinitalisee.[/bold yellow]"))
            return True

        if cmd == "/memory":
            if not memories:
                log.write(Text.from_markup("[dim]Aucun souvenir.[/dim]"))
            else:
                lines = "\n".join([f"[{m['date']}] {m['role'].upper()} : {m['content'][:80]}..." for m in memories[-5:]])
                log.write(Text.from_markup(f"[bold magenta]Souvenirs :[/bold magenta]\n{lines}"))
            return True

        if cmd == "/cowork stop":
            cowork_context = ""
            log.write(Text.from_markup("[bold yellow]Cowork desactive.[/bold yellow]"))
            return True

        if cmd == "/cowork":
            status = "[green]actif[/green]" if cowork_context else "[red]inactif[/red]"
            log.write(Text.from_markup(f"[bold]Cowork :[/bold] {status}"))
            return True

        if cmd.startswith("/mode "):
            mode = cmd[6:].strip()
            if mode == "local":
                log.write(Text.from_markup("[cyan]Configuration mode local...[/cyan]"))
                ok = setup_ollama(model="tinyllama", silent=False)
                if ok:
                    current_mode = "local"
                    log.write(Text.from_markup("[bold cyan]Mode LOCAL active[/bold cyan] — tinyllama."))
                else:
                    log.write(Text.from_markup("[bold red]Mode local indisponible.[/bold red]"))
                self._update_mode_bar()
            elif mode == "cloud":
                current_mode = "cloud"
                log.write(Text.from_markup("[bold magenta]Mode CLOUD active[/bold magenta] — Groq API."))
                self._update_mode_bar()
            return True

        if raw.lower().startswith("/run "):
            cmd_to_run = raw[5:].strip()
            log.write(Text.from_markup(f"[bold yellow]Execution :[/bold yellow] {cmd_to_run}"))
            output = self._run_cmd(cmd_to_run)
            log.write(Syntax(output, "bash", theme="monokai", word_wrap=True))
            return True

        if raw.lower().startswith("/imagine "):
            prompt = raw[9:].strip()
            log.write(Text.from_markup(f"[bold magenta]Generation image :[/bold magenta] {prompt}"))
            self.thinking = True
            self._update_status("generation image...")
            self._generate_image_async(prompt, log)
            return True

        if raw.lower().startswith("/video "):
            prompt = raw[7:].strip()
            log.write(Text.from_markup(f"[bold magenta]Generation video :[/bold magenta] {prompt}"))
            log.write(Text.from_markup("[dim]Patience, peut prendre 1-2 minutes...[/dim]"))
            self.thinking = True
            self._update_status("generation video...")
            self._generate_video_async(prompt, log)
            return True

        if raw.lower().startswith("/load folder "):
            path = raw[13:].strip().strip('"')
            ok, files = read_folder(path)
            if ok and files:
                cowork_context = format_folder_for_prompt(files)
                log.write(Text.from_markup(f"[bold green]Dossier charge :[/bold green] {len(files)} fichier(s)"))
            else:
                log.write(Text.from_markup(f"[bold red]Dossier introuvable : {path}[/bold red]"))
            return True

        if raw.lower().startswith("/load "):
            path = raw[6:].strip().strip('"')
            ok, content = read_file(path)
            if ok:
                cowork_context = format_file_for_prompt(path, content)
                log.write(Text.from_markup(f"[bold green]Fichier charge :[/bold green] {path}"))
            else:
                log.write(Text.from_markup(f"[bold red]{content}[/bold red]"))
            return True

        if raw.lower().startswith("/save "):
            path = raw[6:].strip().strip('"')
            last_code = ""
            for msg in reversed(history):
                if msg["role"] == "assistant" and "```" in msg["content"]:
                    in_block = False; code_lines = []
                    for line in msg["content"].split("\n"):
                        if line.startswith("```") and not in_block: in_block = True; continue
                        elif line.startswith("```") and in_block: break
                        elif in_block: code_lines.append(line)
                    last_code = "\n".join(code_lines); break
            if last_code:
                ok, msg = write_file(path, last_code)
                log.write(Text.from_markup(f"[bold green]{msg}[/bold green]" if ok else f"[bold red]{msg}[/bold red]"))
            else:
                log.write(Text.from_markup("[yellow]Aucun code trouve.[/yellow]"))
            return True

        return False

    def _run_cmd(self, cmd: str) -> str:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True,
                text=True, timeout=30,
                encoding="utf-8", errors="replace"
            )
            return (result.stdout or result.stderr or "(aucune sortie)").strip()
        except Exception as e:
            return f"Erreur : {e}"

    # ─────────────────────────────────────
    #  ASYNC IA
    # ─────────────────────────────────────
    @work(thread=True)
    def _ask_async(self, user_input: str, log: RichLog):
        global memories
        try:
            history.append({"role": "user", "content": user_input})

            if current_mode == "local":
                import urllib.request, json as _json
                payload = _json.dumps({"model": MODEL_LOCAL, "messages": history, "stream": False}).encode("utf-8")
                req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=120) as r:
                    data = _json.loads(r.read())
                reply = data["message"]["content"]
            else:
                if client is None:
                    raise Exception("Cle Groq manquante.")
                response = client.chat.completions.create(
                    model=MODEL_CLOUD, messages=history,
                    temperature=0.7, max_tokens=2048,
                )
                reply = response.choices[0].message.content

            history.append({"role": "assistant", "content": reply})
            memories = add_memory(memories, "user", user_input)
            memories = add_memory(memories, "aether", reply)

            if not self.thinking:
                return

            self.call_from_thread(self._display_reply, reply, log)

        except Exception as e:
            self.call_from_thread(log.write, Text.from_markup(f"[bold red]Erreur :[/bold red] {e}"))
        finally:
            self.call_from_thread(self._set_thinking, False)
            self.call_from_thread(self._update_status, "pret")

    @work(thread=True)
    def _generate_image_async(self, prompt: str, log: RichLog):
        try:
            ok, result = generate_image(prompt)
            if ok:
                self.call_from_thread(log.write, Text.from_markup(f"[bold green]Image sauvee :[/bold green] {result}"))
                open_image(result)
            else:
                self.call_from_thread(log.write, Text.from_markup(f"[bold red]Erreur image :[/bold red] {result}"))
        finally:
            self.call_from_thread(self._set_thinking, False)
            self.call_from_thread(self._update_status, "pret")

    @work(thread=True)
    def _generate_video_async(self, prompt: str, log: RichLog):
        try:
            ok, result = generate_video(prompt)
            if ok:
                self.call_from_thread(log.write, Text.from_markup(f"[bold green]Video sauvee :[/bold green] {result}"))
                open_video_file(result)
            else:
                self.call_from_thread(log.write, Text.from_markup(f"[bold red]Erreur video :[/bold red] {result}"))
        finally:
            self.call_from_thread(self._set_thinking, False)
            self.call_from_thread(self._update_status, "pret")

    def _set_thinking(self, value: bool):
        self.thinking = value
        self.query_one("#status-bar", Static).update(self._status_text())

    def _display_reply(self, reply: str, log: RichLog):
        log.write(Text.from_markup("\n[bold magenta]AetherAI →[/bold magenta]"))
        lines = reply.split("\n")
        clean_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if stripped.startswith("[CMD]"):
                cmd = stripped[5:].strip()
                log.write(Text.from_markup(f"[bold yellow]Execution :[/bold yellow] {cmd}"))
                output = self._run_cmd(cmd)
                log.write(Syntax(output, "bash", theme="monokai", word_wrap=True))
                i += 1
                continue

            if stripped.startswith("[IMG]"):
                prompt = stripped[5:].strip()
                log.write(Text.from_markup(f"[bold magenta]Generation image :[/bold magenta] {prompt}"))
                ok, result = generate_image(prompt)
                if ok:
                    log.write(Text.from_markup(f"[bold green]Image :[/bold green] {result}"))
                    open_image(result)
                else:
                    log.write(Text.from_markup(f"[bold red]Erreur :[/bold red] {result}"))
                i += 1
                continue

            if stripped.startswith("[VID]"):
                prompt = stripped[5:].strip()
                log.write(Text.from_markup(f"[bold magenta]Generation video :[/bold magenta] {prompt}"))
                ok, result = generate_video(prompt)
                if ok:
                    log.write(Text.from_markup(f"[bold green]Video :[/bold green] {result}"))
                    open_video_file(result)
                else:
                    log.write(Text.from_markup(f"[bold red]Erreur :[/bold red] {result}"))
                i += 1
                continue

            # Detecte bloc de code ```
            if stripped.startswith("```"):
                lang = stripped[3:].strip() or "text"
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])
                    i += 1
                code = "\n".join(code_lines)
                log.write(Syntax(code, lang, theme="monokai", word_wrap=True, line_numbers=False))
                i += 1
                continue

            clean_lines.append(line)
            i += 1

        clean_text = "\n".join(clean_lines).strip()
        if clean_text:
            log.write(Markdown(clean_text))
        log.write(Text(""))

# ─────────────────────────────────────────
#  LANCEMENT
# ─────────────────────────────────────────
if __name__ == "__main__":
    app = AetherTUI()
    app.run()
