import pygame

# Couleurs
WHITE = (245, 245, 250)
BG_DARK = (15, 15, 25)
PANEL_GRAY = (30, 30, 45)
ESPORT_BLUE = (41, 98, 255)
GOLD = (212, 175, 55)
SUCCESS_GREEN = (39, 174, 96)
DANGER_RED = (231, 76, 60)

class MarketManager:
    def __init__(self, screen, market_engine, finance_manager, draw_radar_func):
        self.screen = screen
        self.market = market_engine # Instance de TransferMarket
        self.finance = finance_manager
        self.draw_radar_chart = draw_radar_func
        self.selected_idx = 0
        
        self.title_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        
        self.buy_button = pygame.Rect(800, 600, 250, 60)
        self.market_rects = []
        
        # Titre pour les colonnes
        self.headers = ["Nom", "Tier", "Role", "Prix Rachat"]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self.handle_click(event.pos)
        return None

    def handle_click(self, mouse_pos):
        # 1. Sélectionner un joueur dans la liste
        for i, rect in enumerate(self.market_rects):
            if rect.collidepoint(mouse_pos):
                self.selected_idx = i
                return "SELECT"

        # 2. Bouton d'achat
        if self.buy_button.collidepoint(mouse_pos):
            return self.attempt_purchase()
        return None

    def attempt_purchase(self):
        if not self.market.available_players:
            return None
            
        player = self.market.available_players[self.selected_idx]
        if self.finance.budget >= player.buyout_fee:
            # On retire l'argent et on renvoie le joueur pour l'ajouter au Roster
            bought_player = self.market.buy_player(self.selected_idx, self.finance)
            if self.selected_idx >= len(self.market.available_players):
                self.selected_idx = max(0, len(self.market.available_players) - 1)
            return ("PURCHASE_SUCCESS", bought_player)
        return "FUNDS_ERROR"

    def draw(self):
        # Fond
        self.screen.fill(BG_DARK)
        
        # 1. En-tête avec Budget
        title_surf = self.title_font.render("MARCHÉ DES TRANSFERTS", True, WHITE)
        self.screen.blit(title_surf, (50, 30))
        
        budget_color = SUCCESS_GREEN if self.finance.budget > 0 else DANGER_RED
        budget_surf = self.text_font.render(f"Budget: {self.finance.budget:,} $", True, budget_color)
        self.screen.blit(budget_surf, (50, 80))

        # 2. Liste des Free Agents (Panneau de gauche)
        list_rect = pygame.Rect(50, 130, 650, 520)
        pygame.draw.rect(self.screen, PANEL_GRAY, list_rect, border_radius=10)
        
        # En-têtes de colonnes
        header_y = list_rect.y + 15
        self.screen.blit(self.small_font.render("NOM", True, GOLD), (70, header_y))
        self.screen.blit(self.small_font.render("TIER", True, GOLD), (220, header_y))
        self.screen.blit(self.small_font.render("ROLE", True, GOLD), (350, header_y))
        self.screen.blit(self.small_font.render("BUYOUT", True, GOLD), (500, header_y))
        
        pygame.draw.line(self.screen, (60, 60, 80), (70, header_y + 25), (630, header_y + 25))

        self.market_rects = []
        for i, p in enumerate(self.market.available_players):
            row_y = list_rect.y + 50 + (i * 45)
            row_rect = pygame.Rect(60, row_y - 10, 630, 40)
            self.market_rects.append(row_rect)
            
            if i == self.selected_idx:
                pygame.draw.rect(self.screen, (50, 50, 70), row_rect, border_radius=5)
                color = ESPORT_BLUE
            else:
                color = WHITE
                
            # Affichage des colonnes
            self.screen.blit(self.text_font.render(p.name, True, color), (70, row_y))
            self.screen.blit(self.small_font.render(p.tier, True, (180, 180, 180)), (220, row_y + 3))
            self.screen.blit(self.small_font.render(p.role.name, True, (180, 180, 180)), (350, row_y + 3))
            
            buyout_color = SUCCESS_GREEN if self.finance.budget >= p.buyout_fee else DANGER_RED
            self.screen.blit(self.text_font.render(f"{p.buyout_fee:,}$", True, buyout_color), (500, row_y))

        # 3. Détails du joueur sélectionné (Panneau de droite)
        if self.market.available_players:
            p = self.market.available_players[self.selected_idx]
            detail_rect = pygame.Rect(720, 130, 510, 520)
            pygame.draw.rect(self.screen, (40, 40, 55), detail_rect, border_radius=15)
            
            # Nom et Titre
            name_surf = self.title_font.render(p.name, True, WHITE)
            role_surf = self.text_font.render(f"{p.role.name} | {p.tier}", True, GOLD)
            self.screen.blit(name_surf, (detail_rect.x + 30, detail_rect.y + 30))
            self.screen.blit(role_surf, (detail_rect.x + 30, detail_rect.y + 80))
            
            # Stats Numériques
            stats_y = detail_rect.y + 130
            stats_list = [
                (f"MEC: {p.mec}", (255, 100, 100)),
                (f"MAC: {p.mac}", (100, 255, 100)),
                (f"VIS: {p.vis}", (100, 100, 255)),
                (f"SNG: {p.sng}", (255, 255, 100))
            ]
            for j, (txt, s_color) in enumerate(stats_list):
                s_surf = self.text_font.render(txt, True, s_color)
                self.screen.blit(s_surf, (detail_rect.x + 30, stats_y + (j * 35)))

            # Radar Chart
            stats_map = {"MEC": p.mec, "MAC": p.mac, "VIS": p.vis, "SNG": p.sng}
            radar_x = detail_rect.right - 150
            radar_y = detail_rect.y + 250
            self.draw_radar_chart(self.screen, radar_x, radar_y, 100, stats_map, (ESPORT_BLUE[0], ESPORT_BLUE[1], ESPORT_BLUE[2], 180))

            # Bouton d'achat
            can_afford = self.finance.budget >= p.buyout_fee
            btn_color = SUCCESS_GREEN if can_afford else (100, 100, 100)
            pygame.draw.rect(self.screen, btn_color, self.buy_button, border_radius=10)
            
            # Effet de survol (simplifié car on n'a pas la position souris ici sans handle_event continu)
            buy_txt = self.text_font.render("RECRUTER LE JOUEUR", True, WHITE)
            self.screen.blit(buy_txt, (self.buy_button.x + (self.buy_button.width - buy_txt.get_width()) // 2, 
                                       self.buy_button.y + (self.buy_button.height - buy_txt.get_height()) // 2))
            
            # Info Salaire
            salary_txt = self.small_font.render(f"Salaire Hebdo: {p.salary:,}$", True, (150, 150, 150))
            self.screen.blit(salary_txt, (self.buy_button.x, self.buy_button.y + 70))

        # Tip
        tip = self.small_font.render("[H] Accueil | [R] Roster | Cliquez pour sélectionner", True, (120, 120, 140))
        self.screen.blit(tip, (SCREEN_WIDTH // 2 - tip.get_width() // 2, 680))

# Mock SCREEN_WIDTH si pas importé (sera normalement dans le main)
SCREEN_WIDTH = 1280
