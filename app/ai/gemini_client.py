import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found")

client = genai.Client(api_key=api_key)


def analyze_market(
    report_text: str,
    macro_context: dict,
    sector_breadth: dict,
    earnings_context: dict
):
    prompt = f"""
You are a disciplined professional financial market intelligence analyst.

Return ONLY valid JSON.

No markdown.
No explanations.
No prose outside JSON.

Required JSON schema:

{{
  "market_regime": "RISK_ON | RISK_OFF | MIXED",
  "confidence": 0-100,
  "macro_summary": [],
  "strong_sectors": [],
  "weak_sectors": [],
  "top_candidates": [],
  "overheated_names": [],
  "weak_names": [],
  "event_risk_names": [],
  "short_term_outlook": "",
  "medium_term_outlook": "",
  "major_risks": []
}}

Rules:
- Base conclusions ONLY on provided data
- Use earnings event risk intelligently
- Stocks with HIGH event risk should be flagged
- If uncertain, reduce confidence
- Do not invent narratives unsupported by inputs
- No BUY/SELL language
- Return valid JSON only

MARKET MACRO CONTEXT:
{macro_context}

SECTOR BREADTH:
{sector_breadth}

EARNINGS EVENT CONTEXT:
{earnings_context}

TECHNICAL STOCK SCREENING REPORT:
{report_text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    raw = response.text.strip()

    if raw.startswith("```json"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    return json.loads(raw)


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