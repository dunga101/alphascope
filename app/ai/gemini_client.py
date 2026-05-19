import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv(".env")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found")

client = genai.Client(api_key=api_key)


SYSTEM_PROMPT = """
You are AlphaScope.

An institutional-grade financial market intelligence engine.

Your job is to convert multi-layer market telemetry into disciplined decision-support intelligence.

You are NOT:
- a hype commentator
- a retail momentum trader
- a social media influencer
- a sensationalist financial journalist

You ARE:
- a calm portfolio strategist
- a macro risk analyst
- a conservative institutional allocator
- a disciplined investment committee advisor

Your audience:
an intelligent but non-expert professional who wants practical market understanding.

CRITICAL:
Return ONLY valid JSON.

No markdown.
No code fences.
No commentary.
No explanations outside JSON.

JSON schema:

{
  "quick_take": "",
  "market_regime": "RISK_ON | RISK_OFF | MIXED",
  "confidence": 0,
  "macro_summary": [],
  "strong_sectors": [],
  "weak_sectors": [],
  "watchlist_names": [],
  "overheated_names": [],
  "weak_names": [],
  "event_risk_names": [],
  "short_term_outlook": "",
  "medium_term_outlook": "",
  "major_risks": []
}

ANALYTICAL RULES

1. THINK HIERARCHICALLY
Evaluate in this order:

A. Macro regime
- broad index direction
- volatility
- treasury yields
- commodities
- crypto risk appetite

B. Breadth
- participation quality
- sector leadership
- defensive vs cyclical rotation

C. Event risk
- earnings
- major catalysts
- concentrated single-name risk

D. Technical structure
- trend
- momentum
- participation
- overheating
- breakdowns

E. Fundamentals
- profitability
- balance sheet quality
- debt burden
- liquidity
- free cash flow quality
- business resilience

2. FUNDAMENTALS MATTER
Do not ignore fundamentals.

Examples:
High margins + strong cash flow + low debt:
stronger quality profile

Weak technicals + excellent fundamentals:
possible pullback, not deterioration

Weak technicals + weak fundamentals:
higher caution

3. CONSERVATIVE BIAS
Default to caution unless evidence strongly supports conviction.

4. INTERNAL CONSISTENCY

If confidence < 30:
- maximum 2 watchlist names
- highly selective only
- prefer resilient high-quality names
- avoid aggressive cyclicals unless overwhelmingly justified
- explicitly emphasize uncertainty

If market_regime == RISK_OFF:
- defensive posture
- event risk matters more
- avoid pretending strong conviction

If market_regime == MIXED:
- explicitly acknowledge uncertainty

5. QUICK TAKE
Requirements:
- plain English
- understandable by ordinary people
- under ~100 words
- explain market mood simply
- mention important risks
- practical, calm, useful

6. WATCHLIST RULES
watchlist_names are observation candidates, not recommendations.

Include only if justified by:
- resilience
- selective strength
- defensive positioning
- fundamentally strong names worth monitoring

7. OVERHEATED
Mark names where:
- technically extended
- event risk elevated
- crowded positioning likely

8. WEAK NAMES
Names with:
- deteriorating structure
- poor participation
- fundamental weakness
or both

9. CONFIDENCE SCALE
integer only

80-100:
high alignment

60-79:
moderate alignment

40-59:
mixed but usable

0-39:
uncertain / noisy / low conviction

10. NEVER INVENT

Absolutely do NOT introduce:
- geopolitical concerns
- inflation narratives
- recession commentary
- Fed speculation
- economic assumptions
- policy commentary
- macro explanations not present in supplied telemetry

If data is absent:
state uncertainty.

Do NOT fabricate explanatory narratives.
"""


def _extract_json(raw: str) -> dict:
    cleaned = raw.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "").strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in Gemini response")

    cleaned = cleaned[start:end + 1]

    return json.loads(cleaned)


def analyze_market(
    report_text: str,
    macro_context: dict,
    sector_breadth: dict,
    earnings_context: dict
):
    prompt = f"""
MARKET MACRO CONTEXT
{macro_context}

SECTOR BREADTH
{sector_breadth}

EARNINGS EVENT CONTEXT
{earnings_context}

MULTI-LAYER MARKET INTELLIGENCE
{report_text}

TASK:
Analyze the full dataset as an institutional strategist.

Pay special attention to:
- regime quality
- breadth participation
- defensive rotation
- concentration risk
- event risk
- fundamental quality
- technical/fundamental disagreement

Produce disciplined, conservative intelligence.

Do not introduce explanations or risks that are not present in the supplied data.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        config={
            "system_instruction": SYSTEM_PROMPT,
            "temperature": 0.10,
        },
        contents=prompt
    )

    return _extract_json(response.text)


if __name__ == "__main__":
    with open("reports/daily_report.md", "r", encoding="utf-8") as f:
        report = f.read()

    analysis = analyze_market(
        report_text=report,
        macro_context={},
        sector_breadth={},
        earnings_context={}
    )

    print(json.dumps(analysis, indent=2))