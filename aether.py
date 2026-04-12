import os
import requests
import subprocess
from groq import Groq
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import prompt as pt_prompt

# ─────────────────────────────────────────
#  CHARGEMENT CONFIG
# ─────────────────────────────────────────
from first_run import get_or_setup, get_user_setting
_config = get_or_setup()

API_KEY          = _config.get("groq_key", "")
POLLINATIONS_KEY = _config.get("pollinations_key", "")
SEEDANCE_KEY     = _config.get("seedance_api_key", "")
HEYGEN_KEY       = _config.get("heygen_api_key", "")
DISCORD_TOKEN    = _config.get("discord_token", "")

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
MODEL_CLOUD  = "llama-3.3-70b-versatile"
MODEL_LOCAL  = "tinyllama"
OLLAMA_URL   = "http://localhost:11434/api/chat"
current_mode = "cloud"

# ─────────────────────────────────────────
#  MODULES
# ─────────────────────────────────────────
from detect import get_config
from memory import load_memory, add_memory, format_for_prompt, clear_memory
from cowork import read_file, read_folder, format_file_for_prompt, format_folder_for_prompt, write_file
from imagine import generate_image, open_image
import imagine as _imagine_module
_imagine_module.POLLINATIONS_API_KEY = POLLINATIONS_KEY
from imagine_video import generate_video, open_file as open_video_file
import imagine_video as _video_module
_video_module.generate_video_heygen = HEYGEN_KEY
from setup_local import setup_ollama, ollama_running

OS_CONFIG      = get_config()
memories       = load_memory()
cowork_context = ""

def build_system_prompt():
    mem_context    = format_for_prompt(memories)
    cowork_section = f"\n\nCONTEXTE COWORK :\n{cowork_context}" if cowork_context else ""
    return (
        "Tu es AetherAI, l'assistant IA personnel de ton utilisateur.\n"
        "Tu parles comme un pote proche : detendu, direct, sans bullshit.\n"
        "Tu peux coder dans tous les langages, expliquer des concepts techniques,\n"
        "executer des commandes systeme, generer des images/videos, et aider a n'importe quel projet.\n\n"
        + OS_CONFIG['prompt'] + "\n\n"
        "Regles :\n"
        "- Parle naturellement, pas comme un robot corporate\n"
        "- Si tu codes, mets toujours le code dans des blocs ```langage\n"
        "- Si tu n'es pas sur de quelque chose, dis-le franchement\n"
        "- Sois efficace : pas de blabla inutile\n"
        "- Pour executer une commande systeme : [CMD] commande\n"
        "- Pour generer une image : [IMG] description en anglais\n"
        "- Pour generer une video : [VID] description en anglais\n"
        "- Si l'utilisateur demande une video, utilise TOUJOURS [VID], jamais [IMG]\n"
        "- Commandes disponibles : " + str(OS_CONFIG['commands']) + "\n"
        "- Commandes INTERDITES  : " + str(OS_CONFIG['forbidden']) + "\n\n"
        + mem_context + cowork_section
    )

# ─────────────────────────────────────────
#  INIT
# ─────────────────────────────────────────
console = Console()
client  = Groq(api_key=API_KEY) if API_KEY else None
history = [{"role": "system", "content": build_system_prompt()}]
session = PromptSession(history=FileHistory(".aether_history"))

def refresh_system_prompt():
    history[0] = {"role": "system", "content": build_system_prompt()}

# ─────────────────────────────────────────
#  CONFIRMATION INLINE
# ─────────────────────────────────────────
def confirm_command(cmd: str) -> bool:
    selected = [0]
    kb = KeyBindings()

    @kb.add("left")
    @kb.add("right")
    def toggle(event):
        selected[0] = 1 - selected[0]

    @kb.add("o")
    @kb.add("O")
    def yes(event): event.app.exit(result=True)

    @kb.add("n")
    @kb.add("N")
    def no(event): event.app.exit(result=False)

    @kb.add("enter")
    def confirm(event): event.app.exit(result=(selected[0] == 0))

    @kb.add("c-c")
    def cancel(event): event.app.exit(result=False)

    def get_prompt():
        oui = "[Oui]" if selected[0] == 0 else " Oui "
        non = "[Non]" if selected[0] == 1 else " Non "
        return HTML(
            f'<ansiyellow>Executer</ansiyellow> <b>{cmd[:60]}</b> ? '
            f'<ansigreen>{oui}</ansigreen> / <ansired>{non}</ansired> '
            f'<ansibrightblack>(fleches ou O/N + Entree)</ansibrightblack> '
        )

    try:
        result = pt_prompt(get_prompt, key_bindings=kb, refresh_interval=0.1)
        return result if isinstance(result, bool) else (selected[0] == 0)
    except (KeyboardInterrupt, EOFError):
        return False

# ─────────────────────────────────────────
#  EXÉCUTION COMMANDES
# ─────────────────────────────────────────
def run_command(cmd: str) -> str:
    for forbidden in OS_CONFIG["forbidden"]:
        if cmd.strip().lower().startswith(forbidden):
            return f"Commande '{forbidden}' interdite sur {OS_CONFIG['os']}."
    if not confirm_command(cmd):
        return "Execution annulee."
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=30,
            encoding="utf-8", errors="replace", cwd=os.getcwd()
        )
        output = result.stdout or result.stderr or "(aucune sortie)"
        return output.strip()
    except subprocess.TimeoutExpired:
        return "Commande trop longue (timeout 30s)"
    except Exception as e:
        return f"Erreur : {e}"

# ─────────────────────────────────────────
#  APPEL GROQ / OLLAMA
# ─────────────────────────────────────────
def ask_aether_cloud(user_input: str) -> str:
    if client is None:
        raise Exception("Cle Groq introuvable. Lance 'python first_run.py'.")
    history.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model=MODEL_CLOUD, messages=history,
        temperature=0.7, max_tokens=2048,
    )
    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})
    return reply

def ask_aether_local(user_input: str) -> str:
    import urllib.request, json as _json
    history.append({"role": "user", "content": user_input})
    payload = _json.dumps({"model": MODEL_LOCAL, "messages": history, "stream": False}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        data = _json.loads(r.read())
    reply = data["message"]["content"]
    history.append({"role": "assistant", "content": reply})
    return reply

def ask_aether(user_input: str) -> str:
    global memories, current_mode
    try:
        reply = ask_aether_local(user_input) if current_mode == "local" else ask_aether_cloud(user_input)
    except Exception as e:
        if current_mode == "local":
            raise Exception(f"Ollama inaccessible. ({e})")
        raise
    memories = add_memory(memories, "user", user_input)
    memories = add_memory(memories, "aether", reply)
    return reply

# ─────────────────────────────────────────
#  AFFICHAGE
# ─────────────────────────────────────────
def display_response(text: str):
    lines = text.split("\n")
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[CMD]"):
            cmd = stripped[5:].strip()
            console.print(f"\n[bold yellow]Execution :[/bold yellow] {cmd}")
            output = run_command(cmd)
            console.print(Panel(output, title="[cyan]Resultat[/cyan]", border_style="cyan", expand=True))
        elif stripped.startswith("[IMG]"):
            prompt = stripped[5:].strip()
            console.print(f"\n[bold magenta]Generation image :[/bold magenta] {prompt}")
            with console.status("[magenta]Generation...[/magenta]"):
                ok, result = generate_image(prompt)
            if ok:
                console.print(f"[bold green]Image sauvee :[/bold green] {result}")
                open_image(result)
            else:
                console.print(f"[bold red]Erreur image :[/bold red] {result}")
        elif stripped.startswith("[VID]"):
            prompt = stripped[5:].strip()
            console.print(f"\n[bold magenta]Generation video :[/bold magenta] {prompt}")
            console.print("[dim]Patience, peut prendre 1-2 minutes...[/dim]")
            with console.status("[magenta]Seedance genere...[/magenta]"):
                ok, result = generate_video(prompt)
            if ok:
                console.print(f"[bold green]Video sauvee :[/bold green] {result}")
                open_video_file(result)
            else:
                console.print(f"[bold red]Erreur video :[/bold red] {result}")
        else:
            clean_lines.append(line)
    clean_text = "\n".join(clean_lines).strip()
    if clean_text:
        console.print(Markdown(clean_text))

# ─────────────────────────────────────────
#  COMMANDES SPECIALES
# ─────────────────────────────────────────
def handle_special(user_input: str) -> bool:
    global cowork_context, current_mode
    cmd = user_input.strip().lower()
    raw = user_input.strip()

    if cmd in ("exit", "quit", "bye", "ciao"):
        console.print("\n[bold magenta]AetherAI :[/bold magenta] A plus !\n")
        return True
    if cmd == "clear":
        console.clear(); return True
    if cmd == "reset":
        history.clear()
        history.append({"role": "system", "content": build_system_prompt()})
        console.print("[bold yellow]Session effacee.[/bold yellow]"); return True
    if cmd == "reset memory":
        clear_memory(); memories.clear(); history.clear()
        history.append({"role": "system", "content": build_system_prompt()})
        console.print("[bold red]Memoire effacee.[/bold red]"); return True
    if cmd == "cowork stop":
        cowork_context = ""; refresh_system_prompt()
        console.print("[bold yellow]Cowork desactive.[/bold yellow]"); return True
    if cmd == "cowork":
        console.print(f"[bold]Cowork :[/bold] {'[green]actif[/green]' if cowork_context else '[red]inactif[/red]'}")
        return True
    if raw.lower().startswith("load ") and not raw.lower().startswith("load folder"):
        path = raw[5:].strip().strip('"')
        with console.status("[magenta]Chargement...[/magenta]"):
            ok, content = read_file(path)
        if ok:
            cowork_context = format_file_for_prompt(path, content)
            refresh_system_prompt()
            console.print(f"[bold green]Fichier charge :[/bold green] {path} ({content.count(chr(10))+1} lignes)")
        else:
            console.print(f"[bold red]{content}[/bold red]")
        return True
    if raw.lower().startswith("load folder "):
        path = raw[12:].strip().strip('"')
        with console.status("[magenta]Chargement...[/magenta]"):
            ok, files = read_folder(path)
        if ok and files:
            cowork_context = format_folder_for_prompt(files); refresh_system_prompt()
            console.print(f"[bold green]Dossier charge :[/bold green] {len(files)} fichier(s)")
            for f in files: console.print(f"   [cyan]->[/cyan] {f}")
        elif ok:
            console.print("[yellow]Aucun fichier supporte.[/yellow]")
        else:
            console.print(f"[bold red]Dossier introuvable : {path}[/bold red]")
        return True
    if raw.lower().startswith("save "):
        path = raw[5:].strip().strip('"')
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
            console.print(f"[bold green]{msg}[/bold green]" if ok else f"[bold red]{msg}[/bold red]")
        else:
            console.print("[yellow]Aucun code trouve.[/yellow]")
        return True
    if raw.lower().startswith("imagine "):
        prompt = raw[8:].strip()
        console.print(f"\n[bold magenta]Generation image :[/bold magenta] {prompt}")
        with console.status("[magenta]Generation...[/magenta]"):
            ok, result = generate_image(prompt)
        console.print(f"[bold green]Image sauvee :[/bold green] {result}" if ok else f"[bold red]Erreur :[/bold red] {result}")
        if ok: open_image(result)
        return True
    if raw.lower().startswith("video "):
        prompt = raw[6:].strip()
        console.print(f"\n[bold magenta]Generation video :[/bold magenta] {prompt}")
        console.print("[dim]Patience...[/dim]")
        with console.status("[magenta]Seedance genere...[/magenta]"):
            ok, result = generate_video(prompt)
        console.print(f"[bold green]Video sauvee :[/bold green] {result}" if ok else f"[bold red]Erreur :[/bold red] {result}")
        if ok: open_video_file(result)
        return True
    if cmd in ("mode local", "mode cloud", "mode"):
        if cmd == "mode local":
            with console.status("[cyan]Verification Ollama...[/cyan]"):
                ok = setup_ollama(model="tinyllama", silent=False)
            if ok:
                current_mode = "local"
                console.print("[bold cyan]Mode LOCAL active[/bold cyan] — tinyllama.")
            else:
                console.print("[bold red]Mode local indisponible.[/bold red]")
        elif cmd == "mode cloud":
            current_mode = "cloud"
            console.print("[bold magenta]Mode CLOUD active[/bold magenta] — Groq API.")
        else:
            icon = "[cyan]LOCAL[/cyan]" if current_mode == "local" else "[magenta]CLOUD[/magenta]"
            console.print(f"[bold]Mode :[/bold] {icon}")
            if current_mode == "local":
                console.print(f"[bold]Ollama :[/bold] {'[green]actif[/green]' if ollama_running() else '[red]inactif[/red]'}")
        return True
    if cmd == "memory":
        if not memories:
            console.print("[dim]Aucun souvenir.[/dim]")
        else:
            lines = "\n".join([f"[{m['date']}] {m['role'].upper()} : {m['content'][:100]}..." for m in memories[-5:]])
            console.print(Panel(lines, title="[magenta]Souvenirs[/magenta]", border_style="magenta", expand=True))
        return True
    if cmd.startswith("run "):
        output = run_command(raw[4:].strip())
        console.print(Panel(output, title="[cyan]Resultat[/cyan]", border_style="cyan", expand=True))
        return True
    if cmd == "help":
        console.print(Panel(
            f"[bold]OS :[/bold] {OS_CONFIG['os']} | [bold]Mode :[/bold] {current_mode} | [bold]Souvenirs :[/bold] {len(memories)}\n\n"
            "[bold]Commandes :[/bold]\n"
            "  [cyan]imagine <desc>[/cyan]        -> genere une image\n"
            "  [cyan]video <desc>[/cyan]          -> genere une video\n"
            "  [cyan]load <fichier>[/cyan]        -> cowork fichier\n"
            "  [cyan]load folder <dir>[/cyan]     -> cowork dossier\n"
            "  [cyan]save <fichier>[/cyan]        -> sauvegarde code\n"
            "  [cyan]run <cmd>[/cyan]             -> execute commande\n"
            "  [cyan]mode local/cloud[/cyan]      -> change le mode IA\n"
            "  [cyan]memory[/cyan]                -> souvenirs\n"
            "  [cyan]reset[/cyan]                 -> efface session\n"
            "  [cyan]reset memory[/cyan]          -> efface memoire\n"
            "  [cyan]clear[/cyan]                 -> nettoie ecran\n"
            "  [cyan]exit[/cyan]                  -> quitte",
            title="[magenta]Aide[/magenta]", border_style="magenta", expand=True
        ))
        return True
    return False

# ─────────────────────────────────────────
#  BOUCLE PRINCIPALE
# ─────────────────────────────────────────
def main():
    console.clear()
    console.print(Panel.fit(
        f"[bold magenta]AetherAI[/bold magenta] — Ton assistant IA\n"
        f"[dim]OS: {OS_CONFIG['os']} | Souvenirs: {len(memories)} | Mode: {current_mode} | [bold]help[/bold][/dim]",
        border_style="magenta"
    ))
    console.print()

    while True:
        try:
            console.print(Rule(style="dim"))
            user_input = session.prompt("> ").strip()
            console.print(Rule(style="dim"))
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold magenta]AetherAI :[/bold magenta] A plus !\n")
            break

        if not user_input:
            continue

        if handle_special(user_input):
            if user_input.strip().lower() in ("exit", "quit", "bye", "ciao"):
                break
            continue

        try:
            with console.status("[magenta]AetherAI reflechit...[/magenta]"):
                reply = ask_aether(user_input)
            console.print(f"\n[bold magenta]AetherAI ->[/bold magenta]")
            display_response(reply)
            console.print()
        except Exception as e:
            console.print(f"[bold red]Erreur :[/bold red] {e}")

if __name__ == "__main__":
    main()
