from dataclasses import dataclass
from typing import Dict, Callable, List, Set
import random

@dataclass
class EmailEvent:
    """Représente un événement par email avec des choix et des effets."""
    id: str
    sender: str
    subject: str
    body: str
    choices: Dict[str, Callable]  # Texte du choix: fonction d'effet
    once: bool = True  # Si l'événement ne peut se produire qu'une seule fois

class EmailManager:
    """Gère la réception et le traitement des événements par email."""
    
    def __init__(self, league):
        self.inbox: List[EmailEvent] = []
        self.league = league
        self.resolved_events: Set[str] = set()
        self._setup_events()

    def _setup_events(self):
        """Initialise les événements disponibles."""
        self.available_events = [
            self._create_sponsor_aggressive_campaign(),
            self._create_player_burnout_warning(),
            self._create_league_rule_change(),
            EmailEvent(
                id="PLAYER_TRANSFER_OFFER_001",
                sender="Agent de transfert",
                subject="Offre pour un de vos joueurs",
                body=(
                    "Une équipe est intéressée par l'un de vos joueurs.\n"
                    "Voulez-vous le mettre sur le marché des transferts ?"
                ),
                choices={
                    "OUI": self._trigger_player_transfer,
                    "NON": lambda: None
                }
            )
        ]
        
    def _create_sponsor_aggressive_campaign(self):
        """Crée un événement de campagne de sponsor agressive."""
        return EmailEvent(
            id="SPONSOR_AGGRO_001",
            sender="HyperFuel Corp",
            subject="Campagne agressive – Visibilité maximale",
            body=(
                "Nous voulons une image agressive.\n\n"
                "+50 000$ immédiat\n"
                "-5 prestige si vos résultats chutent\n\n"
                "Acceptez-vous ?"
            ),
            choices={
                "ACCEPTER": lambda: self._apply_sponsor_risk(50000, 5),
                "REFUSER": lambda: self._refuse_sponsor()
            }
        )
        
    def _create_player_burnout_warning(self):
        """Crée un avertissement de fatigue des joueurs."""
        return EmailEvent(
            id="PLAYER_BURNOUT_001",
            sender="Staff Médical",
            subject="Alerte fatigue – risque de burnout",
            body=(
                "Plusieurs joueurs montrent des signes de fatigue.\n\n"
                "Repos = meilleur sang-froid\n"
                "Pression = meilleures mécaniques, mais risque mental"
            ),
            choices={
                "ACCORDER DU REPOS": self._rest_players,
                "CONTINUER LA PRESSION": self._push_harder
            }
        )
        
    def _create_league_rule_change(self):
        """Crée un événement de changement de règles de la ligue."""
        return EmailEvent(
            id="LEAGUE_RULES_001",
            sender="Commission eSport",
            subject="Changement de règles – Patch compétitif",
            body=(
                "La ligue modifie certaines règles macro.\n\n"
                "Soutenir = bonne image\n"
                "S'opposer = mal vu par la ligue"
            ),
            choices={
                "SOUTENIR": self._accept_rule_change,
                "PROTESTER": self._protest_rule_change
            }
        )

    def _apply_sponsor_risk(self, money: int, prestige_penalty: int):
        """Applique les effets du sponsor risqué."""
        team = self.league.teams[0]  # L'équipe du joueur
        team.finance.budget += money
        # On stocke le callback pour le prochain match
        original_handle_match_result = self.league.handle_match_result
        
        def wrapped_handle_match_result(*args, **kwargs):
            result = original_handle_match_result(*args, **kwargs)
            if not result:  # Si défaite
                team.prestige = max(0, team.prestige - prestige_penalty)
            # On restaure la méthode originale
            self.league.handle_match_result = original_handle_match_result
            return result
            
        self.league.handle_match_result = wrapped_handle_match_result

    def _trigger_player_transfer(self):
        """Déclenche un transfert de joueur."""
        if not self.league.teams[0].roster:
            return
            
        player = random.choice(list(self.league.teams[0].roster.values()))
        base_value = player.skill * 10000
        offer = base_value * random.uniform(1.2, 2.0)
        
        # Créer un nouvel email pour l'offre de transfert
        transfer_event = EmailEvent(
            id=f"TRANSFER_OFFER_{player.name.upper()}",
            sender=random.choice(["Équipe rivale", "Club étranger", "Agent libre"]),
            subject=f"Offre pour {player.name}",
            body=f"Offre de {int(offer)}$ pour {player.name} ({player.role.name}).",
            choices={
                "ACCEPTER": lambda: self._accept_transfer(player, offer),
                "REFUSER": lambda: None
            }
        )
        self.push_event(transfer_event)

    def _accept_transfer(self, player, offer):
        """Accepte une offre de transfert."""
        team = self.league.teams[0]
        team.finance.budget += offer
        del team.roster[player.role]
        # On pourrait ajouter un message de confirmation ici
        
    def _refuse_sponsor(self):
        """Effet de refus d'un sponsor."""
        self.league.teams[0].prestige += 1
        
    def _rest_players(self):
        """Donne du repos aux joueurs."""
        team = self.league.teams[0]
        for player in team.roster.values():
            if hasattr(player, 'sng'):
                player.sng = min(99, player.sng + 3)
    
    def _push_harder(self):
        """Pousse les joueurs à se dépasser."""
        team = self.league.teams[0]
        for player in team.roster.values():
            if hasattr(player, 'mec') and hasattr(player, 'sng'):
                player.mec = min(99, player.mec + 2)
                player.sng = max(10, player.sng - 4)
    
    def _accept_rule_change(self):
        """Accepte les changements de règles de la ligue."""
        for team in self.league.teams:
            team.prestige += 2
            
    def _protest_rule_change(self):
        """Proteste contre les changements de règles de la ligue."""
        self.league.teams[0].prestige = max(0, self.league.teams[0].prestige - 3)

    def push_event(self, event: EmailEvent):
        """Ajoute un nouvel événement à la boîte de réception."""
        if event.once and event.id in self.resolved_events:
            return False
        self.inbox.append(event)
        return True

    def trigger_random_event(self, chance: float = 0.25) -> bool:
        """
        Déclenche un événement aléatoire avec une certaine probabilité.
        
        Args:
            chance: Probabilité (entre 0 et 1) qu'un événement se produise
            
        Returns:
            bool: True si un événement a été déclenché, False sinon
        """
        if random.random() >= chance or not self.available_events:
            return False
            
        # Filtrer les événements uniques déjà résolus
        available = [e for e in self.available_events 
                    if not e.once or e.id not in self.resolved_events]
        
        if not available:
            return False
            
        event = random.choice(available)
        self.push_event(event)
        return True

    def resolve(self, event_id: str, choice_key: str):
        """Résout un événement en appliquant le choix du joueur."""
        event = next((e for e in self.inbox if e.id == event_id), None)
        if not event:
            return False
            
        if choice_key in event.choices:
            effect_fn = event.choices[choice_key]
            effect_fn()  # Appel de la fonction d'effet
            
        if event.once:
            self.resolved_events.add(event_id)
        self.inbox.remove(event)
        return True

    def get_unread_count(self) -> int:
        """Retourne le nombre d'emails non lus."""
        return len(self.inbox)
        
    def has_mail(self) -> bool:
        """Vérifie s'il y a des emails non lus dans la boîte de réception.
        
        Returns:
            bool: True s'il y a des emails non lus, False sinon
        """
        return len(self.inbox) > 0
