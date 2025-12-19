from dataclasses import dataclass, field  # noqa: F401
from enum import Enum
from typing import List
import random

class TeamStyle(Enum):
    """Styles d'équipe prédéfinis."""
    ROOKIE = "rookie"          # Débutant, joue de manière sécuritaire
    BALANCED = "balanced"     # Équilibre entre agressivité et défense
    AGGRESSIVE = "aggressive" # Style agressif, prise de risques
    SCALING = "scaling"       # Focus sur le late game
    TEAMFIGHT = "teamfight"   # Privilégie les combats d'équipe
    SPLIT_PUSH = "split_push" # Privilégie le split push

@dataclass
class TeamProfile:
    """
    Profil d'une équipe IA qui définit son style de jeu et ses préférences.
    """
    style: TeamStyle = TeamStyle.BALANCED
    aggression: float = 0.5           # 0.0 (défensif) à 1.0 (agressif)
    risk_tolerance: float = 0.5       # 0.0 (évite les risques) à 1.0 (prend des risques)
    objective_focus: float = 0.7      # Priorité donnée aux objectifs (0.0 à 1.0)
    teamfight_tendency: float = 0.6   # Tendance à chercher les combats d'équipe (0.0 à 1.0)
    
    # Facteurs de personnalité
    patience: float = 0.5             # Patience avant d'engager (0.0 à 1.0)
    adaptability: float = 0.7         # Capacité à s'adapter aux changements (0.0 à 1.0)
    
    # Préférences de jeu
    preferred_objectives: List[str] = None  # Objectifs préférés (dragon, baron, etc.)
    play_style: str = "balanced"      # 'early', 'mid', 'late', ou 'balanced'
    
    def __post_init__(self):
        # Initialiser les préférences d'objectifs par défaut si non spécifiées
        if self.preferred_objectives is None:
            self.preferred_objectives = ["dragon", "baron", "tower"]
        
        # Ajuster les attributs en fonction du style
        if self.style == TeamStyle.ROOKIE:
            self.aggression = 0.3
            self.risk_tolerance = 0.2
            self.objective_focus = 0.5
            self.teamfight_tendency = 0.4
            self.patience = 0.7
            self.adaptability = 0.4
            self.play_style = "balanced"
            
        elif self.style == TeamStyle.AGGRESSIVE:
            self.aggression = 0.9
            self.risk_tolerance = 0.8
            self.objective_focus = 0.8
            self.teamfight_tendency = 0.9
            self.patience = 0.3
            self.adaptability = 0.7
            self.play_style = "early"
            
        elif self.style == TeamStyle.SCALING:
            self.aggression = 0.4
            self.risk_tolerance = 0.3
            self.objective_focus = 0.9
            self.teamfight_tendency = 0.7
            self.patience = 0.9
            self.adaptability = 0.6
            self.play_style = "late"
            
        elif self.style == TeamStyle.TEAMFIGHT:
            self.aggression = 0.7
            self.risk_tolerance = 0.6
            self.objective_focus = 0.8
            self.teamfight_tendency = 1.0
            self.patience = 0.5
            self.adaptability = 0.7
            self.play_style = "mid"
            
        elif self.style == TeamStyle.SPLIT_PUSH:
            self.aggression = 0.6
            self.risk_tolerance = 0.7
            self.objective_focus = 0.5
            self.teamfight_tendency = 0.3
            self.patience = 0.6
            self.adaptability = 0.8
            self.play_style = "mid"
    
    def should_take_risk(self, risk_level: float) -> bool:
        """
        Détermine si l'équipe devrait prendre un risque donné.
        
        Args:
            risk_level: Niveau de risque (0.0 à 1.0)
            
        Returns:
            True si le risque est acceptable, False sinon
        """
        # Ajouter une petite variation aléatoire
        adjusted_risk_tolerance = self.risk_tolerance * random.uniform(0.9, 1.1)
        return risk_level <= adjusted_risk_tolerance
    
    def get_aggression_modifier(self) -> float:
        """Retourne un modificateur d'agressivité avec une petite variation aléatoire."""
        return self.aggression * random.uniform(0.8, 1.2)
    
    def get_objective_priority(self, objective_type: str) -> float:
        """
        Retourne la priorité donnée à un type d'objectif.
        
        Args:
            objective_type: Type d'objectif ('dragon', 'baron', 'tower', etc.)
            
        Returns:
            Score de priorité (0.0 à 1.0)
        """
        # Priorité de base basée sur le style
        base_priority = 0.5
        
        # Ajustements basés sur le type d'objectif
        if objective_type in self.preferred_objectives:
            base_priority += 0.3
        
        # Ajustement basé sur la phase de jeu
        if self.play_style == "early" and objective_type == "dragon":
            base_priority += 0.2
        elif self.play_style == "late" and objective_type == "baron":
            base_priority += 0.2
        
        # Retourner une valeur entre 0 et 1
        return max(0.0, min(1.0, base_priority))

# Profils prédéfinis pour une utilisation facile
TEAM_PROFILES = {
    "rookie": TeamProfile(style=TeamStyle.ROOKIE),
    "balanced": TeamProfile(style=TeamStyle.BALANCED),
    "aggressive": TeamProfile(style=TeamStyle.AGGRESSIVE),
    "scaling": TeamProfile(style=TeamStyle.SCALING),
    "teamfight": TeamProfile(style=TeamStyle.TEAMFIGHT),
    "split_push": TeamProfile(style=TeamStyle.SPLIT_PUSH),
}

def get_profile(profile_name: str) -> TeamProfile:
    """
    Récupère un profil d'équipe par son nom.
    
    Args:
        profile_name: Nom du profil ('rookie', 'aggressive', etc.)
        
    Returns:
        Un objet TeamProfile correspondant
        
    Raises:
        ValueError: Si le profil n'existe pas
    """
    profile = TEAM_PROFILES.get(profile_name.lower())
    if not profile:
        raise ValueError(f"Profil inconnu: {profile_name}. Profils disponibles: {', '.join(TEAM_PROFILES.keys())}")
    return profile
