from typing import List


SYSTEMIC_KEYWORDS = [
    "fed",
    "federal reserve",
    "interest rate",
    "rate hike",
    "rate cut",
    "inflation",
    "cpi",
    "ppi",
    "recession",
    "banking crisis",
    "liquidity crisis",
    "default",
    "debt ceiling",
    "tariff",
    "trade war",
    "oil shock",
    "war",
    "geopolitical",
    "sanctions",
    "black swan",
    "credit event",
    "treasury",
    "yield shock",
]


def detect_systemic_event(headlines: List[str]) -> bool:
    if not headlines:
        return False

    combined = " ".join(headlines).lower()

    for keyword in SYSTEMIC_KEYWORDS:
        if keyword in combined:
            return True

    return False


if __name__ == "__main__":
    test = [
        "Fed warns inflation remains sticky",
        "Treasury yields surge after CPI surprise",
    ]

    print(detect_systemic_event(test))
