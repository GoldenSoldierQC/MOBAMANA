import math
import random
from typing import Optional

import pygame
from .gui_setup import draw_team_logo

WHITE = (255, 255, 255)

class KillNotification:
    def __init__(self, text, color, duration_ms=3000):
        self.text = text
        self.color = color
        self.start_time = pygame.time.get_ticks()
        self.duration = duration_ms
        self.y_offset = -50

    def is_expired(self):
        return pygame.time.get_ticks() - self.start_time > self.duration

    def draw(self, screen, font):
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time
        
        if elapsed < 500:
            self.y_offset = -50 + (elapsed / 500) * 120
        elif elapsed > self.duration - 500:
            self.y_offset = 70 - ((elapsed - (self.duration - 500)) / 500) * 120
        else:
            self.y_offset = 70

        rect = pygame.Rect(440, self.y_offset, 400, 45)
        pygame.draw.rect(screen, (20, 20, 30), rect, border_radius=10)
        pygame.draw.rect(screen, self.color, rect, 2, border_radius=10)
        
        txt_surf = font.render(self.text, True, (255, 255, 255))
        screen.blit(txt_surf, (rect.centerx - txt_surf.get_width()//2, rect.centery - txt_surf.get_height()//2))

class EnhancedMinimap:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

        self.lanes = {
            "BASE_A": (self.rect.x + width * 0.12, self.rect.y + height * 0.88),
            "BASE_B": (self.rect.x + width * 0.88, self.rect.y + height * 0.12),
            "TOP": (self.rect.x + width * 0.25, self.rect.y + height * 0.25),
            "MID": (self.rect.x + width * 0.50, self.rect.y + height * 0.50),
            "BOT": (self.rect.x + width * 0.75, self.rect.y + height * 0.75),
            "JUNGLE_TOP": (self.rect.x + width * 0.42, self.rect.y + height * 0.32),
            "JUNGLE_BOT": (self.rect.x + width * 0.58, self.rect.y + height * 0.68),
        }

        self.player_positions = {}
        self.player_targets = {}
        self.movement_history = {}
        self.map_events = []

        self._last_tick_ms = pygame.time.get_ticks()

    def update_player_action(self, player, team_side: str, game_phase, current_minute):
        player_id = id(player)
        target_pos = self._calculate_target_position(player, team_side, game_phase)

        if player_id not in self.player_positions:
            self.player_positions[player_id] = target_pos
            self.player_targets[player_id] = target_pos
        else:
            self.player_targets[player_id] = target_pos

    def _is_player_dead(self, player) -> bool:
        return bool(
            getattr(player, "is_dead", False)
            or getattr(player, "dead", False)
            or getattr(player, "is_ko", False)
        )

    def _calculate_target_position(self, player, team_side: str, game_phase):
        if self._is_player_dead(player):
            return self.lanes["BASE_A"] if team_side == "A" else self.lanes["BASE_B"]

        role_name = getattr(getattr(player, "role", None), "name", None)
        if not role_name:
            role_name = str(getattr(player, "role", "MID"))
        role_name = role_name.upper()

        priority = getattr(player, "priority", "Lane")

        if role_name == "JUNGLE":
            if priority == "Roam":
                return random.choice([
                    self.lanes["JUNGLE_TOP"],
                    self.lanes["JUNGLE_BOT"],
                    self.lanes["MID"],
                ])
            return self.lanes["JUNGLE_TOP"]

        if priority == "Roam" and role_name in {"SUPPORT", "ADC"}:
            return self.lanes["MID"]

        if priority == "Obj":
            return self.lanes["MID"]

        if role_name == "TOP":
            return self.lanes["TOP"]
        if role_name in {"ADC", "SUPPORT"}:
            return self.lanes["BOT"]
        return self.lanes["MID"]

    def interpolate_positions(self, delta_time: Optional[float] = None):
        if delta_time is None:
            now = pygame.time.get_ticks()
            delta_time = max(0.0, (now - self._last_tick_ms) / 1000.0)
            self._last_tick_ms = now

        speed = 220.0
        step = speed * delta_time
        if step <= 0:
            return

        for player_id in list(self.player_positions.keys()):
            current = self.player_positions[player_id]
            target = self.player_targets.get(player_id, current)

            dx = target[0] - current[0]
            dy = target[1] - current[1]
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < 1.5:
                self.player_positions[player_id] = target
                continue

            ratio = min(1.0, step / distance)
            new_pos = (current[0] + dx * ratio, current[1] + dy * ratio)
            self.player_positions[player_id] = new_pos

            history = self.movement_history.setdefault(player_id, [])
            history.append((*new_pos, pygame.time.get_ticks()))
            if len(history) > 20:
                history.pop(0)

    def register_event(self, x, y, event_type):
        self.map_events.append((x, y, event_type, pygame.time.get_ticks()))
        current_time = pygame.time.get_ticks()
        self.map_events = [e for e in self.map_events if current_time - e[3] < 5000]

    def draw(self, screen, team_a_players, team_b_players, color_a, color_b, momentum_ratio=0.0):
        pygame.draw.rect(screen, (20, 25, 35), self.rect, border_radius=10)
        pygame.draw.rect(screen, (60, 60, 70), self.rect, 2, border_radius=10)

        # Dessiner la ligne de front (momentum visuel)
        self._draw_front_line(screen, momentum_ratio)
        
        self._draw_lanes(screen)
        self._draw_map_events(screen)
        self._draw_players(screen, team_a_players, color_a)
        self._draw_players(screen, team_b_players, color_b)

    def _draw_front_line(self, screen, ratio):
        """Dessine une ombre colorée représentant le contrôle du terrain."""
        # ratio: -1 (Rouge domine) à 1 (Bleu domine)
        center_x = self.rect.centerx + (ratio * (self.rect.width // 2))
        
        # Zone Bleue (Influence gauche/bas)
        blue_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(blue_surf, (41, 128, 185, 40), (0, 0, center_x - self.rect.x, self.rect.height))
        screen.blit(blue_surf, self.rect.topleft)
        
        # Zone Rouge (Influence droite/haut)
        red_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(red_surf, (192, 57, 43, 40), (center_x - self.rect.x, 0, self.rect.right - center_x, self.rect.height))
        screen.blit(red_surf, self.rect.topleft)

        # La ligne de démarcation
        pygame.draw.line(screen, (255, 255, 255, 100), (center_x, self.rect.y), (center_x, self.rect.bottom), 2)

    def _draw_lanes(self, screen):
        inset = 10
        inner = self.rect.inflate(-inset * 2, -inset * 2)
        a = (int(inner.x + inner.w * 0.10), int(inner.y + inner.h * 0.90))
        b = (int(inner.x + inner.w * 0.90), int(inner.y + inner.h * 0.10))
        mid = (int(inner.centerx), int(inner.centery))

        top_lane_start = (int(inner.x + inner.w * 0.12), int(inner.y + inner.h * 0.22))
        top_lane_end = (int(inner.x + inner.w * 0.78), int(inner.y + inner.h * 0.12))
        bot_lane_start = (int(inner.x + inner.w * 0.22), int(inner.y + inner.h * 0.88))
        bot_lane_end = (int(inner.x + inner.w * 0.88), int(inner.y + inner.h * 0.78))

        river1 = (int(inner.x + inner.w * 0.18), int(inner.y + inner.h * 0.55))
        river2 = (int(inner.x + inner.w * 0.55), int(inner.y + inner.h * 0.18))
        river3 = (int(inner.x + inner.w * 0.45), int(inner.y + inner.h * 0.82))
        river4 = (int(inner.x + inner.w * 0.82), int(inner.y + inner.h * 0.45))

        jungle_a = [(inner.x, inner.y + inner.h), (inner.x, int(inner.y + inner.h * 0.55)), (int(inner.x + inner.w * 0.55), inner.y + inner.h)]
        jungle_b = [(inner.x + inner.w, inner.y), (int(inner.x + inner.w * 0.45), inner.y), (inner.x + inner.w, int(inner.y + inner.h * 0.45))]
        pygame.draw.polygon(screen, (18, 38, 28), jungle_a)
        pygame.draw.polygon(screen, (18, 38, 28), jungle_b)

        pygame.draw.line(screen, (22, 42, 72), river1, river2, 6)
        pygame.draw.line(screen, (22, 42, 72), river3, river4, 6)
        pygame.draw.line(screen, (34, 60, 105), river1, river2, 2)
        pygame.draw.line(screen, (34, 60, 105), river3, river4, 2)

        lane_color = (70, 70, 85)
        lane_edge = (110, 110, 130)

        pygame.draw.line(screen, lane_color, a, mid, 6)
        pygame.draw.line(screen, lane_edge, a, mid, 2)
        pygame.draw.line(screen, lane_color, mid, b, 6)
        pygame.draw.line(screen, lane_edge, mid, b, 2)

        pygame.draw.line(screen, lane_color, top_lane_start, top_lane_end, 5)
        pygame.draw.line(screen, lane_edge, top_lane_start, top_lane_end, 2)
        pygame.draw.line(screen, lane_color, bot_lane_start, bot_lane_end, 5)
        pygame.draw.line(screen, lane_edge, bot_lane_start, bot_lane_end, 2)

        base_a = self.lanes["BASE_A"]
        base_b = self.lanes["BASE_B"]
        pygame.draw.circle(screen, (45, 120, 210), (int(base_a[0]), int(base_a[1])), 9)
        pygame.draw.circle(screen, (255, 255, 255), (int(base_a[0]), int(base_a[1])), 9, 2)
        pygame.draw.circle(screen, (210, 70, 70), (int(base_b[0]), int(base_b[1])), 9)
        pygame.draw.circle(screen, (255, 255, 255), (int(base_b[0]), int(base_b[1])), 9, 2)

        tower_color = (140, 140, 155)
        for t in (
            (inner.x + inner.w * 0.22, inner.y + inner.h * 0.78),
            (inner.x + inner.w * 0.32, inner.y + inner.h * 0.68),
            (inner.x + inner.w * 0.42, inner.y + inner.h * 0.58),
            (inner.x + inner.w * 0.58, inner.y + inner.h * 0.42),
            (inner.x + inner.w * 0.68, inner.y + inner.h * 0.32),
            (inner.x + inner.w * 0.78, inner.y + inner.h * 0.22),
        ):
            pygame.draw.circle(screen, tower_color, (int(t[0]), int(t[1])), 3)

    def _draw_map_events(self, screen):
        current_time = pygame.time.get_ticks()
        for x, y, event_type, timestamp in self.map_events:
            age = current_time - timestamp
            alpha = max(0, 255 - (age / 5000) * 255)

            if event_type == "KILL":
                color = (255, 50, 50, int(alpha))
                pygame.draw.circle(screen, color[:3], (int(x), int(y)), 12, 2)
            elif event_type == "OBJECTIVE":
                color = (255, 215, 0, int(alpha))
                pygame.draw.circle(screen, color[:3], (int(x), int(y)), 15, 3)

    def _draw_players(self, screen, players, color):
        for player in players:
            player_id = id(player)
            if player_id not in self.player_positions:
                continue

            pos = self.player_positions[player_id]
            pygame.draw.circle(screen, color, (int(pos[0]), int(pos[1])), 6)
            pygame.draw.circle(screen, (255, 255, 255), (int(pos[0]), int(pos[1])), 6, 1)


class Slider:
    def __init__(self, x, y, w, h, label, min_val=0.5, max_val=1.5):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.val = (min_val + max_val) / 2 # Valeur par défaut (1.0)
        self.grabbed = False

    def draw(self, screen, font):
        # Label sous le slider
        lbl_txt = font.render(self.label, True, (180, 180, 180))
        screen.blit(lbl_txt, (self.rect.x, self.rect.y - 22))
        
        # Valeur à droite
        val_txt = font.render(f"{self.val:.2f}x", True, (212, 175, 55))
        screen.blit(val_txt, (self.rect.right + 10, self.rect.y - 5))

        # Barre de fond
        pygame.draw.rect(screen, (40, 40, 50), self.rect, border_radius=self.rect.h//2)
        # Remplissage actif
        active_w = int((self.val - self.min_val) / (self.max_val - self.min_val) * self.rect.w)
        if active_w > 0:
            active_rect = pygame.Rect(self.rect.x, self.rect.y, active_w, self.rect.h)
            pygame.draw.rect(screen, (100, 100, 120), active_rect, border_radius=self.rect.h//2)
            
        # Curseur
        pos_x = self.rect.x + active_w
        pygame.draw.circle(screen, (255, 255, 255), (pos_x, self.rect.centery), self.rect.h + 2)
        pygame.draw.circle(screen, (212, 175, 55), (pos_x, self.rect.centery), self.rect.h - 1)

    def handle_event(self, event):
        """Gère le drag-and-drop du slider."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.inflate(20, 20).collidepoint(event.pos):
                self.grabbed = True
                self.update_val(event.pos)
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.grabbed = False
        elif event.type == pygame.MOUSEMOTION and self.grabbed:
            self.update_val(event.pos)
            return True

        return False

    def update_val(self, mouse_pos):
        rel_x = max(0, min(mouse_pos[0] - self.rect.x, self.rect.w))
        self.val = self.min_val + (rel_x / self.rect.w) * (self.max_val - self.min_val)


class MatchDashboard:
    def __init__(self, screen, match_engine):
        self.screen = screen
        self.engine = match_engine  # Instance de MatchSimulator
        self.font_main = pygame.font.Font(None, 32)
        self.font_log = pygame.font.Font(None, 22)
        
        # Couleurs
        self.BLUE = self.engine.blue.team_color
        self.RED = self.engine.red.team_color
        self.GOLD = (212, 175, 55)

        self.speed = 1  # Multiplicateur de vitesse
        self.is_paused = False
        self.score_history = []
        self._last_recorded_minute = -1
        
        # Définition des boutons de vitesse (x1, x2, x4, ||)
        self.speed_buttons = {
            "PAUSE": pygame.Rect(950, 540, 60, 30),
            "x1": pygame.Rect(1020, 540, 40, 30),
            "x2": pygame.Rect(1070, 540, 40, 30),
            "x4": pygame.Rect(1120, 540, 40, 30)
        }

        # Sliders tactiques globaux pour l'équipe Bleue
        self.slider_aggro = Slider(350, 550, 200, 10, "Agressivité")
        self.slider_focus = Slider(650, 550, 200, 10, "Focus")

        self.minimap = EnhancedMinimap(320, 80, 650, 300)
        self._last_minimap_log_idx = 0
        
        # Gestionnaire de notifications de kill
        self.kill_notifications = []

    def add_kill_notification(self, killer_name, victim_name, team_color):
        """Ajoute une notification de kill avec animation"""
        text = f"{killer_name} a éliminé {victim_name} !"
        notification = KillNotification(text, team_color)
        self.kill_notifications.append(notification)

    def update_notifications(self):
        """Met à jour et nettoie les notifications expirées"""
        self.kill_notifications = [n for n in self.kill_notifications if not n.is_expired()]

    def _sync_minimap_events(self):
        """Transforme les nouveaux événements du log en pings visuels sur la minimap."""
        logs = getattr(self.engine, "logs", [])
        if not logs:
            return

        start_idx = max(0, min(self._last_minimap_log_idx, len(logs)))
        new_events = logs[start_idx:]
        self._last_minimap_log_idx = len(logs)

        for ev in new_events:
            ev_type = ev.get("type")
            team_color = self.BLUE if ev.get("team") == "A" else self.RED

            location_role = str(ev.get("location_role", "MID")).upper()
            if location_role == "JUNGLE":
                base_x, base_y = random.choice([self.minimap.lanes["JUNGLE_TOP"], self.minimap.lanes["JUNGLE_BOT"]])
            elif location_role == "TOP":
                base_x, base_y = self.minimap.lanes["TOP"]
            elif location_role in {"BOT", "ADC", "SUPPORT"}:
                base_x, base_y = self.minimap.lanes["BOT"]
            else:
                base_x, base_y = self.minimap.lanes["MID"]

            x = base_x + random.randint(-15, 15)
            y = base_y + random.randint(-15, 15)

            if ev_type == "KILL":
                # On récupère le texte du log et la couleur de l'équipe
                msg = ev.get("msg", "ÉLIMINATION !")
                # Tentative de nettoyage du message, ex: "[12] NOVA a elimine..." -> "NOVA a elimine..."
                if ']' in msg:
                    msg = msg.split(']', 1)[-1].strip()
                
                # Extraire les noms pour la notification
                if "a elimine" in msg:
                    parts = msg.split(" a elimine ")
                    killer_name = parts[0].strip()
                    victim_name = parts[1].replace(" !", "").strip()
                    self.add_kill_notification(killer_name, victim_name, team_color)
                else: # Fallback si le message n'a pas le format attendu
                    notification = KillNotification(msg.upper(), team_color)
                    self.kill_notifications.append(notification)

                self.minimap.register_event(x, y, "KILL")
            elif ev_type == "OBJECTIVE":
                self.minimap.register_event(x, y, "OBJECTIVE")

    def update(self):
        """Fait progresser le match selon la vitesse choisie."""
        # Mise à jour continue de la minimap (interpolation fluide)
        self.minimap.interpolate_positions()
        self.update_notifications()

        if self.is_paused:
            return

        # On simule 'speed' fois par frame (ou par tick de jeu appelé depuis le main)
        for _ in range(self.speed):
            if self.engine.is_finished:
                break
                
            self.engine.simulate_step()
            
            # Synchroniser les événements récents (logs -> minimap)
            self._sync_minimap_events()
            
            # Enregistrer l'historique du score pour le graphe
            self._record_history_if_needed()
            
        # Mise à jour des positions cibles des joueurs sur la minimap
        if not self.engine.is_finished:
            phase = self._get_current_phase()
            for p in self.engine.team_a.players:
                self.minimap.update_player_action(p, "A", phase, self.engine.current_minute)
            for p in self.engine.team_b.players:
                self.minimap.update_player_action(p, "B", phase, self.engine.current_minute)

    def _get_current_phase(self):
        if self.engine.current_minute <= 10:
            return "EARLY"
        if self.engine.current_minute <= 20:
            return "MID"
        return "LATE"

    def _record_history_if_needed(self):
        minute = self.engine.current_minute
        if minute == self._last_recorded_minute:
            return
        score_diff = int(self.engine.scores["blue"] - self.engine.scores["red"])
        self.score_history.append((minute, score_diff))
        if len(self.score_history) > 600:
            self.score_history = self.score_history[-600:]
        self._last_recorded_minute = minute

    def handle_event(self, event):
        """Gère tous les événements du Dashboard Match."""
        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
            # Sliders tactiques prioritaires pour le dragging
            if self.slider_aggro.handle_event(event):
                self.engine.blue_tactics["aggro"] = self.slider_aggro.val
            if self.slider_focus.handle_event(event):
                self.engine.blue_tactics["focus"] = self.slider_focus.val
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_click(event.pos)

    def handle_click(self, mouse_pos):
        """Détecte les clics simples sur les boutons."""
        # Boutons de vitesse
        for speed_key, rect in self.speed_buttons.items():
            if rect.collidepoint(mouse_pos):
                if speed_key == "PAUSE":
                    self.is_paused = not self.is_paused
                else:
                    self.is_paused = False
                    self.speed = int(speed_key[1:])
                return


        # Contrôles des joueurs
        for i, p in enumerate(self.engine.team_a.players):
            self.handle_player_controls_click(p, 10, 80 + (i * 125), mouse_pos)
            
        for i, p in enumerate(self.engine.team_b.players):
            self.handle_player_controls_click(p, 1000, 80 + (i * 125), mouse_pos)

    def handle_player_controls_click(self, player, x, y, mouse_pos):
        """Gère les clics sur les sliders et boutons radio d'un joueur."""
        # Sliders (Focus et Risk)
        # Rect pour Focus: y + 35 + ~10px de zone de clic
        focus_rect = pygame.Rect(x + 75, y + 35, 120, 25)
        if focus_rect.collidepoint(mouse_pos):
            relative_x = mouse_pos[0] - focus_rect.x
            player.focus = max(0, min(100, int((relative_x / focus_rect.width) * 100)))

        # Rect pour Risk: y + 60
        risk_rect = pygame.Rect(x + 75, y + 60, 120, 25)
        if risk_rect.collidepoint(mouse_pos):
            relative_x = mouse_pos[0] - risk_rect.x
            player.risk = max(0, min(100, int((relative_x / risk_rect.width) * 100)))

        # Priority Radio Buttons: y + 85
        options = ["Lane", "Roam", "Obj"]
        for j, opt in enumerate(options):
            # Centré sur x + 75 + (j*60)
            radio_rect = pygame.Rect(x + 75 + (j * 60) - 10, y + 85, 50, 25)
            if radio_rect.collidepoint(mouse_pos):
                player.priority = opt

    def draw(self):
        self.draw_top_bar()
        
        # Dessiner les bannières de kill (avant les autres éléments)
        for notification in self.kill_notifications:
            notification.draw(self.screen, self.font_main)
        
        # Calcul du momentum ratio basé sur l'écart d'or
        gold_diff = self.engine.gold_a - self.engine.gold_b
        # On sature à +/- 5000 gold pour le visuel
        momentum_ratio = max(-1.0, min(1.0, gold_diff / 5000.0))
        
        self.minimap.draw(
            self.screen,
            self.engine.team_a.players,
            self.engine.team_b.players,
            self.BLUE,
            self.RED,
            momentum_ratio  # Ajout du momentum ratio
        )
        self.draw_sidebars()
        self.draw_timeline()
        self.draw_momentum_graph()
        self.draw_event_log()
        self.draw_controls()
        self.draw_tactics()
        
        if self.engine.is_finished:
            self.draw_end_screen()

    def draw_tactics(self):
        """Dessine les sliders tactiques globaux dans un panneau dédié."""
        # Panneau de fond
        panel_rect = pygame.Rect(320, 500, 650, 150)
        pygame.draw.rect(self.screen, (20, 20, 30), panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, (50, 50, 65), panel_rect, width=2, border_radius=10)
        
        # Titre du panneau
        title_surf = self.font_main.render("Logique Tactique Globale", True, (255, 255, 255))
        self.screen.blit(title_surf, (panel_rect.centerx - title_surf.get_width()//2, panel_rect.y + 10))

        # Dessin des sliders
        self.slider_aggro.draw(self.screen, self.font_log)
        self.slider_focus.draw(self.screen, self.font_log)

    def draw_controls(self):
        """Dessine les boutons de contrôle en bas à droite."""
        for speed_key, rect in self.speed_buttons.items():
            is_active = (f"x{self.speed}" == speed_key) or (speed_key == "PAUSE" and self.is_paused)
            color = self.GOLD if is_active else (60, 60, 70)
            
            pygame.draw.rect(self.screen, color, rect, border_radius=3)
            btn_txt = self.font_log.render(speed_key, True, (255, 255, 255))
            self.screen.blit(btn_txt, (rect.x + (rect.width - btn_txt.get_width())//2, rect.y + 7))


    def draw_top_bar(self):
        # Fond
        pygame.draw.rect(self.screen, (10, 10, 15), (0, 0, 1280, 70))
        
        # Chrono et Score (Données Live)
        score_txt = f"{self.engine.kills_a}   -   {self.engine.kills_b}"
        timer_txt = f"{self.engine.current_minute}:00"
        
        surf_score = self.font_main.render(score_txt, True, (255, 255, 255))
        surf_timer = self.font_log.render(timer_txt, True, self.GOLD)
        
        self.screen.blit(surf_score, (640 - surf_score.get_width()//2, 15))
        self.screen.blit(surf_timer, (640 - surf_timer.get_width()//2, 45))

        # Logos des équipes
        draw_team_logo(self.screen, 500, 35, 15, self.engine.blue.logo_shape, self.BLUE)
        draw_team_logo(self.screen, 780, 35, 15, self.engine.red.logo_shape, self.RED)
        
        # Noms des équipes
        name_a = self.font_log.render(self.engine.blue.name, True, WHITE)
        name_b = self.font_log.render(self.engine.red.name, True, WHITE)
        self.screen.blit(name_a, (480 - name_a.get_width(), 25))
        self.screen.blit(name_b, (800, 25))

    def draw_sidebars(self):
        # On affiche les 5 joueurs de chaque équipe
        for i, p in enumerate(self.engine.team_a.players):
            self.draw_player_slot(p, 10, 80 + (i * 125), self.BLUE)
            
        for i, p in enumerate(self.engine.team_b.players):
            self.draw_player_slot(p, 1000, 80 + (i * 125), self.RED)

    def draw_player_slot(self, player, x, y, color):
        # Carte joueur agrandie
        height = 120
        pygame.draw.rect(self.screen, (25, 25, 35), (x, y, 270, height), border_radius=5)
        pygame.draw.rect(self.screen, color, (x, y, 5, height)) # Barre d'équipe
        
        # Nom et Hero
        name_txt = f"{player.name} ({player.current_hero})"
        name_surf = self.font_log.render(name_txt, True, (255, 255, 255))
        self.screen.blit(name_surf, (x + 15, y + 10))
        
        # KDA
        kda_txt = f"{player.kills}/{player.deaths}/{player.assists}"
        kda_surf = self.font_log.render(kda_txt, True, (150, 150, 150))
        self.screen.blit(kda_surf, (x + 210, y + 10))
        
        # --- PANNEAU DE COMMANDE ---
        # Focus: [Farm]──●──[Fight]
        self.draw_slider(x + 15, y + 35, "Focus", player.focus, "Farm", "Fight")
        
        # Risk: [Safe]──●──[Aggro]
        self.draw_slider(x + 15, y + 60, "Risk", player.risk, "Safe", "Aggro")
        
        # Priority: ○ Lane ● Roam ○ Obj
        self.draw_priority(x + 15, y + 85, player.priority)

    def draw_slider(self, x, y, label, value, label_low, label_high):
        # Label
        lbl_surf = self.font_log.render(f"{label}:", True, (180, 180, 180))
        self.screen.blit(lbl_surf, (x, y + 5))
        
        # Labels small
        low_surf = self.font_log.render(label_low, True, (100, 100, 100))
        high_surf = self.font_log.render(label_high, True, (100, 100, 100))
        self.screen.blit(low_surf, (x + 60 - low_surf.get_width() - 5, y + 5))
        self.screen.blit(high_surf, (x + 60 + 120 + 5, y + 5))

        # Track
        track_x = x + 60
        track_w = 120
        pygame.draw.line(self.screen, (60, 60, 70), (track_x, y + 12), (track_x + track_w, y + 12), 2)
        
        # Knob
        knob_x = track_x + int((value / 100) * track_w)
        pygame.draw.circle(self.screen, self.GOLD, (knob_x, y + 12), 5)

    def draw_priority(self, x, y, current_priority):
        lbl_surf = self.font_log.render("Prio:", True, (180, 180, 180))
        self.screen.blit(lbl_surf, (x, y + 5))
        
        options = ["Lane", "Roam", "Obj"]
        for i, opt in enumerate(options):
            opt_x = x + 75 + (i * 60)
            is_sel = (current_priority == opt)
            color = self.GOLD if is_sel else (80, 80, 90)
            
            # Radio circle
            pygame.draw.circle(self.screen, color, (opt_x, y + 12), 6, 0 if is_sel else 2)
            
            # Text
            txt_color = (255, 255, 255) if is_sel else (120, 120, 130)
            txt_surf = self.font_log.render(opt, True, txt_color)
            self.screen.blit(txt_surf, (opt_x + 10, y + 5))

    def draw_event_log(self):
        """Affiche le log avec un code couleur et des icônes textuelles."""
        left_rect = pygame.Rect(10, 580, 280, 135)
        right_rect = pygame.Rect(990, 580, 280, 135)

        def draw_panel(rect, team_letter, title, accent_color):
            pygame.draw.rect(self.screen, (15, 15, 20), rect, border_radius=5)
            pygame.draw.rect(self.screen, (40, 40, 50), rect, width=1, border_radius=5)
            pygame.draw.rect(self.screen, accent_color, (rect.x, rect.y, 4, rect.h), border_radius=5)

            title_surf = self.font_log.render(title, True, (220, 220, 230))
            self.screen.blit(title_surf, (rect.x + 10, rect.y + 6))

            team_events = [e for e in self.engine.logs if e.get("team") == team_letter]
            team_events = team_events[-4:]
            for i, event in enumerate(team_events):
                y_pos = rect.y + 32 + (i * 22)

                color = accent_color
                if event.get("type") == "TACTIC":
                    color = self.GOLD

                icon = "[KILL]" if event.get("type") == "KILL" else "[OBJ]"
                if event.get("type") == "TACTIC":
                    icon = "[TAC]"

                msg_surf = self.font_log.render(f"{icon} {event['msg']}", True, color)
                self.screen.blit(msg_surf, (rect.x + 10, y_pos))

        draw_panel(left_rect, "A", "Log Team A", self.BLUE)
        draw_panel(right_rect, "B", "Log Team B", self.RED)

    def draw_momentum_graph(self):
        rect = pygame.Rect(320, 430, 650, 60)
        pygame.draw.rect(self.screen, (15, 15, 20), rect, border_radius=6)
        pygame.draw.rect(self.screen, (40, 40, 50), rect, width=1, border_radius=6)

        mid_y = rect.y + rect.h // 2
        pygame.draw.line(self.screen, (55, 55, 65), (rect.x + 8, mid_y), (rect.right - 8, mid_y), 1)

        if len(self.score_history) < 2:
            return

        max_minute = max(1, self.engine.max_minutes)
        max_abs = 25
        points = []
        for minute, diff in self.score_history:
            x = rect.x + 8 + int((minute / max_minute) * (rect.w - 16))
            clamped = max(-max_abs, min(max_abs, diff))
            y = mid_y - int((clamped / max_abs) * (rect.h * 0.42))
            points.append((x, y))

        pygame.draw.lines(self.screen, self.GOLD, False, points, 2)

    def draw_timeline(self):
        rect = pygame.Rect(320, 395, 650, 30)
        pygame.draw.rect(self.screen, (12, 12, 16), rect, border_radius=6)
        pygame.draw.rect(self.screen, (40, 40, 50), rect, width=1, border_radius=6)

        max_minute = max(1, self.engine.max_minutes)

        for m in range(0, max_minute + 1, 5):
            x = rect.x + 8 + int((m / max_minute) * (rect.w - 16))
            pygame.draw.line(self.screen, (40, 40, 50), (x, rect.y + 18), (x, rect.y + 26), 1)

        events = self.engine.logs[-80:]
        for ev in events:
            minute = ev.get("minute")
            if minute is None:
                continue
            x = rect.x + 8 + int((minute / max_minute) * (rect.w - 16))

            ev_type = ev.get("type")
            team = ev.get("team")
            color = self.BLUE if team == "A" else self.RED
            if ev_type == "TACTIC":
                color = self.GOLD

            cy = rect.y + rect.h // 2
            if ev_type == "KILL":
                pygame.draw.circle(self.screen, color, (x, cy), 4)
            elif ev_type == "OBJECTIVE":
                pygame.draw.rect(self.screen, color, pygame.Rect(x - 4, cy - 4, 8, 8), border_radius=2)
            else:
                pygame.draw.polygon(self.screen, color, [(x, cy - 5), (x - 5, cy + 4), (x + 5, cy + 4)])

    def draw_end_screen(self):
        """Affiche l'overlay de fin de match."""
        # 1. Overlay semi-transparent
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # 2. Panneau Central
        panel_rect = pygame.Rect(340, 110, 600, 500)
        pygame.draw.rect(self.screen, (30, 30, 40), panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, self.GOLD, panel_rect, 3, border_radius=15)

        # 3. Titre et MVP
        blue_win = self.engine.scores["blue"] >= self.engine.scores["red"]
        winner_team = "EQUIPE BLEUE" if blue_win else "EQUIPE ROUGE"
        win_color = self.BLUE if blue_win else self.RED
        
        title_surf = self.font_main.render(f"VICTOIRE : {winner_team}", True, win_color)
        self.screen.blit(title_surf, (640 - title_surf.get_width()//2, 150))

        mvp = self.engine.get_mvp()
        mvp_surf = self.font_log.render(f"MVP DU MATCH : {mvp.name} ({mvp.current_hero})", True, self.GOLD)
        self.screen.blit(mvp_surf, (640 - mvp_surf.get_width()//2, 220))

        # 4. Liste des XP (Simplifiée pour l'équipe du joueur)
        xp_title = self.font_log.render("PROGRESSION DES JOUEURS :", True, (255, 255, 255))
        self.screen.blit(xp_title, (380, 260))
        
        for i, p in enumerate(self.engine.team_a.players):
            xp_txt = f"{p.name} : Niveau {p.level} (XP: {p.xp}/1000)"
            p_surf = self.font_log.render(xp_txt, True, (200, 200, 200))
            self.screen.blit(p_surf, (380, 300 + (i * 30)))

        # 5. Statistiques Globales
        stats_y = 480
        blue_killy = self.font_log.render(f"Kills Bleus: {self.engine.kills_a}", True, self.BLUE)
        red_killy = self.font_log.render(f"Kills Rouges: {self.engine.kills_b}", True, self.RED)
        gold_txt = self.font_log.render(f"Or total: {self.engine.gold_a} vs {self.engine.gold_b}", True, (150, 150, 150))
        
        self.screen.blit(blue_killy, (380, stats_y))
        self.screen.blit(red_killy, (550, stats_y))
        self.screen.blit(gold_txt, (380, stats_y + 30))

        # 6. Bouton Retour
        btn_txt = self.font_log.render("APPUYEZ SUR [ESPACE] POUR CONTINUER", True, (255, 255, 255))
        self.screen.blit(btn_txt, (640 - btn_txt.get_width()//2, 560))
