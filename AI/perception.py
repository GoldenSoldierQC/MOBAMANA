from dataclasses import dataclass
from enum import Enum

class GamePhase(Enum):
    EARLY = "early"
    MID = "mid"
    LATE = "late"

@dataclass
class GameState:
    """
    État compressé du jeu pour la prise de décision IA.
    Contient uniquement les informations nécessaires pour la stratégie.
    """
    gold_diff: int = 0          # Différence d'or entre les équipes (allié - ennemi)
    xp_diff: int = 0            # Différence d'XP entre les équipes (allié - ennemi)
    game_phase: GamePhase = GamePhase.EARLY  # Phase de jeu actuelle
    dragon_timer: int = 0       # Temps restant avant le prochain dragon (secondes)
    baron_timer: int = 0        # Temps restant avant le prochain baron (secondes)
    ally_power: float = 0.0     # Score de puissance de l'équipe alliée
    enemy_power: float = 0.0    # Score de puissance de l'équipe ennemie
    
    @classmethod
    def from_game_data(cls, game_data: dict) -> 'GameState':
        """
        Construit un GameState à partir des données brutes du jeu.
        À adapter selon la structure de vos données de jeu.
        """
        # Exemple d'implémentation - à adapter
        return cls(
            gold_diff=game_data.get('gold_diff', 0),
            xp_diff=game_data.get('xp_diff', 0),
            game_phase=GamePhase(game_data.get('game_phase', 'early')),
            dragon_timer=game_data.get('dragon_timer', 0),
            baron_timer=game_data.get('baron_timer', 0),
            ally_power=game_data.get('ally_power', 0.0),
            enemy_power=game_data.get('enemy_power', 0.0)
        )

    def to_dict(self) -> dict:
        """Convertit l'état en dictionnaire pour le débogage ou le logging."""
        return {
            'gold_diff': self.gold_diff,
            'xp_diff': self.xp_diff,
            'game_phase': self.game_phase.value,
            'dragon_timer': self.dragon_timer,
            'baron_timer': self.baron_timer,
            'ally_power': self.ally_power,
            'enemy_power': self.enemy_power
        }
