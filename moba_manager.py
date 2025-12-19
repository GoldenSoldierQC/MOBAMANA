from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional
import math
import random
import json

# ============================================================================
# 1. CONFIGURATION ET ÉQUILIBRAGE (GameBalance)
# ============================================================================
class Role(Enum):
    TOP = "TOP"
    JUNGLE = "JUNGLE"
    MID = "MID"
    ADC = "ADC"
    SUPPORT = "SUPPORT"

class GamePhase(Enum):
    EARLY = "Early Game"
    MID = "Mid Game"
    LATE = "Late Game"

class GameBalance:
    """Toutes les variables d'équilibrage centralisées"""
    # Probabilités
    SIGMOID_K = 0.05
    SYNERGY_WEIGHT_NORMAL = 1.0
    SYNERGY_WEIGHT_CRITICAL = 1.5
    CRITICAL_ZONE_MIN = 90
    CRITICAL_ZONE_MAX = 110
    
    # Économie
    TRANSFER_SUCCESS_CAP = 0.95
    INFLATION_RATE_BASE = 0.05
    
    # Valeurs des événements en jeu
    POINTS_KILL = 1
    POINTS_TOWER = 2
    POINTS_BARON = 5
    POINTS_ELDER = 8

STARTER_KITS = {
    "LA PÉPITE": {
        "desc": "Un prodige au MID (Elite), mais le reste est très jeune.",
        "distribution": {Role.MID: "Elite", Role.TOP: "Rookie", Role.JUNGLE: "Rookie", Role.ADC: "Rookie", Role.SUPPORT: "Rookie"}
    },
    "LE MUR": {
        "desc": "Une défense solide (Pro) sur le TOP et le SUPPORT.",
        "distribution": {Role.TOP: "Pro", Role.SUPPORT: "Pro", Role.MID: "Rookie", Role.JUNGLE: "Rookie", Role.ADC: "Rookie"}
    },
    "OFFENSIF": {
        "desc": "Une paire agressive (Pro) en JUNGLE et ADC.",
        "distribution": {Role.JUNGLE: "Pro", Role.ADC: "Pro", Role.TOP: "Rookie", Role.MID: "Rookie", Role.SUPPORT: "Rookie"}
    }
}


# ============================================================================
# 2. MODÈLES DE DONNÉES (Entities)
# ============================================================================
class Player:
    def __init__(self, name: str, age: int, role: Role, market_value: int, tier="Pro"):
        self.name = name
        self.age = age
        self.role = role
        self.market_value = market_value
        self.tier = tier
        
        # Nouvelles Aptitudes (0-100)
        self.mec = 50  # Mécaniques (Ligne / Kills)
        self.mac = 50  # Macro (Objectifs / Baron)
        self.vis = 50  # Vision (Survie / Placement)
        self.sng = 50  # Sang-froid (Clutch / Playoffs)
        
        # Maîtrise des Héros { "NomHéros": NiveauDeMaîtrise(0.8 à 1.2) }
        self.hero_mastery = {}
        
        # Statistiques de carrière
        self.kills = 0
        self.deaths = 0
        self.assists = 0
        
        # Progression
        self.xp = 0
        self.level = 1
        
        # Données du match en cours
        self.current_hero: Optional[str] = None
        self.focus = 50     # 0: Farm, 100: Fight
        self.risk = 50      # 0: Safe, 100: Aggro
        self.priority = "Lane" # "Lane", "Roam", "Obj"
        
        # Économie
        self.salary = 0 # Salaire hebdomadaire
        self.buyout_fee = 0 # Frais de transfert


    @property
    def gen(self):
        """Calcul du score général pour rester compatible avec tes anciens tests."""
        return (self.mec + self.mac + self.vis + self.sng) // 4

    def get_overall_rating(self) -> float:
        """Calcul du score général pour compatibilité"""
        return float(self.gen)

    def gain_xp(self, amount: int):
        self.xp += amount
        print(f"[XP] {self.name} a gagne {amount} XP !")
        while self.xp >= 1000:
            self.level_up()

    def level_up(self):
        self.xp -= 1000
        self.level += 1
        # Bonus de stat aléatoire
        stat_to_up = random.choice(['mec', 'mac', 'vis', 'sng'])
        current_val = getattr(self, stat_to_up)
        
        if current_val < 99:
            setattr(self, stat_to_up, current_val + 1)
            print(f"[LEVEL UP] {self.name} est niveau {self.level} (+1 {stat_to_up.upper()})")


# --- Système de Champions ---
class HeroArchetype(Enum):
    ASSASSIN = "Assassin" # Fort Early
    TANK = "Tank"         # Fort Late
    MAGE = "Mage"         # Équilibré / Mid
    MARKSMAN = "Marksman" # Très Fort Late
    BRUISER = "Bruiser"   # Constant / Early-Mid
    UTILITY = "Utility"   # Utilitaire

@dataclass
class Champion:
    name: str
    archetype: HeroArchetype
    mec: int
    mac: int
    vis: int
    sng: int
    desc: str

# Catalogue de base (Database)
CHAMPIONS_DB = {
    "Boulder": Champion("Boulder", HeroArchetype.TANK, 40, 85, 95, 60, "Un golem de pierre immense. Quasi impossible à tuer en late game."),
    "Ironclad": Champion("Ironclad", HeroArchetype.TANK, 60, 80, 90, 70, "Guerrier en armure lourde spécialisé dans l'engagement de combat."),
    "Swiftarrow": Champion("Swiftarrow", HeroArchetype.MARKSMAN, 85, 90, 35, 65, "Archère classique. Fragile mais inflige des dégâts constants."),
    "Spectre": Champion("Spectre", HeroArchetype.MARKSMAN, 50, 98, 25, 80, "Chasseur du néant. Inutile avant 20min, gagne seul après 35min."),
    "Shadowblade": Champion("Shadowblade", HeroArchetype.ASSASSIN, 95, 45, 60, 75, "Ninja létal. Excellent duelliste qui doit dominer sa ligne."),
    "Voidwalker": Champion("Voidwalker", HeroArchetype.ASSASSIN, 90, 50, 85, 80, "Mage assassin très mobile, difficile à attraper."),
    "Ignis": Champion("Ignis", HeroArchetype.MAGE, 75, 85, 50, 70, "Mage de feu. Capable d'anéantir une équipe regroupée."),
    "Chronos": Champion("Chronos", HeroArchetype.MAGE, 65, 92, 60, 85, "Mage temporel de contrôle. Excelle dans les combats longs."),
    "Vanguard": Champion("Vanguard", HeroArchetype.BRUISER, 80, 75, 75, 70, "Combattant équilibré. Bon partout, excellent nulle part."),
    "Aegis": Champion("Aegis", HeroArchetype.UTILITY, 30, 85, 85, 95, "Protectrice pure. Ne fait pas de dégâts, mais sauve ses alliés.")
}


# ============================================================================
# 1b. GESTION FINANCIÈRE (FinanceManager)
# ============================================================================
class FinanceManager:
    """Gère le compte en banque de l'organisation et les flux hebdomadaires."""
    def __init__(self, initial_budget=500000):
        self.budget = initial_budget
        self.weekly_revenue = 15000  # Sponsors de base
        self.transaction_history = []

    def process_weekly_expenses(self, players: List['Player']):
        """Déduit les salaires du budget total."""
        total_salaries = sum(p.salary for p in players)
        self.budget -= total_salaries
        self.budget += self.weekly_revenue
        log_msg = f"Semaine : -{total_salaries}$ (Salaires) | +{self.weekly_revenue}$ (Sponsors)"
        self.transaction_history.append(log_msg)
        return total_salaries

    def add_match_bonus(self, won=True):
        """Bonus financier selon le résultat du match."""
        amount = 10000 if won else 2000
        self.budget += amount
        return amount

@dataclass
class TeamStats:

    wins: int = 0
    losses: int = 0

@dataclass
class Team:
    name: str
    prestige: int
    budget: int
    coach_name: str = "Coach"
    team_color: tuple = (41, 128, 185)
    logo_shape: str = "Cercle" # Cercle, Carré, Diamant
    specialization: str = "Polyvalent" # Analyste, Motivateur, Scout, Entraîneur
    roster: Dict[Role, Optional['Player']] = field(default_factory=lambda: {role: None for role in Role})
    bench: List['Player'] = field(default_factory=list)
    stats: TeamStats = field(default_factory=TeamStats)
    finance: Optional[FinanceManager] = field(default=None, init=False)

    def __post_init__(self):
        self.finance = FinanceManager(self.budget)

    @property
    def current_budget(self):
        return self.finance.budget if self.finance else self.budget


    @property
    def players(self) -> List['Player']:
        """Retourne les titulaires (pour le match)."""
        return [p for p in self.roster.values() if p]

    @property
    def starters(self) -> List['Player']:
        """Alias pour les titulaires."""
        return self.players

    @property
    def all_players(self) -> List['Player']:
        """Retourne l'intégralité du roster incluant le banc (pour salaires)."""
        return self.starters + self.bench

    def swap_players(self, role: Role, bench_idx: int):
        """Échange un titulaire d'un poste spécifique avec un joueur du banc."""
        if not isinstance(role, Role):
            print(f"[ERROR] Rôle invalide fourni : {role}")
            return False
            
        if 0 <= bench_idx < len(self.bench):
            starter = self.roster.get(role)
            sub = self.bench[bench_idx]
            
            self.roster[role] = sub
            if starter:
                self.bench[bench_idx] = starter
            else:
                self.bench.pop(bench_idx)
            return True
        else:
            print(f"[ERROR] Index de banc invalide : {bench_idx} (Taille banc: {len(self.bench)})")
            return False


# ============================================================================
# 2b. STRATÉGIES DE JEU (Strategy)
# ============================================================================
class Strategy:
    """Classe de base pour les stratégies d'équipe"""
    name = "Base"
    # Multiplicateurs par phase : [Early, Mid, Late]
    multipliers = [1.0, 1.0, 1.0]

class AggressiveStrategy(Strategy):
    name = "Agressive (Early Game)"
    multipliers = [1.2, 1.0, 0.8] # Fort au début, tombe à la fin

class ScalingStrategy(Strategy):
    name = "Scaling (Late Game)"
    multipliers = [0.8, 1.0, 1.3] # Faible au début, monstrueux à la fin

class BalancedStrategy(Strategy):
    name = "Équilibrée"
    multipliers = [1.05, 1.05, 1.05] # Bonus léger et constant

# ============================================================================
# 3. MOTEUR DE PROBABILITÉS (ProbabilityEngine)
# ============================================================================
class ProbabilityEngine:
    """Le moteur de calcul mathématique pour les résultats aléatoires"""

    def sigmoid_win_chance(self, power_diff: float, k: float = GameBalance.SIGMOID_K) -> float:
        """
        Calcule la probabilité de victoire (0.0 à 1.0).
        Utilise la formule : 1 / (1 + e^(-k * diff))
        """
        # Protection contre les dépassements de mémoire (overflow)
        # Si l'écart est trop immense, on sature à 0.999 ou 0.001
        try:
            if k * power_diff > 20:
                return 0.999
            if k * power_diff < -20:
                return 0.001
            
            return 1 / (1 + math.exp(-k * power_diff))
        except OverflowError:
            return 1.0 if power_diff > 0 else 0.0

    def calculate_synergy_impact(self, rating: float, synergy_score: float) -> float:
        """
        Applique un bonus de synergie. 
        Si le rating est en 'Zone Critique' (90-110), la synergie est amplifiée.
        """
        is_critical = GameBalance.CRITICAL_ZONE_MIN <= rating <= GameBalance.CRITICAL_ZONE_MAX
        
        # On utilise une puissance (exponentielle) pour rendre la synergie plus impactante
        weight = GameBalance.SYNERGY_WEIGHT_CRITICAL if is_critical else GameBalance.SYNERGY_WEIGHT_NORMAL
        return synergy_score ** weight

    def calculate_transfer_success(self, price_ratio: float, team_prestige: int) -> float:
        """
        Calcule la chance qu'un joueur accepte une offre.
        - price_ratio : ce que tu proposes / sa valeur réelle
        - team_prestige : de 0 à 100
        """
        # Base de succès selon le prestige (20% de l'influence)
        prestige_factor = team_prestige / 100.0
        
        # Influence du prix (80% de l'influence)
        # Courbe logarithmique : proposer 2x le prix aide beaucoup, 
        # mais proposer 10x le prix n'aide pas 10x plus.
        if price_ratio <= 1.0:
            price_factor = price_ratio * 0.7  # Si tu sous-payes, ça chute vite
        else:
            price_factor = 0.7 + (math.log(price_ratio) * 0.25)

        # Calcul final pondéré
        chance = (price_factor * 0.8) + (prestige_factor * 0.2)
        
        # On applique le plafond (cap) de sécurité défini dans GameBalance
        return max(0.05, min(GameBalance.TRANSFER_SUCCESS_CAP, chance))


PLAYER_PSEUDONYM_POOL = [
    "Nova", "Riven", "Kairo", "Sora", "Vex", "Nyx", "Astra", "Blitz", "Keen", "Jett",
    "Rook", "Pulse", "Echo", "Frost", "Viper", "Raze", "Shade", "Iris", "Grit", "Riot",
    "SilentWolf", "IronMind", "StormRider", "NeonKnight", "CrimsonFox", "RapidTempo",
    "LunarVanguard", "HyperSage", "VoidCaptain", "PrimeVector", "ArcticStride", "ShadowCircuit",
    "Nordik", "Caribou", "BleuNuit", "ZeroTilt", "MidDiff", "GankPlz", "FarmLord", "Objectif",
]


def generate_realistic_pseudonym() -> str:
    if random.random() < 0.75:
        base = random.choice(PLAYER_PSEUDONYM_POOL)
        if random.random() < 0.20:
            return f"{base}{random.randint(2, 9)}"
        if random.random() < 0.10:
            return f"{base}X"
        return base

    left = ["Shadow", "Neon", "Iron", "Lunar", "Arctic", "Crimson", "Silent", "Swift", "Prime", "Void"]
    right = ["Blade", "Wolf", "Rider", "Knight", "Fox", "Sage", "Vanguard", "Circuit", "Tempo", "Vector"]
    nick = f"{random.choice(left)}{random.choice(right)}"
    if random.random() < 0.15:
        nick = nick.replace("o", "0").replace("i", "1")
    return nick

# ============================================================================
# 4. OUTILS DE CALIBRATION (CalibrationTools)
# ============================================================================
class CalibrationTools:
    """Générateur de joueurs et d'équipes basés sur des paliers (tiers)"""
    
    TIER_CONFIG = {
        "rookie": {"min": 60, "max": 75, "price": (20000, 80000)},
        "pro": {"min": 72, "max": 85, "price": (150000, 400000)},
        "elite": {"min": 82, "max": 92, "price": (600000, 1500000)},
        "superstar": {"min": 90, "max": 99, "price": (2000000, 5000000)}
    }

    @staticmethod
    def generate_balanced_player(role: Role, tier: str) -> Player:
        """Alias pour maintenir la compatibilité avec le reste du code"""
        return CalibrationTools.generate_player(role, tier)

    @staticmethod
    def generate_player(role: Role, tier="Pro") -> Player:
        # Normalisation du tier (minuscule pour la config)
        t_key = tier.lower()
        config = CalibrationTools.TIER_CONFIG.get(t_key, CalibrationTools.TIER_CONFIG["rookie"])
        low, high = config["min"], config["max"]
        
        # Calcul du prix
        price = random.randint(config["price"][0], config["price"][1])
        name = generate_realistic_pseudonym()
        
        player = Player(
            name=name,
            age=random.randint(17, 28),
            role=role,
            market_value=price,
            tier=tier.capitalize()
        )
        
        # Distribution aléatoire pour créer des profils uniques
        # Chaque stat est tirée indépendamment pour favoriser la variété
        player.mec = random.randint(low, high)
        player.mac = random.randint(low, high)
        player.vis = random.randint(low, high)
        player.sng = random.randint(low, high)
        
        # Calcul du salaire basé sur le Tier et le Niveau
        salary_map = {"Rookie": 1000, "Pro": 5000, "Elite": 12000, "Superstar": 25000}
        player.salary = salary_map.get(player.tier, 5000) + (player.level * 200)
        
        # Le rachat du contrat (Buyout) est estimé à 6 mois de salaire
        player.buyout_fee = player.salary * 26
        
        return player


def _apply_specialization_bonuses(team: 'Team', specialization: str):
    """
    Applique des bonus de statistiques selon la spécialisation du coach.
    """
    bonus_map = {
        "Analyste": {"vis": 10, "mac": 5},
        "Motivateur": {"sng": 10, "mec": 5},
        "Scout": {"mec": 5, "mac": 5, "vis": 5, "sng": 5},
        "Entraîneur": {"mec": 3, "mac": 3, "vis": 3, "sng": 3},
        "Polyvalent": {"mec": 2, "mac": 2, "vis": 2, "sng": 2}
    }
    
    bonuses = bonus_map.get(specialization, {})
    
    for player in team.roster.values():
        if player:
            for stat, bonus in bonuses.items():
                current_value = getattr(player, stat)
                setattr(player, stat, min(99, current_value + bonus))


def create_initial_roster(team_name: str, coach_name: str, color: tuple, specialization: str = "Polyvalent", prestige: int = 70, budget: int = None, kit_name: str = "LA PÉPITE") -> 'Team':
    """
    Crée une équipe initiale avec un Starter Pack.
    
    Args:
        team_name: Nom de l'équipe
        coach_name: Nom du coach
        color: Couleur de l'équipe
        specialization: Spécialisation du coach (pour les bonus)
        prestige: Prestige initial
        budget: Budget initial
        kit_name: Nom du Starter Kit à utiliser
    
    Returns:
        Team: L'équipe créée avec son roster initial
    """
    specialization_budgets = {
        "Polyvalent": 1_000_000, "Analyste": 900_000, "Motivateur": 950_000,
        "Scout": 1_100_000, "Entraîneur": 850_000
    }
    
    if budget is None:
        budget = specialization_budgets.get(specialization, 1_000_000)
    
    new_team = Team(team_name, prestige=prestige, budget=budget, coach_name=coach_name, team_color=color, specialization=specialization)
    
    # Utilisation du Starter Kit pour générer le roster
    kit = STARTER_KITS.get(kit_name, STARTER_KITS["LA PÉPITE"])
    distribution = kit["distribution"]
    
    for role, tier in distribution.items():
        new_team.roster[role] = CalibrationTools.generate_player(role, tier)
    
    # Application des bonus de spécialisation du coach
    _apply_specialization_bonuses(new_team, specialization)
    
    return new_team


def generate_league_teams(exclude_name: str, count: int = 7) -> List['Team']:
    """Génère des équipes rivales avec des noms réels et des niveaux variés."""
    rival_pool = [
        ("Fnatic", 82, (255, 152, 0)),        # Orange
        ("Cloud9", 80, (0, 174, 243)),       # Bleu ciel
        ("T1", 95, (226, 0, 52)),            # Rouge Coréen
        ("Gen.G", 93, (170, 140, 0)),        # Or
        ("Vitality", 78, (255, 255, 0)),     # Jaune
        ("Karmine Corp", 75, (0, 71, 171)),  # Bleu royal
        ("Team Liquid", 85, (10, 30, 60)),   # Bleu Marine
        ("FlyQuest", 72, (0, 100, 50))       # Vert
    ]
    
    teams = []
    random.shuffle(rival_pool)  # Pour ne pas avoir toujours les mêmes si on limite le nombre
    
    for i in range(min(count, len(rival_pool))):
        name, prestige, color = rival_pool[i]
        if name == exclude_name: 
            continue  # Évite les doublons
        
        # On définit un "style" de recrutement pour l'IA rivale
        # (Elite pour les grosses écuries, Pro/Rookie pour les petites)
        tier = "elite" if prestige > 85 else "pro" if prestige > 75 else "rookie"
        
        # Création de l'équipe avec les paramètres définis
        t = Team(
            name=name,
            prestige=prestige,
            budget=random.randint(500000, 2000000),
            team_color=color
        )
        
        # Remplissage du roster selon le tier choisi
        for role in Role:
            t.roster[role] = CalibrationTools.generate_player(role, tier)
            
        teams.append(t)
    return teams


# ============================================================================
# 5. MARCHÉ DES TRANSFERTS (TransferMarket)
# ============================================================================
class TransferMarket:
    """Gère la liste des joueurs disponibles et les transactions"""
    
    def __init__(self):
        self.engine = ProbabilityEngine()
        self.available_players: List[Player] = []
        self.transfer_history = []
        self.refresh_market()

    def refresh_market(self):
        """Génère un nouveau catalogue de talents avec un mix de Tiers."""
        self.available_players = []
        roles = [Role.TOP, Role.JUNGLE, Role.MID, Role.ADC, Role.SUPPORT]
        
        # On définit le mix de tiers souhaité
        tiers_to_gen = ["Rookie"]*5 + ["Pro"]*5 + ["Elite"]*3 + ["Superstar"]*1
        
        for tier in tiers_to_gen:
            role = random.choice(roles)
            p = CalibrationTools.generate_player(role, tier)
            # Prix d'achat = (Salaire annuel estimé / 2)
            p.buyout_fee = p.salary * 26 
            self.available_players.append(p)

    def buy_player(self, player_index, finance_manager):
        """Gère la transaction financière et l'ajout au marché des transferts."""
        if 0 <= player_index < len(self.available_players):
            player = self.available_players[player_index]
            if finance_manager.budget >= player.buyout_fee:
                finance_manager.budget -= player.buyout_fee
                # On retire le joueur du marché
                return self.available_players.pop(player_index)
        return None

    def list_player(self, player: Player):
        if player not in self.available_players:
            self.available_players.append(player)

    def scout_players(self, role: Optional[Role] = None, max_price: Optional[int] = None) -> List[Player]:
        """Filtre le marché selon vos besoins"""
        results = self.available_players
        if role:
            results = [p for p in results if p.role == role]
        if max_price:
            results = [p for p in results if p.market_value <= max_price]
        return results

    def attempt_transfer(self, buying_team: Team, player: Player, offer_amount: int) -> bool:
        """Logique de négociation"""
        # 1. Vérifier le budget
        if offer_amount > buying_team.budget:
            return False
        
        # 2. Calculer le ratio de l'offre
        price_ratio = offer_amount / player.market_value
        
        # 3. Calculer la probabilité de succès via l'Engine
        success_chance = self.engine.calculate_transfer_success(price_ratio, buying_team.prestige)
        
        if random.random() < success_chance:
            # Transfert réussi
            buying_team.budget -= offer_amount
            buying_team.roster[player.role] = player
            if player in self.available_players:
                self.available_players.remove(player)
            
            self.transfer_history.append({
                "player": player.name,
                "team": buying_team.name,
                "price": offer_amount
            })
            return True
            
# 6. SIMULATEUR DE MATCH (MatchSimulator)
# ============================================================================
class MatchSimulator:
    """Simule un match complet entre deux équipes"""
    
    EVENT_VALUES = {
        "KILL": {"points": GameBalance.POINTS_KILL, "label": "Kill"},
        "TOWER": {"points": GameBalance.POINTS_TOWER, "label": "Tour"},
        "BARON": {"points": GameBalance.POINTS_BARON, "label": "Baron"},
        "ELDER": {"points": GameBalance.POINTS_ELDER, "label": "Dragon Ancestral"},
        "STEAL": {"points": GameBalance.POINTS_BARON + 2, "label": "STEAL ÉPIQUE !"}
    }

    def __init__(self, team_blue: Team, team_red: Team):
        self.blue = team_blue
        self.red = team_red
        self.team_a = team_blue # Alias
        self.team_b = team_red  # Alias
        self.engine = ProbabilityEngine()
        self.blue_strategy = BalancedStrategy()
        self.red_strategy = BalancedStrategy()

        self.scores = {"blue": 0, "red": 0}
        self.kills_a = 0
        self.kills_b = 0
        self.gold_a = 0
        self.gold_b = 0
        self.log = []
        self.logs = [] # Alias plural pour le GUI

        self.current_minute = 0
        self.max_minutes = 30
        self.is_finished = False
        self.winner = None # "A" ou "B"

        # Picks par défaut
        self.blue_picks = {role: random.choice(list(CHAMPIONS_DB.values())) for role in Role}
        self.red_picks = {role: random.choice(list(CHAMPIONS_DB.values())) for role in Role}

        # Assigner les héros aux joueurs pour le match
        for role, p in self.blue.roster.items():
            if p:
                p.current_hero = self.blue_picks[role].name
        for role, p in self.red.roster.items():
            if p:
                p.current_hero = self.red_picks[role].name

        # Tactiques globales (influencables par l'UI)
        # aggro: 0.5 (safe) à 1.5 (agressive)
        # focus: 0.5 (farm) à 1.5 (macro/obj)
        self.blue_tactics = {"aggro": 1.0, "focus": 1.0}
        self.red_tactics = {"aggro": 1.0, "focus": 1.0}

        self.ai_brain = {
            "prev_gold_diff": 0,
            "current_strategy": "DEF",
            "weights": {"AGGRO": 1.0, "DEF": 1.0}
        }

    def set_strategies(self, blue_strat: Strategy, red_strat: Strategy):
        self.blue_strategy = blue_strat
        self.red_strategy = red_strat

    # ...

    def simulate_step(self):
        """Simule une minute de jeu avec Logique Tactique"""
        if self.is_finished:
            return
            
        self.current_minute += 1
        phase_idx = 0 if self.current_minute <= 10 else 1 if self.current_minute <= 20 else 2
        phase = GamePhase.EARLY if phase_idx == 0 else GamePhase.MID if phase_idx == 1 else GamePhase.LATE
            
        blue_power = self._calculate_team_power(self.blue, self.blue_strategy, phase_idx, self.blue_tactics)
        red_power = self._calculate_team_power(self.red, self.red_strategy, phase_idx, self.red_tactics)
        win_chance = self.engine.sigmoid_win_chance(blue_power - red_power)
        
        # 1. Fréquence des événements influencée par l'Agressivité
        # Base 0.3, influencée par la moyenne d'aggro des deux équipes
        aggro_total = (self.blue_tactics["aggro"] + self.red_tactics["aggro"]) / 2
        if random.random() < 0.3 * aggro_total:
            winner_key = "blue" if random.random() < win_chance else "red"
            tactics = self.blue_tactics if winner_key == "blue" else self.red_tactics
            
            # 2. Type d'événement influencé par la Phase et le Focus
            # Phase influence les poids de base
            if phase == GamePhase.EARLY:
                base_weights = {"KILL": 0.7, "TOWER": 0.3, "BARON": 0.0, "ELDER": 0.0, "STEAL": 0.0}
            elif phase == GamePhase.MID:
                base_weights = {"KILL": 0.5, "TOWER": 0.4, "BARON": 0.1, "ELDER": 0.0, "STEAL": 0.01}
            else: # LATE
                base_weights = {"KILL": 0.3, "TOWER": 0.4, "BARON": 0.2, "ELDER": 0.1, "STEAL": 0.03}

            # Application des multiplicateurs tactiques
            weights = {
                "KILL": base_weights["KILL"] * tactics["aggro"],
                "TOWER": base_weights["TOWER"] * tactics["focus"]
            }
            if base_weights["BARON"] > 0:
                weights["BARON"] = base_weights["BARON"] * tactics["focus"]
            if base_weights["ELDER"] > 0:
                weights["ELDER"] = base_weights["ELDER"] * tactics["focus"]
            if base_weights["STEAL"] > 0:
                weights["STEAL"] = base_weights["STEAL"] # Les steals sont purement aléatoires

            # Sélection pondérée simplifiée
            et = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
                
            points = self.EVENT_VALUES[et]["points"]
            self.scores[winner_key] += points
            
            if et == "KILL":
                if winner_key == "blue":
                    self.kills_a += 1
                else:
                    self.kills_b += 1
                all_allies = self.blue.players if winner_key == "blue" else self.red.players
                if not all_allies:
                    return # Protection
                killer = random.choice(all_allies)
                killer.kills += 1
                teammates = [p for p in all_allies if p != killer]
                if teammates:
                    random.choice(teammates).assists += 1
                victim = random.choice(self.red.players if winner_key == "blue" else self.blue.players)
                victim.deaths += 1
                
            # Mise à jour de l'or (approx: 1 point = 300 gold)
            if winner_key == "blue":
                self.gold_a += points * 300
            else:
                self.gold_b += points * 300

            # Création du message structuré
            team_letter = "A" if winner_key == "blue" else "B"
            event_type = "KILL" if et == "KILL" else "OBJECTIVE"
            location_role = "MID"
            
            if et == "KILL":
                msg = f"{killer.name} a elimine un adversaire !"
                location_role = getattr(getattr(killer, "role", None), "name", "MID")
            else:
                msg = f"L'equipe {'bleue' if winner_key == 'blue' else 'rouge'} a pris un objectif ({self.EVENT_VALUES[et]['label']})."

                if et == "TOWER":
                    location_role = random.choice(["TOP", "MID", "BOT"])
                elif et in {"BARON", "ELDER", "STEAL"}:
                    location_role = "JUNGLE"

            self.logs.append({
                "type": event_type,
                "team": team_letter,
                "minute": self.current_minute,
                "msg": f"[{self.current_minute}'] {msg}",
                "event_subtype": et,
                "location_role": location_role,
            })

        # 3. L'IA adapte ses tactiques toutes les 3 minutes
        if self.current_minute % 3 == 0:
            self.update_ai_tactics()

        if self.current_minute >= self.max_minutes:
            self.is_finished = True
            self.winner = "A" if self.scores["blue"] >= self.scores["red"] else "B"
            distribute_match_rewards(self)



    def update_ai_tactics(self):
        """L'IA apprend de sa dernière tactique et choisit la plus efficace (Équipe Rouge / Team B)."""
        self.evaluate_strategy()

        w_aggro = float(self.ai_brain["weights"].get("AGGRO", 1.0))
        w_def = float(self.ai_brain["weights"].get("DEF", 1.0))

        if w_aggro > w_def:
            self.red_tactics = {"aggro": 1.4, "focus": 0.7}
            self.ai_brain["current_strategy"] = "AGGRO"
            self.logs.append({"type": "TACTIC", "team": "B", "minute": self.current_minute, "msg": "L'IA choisit AGGRO."})
        else:
            self.red_tactics = {"aggro": 0.7, "focus": 1.4}
            self.ai_brain["current_strategy"] = "DEF"
            self.logs.append({"type": "TACTIC", "team": "B", "minute": self.current_minute, "msg": "L'IA choisit DEF."})

    def evaluate_strategy(self):
        current_diff = self.gold_b - self.gold_a
        reward = current_diff - self.ai_brain["prev_gold_diff"]

        strat = self.ai_brain["current_strategy"]
        if strat not in self.ai_brain["weights"]:
            self.ai_brain["weights"][strat] = 1.0

        if reward > 0:
            self.ai_brain["weights"][strat] += 0.1
        else:
            self.ai_brain["weights"][strat] -= 0.1

        self.ai_brain["weights"][strat] = max(0.1, self.ai_brain["weights"][strat])
        self.ai_brain["prev_gold_diff"] = current_diff

    def get_mvp(self):
        """Calcule le MVP basé sur le score de performance (KDA + Impact)."""
        all_players = self.blue.players + self.red.players
        # Formule : (Kills * 2 + Assists) - (Deaths)
        return max(all_players, key=lambda p: (p.kills * 2 + p.assists) - p.deaths)

    def print_match_logs(self):
        """Affiche les logs du match de manière lisible pour la console."""
        print(f"\n--- MATCH : {self.blue.name} vs {self.red.name} ---")
        for log in self.logs:
            team_label = "BLEU" if log['team'] == "A" else "ROUGE"
            print(f"[{team_label}] {log['msg']}")
        print(f"SCORE FINAL : {self.scores['blue']} - {self.scores['red']}")
        mvp = self.get_mvp()
        print(f"⭐ MVP : {mvp.name} ({mvp.current_hero})")

    def _calculate_team_power(self, team: Team, strategy: Strategy, phase_idx: int, tactics: dict = None) -> float:
        """Calcule la puissance réelle d'une équipe avec la logique des champions et tactiques"""
        if tactics is None: 
            tactics = {"aggro": 1.0, "focus": 1.0}
        
        # Optimisation : sortir les valeurs de tactiques pour éviter les accès répétés au dictionnaire
        aggro = tactics.get("aggro", 1.0)
        focus = tactics.get("focus", 1.0)
        inv_aggro = 1.0 / aggro if aggro != 0 else 1.0
        
        is_blue = (team == self.blue)
        picks = self.blue_picks if is_blue else self.red_picks
        
        total_sp = 0
        count = 0

        # Multiplicateurs de spécialisation du Coach
        spec_mec = 1.05 if team.specialization == "Entraîneur" else 1.0
        spec_mac = 1.05 if team.specialization == "Analyste" else 1.0
        spec_vis = 1.05 if team.specialization == "Scout" else 1.0
        spec_sng = 1.05 if team.specialization == "Motivateur" else 1.0

        for role, player in team.roster.items():
            if player:
                champion = picks[role]
                
                # Accès direct aux stats du joueur avec bonus tactiques et coach
                p_mec = player.mec * aggro * spec_mec
                p_mac = player.mac * focus * spec_mac
                p_vis = player.vis * inv_aggro * spec_vis
                p_sng = player.sng * spec_sng
                
                if phase_idx == 0: # EARLY
                    stats_base = p_mec * 0.8 + p_mac * 0.2
                    mod_hero = champion.mec * 0.01
                elif phase_idx == 1: # MID
                    stats_base = (p_mec + p_mac + p_vis) * 0.3333
                    mod_hero = (champion.mec + champion.mac + champion.vis) * 0.003333
                else: # LATE
                    # On inclut le Sang-froid (SNG) dans le calcul du Late Game
                    stats_base = p_mec * 0.2 + p_mac * 0.5 + p_sng * 0.3
                    mod_hero = champion.mac * 0.01
                
                # Score Sp = (Stats_Base * Mod_Hero) * Maîtrise
                mastery = player.hero_mastery.get(champion.name, 1.0)
                total_sp += (stats_base * mod_hero) * mastery
                count += 1

        if count == 0:
            return 10.0
            
        base_power = total_sp / 5
        
        # 4. Application de la synergie
        synergy_impact = self.engine.calculate_synergy_impact(base_power, 1.1)
        
        # 5. Application du multiplicateur de stratégie
        strat_mult = strategy.multipliers[phase_idx]
        
        return base_power * synergy_impact * strat_mult


    def _simulate_phase(self, phase: GamePhase, phase_idx: int):
        """Simule une des trois phases du match"""
        blue_power = self._calculate_team_power(self.blue, self.blue_strategy, phase_idx)
        red_power = self._calculate_team_power(self.red, self.red_strategy, phase_idx)
        
        # Chance de gagner des événements dans cette phase
        win_chance = self.engine.sigmoid_win_chance(blue_power - red_power)
        
        # On simule 3 événements majeurs par phase
        events_this_phase = []
        for _ in range(3):
            # Qui gagne l'événement ?
            winner = "blue" if random.random() < win_chance else "red"
            
            # Quel type d'événement ? (Plus d'objectifs en Late Game)
            if phase == GamePhase.LATE and random.random() > 0.6:
                event_type = random.choice(["BARON", "ELDER"])
            else:
                event_type = random.choice(["KILL", "TOWER"])
                
            points = self.EVENT_VALUES[event_type]["points"]
            self.scores[winner] += points
            
            event_data = {
                "phase": phase.value,
                "winner": winner,
                "type": self.EVENT_VALUES[event_type]["label"],
                "points": points
            }
            events_this_phase.append(event_data)
            self.log.append(event_data)
            
        return events_this_phase

    def run_full_match(self) -> dict:
        """Exécute la simulation complète minute par minute"""
        while not self.is_finished:
            self.simulate_step()
            
        match_data = {}
        # Détermination du vainqueur
        if self.scores["blue"] >= self.scores["red"]:
            winner_name = "blue"
        else:
            winner_name = "red"
            
        match_data["winner"] = winner_name
        match_data["blue_score"] = self.scores["blue"]
        match_data["red_score"] = self.scores["red"]
        match_data["phases"] = [{"name": "Early"}, {"name": "Mid"}, {"name": "Late"}] # Pour compatibilité tests

        
        return match_data


# ============================================================================
# 7. LIGUE ET SAISON (League)
# ============================================================================
class League:
    """Gère une saison complète avec plusieurs équipes"""
    
    def __init__(self, name: str, teams: List[Team]):
        self.name = name
        self.teams = teams
        self.market = TransferMarket()
        self.standings = {team.name: {"wins": 0, "losses": 0} for team in teams}
        self.calendar = []

    def create_round_robin_schedule(self):
        """Génère un calendrier où chaque équipe affronte toutes les autres"""
        self.calendar = []
        for i, team_a in enumerate(self.teams):
            for team_b in self.teams[i+1:]:
                self.calendar.append((team_a, team_b))
        random.shuffle(self.calendar)

    def run_season(self):
        """Simule tous les matchs du calendrier"""
        for team_blue, team_red in self.calendar:
            sim = MatchSimulator(team_blue, team_red)
            # On peut varier les stratégies aléatoirement pour les IA
            sim.set_strategies(BalancedStrategy(), BalancedStrategy())
            
            result = sim.run_full_match()
            sim.print_match_logs()
            self.distribute_rewards(sim)
            winner_key = result["winner"] # "blue" ou "red"
            
            if winner_key == "blue":
                self._update_result(team_blue, team_red)
            else:
                self._update_result(team_red, team_blue)
            
            # Une itération de match = Une semaine de dépenses
            self.process_week()

    def distribute_rewards(self, match: 'MatchSimulator'):
        """Distribue l'XP aux joueurs à la fin d'un match."""
        distribute_match_rewards(match)

    def process_week(self):
        """Calcule les revenus et dépenses pour toutes les équipes de la ligue."""
        print("\n🗓️  Fin de semaine : Traitement des finances...")
        for team in self.teams:
            team.finance.process_weekly_expenses(team.all_players)
            
            # Événements aléatoires (20% de chance par équipe)
            if random.random() < 0.2:
                self._trigger_random_event(team)
                
            if team.finance.budget <= 0:
                print(f"⚠️  ALERTE : {team.name} est en difficulté financière ! (Solde : {team.finance.budget}$)")

    def _trigger_random_event(self, team: Team):
        """Déclenche un événement aléatoire impactant une équipe."""
        events = [
            ("SPONSOR_BONUS", "Un sponsor local offre un bonus !", lambda t: t.finance.__setattr__('budget', t.finance.budget + 5000)),
            ("INTENSIVE_TRAINING", "Entraînement intensif : l'équipe gagne de l'XP !", self._event_xp_boost),
            ("SICKNESS", "Un joueur de l'équipe est tombé malade...", self._event_sickness),
            ("GEAR_UPGRADE", "Nouveau matériel gaming ! Boost de motivation.", self._event_motivation_boost)
        ]
        
        evt_type, msg, effect = random.choice(events)
        print(f"🎲 ÉVÉNEMENT [{team.name}] : {msg}")
        effect(team)

    def _event_xp_boost(self, team: Team):
        for p in team.all_players:
            p.gain_xp(150)

    def _event_sickness(self, team: Team):
        # Un joueur au hasard perd temporairement un peu de stats (ici on simplifie en baisse permanente pour le proto)
        players = team.all_players
        if players:
            p = random.choice(players)
            stat = random.choice(["mec", "mac", "vis", "sng"])
            old_val = getattr(p, stat)
            setattr(p, stat, max(40, old_val - 5))
            print(f"   > {p.name} est affaibli (-5 en {stat.upper()})")

    def _event_motivation_boost(self, team: Team):
        for p in team.all_players:
            p.sng = min(100, p.sng + 3)
        print("   > Toute l'équipe gagne +3 en SNG (Sang-froid)")


    def _update_result(self, winner: Team, loser: Team):
        """Met à jour les objets Team et le classement de la Ligue"""
        winner.stats.wins += 1
        loser.stats.losses += 1
        self.standings[winner.name]["wins"] += 1
        self.standings[loser.name]["losses"] += 1

    def get_rankings(self):
        """Retourne le classement trié par nombre de victoires"""
        return sorted(self.standings.items(), key=lambda x: x[1]["wins"], reverse=True)

    def advance_season(self):
        """Prépare la saison suivante : vieillissement, progression et inflation"""
        for team in self.teams:
            for player in team.all_players:
                # 1. Vieillissement
                player.age += 1
                
                # 2. Évolution des stats (Progression/Déclin)
                # Les jeunes ( < 23 ans) progressent, les vieux déclinent
                if player.age < 23:
                    growth = random.randint(1, 3)
                elif player.age > 26:
                    growth = random.randint(-4, -1)
                else:
                    growth = random.randint(-1, 1)
                
                # Application du changement aux aptitudes
                player.mec = max(40, min(100, player.mec + growth))
                player.mac = max(40, min(100, player.mac + growth))
                player.vis = max(40, min(100, player.vis + growth))
                player.sng = max(40, min(100, player.sng + growth))
                
                # 3. Mise à jour de la valeur marchande (Inflation/Dépréciation)
                if growth > 0:
                    player.market_value = int(player.market_value * (1 + GameBalance.INFLATION_RATE_BASE))
                else:
                    player.market_value = int(player.market_value * 0.9)

        # 4. Rafraîchissement du marché des transferts
        self.market.refresh_market()
        print("\n🔄 Le marché des transferts a été rafraîchi !")


    def run_playoffs(self):
        """Simule un tournoi à élimination directe pour le Top 4"""
        rankings = self.get_rankings()
        if len(rankings) < 4:
            print("Pas assez d'équipes pour les playoffs.")
            return
            
        # 1. Sélection des noms des 4 meilleures équipes
        top_4_names = [rankings[i][0] for i in range(4)]
        # Récupération des objets Team correspondants
        top_teams = [t for t in self.teams if t.name in top_4_names]
        # Tri pour s'assurer de l'ordre (1er vs 4ème, 2ème vs 3ème)
        top_teams.sort(key=lambda t: self.standings[t.name]["wins"], reverse=True)

        print("\n--- DEBUT DES PLAYOFFS ---")
        
        # 2. Demi-finales (BO1 pour rester simple)
        def play_knockout(t1, t2, label):
            sim = MatchSimulator(t1, t2)
            res = sim.run_full_match()
            sim.print_match_logs()
            self.distribute_rewards(sim)
            # Une itération de match = Une semaine de dépenses
            self.process_week()
            winner = t1 if res["winner"] == "blue" else t2
            print(f"{label} : {t1.name} vs {t2.name} -> VAINQUEUR : {winner.name}")
            return winner

        sf1_winner = play_knockout(top_teams[0], top_teams[3], "Demi-finale 1")
        sf2_winner = play_knockout(top_teams[1], top_teams[2], "Demi-finale 2")

        # 3. Grande Finale
        print("\n--- GRANDE FINALE ---")
        champion = play_knockout(sf1_winner, sf2_winner, "Finale")

        # 4. Récompenses
        print(f"[{champion.name}] remporte le titre !")
        champion.finance.budget += 500000
        champion.prestige = min(100, champion.prestige + 5)
        return champion.name

def save_game(league: League, filename="savegame.json"):
    """Convertit les données de la ligue en JSON et les sauvegarde dans un fichier."""
    data = {
        "league_name": league.name,
        "standings": league.standings,
        "teams": []
    }
    
    for team in league.teams:
        def serialize_player(p):
            if not p:
                return None
            return {
                "name": p.name,
                "age": p.age,
                "market_value": p.market_value,
                "tier": p.tier,
                "stats": {
                    "mec": p.mec,
                    "mac": p.mac,
                    "vis": p.vis,
                    "sng": p.sng,
                    "hero_mastery": p.hero_mastery,
                    "kills": p.kills,
                    "deaths": p.deaths,
                    "assists": p.assists,
                    "xp": p.xp,
                    "level": p.level,
                    "salary": p.salary,
                    "buyout_fee": p.buyout_fee
                }
            }

        team_data = {
            "name": team.name,
            "prestige": team.prestige,
            "budget": team.finance.budget if team.finance else team.budget,
            "roster": {role.name: serialize_player(p) for role, p in team.roster.items()},
            "bench": [serialize_player(p) for p in team.bench]
        }
        data["teams"].append(team_data)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"\n✅ Partie sauvegardée sous '{filename}' !")

def load_game(filename="savegame.json") -> Optional[League]:
    """Charge les données depuis un fichier JSON et reconstruit les objets du jeu."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        def deserialize_player(p_data, role=Role.MID):
            if not p_data:
                return None
            player = Player(
                name=p_data["name"],
                age=p_data["age"],
                role=role,
                market_value=p_data["market_value"],
                tier=p_data.get("tier", "Pro")
            )
            s = p_data["stats"]
            player.mec = s.get("mec", 50)
            player.mac = s.get("mac", 50)
            player.vis = s.get("vis", 50)
            player.sng = s.get("sng", 50)
            player.hero_mastery = s.get("hero_mastery", {})
            player.kills = s.get("kills", 0)
            player.deaths = s.get("deaths", 0)
            player.assists = s.get("assists", 0)
            player.xp = s.get("xp", 0)
            player.level = s.get("level", 1)
            player.salary = s.get("salary", 0)
            player.buyout_fee = s.get("buyout_fee", 0)
            return player

        teams = []
        for t_data in data["teams"]:
            team = Team(t_data["name"], t_data["prestige"], t_data["budget"])
            for role_name, p_data in t_data["roster"].items():
                team.roster[Role[role_name]] = deserialize_player(p_data, Role[role_name])
            
            if "bench" in t_data:
                team.bench = [deserialize_player(p_data) for p_data in t_data["bench"]]

            teams.append(team)
            
        league = League(data["league_name"], teams)
        league.standings = data["standings"]
        print("\n📂 Partie chargée avec succès !")
        return league
    except FileNotFoundError:
        print("\n❌ Aucun fichier de sauvegarde trouvé.")
        return None

# ============================================================================
# 8. BOUCLE DE JEU (Game Loop)
# ============================================================================
def game_loop():
    print("=== WELCOME TO MOBA TEAM MANAGER 2025 ===")
    
    # 1. Initialisation du monde
    all_teams = [
        Team("Karmine Corp", prestige=75, budget=500000),
        Team("G2 Esports", prestige=90, budget=1200000),
        Team("T1", prestige=98, budget=2000000),
        Team("Team Heretics", prestige=65, budget=400000)
    ]
    
    # Remplissage automatique des équipes avec des joueurs PRO
    for team in all_teams:
        for role in Role:
            team.roster[role] = CalibrationTools.generate_balanced_player(role, "pro")
            
    league = League("World Championship", all_teams)
    
    # 2. Choix de l'équipe par l'utilisateur
    print("\nChoisissez votre équipe :")
    for i, t in enumerate(all_teams):
        print(f"[{i}] {t.name} (Prestige: {t.prestige}, Budget: {t.budget:,}€)")
    
    user_team = None
    while user_team is None:
        try:
            choice_str = input("\nNuméro de l'équipe : ")
            if not choice_str.isdigit():
                print("Veuillez entrer un nombre valide.")
                continue
            choice = int(choice_str)
            if 0 <= choice < len(all_teams):
                user_team = all_teams[choice]
            else:
                print(f"Veuillez choisir un nombre entre 0 et {len(all_teams)-1}.")
        except (ValueError, IndexError):
            print("Entrée invalide.")

    print(f"\nFélicitations ! Vous êtes le nouveau manager de {user_team.name}.")

    # 3. Boucle principale
    while True:
        print(f"\n--- {user_team.name} | Budget: {user_team.budget}€ ---")
        print("[1] Roster [2] Marché [3] Saison [4] Classement")
        print("[5] New Season [6] Sauvegarder [7] Charger [0] Quitter")
        
        act = input("\nChoix : ")
        
        if act == "1":
            for role, p in user_team.roster.items():
                rating = p.stats.get_overall_rating() if p else 0
                print(f"{role.value}: {p.name if p else 'VIDE'} | Rating: {rating:.1f} | Age: {p.age if p else 'N/A'}")
        
        elif act == "2":
            # Simulation rapide du marché
            print("\nJoueurs disponibles :")
            market_players = [CalibrationTools.generate_balanced_player(random.choice(list(Role)), "elite") for _ in range(3)]
            for i, p in enumerate(market_players):
                print(f"[{i}] {p.name} ({p.role.value}) - Rating: {p.stats.get_overall_rating():.1f} | Prix: {p.market_value}€")
            
            buy_choice = input("\nAcheter un joueur (numéro) ou [Retour]: ")
            if buy_choice.isdigit():
                idx = int(buy_choice)
                if 0 <= idx < len(market_players):
                    p_to_buy = market_players[idx]
                    try:
                        offer_str = input(f"Votre offre pour {p_to_buy.name} (Valeur: {p_to_buy.market_value:,}€) : ")
                        if offer_str.isdigit():
                            offer = int(offer_str)
                            if league.market.attempt_transfer(user_team, p_to_buy, offer):
                                print("TRANSFERT RÉUSSI !")
                            else:
                                print("TRANSFERT ÉCHOUÉ.")
                        else:
                            print("Montant invalide.")
                    except ValueError:
                        print("Erreur lors de la saisie de l'offre.")
                else:
                    print("Index de joueur invalide.")

        elif act == "3":
            print("\nSimulation de la saison régulière...")
            league.create_round_robin_schedule()
            league.run_season()
            print("Saison régulière terminée !")
            
            # Lancement automatique des Playoffs
            input("\nAppuyez sur Entrée pour lancer les PLAYOFFS...")
            league.run_playoffs()
            
        elif act == "4":
            print("\n=== CLASSEMENT ===")
            rankings = league.get_rankings()
            for name, stats in rankings:
                print(f"{name}: {stats['wins']}V - {stats['losses']}D")

        elif act == "5":
            league.advance_season()
            print("\nLes joueurs ont vieilli. Les statistiques ont évolué.")

        elif act == "6":
            try:
                save_game(league)
            except Exception as e:
                print(f"Erreur lors de la sauvegarde : {e}")

        elif act == "7":
            try:
                loaded_league = load_game()
                if loaded_league:
                    league = loaded_league
                    # Retrouver l'équipe de l'utilisateur dans la nouvelle liste
                    for t in league.teams:
                        if t.name == user_team.name:
                            user_team = t
            except Exception as e:
                print(f"Erreur lors du chargement : {e}")

        elif act == "0":
            break

def distribute_match_rewards(match: 'MatchSimulator'):
    """Fonction utilitaire pour distribuer l'XP à la fin d'un match."""
    # Déterminer le vainqueur
    blue_win = match.scores["blue"] >= match.scores["red"]
    
    # Équipe Bleue (Team A)
    for p in match.blue.players:
        base_xp = 500 if blue_win else 200
        perf_xp = (p.kills * 10) + (p.assists * 5)
        p.gain_xp(base_xp + perf_xp)
        
    # Équipe Rouge (Team B)
    for p in match.red.players:
        base_xp = 500 if not blue_win else 200
        perf_xp = (p.kills * 10) + (p.assists * 5)
        p.gain_xp(base_xp + perf_xp)

if __name__ == "__main__":
    game_loop()
