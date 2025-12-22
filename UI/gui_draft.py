import pygame
import random
from moba_manager import CHAMPIONS_DB

class DraftManager:
    def __init__(self, screen):
        self.screen = screen
        self.champions_list = list(CHAMPIONS_DB.keys())
        self.champions_data = CHAMPIONS_DB
        
        # 1. Gestionnaire de Rectangles
        self.hero_rects = {} # Associe un nom de héros à un objet pygame.Rect
        self._init_grid()

        # 2. Logique de Tour et Sélections
        self.picks_a = [] # Héros choisis par toi
        self.picks_b = [] # Héros choisis par l'IA (ou l'adversaire)
        self.all_selected = [] # Liste globale pour le verrouillage
        
        # Ordre des tours (10 sélections au total)
        self.turn_order = ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"]
        self.current_step = 0 # Index du tour actuel

        # Timer pour donner l'impression que l'IA "réfléchit"
        self.ai_timer = 0
        self.AI_DELAY = 60 # Environ 1 seconde à 60 FPS
        
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 48)
        
        self.color_a = (41, 128, 185)
        self.color_b = (192, 57, 43)

    def _init_grid(self):
        """Crée les rectangles de collision pour chaque héros."""
        for i, name in enumerate(self.champions_list):
            x = 350 + (i % 5) * 120 # Grille de 5 colonnes
            y = 200 + (i // 5) * 150
            self.hero_rects[name] = pygame.Rect(x, y, 100, 100)

    def update(self):
        """Vérifie si c'est au tour de l'IA et agit après un court délai."""
        if self.current_step < len(self.turn_order):
            if self.turn_order[self.current_step] == "B":
                self.ai_timer += 1
                if self.ai_timer >= self.AI_DELAY:
                    self._ai_pick()
                    self.ai_timer = 0

    def _ai_pick(self):
        """Logique de sélection de l'IA."""
        # Filtrer les héros encore disponibles
        available = [h for h in self.champions_list if h not in self.all_selected]
        
        if available:
            # Pour l'instant, l'IA choisit au hasard. 
            choice = random.choice(available)
            self._select_hero(choice)

    def handle_click(self, mouse_pos):
        """Gère la sélection d'un héros au clic."""
        if self.current_step < len(self.turn_order):
            # On ne traite le clic que si c'est le tour du joueur
            if self.turn_order[self.current_step] == "A":
                for name, rect in self.hero_rects.items():
                    # Vérification : Clic dans le rectangle ET héros non encore choisi
                    if rect.collidepoint(mouse_pos) and name not in self.all_selected:
                        self._select_hero(name)
                        break

    def _select_hero(self, hero_name):
        """Assigne le héros à l'équipe dont c'est le tour."""
        current_team = self.turn_order[self.current_step]
        
        if current_team == "A":
            self.picks_a.append(hero_name)
        else:
            self.picks_b.append(hero_name)
            
        self.all_selected.append(hero_name)
        self.current_step += 1
        print(f"Tour {self.current_step}: {hero_name} sélectionné pour Team {current_team}")

    def draw(self):
        """Affiche la grille de draft avec l'état de verrouillage."""
        self.screen.fill((20, 20, 30)) # Fond sombre pro-gaming
        
        # Titre
        title_text = "PHASE DE DRAFT"
        if self.current_step >= len(self.turn_order):
            title_text = "DRAFT TERMINÉE"
        title_surf = self.title_font.render(title_text, True, (255, 255, 255))
        self.screen.blit(title_surf, (1280 // 2 - title_surf.get_width() // 2, 40))

        for name, rect in self.hero_rects.items():
            # 3. Verrouillage : Si choisi, on assombrit la carte
            is_picked = name in self.all_selected
            bg_color = (40, 40, 40) if is_picked else (70, 70, 90)
            text_color = (100, 100, 100) if is_picked else (255, 255, 255)

            pygame.draw.rect(self.screen, bg_color, rect, border_radius=10)
            if not is_picked:
                pygame.draw.rect(self.screen, (100, 100, 150), rect, 2, border_radius=10)
            
            txt_surf = self.font.render(name, True, text_color)
            self.screen.blit(txt_surf, (rect.x + (100 - txt_surf.get_width())//2, rect.y + 40))

        # Affichage du tour actuel
        if self.current_step < len(self.turn_order):
            team_text = "VOTRE TOUR" if self.turn_order[self.current_step] == "A" else "TOUR ADVERSAIRE"
            color = self.color_a if "VOTRE" in team_text else self.color_b
            turn_surf = self.font.render(team_text, True, color)
            self.screen.blit(turn_surf, (640 - turn_surf.get_width()//2, 120))
            
        # Affichage des sélections actuelles
        self._draw_selections()

    def _draw_selections(self):
        """Dessine les héros choisis sur les côtés."""
        # Team A (Gauche)
        for i, name in enumerate(self.picks_a):
            txt = self.font.render(name, True, (41, 128, 185))
            self.screen.blit(txt, (50, 150 + i * 40))
            
        # Team B (Droite)
        for i, name in enumerate(self.picks_b):
            txt = self.font.render(name, True, (192, 57, 43))
            self.screen.blit(txt, (1280 - txt.get_width() - 50, 150 + i * 40))
