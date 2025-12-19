"""
Overlays visuels sur la carte pour montrer la stratégie de l'IA.
Flèches, cercles pulsants et zones colorées pour une communication visuelle instantanée.
"""

import pygame
import math
from typing import Tuple, List, Optional
from enum import Enum
from dataclasses import dataclass

from AI import Strategy, Objective
from .strategy_hud import StrategyColor

class OverlayType(Enum):
    """Types d'overlays visuels."""
    ARROW = "arrow"           # Flèche de direction (push)
    PULSE_CIRCLE = "pulse"    # Cercle pulsant (objectif)
    DEFENSE_ZONE = "zone"     # Zone défensive
    WARNING = "warning"       # Avertissement

@dataclass
class MapOverlay:
    """Overlay visuel sur la carte."""
    overlay_type: OverlayType
    position: Tuple[float, float]  # Position sur la carte (coordonnées du jeu)
    color: Tuple[int, int, int]
    size: float = 1.0
    alpha: int = 180
    animation_time: float = 0.0

class MapOverlayManager:
    """
    Gère tous les overlays visuels sur la carte pour communiquer
    la stratégie de manière non-textuelle.
    """
    
    def __init__(self):
        self.overlays: List[MapOverlay] = []
        self.animation_time: float = 0.0
        
        # Paramètres visuels
        self.arrow_length = 60
        self.arrow_width = 8
        self.pulse_min_radius = 15
        self.pulse_max_radius = 25
        self.pulse_speed = 2.0
        
    def update(self, strategy: Strategy, objective: Optional[Objective], 
               game_state: dict, allies: List[dict], enemies: List[dict]):
        """
        Met à jour les overlays en fonction de la stratégie et de l'état du jeu.
        
        Args:
            strategy: Stratégie actuelle
            objective: Objectif actuel
            game_state: État du jeu
            allies: Liste des alliés
            enemies: Liste des ennemis
        """
        self.overlays.clear()
        color = StrategyColor[strategy.name].value
        
        # Overlays basés sur la stratégie
        if strategy == Strategy.AGGRESSIVE:
            self._add_aggressive_overlays(objective, allies, color)
        elif strategy == Strategy.DEFENSIVE:
            self._add_defensive_overlays(allies, color)
        elif strategy == Strategy.SCALING:
            self._add_scaling_overlays(objective, allies, color)
        else:  # BALANCED
            self._add_balanced_overlays(objective, allies, color)
            
        # Overlays basés sur l'objectif
        if objective:
            self._add_objective_overlay(objective, game_state)
            
    def _add_aggressive_overlays(self, objective: Optional[Objective], 
                                allies: List[dict], color: Tuple[int, int, int]):
        """Ajoute les overlays pour la stratégie agressive."""
        # Flèches de push depuis les positions des alliés
        for ally in allies:
            if ally.get('is_alive', True):
                pos = ally.get('position', (0, 0))
                
                overlay = MapOverlay(
                    overlay_type=OverlayType.ARROW,
                    position=pos,
                    color=color,
                    animation_time=self.animation_time
                )
                self.overlays.append(overlay)
                
    def _add_defensive_overlays(self, allies: List[dict], color: Tuple[int, int, int]):
        """Ajoute les overlays pour la stratégie défensive."""
        # Zones défensives autour des alliés
        for ally in allies:
            if ally.get('is_alive', True):
                pos = ally.get('position', (0, 0))
                
                overlay = MapOverlay(
                    overlay_type=OverlayType.DEFENSE_ZONE,
                    position=pos,
                    color=color,
                    size=2.0,
                    animation_time=self.animation_time
                )
                self.overlays.append(overlay)
                
    def _add_scaling_overlays(self, objective: Optional[Objective], 
                             allies: List[dict], color: Tuple[int, int, int]):
        """Ajoute les overlays pour la stratégie de scaling."""
        # Indicateurs de regroupement
        if len(allies) > 1:
            # Position moyenne des alliés
            avg_x = sum(a.get('position', (0, 0))[0] for a in allies) / len(allies)
            avg_y = sum(a.get('position', (0, 0))[1] for a in allies) / len(allies)
            
            overlay = MapOverlay(
                overlay_type=OverlayType.PULSE_CIRCLE,
                position=(avg_x, avg_y),
                color=color,
                size=1.5,
                animation_time=self.animation_time
            )
            self.overlays.append(overlay)
            
    def _add_balanced_overlays(self, objective: Optional[Objective], 
                              allies: List[dict], color: Tuple[int, int, int]):
        """Ajoute les overlays pour la stratégie équilibrée."""
        # Indicateurs subtils de direction
        for ally in allies[:2]:  # Seulement les 2 premiers alliés
            if ally.get('is_alive', True):
                pos = ally.get('position', (0, 0))
                
                overlay = MapOverlay(
                    overlay_type=OverlayType.ARROW,
                    position=pos,
                    color=color,
                    size=0.7,  # Plus petit pour une stratégie équilibrée
                    animation_time=self.animation_time
                )
                self.overlays.append(overlay)
                
    def _add_objective_overlay(self, objective: Objective, game_state: dict):
        """Ajoute un overlay pour l'objectif actuel."""
        # Position de l'objectif (à adapter selon votre système)
        obj_pos = self._get_objective_position(objective, game_state)
        
        if obj_pos:
            color = (255, 200, 50)  # Jaune pour les objectifs
            
            overlay = MapOverlay(
                overlay_type=OverlayType.PULSE_CIRCLE,
                position=obj_pos,
                color=color,
                size=2.0,
                animation_time=self.animation_time
            )
            self.overlays.append(overlay)
            
    def _get_objective_position(self, objective: Objective, game_state: dict) -> Optional[Tuple[float, float]]:
        """Retourne la position d'un objectif sur la carte."""
        # À adapter selon votre système de coordonnées
        positions = {
            Objective.DRAGON: game_state.get('dragon_position'),
            Objective.BARON: game_state.get('baron_position'),
            Objective.PUSH: game_state.get('enemy_base_position'),
            Objective.DEFEND: game_state.get('ally_base_position'),
        }
        return positions.get(objective)
        
    def draw(self, screen: pygame.Surface, map_rect: pygame.Rect, 
             game_to_screen_transform: callable):
        """
        Dessine tous les overlays sur la carte.
        
        Args:
            screen: Surface pygame où dessiner
            map_rect: Rectangle de la carte sur l'écran
            game_to_screen_transform: Fonction pour convertir les coordonnées du jeu en coordonnées écran
        """
        for overlay in self.overlays:
            screen_pos = game_to_screen_transform(overlay.position)
            
            if overlay.overlay_type == OverlayType.ARROW:
                self._draw_arrow(screen, screen_pos, overlay)
            elif overlay.overlay_type == OverlayType.PULSE_CIRCLE:
                self._draw_pulse_circle(screen, screen_pos, overlay)
            elif overlay.overlay_type == OverlayType.DEFENSE_ZONE:
                self._draw_defense_zone(screen, screen_pos, overlay)
            elif overlay.overlay_type == OverlayType.WARNING:
                self._draw_warning(screen, screen_pos, overlay)
                
    def _draw_arrow(self, screen: pygame.Surface, pos: Tuple[int, int], overlay: MapOverlay):
        """Dessine une flèche de direction."""
        # Direction par défaut (vers la droite) - à adapter
        angle = 0
        
        # Calcul des points de la flèche
        arrow_length = self.arrow_length * overlay.size
        arrow_width = self.arrow_width * overlay.size
        
        end_x = pos[0] + arrow_length * math.cos(angle)
        end_y = pos[1] + arrow_length * math.sin(angle)
        
        # Ligne principale
        pygame.draw.line(screen, overlay.color, pos, (end_x, end_y), arrow_width)
        
        # Pointe de la flèche
        tip_angle1 = angle + 2.5
        tip_angle2 = angle - 2.5
        tip_length = 15 * overlay.size
        
        tip1_x = end_x - tip_length * math.cos(tip_angle1)
        tip1_y = end_y - tip_length * math.sin(tip_angle1)
        tip2_x = end_x - tip_length * math.cos(tip_angle2)
        tip2_y = end_y - tip_length * math.sin(tip_angle2)
        
        pygame.draw.polygon(screen, overlay.color, [
            (end_x, end_y),
            (tip1_x, tip1_y),
            (tip2_x, tip2_y)
        ])
        
    def _draw_pulse_circle(self, screen: pygame.Surface, pos: Tuple[int, int], overlay: MapOverlay):
        """Dessine un cercle pulsant."""
        # Calcul du rayon avec animation
        pulse = (math.sin(overlay.animation_time * self.pulse_speed) + 1) / 2
        radius = self.pulse_min_radius + (self.pulse_max_radius - self.pulse_min_radius) * pulse
        radius *= overlay.size
        
        # Dessin du cercle avec transparence
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*overlay.color, overlay.alpha), (radius, radius), radius, 3)
        screen.blit(s, (pos[0] - radius, pos[1] - radius))
        
    def _draw_defense_zone(self, screen: pygame.Surface, pos: Tuple[int, int], overlay: MapOverlay):
        """Dessine une zone défensive."""
        radius = 40 * overlay.size
        
        # Zone semi-transparente
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*overlay.color, 50), (radius, radius), radius)
        pygame.draw.circle(s, overlay.color, (radius, radius), radius, 2)
        screen.blit(s, (pos[0] - radius, pos[1] - radius))
        
    def _draw_warning(self, screen: pygame.Surface, pos: Tuple[int, int], overlay: MapOverlay):
        """Dessine un avertissement."""
        size = 20 * overlay.size
        
        # Triangle d'avertissement
        points = [
            (pos[0], pos[1] - size),
            (pos[0] - size * 0.8, pos[1] + size * 0.5),
            (pos[0] + size * 0.8, pos[1] + size * 0.5)
        ]
        pygame.draw.polygon(screen, overlay.color, points, 3)
        
        # Point d'exclamation
        font = pygame.font.Font(None, 16)
        text = font.render("!", True, overlay.color)
        text_rect = text.get_rect(center=pos)
        screen.blit(text, text_rect)
        
    def update_animation(self, delta_time: float):
        """Met à jour les animations."""
        self.animation_time += delta_time
        for overlay in self.overlays:
            overlay.animation_time = self.animation_time
