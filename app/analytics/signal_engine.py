from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List, Tuple

from app.analytics.technical_engine import (
    TechnicalIndicators,
    get_symbol_indicators,
)


@dataclass
class TechnicalSignal:
    symbol: str
    latest_date: str
    latest_close: float

    trend: str
    momentum: str
    volatility: str
    relative_strength: str
    risk_state: str

    signal: str
    confidence_score: int
    reasoning: List[str]


def classify_trend(indicators: TechnicalIndicators) -> Tuple[str, List[str], int]:
    reasons = []
    score = 0

    price = indicators.latest_close
    sma20 = indicators.sma20
    sma50 = indicators.sma50
    sma200 = indicators.sma200

    if sma20 is None or sma50 is None or sma200 is None:
        return "UNKNOWN", ["Insufficient moving average data."], 0

    if price > sma20 > sma50 > sma200:
        reasons.append("Price is above SMA20, SMA50, and SMA200 with bullish moving average alignment.")
        score += 30
        return "STRONG_BULLISH", reasons, score

    if price > sma50 > sma200:
        reasons.append("Price is above SMA50 and SMA200, indicating a constructive intermediate trend.")
        score += 22
        return "BULLISH", reasons, score

    if price > sma200 and sma50 < sma200:
        reasons.append("Price is above SMA200, but SMA50 remains below SMA200, suggesting an improving but incomplete trend.")
        score += 12
        return "RECOVERING", reasons, score

    if price < sma20 < sma50 < sma200:
        reasons.append("Price is below SMA20, SMA50, and SMA200 with bearish moving average alignment.")
        score -= 30
        return "STRONG_BEARISH", reasons, score

    if price < sma50 < sma200:
        reasons.append("Price is below SMA50 and SMA200, indicating a weak intermediate trend.")
        score -= 22
        return "BEARISH", reasons, score

    if price < sma200:
        reasons.append("Price is below SMA200, indicating long-term trend weakness.")
        score -= 15
        return "WEAK", reasons, score

    reasons.append("Trend structure is mixed without clear bullish or bearish alignment.")
    return "MIXED", reasons, score


def classify_momentum(indicators: TechnicalIndicators) -> Tuple[str, List[str], int]:
    reasons = []
    score = 0

    rsi = indicators.rsi14

    if rsi is None:
        return "UNKNOWN", ["Insufficient RSI data."], 0

    if rsi >= 75:
        reasons.append("RSI is above 75, indicating very stretched upside momentum.")
        score -= 8
        return "EXTREME_OVERBOUGHT", reasons, score

    if rsi >= 70:
        reasons.append("RSI is above 70, indicating overbought momentum risk.")
        score -= 4
        return "OVERBOUGHT", reasons, score

    if 55 <= rsi < 70:
        reasons.append("RSI is between 55 and 70, indicating healthy bullish momentum.")
        score += 12
        return "BULLISH", reasons, score

    if 45 <= rsi < 55:
        reasons.append("RSI is neutral, showing balanced momentum.")
        return "NEUTRAL", reasons, score

    if 30 <= rsi < 45:
        reasons.append("RSI is below 45, indicating weakening momentum.")
        score -= 10
        return "BEARISH", reasons, score

    reasons.append("RSI is below 30, indicating oversold conditions.")
    score -= 5
    return "OVERSOLD", reasons, score


def classify_volatility(indicators: TechnicalIndicators) -> Tuple[str, List[str], int]:
    reasons = []
    score = 0

    vol = indicators.volatility30d

    if vol is None:
        return "UNKNOWN", ["Insufficient volatility data."], 0

    if vol < 15:
        reasons.append("30-day annualized volatility is low.")
        score += 8
        return "LOW", reasons, score

    if 15 <= vol < 30:
        reasons.append("30-day annualized volatility is moderate.")
        score += 4
        return "MODERATE", reasons, score

    if 30 <= vol < 50:
        reasons.append("30-day annualized volatility is elevated.")
        score -= 8
        return "ELEVATED", reasons, score

    reasons.append("30-day annualized volatility is very high.")
    score -= 15
    return "HIGH", reasons, score


def classify_relative_strength(indicators: TechnicalIndicators) -> Tuple[str, List[str], int]:
    reasons = []
    score = 0

    rs = indicators.relative_strength_vs_spy_90d

    if rs is None:
        if indicators.symbol == "SPY":
            return "BENCHMARK", ["SPY is the benchmark reference asset."], 0
        return "UNKNOWN", ["Insufficient relative strength data versus SPY."], 0

    if rs >= 15:
        reasons.append("The symbol has strongly outperformed SPY over the last 90 trading days.")
        score += 18
        return "VERY_STRONG", reasons, score

    if 5 <= rs < 15:
        reasons.append("The symbol has outperformed SPY over the last 90 trading days.")
        score += 12
        return "STRONG", reasons, score

    if -5 < rs < 5:
        reasons.append("The symbol has performed roughly in line with SPY over the last 90 trading days.")
        return "NEUTRAL", reasons, score

    if -15 < rs <= -5:
        reasons.append("The symbol has underperformed SPY over the last 90 trading days.")
        score -= 12
        return "WEAK", reasons, score

    reasons.append("The symbol has strongly underperformed SPY over the last 90 trading days.")
    score -= 18
    return "VERY_WEAK", reasons, score


def classify_risk_state(indicators: TechnicalIndicators) -> Tuple[str, List[str], int]:
    reasons = []
    score = 0

    drawdown = indicators.drawdown_from_52w_high_pct
    vol = indicators.volatility30d
    rsi = indicators.rsi14

    if drawdown is None or vol is None or rsi is None:
        return "UNKNOWN", ["Insufficient risk-state data."], 0

    if drawdown > -5 and vol < 25 and rsi < 70:
        reasons.append("Asset is near 52-week highs with controlled volatility and non-extreme RSI.")
        score += 12
        return "CONTROLLED_RISK", reasons, score

    if drawdown > -10 and vol < 35:
        reasons.append("Asset is near highs but risk is moderately elevated.")
        score += 5
        return "MODERATE_RISK", reasons, score

    if drawdown <= -20 or vol >= 50:
        reasons.append("Asset has either a deep drawdown or very high volatility.")
        score -= 18
        return "HIGH_RISK", reasons, score

    if rsi >= 70 and drawdown > -10:
        reasons.append("Asset is near highs with overbought momentum, increasing pullback risk.")
        score -= 6
        return "PULLBACK_RISK", reasons, score

    reasons.append("Risk state is mixed.")
    return "MIXED_RISK", reasons, score


def determine_final_signal(
    trend: str,
    momentum: str,
    volatility: str,
    relative_strength: str,
    risk_state: str,
    score: int,
) -> str:
    if trend in ["STRONG_BULLISH", "BULLISH"] and relative_strength in ["VERY_STRONG", "STRONG"]:
        if momentum in ["OVERBOUGHT", "EXTREME_OVERBOUGHT"]:
            return "WATCHLIST_EXTENDED_LEADER"
        if volatility in ["ELEVATED", "HIGH"]:
            return "WATCHLIST_HIGH_BETA_LEADER"
        return "BULLISH_LEADER"

    if trend in ["STRONG_BULLISH", "BULLISH"] and momentum == "BULLISH":
        return "BULLISH_CONTINUATION"

    if trend == "RECOVERING" and relative_strength in ["STRONG", "VERY_STRONG"]:
        return "RECOVERY_WITH_RELATIVE_STRENGTH"

    if trend in ["WEAK", "BEARISH", "STRONG_BEARISH"] and relative_strength in ["WEAK", "VERY_WEAK"]:
        return "AVOID_WEAK_STRUCTURE"

    if risk_state == "HIGH_RISK":
        return "HIGH_RISK_MONITOR_ONLY"

    if score >= 40:
        return "CONSTRUCTIVE"

    if score <= -25:
        return "DEFENSIVE_AVOID"

    return "MIXED_NEUTRAL"


def clamp_confidence(score: int) -> int:
    """
    Conservative confidence normalization.

    Old model used 50 + raw score and could produce 100 too easily.
    New model dampens confidence and caps the system at 90.

    25-40: weak/caution
    40-55: mixed/uncertain
    55-70: constructive
    70-82: strong
    82-90: elite but still uncertain
    """
    confidence = 45 + (score * 0.75)
    return int(max(25, min(90, round(confidence))))


def generate_signal(symbol: str) -> Optional[TechnicalSignal]:
    indicators = get_symbol_indicators(symbol)

    if indicators is None:
        return None

    all_reasons = []
    total_score = 0

    trend, trend_reasons, trend_score = classify_trend(indicators)
    momentum, momentum_reasons, momentum_score = classify_momentum(indicators)
    volatility, volatility_reasons, volatility_score = classify_volatility(indicators)
    relative_strength, rs_reasons, rs_score = classify_relative_strength(indicators)
    risk_state, risk_reasons, risk_score = classify_risk_state(indicators)

    total_score += trend_score
    total_score += momentum_score
    total_score += volatility_score
    total_score += rs_score
    total_score += risk_score

    all_reasons.extend(trend_reasons)
    all_reasons.extend(momentum_reasons)
    all_reasons.extend(volatility_reasons)
    all_reasons.extend(rs_reasons)
    all_reasons.extend(risk_reasons)

    final_signal = determine_final_signal(
        trend=trend,
        momentum=momentum,
        volatility=volatility,
        relative_strength=relative_strength,
        risk_state=risk_state,
        score=total_score,
    )

    confidence_score = clamp_confidence(total_score)

    return TechnicalSignal(
        symbol=indicators.symbol,
        latest_date=indicators.latest_date,
        latest_close=indicators.latest_close,
        trend=trend,
        momentum=momentum,
        volatility=volatility,
        relative_strength=relative_strength,
        risk_state=risk_state,
        signal=final_signal,
        confidence_score=confidence_score,
        reasoning=all_reasons,
    )


def signal_to_dict(signal: TechnicalSignal) -> Dict[str, Any]:
    return asdict(signal)


def print_signal_report(symbol: str):
    signal = generate_signal(symbol)

    if signal is None:
        print(f"No signal generated for {symbol.upper()}")
        return

    data = signal_to_dict(signal)

    print("\n" + "=" * 70)
    print(f"TECHNICAL SIGNAL REPORT: {symbol.upper()}")
    print("=" * 70)

    for key, value in data.items():
        if key != "reasoning":
            print(f"{key}: {value}")

    print("\nreasoning:")
    for reason in data["reasoning"]:
        print(f"- {reason}")


def main():
    test_symbols = ["SPY", "NVDA", "TSLA"]

    for symbol in test_symbols:
        print_signal_report(symbol)


if __name__ == "__main__":
    main()