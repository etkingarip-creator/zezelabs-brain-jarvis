import math
import random
from typing import Dict, Any, List, Tuple
from departments.zeze_betting.strategy_engine import ZezeBettingStrategyEngine

class ZezeBettingBacktestEngine:
    def __init__(self, strategy_engine: ZezeBettingStrategyEngine = None):
        self.strategy = strategy_engine or ZezeBettingStrategyEngine(bankroll=17.0)

    def generate_mock_historical_data(self, size: int = 1000) -> List[Dict[str, Any]]:
        """
        Generates a synthetic historical dataset of soccer matches with realistic
        underlying goal rates, fatigue parameters, news sentiment, and simulated final scores.
        """
        random.seed(42)  # For deterministic reproducibility
        fixtures = []
        
        teams = [
            ("Bayern", 2.2, 0.8), ("Real Madrid", 2.1, 0.9), ("Man City", 2.3, 0.7),
            ("Arsenal", 2.0, 0.8), ("Chelsea", 1.6, 1.2), ("Liverpool", 2.0, 0.9),
            ("Dortmund", 1.8, 1.1), ("PSG", 2.1, 1.0), ("Juventus", 1.4, 0.9),
            ("Inter", 1.7, 0.8), ("Milan", 1.6, 1.0), ("Napoli", 1.7, 1.1),
            ("Barcelona", 1.9, 1.1), ("Atletico", 1.3, 0.8), ("Sevilla", 1.4, 1.3),
            ("Galatasaray", 1.9, 1.0), ("Fenerbahce", 1.8, 0.9), ("Besiktas", 1.6, 1.1),
            ("Trabzonspor", 1.5, 1.2), ("Basaksehir", 1.3, 1.2)
        ]
        
        for i in range(size):
            home_idx = random.randint(0, len(teams) - 1)
            away_idx = random.randint(0, len(teams) - 1)
            while home_idx == away_idx:
                away_idx = random.randint(0, len(teams) - 1)
                
            home_name, home_att, home_def = teams[home_idx]
            away_name, away_att, away_def = teams[away_idx]
            
            # Fatigue rest hours (48 to 144 hours)
            home_rest = float(random.choice([48, 72, 96, 120, 144]))
            away_rest = float(random.choice([48, 72, 96, 120, 144]))
            
            # Travel km penalty for away team
            away_travel = float(random.randint(0, 15) * 100.0)
            
            # LLM Sentiment (-1.0 to 1.0)
            sentiment_val = float(random.uniform(-1.0, 1.0))
            
            # Form strings
            forms = ["WWWWW", "WWDLW", "WDLWD", "LDWLD", "LLWDL", "LLLLL"]
            home_form = random.choice(forms)
            away_form = random.choice(forms)
            
            # Ground-truth lambda parameters
            home_fatigue = max(0.70, min(1.0, home_rest / 72.0))
            away_fatigue = max(0.70, min(1.0, away_rest / 72.0))
            travel_penalty = 1.0 + min(0.15, away_travel / 2000.0)
            
            l1_gt = home_att * away_def * 1.10 * home_fatigue
            l2_gt = away_att * home_def * away_fatigue * travel_penalty
            l3_gt = max(0.01, 0.08 * math.sqrt(l1_gt * l2_gt))
            
            # Simulate actual goals using Bivariate Poisson (U1+U3, U2+U3)
            def poisson_sample(lam: float) -> int:
                if lam <= 0: return 0
                L = math.exp(-lam)
                k = 0
                p = 1.0
                while p > L:
                    k += 1
                    p *= random.random()
                return k - 1

            u1 = poisson_sample(l1_gt)
            u2 = poisson_sample(l2_gt)
            u3 = poisson_sample(l3_gt)
            
            goals_home = u1 + u3
            goals_away = u2 + u3
            
            # Determine actual outcome ('1', 'X', '2')
            if goals_home > goals_away:
                outcome = "1"
            elif goals_home == goals_away:
                outcome = "X"
            else:
                outcome = "2"
                
            # Simulate bookmaker odds with minor noise around fair probabilities
            sum_odds = 1.0 / l1_gt + 1.0 / l2_gt
            home_odds = round(1.10 * (1.0 / (l1_gt / (l1_gt + l2_gt))), 2)
            away_odds = round(1.10 * (1.0 / (l2_gt / (l1_gt + l2_gt))), 2)
            draw_odds = round(1.15 * (1.0 / (0.25)), 2)
            
            fixtures.append({
                "id": f"hist_{i}",
                "home": home_name,
                "away": away_name,
                "home_odds": max(1.05, home_odds),
                "draw_odds": max(1.05, draw_odds),
                "away_odds": max(1.05, away_odds),
                "stats": {
                    "home_xG": home_att,
                    "away_xG": away_att,
                    "home_xGA": home_def,
                    "away_xGA": away_def,
                    "home_rest_hours": home_rest,
                    "away_rest_hours": away_rest,
                    "away_travel_km": away_travel,
                    "home_form": home_form,
                    "away_form": away_form
                },
                "sentiment": {
                    "sentiment_score": sentiment_val,
                    "key_player_injured": False
                },
                "actual_goals_home": goals_home,
                "actual_goals_away": goals_away,
                "actual_outcome": outcome
            })
            
        return fixtures

    def run_backtest(self, dataset: List[Dict[str, Any]], base_cov_factor: float = 0.08) -> Dict[str, Any]:
        """
        Runs the Bivariate Poisson & Monte Carlo prediction engine on the dataset,
        computing Brier Score, Log-Loss, and prediction accuracy metrics.
        """
        # Override the strategy engine's base covariance factor for this backtest
        self.strategy.base_cov_factor = base_cov_factor
        
        log_loss_sum = 0.0
        brier_sum = 0.0
        correct_predictions = 0
        total_evaluations = 0
        
        for fixture in dataset:
            stats = fixture["stats"]
            sentiment = fixture["sentiment"]
            
            # Predict outcome probabilities using Monte Carlo (1000 runs for speed during backtest)
            xg_home = float(stats["home_xG"])
            xg_away = float(stats["away_xG"])
            xga_home = float(stats["home_xGA"])
            xga_away = float(stats["away_xGA"])
            
            home_rest = float(stats["home_rest_hours"])
            away_rest = float(stats["away_rest_hours"])
            away_travel = float(stats["away_travel_km"])
            
            home_fatigue = max(0.70, min(1.0, home_rest / 72.0))
            away_fatigue = max(0.70, min(1.0, away_rest / 72.0))
            travel_penalty = 1.0 + min(0.15, away_travel / 2000.0)
            
            l1 = xg_home * xga_away * 1.10 * home_fatigue
            l2 = xg_away * xga_home * away_fatigue * travel_penalty
            
            # Calculate covariance with the backtest's base_cov_factor
            home_form_val = self.strategy._get_form_score(stats["home_form"])
            away_form_val = self.strategy._get_form_score(stats["away_form"])
            sent_val = float(sentiment["sentiment_score"])
            
            form_correlation = 0.02 * (home_form_val + away_form_val)
            sent_correlation = 0.01 * sent_val
            cov_factor = max(0.02, min(0.20, base_cov_factor + form_correlation + sent_correlation))
            
            l3 = max(0.01, round(cov_factor * math.sqrt(max(0.01, l1 * l2)), 4))
            
            # Simulate outcomes
            sim = self.strategy.run_monte_carlo_simulation(l1, l2, l3, runs=1000)
            
            p_home = sim["home_prob"]
            p_draw = sim["draw_prob"]
            p_away = sim["away_prob"]
            
            # Map actual outcomes
            actual = fixture["actual_outcome"]
            y_home = 1.0 if actual == "1" else 0.0
            y_draw = 1.0 if actual == "X" else 0.0
            y_away = 1.0 if actual == "2" else 0.0
            
            # Compute Log-Loss (clamped to prevent log(0) errors)
            eps = 1e-15
            p_home_c = max(eps, min(1.0 - eps, p_home))
            p_draw_c = max(eps, min(1.0 - eps, p_draw))
            p_away_c = max(eps, min(1.0 - eps, p_away))
            
            log_loss = -(y_home * math.log(p_home_c) + y_draw * math.log(p_draw_c) + y_away * math.log(p_away_c))
            log_loss_sum += log_loss
            
            # Compute Brier Score
            brier = (p_home - y_home)**2 + (p_draw - y_draw)**2 + (p_away - y_away)**2
            brier_sum += brier
            
            # Check accuracy of the argmax prediction
            pred_outcome = "1"
            if p_draw > p_home and p_draw > p_away:
                pred_outcome = "X"
            elif p_away > p_home and p_away > p_draw:
                pred_outcome = "2"
                
            if pred_outcome == actual:
                correct_predictions += 1
                
            total_evaluations += 1
            
        mean_log_loss = log_loss_sum / total_evaluations if total_evaluations > 0 else 0.0
        mean_brier = brier_sum / total_evaluations if total_evaluations > 0 else 0.0
        accuracy = correct_predictions / total_evaluations if total_evaluations > 0 else 0.0
        
        return {
            "evaluations_count": total_evaluations,
            "accuracy_rate": round(accuracy, 4),
            "mean_log_loss": round(mean_log_loss, 4),
            "mean_brier_score": round(mean_brier, 4),
            "tested_cov_factor": base_cov_factor
        }

    def optimize_hyperparameters(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Runs grid search optimization to find the base covariance factor that minimizes Log-Loss.
        """
        candidates = [0.02, 0.05, 0.08, 0.12, 0.16, 0.20]
        best_cov = 0.08
        min_loss = float('inf')
        results = []
        
        for cov in candidates:
            res = self.run_backtest(dataset, base_cov_factor=cov)
            results.append(res)
            if res["mean_log_loss"] < min_loss:
                min_loss = res["mean_log_loss"]
                best_cov = cov
                
        return {
            "optimal_covariance_factor": best_cov,
            "minimized_log_loss": min_loss,
            "grid_search_history": results
        }
