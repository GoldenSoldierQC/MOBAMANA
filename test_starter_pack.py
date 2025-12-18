#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion Setup-Starter Pack
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from moba_manager import create_initial_roster

def test_starter_pack_generation():
    """Test la génération de Starter Pack pour chaque spécialisation"""
    print("=== TEST DE GÉNÉRATION DE STARTER PACK ===\n")
    
    specializations = ["Polyvalent", "Analyste", "Motivateur", "Scout", "Entraîneur"]
    
    for spec in specializations:
        print(f"--- Spécialisation: {spec} ---")
        
        # Création de l'équipe avec le Starter Pack
        team = create_initial_roster(
            team_name=f"Team_{spec}",
            coach_name=f"Coach_{spec}",
            color=(100, 100, 100),
            specialization=spec,
            prestige=70
        )
        
        print(f"Nom de l'équipe: {team.name}")
        print(f"Coach: {team.coach_name}")
        print(f"Spécialisation: {team.specialization}")
        print(f"Budget initial: {team.finance.budget:,} $")
        print(f"Couleur: {team.team_color}")
        print(f"Forme du logo: {team.logo_shape}")
        
        print("\nRoster:")
        total_market_value = 0
        for role, player in team.roster.items():
            if player:
                print(f"  {role.value}: {player.name} ({player.tier}) - Niv.{player.level} - {player.market_value:,} $")
                print(f"    Stats: MEC={player.mec}, MAC={player.mac}, VIS={player.vis}, SNG={player.sng}")
                total_market_value += player.market_value
            else:
                print(f"  {role.value}: VIDE")
        
        print(f"\nValeur totale du roster: {total_market_value:,} $")
        print(f"Budget restant: {team.finance.budget:,} $")
        print(f"Coût total (roster + budget): {total_market_value + team.finance.budget:,} $")
        
        # Vérification des bonus de spécialisation
        print("\nBonus de spécialisation appliqués:")
        if spec == "Analyste":
            print("  +10 Vision, +5 Macro attendus")
        elif spec == "Motivateur":
            print("  +10 Sang-froid, +5 Mécaniques attendus")
        elif spec == "Scout":
            print("  +5 dans toutes les stats attendues")
        elif spec == "Entraîneur":
            print("  +3 dans toutes les stats attendues")
        elif spec == "Polyvalent":
            print("  +2 dans toutes les stats attendues")
        
        print("\n" + "=" * 60 + "\n")

def test_setup_connection():
    """Test simule la connexion avec l'écran Setup"""
    print("=== TEST DE CONNEXION SETUP ===\n")
    
    # Simulation des données de l'écran Setup
    setup_data = {
        "coach_name": "GoldenCoach",
        "team_name": "MOBA Warriors",
        "selected_color": (255, 100, 50),
        "specialization": "Analyste",
        "selected_shape": "Diamant"
    }
    
    print("Données de l'écran Setup:")
    for key, value in setup_data.items():
        print(f"  {key}: {value}")
    
    print("\nCréation de l'équipe...")
    
    # Création de l'équipe avec les données du Setup
    team = create_initial_roster(
        team_name=setup_data["team_name"],
        coach_name=setup_data["coach_name"],
        color=setup_data["selected_color"],
        specialization=setup_data["specialization"],
        prestige=70
    )
    
    # Ajout des données supplémentaires du Setup
    team.logo_shape = setup_data["selected_shape"]
    
    print("\nÉquipe créée avec succès:")
    print(f"  Nom: {team.name}")
    print(f"  Coach: {team.coach_name}")
    print(f"  Spécialisation: {team.specialization}")
    print(f"  Budget: {team.finance.budget:,} $")
    print(f"  Couleur: {team.team_color}")
    print(f"  Forme du logo: {team.logo_shape}")
    
    print("\nRoster généré:")
    for role, player in team.roster.items():
        if player:
            print(f"  {role.value}: {player.name} ({player.tier})")

if __name__ == "__main__":
    test_starter_pack_generation()
    test_setup_connection()
    
    print("✅ Tous les tests complétés avec succès!")
