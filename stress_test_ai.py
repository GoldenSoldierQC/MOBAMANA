import argparse
import random
import statistics

from moba_manager import MatchSimulator, create_initial_roster


def run_one(seed: int, prestige: int, budget: int):
    random.seed(seed)

    t1 = create_initial_roster("BLUE", "CoachB", (0, 0, 255), prestige=prestige, budget=budget)
    t2 = create_initial_roster("RED", "CoachR", (255, 0, 0), prestige=prestige, budget=budget)

    m = MatchSimulator(t1, t2)
    while not m.is_finished:
        m.simulate_step()

    rl_logs = [log for log in m.logs if log.get("type") == "TACTIC" and "(RL)" in log.get("msg", "")]
    aggro = sum("AGGRO" in log.get("msg", "") for log in rl_logs)
    deff = sum("DEF" in log.get("msg", "") for log in rl_logs)

    weights = m.ai_brain.get("weights", {})

    return {
        "winner": m.winner,
        "rl_aggro": aggro,
        "rl_def": deff,
        "w_aggro": float(weights.get("AGGRO", 1.0)),
        "w_def": float(weights.get("DEF", 1.0)),
        "w_bal": float(weights.get("BALANCED", 1.0)),
        "minutes": m.current_minute,
        "score_diff": m.scores["blue"] - m.scores["red"],
        "gold_diff": m.gold_a - m.gold_b,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--prestige", type=int, default=70)
    parser.add_argument("--budget", type=int, default=1_000_000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    results = [run_one(args.seed + i, args.prestige, args.budget) for i in range(args.n)]

    wins_a = sum(r["winner"] == "A" for r in results)
    wins_b = sum(r["winner"] == "B" for r in results)

    aggro_total = sum(r["rl_aggro"] for r in results)
    def_total = sum(r["rl_def"] for r in results)

    w_aggro = [r["w_aggro"] for r in results]
    w_def = [r["w_def"] for r in results]
    w_bal = [r["w_bal"] for r in results]

    print("matches", args.n)
    print("wins blue(A):", wins_a, "wins red/AI(B):", wins_b)
    print("RL decisions total -> AGGRO:", aggro_total, "DEF:", def_total)
    print(
        "avg weights:",
        {
            "AGGRO": round(statistics.mean(w_aggro), 3),
            "DEF": round(statistics.mean(w_def), 3),
            "BALANCED": round(statistics.mean(w_bal), 3),
        },
    )
    print(
        "min/max weights:",
        {
            "AGGRO": (round(min(w_aggro), 3), round(max(w_aggro), 3)),
            "DEF": (round(min(w_def), 3), round(max(w_def), 3)),
            "BALANCED": (round(min(w_bal), 3), round(max(w_bal), 3)),
        },
    )


if __name__ == "__main__":
    main()
