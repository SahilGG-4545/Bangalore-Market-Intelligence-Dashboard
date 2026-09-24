"""
ai/analyst.py — Evidence-grounded AI Market Analyst

Flow:
  question
    -> detect_intent()        keyword-based classification, no LLM
    -> build_evidence()       calls analytics/queries.py, never raw SQL
    -> format_evidence()      converts to readable text block
    -> call_llm()             sends ONLY evidence + question to LLM
    -> analyse()              orchestrates everything, returns dict for UI

The LLM receives a structured evidence package.
It never touches the database.
"""

import json
import os
import re

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from analytics.queries import (
    get_expansion_matches,
    get_market_comparison,
    get_market_detail,
    get_transactions,
)

load_dotenv()

# ── LLM client (Groq via OpenAI-compatible endpoint) ─────────────────────────
_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
MODEL = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")

# ── Known markets (for mention detection) ────────────────────────────────────
KNOWN_MARKETS = [
    "ORR", "Whitefield", "North Bangalore", "Electronic City",
    "Central Bangalore", "Koramangala", "SBD", "PBD West",
    "Hebbal", "Marathahalli",
]

# Predefined example questions (shown as clickable chips in the UI)
EXAMPLE_QUESTIONS = [
    "Which Bangalore markets are seeing increasing demand?",
    "Which markets have relatively attractive rental economics?",
    "What is driving demand in ORR?",
    "Where is managed-office competition already high?",
    "Which markets show signs of oversupply?",
    "Which markets should Autopilot investigate further?",
    "Autopilot needs 500 seats at Rs 80/sqft. Which markets should we investigate?",
]


# ── 1. Intent detection ───────────────────────────────────────────────────────
def detect_intent(question: str) -> dict:
    """
    Classify question into a category using keyword matching.
    No LLM call — fast, transparent, debuggable.
    """
    q = question.lower()

    mentioned_markets = [m for m in KNOWN_MARKETS if m.lower() in q]

    seats_m = re.search(r"(\d+)\s*seats?", q)
    rent_m  = re.search(r"(?:rs?\.?|₹|inr)\s*(\d+)", q)
    if not rent_m:
        rent_m = re.search(r"(\d+)\s*(?:/|\s+per\s+)?(?:sq\.?\s*ft|sqft)", q)

    if any(w in q for w in ["competition", "competitor", "operator", "coworking",
                              "co-working", "managed office", "flex operator"]):
        category = "COMPETITION"
    elif any(w in q for w in ["oversupply", "surplus", "too much supply", "over supply"]):
        category = "OVERSUPPLY"
    elif seats_m or (rent_m and any(w in q for w in ["seat", "need", "require",
                                                       "expand", "space for"])):
        category = "EXPANSION"
    elif any(w in q for w in ["rent", "afford", "cheap", "economic",
                               "cost", "price"]) and "which" in q:
        category = "RENT_ECONOMICS"
    elif any(w in q for w in ["demand", "growing", "increasing",
                               "active", "momentum"]) and not mentioned_markets:
        category = "DEMAND"
    elif any(w in q for w in ["recommend", "investigate", "should", "best",
                               "top market", "consider"]) and not mentioned_markets:
        category = "BEST_MARKETS"
    elif mentioned_markets:
        category = "MARKET_SPECIFIC"
    else:
        category = "BEST_MARKETS"

    return {
        "category":          category,
        "mentioned_markets": mentioned_markets,
        "seats":             int(seats_m.group(1)) if seats_m else 500,
        "target_rent":       float(rent_m.group(1)) if rent_m else 80.0,
    }


# ── 2. Evidence builder ───────────────────────────────────────────────────────
def build_evidence(intent: dict) -> dict:
    """
    Retrieve ONLY the data needed for this question category.
    Never sends the full database to the LLM.
    """
    cat     = intent["category"]
    markets = intent["mentioned_markets"]

    if cat == "MARKET_SPECIFIC" and markets:
        target = markets[0]
        detail = get_market_detail(target)
        txns   = get_transactions(target)
        return {
            "type":   "market_specific",
            "market": target,
            "detail": detail,
            "txns":   txns,
            "gaps":   [
                "Single Q2-2026 snapshot — no vacancy trend available",
                "Seat demand estimated at 60 sqft/seat (industry proxy)",
            ],
        }

    elif cat == "DEMAND":
        mf   = get_market_comparison()
        txns = get_transactions()
        tc   = txns.groupby("market_name").size().reset_index(name="txn_count")
        ta   = txns.groupby("market_name")["area_leased_sqft"].sum().reset_index(
                   name="total_area_sqft")
        mf   = mf.merge(tc, on="market_name", how="left") \
                  .merge(ta, on="market_name", how="left")
        mf["txn_count"]       = mf["txn_count"].fillna(0).astype(int)
        mf["total_area_sqft"] = mf["total_area_sqft"].fillna(0).astype(int)
        mf["est_seats"]       = (mf["total_area_sqft"] / 60).astype(int)
        return {
            "type": "demand", "mf": mf,
            "gaps": [
                "No Q1-vs-Q2 per-market vacancy trend",
                "Leasing activity qualitative for most markets",
                "Transaction count incomplete (only confirmed deals included)",
            ],
        }

    elif cat == "RENT_ECONOMICS":
        mf = get_market_comparison()
        return {
            "type": "rent_economics", "mf": mf,
            "target_rent": intent["target_rent"],
            "gaps": [
                "Rent figures are Q2-2026 derived midpoints from broker reports",
                "Actual signed deal rents may differ from asking rents",
            ],
        }

    elif cat == "COMPETITION":
        mf = get_market_comparison()
        return {
            "type": "competition", "mf": mf,
            "gaps": [
                "Managed-office supply in sqft not available — only WeWork centre count",
                "Awfis and Smartworks market share unknown",
            ],
        }

    elif cat == "OVERSUPPLY":
        mf = get_market_comparison()
        return {
            "type": "oversupply", "mf": mf,
            "gaps": [
                "No historical vacancy series — cannot confirm worsening trend",
                "Future supply pipeline only qualitative (no firm dates/sqft)",
            ],
        }

    elif cat == "EXPANSION":
        df = get_expansion_matches(intent["target_rent"], intent["seats"])
        return {
            "type": "expansion", "mf": df,
            "required_seats": intent["seats"],
            "target_rent":    intent["target_rent"],
            "gaps": [
                "No floor-plate data — vacancy doesn't confirm single-block availability",
                "Competition pricing ranges are broad; exact operator pricing varies",
            ],
        }

    else:  # BEST_MARKETS
        mf   = get_market_comparison()
        txns = get_transactions()
        return {
            "type": "best_markets", "mf": mf, "txns": txns,
            "gaps": [
                "Analysis based on single Q2-2026 snapshot",
                "No client demand survey — seat demand inferred from transactions",
            ],
        }


# ── 3. Evidence → readable text for LLM ─────────────────────────────────────
def format_evidence(evidence: dict, question: str) -> str:
    """Serialise evidence dict to a structured text block."""
    lines = [
        "=== EVIDENCE PACKAGE ===",
        f"Question: {question}",
        f"Evidence type: {evidence['type']}",
        "",
    ]

    mf: pd.DataFrame | None = evidence.get("mf")

    if evidence["type"] == "market_specific":
        d    = evidence["detail"]
        fund = d["fundamentals"][0] if d["fundamentals"] else {}
        comp = d["competition"][0]  if d["competition"]  else {}
        cat  = d["catalysts"][0]    if d["catalysts"]    else {}
        dem  = d["demand"][0]       if d["demand"]       else {}
        der  = d["derived"]

        lines += [
            f"MARKET: {evidence['market']}",
            "",
            "FUNDAMENTALS:",
            f"  Grade A Supply : {fund.get('grade_a_supply_msf', 'N/A')} MSF",
            f"  Vacancy        : {fund.get('vacancy_pct', 'N/A')}%",
            f"  Avg Asking Rent: Rs {fund.get('avg_asking_rent', 'N/A')}/sqft/month",
            f"  Rent Movement  : {fund.get('rent_movement_text', 'N/A')}",
            f"  Net Absorption : {fund.get('absorption_msf', 'N/A')} MSF",
            f"  New Supply     : {fund.get('new_supply_msf', 'N/A')} MSF",
            "",
            "DEMAND SIGNALS:",
            f"  Leasing Activity   : {dem.get('leasing_activity_text', 'N/A')}",
            f"  Major Occupiers    : {dem.get('major_occupiers', 'N/A')}",
            f"  Companies Expanding: {dem.get('companies_expanding', 'N/A')}",
            "",
            "COMPETITION:",
            f"  Operators      : {comp.get('operators', 'None confirmed')}",
            f"  WeWork Centres : {comp.get('wework_centres', 'N/A')}",
            f"  Pricing (seat) : Rs {comp.get('pricing_min', 'N/A')} - Rs {comp.get('pricing_max', 'N/A')}/month",
            "",
            "INFRASTRUCTURE:",
            f"  {cat.get('upcoming_infrastructure', 'N/A')}",
            f"  {cat.get('key_developments', 'N/A')}",
            "",
            "RECENT TRANSACTIONS:",
        ]
        for t in d["transactions"]:
            rent_str = f"Rs {t['rent_per_sqft']}/sqft" if t.get("rent_per_sqft") else "rent undisclosed"
            lines.append(
                f"  {t['company']}: {t['area_leased_sqft']:,} sqft "
                f"(~{int(t['area_leased_sqft']/60):,} seats), "
                f"{rent_str}, {t['sector']}, {t['transaction_date']}"
            )
        lines.append(
            f"\nDERIVED: {der['transaction_count']} confirmed transaction(s), "
            f"{der['total_area_leased_sqft']:,} sqft, "
            f"~{der.get('est_seat_demand', 'N/A')} estimated seats"
        )

    elif mf is not None:
        if evidence["type"] == "expansion":
            lines.append(
                f"EXPANSION REQUIREMENT: {evidence['required_seats']} seats "
                f"@ Rs {evidence['target_rent']}/sqft target rent"
            )
            lines.append("")

        lines.append("MARKET DATA:")
        for _, r in mf.iterrows():
            row_str = (
                f"  {r['market_name']}: "
                f"vacancy {r['vacancy_pct']:.1f}%, "
                f"rent Rs {r['avg_asking_rent']:.0f}/sqft, "
                f"absorption {r['absorption_msf']:.2f} MSF "
                f"({r['absorption_ratio']:.1%} of stock), "
                f"new supply {r['new_supply_msf']:.2f} MSF, "
                f"competition {r['competition_level']}"
            )
            if "rent_gap" in r.index:
                row_str += f", rent gap Rs {r['rent_gap']:+.0f} vs target"
            if pd.notna(r.get("operators")):
                row_str += f", operators: {r['operators']}"
            lines.append(row_str)

        if "txns" in evidence:
            lines += ["", "CONFIRMED TRANSACTIONS (H1 2026):"]
            for _, t in evidence["txns"].iterrows():
                lines.append(
                    f"  {t['company']} @ {t['market_name']}: "
                    f"{t['area_leased_sqft']:,} sqft (~{t['est_seats']} seats), "
                    f"{t['sector']}, {t['transaction_date']}"
                )

    lines += ["", "DATA GAPS:"]
    for gap in evidence.get("gaps", []):
        lines.append(f"  - {gap}")

    return "\n".join(lines)


# ── 4. LLM call ───────────────────────────────────────────────────────────────
_SYSTEM = """You are a senior commercial real estate analyst for Autopilot Offices evaluating Bangalore expansion.

You will receive a user question and a structured EVIDENCE PACKAGE retrieved from the market intelligence database.

Respond ONLY with valid JSON in this exact structure:

{
  "insight": "One clear, evidence-based finding in 1-2 sentences.",
  "evidence_cited": ["exact figure 1", "exact figure 2", "exact figure 3"],
  "reasoning": "Explain how the evidence supports the insight in 2-3 short sentences.",
  "risks": "State important data gaps, trade-offs, or assumptions in 1-2 sentences."
}

RULES:

- Use ONLY information contained in the EVIDENCE PACKAGE.
- Never invent statistics, facts, transactions, or comparisons.
- evidence_cited must contain 3-5 specific phrases with exact figures from the evidence.
- Use exact figures whenever available: "vacancy 2.9%" rather than "very low vacancy".
- Base conclusions on multiple relevant indicators in the evidence, not on a single metric.
- Consider both positive signals and trade-offs. For example, high rent may indicate strong demand but also increases expansion cost.
- Do not treat one transaction as proof of overall market demand.
- If comparing markets, explicitly use the available comparative evidence.
- If the evidence is insufficient to answer the question, say so clearly in "insight".
- Do not make claims beyond what the evidence supports.
- Keep all string values concise.
"""

def call_llm(question: str, evidence_str: str) -> dict:
    """Send question + evidence to LLM, return parsed JSON response."""
    user_msg = f"QUESTION: {question}\n\n{evidence_str}"
    try:
        resp = _client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.15,
            max_tokens=2000,
        )
        raw = resp.choices[0].message.content.strip()
        # Extract JSON even if the model wraps it in markdown code fences
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {
            "insight":        raw if "raw" in dir() else "Could not parse LLM response.",
            "evidence_cited": [],
            "reasoning":      f"JSON parse error: {e}",
            "risks":          "Response format issue — try rephrasing the question.",
        }
    except Exception as e:
        return {
            "insight":        f"API error: {e}",
            "evidence_cited": [],
            "reasoning":      "",
            "risks":          "Check GROQ_API_KEY and MODEL_NAME in .env file.",
        }


# ── 5. Public entry point ─────────────────────────────────────────────────────
def analyse(question: str) -> dict:
    """
    Orchestrate the full evidence-grounded analysis pipeline.
    Returns everything the Streamlit UI needs.
    """
    intent       = detect_intent(question)
    evidence     = build_evidence(intent)
    evidence_str = format_evidence(evidence, question)
    response     = call_llm(question, evidence_str)

    return {
        "question":      question,
        "intent":        intent,
        "evidence":      evidence,
        "evidence_text": evidence_str,
        "response":      response,
    }


def analyse_expansion_scenario(seats: int, rent: float, client_size: int,
                                all_markets_evidence: str, market_names: list) -> dict:
    """
    Evaluate market fit for ALL markets against the expansion requirements.
    Returns a dict keyed by market name with a short evidence-based summary.
    """
    # Build explicit JSON template so LLM doesn't add "..." or truncate
    json_template = "{\n" + ",\n".join(
        f'  "{m}": "2-sentence assessment for {m}."' for m in market_names
    ) + "\n}"

    prompt = f"""You are a commercial real estate market analyst. A company wants to expand in Bangalore.

EXPANSION REQUIREMENTS:
- Required Seats: {seats}
- Target Rent: Rs {rent}/sq.ft/month (maximum budget)
- Minimum Client Size: {client_size} employees
- City: Bangalore

MARKET DATA (from database):
{all_markets_evidence}

For EACH market, write an AI Summary of 2-3 sentences that INTERPRETS the data — do NOT repeat raw numbers.
The raw numbers (rent, vacancy, absorption, operators) will already be shown separately as "Evidence".
Your job is to explain what those facts MEAN for the expansion decision.

Connect:
- Rent vs target → does the market fit the budget?
- Vacancy → is space available?
- Absorption/leasing → is there active demand for office space?
- Operators → how competitive is the managed-office environment?
- End with a short, factual implication for the expansion.

STRICT RULES:
- Use ONLY the data provided. Do not invent, estimate, or assume.
- N/A means unavailable — do not interpret it as zero or "none".
- Do not create scores or rankings.
- Do not use vague words like "high", "strong", "low" unless the data clearly supports them.
- Do not repeat the numbers — interpret what they mean.

Example of the correct style:
"Whitefield is financially feasible against the target budget. The vacancy level indicates some available space, while the absorption and leasing activity show active office demand in the market. Three managed-office operators are present, so expansion is feasible but would need to account for an established competitive environment."

Respond ONLY with valid JSON matching this exact structure:
{json_template}
"""
    try:
        resp = _client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.15,
            max_tokens=2000,
        )
        raw = resp.choices[0].message.content.strip()
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        parsed = json.loads(json_match.group() if json_match else raw)
        return parsed
    except json.JSONDecodeError:
        # Fallback: return the raw text mapped to all markets
        return {m: "Could not parse structured response. Try again." for m in market_names}
    except Exception as e:
        return {"error": f"Analysis error: {e}"}
