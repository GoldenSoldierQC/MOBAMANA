# 🏆 MOBA Team Manager 2025

MOBA Team Manager est une simulation de gestion d'e-sport développée en Python. Prenez les commandes d'une structure professionnelle, gérez votre budget, recrutez des talents et tentez de remporter le titre mondial.

## 🚀 Fonctionnalités Clés

* **Moteur de Match Dynamique** : Simulation minute par minute avec des probabilités évolutives selon la phase du match (Early, Mid, Late). Gain d'XP et statistiques individuelles (Kills, Assists, Deaths).
* **IA Tactique Adaptive** : L'IA analyse votre composition et votre style de jeu pour ajuster ses propres curseurs d'agressivité et de défense.
* **Gestion du Roster & Réserve** : Gérez un banc de remplaçants et effectuez des transferts stratégiques. Système de swap intuitif entre titulaires et réservistes.
* **Marché des Transferts Complet** : Catalogue de joueurs générés dynamiquement avec frais de rachat (buyout) et négociations basées sur le prestige.
* **Événements Aléatoires** : Des imprévus hebdomadaires (bonus sponsors, maladies, entraînements intensifs) et des actions "Clutch" en match (Epic Steals).
* **Système de Ligue & Playoffs** : Saison régulière complète suivie d'un tournoi final pour le Top 4.
* **Persistance** : Sauvegarde et chargement de votre carrière au format JSON.

## 🎮 Interface Graphique (GUI) Premium

L'application propose une interface riche développée avec Pygame, incluant :

* **Dashboard de Match** : Contrôlez la vitesse de simulation, ajustez les tactiques en temps réel et suivez le log des événements.
* **Radar Charts** : Visualisation multidimensionnelle des compétences des joueurs (Mécanique, Macro, Vision, Sang-froid).
* **Marché Interactif** : Interface de recrutement dédiée avec visualisation des stats et gestion du budget.
* **Gestion du Roster** : Système de drag-and-drop (via sélection) pour gérer votre effectif.

## 🛠️ Installation et Lancement

**Prérequis** : Python 3.10 ou supérieur (Python 3.11 recommandé pour la GUI).

**Lancement de la version Console** :

```bash
python moba_manager.py
```

**Lancement de l'interface Graphique (GUI)** :
Un environnement virtuel `venv_py11` est déjà configuré.

```powershell
.\venv_py11\Scripts\python gui_main.py
```

**Exécution des tests** :

```bash
python test_all.py
```

## 📊 Architecture Technique

Le projet est structuré de manière modulaire :

* **moba_manager.py** : Cœur du moteur (Logique métier, simulation, ligue, économie).
* **gui_main.py** : Point d'entrée de l'interface graphique et gestion des états globaux.
* **gui_match.py** : Dashboard de simulation de match en temps réel.
* **gui_market.py** : Interface du marché des transferts.
* **gui_draft.py** : Système de Phase de Pick & Ban interactive.

## ⌨️ Raccourcis (GUI)

* `[D]` : Lancer une phase de Draft / Match
* `[R]` : Accéder au Roster (et banc)
* `[M]` : Ouvrir le Marché des transferts
* `[H]` : Revenir à l'accueil
* `[Espace]` : Valider les choix (Draft) / Continuer après un match
* `[Echap]` : Quitter
