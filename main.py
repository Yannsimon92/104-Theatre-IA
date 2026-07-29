"""
Orchestrateur du dialogue théâtral entre deux personnages joués par deux
agents IA différents (ex: Claude pour Philippe, GLM-5.2 pour Noa).

Usage :
    python main.py
"""

import yaml
from datetime import datetime
from pathlib import Path

from agents import ENGINES

ROOT = Path(__file__).parent


def load_yaml(path):
    with open(ROOT / path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_personnages(config):
    personnages = {}
    for p in config["personnages"]:
        data = load_yaml(p["fichier"])
        personnages[p["id"]] = data
    return personnages


def ivresse_pour_tour(tour_index, total_turns, config):
    """Calcule le niveau d'ivresse (0-10) en fonction de l'avancement de la scène."""
    debut = config["ivresse"]["debut"]
    fin = config["ivresse"]["fin"]
    seuil = config["ivresse"].get("seuil_bascule", 0)

    if tour_index < seuil:
        # progression lente au début
        progression = (tour_index / max(seuil, 1)) * 0.4
    else:
        # accélération après le seuil de bascule
        progression = 0.4 + ((tour_index - seuil) / max(total_turns - seuil, 1)) * 0.6

    progression = min(max(progression, 0), 1)
    return round(debut + progression * (fin - debut), 1)


def render_history(history):
    """Transforme l'historique en texte brut 'NOM: réplique' pour le contexte des agents."""
    lignes = []
    for tour in history:
        lignes.append(f"{tour['nom_affiche']}: {tour['texte']}")
    return "\n".join(lignes) if lignes else "(La scène commence. Aucune réplique n'a encore été prononcée.)"


def jouer_scene(config, personnages):
    ordre_ids = list(personnages.keys())
    premier = config.get("premier_a_parler")
    if premier in ordre_ids:
        ordre_ids.remove(premier)
        ordre_ids.insert(0, premier)

    max_turns = config["max_turns"]
    history = []

    print(f"\n--- {config['scene']['lieu']} — {config['scene']['moment']} ---\n")

    for tour_index in range(max_turns):
        perso_id = ordre_ids[tour_index % len(ordre_ids)]
        perso = personnages[perso_id]

        ivresse = ivresse_pour_tour(tour_index, max_turns, config)
        system_prompt = perso["system_prompt"].format(ivresse=ivresse)

        # Contexte de scène injecté une seule fois en tête du system prompt
        contexte_scene = (
            f"CONTEXTE DE LA SCÈNE :\n"
            f"Lieu : {config['scene']['lieu']}\n"
            f"Moment : {config['scene']['moment']}\n"
            f"{config['scene']['contexte']}\n\n"
        )
        system_prompt_final = contexte_scene + system_prompt

        history_text = render_history(history)

        call_fn = ENGINES[perso["moteur"]]
        replique = call_fn(
            system_prompt=system_prompt_final,
            history_text=history_text,
            temperature=perso.get("temperature", 0.9),
        )

        history.append({"nom_affiche": perso["nom_affiche"], "texte": replique})

        print(f"[{perso['nom_affiche']}] (ivresse {ivresse}/10)")
        print(replique)
        print()

    return history


def sauvegarder_scene(history, config):
    dossier = ROOT / config["output"]["dossier"]
    dossier.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fichier = dossier / f"scene_{timestamp}.md"

    with open(fichier, "w", encoding="utf-8") as f:
        f.write(f"# {config['scene']['lieu']}\n\n")
        f.write(f"*{config['scene']['moment']}*\n\n")
        f.write("---\n\n")
        for tour in history:
            f.write(f"**{tour['nom_affiche']}** — {tour['texte']}\n\n")

    print(f"\nScène sauvegardée dans : {fichier}")


def main():
    config = load_yaml("config.yaml")
    personnages = load_personnages(config)
    history = jouer_scene(config, personnages)
    sauvegarder_scene(history, config)


if __name__ == "__main__":
    main()
