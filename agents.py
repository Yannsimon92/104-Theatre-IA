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

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")  # clé API GLM (BigModel / Zhipu AI)

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
GLM_MODEL = os.getenv("GLM_MODEL", "glm-5.2")

# Endpoint officiel Zhipu AI (compatible format chat completions)
GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


def call_claude(system_prompt: str, history_text: str, temperature: float = 0.9) -> str:
    """Appelle l'API Anthropic pour générer la prochaine réplique."""
    import anthropic

    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY manquante dans .env")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    user_message = (
        f"Voici le dialogue jusqu'ici :\n\n{history_text}\n\n"
        f"Écris maintenant la prochaine réplique de ton personnage."
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=400,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    return "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()


def call_glm(system_prompt: str, history_text: str, temperature: float = 1.0) -> str:
    """Appelle l'API GLM (Zhipu AI / BigModel) pour générer la prochaine réplique."""
    if not ZHIPU_API_KEY:
        raise RuntimeError("ZHIPU_API_KEY manquante dans .env")

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
