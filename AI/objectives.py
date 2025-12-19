from enum import Enum
from typing import Optional
from .perception import GameState
from .manager import Strategy

class Objective(Enum):
    """Objectifs stratégiques possibles pour l'IA."""
    DRAGON = "dragon"        # Contrôle du dragon
    BARON = "baron"          # Contrôle du baron
    PUSH = "push"            # Pousser les lanes
    DEFEND = "defend"        # Défendre les structures
    FARM = "farm"            # Farm des sbires et monstres
    GROUP = "group"          # Regroupement d'équipe
    SPLIT_PUSH = "split"     # Push séparé
    VISION = "vision"        # Contrôle de vision

class ObjectiveManager:
    """Gestionnaire des objectifs de l'IA."""
    
    def __init__(self):
        self.current_objective: Optional[Objective] = None
        self.objective_priority = {
            Objective.DRAGON: 90,    # Haute priorité quand disponible
            Objective.BARON: 85,     # Haute priorité en fin de partie
            Objective.DEFEND: 80,    # Défense des structures importantes
            Objective.PUSH: 70,      # Pousser les lanes
            Objective.FARM: 50,      # Farm de base
            Objective.GROUP: 60,     # Regroupement
            Objective.SPLIT_PUSH: 65,# Split push
            Objective.VISION: 30     # Contrôle de vision
        }
    
    def select_objective(self, state: GameState, strategy: Strategy) -> Objective:
        """
        Sélectionne l'objectif prioritaire en fonction de l'état du jeu et de la stratégie.
        
        Args:
            state: État actuel du jeu
            strategy: Stratégie actuelle de l'IA
            
        Returns:
            L'objectif prioritaire
        """
        # Vérification des objectifs critiques
        if state.dragon_timer < 45 and state.dragon_timer > 0:
            return Objective.DRAGON
            
        if state.baron_timer < 60 and state.baron_timer > 0 and state.game_phase == "late":
            return Objective.BARON
            
        # Adaptation en fonction de la stratégie
        if strategy == Strategy.AGGRESSIVE:
            return Objective.PUSH
        elif strategy == Strategy.DEFENSIVE:
            return Objective.DEFEND
        elif strategy == Strategy.SCALING:
            if state.game_phase == "late":
                return Objective.BARON if state.baron_timer < 120 else Objective.GROUP
            return Objective.FARM
            
        # Par défaut, on farm
        return Objective.FARM
    
    def update(self, state: GameState, strategy: Strategy) -> None:
        """
        Met à jour l'objectif actuel.
        
        Args:
            state: État actuel du jeu
            strategy: Stratégie actuelle de l'IA
        """
        new_objective = self.select_objective(state, strategy)
        if new_objective != self.current_objective:
            self.current_objective = new_objective
            print(f"[AI] Nouvel objectif: {self.current_objective.value}")
    
    def get_current_objective(self) -> Optional[Objective]:
        """Retourne l'objectif actuel."""
        return self.current_objective
