"""
A/B Test Statistical Significance Analysis

This module provides statistical analysis for the VibeReco A/B test results:
- Win rate with confidence intervals (Wilson 95% CI)
- Binomial test for significance (H0: p = 0.5)
- Summary statistics for scientific reporting

Usage:
    python ab_significance.py              # Fetch from Redis and analyze
    python ab_significance.py --local      # Use local votes from JSON
"""

import json
import os
import math
from typing import Optional
from dataclasses import dataclass

# For fetching from Redis (optional)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


@dataclass
class SignificanceResult:
    """Container for statistical significance analysis results."""
    n_votes: int
    vibe_wins: int
    youtube_wins: int
    win_rate: float
    wilson_ci_lower: float
    wilson_ci_upper: float
    margin_of_error: float
    p_value: float
    is_significant: bool
    interpretation: str


def wilson_confidence_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """
    Calculate Wilson score confidence interval for a binomial proportion.
    
    This is preferred over the normal approximation (Wald interval) for small
    samples and extreme proportions. It has better coverage properties.
    
    Args:
        successes: Number of successes (vibe wins)
        n: Total number of trials (votes)
        z: Z-score for confidence level (1.96 = 95% CI)
        
    Returns:
        Tuple of (lower_bound, upper_bound) for the confidence interval
    """
    if n == 0:
        return (0.0, 0.0)
    
    p_hat = successes / n
    
    denominator = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denominator
    margin = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denominator
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    
    return (lower, upper)


def binomial_test_pvalue(successes: int, n: int, p0: float = 0.5) -> float:
    """
    Calculate p-value for a two-sided binomial test.
    
    Tests H0: p = p0 vs H1: p ≠ p0
    Uses normal approximation for n >= 30, exact binomial for smaller samples.
    
    Args:
        successes: Number of observed successes
        n: Total number of trials
        p0: Null hypothesis proportion (default 0.5)
        
    Returns:
        Two-sided p-value
    """
    if n == 0:
        return 1.0
    
    p_hat = successes / n
    
    # For larger samples, use normal approximation
    if n >= 30:
        # z-test for proportion
        se = math.sqrt(p0 * (1 - p0) / n)
        z = abs(p_hat - p0) / se
        
        # Two-sided p-value using normal approximation
        # P(Z > |z|) * 2
        p_value = 2 * (1 - normal_cdf(z))
        return p_value
    else:
        # For small samples, use exact binomial test
        return exact_binomial_test(successes, n, p0)


def normal_cdf(x: float) -> float:
    """
    Standard normal cumulative distribution function.
    Uses the error function approximation.
    """
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def exact_binomial_test(k: int, n: int, p: float = 0.5) -> float:
    """
    Exact two-sided binomial test p-value.
    
    Calculates P(X <= k) if k < n*p, else P(X >= k), then doubles for two-sided.
    """
    def binomial_pmf(x, n, p):
        """Probability mass function for binomial distribution."""
        from math import comb
        return comb(n, x) * (p ** x) * ((1 - p) ** (n - x))
    
    # Calculate probability of observed or more extreme
    expected = n * p
    
    if k <= expected:
        # Sum P(X <= k)
        p_value = sum(binomial_pmf(i, n, p) for i in range(k + 1))
    else:
        # Sum P(X >= k)
        p_value = sum(binomial_pmf(i, n, p) for i in range(k, n + 1))
    
    # Two-sided: multiply by 2 (capped at 1)
    return min(1.0, 2 * p_value)


def analyze_significance(
    vibe_wins: int, 
    youtube_wins: int,
    confidence_level: float = 0.95
) -> SignificanceResult:
    """
    Perform complete statistical significance analysis.
    
    Args:
        vibe_wins: Number of votes for VibeReco
        youtube_wins: Number of votes for YouTube
        confidence_level: Confidence level for CI (default 0.95)
        
    Returns:
        SignificanceResult with all statistical measures
    """
    n_votes = vibe_wins + youtube_wins
    
    if n_votes == 0:
        return SignificanceResult(
            n_votes=0,
            vibe_wins=0,
            youtube_wins=0,
            win_rate=0.0,
            wilson_ci_lower=0.0,
            wilson_ci_upper=0.0,
            margin_of_error=0.0,
            p_value=1.0,
            is_significant=False,
            interpretation="Aucun vote enregistré."
        )
    
    # Win rate
    win_rate = vibe_wins / n_votes
    
    # Wilson confidence interval
    z = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%
    ci_lower, ci_upper = wilson_confidence_interval(vibe_wins, n_votes, z)
    margin = (ci_upper - ci_lower) / 2
    
    # P-value for H0: p = 0.5 (no difference)
    p_value = binomial_test_pvalue(vibe_wins, n_votes, 0.5)
    
    # Significance at α = 0.05
    is_significant = p_value < 0.05
    
    # Generate interpretation
    interpretation = generate_interpretation(
        win_rate, ci_lower, ci_upper, p_value, n_votes, is_significant
    )
    
    return SignificanceResult(
        n_votes=n_votes,
        vibe_wins=vibe_wins,
        youtube_wins=youtube_wins,
        win_rate=win_rate,
        wilson_ci_lower=ci_lower,
        wilson_ci_upper=ci_upper,
        margin_of_error=margin,
        p_value=p_value,
        is_significant=is_significant,
        interpretation=interpretation
    )


def generate_interpretation(
    win_rate: float, 
    ci_lower: float, 
    ci_upper: float, 
    p_value: float, 
    n: int,
    is_significant: bool
) -> str:
    """Generate human-readable interpretation of results."""
    
    win_pct = win_rate * 100
    ci_lower_pct = ci_lower * 100
    ci_upper_pct = ci_upper * 100
    
    if is_significant and ci_lower > 0.5:
        return (
            f"✅ Résultat SIGNIFICATIF (p = {p_value:.4f})\n"
            f"VibeReco obtient un taux de victoire de {win_pct:.1f}% "
            f"[IC 95% : {ci_lower_pct:.1f}% – {ci_upper_pct:.1f}%].\n"
            f"Avec {n} votes, on peut affirmer que VibeReco surpasse YouTube "
            f"de manière statistiquement robuste."
        )
    elif is_significant and ci_upper < 0.5:
        return (
            f"⚠️ Résultat SIGNIFICATIF en faveur de YouTube (p = {p_value:.4f})\n"
            f"VibeReco obtient seulement {win_pct:.1f}% "
            f"[IC 95% : {ci_lower_pct:.1f}% – {ci_upper_pct:.1f}%].\n"
            f"YouTube performe mieux de manière significative."
        )
    else:
        # Not significant - tendance but need more data
        direction = "positive" if win_rate >= 0.5 else "négative"
        return (
            f"📊 Tendance {direction} mais PAS ENCORE DÉFINITIVE (p = {p_value:.4f})\n"
            f"VibeReco obtient {win_pct:.1f}% [IC 95% : {ci_lower_pct:.1f}% – {ci_upper_pct:.1f}%].\n"
            f"Avec {n} votes, l'intervalle de confiance chevauche 50%.\n"
            f"→ Besoin de plus de votes pour conclure de manière robuste."
        )


def load_votes_from_local(filepath: str = None) -> tuple[int, int]:
    """
    Load votes from local JSON file (localStorage backup).
    
    Returns:
        Tuple of (vibe_wins, youtube_wins)
    """
    if filepath is None:
        # Try common locations
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "data", "local_votes.json"),
            os.path.join(os.path.dirname(__file__), "votes.json"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                filepath = path
                break
    
    if filepath is None or not os.path.exists(filepath):
        print("⚠️ No local votes file found.")
        return (0, 0)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        votes = json.load(f)
    
    vibe_wins = sum(1 for v in votes if v.get('winnerSource') == 'vibe')
    youtube_wins = sum(1 for v in votes if v.get('winnerSource') == 'youtube')
    
    return (vibe_wins, youtube_wins)


def fetch_stats_from_api(api_url: str = None) -> Optional[tuple[int, int]]:
    """
    Fetch vote stats from the API endpoint.
    
    Returns:
        Tuple of (vibe_wins, youtube_wins) or None if failed
    """
    if not HAS_REQUESTS:
        print("⚠️ requests library not installed. Run: pip install requests")
        return None
    
    if api_url is None:
        # Default to production URL or local
        api_url = os.environ.get(
            'VIBERECO_API_URL', 
            'https://vibe-reco.vercel.app/api/track'
        )
    
    try:
        response = requests.get(api_url, timeout=10)
        if response.ok:
            data = response.json()
            return (data.get('vibe_wins', 0), data.get('youtube_wins', 0))
        else:
            print(f"⚠️ API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Failed to fetch from API: {e}")
        return None


def print_report(result: SignificanceResult, for_article: bool = True):
    """Print formatted statistical report."""
    
    print("\n" + "=" * 70)
    print(" VibeReco A/B Test - Analyse de Significativité Statistique")
    print("=" * 70)
    
    print(f"\n📊 DONNÉES")
    print(f"   • Nombre total de votes : {result.n_votes}")
    print(f"   • Victoires VibeReco    : {result.vibe_wins}")
    print(f"   • Victoires YouTube     : {result.youtube_wins}")
    
    print(f"\n📈 MÉTRIQUES PRINCIPALES")
    print(f"   • Win Rate VibeReco     : {result.win_rate * 100:.1f}%")
    print(f"   • Intervalle de confiance Wilson (95%) :")
    print(f"     [{result.wilson_ci_lower * 100:.1f}% – {result.wilson_ci_upper * 100:.1f}%]")
    print(f"   • Marge d'erreur        : ± {result.margin_of_error * 100:.1f}%")
    
    print(f"\n🔬 TEST STATISTIQUE")
    print(f"   • H₀ : p = 50% (pas de différence)")
    print(f"   • H₁ : p ≠ 50%")
    print(f"   • p-value               : {result.p_value:.4f}")
    print(f"   • Significatif (α=0.05) : {'✅ Oui' if result.is_significant else '❌ Non'}")
    
    print(f"\n💡 INTERPRÉTATION")
    for line in result.interpretation.split('\n'):
        print(f"   {line}")
    
    if for_article:
        print(f"\n📝 FORMULATION POUR L'ARTICLE")
        print("-" * 50)
        if result.is_significant:
            print(f"« Sur {result.n_votes} évaluations en aveugle, VibeReco a été préféré")
            print(f"  dans {result.win_rate * 100:.1f}% des cas (IC 95% : {result.wilson_ci_lower * 100:.1f}%–{result.wilson_ci_upper * 100:.1f}%,")
            print(f"  p = {result.p_value:.3f}), démontrant une amélioration significative")
            print(f"  de la cohérence perçue par rapport à l'ordre YouTube original. »")
        else:
            print(f"« Sur {result.n_votes} évaluations en aveugle, VibeReco a été préféré")
            print(f"  dans {result.win_rate * 100:.1f}% des cas (IC 95% : {result.wilson_ci_lower * 100:.1f}%–{result.wilson_ci_upper * 100:.1f}%,")
            print(f"  p = {result.p_value:.2f}). Cette tendance positive nécessite")
            print(f"  davantage de données pour atteindre la significativité statistique. »")
    
    print("\n" + "=" * 70)


def main():
    """Main entry point for CLI usage."""
    import sys
    
    use_local = '--local' in sys.argv
    
    if use_local:
        print("📂 Loading from local votes file...")
        vibe_wins, youtube_wins = load_votes_from_local()
    else:
        print("🌐 Fetching from API...")
        result = fetch_stats_from_api()
        if result is None:
            print("Falling back to local votes...")
            vibe_wins, youtube_wins = load_votes_from_local()
        else:
            vibe_wins, youtube_wins = result
    
    # Demo mode if no votes found
    if vibe_wins == 0 and youtube_wins == 0:
        print("\n⚠️ No votes found. Running with example data (N=51, 52% vibe wins)...")
        vibe_wins, youtube_wins = 27, 24  # Example: 52.9% win rate
    
    result = analyze_significance(vibe_wins, youtube_wins)
    print_report(result)
    
    return result


if __name__ == "__main__":
    main()
