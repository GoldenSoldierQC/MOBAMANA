import pygame
import sys
import math
from moba_manager import Team, Role, CalibrationTools, MatchSimulator, create_initial_roster, load_game, save_game
from gui_match import MatchDashboard
from gui_market import MarketManager

from gui_draft import DraftManager
from gui_setup import draw_team_logo

# --- CONSTANTES ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Couleurs (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ESPORT_BLUE = (41, 98, 255)
BG_DARK = (30, 30, 40)
GOLD = (212, 175, 55)

# --- ÉTATS DU JEU ---
STATE_HOME = "home"
STATE_ROSTER = "roster"
STATE_MATCH = "match"
STATE_DRAFT = "draft"
STATE_MARKET = "market"
STATE_SETUP = "setup"
STATE_MAIN_MENU = "main_menu"
STATE_SETTINGS = "settings"


class MobaGui:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("MOBA Team Manager 2025")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # L'état actuel de l'interface
        self.current_state = STATE_MAIN_MENU
        
        # Chargement des polices
        self.title_font = pygame.font.Font(None, 74)
        self.text_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        from gui_setup import ProfileSetup
        self.setup_manager = ProfileSetup(self.screen)

        self.settings = {
            "show_fps": False,
        }

        self.menu_buttons = {}
        self.settings_buttons = {}
        self.home_buttons = {}

        self.toast_msg = ""
        self.toast_until_ms = 0

        # --- CONNEXION AU BACKEND ---
        # Création d'équipes de démonstration
        self.team_blue = Team("Joueur", prestige=70, budget=1000000)
        self.team_red = Team("G2 Esports", prestige=90, budget=1200000, team_color=(192, 57, 43))
        
        # Remplissage automatique
        for role in Role:
            self.team_blue.roster[role] = CalibrationTools.generate_balanced_player(role, "elite")
            self.team_red.roster[role] = CalibrationTools.generate_balanced_player(role, "pro")
            
        # Initialisation du MatchSimulator
        self.match_simulator = MatchSimulator(self.team_blue, self.team_red)
        
        # Initialisation du MatchDashboard
        self.match_dashboard = MatchDashboard(self.screen, self.match_simulator)

        # Initialisation de la Ligue (pour gérer les coûts hebdomadaires)
        from moba_manager import League
        self.league = League("Worlds 2025", [self.team_blue, self.team_red])
        
        # Initialisation du DraftManager
        self.draft_manager = DraftManager(self.screen)
        # Initialisation du MarketManager
        self.market_manager = MarketManager(self.screen, self.league.market, self.team_blue.finance, self.draw_radar_chart)
        
        self.team_name = self.team_blue.name
        self.budget = self.team_blue.budget
        self.current_year = 2025
        
        # Chronomètre pour la simulation (ms)
        self.sim_timer = 0
        
        # Gestion du Roster
        self.selected_player_index = 0
        self.selected_starter_role = None
        self.selected_bench_idx = None
        self.roster_view_mode = "starters" # "starters" ou "bench"



    def run(self):
        """La boucle principale du jeu (The Game Loop)"""
        while self.running:
            # 1. GESTION DES ÉVÉNEMENTS
            self.handle_events()
            
            # 2. MISE À JOUR
            self.update()
            
            # 3. DESSIN
            self.draw()
            
            # Contrôle des FPS
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.current_state == STATE_MAIN_MENU:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_main_menu_click(event.pos)

            if self.current_state == STATE_SETTINGS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.current_state = STATE_MAIN_MENU
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_settings_click(event.pos)
            
            # Navigation
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:
                    self._quick_save()
                elif event.key == pygame.K_F9:
                    self._quick_load(keep_state=True)
                if event.key == pygame.K_h:
                    self.current_state = STATE_HOME
                elif event.key == pygame.K_r:
                    self.current_state = STATE_ROSTER
                elif event.key == pygame.K_d:
                    self.current_state = STATE_DRAFT
                elif event.key == pygame.K_m:
                    self.current_state = STATE_MARKET
                elif event.key == pygame.K_SPACE:
                    if self.current_state == STATE_MATCH and self.match_simulator.is_finished:
                        self.current_state = STATE_HOME
                    else:
                        # Lancement manuel si draft finie (depuis draft ou accueil)
                        is_draft_ready = self.draft_manager.current_step >= 10
                        if (self.current_state == STATE_DRAFT or self.current_state == STATE_HOME) and is_draft_ready:
                            self.finalize_draft()

            # Gestion des événements spécifiques à l'état
            if self.current_state == STATE_SETUP:
                self.setup_manager.handle_event(event)
            elif self.current_state == STATE_MATCH:
                self.match_dashboard.handle_event(event)
            elif self.current_state == STATE_DRAFT:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.draft_manager.handle_click(event.pos)
            elif self.current_state == STATE_MARKET:
                res = self.market_manager.handle_event(event)
                if isinstance(res, tuple) and res[0] == "PURCHASE_SUCCESS":
                    new_player = res[1]
                    print(f"Nouveau joueur recruté : {new_player.name}")
                    # On l'ajoute directement à la réserve
                    self.team_blue.bench.append(new_player)

            if self.current_state == STATE_HOME:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_home_click(event.pos)





    def update(self):
        if self.current_state in {STATE_MAIN_MENU, STATE_SETTINGS}:
            return
        if self.current_state == STATE_SETUP:
            if self.setup_manager.done:
                self.team_blue = create_initial_roster(
                    self.setup_manager.team_name,
                    self.setup_manager.coach_name,
                    self.setup_manager.selected_color,
                    specialization=self.setup_manager.specialization,
                    prestige=70,
                    kit_name=self.setup_manager.selected_pack
                )
                self.team_blue.logo_shape = self.setup_manager.selected_shape
                self.team_blue.specialization = self.setup_manager.specialization
                self.team_name = self.team_blue.name

                from moba_manager import League
                self.league = League("Worlds 2025", [self.team_blue, self.team_red])
                self.market_manager = MarketManager(self.screen, self.league.market, self.team_blue.finance, self.draw_radar_chart)

                self.match_simulator = MatchSimulator(self.team_blue, self.team_red)
                self.match_dashboard = MatchDashboard(self.screen, self.match_simulator)

                self.draft_manager.color_a = self.team_blue.team_color
                self.match_dashboard.BLUE = self.team_blue.team_color

                self.current_state = STATE_HOME
        elif self.current_state == STATE_DRAFT:
            self.draft_manager.update() # L'IA surveille son tour ici
        elif self.current_state == STATE_MATCH:
            # On régule la vitesse : 1 minute de match par seconde réelle à x1
            if not self.match_simulator.is_finished:
                self.sim_timer += self.clock.get_time()
                if self.sim_timer >= 1000: # 1 seconde
                    self.match_dashboard.update()
                    self.sim_timer = 0
                    
                    # Vérifier si le match vient de se terminer
                    if self.match_simulator.is_finished:
                        print("Match terminé !")
                        # Reward distribution is now handled inside simulate_step
                        
                        # Bonus financier
                        won = self.match_simulator.winner == "A"
                        amount = self.team_blue.finance.add_match_bonus(won)
                        print(f"Bonus financier : +{amount}$")
                        
                        # Passage de la semaine (Salaires / Sponsors)
                        self.league.process_week()
                        
                        # Vérification Faillite
                        if self.team_blue.finance.budget <= 0:
                            print("FAILLITE ! Votre budget est épuisé.")
                            # On pourrait ajouter un écran de Game Over ici



    def draw(self):
        self.screen.fill(BG_DARK)

        if self.current_state == STATE_MAIN_MENU:
            self.draw_main_menu()
            self._draw_fps_overlay()
            pygame.display.flip()
            return

        if self.current_state == STATE_SETTINGS:
            self.draw_settings()
            self._draw_fps_overlay()
            pygame.display.flip()
            return
        
        if self.current_state == STATE_HOME:
            self.draw_home()
        elif self.current_state == STATE_ROSTER:
            self.draw_roster()
        elif self.current_state == STATE_MATCH:
            self.draw_match()
        elif self.current_state == STATE_DRAFT:
            self.draft_manager.draw()
        elif self.current_state == STATE_MARKET:
            self.market_manager.draw()
        elif self.current_state == STATE_SETUP:
            self.setup_manager.draw()
            
        self._draw_fps_overlay()
        self._draw_toast()
        pygame.display.flip()

    def _draw_fps_overlay(self):
        if not self.settings.get("show_fps", False):
            return
        fps = self.clock.get_fps()
        surf = self.small_font.render(f"FPS: {fps:.0f}", True, (200, 200, 200))
        self.screen.blit(surf, (10, 10))

    def _draw_toast(self):
        if not self.toast_msg:
            return
        if pygame.time.get_ticks() > self.toast_until_ms:
            self.toast_msg = ""
            return
        surf = self.small_font.render(self.toast_msg, True, (240, 240, 240))
        pad_x = 10
        pad_y = 6
        rect = pygame.Rect(0, 0, surf.get_width() + pad_x * 2, surf.get_height() + pad_y * 2)
        rect.midbottom = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 10)
        pygame.draw.rect(self.screen, (10, 10, 15), rect, border_radius=8)
        pygame.draw.rect(self.screen, (60, 60, 75), rect, width=1, border_radius=8)
        self.screen.blit(surf, (rect.x + pad_x, rect.y + pad_y))

    def _handle_home_click(self, pos):
        for key, rect in self.home_buttons.items():
            if not rect.collidepoint(pos):
                continue
            if key == "save":
                self._quick_save()
                return
            if key == "load":
                self._quick_load(keep_state=True)
                return

    def _set_setup_state(self):
        from gui_setup import ProfileSetup
        self.setup_manager = ProfileSetup(self.screen)
        self.current_state = STATE_SETUP

    def _apply_loaded_league(self, league):
        teams = getattr(league, "teams", None) or []
        if len(teams) < 2:
            return False

        self.league = league
        self.team_blue = teams[0]
        self.team_red = teams[1]
        self.team_name = self.team_blue.name

        self.market_manager = MarketManager(self.screen, self.league.market, self.team_blue.finance, self.draw_radar_chart)
        self.match_simulator = MatchSimulator(self.team_blue, self.team_red)
        self.match_dashboard = MatchDashboard(self.screen, self.match_simulator)

        self.draft_manager = DraftManager(self.screen)
        self.draft_manager.color_a = self.team_blue.team_color
        self.match_dashboard.BLUE = self.team_blue.team_color
        self.match_dashboard.RED = self.team_red.team_color
        return True

    def _set_toast(self, msg: str, duration_ms: int = 2000):
        self.toast_msg = msg
        self.toast_until_ms = pygame.time.get_ticks() + duration_ms

    def _quick_save(self):
        try:
            save_game(self.league, "savegame.json")
            self._set_toast("Sauvegarde OK")
        except Exception:
            self._set_toast("Erreur sauvegarde")

    def _quick_load(self, keep_state: bool = True):
        previous_state = self.current_state
        league = None
        try:
            league = load_game("savegame.json")
        except Exception:
            league = None

        if not league:
            self._set_toast("Aucune sauvegarde")
            return

        if not self._apply_loaded_league(league):
            self._set_toast("Erreur chargement")
            return

        self._set_toast("Chargement OK")
        if keep_state:
            if previous_state in {STATE_MAIN_MENU, STATE_SETTINGS, STATE_SETUP}:
                self.current_state = STATE_HOME
            else:
                self.current_state = previous_state
        else:
            self.current_state = STATE_HOME

    def _handle_main_menu_click(self, pos):
        for key, rect in self.menu_buttons.items():
            if not rect.collidepoint(pos):
                continue
            if key == "new":
                self._set_setup_state()
                return
            if key == "load":
                self._quick_load(keep_state=False)
                return
            if key == "settings":
                self.current_state = STATE_SETTINGS
                return
            if key == "quit":
                self.running = False
                return

    def _handle_settings_click(self, pos):
        for key, rect in self.settings_buttons.items():
            if not rect.collidepoint(pos):
                continue
            if key == "toggle_fps":
                self.settings["show_fps"] = not self.settings.get("show_fps", False)
                return
            if key == "back":
                self.current_state = STATE_MAIN_MENU
                return

    def draw_main_menu(self):
        self.screen.fill(BG_DARK)

        title = self.title_font.render("MOBA MANAGER 2025", True, GOLD)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 90))

        btn_w = 420
        btn_h = 60
        start_y = 240
        gap = 18

        items = [
            ("new", "Nouvelle partie"),
            ("load", "Charger partie"),
            ("settings", "Paramètres"),
            ("quit", "Quitter"),
        ]

        self.menu_buttons = {}
        for i, (key, label) in enumerate(items):
            rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, start_y + i * (btn_h + gap), btn_w, btn_h)
            self.menu_buttons[key] = rect

            is_hover = rect.collidepoint(pygame.mouse.get_pos())
            bg = (45, 45, 60) if not is_hover else (60, 60, 80)
            pygame.draw.rect(self.screen, bg, rect, border_radius=12)
            pygame.draw.rect(self.screen, (90, 90, 110), rect, width=2, border_radius=12)

            txt = self.text_font.render(label, True, WHITE)
            self.screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        hint = self.small_font.render("Astuce: [H] Home, [D] Draft, [M] Market, [R] Roster", True, (140, 140, 155))
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 660))

    def draw_settings(self):
        self.screen.fill(BG_DARK)

        title = self.title_font.render("PARAMÈTRES", True, GOLD)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 90))

        panel = pygame.Rect(SCREEN_WIDTH // 2 - 360, 200, 720, 360)
        pygame.draw.rect(self.screen, (20, 20, 30), panel, border_radius=14)
        pygame.draw.rect(self.screen, (50, 50, 65), panel, width=2, border_radius=14)

        self.settings_buttons = {}

        toggle_rect = pygame.Rect(panel.x + 60, panel.y + 80, panel.w - 120, 60)
        self.settings_buttons["toggle_fps"] = toggle_rect
        is_hover = toggle_rect.collidepoint(pygame.mouse.get_pos())
        bg = (45, 45, 60) if not is_hover else (60, 60, 80)
        pygame.draw.rect(self.screen, bg, toggle_rect, border_radius=12)
        pygame.draw.rect(self.screen, (90, 90, 110), toggle_rect, width=2, border_radius=12)
        value = "ON" if self.settings.get("show_fps", False) else "OFF"
        txt = self.text_font.render(f"Afficher FPS : {value}", True, WHITE)
        self.screen.blit(txt, (toggle_rect.centerx - txt.get_width() // 2, toggle_rect.centery - txt.get_height() // 2))

        back_rect = pygame.Rect(panel.x + 60, panel.bottom - 100, panel.w - 120, 60)
        self.settings_buttons["back"] = back_rect
        is_hover = back_rect.collidepoint(pygame.mouse.get_pos())
        bg = (45, 45, 60) if not is_hover else (60, 60, 80)
        pygame.draw.rect(self.screen, bg, back_rect, border_radius=12)
        pygame.draw.rect(self.screen, (90, 90, 110), back_rect, width=2, border_radius=12)
        txt = self.text_font.render("Retour", True, WHITE)
        self.screen.blit(txt, (back_rect.centerx - txt.get_width() // 2, back_rect.centery - txt.get_height() // 2))


    # --- LES PAGES ---
    
    def draw_home(self):
        """Dessine la page d'accueil avec le menu principal."""
        self.screen.fill(BG_DARK)
        
        # Titre
        title = self.title_font.render("MOBA MANAGER 2025", True, self.team_blue.team_color)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        # Équipe et Budget
        draw_team_logo(self.screen, 130, 260, 20, self.team_blue.logo_shape, self.team_blue.team_color)
        team_txt = self.text_font.render(f"Manager de : {self.team_name}", True, WHITE)
        budget = self.team_blue.finance.budget
        budget_color = (0, 255, 100) if budget > 0 else (255, 50, 50)
        budget_txt = self.text_font.render(f"Budget : {budget:,} $", True, budget_color)
        self.screen.blit(team_txt, (165, 250))
        self.screen.blit(budget_txt, (100, 310))
        
        if budget <= 0:
            warn_txt = self.text_font.render("ATTENTION : VOTRE ORGANISATION EST EN FAILLITE !", True, (255, 50, 50))
            self.screen.blit(warn_txt, (100, 350))

        # Instructions
        instr = [
            "[D] Commencer un Match (Draft)",
            "[R] Voir le Roster (Equipe)",
            "[M] Marché des Transferts",
            "[H] Revenir au Menu",
            "[Echap] Quitter"
        ]
        for i, text in enumerate(instr):
            surf = self.text_font.render(text, True, (200, 200, 200))
            self.screen.blit(surf, (100, 400 + (i * 40)))

        self.home_buttons = {}
        btn_w = 240
        btn_h = 44
        btn_y = 250
        save_rect = pygame.Rect(SCREEN_WIDTH - btn_w - 60, btn_y, btn_w, btn_h)
        load_rect = pygame.Rect(SCREEN_WIDTH - btn_w - 60, btn_y + btn_h + 12, btn_w, btn_h)
        self.home_buttons["save"] = save_rect
        self.home_buttons["load"] = load_rect

        for label, rect in (("Sauvegarder", save_rect), ("Charger", load_rect)):
            is_hover = rect.collidepoint(pygame.mouse.get_pos())
            bg = (45, 45, 60) if not is_hover else (60, 60, 80)
            pygame.draw.rect(self.screen, bg, rect, border_radius=10)
            pygame.draw.rect(self.screen, (90, 90, 110), rect, width=2, border_radius=10)
            txt = self.small_font.render(label, True, WHITE)
            self.screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
            
        if self.draft_manager.current_step >= 10:
             tip = self.text_font.render("Draft prête ! Appuyez sur ESPACE pour lancer le match", True, (255, 255, 100))
             self.screen.blit(tip, (100, 600))

    def draw_roster(self):
        """Page de gestion de l'équipe avec Starters, Banc et Swap logic."""
        self.screen.fill(BG_DARK)
        
        # Titre et Budget
        draw_team_logo(self.screen, 460, 55, 15, self.team_blue.logo_shape, self.team_blue.team_color)
        title_surf = self.title_font.render("GESTION DU ROSTER", True, WHITE)
        budget = self.team_blue.finance.budget
        budget_color = (100, 255, 100) if budget > 0 else (255, 50, 50)
        budget_surf = self.text_font.render(f"Fonds: {budget:,} $", True, budget_color)
        self.screen.blit(title_surf, (50, 30))
        self.screen.blit(budget_surf, (SCREEN_WIDTH - budget_surf.get_width() - 50, 40))
        
        # 1. Zone des TITULAIRES (Starters) - À Gauche Haut
        roles_list = [Role.TOP, Role.JUNGLE, Role.MID, Role.ADC, Role.SUPPORT]
        start_y = 120
        
        starter_label = self.text_font.render("TITULAIRES", True, GOLD)
        self.screen.blit(starter_label, (50, start_y - 35))
        
        self.starter_rects = []
        for i, r in enumerate(roles_list):
            p = self.team_blue.roster[r]
            rect = pygame.Rect(50, start_y + (i * 75), 380, 70)
            self.starter_rects.append((rect, r))
            
            # Couleur selon sélection
            color = (50, 80, 200) if self.selected_starter_role == r else (40, 40, 60)
            if self.roster_view_mode == "starters" and i == self.selected_player_index:
                color = ESPORT_BLUE
                
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            
            if p:
                name_txt = self.text_font.render(p.name, True, WHITE)
                role_txt = self.small_font.render(r.value, True, (200, 200, 200))
                self.screen.blit(name_txt, (rect.x + 15, rect.y + 10))
                self.screen.blit(role_txt, (rect.x + 15, rect.y + 40))
            else:
                self.screen.blit(self.text_font.render("VIDE", True, (100, 100, 100)), (rect.x + 15, rect.y + 20))

            # Clic Starters
            if pygame.mouse.get_pressed()[0] and rect.collidepoint(pygame.mouse.get_pos()):
                self.selected_starter_role = r
                self.selected_player_index = i
                self.roster_view_mode = "starters"

        # 2. Zone de la RÉSERVE (Bench) - À Gauche Bas
        bench_y = 530
        bench_label = self.text_font.render("RÉSERVE", True, (150, 150, 150))
        self.screen.blit(bench_label, (50, bench_y - 35))
        
        bench_rect_container = pygame.Rect(50, bench_y, 380, 150)
        pygame.draw.rect(self.screen, (25, 25, 35), bench_rect_container, border_radius=10)
        
        if not self.team_blue.bench:
            self.screen.blit(self.small_font.render("Aucun joueur en réserve", True, (80, 80, 80)), (70, bench_y + 20))
        
        self.bench_rects = []
        # On affiche les joueurs sur le banc (limité à 3 pour l'affichage simple)
        num_bench = len(self.team_blue.bench)
        for i in range(min(num_bench, 4)): 
            p = self.team_blue.bench[i]
            rect = pygame.Rect(60, bench_y + 10 + (i * 40), 360, 35)
            self.bench_rects.append(rect)
            
            color = (150, 100, 50) if self.selected_bench_idx == i else (40, 40, 50)
            if self.roster_view_mode == "bench" and i == self.selected_player_index:
                color = (100, 150, 255)
            
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            name_txt = self.small_font.render(f"{p.name} ({p.tier})", True, WHITE)
            self.screen.blit(name_txt, (rect.x + 10, rect.y + 10))
            
            # Clic Bench
            if pygame.mouse.get_pressed()[0] and rect.collidepoint(pygame.mouse.get_pos()):
                self.selected_bench_idx = i
                self.selected_player_index = i
                self.roster_view_mode = "bench"

        # 3. LOGIQUE DE SWAP
        if self.selected_starter_role and self.selected_bench_idx is not None:
            # On tente le swap
            if self.team_blue.swap_players(self.selected_starter_role, self.selected_bench_idx):
                print("Swap effectué !")
                # Reset sélection
                self.selected_starter_role = None
                self.selected_bench_idx = None

        # 4. Panneau de détails à droite
        # On récupère le joueur à afficher
        p_to_show = None
        if self.roster_view_mode == "starters":
            if self.selected_player_index < len(roles_list):
                p_to_show = self.team_blue.roster[roles_list[self.selected_player_index]]
        elif self.roster_view_mode == "bench":
            if self.team_blue.bench and self.selected_player_index < len(self.team_blue.bench):
                 p_to_show = self.team_blue.bench[self.selected_player_index]

        if p_to_show:
            p = p_to_show
            panel_rect = pygame.Rect(450, 120, 780, 520)
            pygame.draw.rect(self.screen, (40, 40, 55), panel_rect, border_radius=15)
            
            # Informations texte
            p_title = self.title_font.render(p.name, True, WHITE)
            p_lvl = self.text_font.render(f"Niveau {p.level} | Age: {p.age}", True, GOLD)
            p_salary = self.text_font.render(f"Salaire: {p.salary:,} $ / sem.", True, (100, 255, 100))
            self.screen.blit(p_title, (panel_rect.x + 40, panel_rect.y + 20))
            self.screen.blit(p_lvl, (panel_rect.x + 40, panel_rect.y + 70))
            self.screen.blit(p_salary, (panel_rect.x + 40, panel_rect.y + 110))
            
            # Stats détaillées
            stats_list = [
                (f"Mécaniques (MEC): {p.mec}", (255, 100, 100)),
                (f"Macro (MAC): {p.mac}", (100, 255, 100)),
                (f"Vision (VIS): {p.vis}", (100, 100, 255)),
                (f"Sang-froid (SNG): {p.sng}", (255, 255, 100))
            ]
            for j, (txt, color) in enumerate(stats_list):
                s_surf = self.text_font.render(txt, True, color)
                self.screen.blit(s_surf, (panel_rect.x + 40, panel_rect.y + 200 + (j * 40)))

            # XP Bar
            xp_rect = pygame.Rect(panel_rect.x + 40, panel_rect.y + 400, 300, 20)
            pygame.draw.rect(self.screen, (60, 60, 70), xp_rect, border_radius=10)
            progress_w = int((p.xp / 1000) * 300)
            pygame.draw.rect(self.screen, (0, 255, 100), (xp_rect.x, xp_rect.y, progress_w, 20), border_radius=10)
            xp_text = self.text_font.render(f"XP: {p.xp} / 1000", True, WHITE)
            self.screen.blit(xp_text, (xp_rect.x, xp_rect.y + 30))

            # Radar Chart
            stats_map = {"MEC": p.mec, "MAC": p.mac, "VIS": p.vis, "SNG": p.sng}
            self.draw_radar_chart(self.screen, panel_rect.right - 200, panel_rect.centery, 120, stats_map, (41, 98, 255, 150))

        # Tip
        tip = self.small_font.render("CLIQUEZ SUR UN TITULAIRE PUIS UN REMPLAÇANT POUR ÉCHANGER", True, GOLD)
        self.screen.blit(tip, (SCREEN_WIDTH // 2 - tip.get_width() // 2, 680))

    def draw_match(self):
        """Page du Dashboard de Match"""
        self.match_dashboard.draw()

        
        # Petit rappel pour quitter le mode match
        tip_text = self.text_font.render("Appuyez sur 'H' pour revenir à l'Accueil", True, (100, 100, 100))
        self.screen.blit(tip_text, (350, 650))

    def draw_radar_chart(self, screen, x, y, size, stats, color):
        """Dessine un polygone basé sur les 4 axes de statistiques."""
        labels = list(stats.keys())
        values = list(stats.values())
        num_vars = len(labels)
        
        # Fond (grille)
        for r in [0.25, 0.5, 0.75, 1.0]:
            pygame.draw.circle(screen, (70, 70, 90), (x, y), int(size * r), 1)
        
        # Axes
        angle_step = (2 * math.pi) / num_vars
        for i in range(num_vars):
            angle = i * angle_step - math.pi / 2
            ax = x + size * math.cos(angle)
            ay = y + size * math.sin(angle)
            pygame.draw.line(screen, (80, 80, 100), (x, y), (ax, ay), 1)
            
            # Label
            label_surf = self.text_font.render(labels[i], True, (200, 200, 200))
            lx = x + (size + 25) * math.cos(angle) - label_surf.get_width() // 2
            ly = y + (size + 25) * math.sin(angle) - label_surf.get_height() // 2
            screen.blit(label_surf, (lx, ly))

        # Calcul des points du polygone de stats
        points = []
        for i in range(num_vars):
            radius = (values[i] / 100) * size
            angle = i * angle_step - math.pi / 2
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append((px, py))
            
        # Dessin du polygone (remplissage avec transparence simulée via surface si nécessaire, 
        # mais ici on fait simple pour Pygame standard)
        if len(points) >= 3:
            # On utilise une version légèrement transparente si possible, sinon solide
            c = self.team_blue.team_color
            pygame.draw.polygon(screen, (c[0], c[1], c[2]), points, 0)
            pygame.draw.polygon(screen, WHITE, points, 2)

    def finalize_draft(self):
        """Transfère les choix de la draft vers les joueurs avant le match."""
        from moba_manager import CHAMPIONS_DB
        
        picks_a = self.draft_manager.picks_a
        picks_b = self.draft_manager.picks_b

        # 1. Préparation des dictionnaires de champions (Mapping Rôles)
        roles = [Role.TOP, Role.JUNGLE, Role.MID, Role.ADC, Role.SUPPORT]
        blue_mapping = {}
        red_mapping = {}
        
        for i, role in enumerate(roles):
            if i < len(picks_a):
                blue_mapping[role] = CHAMPIONS_DB[picks_a[i]]
            if i < len(picks_b):
                red_mapping[role] = CHAMPIONS_DB[picks_b[i]]

        # 2. Création d'un simulateur "frais" avec les bons picks
        self.match_simulator = MatchSimulator(self.team_blue, self.team_red)
        self.match_simulator.blue_picks = blue_mapping
        self.match_simulator.red_picks = red_mapping
        
        # 3. Synchronisation des objets Player (pour le HUD)
        for role, champ in blue_mapping.items():
            p = self.team_blue.roster.get(role)
            if p: p.current_hero = champ.name  # noqa: E701
                
        for role, champ in red_mapping.items():
            p = self.team_red.roster.get(role)
            if p: p.current_hero = champ.name  # noqa: E701

        # 4. Mise à jour du Dashboard et transition
        self.match_dashboard = MatchDashboard(self.screen, self.match_simulator)
        self.current_state = STATE_MATCH

if __name__ == "__main__":


    game = MobaGui()
    game.run()
