"""
database/seed_database.py

Reads clean, structured CSV files from data/ and loads them into SQLite.
CSVs are assumed to be clean — only basic type conversion is performed here.
"""

import csv
import sqlite3
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent
DATA_DIR    = ROOT / "data"
DB_PATH     = DATA_DIR / "market_intelligence.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Canonical market names — maps CSV variants to the short form used across all tables
MARKET_NAME_MAP = {
    "central (cbd/off cbd)":           "Central",
    "whitefield (peripheral east)":    "Whitefield",
    "north (peripheral north)":        "North",
    "electronic city (peripheral south)": "Electronic City",
    "koramangala (suburban south)":    "Koramangala",
    "orr (incl. marathahalli)":        "ORR",
}

def normalize_market(raw: str) -> str:
    """Return canonical short market name, falling back to the raw value."""
    return MARKET_NAME_MAP.get(raw.strip().lower(), raw.strip())


# ── Type helpers ──────────────────────────────────────────────────────────────

def to_str(val: str) -> str | None:
    """Return stripped string, or None for blank / N/A values."""
    s = str(val).strip()
    return None if s.lower() in ("", "n/a", "na", "null", "none") else s


def to_float(val: str) -> float | None:
    """Strip % and commas, return float or None."""
    s = to_str(val)
    if s is None:
        return None
    try:
        return float(s.replace("%", "").replace(",", "").strip())
    except ValueError:
        return None


def to_int(val: str) -> int | None:
    """Return int or None."""
    f = to_float(val)
    return None if f is None else int(f)


def parse_pricing(val: str) -> tuple[float | None, float | None]:
    """Split '15000-18000' into (15000.0, 18000.0)."""
    s = to_str(val)
    if s is None:
        return None, None
    parts = s.replace(",", "").split("-")
    if len(parts) == 2:
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            pass
    single = to_float(val)
    return single, single


def make_period(quarter: str, year: str) -> str:
    """Combine 'Q2' + '2026' → 'Q2-2026'."""
    return f"{quarter.strip()}-{year.strip()}"


# ── CSV loader ────────────────────────────────────────────────────────────────

def load_csv(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ── Seeder functions ──────────────────────────────────────────────────────────

def seed_market_fundamentals(conn: sqlite3.Connection) -> int:
    path = DATA_DIR / "Market Fundamentals.csv"
    loaded = 0
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # Skip the malformed header row
        for row in reader:
            if not row or not row[0].strip():
                continue
            market = normalize_market(to_str(row[0]))
            conn.execute("""
                INSERT OR REPLACE INTO market_fundamentals
                    (market_name, quarter, year,
                     grade_a_supply_sqft, occupied_space_sqft, vacancy_pct,
                     avg_asking_rent, rent_movement_pct,
                     new_supply_sqft, absorption_sqft)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                market,
                to_str(row[1]),
                to_int(row[2]),
                to_int(row[3]),
                to_int(row[4]),
                to_float(row[5]),
                to_float(row[6]),
                to_float(row[7]),
                to_int(row[8]),
                to_int(row[9]),
            ))
            loaded += 1
    return loaded


def seed_demand_indicators(conn: sqlite3.Connection) -> int:
    rows = load_csv("demand indicators.csv")
    loaded = 0
    for row in rows:
        market = to_str(row.get("Micro-market", ""))
        if not market:
            continue
        conn.execute("""
            INSERT OR REPLACE INTO demand_indicators
                (market_name, quarter, year,
                 leasing_activity_sqft, transaction_count,
                 avg_transaction_size_sqft, major_occupiers, est_seat_demand)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            market,
            to_str(row.get("Quarter", "")),
            to_int(row.get("Year", "")),
            to_int(row.get("Leasing Activity (sq ft)", "")),
            to_int(row.get("Transaction Count", "")),
            to_int(row.get("Avg. Transaction Size (sq ft)", "")),
            to_str(row.get("Major Occupiers", "")),
            to_int(row.get("Est. Employee/Seat Demand", "")),
        ))
        loaded += 1
    return loaded


def seed_competition(conn: sqlite3.Connection) -> int:
    rows = load_csv("competetion.csv")
    loaded = 0
    for row in rows:
        market = to_str(row.get("Micro-market", ""))
        if not market:
            continue
        market = normalize_market(market)
        pricing_min, pricing_max = parse_pricing(
            row.get("Approximate pricing (INR/seat/month)", "")
        )
        conn.execute("""
            INSERT OR REPLACE INTO competition
                (market_name, operators, wework_centres,
                 pricing_min, pricing_max, presence_evidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            market,
            to_str(row.get("Competition Managed-office operators", "")),
            to_int(row.get("Managed-office supply (WeWork)", "")),
            pricing_min,
            pricing_max,
            to_str(row.get("Presence of major operators", "")),
        ))
        loaded += 1
    return loaded


def seed_market_catalysts(conn: sqlite3.Connection) -> int:
    rows = load_csv("market catalysts.csv")
    loaded = 0
    for row in rows:
        market = to_str(row.get("Micro-market", ""))
        if not market:
            continue
        conn.execute("""
            INSERT OR REPLACE INTO market_catalysts
                (market_name, upcoming_infrastructure, metro_airport_connectivity,
                 key_developments, development_period, upcoming_supply_sqft)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            market,
            to_str(row.get("Upcoming Infrastructure", "")),
            to_str(row.get("Metro/Airport Connectivity", "")),
            to_str(row.get("Key Developments", "")),
            to_str(row.get("Development Period", "")),
            to_int(row.get("Upcoming Supply (sq ft)", "")),
        ))
        loaded += 1
    return loaded


def seed_city_summary(conn: sqlite3.Connection) -> int:
    rows = load_csv("market summary.csv")
    loaded = 0
    for row in rows:
        period = to_str(row.get("Period", ""))
        if not period or period.upper() == "H1":
            continue  # skip aggregate row
        period_norm = f"{period}-2026"  # Q1 → Q1-2026
        conn.execute("""
            INSERT OR REPLACE INTO city_summary
                (period, vacancy_pct, net_absorption_msf,
                 gross_leasing_msf, new_supply_msf, avg_rent)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            period_norm,
            to_float(row.get("Vacancy (%)", "")),
            to_float(row.get("Net Absorption (MSF)", "")),
            to_float(row.get("Gross Leasing Activity (MSF)", "")),
            to_float(row.get("New Supply (MSF)", "")),
            to_float(row.get("Rent (₹/SF/Month)", "")),
        ))
        loaded += 1
    return loaded


def seed_transactions(conn: sqlite3.Connection) -> int:
    rows = load_csv("transactions.csv")
    loaded = 0
    for row in rows:
        company = to_str(row.get("Company", ""))
        if not company:
            continue
        conn.execute("""
            INSERT INTO transactions
                (company, market_name, area_leased_sqft, transaction_date,
                 rent_per_sqft, sector, transaction_type, lease_type, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company,
            to_str(row.get("Micro-market", "")),
            to_int(row.get("Area leased (sq ft)", "")),
            make_period(row.get("Quarter", ""), row.get("Year", "")),
            to_float(row.get("Rent (INR/sq ft/month)", "")),
            to_str(row.get("Sector", "")),
            to_str(row.get("Expansion/New Entry", "")),
            to_str(row.get("Lease Type", "")),
            to_str(row.get("Source", "")),
        ))
        loaded += 1
    return loaded


# ── Verification ──────────────────────────────────────────────────────────────

def verify(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    tables = [
        "market_fundamentals", "demand_indicators", "competition",
        "market_catalysts", "city_summary", "transactions",
    ]

    print("\n" + "=" * 60)
    print("VERIFICATION REPORT")
    print("=" * 60)

    print("\n-- Row counts ------------------------------------------")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        n = cur.fetchone()[0]
        print(f"   {t:<30} {n:>3} row(s)")

    print("\n-- Sample records --------------------------------------")
    samples = {
        "market_fundamentals": (
            "SELECT market_name, quarter, year, vacancy_pct, avg_asking_rent, "
            "absorption_sqft FROM market_fundamentals LIMIT 3"
        ),
        "demand_indicators": (
            "SELECT market_name, quarter, year, leasing_activity_sqft, "
            "major_occupiers FROM demand_indicators LIMIT 3"
        ),
        "competition": (
            "SELECT market_name, operators, wework_centres, "
            "pricing_min, pricing_max FROM competition LIMIT 3"
        ),
        "market_catalysts": (
            "SELECT market_name, key_developments, upcoming_supply_sqft "
            "FROM market_catalysts LIMIT 3"
        ),
        "city_summary": "SELECT * FROM city_summary",
        "transactions": (
            "SELECT company, market_name, area_leased_sqft, "
            "transaction_date, rent_per_sqft FROM transactions LIMIT 3"
        ),
    }
    for t, sql in samples.items():
        print(f"\n  {t}:")
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        for r in cur.fetchall():
            print(f"    {dict(zip(cols, r))}")

    print("\n-- NULL audit ------------------------------------------")
    checks = [
        ("market_fundamentals", "avg_asking_rent"),
        ("market_fundamentals", "vacancy_pct"),
        ("transactions",        "area_leased_sqft"),
        ("transactions",        "market_name"),
    ]
    for table, col in checks:
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL")
        n = cur.fetchone()[0]
        flag = "  OK" if n == 0 else f"  WARN: {n} NULL(s)"
        print(f"   {table}.{col:<25} {flag}")

    print("\n" + "=" * 60)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("Bangalore Market Intelligence — Database Seeder")
    print("=" * 60)
    print(f"\nDB path  : {DB_PATH}")
    print(f"Schema   : {SCHEMA_PATH}")
    print(f"Data dir : {DATA_DIR}")

    if DB_PATH.exists():
        DB_PATH.unlink()
        print("\nDropped existing database.")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    print("Schema applied.")

    seeders = [
        ("market_fundamentals", seed_market_fundamentals),
        ("demand_indicators",   seed_demand_indicators),
        ("competition",         seed_competition),
        ("market_catalysts",    seed_market_catalysts),
        ("city_summary",        seed_city_summary),
        ("transactions",        seed_transactions),
    ]

    print("\nLoading CSV data...")
    total = 0
    for table_name, fn in seeders:
        n = fn(conn)
        total += n
        status = "OK" if n > 0 else "WARN"
        print(f"   [{status}] {table_name:<30} {n} row(s) loaded")

    conn.commit()
    print(f"\nTotal rows inserted: {total}")

    verify(conn)

    conn.close()
    print(f"\nDatabase ready: {DB_PATH}\n")


if __name__ == "__main__":
    main()
