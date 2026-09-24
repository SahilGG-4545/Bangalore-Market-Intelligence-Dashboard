"""
analytics/queries.py

Data-access layer for the Bangalore Market Intelligence dashboard.
All functions return pandas DataFrames or plain dicts.
Both the Streamlit UI and the AI Market Analyst import from here.

Five public functions:
    get_city_summary()                          -> DataFrame
    get_market_comparison()                     -> DataFrame  (with derived metrics)
    get_market_detail(market_name)              -> dict       (full evidence package)
    get_transactions(market_name=None)          -> DataFrame
    get_expansion_matches(target_rent, seats)   -> DataFrame
"""

from contextlib import closing

import pandas as pd

from database.connection import get_connection


# ── helpers ───────────────────────────────────────────────────────────────────

def _query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Execute a SELECT and return a DataFrame. Opens and closes the connection."""
    with closing(get_connection()) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def _operator_count(operators: str | None) -> int:
    if not operators or pd.isna(operators):
        return 0
    return len([o.strip() for o in operators.split(",") if o.strip()])


def _competition_level(n: int) -> str:
    if n >= 4:   return "High"
    if n >= 2:   return "Medium"
    if n == 1:   return "Low"
    return "None"


# ── public functions ──────────────────────────────────────────────────────────

def get_city_summary() -> pd.DataFrame:
    """
    Q1-2026 and Q2-2026 city-level KPIs.
    Source: city_summary table.
    """
    return _query("SELECT * FROM city_summary ORDER BY period")


def get_market_comparison() -> pd.DataFrame:
    """
    All markets with fundamentals + competition, aggregated to latest quarter.
    Derived metrics added in Python (not SQL):
      grade_a_supply_msf = grade_a_supply_sqft / 1,000,000
      absorption_msf     = absorption_sqft / 1,000,000
      new_supply_msf     = new_supply_sqft / 1,000,000
      absorption_ratio   = absorption_sqft / grade_a_supply_sqft
      operator_count     = number of operators (comma-split)
      competition_level  = High / Medium / Low / None
      pricing_midpoint   = (pricing_min + pricing_max) / 2
    """
    # Pick the latest quarter per market (Q2 > Q1 within each year)
    sql = """
        WITH latest AS (
            SELECT market_name,
                   MAX(year * 10 + CAST(REPLACE(quarter,'Q','') AS INTEGER)) AS sort_key
            FROM market_fundamentals
            GROUP BY market_name
        ),
        mf AS (
            SELECT f.*
            FROM market_fundamentals f
            JOIN latest l ON f.market_name = l.market_name
              AND (f.year * 10 + CAST(REPLACE(f.quarter,'Q','') AS INTEGER)) = l.sort_key
        )
        SELECT
            mf.market_name,
            mf.grade_a_supply_sqft,
            mf.occupied_space_sqft,
            mf.vacancy_pct,
            mf.avg_asking_rent,
            mf.rent_movement_pct,
            mf.new_supply_sqft,
            mf.absorption_sqft,
            c.operators,
            c.wework_centres,
            c.pricing_min,
            c.pricing_max
        FROM mf
        LEFT JOIN competition c ON mf.market_name = c.market_name
        ORDER BY mf.grade_a_supply_sqft DESC
    """
    df = _query(sql)

    # Convert sqft columns to MSF for backward compatibility with app.py
    df["grade_a_supply_msf"] = (df["grade_a_supply_sqft"] / 1_000_000).round(3)
    df["absorption_msf"]     = (df["absorption_sqft"]     / 1_000_000).round(3)
    df["new_supply_msf"]     = (df["new_supply_sqft"]     / 1_000_000).round(3)
    df["rent_movement_text"] = df["rent_movement_pct"].apply(
        lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A"
    )

    df["absorption_ratio"]  = (df["absorption_sqft"] / df["grade_a_supply_sqft"].replace(0, pd.NA)).round(4)
    df["operator_count"]    = df["operators"].apply(_operator_count)
    df["competition_level"] = df["operator_count"].apply(_competition_level)
    df["pricing_midpoint"]  = (
        (df["pricing_min"].fillna(0) + df["pricing_max"].fillna(0)) / 2
    ).where(df["pricing_min"].notna())

    return df


def get_market_detail(market_name: str) -> dict:
    """
    Full evidence package for one market — used by the AI Market Analyst.
    Fundamentals are returned for the latest quarter only.
    Returns a dict with five DataFrames (as record lists) plus derived metrics.
    """
    p = (market_name,)

    with closing(get_connection()) as conn:
        # Latest quarter only for fundamentals
        fundamentals = pd.read_sql_query("""
            SELECT * FROM market_fundamentals
            WHERE market_name = ?
            ORDER BY year DESC, CAST(REPLACE(quarter,'Q','') AS INTEGER) DESC
            LIMIT 1
        """, conn, params=p)
        demand = pd.read_sql_query(
            "SELECT * FROM demand_indicators WHERE market_name = ? ORDER BY year, quarter",
            conn, params=p
        )
        competition = pd.read_sql_query(
            "SELECT * FROM competition WHERE market_name = ?", conn, params=p
        )
        catalysts = pd.read_sql_query(
            "SELECT * FROM market_catalysts WHERE market_name = ?", conn, params=p
        )
        transactions = pd.read_sql_query(
            "SELECT * FROM transactions WHERE market_name = ?", conn, params=p
        )

    # Add MSF aliases for backward compatibility
    if not fundamentals.empty:
        fundamentals["grade_a_supply_msf"] = fundamentals["grade_a_supply_sqft"] / 1_000_000
        fundamentals["absorption_msf"]     = fundamentals["absorption_sqft"]     / 1_000_000
        fundamentals["new_supply_msf"]     = fundamentals["new_supply_sqft"]     / 1_000_000
        fundamentals["rent_movement_text"] = fundamentals["rent_movement_pct"].apply(
            lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A"
        )

    total_area = int(transactions["area_leased_sqft"].sum()) if len(transactions) else 0

    return {
        "market_name":  market_name,
        "fundamentals": fundamentals.to_dict("records"),
        "demand":       demand.to_dict("records"),
        "competition":  competition.to_dict("records"),
        "catalysts":    catalysts.to_dict("records"),
        "transactions": transactions.to_dict("records"),
        "derived": {
            "transaction_count":      len(transactions),
            "total_area_leased_sqft": total_area,
            "est_seat_demand":        int(total_area / 60) if total_area else None,
        },
    }


def get_transactions(market_name: str | None = None) -> pd.DataFrame:
    """
    All transactions, optionally filtered by market.
    Adds est_seats = area_leased_sqft / 60 (confirmed derivation rule).
    """
    if market_name:
        df = _query(
            "SELECT * FROM transactions WHERE market_name = ? ORDER BY transaction_date",
            params=(market_name,),
        )
    else:
        df = _query("SELECT * FROM transactions ORDER BY market_name, transaction_date")

    df["est_seats"] = (df["area_leased_sqft"] / 60).round(0).astype("Int64")
    return df


def get_expansion_matches(target_rent: float, required_seats: int) -> pd.DataFrame:
    """
    Rank markets against expansion requirements.
    rent_gap < 0  → market is affordable at target rent
    Ranking: lower rent_gap + lower vacancy = better fit.
    """
    df = get_market_comparison()
    df["rent_gap"]      = (df["avg_asking_rent"] - target_rent).round(2)
    df["rent_feasible"] = df["rent_gap"] <= 0
    # Rank: rent proximity (ascending) + vacancy (ascending) — lower = better
    df["fit_rank"] = (
        df["rent_gap"].rank(ascending=True) + df["vacancy_pct"].rank(ascending=True)
    )
    return df.sort_values("fit_rank").reset_index(drop=True)
