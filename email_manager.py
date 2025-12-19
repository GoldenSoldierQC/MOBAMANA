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
            EmailEvent(
                id="SPONSOR_RISK_001",
                sender="HyperFuel Corp",
                subject="Offre agressive – visibilité maximale",
                body=(
                    "Nous voulons pousser votre image agressive.\n"
                    "+50 000$ immédiat\n"
                    "-5 prestige si vous perdez le prochain match"
                ),
                choices={
                    "ACCEPTER": lambda: self._apply_sponsor_risk(50000, 5),
                    "REFUSER": lambda: None
                }
            ),
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

    def push_event(self, event: EmailEvent):
        """Ajoute un nouvel événement à la boîte de réception."""
        if event.id not in self.resolved_events:
            self.inbox.append(event)
            return True
        return False

    def trigger_random_event(self):
        """Déclenche un événement aléatoire."""
        if not self.available_events:
            return False
            
        event = random.choice(self.available_events)
        self.push_event(event)
        return True

    def resolve(self, event_id: str, choice_key: str):
        """Résout un événement en appliquant le choix du joueur."""
        event = next((e for e in self.inbox if e.id == event_id), None)
        if not event:
            return False
            
        if choice_key in event.choices:
            event.choices[choice_key]()
            
        self.resolved_events.add(event_id)
        self.inbox.remove(event)
        return True

    def get_unread_count(self) -> int:
        """Retourne le nombre d'emails non lus."""
        return len(self.inbox)
