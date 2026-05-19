import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from google import genai


load_dotenv(".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found")

client = genai.Client(api_key=GEMINI_API_KEY)


SYSTEM_PROMPT = """
You are AlphaScope's institutional event-intelligence analyst.

Your job is to convert filtered macro/market news into disciplined directional intelligence.

STRICT OUTPUT RULE:
Return ONLY raw JSON.
No markdown.
No explanations.
No code fences.

Required schema:

{
  "executive_summary": "",
  "market_regime_bias": "RISK_ON | RISK_OFF | MIXED | NEUTRAL",
  "macro_risks": [],
  "macro_opportunities": [],
  "sector_watchlist": [],
  "key_catalysts": [],
  "confidence": 0
}

DECISION RULES:

1. Default to directional classification when evidence exists.

2. Use RISK_OFF when:
- inflation pressure rises
- war/geopolitical escalation exists
- sanctions appear
- treasury instability exists
- recession risk rises
- credit stress appears
- macro downside dominates

3. Use RISK_ON when:
- easing inflation
- improving liquidity
- broad growth optimism
- falling volatility
- constructive macro expansion

4. Use MIXED ONLY when:
- materially balanced positive and negative forces exist
AND
- no dominant macro narrative exists

5. NEUTRAL only when:
- insufficient information exists

6. MIXED should be rare.

7. Confidence logic:
- 80–95 only for strong coherent macro narratives
- 60–79 moderate conviction
- <60 uncertain conditions

STYLE:
- conservative
- institutional
- concise
- no hype
- no trade recommendations
"""


def _clean_json_response(raw_text: str) -> str:
    cleaned = raw_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "", 1)

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "", 1)

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def _fallback_response(raw_text: str) -> Dict[str, Any]:
    return {
        "executive_summary": raw_text[:1000],
        "market_regime_bias": "MIXED",
        "macro_risks": [],
        "macro_opportunities": [],
        "sector_watchlist": [],
        "key_catalysts": [],
        "confidence": 50,
    }


def _post_process_bias(result: Dict[str, Any]) -> Dict[str, Any]:
    bias = str(result.get("market_regime_bias", "MIXED")).upper()
    risks = result.get("macro_risks", [])
    summary = str(result.get("executive_summary", "")).lower()

    risk_keywords = [
        "inflation",
        "war",
        "sanctions",
        "treasury",
        "recession",
        "crisis",
        "consumer weakness",
        "yield shock",
        "credit",
        "geopolitical",
    ]

    if bias == "MIXED":
        strong_risk_signals = len(risks) >= 3

        summary_risk_hit = any(
            keyword in summary for keyword in risk_keywords
        )

        if strong_risk_signals or summary_risk_hit:
            result["market_regime_bias"] = "RISK_OFF"

            if result.get("confidence", 0) < 70:
                result["confidence"] = 70

    return result


def analyze_news_events(news_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not news_events:
        return {
            "executive_summary": "No high-quality market events available.",
            "market_regime_bias": "NEUTRAL",
            "macro_risks": [],
            "macro_opportunities": [],
            "sector_watchlist": [],
            "key_catalysts": [],
            "confidence": 0,
        }

    payload = {
        "news_events": news_events[:12]
    }

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                SYSTEM_PROMPT,
                json.dumps(payload, indent=2)
            ],
        )

        raw_text = response.text.strip()
        cleaned_text = _clean_json_response(raw_text)

        try:
            parsed = json.loads(cleaned_text)
            return _post_process_bias(parsed)

        except json.JSONDecodeError:
            return _fallback_response(raw_text)

    except Exception as e:
        return {
            "executive_summary": f"Gemini analysis failed: {str(e)}",
            "market_regime_bias": "MIXED",
            "macro_risks": [],
            "macro_opportunities": [],
            "sector_watchlist": [],
            "key_catalysts": [],
            "confidence": 0,
        }


if __name__ == "__main__":
    from pprint import pprint
    from app.collectors.news_intelligence import collect_news_intelligence

    events = collect_news_intelligence()
    analysis = analyze_news_events(events)
    pprint(analysis)