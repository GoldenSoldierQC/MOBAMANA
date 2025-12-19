from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .manager import Strategy
from .perception import GameState

class CombatAction(Enum):
    """Actions de combat possibles."""
    ATTACK = "attack"
    ABILITY_1 = "ability1"
    ABILITY_2 = "ability2"
    ULTIMATE = "ultimate"
    RETREAT = "retreat"
    MOVE = "move"
    USE_ITEM = "use_item"

class TargetType(Enum):
    """Types de cibles possibles."""
    CHAMPION = "champion"
    MINION = "minion"
    TURRET = "turret"
    OBJECTIVE = "objective"
    NONE = "none"

@dataclass
class CombatDecision:
    """Décision de combat prise par l'IA."""
    action: CombatAction
    target_type: TargetType
    target_id: Optional[int] = None
    position: Optional[Tuple[float, float]] = None
    confidence: float = 1.0  # Confiance dans la décision (0.0 à 1.0)

class CombatTactics:
    """
    Gère les décisions de combat locales basées sur la stratégie globale.
    """
    
    def __init__(self):
        self.last_action_time: Dict[str, float] = {}
        self.action_cooldowns = {
            CombatAction.ATTACK: 0.0,
            CombatAction.ABILITY_1: 0.5,
            CombatAction.ABILITY_2: 0.5,
            CombatAction.ULTIMATE: 1.0,
            CombatAction.RETREAT: 0.0,
            CombatAction.MOVE: 0.0,
            CombatAction.USE_ITEM: 0.5
        }
    
    def can_perform_action(self, action: CombatAction, current_time: float) -> bool:
        """Vérifie si une action peut être effectuée en fonction de son temps de recharge."""
        last_time = self.last_action_time.get(action.value, 0)
        cooldown = self.action_cooldowns.get(action, 0.5)
        return (current_time - last_time) >= cooldown
    
    def decide_combat_action(
        self, 
        state: GameState,
        strategy: Strategy,
        current_time: float,
        allies: List[dict],
        enemies: List[dict],
        objectives: List[dict]
    ) -> CombatDecision:
        """
        Prend une décision de combat basée sur la situation actuelle.
        
        Args:
            state: État actuel du jeu
            strategy: Stratégie actuelle de l'IA
            current_time: Temps de jeu actuel
            allies: Liste des alliés proches
            enemies: Liste des ennemis proches
            objectives: Liste des objectifs proches
            
        Returns:
            Une décision de combat
        """
        # Logique de base : attaquer l'ennemi le plus faible si on est en position avantageuse
        if enemies:
            # Trier les ennemis par points de vie
            target = min(enemies, key=lambda x: x.get('health', 100))
            
            # Vérifier si on peut attaquer
            if self.can_perform_action(CombatAction.ATTACK, current_time):
                self.last_action_time[CombatAction.ATTACK.value] = current_time
                return CombatDecision(
                    action=CombatAction.ATTACK,
                    target_type=TargetType.CHAMPION,
                    target_id=target.get('id'),
                    confidence=0.8
                )
            
            # Sinon, se déplacer vers la cible
            return CombatDecision(
                action=CombatAction.MOVE,
                target_type=TargetType.CHAMPION,
                target_id=target.get('id'),
                confidence=0.6
            )
        
        # Si pas d'ennemis proches, se déplacer vers l'objectif
        if objectives:
            objective = objectives[0]  # Prendre le premier objectif disponible
            return CombatDecision(
                action=CombatAction.MOVE,
                target_type=TargetType.OBJECTIVE,
                target_id=objective.get('id'),
                position=objective.get('position'),
                confidence=0.7
            )
        
        # Par défaut, retourner une action neutre
        return CombatDecision(
            action=CombatAction.MOVE,
            target_type=TargetType.NONE,
            position=(0, 0),  # Position par défaut (à adapter)
            confidence=0.3
        )
    
    def update_cooldowns(self, delta_time: float):
        """Met à jour les cooldowns des actions."""
        # Cette méthode serait appelée à chaque frame avec le temps écoulé
        pass
