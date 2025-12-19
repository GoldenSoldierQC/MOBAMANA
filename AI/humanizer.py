import random
from enum import Enum
from typing import Dict, Tuple

from .tactics import CombatAction, CombatDecision

class StressLevel(Enum):
    """Niveaux de stress qui affectent le comportement humain."""
    CALM = 0.1       # Détendu, peu d'erreurs
    NORMAL = 0.3     # Comportement standard
    PRESSURED = 0.6  # Sous pression, plus d'erreurs
    PANIC = 0.9      # Panique, beaucoup d'erreurs

class Humanizer:
    """
    Ajoute des imperfections humaines aux actions de l'IA pour un gameplay plus naturel.
    """
    
    def __init__(self):
        self.stress_level: StressLevel = StressLevel.NORMAL
        self.last_action_time: Dict[str, float] = {}
        self.action_history: list = []
        self.reaction_times: Dict[str, list] = {
            'min': 0.15,  # Temps de réaction humain minimum (secondes)
            'max': 0.5    # Temps de réaction humain maximum (secondes)
        }
        
        # Facteurs d'erreur basés sur le stress
        self.error_factors = {
            'click_accuracy': 0.98,  # Précision des clics (0.0 à 1.0)
            'reaction_time': 1.0,    # Facteur multiplicateur du temps de réaction
            'decision_quality': 1.0   # Qualité des décisions (1.0 = parfaite)
        }
    
    def update_stress(self, game_state: dict):
        """
        Met à jour le niveau de stress en fonction de l'état du jeu.
        
        Args:
            game_state: État actuel du jeu
        """
        # Exemple simple : augmenter le stress en fonction des ennemis proches
        nearby_enemies = game_state.get('nearby_enemies', 0)
        health_percent = game_state.get('health_percent', 1.0)
        
        if health_percent < 0.3 or nearby_enemies > 2:
            self.stress_level = StressLevel.PANIC
        elif health_percent < 0.6 or nearby_enemies > 0:
            self.stress_level = StressLevel.PRESSURED
        else:
            self.stress_level = StressLevel.NORMAL
        
        # Mettre à jour les facteurs d'erreur en fonction du stress
        stress_value = self.stress_level.value
        self.error_factors = {
            'click_accuracy': max(0.7, 1.0 - (stress_value * 0.3)),
            'reaction_time': 1.0 + stress_value,
            'decision_quality': 1.0 - (stress_value * 0.5)
        }
    
    def humanize_decision(self, decision: CombatDecision) -> CombatDecision:
        """
        Ajoute des imperfections humaines à une décision de combat.
        
        Args:
            decision: Décision de combat originale
            
        Returns:
            Décision modifiée avec des imperfections
        """
        if random.random() > self.error_factors['decision_quality']:
            # Prendre une mauvaise décision occasionnellement
            if decision.action == CombatAction.ATTACK and random.random() > 0.5:
                decision.action = CombatAction.RETREAT
                decision.confidence *= 0.5
        
        return decision
    
    def humanize_click_position(self, position: Tuple[float, float]) -> Tuple[float, float]:
        """
        Ajoute une légère imprécision à une position de clic.
        
        Args:
            position: Position cible (x, y)
            
        Returns:
            Nouvelle position avec une légère variation
        """
        accuracy = self.error_factors['click_accuracy']
        x, y = position
        
        # Ajouter un décalage aléatoire basé sur la précision
        max_offset = 10 * (1.0 - accuracy)  # Jusqu'à 10 pixels de décalage
        x += random.uniform(-max_offset, max_offset)
        y += random.uniform(-max_offset, max_offset)
        
        return (x, y)
    
    def get_human_delay(self, action_type: str) -> float:
        """
        Retourne un délai humain pour une action donnée.
        
        Args:
            action_type: Type d'action ('move', 'attack', 'ability', etc.)
            
        Returns:
            Délai en secondes avant d'effectuer l'action
        """
        base_delay = random.uniform(
            self.reaction_times['min'],
            self.reaction_times['max']
        )
        
        # Ajuster en fonction du type d'action et du stress
        if action_type in ['ability', 'ultimate']:
            base_delay *= 1.2  # Les compétences prennent plus de temps
        
        return base_delay * self.error_factors['reaction_time']
    
    def should_make_mistake(self, mistake_type: str) -> bool:
        """
        Détermine si l'IA devrait faire une erreur.
        
        Args:
            mistake_type: Type d'erreur ('miss_click', 'bad_decision', 'slow_reaction')
            
        Returns:
            True si une erreur devrait être faite, False sinon
        """
        base_chance = 0.05  # 5% de chance de base de faire une erreur
        stress_factor = self.stress_level.value
        
        if mistake_type == 'miss_click':
            chance = base_chance * (1.0 + stress_factor)
        elif mistake_type == 'bad_decision':
            chance = base_chance * 0.7 * (1.0 + stress_factor)
        elif mistake_type == 'slow_reaction':
            chance = base_chance * 0.5 * (1.0 + stress_factor)
        else:
            chance = base_chance
            
        return random.random() < chance
