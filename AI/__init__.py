"""
Module d'IA pour le jeu MOBAMANA.

Ce module fournit une architecture modulaire pour l'IA du jeu, avec des composants
pour la perception, la prise de décision, les tactiques de combat, etc.
"""

# Importations pour faciliter l'accès aux classes principales
from .perception import GameState, GamePhase
from .manager import AIManager, Strategy
from .objectives import Objective, ObjectiveManager
from .tactics import CombatTactics, CombatAction, TargetType, CombatDecision
from .humanizer import Humanizer, StressLevel
from .profiles import TeamProfile, TeamStyle, get_profile, TEAM_PROFILES

# Version du module
__version__ = "0.1.0"

# Liste des symboles à exporter avec "from AI import *"
__all__ = [
    # perception.py
    'GameState',
    'GamePhase',
    
    # manager.py
    'AIManager',
    'Strategy',
    
    # objectives.py
    'Objective',
    'ObjectiveManager',
    
    # tactics.py
    'CombatTactics',
    'CombatAction',
    'TargetType',
    'CombatDecision',
    
    # humanizer.py
    'Humanizer',
    'StressLevel',
    
    # profiles.py
    'TeamProfile',
    'TeamStyle',
    'get_profile',
    'TEAM_PROFILES',
]
