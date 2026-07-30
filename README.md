# Le Trianon — dialogue Philippe / Noa

Pièce de théâtre à deux voix, générée par deux agents IA distincts (Claude
pour Philippe, GLM-5.2 pour Noa), puis resserrée et éditée à la main.

**Décor** : Bar Le Trianon, 18e arrondissement, Paris — 1h du matin, un
lundi soir. Deux inconnus, deux tabourets l'un de l'autre, deux mondes qui
ne se croisent jamais, sauf par accident.

**Intention esthétique** : Philippe (63 ans, ancien chercheur en
immunologie, licencié économique) est écrit dans un registre proche de
Houellebecq — désenchantement clinique, froid, presque médical. Noa (24
ans, étudiante aux Beaux-Arts, trans, précaire) est écrite dans un registre
proche de Fante — orgueil abîmé, lyrisme malgré elle, une morgue à la
Arturo Bandini. L'ambiance générale du bar (le zinc, l'alcool tiède, la
crasse) emprunte à Bukowski, sans jamais faire basculer les deux
personnages dans la vulgarité gratuite.

Philippe (Claude) est généré via le CLI [Claude Code](https://claude.com/claude-code)
en mode headless (`claude -p`), donc via ton abonnement Pro/Max (`claude login`) —
pas de clé API Anthropic à payer séparément. Noa (GLM) passe par la
passerelle [OpenCode Zen](https://opencode.ai/docs/zen) (plan "Go"), facturée
sur ton compte opencode — pas de clé Zhipu séparée non plus.

## Structure du projet

```
theatre_ia/
├── index.html               # page de lecture (GitHub Pages)
├── scene_1.md                # script canonique, édité à la main —
│                              # distinct des sorties brutes des agents
├── main.py                   # orchestrateur : alterne les tours, nettoie
│                              # les sorties (préfixes de nom, non-latin)
├── agents.py                  # wrappers d'appel (claude -p / OpenCode Zen)
├── config.yaml                 # config de la scène (lieu, ivresse, tours...)
├── characters/
│   ├── philippe.yaml           # fiche + system prompt de Philippe
│   └── noa.yaml                  # fiche + system prompt de Noa
├── output/                    # scènes brutes générées par main.py
├── requirements.txt
└── auth.json.example            # optionnel, voir plus bas
```

## Lire la pièce en ligne (GitHub Pages)

1. Dans les paramètres du dépôt GitHub : **Settings → Pages → Source**,
   sélectionner la branche `master` et le dossier `/ (root)`.
2. GitHub publie la page à une URL du type
   `https://yannsimon92.github.io/104-Theatre-IA/`.
3. `index.html` charge `scene_1.md` dynamiquement au chargement de la page
   (via `fetch`) — donc toute modification de `scene_1.md` se reflète
   automatiquement sur la page publiée, sans toucher au HTML.

Pour prévisualiser en local avant de pousser sur GitHub (un simple
double-clic sur `index.html` ne fonctionnera pas, le `fetch` d'un fichier
local étant bloqué par le navigateur) :

```bash
cd theatre_ia
python3 -m http.server 8000
# puis ouvrir http://localhost:8000 dans le navigateur
```

## Générer une nouvelle scène (pipeline agents)

```bash
python3 -m venv venv
source venv/bin/activate   # sous Windows : venv\Scripts\activate
pip install -r requirements.txt
claude login                # si ce n'est pas déjà fait (compte Pro/Max)
opencode auth login         # si ce n'est pas déjà fait (compte Zen)
python3 -u main.py
```

`claude` et `opencode` doivent être installés et accessibles dans le PATH.
Ce sont eux qui gèrent l'auth via tes abonnements respectifs — `main.py` ne
s'en occupe pas. Aucune clé API payante n'est nécessaire.

La clé du compte Zen est retrouvée automatiquement dans l'`auth.json` global
d'opencode (`~/.local/share/opencode/auth.json`, entrée `opencode-go` ou
`opencode`). Tu n'as rien à configurer si `opencode auth login` a déjà été
fait. Pour surcharger (autre compte, autre machine), copie
`auth.json.example` en `auth.json` avec `zen.key`, ou exporte
`OPENCODE_API_KEY`.

La scène générée est sauvegardée, tour par tour, dans
`output/scene_<timestamp>.md`. C'est un **brouillon brut** : pour en faire
la version publiée (`scene_1.md`), il faut la relire et l'éditer à la main
— voir la section suivante.

## Principes de polissage éditorial (`scene_1.md`)

`scene_1.md` n'est pas une sortie automatique : c'est un script figé, édité
à partir des brouillons générés par les agents. Quand tu resserres une
nouvelle scène brute :

- **Coupe le méta-dialogue** : les personnages ne doivent jamais commenter
  qu'ils sont en train de devenir sincères ("c'est la première fois ce
  soir que...", "tu remarqueras que..."). Ça reste un tic d'IA à éliminer
  systématiquement à l'édition, même si le prompt le limite déjà en amont.
- **Ne brusque jamais le rythme des grandes révélations** (la fille de
  Philippe, le deuil de Noa). Elles doivent rester progressives et
  arrachées, jamais rapprochées ou rendues plus abruptes pour gagner en
  longueur — c'est ce qui fait tenir la scène émotionnellement.
- **Coupe les hésitations et répétitions redondantes**, resserre sans
  aplatir le rythme Fante/Houellebecq (phrases courtes qui alternent avec
  de longues subordonnées chez Philippe).
- **Répartis le décor matériel** (registre Bukowski) entre de courtes
  didascalies et des détails glissés dans le dialogue — jamais en
  accumulant plusieurs détails sensoriels dans une seule didascalie longue.

## Comment ça marche

- Chaque personnage a son propre fichier YAML (`characters/`) avec sa fiche
  complète et son system prompt. Le prompt contient un placeholder
  `{ivresse}` qui est rempli dynamiquement à chaque tour.
- L'**ivresse** (0 à 10) augmente progressivement (paramètres dans
  `config.yaml`), et conditionne à la fois le style d'écriture et le niveau
  de confidence autorisé (voir "Progressivité des confidences" dans chaque
  fiche personnage).
- Chaque agent ne voit que l'historique du dialogue déjà prononcé (texte brut
  "NOM: réplique"), jamais les instructions internes de l'autre personnage —
  comme au théâtre, chacun ignore les intentions cachées de l'autre.
- `main.py` alterne les tours, appelle l'API correspondante (voir
  `moteur: claude` ou `moteur: glm` dans chaque fichier de personnage),
  nettoie la sortie (préfixe de nom auto-écrit, caractères non-latins avec
  régénération automatique — `max_retries_par_replique` dans `config.yaml`),
  et sauvegarde après chaque tour.

## Pour ajuster la pièce

- **Nombre de répliques** : `max_turns` dans `config.yaml`
- **Vitesse de montée de l'ivresse** : `ivresse.seuil_bascule` (plus il est
  bas, plus l'ivresse monte vite)
- **Qui parle en premier** : `premier_a_parler`
- **Personnalité / ton / secrets de chaque personnage** : directement dans
  `characters/philippe.yaml` et `characters/noa.yaml`
- **Tolérance aux échecs de génération** : `max_retries_par_replique`

## Notes sur les modèles

- Le nom de modèle GLM (variable d'environnement `GLM_MODEL`, défaut
  `glm-5.2`) doit correspondre à un modèle listé par `opencode models` sous
  le provider `opencode-go`.
- Si tu préfères utiliser un autre fournisseur pour le rôle "GLM" (ex: OpenAI,
  Mistral, un modèle local via Ollama...), il suffit d'ajouter une nouvelle
  fonction `call_xxx` dans `agents.py` et de l'ajouter au dict `ENGINES`, puis
  de changer `moteur: xxx` dans le fichier YAML du personnage concerné.

## Limite connue

Un process lancé en arrière-plan (`nohup ... & disown`) ne survit pas à un
redémarrage de la machine/WSL. Rien à corriger côté code pour ça — c'est
structurel à cette approche ; il faut relancer manuellement le cas échéant.
