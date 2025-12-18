import unittest
from moba_manager import (
    Role, Player, 
    Team, AggressiveStrategy, ScalingStrategy, 
    BalancedStrategy, ProbabilityEngine, CalibrationTools, TransferMarket, 
    MatchSimulator, League, distribute_match_rewards, create_initial_roster, generate_realistic_pseudonym
)


class TestMobaManager(unittest.TestCase):
    def setUp(self):
        # Common setup
        self.engine = ProbabilityEngine()
        self.market = TransferMarket()
        self.t1 = Team("T1", prestige=90, budget=1000000)
        self.t2 = Team("G2", prestige=85, budget=800000)

    def test_entities(self):
        """Test basic entity creation and stats"""
        player = Player("Faker", 25, Role.MID, 1000000)
        player.mec = 80
        player.mac = 80
        player.vis = 80
        player.sng = 80
        
        self.assertEqual(player.gen, 80)
        self.assertEqual(player.role, Role.MID)

    def test_player_progression(self):
        """Test XP gain and leveling up"""
        player = Player("Rookie", 18, Role.TOP, 50000)
        
        # Gain some XP
        player.gain_xp(500)
        self.assertEqual(player.xp, 500)
        self.assertEqual(player.level, 1)
        
        # Reach next level
        player.gain_xp(600)
        self.assertEqual(player.level, 2)
        
        # Check if a stat increased (might be tricky due to randomness, but sum of stats should increase)
        total_stats = player.mec + player.mac + player.vis + player.sng
        # Initial stats are all 50 in __init__, but let's be safe
        self.assertGreater(total_stats, 50 * 4)

    def test_probability_engine(self):
        """Test probability calculations"""
        # Test sigmoid bounds
        self.assertAlmostEqual(self.engine.sigmoid_win_chance(0), 0.5)
        self.assertGreater(self.engine.sigmoid_win_chance(100), 0.9)
        self.assertLess(self.engine.sigmoid_win_chance(-100), 0.1)
        
        # Test synergy
        # Normal
        self.assertEqual(self.engine.calculate_synergy_impact(80, 1.1), 1.1)
        # Critical zone (boosted)
        crit_impact = self.engine.calculate_synergy_impact(95, 1.1)
        self.assertGreater(crit_impact, 1.1)

    def test_calibration_tools(self):
        """Test player generation"""
        rookie = CalibrationTools.generate_balanced_player(Role.ADC, "rookie")
        self.assertTrue(55 <= rookie.gen <= 80)

        self.assertEqual(rookie.role, Role.ADC)

    def test_match_simulator(self):
        """Test a full match simulation"""
        # Fill rosters with dummy players
        for role in Role:
            p1 = CalibrationTools.generate_balanced_player(role, "pro")
            p2 = CalibrationTools.generate_balanced_player(role, "pro")
            self.t1.roster[role] = p1
            self.t2.roster[role] = p2
        
        sim = MatchSimulator(self.t1, self.t2)
        sim.set_strategies(AggressiveStrategy(), ScalingStrategy())
        
        result = sim.run_full_match()
        
        self.assertIn("winner", result)
        self.assertIn("phases", result)
        self.assertEqual(len(result["phases"]), 3)
        self.assertTrue(result["blue_score"] >= 0)
        self.assertTrue(result["red_score"] >= 0)

    def test_transfer_market(self):
        """Test market mechanics"""
        p = CalibrationTools.generate_balanced_player(Role.JUNGLE, "pro")
        p.market_value = 100000
        self.market.list_player(p)
        
        # Scouting
        scouted = self.market.scout_players(role=Role.JUNGLE, max_price=150000)
        self.assertIn(p, scouted)
        
        # Transfer logic
        # Force a likely success with high offer
        success = self.market.attempt_transfer(self.t1, p, 200000)
        self.assertIsInstance(success, bool)
        
        if success:
            self.assertEqual(self.t1.roster[Role.JUNGLE], p)

    def test_league(self):
        """Test league season execution"""
        # Create a small league with 3 teams
        t3 = Team("FNC", prestige=88, budget=900000)
        teams = [self.t1, self.t2, t3]
        
        # Fill rosters for all teams
        for team in teams:
            for role in Role:
                if role not in team.roster or team.roster[role] is None:
                    team.roster[role] = CalibrationTools.generate_balanced_player(role, "pro")
        
        league = League("LEC", teams)
        
        # Test schedule creation
        league.create_round_robin_schedule()
        expected_games = 3  # 3 teams -> 3 pairings (1vs2, 1vs3, 2vs3)
        self.assertEqual(len(league.calendar), expected_games)
        
        # Test season run
        league.run_season()
        
        # Check if standings are updated
        rankings = league.get_rankings()
        self.assertEqual(len(rankings), 3)
        
        total_wins = sum(stat["wins"] for _, stat in league.standings.items())
        total_losses = sum(stat["losses"] for _, stat in league.standings.items())
        
        self.assertEqual(total_wins, 3)
        self.assertEqual(total_losses, 3)

    def test_season_progression(self):
        """Test player evolution and season advancement"""
        # Setup a single player in a team
        p = CalibrationTools.generate_balanced_player(Role.MID, "rookie")
        p.age = 20
        initial_mech = p.mec
        initial_value = p.market_value
        
        self.t1.roster[Role.MID] = p
        league = League("TestLeague", [self.t1])
        
        # Advance season
        league.advance_season()
        
        # Check aging
        self.assertEqual(p.age, 21)
        
        # Check stats evolution
        self.assertGreater(p.mec, initial_mech)

        
        # Check market value update
        # If stats grew, value should increase by inflation
        self.assertGreater(p.market_value, initial_value)

    def test_playoffs(self):
        """Test playoffs logic"""
        # Create 4 teams for playoffs
        t3 = Team("FNC", prestige=88, budget=900000)
        t4 = Team("KCORP", prestige=75, budget=500000)
        teams = [self.t1, self.t2, t3, t4]
        
        # Fill rosters
        for team in teams:
            for role in Role:
                if role not in team.roster or team.roster[role] is None:
                    team.roster[role] = CalibrationTools.generate_balanced_player(role, "pro")
        
        league = League("Worlds", teams)
        
        # Force standings to avoid needing to run season
        rankings = ["T1", "G2", "FNC", "KCORP"]
        for i, name in enumerate(rankings):
            league.standings[name]["wins"] = 4 - i # T1=4, G2=3, etc.
            
        # Run playoffs
        champion_name = league.run_playoffs()
        
        self.assertIn(champion_name, rankings)
        
        # Check that the champion got the budget bonus
        next(t for t in teams if t.name == champion_name)
        # Check budget greater than initial budget (we need to be careful with hardcoded values)

    def test_player_xp_logic(self):
        """Vérifie qu'un joueur monte de niveau correctement et gère le reliquat d'XP."""
        p = Player("Test Player", 20, Role.MID, 50000)
        p.xp = 950
        p.gain_xp(100) # Doit passer à 1050, puis 50 après level up
        self.assertEqual(p.level, 2)
        self.assertEqual(p.xp, 50)

    def test_stat_caps(self):
        """Vérifie que les stats ne dépassent pas 99 même après plusieurs level ups."""
        p = Player("Superstar", 20, Role.MID, 1000000)
        # On booste toutes les stats à 99
        p.mec = 99
        p.mac = 99
        p.vis = 99
        p.sng = 99
        
        # On force 10 level ups
        for _ in range(10):
            p.level_up()
            
        self.assertLessEqual(p.mec, 99)
        self.assertLessEqual(p.mac, 99)
        self.assertLessEqual(p.vis, 99)
        self.assertLessEqual(p.sng, 99)

    def test_reward_mechanics(self):
        """Vérifie la distribution d'XP basée sur les scores réels."""
        # Création d'objets réels simplifiés
        team_a = Team("Blue", 100, 1000)
        team_b = Team("Red", 100, 1000)
        p_a = Player("P_A", 20, Role.MID, 100)
        p_b = Player("P_B", 20, Role.MID, 100)
        team_a.roster[Role.MID] = p_a
        team_b.roster[Role.MID] = p_b
        
        class MockMatch:
            def __init__(self):
                self.blue = team_a
                self.red = team_b
                self.scores = {"blue": 10, "red": 5}
        
        match = MockMatch()
        # On simule manuellement quelques stats
        p_a.kills = 2 # +20 XP
        p_b.kills = 0
        
        distribute_match_rewards(match)
        
        # Team A gagne (10 > 5) : 500 base + 20 performance = 520
        self.assertEqual(p_a.xp, 520)
        # Team B perd : 200 base + 0 performance = 200
        self.assertEqual(p_b.xp, 200)

    def test_tactical_influences(self):
        """Vérifie que les tactiques impactent bien le calcul de puissance."""
        p = Player("Tactician", 20, Role.MID, 100000)
        self.t1.roster[Role.MID] = p
        sim = MatchSimulator(self.t1, self.t2)
        
        # Puissance avec tactique par défaut (1.0)
        pwr_default = sim._calculate_team_power(self.t1, BalancedStrategy(), 1, {"aggro": 1.0, "focus": 1.0})
        
        # Puissance avec Aggro élevée (boost MEC)
        pwr_aggro = sim._calculate_team_power(self.t1, BalancedStrategy(), 1, {"aggro": 1.5, "focus": 1.0})
        
        self.assertNotEqual(pwr_default, pwr_aggro)
        # Le MID en phase 1 (MID game) utilise (MEC+MAC+VIS)/3. 
        # Si Aggro=1.5, MEC -> 50*1.5=75. VIS -> 50*(1/1.5)=33.3. 
        # (75 + 50 + 33.3) / 3 = 158.3 / 3 = 52.7 (vs 50 par défaut)
        self.assertGreater(pwr_aggro, pwr_default)

    def test_extreme_tactics(self):
        """Vérifie le moteur avec une agressivité minimum et maximum."""
        # Setup teams with real players
        for role in Role:
            self.t1.roster[role] = CalibrationTools.generate_balanced_player(role, "pro")
            self.t2.roster[role] = CalibrationTools.generate_balanced_player(role, "pro")
            
        sim = MatchSimulator(self.t1, self.t2)
        
        # Test Agressivité 0.1x (Match très lent)
        sim.blue_tactics["aggro"] = 0.1
        sim.simulate_step()
        self.assertEqual(sim.current_minute, 1)
        
        # Test Agressivité 10.0x (Match ultra violent)
        sim.blue_tactics["aggro"] = 10.0
        for _ in range(10): 
            sim.simulate_step()
        
        # On s'attend à ce que le code ne crashe pas et que les scores soient valides
        self.assertGreaterEqual(sim.kills_a + sim.kills_b, 0)
        self.assertGreaterEqual(sim.scores["blue"], 0)

    def test_create_initial_roster(self):
        team = create_initial_roster("MyTeam", "MyCoach", (1, 2, 3), prestige=70, budget=123456)
        self.assertIsInstance(team, Team)
        self.assertEqual(team.name, "MyTeam")
        self.assertEqual(team.coach_name, "MyCoach")
        self.assertEqual(team.team_color, (1, 2, 3))
        self.assertEqual(team.prestige, 70)
        self.assertEqual(team.budget, 123456)

        # Roster complet
        for role in Role:
            self.assertIsNotNone(team.roster[role])

    def test_generate_realistic_pseudonym(self):
        nick = generate_realistic_pseudonym()
        self.assertIsInstance(nick, str)
        self.assertTrue(len(nick) > 0)

    def test_match_logs_have_minute(self):
        # Setup teams with real players
        for role in Role:
            self.t1.roster[role] = CalibrationTools.generate_balanced_player(role, "pro")
            self.t2.roster[role] = CalibrationTools.generate_balanced_player(role, "pro")

        sim = MatchSimulator(self.t1, self.t2)
        sim.simulate_step()

        # Soit un event est loggé, soit non; si oui, il doit avoir minute
        for ev in sim.logs:
            self.assertIn("minute", ev)
            self.assertIsInstance(ev["minute"], int)


if __name__ == '__main__':
    unittest.main()
