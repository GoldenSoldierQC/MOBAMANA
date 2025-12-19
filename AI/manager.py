from enum import Enum
from dataclasses import dataclass
from .perception import GameState

class Strategy(Enum):
    """Stratégies globales de l'IA."""
    AGGRESSIVE = "aggro"        # Agressif, prise de risques élevée
    BALANCED = "balanced"       # Équilibre entre agressivité et défense
    DEFENSIVE = "defensive"     # Défensif, évite les risques
    SCALING = "scaling"         # Focus sur l'échelle de puissance en fin de partie

@dataclass
class AIManager:
    """
    Gestionnaire principal de l'IA, responsable de la stratégie globale.
    Prend des décisions basées sur l'état actuel du jeu.
    """
    current_strategy: Strategy = Strategy.BALANCED
    last_strategy_change: float = 0.0
    
    def decide_strategy(self, state: GameState) -> Strategy:
        """
        Détermine la meilleure stratégie en fonction de l'état du jeu.
        
        Args:
            state: L'état actuel du jeu
            
        Returns:
            La stratégie à adopter
        """
        # Si on a un avantage d'or important et qu'on est en début de partie
        if state.gold_diff > 1500 and state.game_phase == "early":
            return Strategy.AGGRESSIVE
            
        # Si on est en retard en or
        if state.gold_diff < -1500:
            return Strategy.DEFENSIVE
            
        # En fin de partie, on favorise le scaling
        if state.game_phase == "late" and state.ally_power > state.enemy_power * 1.2:
            return Strategy.SCALING
            
        # Par défaut, on reste équilibré
        return Strategy.BALANCED
    
    def update(self, state: GameState, current_time: float) -> None:
        """
        Met à jour la stratégie en fonction de l'état du jeu.
        
        Args:
            state: L'état actuel du jeu
            current_time: Temps de jeu actuel (en secondes)
        """
        # On évite de changer de stratégie trop fréquemment
        if current_time - self.last_strategy_change < 60.0:  # Au moins 1 minute entre les changements
            return
            
        new_strategy = self.decide_strategy(state)
        if new_strategy != self.current_strategy:
            self.current_strategy = new_strategy
            self.last_strategy_change = current_time
            print(f"[AI] Changement de stratégie: {self.current_strategy.value}")
    
    def get_current_strategy(self) -> Strategy:
        """Retourne la stratégie actuelle."""
        return self.current_strategy
