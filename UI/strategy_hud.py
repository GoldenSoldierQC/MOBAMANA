"""
HUD stratégique principal pour afficher la stratégie de l'IA en temps réel.
Conçu pour être lisible en 1 seconde maximum.
"""

import pygame
from typing import Tuple, Optional
from enum import Enum
from dataclasses import dataclass

from AI import Strategy, Objective, GameState

class StrategyColor(Enum):
    """Codes couleur universels pour les stratégies."""
    AGGRESSIVE = (220, 50, 50)    # Rouge
    BALANCED = (220, 180, 50)     # Jaune
    DEFENSIVE = (50, 120, 220)    # Bleu
    SCALING = (150, 50, 220)      # Violet

@dataclass
class HUDPosition:
    """Position et dimensions du HUD stratégique."""
    x: int
    y: int
    width: int = 300
    height: int = 80
    
class StrategyHUD:
    """
    HUD stratégique principal affichant la stratégie actuelle,
    l'objectif et la puissance d'équipe.
    """
    
    def __init__(self, position: HUDPosition):
        self.position = position
        self.font_large = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        
        # État actuel
        self.current_strategy: Strategy = Strategy.BALANCED
        self.current_objective: Optional[Objective] = None
        self.current_objective_timer: int = 0
        self.team_power_diff: float = 0.0
        
        # Animation
        self.pulse_time: float = 0.0
        self.show_explanation: bool = False
        self.explanation_text: str = ""
        
    def update(self, state: GameState, strategy: Strategy, objective: Optional[Objective], 
               objective_timer: int = 0):
        """
        Met à jour l'état du HUD.
        
        Args:
            state: État actuel du jeu
            strategy: Stratégie actuelle
            objective: Objectif actuel
            objective_timer: Temps restant pour l'objectif (secondes)
        """
        self.current_strategy = strategy
        self.current_objective = objective
        self.current_objective_timer = objective_timer
        self.team_power_diff = state.ally_power - state.enemy_power
        
        # Générer l'explication
        self._generate_explanation(state, strategy, objective)
        
    def _generate_explanation(self, state: GameState, strategy: Strategy, objective: Optional[Objective]):
        """Génère le texte d'explication pour la stratégie actuelle."""
        explanations = []
        
        if strategy == Strategy.AGGRESSIVE:
            if state.gold_diff > 1000:
                explanations.append("+ Gold advantage")
            if objective == Objective.DRAGON and state.dragon_timer < 60:
                explanations.append("+ Dragon soon")
            if state.enemy_power < state.ally_power * 0.8:
                explanations.append("+ Enemy vision low")
                
        elif strategy == Strategy.DEFENSIVE:
            if state.gold_diff < -1000:
                explanations.append("- Gold disadvantage")
            if state.ally_power < state.enemy_power * 0.7:
                explanations.append("- Team weaker")
                
        elif strategy == Strategy.SCALING:
            if state.game_phase == "late":
                explanations.append("+ Late game power")
            if state.ally_power > state.enemy_power:
                explanations.append("+ Scaling advantage")
                
        else:  # BALANCED
            explanations.append("Standard play")
            
        self.explanation_text = "\n".join(explanations)
        
    def draw(self, screen: pygame.Surface, mouse_pos: Tuple[int, int]):
        """
        Dessine le HUD stratégique sur l'écran.
        
        Args:
            screen: Surface pygame où dessiner
            mouse_pos: Position actuelle de la souris
        """
        # Couleur de fond semi-transparente
        bg_surface = pygame.Surface((self.position.width, self.position.height))
        bg_surface.set_alpha(200)
        bg_surface.fill((20, 20, 20))
        
        # Bordure colorée selon la stratégie
        border_color = StrategyColor[self.current_strategy.name].value
        pygame.draw.rect(bg_surface, border_color, bg_surface.get_rect(), 3)
        
        # Dessiner le fond
        screen.blit(bg_surface, (self.position.x, self.position.y))
        
        # Ligne 1: Stratégie
        strategy_text = f"STRATEGY: {self.current_strategy.value.upper()}"
        strategy_surface = self.font_large.render(strategy_text, True, (255, 255, 255))
        screen.blit(strategy_surface, (self.position.x + 10, self.position.y + 10))
        
        # Ligne 2: Objectif avec timer
        if self.current_objective:
            if self.current_objective_timer > 0:
                objective_text = f"OBJECTIVE: {self.current_objective.value.upper()} ({self.current_objective_timer}s)"
            else:
                objective_text = f"OBJECTIVE: {self.current_objective.value.upper()}"
        else:
            objective_text = "OBJECTIVE: NONE"
            
        objective_surface = self.font_small.render(objective_text, True, (200, 200, 200))
        screen.blit(objective_surface, (self.position.x + 10, self.position.y + 35))
        
        # Ligne 3: Puissance d'équipe
        power_percent = int(self.team_power_diff * 100)
        if power_percent > 0:
            power_text = f"TEAM POWER: +{power_percent}%"
            power_color = (100, 255, 100)
        elif power_percent < 0:
            power_text = f"TEAM POWER: {power_percent}%"
            power_color = (255, 100, 100)
        else:
            power_text = "TEAM POWER: EQUAL"
            power_color = (200, 200, 200)
            
        power_surface = self.font_small.render(power_text, True, power_color)
        screen.blit(power_surface, (self.position.x + 10, self.position.y + 55))
        
        # Afficher l'explication au survol
        if self._is_mouse_over(mouse_pos):
            self._draw_explanation(screen, mouse_pos)
            
    def _is_mouse_over(self, mouse_pos: Tuple[int, int]) -> bool:
        """Vérifie si la souris est au-dessus du HUD."""
        mx, my = mouse_pos
        return (self.position.x <= mx <= self.position.x + self.position.width and
                self.position.y <= my <= self.position.y + self.position.height)
                
    def _draw_explanation(self, screen: pygame.Surface, mouse_pos: Tuple[int, int]):
        """Dessine la bulle d'explication au survol."""
        if not self.explanation_text:
            return
            
        # Taille de la bulle d'explication
        lines = self.explanation_text.split('\n')
        max_width = max(self.font_small.size(line)[0] for line in lines)
        bubble_width = max_width + 20
        bubble_height = len(lines) * 20 + 10
        
        # Position de la bulle (au-dessus du HUD)
        bubble_x = mouse_pos[0] - bubble_width // 2
        bubble_y = self.position.y - bubble_height - 10
        
        # S'assurer que la bulle reste dans l'écran
        bubble_x = max(10, min(bubble_x, screen.get_width() - bubble_width - 10))
        bubble_y = max(10, bubble_y)
        
        # Dessiner la bulle
        bubble_surface = pygame.Surface((bubble_width, bubble_height))
        bubble_surface.set_alpha(230)
        bubble_surface.fill((40, 40, 40))
        pygame.draw.rect(bubble_surface, StrategyColor[self.current_strategy.name].value, 
                        bubble_surface.get_rect(), 2)
        
        # Dessiner le texte
        for i, line in enumerate(lines):
            text_surface = self.font_small.render(line, True, (255, 255, 255))
            bubble_surface.blit(text_surface, (10, 5 + i * 20))
            
        screen.blit(bubble_surface, (bubble_x, bubble_y))
        
    def get_strategy_color(self) -> Tuple[int, int, int]:
        """Retourne la couleur de la stratégie actuelle."""
        return StrategyColor[self.current_strategy.name].value
