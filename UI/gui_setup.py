import pygame

class ProfileSetup:
    def __init__(self, screen):
        self.screen = screen
        # On essaie de récupérer les polices depuis le main ou on en recrée
        self.font_main = pygame.font.Font(None, 48)
        self.font_text = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Données à remplir
        self.coach_name = ""
        self.team_name = ""
        self.selected_color = (41, 128, 185) # Bleu par défaut
        self.specialization = "Polyvalent"
        
        self.active_field = "coach" # coach ou team
        self.done = False
        
        # Choix de couleurs (Logo/UI)
        self.colors = [
            (41, 128, 185), (192, 57, 43), (39, 174, 96), 
            (241, 196, 15), (155, 89, 182), (230, 126, 34)
        ]
        
        # Spécialisations
        self.specs = ["Polyvalent", "Analyste", "Motivateur", "Scout", "Entraîneur"]
        self.spec_idx = 0
        
        # Formes de Logo
        self.shapes = ["Cercle", "Carré", "Diamant"]
        self.shape_idx = 0
        self.selected_shape = "Cercle"
        
        # Starter Packs
        from moba_manager import STARTER_KITS
        self.starter_packs = list(STARTER_KITS.keys())
        self.pack_idx = 0
        self.selected_pack = self.starter_packs[0]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self.active_field == "coach":
                    self.coach_name = self.coach_name[:-1]
                else:
                    self.team_name = self.team_name[:-1]
            elif event.key == pygame.K_TAB:
                self.active_field = "team" if self.active_field == "coach" else "coach"
            elif event.key == pygame.K_RETURN:
                if self.coach_name and self.team_name:
                    self.done = True
            elif event.unicode.isprintable() and len(event.unicode) == 1:
                # Protection sur la longueur
                if self.active_field == "coach" and len(self.coach_name) < 20:
                    self.coach_name += event.unicode
                elif self.active_field == "team" and len(self.team_name) < 20:
                    self.team_name += event.unicode
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            # Sélection de couleur
            for i, color in enumerate(self.colors):
                rect = pygame.Rect(400 + (i * 60), 550, 45, 45)
                if rect.collidepoint(mouse_pos):
                    self.selected_color = color
            
            # Sélection spécialisation
            for i, spec in enumerate(self.specs):
                rect = pygame.Rect(400 + (i * 100), 410 + 40, 90, 30)
                if rect.collidepoint(mouse_pos):
                    self.spec_idx = i
                    self.specialization = spec

            # Sélection forme de logo
            for i, shape in enumerate(self.shapes):
                rect = pygame.Rect(400 + (i * 110), 620 + 40, 100, 30)
                if rect.collidepoint(mouse_pos):
                    self.shape_idx = i
                    self.selected_shape = shape
                    
            # Sélection du pack de départ
            for i, pack in enumerate(self.starter_packs):
                rect = pygame.Rect(400 + (i * 200), 720, 190, 50)
                if rect.collidepoint(mouse_pos):
                    self.pack_idx = i
                    self.selected_pack = pack
            
            # Bouton de validation
            btn_rect = pygame.Rect(540, 800, 200, 50)
            if btn_rect.collidepoint(mouse_pos):
                if self.coach_name and self.team_name:
                    self.done = True

    def draw(self):
        self.screen.fill((10, 10, 15))
        
        # Titre
        title = self.font_main.render("CRÉATION DE VOTRE ORGANISATION", True, (255, 255, 255))
        self.screen.blit(title, (640 - title.get_width()//2, 50))

        # Champs de texte
        self._draw_input_field("NOM DU COACH / MANAGER", self.coach_name, 150, self.active_field == "coach")
        self._draw_input_field("NOM DE VOTRE ÉQUIPE", self.team_name, 280, self.active_field == "team")
        
        # Sélecteur de spécialisation
        self._draw_spec_picker(410)
        
        # Sélecteur de couleur
        self._draw_color_picker(510)
        
        # Sélecteur de forme
        self._draw_logo_picker(610)
        
        # Sélecteur de pack de départ
        self._draw_pack_picker(700)
        
        # Aperçu du Logo
        self._draw_logo_preview(950, 200)

        # Bouton Valider
        btn_color = (41, 128, 185) if (self.coach_name and self.team_name) else (50, 50, 50)
        btn_rect = pygame.Rect(540, 800, 200, 50)
        pygame.draw.rect(self.screen, btn_color, btn_rect, border_radius=10)
        btn_txt = self.font_text.render("CONFIRMER", True, (255, 255, 255))
        self.screen.blit(btn_txt, (btn_rect.centerx - btn_txt.get_width()//2, btn_rect.centery - btn_txt.get_height()//2))
        
        if not (self.coach_name and self.team_name):
            hint = self.font_small.render("Veuillez remplir tous les champs", True, (150, 150, 150))
            self.screen.blit(hint, (640 - hint.get_width()//2, 860))

    def _draw_input_field(self, label, text, y, is_active):
        color = (212, 175, 55) if is_active else (150, 150, 150)
        lbl_surf = self.font_text.render(label, True, color)
        self.screen.blit(lbl_surf, (400, y))
        
        # Zone de saisie
        pygame.draw.rect(self.screen, (30, 30, 40), (400, y + 35, 480, 45), border_radius=5)
        if is_active:
            pygame.draw.rect(self.screen, (212, 175, 55), (400, y + 35, 480, 45), 2, border_radius=5)
            
        txt_surf = self.font_text.render(text + ("|" if is_active else ""), True, (255, 255, 255))
        self.screen.blit(txt_surf, (415, y + 45))

    def _draw_spec_picker(self, y):
        lbl = self.font_text.render("SPÉCIALISATION DU COACH", True, (200, 200, 200))
        self.screen.blit(lbl, (400, y))
        
        for i, spec in enumerate(self.specs):
            rect = pygame.Rect(400 + (i * 110), y + 40, 100, 30)
            is_sel = (self.spec_idx == i)
            color = (212, 175, 55) if is_sel else (40, 40, 50)
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            
            txt_color = (0, 0, 0) if is_sel else (150, 150, 150)
            txt_surf = self.font_small.render(spec, True, txt_color)
            self.screen.blit(txt_surf, (rect.centerx - txt_surf.get_width()//2, rect.centery - txt_surf.get_height()//2))

    def _draw_color_picker(self, y):
        lbl = self.font_text.render("COULEUR DE L'ORGANISATION", True, (200, 200, 200))
        self.screen.blit(lbl, (400, y))
        
        for i, color in enumerate(self.colors):
            rect = pygame.Rect(400 + (i * 60), y + 40, 45, 45)
            is_sel = (self.selected_color == color)
            
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            if is_sel:
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 3, border_radius=5)

    def _draw_logo_picker(self, y):
        lbl = self.font_text.render("FORME DU LOGO", True, (200, 200, 200))
        self.screen.blit(lbl, (400, y))
        
        for i, shape in enumerate(self.shapes):
            rect = pygame.Rect(400 + (i * 110), y + 40, 100, 30)
            is_sel = (self.shape_idx == i)
            color = (212, 175, 55) if is_sel else (40, 40, 50)
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            
            txt_color = (0, 0, 0) if is_sel else (150, 150, 150)
            txt_surf = self.font_small.render(shape, True, txt_color)
            self.screen.blit(txt_surf, (rect.centerx - txt_surf.get_width()//2, rect.centery - txt_surf.get_height()//2))

    def _draw_pack_picker(self, y):
        lbl = self.font_text.render("PACK DE DÉPART", True, (200, 200, 200))
        self.screen.blit(lbl, (400, y - 30))
        
        for i, pack in enumerate(self.starter_packs):
            rect = pygame.Rect(400 + (i * 200), y, 190, 50)
            is_sel = (self.pack_idx == i)
            color = (212, 175, 55) if is_sel else (40, 40, 50)
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            
            txt_color = (0, 0, 0) if is_sel else (200, 200, 200)
            pack_name = self.font_small.render(pack, True, txt_color)
            from moba_manager import STARTER_KITS
            # Utiliser une police plus petite pour la description si nécessaire, ou tronquer
            desc_font = pygame.font.Font(None, 20)
            pack_desc = desc_font.render(STARTER_KITS[pack]["desc"], True, (150, 150, 150))
            
            self.screen.blit(pack_name, (rect.centerx - pack_name.get_width()//2, rect.y + 8))
            self.screen.blit(pack_desc, (rect.centerx - pack_desc.get_width()//2, rect.y + 28))

    def _draw_logo_preview(self, x, y):
        pygame.draw.rect(self.screen, (20, 20, 30), (x - 60, y - 20, 120, 120), border_radius=10)
        draw_team_logo(self.screen, x, y + 40, 40, self.selected_shape, self.selected_color)
        lbl = self.font_small.render("APERÇU", True, (100, 100, 100))
        self.screen.blit(lbl, (x - lbl.get_width()//2, y + 90))

def draw_team_logo(screen, x, y, size, shape, color):
    """Utilitaire pour dessiner le logo n'importe où."""
    if shape == "Cercle":
        pygame.draw.circle(screen, color, (x, y), size)
        pygame.draw.circle(screen, (255, 255, 255), (x, y), size, 2)
    elif shape == "Carré":
        rect = pygame.Rect(x - size, y - size, size * 2, size * 2)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2)
    elif shape == "Diamant":
        points = [
            (x, y - size), (x + size, y), (x, y + size), (x - size, y)
        ]
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, (255, 255, 255), points, 2)
