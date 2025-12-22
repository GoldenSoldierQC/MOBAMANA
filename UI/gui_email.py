import pygame
import textwrap

# Couleurs
BG = (25, 25, 35)
PANEL = (40, 40, 55)
WHITE = (240, 240, 240)
GOLD = (212, 175, 55)
BTN = (60, 60, 80)
BTN_HOVER = (80, 80, 110)
HIGHLIGHT = (255, 255, 255)
TEXT_COLOR = (200, 200, 200)

class EmailGUI:
    def __init__(self, screen, email_manager, on_back=None):
        self.screen = screen
        self.email_manager = email_manager
        self.on_back = on_back
        
        # Dimensions
        self.width, self.height = screen.get_size()
        self.list_width = 320
        self.padding = 20
        self.scroll_offset = 0
        self.selected_email = 0
        
        # Fonts
        self.font_title = pygame.font.Font(None, 48)
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)
        self.button_font = pygame.font.Font(None, 22)
        
        # Couleurs locales
        self.bg_color = BG
        self.panel_color = PANEL
        self.highlight_color = GOLD
        self.text_color = TEXT_COLOR
        self.button_color = BTN
        self.button_hover_color = BTN_HOVER
        
        self.choice_buttons = []
        self.button_height = 40
        
        if self.email_manager and self.email_manager.inbox:
            self.update_choice_buttons()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.on_back:
                    self.on_back()
                return True
            if not self.email_manager or not self.email_manager.inbox:
                return False
                
            if event.key == pygame.K_UP:
                self.selected_email = max(0, self.selected_email - 1)
                self.ensure_email_visible()
                self.update_choice_buttons()
            elif event.key == pygame.K_DOWN:
                self.selected_email = min(len(self.email_manager.inbox) - 1, self.selected_email + 1)
                self.ensure_email_visible()
                self.update_choice_buttons()
                
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Clic sur le bouton retour
                back_rect = pygame.Rect(self.width - 120, 10, 100, 30)
                if back_rect.collidepoint(event.pos):
                    if self.on_back:
                        self.on_back()
                    return True

                if not self.email_manager:
                    return False

                # Clic dans la liste des emails
                if event.pos[0] < self.list_width:
                    # Calcul simple de l'index cliqué
                    y_click = event.pos[1] - (self.padding + 50)
                    if y_click >= 0:
                        idx = (y_click // 50) + self.scroll_offset
                        if 0 <= idx < len(self.email_manager.inbox):
                            self.selected_email = idx
                            self.update_choice_buttons()
                
                # Clic sur les boutons de choix
                for rect, _, choice_text in self.choice_buttons:
                    if rect.collidepoint(event.pos):
                        # Retrouver l'index du choix
                        email = self.email_manager.inbox[self.selected_email]
                        keys = list(email.choices.keys())
                        if choice_text in keys:
                            idx = keys.index(choice_text)
                            self.handle_choice_click(idx)
                        return True
                        
        return False

    def handle_choice_click(self, choice_index):
        if not self.email_manager or not self.email_manager.inbox:
            return
            
        email = self.email_manager.inbox[self.selected_email]
        if choice_index < len(email.choices):
            choice_key = list(email.choices.keys())[choice_index]
            self.email_manager.resolve(email.id, choice_key)
            
            # Si l'email a été résolu (et supprimé de l'inbox), on ajuste la sélection
            current_ids = {e.id for e in self.email_manager.inbox}
            if email.id not in current_ids:
                if self.selected_email >= len(self.email_manager.inbox):
                    self.selected_email = max(0, len(self.email_manager.inbox) - 1)
            
            self.update_choice_buttons()

    def update_choice_buttons(self):
        self.choice_buttons = []
        if not self.email_manager or not self.email_manager.inbox:
            return
            
        if self.selected_email >= len(self.email_manager.inbox):
             self.selected_email = 0
             
        email = self.email_manager.inbox[self.selected_email]
        button_width = 200
        
        # On recalcule la position Y dynamiquement dans draw, mais on peut pré-calculer ici si on veut
        # Pour simplifier, on laisse draw gérer l'affichage et la création des rects pour la prochaine frame,
        # mais on a besoin des rects pour le handle_click.
        # Idéalement, on sépare logique et rendu. Ici, on va laisser draw_choice_buttons peupler la liste.
        pass

    def ensure_email_visible(self):
        visible_emails = (self.height - 2 * self.padding) // 50
        if self.selected_email < self.scroll_offset:
            self.scroll_offset = self.selected_email
        elif self.selected_email >= self.scroll_offset + visible_emails:
            self.scroll_offset = max(0, self.selected_email - visible_emails + 1)

    def draw(self):
        self.screen.fill(self.bg_color)
        
        # Panneau latéral gauche
        pygame.draw.rect(self.screen, self.panel_color, (0, 0, self.list_width, self.height))
        # Bordure droite du panneau
        pygame.draw.line(self.screen, (60, 60, 80), (self.list_width, 0), (self.list_width, self.height), 2)
        
        # Titre Inbox
        title = self.font_large.render("BOÎTE DE RÉCEPTION", True, self.highlight_color)
        self.screen.blit(title, (self.padding, self.padding))
        
        if not self.email_manager or not self.email_manager.inbox:
            empty = self.font_medium.render("Aucun message", True, self.text_color)
            self.screen.blit(empty, (self.padding, 80))
        else:
            self._draw_email_list()
            self._draw_selected_email_content()
            
        self._draw_back_button()

    def _draw_email_list(self):
        visible_emails = (self.height - 100) // 50
        start_idx = self.scroll_offset
        end_idx = min(start_idx + visible_emails, len(self.email_manager.inbox))
        
        for i in range(start_idx, end_idx):
            email = self.email_manager.inbox[i]
            y_pos = 80 + (i - start_idx) * 50
            
            # Highlight selection
            if i == self.selected_email:
                pygame.draw.rect(self.screen, (60, 60, 90), (0, y_pos - 5, self.list_width, 45))
            
            # Sujet (tronqué si trop long)
            subj_txt = email.subject[:22] + "..." if len(email.subject) > 22 else email.subject
            col = self.highlight_color if i == self.selected_email else self.text_color
            surf = self.font_medium.render(subj_txt, True, col)
            self.screen.blit(surf, (self.padding, y_pos))
            
            # Expéditeur
            send_txt = email.sender[:25]
            surf2 = self.font_small.render(send_txt, True, (150, 150, 150))
            self.screen.blit(surf2, (self.padding, y_pos + 22))

    def _draw_selected_email_content(self):
        if self.selected_email >= len(self.email_manager.inbox):
            return
            
        email = self.email_manager.inbox[self.selected_email]
        x_start = self.list_width + 40
        y_start = 40
        
        # En-tête message
        sender = self.font_large.render(f"De: {email.sender}", True, GOLD)
        self.screen.blit(sender, (x_start, y_start))
        
        subject = self.font_title.render(email.subject, True, WHITE)
        self.screen.blit(subject, (x_start, y_start + 40))
        
        # Corps du message
        y_text = y_start + 100
        wrapper = textwrap.TextWrapper(width=70)
        for line in email.body.split('\n'):
            wrapped = wrapper.wrap(line) if line.strip() else ['']
            for wline in wrapped:
                if wline:
                    surf = self.font_medium.render(wline, True, self.text_color)
                    self.screen.blit(surf, (x_start, y_text))
                    y_text += 25
                else:
                    y_text += 25

        # Boutons de choix
        self.choice_buttons = []
        btn_y = self.height - 100
        btn_x = x_start
        
        for choice_text in email.choices.keys():
            rect = pygame.Rect(btn_x, btn_y, 200, 40)
            
            is_hover = rect.collidepoint(pygame.mouse.get_pos())
            col = self.button_hover_color if is_hover else self.button_color
            
            pygame.draw.rect(self.screen, col, rect, border_radius=8)
            pygame.draw.rect(self.screen, (100, 100, 120), rect, 1, border_radius=8)
            
            txt = self.button_font.render(choice_text, True, WHITE)
            self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))
            
            self.choice_buttons.append((rect, col, choice_text))
            
            btn_x += 220

    def _draw_back_button(self):
        rect = pygame.Rect(self.width - 120, 10, 100, 30)
        bg = (180, 50, 50) if rect.collidepoint(pygame.mouse.get_pos()) else (150, 40, 40)
        pygame.draw.rect(self.screen, bg, rect, border_radius=5)
        txt = self.font_small.render("RETOUR", True, WHITE)
        self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

