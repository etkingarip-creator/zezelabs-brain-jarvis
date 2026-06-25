import math
import random
import logging
from typing import Dict, Any, Tuple, List

class ZezeBettingStrategyEngine:
    def __init__(self, bankroll: float = 17.0, logger=None):
        self.bankroll = bankroll
        self.max_stake_limit = 0.85  # Capped at $0.85 (5% of $17 bankroll)
        self.kelly_fraction = 0.25  # 25% Fractional Kelly
        self.logger = logger or logging.getLogger("zeze_betting.strategy_engine")

    def calculate_implied_probability(self, home_odds: float, draw_odds: float, away_odds: float) -> Dict[str, float]:
        """Calculates normalized implied probabilities and the bookmaker margin."""
        p_home = 1.0 / home_odds if home_odds > 0 else 0.0
        p_draw = 1.0 / draw_odds if draw_odds > 0 else 0.0
        p_away = 1.0 / away_odds if away_odds > 0 else 0.0
        
        raw_sum = p_home + p_draw + p_away
        margin = raw_sum - 1.0 if raw_sum > 0 else 0.0
        
        if raw_sum > 0:
            return {
                "home": p_home / raw_sum,
                "draw": p_draw / raw_sum,
                "away": p_away / raw_sum,
                "margin": margin
            }
        else:
            return {
                "home": 0.0,
                "draw": 0.0,
                "away": 0.0,
                "margin": 0.0
            }

    def calculate_bivariate_poisson_pmf(self, x: int, y: int, l1: float, l2: float, l3: float) -> float:
        """
        Calculates the exact Bivariate Poisson probability mass function for scores (x, y)
        with parameters l1 (home goal rate), l2 (away goal rate), and l3 (covariance).
        """
        if l1 <= 0 or l2 <= 0 or x < 0 or y < 0:
            return 0.0
            
        term1 = math.exp(-(l1 + l2 + l3))
        sum_val = 0.0
        
        for k in range(min(x, y) + 1):
            numerator = (l1 ** (x - k)) * (l2 ** (y - k)) * (l3 ** k)
            denominator = math.factorial(k) * math.factorial(x - k) * math.factorial(y - k)
            sum_val += numerator / denominator
            
        return term1 * sum_val

    def run_monte_carlo_simulation(self, l1: float, l2: float, l3: float, runs: int = 10000) -> Dict[str, Any]:
        """
        Runs a Monte Carlo simulation using independent Poisson samples (Knuth's method)
        to construct Bivariate Poisson outcomes for the match.
        """
        def poisson_sample(lam: float) -> int:
            if lam <= 0:
                return 0
            # Knuth's algorithm for Poisson distribution sampling
            L = math.exp(-lam)
            k = 0
            p = 1.0
            while p > L:
                k += 1
                p *= random.random()
            return k - 1

        home_wins = 0
        draws = 0
        away_wins = 0
        over_2_5 = 0
        scores_freq = {}

        for _ in range(runs):
            # Draw independent Poisson variables
            u1 = poisson_sample(l1)
            u2 = poisson_sample(l2)
            u3 = poisson_sample(l3)
            
            # Construct bivariate outcomes
            goals_home = u1 + u3
            goals_away = u2 + u3
            
            # Match results
            if goals_home > goals_away:
                home_wins += 1
            elif goals_home == goals_away:
                draws += 1
            else:
                away_wins += 1
                
            # Over 2.5 goals check
            if (goals_home + goals_away) > 2.5:
                over_2_5 += 1
                
            # Keep track of correct scores frequency
            score = (goals_home, goals_away)
            scores_freq[score] = scores_freq.get(score, 0) + 1

        # Find most likely correct scoreline
        most_likely_score = (1, 1)
        max_freq = 0
        for score, freq in scores_freq.items():
            if freq > max_freq:
                max_freq = freq
                most_likely_score = score

        return {
            "home_prob": home_wins / runs,
            "draw_prob": draws / runs,
            "away_prob": away_wins / runs,
            "over_2_5_prob": over_2_5 / runs,
            "most_likely_score": f"{most_likely_score[0]}-{most_likely_score[1]}",
            "most_likely_score_prob": max_freq / runs
        }

    def _get_form_score(self, form_str: str) -> float:
        """Helper to convert form letters (WWDLW) into a numeric score."""
        if not form_str:
            return 0.0
        score = 0.0
        for char in form_str.upper():
            if char == 'W':
                score += 1.0
            elif char == 'D':
                score += 0.2
            elif char == 'L':
                score -= 0.5
        return score / len(form_str)

    def calculate_expected_value(self, p_win: float, odds: float) -> float:
        """Calculates expected value (EV) of a stake. EV = P_win * Odds - 1.0"""
        return p_win * odds - 1.0

    def calculate_kelly_stake(self, p_win: float, odds: float) -> float:
        """Calculates suggested stake amount based on fractional Kelly Criterion."""
        if odds <= 1.0:
            return 0.0
            
        b = odds - 1.0
        q = 1.0 - p_win
        
        f_star = (b * p_win - q) / b
        if f_star <= 0.0:
            return 0.0
            
        f_frac = self.kelly_fraction * f_star
        stake_amount = f_frac * self.bankroll
        
        return round(min(stake_amount, self.max_stake_limit), 2)

    def evaluate_match(self, match: Dict[str, Any], stats: Dict[str, Any], sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates a single match using Bivariate Poisson rates and Monte Carlo simulations."""
        home_odds = match.get("home_odds", 0.0)
        draw_odds = match.get("draw_odds", 0.0)
        away_odds = match.get("away_odds", 0.0)
        
        if home_odds <= 1.0 or away_odds <= 1.0:
            return {"recommended": False}

        # 1. Fetch Attacking/Defensive parameters (xG / xGA)
        xg_home = float(stats.get("home_xG", 1.5))
        xg_away = float(stats.get("away_xG", 1.3))
        xga_home = float(stats.get("home_xGA", 1.2))
        xga_away = float(stats.get("away_xGA", 1.3))
        
        # 2. Factor in fatigue offsets
        # Rest hours (recovery index)
        home_rest = float(stats.get("home_rest_hours", 72.0))
        away_rest = float(stats.get("away_rest_hours", 72.0))
        
        # Travel km penalty for the away team
        away_travel = float(stats.get("away_travel_km", 0.0))
        
        # Apply fatigue modifiers to attacking/defensive ratings
        home_fatigue_penalty = max(0.70, min(1.0, home_rest / 72.0))  # Decays goal-scoring under 72h
        away_fatigue_penalty = max(0.70, min(1.0, away_rest / 72.0))
        
        # Travel fatigue: away defensive rating decays slightly on long journeys
        travel_penalty = 1.0 + min(0.15, away_travel / 2000.0)  # Up to 15% increase in goals conceded
        
        # 3. Calculate Poisson λ goal rates (Home advantage multiplier of 1.1)
        l1 = xg_home * xga_away * 1.10 * home_fatigue_penalty
        l2 = xg_away * xga_home * away_fatigue_penalty * travel_penalty
        
        # Covariance (λ3) calculated dynamically using empirical multiplicative model
        home_form_val = self._get_form_score(stats.get("home_form", ""))
        away_form_val = self._get_form_score(stats.get("away_form", ""))
        sent_val = float(sentiment.get("sentiment_score", 0.0))
        
        base_cov_factor = 0.08  # Typical average covariance factor
        form_correlation = 0.02 * (home_form_val + away_form_val)
        sent_correlation = 0.01 * sent_val
        cov_factor = max(0.02, min(0.20, base_cov_factor + form_correlation + sent_correlation))
        
        # λ3 = cov_factor * sqrt(l1 * l2)
        l3 = max(0.01, round(cov_factor * math.sqrt(max(0.01, l1 * l2)), 4))

        # 4. Run Monte Carlo Simulation (10,000 matches)
        sim_res = self.run_monte_carlo_simulation(l1, l2, l3, runs=10000)
        
        # Normal implied probabilities from bookmaker odds
        norm_probs = {
            "home": 1.0 / home_odds,
            "draw": 1.0 / draw_odds if draw_odds else 0.0,
            "away": 1.0 / away_odds
        }
        raw_sum = sum(norm_probs.values())
        if raw_sum > 0:
            norm_probs = {k: v / raw_sum for k, v in norm_probs.items()}
        
        # True simulated probabilities
        p_home_true = sim_res["home_prob"]
        p_draw_true = sim_res["draw_prob"]
        p_away_true = sim_res["away_prob"]

        # Calculate EV using simulated true probabilities
        ev_home = self.calculate_expected_value(p_home_true, home_odds)
        ev_draw = self.calculate_expected_value(p_draw_true, draw_odds) if draw_odds else -1.0
        ev_away = self.calculate_expected_value(p_away_true, away_odds)
        
        # Choose the selection with the highest positive EV
        options = [
            ("home", ev_home, home_odds, p_home_true),
            ("draw", ev_draw, draw_odds, p_draw_true),
            ("away", ev_away, away_odds, p_away_true)
        ]
        
        best_option = None
        max_ev = 0.0
        
        for name, ev, odds, prob in options:
            if ev > max_ev:
                max_ev = ev
                best_option = (name, odds, prob)
                
        if best_option:
            name, odds, prob = best_option
            stake = self.calculate_kelly_stake(prob, odds)
            if stake > 0.0:
                return {
                    "recommended": True,
                    "match": match,
                    "selection": name,
                    "odds": odds,
                    "implied_probability": norm_probs[name],
                    "adjusted_probability": prob,
                    "expected_value": round(max_ev, 4),
                    "stake": stake,
                    "lambda_home": round(l1, 2),
                    "lambda_away": round(l2, 2),
                    "most_likely_score": sim_res["most_likely_score"],
                    "most_likely_score_prob": round(sim_res["most_likely_score_prob"], 4),
                    "over_2_5_prob": round(sim_res["over_2_5_prob"], 4)
                }
                
        return {"recommended": False}

    def apply_bayesian_lineup_update(
        self, 
        l1: float, 
        l2: float, 
        missing_players_home: List[str], 
        missing_players_away: List[str]
    ) -> Tuple[float, float]:
        """
        Adjusts expected goal rates (l1, l2) based on kickoff lineup news (Bayesian updates).
        """
        adjusted_l1 = l1
        adjusted_l2 = l2
        
        # If striker/forward is missing, attacking power decays by 15%
        for player in missing_players_home:
            p_lower = player.lower()
            if any(pos in p_lower for pos in ["striker", "forward", "attacker", "salah", "kane", "haaland", "mbappe"]):
                adjusted_l1 *= 0.85
                self.logger.info(f"Bayesian Update: Home key attacker '{player}' missing. Goal rate decays by 15%.")
            if any(pos in p_lower for pos in ["goalkeeper", "gk", "defender", "centre-back", "cb", "van dijk", "alisson"]):
                adjusted_l2 *= 1.10
                self.logger.info(f"Bayesian Update: Home key defender/gk '{player}' missing. Opponent goal rate increased by 10%.")
                
        for player in missing_players_away:
            p_lower = player.lower()
            if any(pos in p_lower for pos in ["striker", "forward", "attacker", "salah", "kane", "haaland", "mbappe"]):
                adjusted_l2 *= 0.85
                self.logger.info(f"Bayesian Update: Away key attacker '{player}' missing. Goal rate decays by 15%.")
            if any(pos in p_lower for pos in ["goalkeeper", "gk", "defender", "centre-back", "cb", "van dijk", "alisson"]):
                adjusted_l1 *= 1.10
                self.logger.info(f"Bayesian Update: Away key defender/gk '{player}' missing. Opponent goal rate increased by 10%.")
                
        return round(adjusted_l1, 4), round(adjusted_l2, 4)

class ZezeCouponCombinator:
    def __init__(self, logger=None):
        import logging
        self.logger = logger or logging.getLogger("zeze_betting.coupon_combinator")

    def combine_coupons(self, evaluated_matches: list) -> dict:
        """
        Combines a list of evaluated matches into slips that conform to MBS rules.
        """
        valid_matches = [m for m in evaluated_matches if m and m.get("recommended")]
        if not valid_matches:
            return {"safe_coupon": None, "value_coupon": None}

        # Sort matches:
        # For safe coupon, sort by highest adjusted probability
        safe_candidates = sorted(valid_matches, key=lambda x: x.get("adjusted_probability", 0.0), reverse=True)
        # For value coupon, sort by highest EV
        value_candidates = sorted(valid_matches, key=lambda x: x.get("expected_value", 0.0), reverse=True)

        # Build coupons
        safe_coupon = self._build_coupon_from_candidates(safe_candidates, max_size=3, target_type="safe")
        value_coupon = self._build_coupon_from_candidates(value_candidates, max_size=3, target_type="value")

        return {
            "safe_coupon": safe_coupon,
            "value_coupon": value_coupon
        }

    def _build_coupon_from_candidates(self, candidates: list, max_size: int, target_type: str) -> dict:
        """Compiles a single coupon from a set of candidates satisfying MBS requirements."""
        if not candidates:
            return None
            
        # First pass: find the maximum MBS among candidates that could be selected
        # If we include a match with MBS 4, we must scale our effective size to at least 4
        effective_max_size = max_size
        for c in candidates:
            mbs = int(c.get("match", {}).get("mbs", 1) or 1)
            if mbs > effective_max_size:
                effective_max_size = mbs

        selected_matches = []
        max_mbs_needed = 1
        
        for c in candidates:
            mbs = int(c.get("match", {}).get("mbs", 1) or 1)
            if len(selected_matches) >= effective_max_size and len(selected_matches) >= max_mbs_needed:
                break
                
            max_mbs_needed = max(max_mbs_needed, mbs)
            selected_matches.append(c)
            
        if len(selected_matches) < max_mbs_needed:
            self.logger.warning(f"Cannot satisfy MBS {max_mbs_needed} with only {len(selected_matches)} candidate matches. Coupon discarded.")
            return None
            
        combined_odds = 1.0
        combined_prob = 1.0
        combined_ev = 0.0
        selections = []
        
        for m in selected_matches:
            combined_odds *= m["odds"]
            combined_prob *= m["adjusted_probability"]
            combined_ev += m["expected_value"]
            selections.append({
                "id": m["match"]["id"],
                "home": m["match"]["home"],
                "away": m["match"]["away"],
                "selection": m["selection"],
                "odds": m["odds"],
                "mbs": m["match"].get("mbs", 1),
                "adjusted_probability": m["adjusted_probability"],
                "most_likely_score": m.get("most_likely_score", "N/A")
            })
            
        return {
            "type": target_type,
            "selections": selections,
            "combined_odds": round(combined_odds, 2),
            "estimated_win_probability": round(combined_prob, 4),
            "collective_expected_value": round(combined_ev, 4)
        }
