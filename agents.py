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


def _load_key(provider: str, env_var: str) -> str | None:
    """Cherche la clé API dans auth.json, sinon dans les variables d'environnement."""
    if AUTH_FILE.exists():
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            auth = json.load(f)
        entry = auth.get(provider)
        if entry and entry.get("key"):
            return entry["key"]
    return os.getenv(env_var)


ZHIPU_API_KEY = _load_key("glm", "ZHIPU_API_KEY")  # clé API GLM (BigModel / Zhipu AI)

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "sonnet")
GLM_MODEL = os.getenv("GLM_MODEL", "glm-5.2")

# Endpoint officiel Zhipu AI (compatible format chat completions)
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


def call_claude(system_prompt: str, history_text: str, temperature: float = 0.9) -> str:
    """Génère la prochaine réplique via le CLI Claude Code en mode headless,
    en utilisant l'abonnement Pro/Max déjà connecté (`claude login`) — pas de
    clé API Anthropic. La température n'est pas réglable dans ce mode."""
    user_message = (
        f"Voici le dialogue jusqu'ici :\n\n{history_text}\n\n"
        f"Écris maintenant la prochaine réplique de ton personnage."
    )

    result = subprocess.run(
        [
            "claude", "-p", user_message,
            "--system-prompt", system_prompt,
            "--model", CLAUDE_MODEL,
            "--tools", "",
            "--no-session-persistence",
            "--output-format", "text",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Échec de l'appel à `claude` : {result.stderr.strip()}")

    return result.stdout.strip()


def call_glm(system_prompt: str, history_text: str, temperature: float = 1.0) -> str:
    """Appelle l'API GLM (Zhipu AI / BigModel) pour générer la prochaine réplique."""
    if not ZHIPU_API_KEY:
        raise RuntimeError("ZHIPU_API_KEY manquante (auth.json ou variable d'environnement)")

    user_message = (
        f"Voici le dialogue jusqu'ici :\n\n{history_text}\n\n"
        f"Écris maintenant la prochaine réplique de ton personnage."
    )

    headers = {
        "Authorization": f"Bearer {ZHIPU_API_KEY}",
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

    resp = requests.post(GLM_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    return data["choices"][0]["message"]["content"].strip()


# Mapping id moteur -> fonction d'appel
ENGINES = {
    "claude": call_claude,
    "glm": call_glm,
}
