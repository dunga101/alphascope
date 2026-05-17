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
    sector_breadth: dict
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
  "short_term_outlook": "",
  "medium_term_outlook": "",
  "major_risks": []
}}

Rules:
- Base conclusions ONLY on provided data.
- If uncertain, lower confidence.
- Do not invent macro narratives unsupported by inputs.
- No BUY/SELL language.

MARKET MACRO CONTEXT:
{macro_context}

SECTOR BREADTH:
{sector_breadth}

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