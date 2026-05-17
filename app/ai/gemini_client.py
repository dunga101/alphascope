import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found")

client = genai.Client(api_key=api_key)


def analyze_market(report_text: str):
    prompt = f"""
You are a disciplined financial market analyst.

Analyze the following technical stock screening report.

Tasks:
1. Summarize overall market conditions.
2. Identify strongest watchlist candidates.
3. Highlight overheated names.
4. Identify weak / avoid names.
5. Provide short-term observations (days to weeks).
6. Provide medium-term observations (1–6 months).
7. Mention major risks.

Do NOT provide direct financial advice.
Do NOT say BUY or SELL.
Use professional concise language.

REPORT:
{report_text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    return response.text


if __name__ == "__main__":
    with open("reports/daily_report.md", "r") as f:
        report = f.read()

    analysis = analyze_market(report)

    print(analysis)
