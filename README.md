# Théâtre IA — dialogue Philippe / Noa

Générateur de dialogue théâtral entre deux personnages joués chacun par un
agent IA différent (Claude pour Philippe, GLM-5.2 pour Noa).

Philippe (Claude) est généré via le CLI [Claude Code](https://claude.com/claude-code)
en mode headless (`claude -p`), donc via ton abonnement Pro/Max (`claude login`) —
pas de clé API Anthropic à payer séparément. Noa (GLM) passe par la
passerelle [OpenCode Zen](https://opencode.ai/docs/zen) (plan "Go"), facturée
sur ton compte opencode — pas de clé Zhipu séparée non plus.

## Structure du projet

```
theatre_ia/
├── main.py                # orchestrateur : fait alterner les tours de parole
├── agents.py               # wrappers d'appel aux API (Claude / GLM)
├── config.yaml              # config de la scène (lieu, ivresse, nb de tours...)
├── characters/
│   ├── philippe.yaml        # fiche + system prompt de Philippe
│   └── noa.yaml              # fiche + system prompt de Noa
├── output/                  # scènes générées (créé automatiquement)
├── requirements.txt
└── auth.json.example         # optionnel, voir plus bas
```

## Installation

```bash
cd theatre_ia
python -m venv venv
source venv/bin/activate   # sous Windows : venv\Scripts\activate
pip install -r requirements.txt
claude login                # si ce n'est pas déjà fait (compte Pro/Max)
opencode auth login         # si ce n'est pas déjà fait (compte Zen)
```

`claude` et `opencode` doivent être installés et accessibles dans le PATH.
Ce sont eux qui gèrent l'auth via tes abonnements respectifs — `main.py` ne
s'en occupe pas.

La clé du compte Zen est retrouvée automatiquement dans l'`auth.json` global
d'opencode (`~/.local/share/opencode/auth.json`, entrée `opencode-go` ou
`opencode`). Tu n'as rien à configurer si `opencode auth login` a déjà été
fait. Pour surcharger (autre compte, autre machine), copie
`auth.json.example` en `auth.json` avec `zen.key`, ou exporte
`OPENCODE_API_KEY`.

## Lancer une scène

```bash
python main.py
```

La scène s'affiche dans le terminal réplique par réplique, et est sauvegardée
en Markdown dans `output/scene_<timestamp>.md`.

## Comment ça marche

- Chaque personnage a son propre fichier YAML (`characters/`) avec sa fiche
  complète et son system prompt. Le prompt contient un placeholder
  `{ivresse}` qui est rempli dynamiquement à chaque tour.
- L'**ivresse** (0 à 10) augmente progressivement au fil de la scène
  (paramètre `ivresse` dans `config.yaml`), ce qui doit se traduire dans le
  style d'écriture de chaque agent (syntaxe qui se délite, digressions...).
- Chaque agent ne voit que l'historique du dialogue déjà prononcé (texte brut
  "NOM: réplique"), jamais les instructions internes de l'autre personnage —
  comme au théâtre, chacun ignore les intentions cachées de l'autre.
- `main.py` alterne les tours entre les deux personnages, appelle l'API
  correspondante (voir `moteur: claude` ou `moteur: glm` dans chaque fichier
  de personnage), et construit l'historique au fur et à mesure.

## Pour ajuster la pièce

- **Nombre de répliques** : `max_turns` dans `config.yaml`
- **Vitesse de montée de l'ivresse** : `ivresse.seuil_bascule` (plus il est
  bas, plus l'ivresse monte vite)
- **Qui parle en premier** : `premier_a_parler`
- **Personnalité / ton / secrets de chaque personnage** : directement dans
  `characters/philippe.yaml` et `characters/noa.yaml`

## Notes sur les modèles

- Le nom de modèle GLM (variable d'environnement `GLM_MODEL`, défaut
  `glm-5.2`) doit correspondre à un modèle listé par `opencode models` sous
  le provider `opencode-go`.
- Si tu préfères utiliser un autre fournisseur pour le rôle "GLM" (ex: OpenAI,
  Mistral, un modèle local via Ollama...), il suffit d'ajouter une nouvelle
  fonction `call_xxx` dans `agents.py` et de l'ajouter au dict `ENGINES`, puis
  de changer `moteur: xxx` dans le fichier YAML du personnage concerné.
