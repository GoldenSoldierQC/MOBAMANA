import pygame

# Couleurs
BG = (25, 25, 35)
PANEL = (40, 40, 55)
WHITE = (240, 240, 240)
GOLD = (212, 175, 55)
BTN = (60, 60, 80)
BTN_HOVER = (80, 80, 110)

class EmailScreen:
    def __init__(self, screen, email_manager):
        self.screen = screen
        self.manager = email_manager
        self.font_title = pygame.font.Font(None, 48)
        self.font_text = pygame.font.Font(None, 26)
        self.font_small = pygame.font.Font(None, 22)
        self.choice_buttons = {}

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in self.choice_buttons.items():
                if rect.collidepoint(event.pos):
                    event_id, choice = key
                    self.manager.resolve(event_id, choice)
                    return "CLOSE"
        return None

    def draw(self):
        self.screen.fill(BG)

        email = None
        if self.manager.inbox:  # Get the latest email
            email = self.manager.inbox[-1]
            
        if not email:
            txt = self.font_title.render("Aucun email", True, WHITE)
            self.screen.blit(txt, (640 - txt.get_width() // 2, 360))
            return

        # Panel principal
        panel = pygame.Rect(160, 80, 960, 560)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=14)
        pygame.draw.rect(self.screen, (90, 90, 110), panel, 2, border_radius=14)

        # Header
        sender = self.font_small.render(f"De : {email.sender}", True, GOLD)
        subject = self.font_title.render(email.subject, True, WHITE)

        self.screen.blit(sender, (panel.x + 30, panel.y + 20))
        self.screen.blit(subject, (panel.x + 30, panel.y + 50))

        # Corps
        y = panel.y + 130
        for line in email.body.split("\n"):
            txt = self.font_text.render(line, True, WHITE)
            self.screen.blit(txt, (panel.x + 30, y))
            y += 30

        # Boutons choix
        self.choice_buttons.clear()
        btn_y = panel.bottom - 90
        btn_w = 260
        gap = 30
        start_x = panel.centerx - ((len(email.choices) * btn_w + (len(email.choices) - 1) * gap) // 2)

        for i, choice in enumerate(email.choices.keys()):
            rect = pygame.Rect(start_x + i * (btn_w + gap), btn_y, btn_w, 50)
            self.choice_buttons[(email.id, choice)] = rect

            hover = rect.collidepoint(pygame.mouse.get_pos())
            color = BTN_HOVER if hover else BTN

            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            pygame.draw.rect(self.screen, (120, 120, 150), rect, 2, border_radius=10)

            txt = self.font_text.render(choice, True, WHITE)
            self.screen.blit(
                txt,
                (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2)
            )

        hint = self.font_small.render("[ESC] Retour", True, (150, 150, 160))
        self.screen.blit(hint, (20, 690))
    
    def update_choice_buttons(self):
        """Met à jour les boutons de choix en fonction de l'email sélectionné."""
        self.choice_buttons = []
        if not self.email_manager.inbox:
            return
            
        email = self.email_manager.inbox[self.selected_email]
        button_width = 200
        button_y = self.height - 2 * (self.button_height + 10)
        
        for i, (choice_text, _) in enumerate(email.choices.items()):
            button_x = self.list_width + (self.width - self.list_width - button_width) // 2
            button_rect = pygame.Rect(button_x, button_y, button_width, self.button_height)
            self.choice_buttons.append((button_rect, self.button_color, choice_text))
            button_y += self.button_height + 10
    
    def handle_choice_click(self, choice_index):
        """Gère le clic sur un bouton de choix."""
        if not self.email_manager.inbox:
            return
            
        email = self.email_manager.inbox[self.selected_email]
        if choice_index < len(email.choices):
            # Exécute l'effet du choix
            choice_key = list(email.choices.keys())[choice_index]
            self.email_manager.resolve(email.id, choice_key)
            
            # Si l'email a été résolu, on le supprime de la sélection
            if email.id not in {e.id for e in self.email_manager.inbox}:
                self.selected_email = max(0, min(self.selected_email, len(self.email_manager.inbox) - 1))
            
            self.update_choice_buttons()
    
    def ensure_email_visible(self):
        """Fait défiler la liste pour que l'email sélectionné soit visible."""
        if not self.email_manager.inbox:
            return
            
        visible_emails = (self.height - 2 * self.padding) // 50
        if self.selected_email < self.scroll_offset:
            self.scroll_offset = self.selected_email
        elif self.selected_email >= self.scroll_offset + visible_emails:
            self.scroll_offset = max(0, self.selected_email - visible_emails + 1)
    
    def draw(self):  # noqa: F811
        """Dessine l'interface des emails."""
        # Fond
        self.screen.fill(self.bg_color)
        
        # Panneau latéral gauche (liste des emails)
        pygame.draw.rect(self.screen, self.panel_color, (0, 0, self.list_width, self.height))
        
        # En-tête
        title = self.font_large.render("BOÎTE DE RÉCEPTION", True, self.highlight_color)
        self.screen.blit(title, (self.padding, self.padding))
        
        # Liste des emails
        if not self.email_manager.inbox:
            empty_text = self.font_medium.render("Aucun email", True, self.text_color)
            self.screen.blit(empty_text, (self.padding, 2 * self.padding + title.get_height()))
        else:
            visible_emails = (self.height - 2 * self.padding) // 50
            start_idx = max(0, min(self.scroll_offset, len(self.email_manager.inbox) - visible_emails))
            end_idx = min(start_idx + visible_emails, len(self.email_manager.inbox))
            
            for i in range(start_idx, end_idx):
                email = self.email_manager.inbox[i]
                y_pos = self.padding + 50 + (i - start_idx) * 50 - self.scroll_offset * 50
                
                # Mise en évidence de l'email sélectionné
                if i == self.selected_email:
                    pygame.draw.rect(self.screen, (60, 60, 90), 
                                   (0, y_pos - 5, self.list_width, 45))
                
                # Sujet
                subject = self.font_medium.render(email.subject, True, 
                                                self.highlight_color if i == self.selected_email else self.text_color)
                self.screen.blit(subject, (self.padding, y_pos))
                
                # Expéditeur
                sender = self.font_small.render(f"De: {email.sender}", True, 
                                              (180, 180, 200) if i == self.selected_email else (150, 150, 170))
                self.screen.blit(sender, (self.padding, y_pos + 25))
        
        # Contenu de l'email sélectionné
        if self.email_manager.inbox:
            self.draw_email_content()
        
        # Bouton de retour
        back_rect = pygame.Rect(self.width - 120, 10, 100, 30)
        pygame.draw.rect(self.screen, self.button_color, back_rect, border_radius=5)
        back_text = self.font_small.render("Retour (Échap)", True, self.text_color)
        self.screen.blit(back_text, (back_rect.x + 10, back_rect.y + 8))
        
        # Aide au clavier
        help_text = self.font_small.render("↑/↓: Sélectionner  Entrée: Lire  Échap: Retour", 
                                          True, (100, 100, 120))
        self.screen.blit(help_text, (self.list_width + 20, self.height - 30))
    
    def draw_email_content(self):
        """Dessine le contenu de l'email sélectionné."""
        if not self.email_manager.inbox:
            return
            
        email = self.email_manager.inbox[self.selected_email]
        x_pos = self.list_width + self.padding
        y_pos = self.padding
        
        # Expéditeur
        sender_text = self.font_large.render(email.sender, True, self.highlight_color)
        self.screen.blit(sender_text, (x_pos, y_pos))
        y_pos += sender_text.get_height() + 10
        
        # Sujet
        subject_text = self.font_medium.render(email.subject, True, self.text_color)
        self.screen.blit(subject_text, (x_pos, y_pos))
        y_pos += subject_text.get_height() + 20
        
        # Corps du message avec retour à la ligne automatique
        wrapper = textwrap.TextWrapper(width=60)  # noqa: F821
        for line in email.body.split('\n'):
            wrapped_lines = wrapper.wrap(line) if line.strip() else ['']
            for wrapped_line in wrapped_lines:
                if wrapped_line:  # Ne pas afficher les lignes vides
                    line_surface = self.font_medium.render(wrapped_line, True, self.text_color)
                    self.screen.blit(line_surface, (x_pos, y_pos))
                    y_pos += line_surface.get_height() + 5
                else:
                    y_pos += self.font_medium.get_linesize()
        
        # Boutons de choix
        self.draw_choice_buttons(y_pos + 20)
    
    def draw_choice_buttons(self, start_y):
        """Dessine les boutons de choix pour l'email actuel."""
        if not self.email_manager.inbox:
            return
            
        email = self.email_manager.inbox[self.selected_email]
        button_width = 200
        button_height = 40
        button_y = start_y
        
        self.choice_buttons = []  # Réinitialiser les boutons
        
        for i, (choice_text, _) in enumerate(email.choices.items()):
            button_x = self.list_width + (self.width - self.list_width - button_width) // 2
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            # Couleur du bouton (survol ou normal)
            mouse_pos = pygame.mouse.get_pos()
            button_color = self.button_hover_color if button_rect.collidepoint(mouse_pos) else self.button_color
            
            # Dessiner le bouton
            pygame.draw.rect(self.screen, button_color, button_rect, border_radius=5)
            pygame.draw.rect(self.screen, self.highlight_color, button_rect, 2, border_radius=5)
            
            # Texte du bouton
            text_surface = self.button_font.render(choice_text, True, self.text_color)
            text_rect = text_surface.get_rect(center=button_rect.center)
            self.screen.blit(text_surface, text_rect)
            
            # Stocker le rectangle du bouton pour la détection des clics
            self.choice_buttons.append((button_rect, button_color, choice_text))
            
            button_y += button_height + 10
    
    def handle_email_selection(self, index):
        """Gère la sélection d'un email."""
        if 0 <= index < len(self.email_manager.inbox):
            self.selected_email = index
            self.update_choice_buttons()
            
            # Marquer comme lu (optionnel)
            # email = self.email_manager.inbox[index]
            # email.read = True
