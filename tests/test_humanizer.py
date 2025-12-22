import unittest
import random
from unittest.mock import patch

# Ajouter le répertoire parent au chemin d'importation
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from AI.humanizer import Humanizer, StressLevel
from AI.tactics import CombatAction, CombatDecision, TargetType

class TestHumanizer(unittest.TestCase):
    """Tests pour la classe Humanizer."""
    
    def setUp(self):
        """Initialisation avant chaque test."""
        self.humanizer = Humanizer()
        random.seed(42)  # Pour des tests déterministes
    
    def test_initial_state(self):
        """Vérifie l'état initial du Humanizer."""
        self.assertEqual(self.humanizer.stress_level, StressLevel.NORMAL)
        self.assertEqual(len(self.humanizer.last_action_time), 0)
        self.assertEqual(len(self.humanizer.action_history), 0)
        self.assertIn('click_accuracy', self.humanizer.error_factors)
        self.assertIn('reaction_time', self.humanizer.error_factors)
        self.assertIn('decision_quality', self.humanizer.error_factors)
    
    def test_update_stress_calm(self):
        """Teste la mise à jour du stress en mode calme."""
        game_state = {'health_percent': 0.95, 'nearby_enemies': 0}
        self.humanizer.update_stress(game_state)
        self.assertEqual(self.humanizer.stress_level, StressLevel.CALM)
    
    def test_update_stress_panic(self):
        """Teste la mise à jour du stress en mode panique."""
        # Test avec peu de vie
        game_state = {'health_percent': 0.2, 'nearby_enemies': 0}
        self.humanizer.update_stress(game_state)
        self.assertEqual(self.humanizer.stress_level, StressLevel.PANIC)
        
        # Test avec beaucoup d'ennemis
        game_state = {'health_percent': 0.8, 'nearby_enemies': 3}
        self.humanizer.update_stress(game_state)
        self.assertEqual(self.humanizer.stress_level, StressLevel.PANIC)
    
    def test_update_stress_invalid_input(self):
        """Teste la gestion des entrées invalides pour update_stress."""
        # Test avec un pourcentage de vie invalide
        with self.assertRaises(ValueError):
            self.humanizer.update_stress(
                {'health_percent': 1.5, 'nearby_enemies': 0},
                silent=True  # Désactive les messages d'erreur pour les tests
            )
        
        # Test avec un nombre d'ennemis négatif
        with self.assertRaises(ValueError):
            self.humanizer.update_stress(
                {'health_percent': 0.5, 'nearby_enemies': -1},
                silent=True
            )
        
        # Test avec un type invalide
        with self.assertRaises(ValueError):
            self.humanizer.update_stress(
                {'health_percent': 'invalid', 'nearby_enemies': 0},
                silent=True
            )
    
    def test_humanize_click_position(self):
        """Teste l'ajout d'imprécision aux positions de clic."""
        # Test avec une position valide
        position = (100.0, 200.0)
        new_position = self.humanizer.humanize_click_position(position)
        
        # Vérifie que la nouvelle position est un tuple de 2 éléments
        self.assertIsInstance(new_position, tuple)
        self.assertEqual(len(new_position), 2)
        
        # Vérifie que les nouvelles coordonnées sont proches des originales
        x, y = new_position
        self.assertAlmostEqual(x, 100.0, delta=10.0)
        self.assertAlmostEqual(y, 200.0, delta=10.0)
        
        # Test avec une position invalide
        with self.assertRaises(ValueError):
            self.humanizer.humanize_click_position(('invalid', 'position'))
    
    def test_humanize_decision(self):
        """Teste l'ajout d'imperfections aux décisions."""
        # Crée une décision de test
        original_decision = CombatDecision(
            action=CombatAction.ATTACK,
            target_type=TargetType.CHAMPION,
            target_id=1,
            confidence=0.9
        )
        
        # Test avec un niveau de stress normal (peu de chances de mauvaise décision)
        with patch('random.random', return_value=0.9):  # Force un résultat spécifique
            modified_decision = self.humanizer.humanize_decision(original_decision)
            self.assertEqual(modified_decision.action, CombatAction.ATTACK)
        
        # Test avec un niveau de stress élevé et une décision modifiée
        self.humanizer.stress_level = StressLevel.PANIC
        with patch('random.random', return_value=0.1):  # Force une mauvaise décision
            modified_decision = self.humanizer.humanize_decision(original_decision)
            self.assertIn(modified_decision.action, [CombatAction.ATTACK, CombatAction.RETREAT])
    
    def test_error_factors_update(self):
        """Vérifie que les facteurs d'erreur sont correctement mis à jour."""
        # Test avec différents niveaux de stress
        test_cases = [
            (StressLevel.CALM, 0.1),
            (StressLevel.NORMAL, 0.3),
            (StressLevel.PRESSURED, 0.6),
            (StressLevel.PANIC, 0.9)
        ]
        
        for stress_level, expected_stress in test_cases:
            with self.subTest(stress_level=stress_level):
                self.humanizer.stress_level = stress_level
                self.humanizer._update_error_factors()
                
                # Vérifie que les facteurs sont dans des plages raisonnables
                self.assertGreaterEqual(self.humanizer.error_factors['click_accuracy'], 0.0)
                self.assertLessEqual(self.humanizer.error_factors['click_accuracy'], 1.0)
                
                self.assertGreaterEqual(self.humanizer.error_factors['reaction_time'], 1.0)
                
                self.assertGreaterEqual(self.humanizer.error_factors['decision_quality'], 0.0)
                self.assertLessEqual(self.humanizer.error_factors['decision_quality'], 1.0)

if __name__ == '__main__':
    unittest.main()
