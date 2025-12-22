#!/usr/bin/env python3
"""
Script de test pour vérifier la Ligne de Front (Momentum Visuel)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️  Pygame non disponible, test en mode simulation uniquement")

from moba_manager import MatchSimulator, create_initial_roster

def test_momentum_calculation():
    """Test le calcul du momentum ratio basé sur l'écart d'or"""
    print("=== TEST DE CALCUL DE MOMENTUM ===\n")
    
    # Création d'équipes de test
    create_initial_roster("Team_A", "Coach_A", (41, 128, 185), "Polyvalent")
    create_initial_roster("Team_B", "Coach_B", (192, 57, 43), "Analyste")
    
    # Simulation de différents écarts d'or
    test_scenarios = [
        (0, "Égalité parfaite"),
        (2500, "Avantage Bleu modéré"),
        (5000, "Avantage Bleu maximum"),
        (-2500, "Avantage Rouge modéré"),
        (-5000, "Avantage Rouge maximum"),
        (7500, "Avantage Bleu saturé"),
        (-7500, "Avantage Rouge saturé")
    ]
    
    for gold_diff, description in test_scenarios:
        # Simulation des valeurs d'or
        team_a_gold = 5000 + max(0, gold_diff)
        team_b_gold = 5000 + max(0, -gold_diff)
        
        # Calcul du momentum ratio (comme dans le code)
        momentum_ratio = max(-1.0, min(1.0, gold_diff / 5000.0))
        
        print(f"--- {description} ---")
        print(f"  Écart d'or: {gold_diff:+d}")
        print(f"  Or Bleu: {team_a_gold:,} $")
        print(f"  Or Rouge: {team_b_gold:,} $")
        print(f"  Momentum Ratio: {momentum_ratio:.2f}")
        
        # Position de la ligne de front
        minimap_width = 650  # Largeur de la minimap
        center_x = minimap_width // 2 + (momentum_ratio * (minimap_width // 2))
        print(f"  Position ligne: {center_x:.0f}px (sur {minimap_width}px)")
        
        print()

def test_momentum_visual():
    """Test visuel du momentum si pygame est disponible"""
    if not PYGAME_AVAILABLE:
        print("⚠️  Test visuel skipé (pygame non disponible)")
        return
    
    print("=== TEST VISUEL DU MOMENTUM ===\n")
    
    pygame.init()
    screen = pygame.display.set_mode((800, 400))
    pygame.display.set_caption("Test Momentum Visuel")
    clock = pygame.time.Clock()
    
    # Création d'une minimap de test
    from gui_match import EnhancedMinimap
    minimap = EnhancedMinimap(75, 50, 650, 300)
    
    # Test avec différents ratios
    test_ratios = [-1.0, -0.5, 0.0, 0.5, 1.0]
    current_test = 0
    
    font = pygame.font.Font(None, 24)
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    current_test = (current_test + 1) % len(test_ratios)
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        screen.fill((30, 30, 40))
        
        # Affichage du test actuel
        ratio = test_ratios[current_test]
        title = font.render(f"Momentum Ratio: {ratio:.1f} (SPACE pour changer)", True, (255, 255, 255))
        screen.blit(title, (10, 10))
        
        # Description
        if ratio == -1.0:
            desc = "Rouge domine totalement"
        elif ratio == -0.5:
            desc = "Rouge domine modérément"
        elif ratio == 0.0:
            desc = "Égalité parfaite"
        elif ratio == 0.5:
            desc = "Bleu domine modérément"
        elif ratio == 1.0:
            desc = "Bleu domine totalement"
        
        desc_surf = font.render(desc, True, (200, 200, 200))
        screen.blit(desc_surf, (10, 40))
        
        # Dessin de la minimap avec ligne de front
        minimap.draw(screen, [], [], (41, 128, 185), (192, 57, 43), ratio)
        
        # Instructions
        inst1 = font.render("SPACE: Changer de ratio", True, (150, 150, 150))
        inst2 = font.render("ESC: Quitter", True, (150, 150, 150))
        screen.blit(inst1, (10, 360))
        screen.blit(inst2, (10, 385))
        
        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()

def test_integration_complete():
    """Test d'intégration complète avec MatchSimulator"""
    print("=== TEST D'INTÉGRATION COMPLÈTE ===\n")
    
    # Création des équipes
    team_a = create_initial_roster("Bleue", "Coach_Bleu", (41, 128, 185), "Polyvalent")
    team_b = create_initial_roster("Rouge", "Coach_Rouge", (192, 57, 43), "Analyste")
    
    # Création du simulateur
    simulator = MatchSimulator(team_a, team_b)
    
    print("Simulation de quelques minutes pour tester le momentum...")
    
    # Simulation de 5 minutes
    for minute in range(5):
        if not simulator.is_finished:
            simulator.simulate_step()
            
            gold_diff = simulator.gold_a - simulator.gold_b
            momentum_ratio = max(-1.0, min(1.0, gold_diff / 5000.0))
            
            print(f"Minute {minute + 1}:")
            print(f"  Or Bleu: {simulator.gold_a:,} $")
            print(f"  Or Rouge: {simulator.gold_b:,} $")
            print(f"  Écart: {gold_diff:+d}")
            print(f"  Momentum: {momentum_ratio:.2f}")
            print()
    
    print("✅ Test d'intégration complété!")

if __name__ == "__main__":
    test_momentum_calculation()
    test_integration_complete()
    
    if PYGAME_AVAILABLE:
        test_momentum_visual()
    else:
        print("\n💡 Pour tester visuellement, installez pygame: pip install pygame")
    
    print("\n✅ Tous les tests de momentum complétés!")
