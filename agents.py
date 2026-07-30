"""
Wrappers d'appel aux différentes API de modèles.

Chaque fonction call_xxx(system_prompt, history_text, temperature) -> str
prend :
- system_prompt : le prompt système déjà formaté (avec l'ivresse injectée)
- history_text : l'historique du dialogue tel que ce personnage doit le voir,
  sous forme d'un simple bloc de texte "NOM: réplique" par ligne.
- temperature : température du modèle pour ce personnage

et renvoie la réplique générée (texte brut, sans le nom du personnage devant).
"""

import json
import os
import subprocess
from pathlib import Path

import requests

AUTH_FILE = Path(__file__).parent / "auth.json"


def _opencode_auth_candidates() -> list[Path]:
    """Emplacements possibles de l'auth.json global d'opencode (géré par
    `opencode auth login`). Inclut le home Windows vu depuis WSL (/mnt/c),
    car opencode et son fichier d'auth vivent côté Windows alors que ce
    script peut tourner côté WSL."""
    candidates = [Path.home() / ".local" / "share" / "opencode" / "auth.json"]
    mnt_c_users = Path("/mnt/c/Users")
    if mnt_c_users.exists():
        candidates.extend(mnt_c_users.glob("*/.local/share/opencode/auth.json"))
    return candidates


def _load_key(provider: str, env_var: str) -> str | None:
    """Cherche la clé API dans auth.json, sinon dans les variables d'environnement."""
    if AUTH_FILE.exists():
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            auth = json.load(f)
        entry = auth.get(provider)
        if entry and entry.get("key"):
            return entry["key"]
    return os.getenv(env_var)


def _load_zen_key() -> str | None:
    """Clé du compte OpenCode Zen : auth.json du projet, sinon l'auth.json
    global d'opencode (`opencode-go` / `opencode`), sinon variable d'env."""
    key = _load_key("zen", "OPENCODE_API_KEY")
    if key:
        return key
    for path in _opencode_auth_candidates():
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            auth = json.load(f)
        for provider in ("opencode-go", "opencode"):
            entry = auth.get(provider)
            if entry and entry.get("key"):
                return entry["key"]
    return None


ZEN_API_KEY = _load_zen_key()

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "sonnet")
GLM_MODEL = os.getenv("GLM_MODEL", "glm-5.2")

# Endpoint OpenCode Zen (compatible OpenAI chat completions), facturé sur le
# compte/abonnement opencode plutôt que sur une clé Zhipu séparée.
ZEN_API_URL = "https://opencode.ai/zen/go/v1/chat/completions"


def call_claude(system_prompt: str, history_text: str, temperature: float = 0.9) -> str:
    """Génère la prochaine réplique via le CLI Claude Code en mode headless,
    en utilisant l'abonnement Pro/Max déjà connecté (`claude login`) — pas de
    clé API Anthropic. La température n'est pas réglable dans ce mode."""
    user_message = (
        f"Voici le dialogue jusqu'ici :\n\n{history_text}\n\n"
        f"Écris maintenant la prochaine réplique de ton personnage."
    )

    args = [
        "claude", "-p", user_message,
        "--system-prompt", system_prompt,
        "--model", CLAUDE_MODEL,
        "--tools", "",
        "--no-session-persistence",
        "--output-format", "text",
    ]

    for attempt in range(3):
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=300,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            if attempt == 2:
                raise RuntimeError(f"Échec de l'appel à `claude` : {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            if attempt == 2:
                raise


def call_glm(system_prompt: str, history_text: str, temperature: float = 1.0) -> str:
    """Génère la prochaine réplique via GLM sur la passerelle OpenCode Zen,
    facturée sur le compte/abonnement opencode (pas de clé Zhipu séparée)."""
    if not ZEN_API_KEY:
        raise RuntimeError(
            "Clé OpenCode Zen introuvable (auth.json du projet, auth.json "
            "global d'opencode, ou variable d'environnement OPENCODE_API_KEY) "
            "— lance `opencode auth login`"
        )

    user_message = (
        f"Voici le dialogue jusqu'ici :\n\n{history_text}\n\n"
        f"Écris maintenant la prochaine réplique de ton personnage."
    )

    headers = {
        "Authorization": f"Bearer {ZEN_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GLM_MODEL,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }

    for attempt in range(3):
        try:
            resp = requests.post(ZEN_API_URL, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            break
        except requests.exceptions.RequestException:
            if attempt == 2:
                raise
    data = resp.json()

    return data["choices"][0]["message"]["content"].strip()


# Mapping id moteur -> fonction d'appel
ENGINES = {
    "claude": call_claude,
    "glm": call_glm,
}
