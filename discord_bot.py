import discord
import os
import sys
import subprocess
from groq import Groq

# ─────────────────────────────────────────
#  CHARGEMENT CONFIG
# ─────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from first_run import get_or_setup
_config = get_or_setup()

DISCORD_TOKEN = _config.get("discord_token", "")
API_KEY       = _config.get("groq_key", "")
MODEL         = "llama-3.3-70b-versatile"
OWNER_ID      = 1327680696034132110

BLOCKED_COMMANDS = [
    "format", "rm -rf", "del /f /s", "rmdir /s",
    "shutdown", "reg delete", "bcdedit", "diskpart",
    "net user", "takeown"
]

# ─────────────────────────────────────────
#  MODULES
# ─────────────────────────────────────────
from memory import load_memory, add_memory, format_for_prompt
from detect import get_config

memories  = load_memory()
OS_CONFIG = get_config()

def build_system_prompt():
    return (
        "Tu es AetherAI, l'assistant IA personnel de ton utilisateur.\n"
        "Tu parles comme un pote proche : detendu, direct, sans bullshit.\n"
        "Reponds sur Discord : concis, blocs de code ```langage```.\n\n"
        + OS_CONFIG['prompt'] + "\n\n"
        "Pour executer une commande : [CMD] commande\n"
        "Commandes INTERDITES : " + str(OS_CONFIG['forbidden']) + "\n\n"
        + format_for_prompt(memories)
    )

# ─────────────────────────────────────────
#  INIT
# ─────────────────────────────────────────
client_groq       = Groq(api_key=API_KEY) if API_KEY else None
channel_histories = {}

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def is_owner(message):
    return message.author.id == OWNER_ID

# ─────────────────────────────────────────
#  COMMANDES SYSTEME
# ─────────────────────────────────────────
def run_command(cmd: str) -> str:
    cmd_lower = cmd.strip().lower()
    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            return f"Commande bloquee : `{blocked}`"
    for forbidden in OS_CONFIG["forbidden"]:
        if cmd_lower.startswith(forbidden):
            return f"Commande `{forbidden}` interdite sur {OS_CONFIG['os']}."
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True,
            text=True, timeout=30,
            encoding="utf-8", errors="replace", cwd=os.getcwd()
        )
        output = result.stdout or result.stderr or "(aucune sortie)"
        return output.strip()[:1800]
    except subprocess.TimeoutExpired:
        return "Timeout 30s"
    except Exception as e:
        return f"Erreur : {e}"

# ─────────────────────────────────────────
#  APPEL GROQ
# ─────────────────────────────────────────
def ask_aether(channel_id: int, user_input: str) -> str:
    global memories
    if client_groq is None:
        return "Cle Groq manquante."
    if channel_id not in channel_histories:
        channel_histories[channel_id] = [{"role": "system", "content": build_system_prompt()}]
    hist = channel_histories[channel_id]
    hist.append({"role": "user", "content": user_input})
    response = client_groq.chat.completions.create(
        model=MODEL, messages=hist,
        temperature=0.7, max_tokens=1024,
    )
    reply = response.choices[0].message.content
    hist.append({"role": "assistant", "content": reply})
    memories = add_memory(memories, "user", f"[Discord] {user_input}")
    memories = add_memory(memories, "aether", reply)
    return reply

# ─────────────────────────────────────────
#  ENVOI REPONSE IA (avec [CMD])
# ─────────────────────────────────────────
async def send_ai_reply(channel, reply: str):
    lines = reply.split("\n")
    clean_lines = []
    for line in lines:
        if line.strip().startswith("[CMD]"):
            cmd = line.strip()[5:].strip()
            output = run_command(cmd)
            clean_lines.append(f"⚡ **`{cmd}`**")
            clean_lines.append(f"```\n{output[:1000]}\n```")
        else:
            clean_lines.append(line)
    final = "\n".join(clean_lines).strip()
    while len(final) > 1900:
        split_at = final.rfind("\n", 0, 1900)
        if split_at == -1: split_at = 1900
        await channel.send(final[:split_at])
        final = final[split_at:].strip()
    if final:
        await channel.send(final)

# ─────────────────────────────────────────
#  ÉVÉNEMENTS
# ─────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"AetherAI Discord connecte : {bot.user}")
    try:
        owner = await bot.fetch_user(OWNER_ID)
        await owner.send("AetherAI Discord is online !")
    except Exception as e:
        print(f"MP demarrage impossible : {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if not is_owner(message):
        if isinstance(message.channel, discord.DMChannel):
            await message.channel.send("Acces refuse.")
        return
    if not isinstance(message.channel, discord.DMChannel):
        return

    content = message.content.strip()

    if content.lower().startswith("run "):
        cmd = content[4:].strip()
        async with message.channel.typing():
            output = run_command(cmd)
            await message.channel.send(f"**`{cmd}`**\n```\n{output}\n```")
        return

    if content == "!help":
        await message.channel.send(
            "**AetherAI — Commandes MP**\n\n"
            "`run <commande>` → execute sur ton PC\n"
            "`!ask <question>` → pose une question\n"
            "`!reset` → efface la session\n"
            "`!memory` → souvenirs\n"
            "`!os` → infos systeme\n"
            "`!ping` → test connexion"
        )
        return
    if content == "!ping":
        await message.channel.send("En ligne !")
        return
    if content == "!os":
        await message.channel.send(f"**{OS_CONFIG['os']}** | **{OS_CONFIG['shell']}**")
        return
    if content == "!reset":
        channel_histories.pop(message.channel.id, None)
        await message.channel.send("Session effacee.")
        return
    if content == "!memory":
        if not memories:
            await message.channel.send("Aucun souvenir.")
        else:
            lines = "\n".join([f"[{m['date']}] {m['role'].upper()} : {m['content'][:80]}..." for m in memories[-5:]])
            await message.channel.send(f"```\n{lines}\n```")
        return

    user_input = content[5:].strip() if content.startswith("!ask ") else content
    if not user_input:
        return

    async with message.channel.typing():
        try:
            reply = ask_aether(message.channel.id, user_input)
            await send_ai_reply(message.channel, reply)
        except Exception as e:
            await message.channel.send(f"Erreur : {e}")

# ─────────────────────────────────────────
#  LANCEMENT
# ─────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Token Discord manquant. Lance 'python first_run.py'.")
    else:
        print("Demarrage AetherAI Discord...")
        bot.run(DISCORD_TOKEN)
