"""
Simulation scenarios — PRD Section 38.
10 unique crash scenarios that rotate for variety each demo run.
"""
import random

# Base portfolio: NVDA (20%), AAPL (15%), MSFT (12%), TSLA (8%), AMD (5%)
# Seed prices: NVDA=120.48, AAPL=192.31, MSFT=428.57, TSLA=250.00, AMD=161.29

_ALL_CRASHES = [
    # ── 1. AI Chip Export Ban (NVDA + AMD hit) ─────────────────────────────
    {
        "id": "ai_chip_export_ban",
        "events": [
            {"delay_seconds": 1, "event": {"type": "NEWS", "headline": "BREAKING: US bans export of AI accelerator chips to China, effective immediately", "summary": "The Commerce Department issued an emergency order halting sales of NVIDIA H100, A100, and AMD MI300 chips to Chinese entities. Analysts warn of a $15B revenue hit to US chip makers.", "symbol": "NVDA"}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "NVDA", "change_percent": -5.2, "price": 114.22, "previous_price": 120.48, "volume_ratio": 4.1}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "AMD",  "change_percent": -4.8, "price": 153.54, "previous_price": 161.29, "volume_ratio": 3.7}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "NVDA", "change_percent": -9.1, "price": 109.56, "previous_price": 120.48, "volume_ratio": 6.2}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "AMD",  "change_percent": -8.3, "price": 147.89, "previous_price": 161.29, "volume_ratio": 5.8}},
        ]
    },

    # ── 2. Tesla CEO Crisis ──────────────────────────────────────────────────
    {
        "id": "tesla_ceo_crisis",
        "events": [
            {"delay_seconds": 1, "event": {"type": "NEWS", "headline": "BREAKING: SEC charges Tesla CEO with securities fraud over misleading production figures", "summary": "The SEC filed civil charges alleging the CEO deliberately inflated delivery numbers. Tesla's board is holding an emergency meeting. Trading halted briefly.", "symbol": "TSLA"}},
            {"delay_seconds": 4, "event": {"type": "PRICE_MOVEMENT", "symbol": "TSLA", "change_percent": -7.2, "price": 232.00, "previous_price": 250.00, "volume_ratio": 8.3}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "TSLA", "change_percent": -13.5, "price": 216.25, "previous_price": 250.00, "volume_ratio": 11.0}},
            {"delay_seconds": 4, "event": {"type": "NEWS", "headline": "Tesla board convenes emergency session — CEO resignation rumoured", "summary": "Sources close to the board suggest the CEO may step down as early as tonight.", "symbol": "TSLA"}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "TSLA", "change_percent": -18.4, "price": 203.99, "previous_price": 250.00, "volume_ratio": 14.5}},
        ]
    },

    # ── 3. Microsoft Cloud Outage ────────────────────────────────────────────
    {
        "id": "msft_cloud_outage",
        "events": [
            {"delay_seconds": 1, "event": {"type": "NEWS", "headline": "Azure suffers global outage — Microsoft 365, Teams, and OpenAI APIs all down", "summary": "A botched update to Azure's core DNS infrastructure has taken down services worldwide. Estimated 40M users affected. SLA breach could cost $2B+ in credits.", "symbol": "MSFT"}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "MSFT", "change_percent": -3.8, "price": 412.32, "previous_price": 428.57, "volume_ratio": 5.1}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "MSFT", "change_percent": -7.6, "price": 395.71, "previous_price": 428.57, "volume_ratio": 7.4}},
            {"delay_seconds": 3, "event": {"type": "NEWS", "headline": "Outage extends into 6th hour — Microsoft CEO addresses media", "summary": "Restoration is ongoing but not expected until overnight. Enterprise clients are exploring alternatives.", "symbol": "MSFT"}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "MSFT", "change_percent": -10.2, "price": 384.94, "previous_price": 428.57, "volume_ratio": 9.0}},
        ]
    },

    # ── 4. Apple Supply Chain Shock ──────────────────────────────────────────
    {
        "id": "apple_supply_shock",
        "events": [
            {"delay_seconds": 1, "event": {"type": "NEWS", "headline": "Foxconn halts iPhone production at all China factories amid labour unrest", "summary": "Massive worker protests at Foxconn's Zhengzhou complex have shut down assembly lines. Apple's holiday quarter shipment targets now in serious jeopardy.", "symbol": "AAPL"}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "AAPL", "change_percent": -4.1, "price": 184.44, "previous_price": 192.31, "volume_ratio": 4.5}},
            {"delay_seconds": 4, "event": {"type": "PRICE_MOVEMENT", "symbol": "AAPL", "change_percent": -8.3, "price": 176.38, "previous_price": 192.31, "volume_ratio": 7.2}},
            {"delay_seconds": 3, "event": {"type": "NEWS", "headline": "Apple cuts iPhone 16 Pro production target by 15M units", "summary": "Analyst supply chain checks confirm Apple has formally notified component suppliers to reduce Q4 orders.", "symbol": "AAPL"}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "AAPL", "change_percent": -12.0, "price": 169.23, "previous_price": 192.31, "volume_ratio": 9.8}},
        ]
    },

    # ── 5. Fed Emergency Rate Hike ───────────────────────────────────────────
    {
        "id": "fed_emergency_hike",
        "events": [
            {"delay_seconds": 1, "event": {"type": "NEWS", "headline": "Federal Reserve calls emergency meeting — surprise 75bps rate hike announced", "summary": "In an unscheduled press release, the Fed cited surging core inflation data and raised rates by 75bps. Markets in shock — this is the first emergency hike since 2020.", "symbol": None}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "NVDA", "change_percent": -6.5, "price": 112.65, "previous_price": 120.48, "volume_ratio": 5.0}},
            {"delay_seconds": 2, "event": {"type": "PRICE_MOVEMENT", "symbol": "MSFT", "change_percent": -5.1, "price": 406.73, "previous_price": 428.57, "volume_ratio": 4.4}},
            {"delay_seconds": 2, "event": {"type": "PRICE_MOVEMENT", "symbol": "TSLA", "change_percent": -9.2, "price": 226.97, "previous_price": 250.00, "volume_ratio": 6.5}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "AAPL", "change_percent": -4.8, "price": 183.09, "previous_price": 192.31, "volume_ratio": 4.0}},
        ]
    },

    # ── 6. NVDA Flash Crash ──────────────────────────────────────────────────
    {
        "id": "nvda_earnings_miss",
        "events": [
            {"delay_seconds": 1, "event": {"type": "NEWS", "headline": "NVIDIA Q3 earnings miss by 18% — data center revenue disappoints Wall Street", "summary": "NVIDIA reported data center revenue of $22.1B vs expected $26.8B, citing project delays at hyperscalers and tightening budgets.", "symbol": "NVDA"}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "NVDA", "change_percent": -4.5, "price": 115.04, "previous_price": 120.48, "volume_ratio": 3.8}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "NVDA", "change_percent": -8.9, "price": 109.75, "previous_price": 120.48, "volume_ratio": 7.6}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "AMD",  "change_percent": -6.2, "price": 151.30, "previous_price": 161.29, "volume_ratio": 5.5}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "NVDA", "change_percent": -14.3, "price": 103.21, "previous_price": 120.48, "volume_ratio": 12.3}},
        ]
    },

    # ── 7. Geopolitical Taiwan Crisis ────────────────────────────────────────
    {
        "id": "taiwan_strait_crisis",
        "events": [
            {"delay_seconds": 1, "event": {"type": "NEWS", "headline": "China begins military exercises in Taiwan Strait — TSMC warns of operational risk", "summary": "PLA naval vessels have entered the Taiwan Strait as part of what Beijing calls a 'routine exercise'. TSMC has put contingency protocols in place. Semiconductor supply chain at risk.", "symbol": None}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "NVDA", "change_percent": -7.8, "price": 111.08, "previous_price": 120.48, "volume_ratio": 6.9}},
            {"delay_seconds": 2, "event": {"type": "PRICE_MOVEMENT", "symbol": "AMD",  "change_percent": -7.1, "price": 149.83, "previous_price": 161.29, "volume_ratio": 6.2}},
            {"delay_seconds": 2, "event": {"type": "PRICE_MOVEMENT", "symbol": "AAPL", "change_percent": -5.5, "price": 181.74, "previous_price": 192.31, "volume_ratio": 5.0}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "MSFT", "change_percent": -4.2, "price": 410.57, "previous_price": 428.57, "volume_ratio": 3.8}},
        ]
    },

    # ── 8. Cyber Attack on Big Tech ──────────────────────────────────────────
    {
        "id": "big_tech_cyberattack",
        "events": [
            {"delay_seconds": 1, "event": {"type": "NEWS", "headline": "Nation-state actors breach Microsoft and Apple internal networks — source code stolen", "summary": "CISA confirms a sophisticated intrusion compromised internal repositories at both Microsoft and Apple. Customer data not yet confirmed compromised, but investigation ongoing.", "symbol": "MSFT"}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "MSFT", "change_percent": -5.9, "price": 403.25, "previous_price": 428.57, "volume_ratio": 6.8}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "AAPL", "change_percent": -4.7, "price": 183.26, "previous_price": 192.31, "volume_ratio": 5.3}},
            {"delay_seconds": 3, "event": {"type": "NEWS", "headline": "Leaked documents suggest Microsoft Azure credentials were exposed for 72 hours", "summary": "Security researchers claim to have found the breach timeline showing 3-day window of unauthorized access.", "symbol": "MSFT"}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "MSFT", "change_percent": -10.5, "price": 383.62, "previous_price": 428.57, "volume_ratio": 9.4}},
        ]
    },

    # ── 9. AMD Recall Crisis ─────────────────────────────────────────────────
    {
        "id": "amd_product_recall",
        "events": [
            {"delay_seconds": 1, "event": {"type": "NEWS", "headline": "AMD issues emergency recall of Ryzen 9000 CPUs — critical silicon defect causing data corruption", "summary": "AMD has halted shipments and initiated a recall of all Ryzen 9000 series processors after discovering a manufacturing defect causing memory data corruption under load.", "symbol": "AMD"}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "AMD",  "change_percent": -9.5, "price": 145.96, "previous_price": 161.29, "volume_ratio": 9.2}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "NVDA", "change_percent": 3.1,  "price": 124.22, "previous_price": 120.48, "volume_ratio": 2.5}},  # NVDA benefits
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "AMD",  "change_percent": -16.2, "price": 135.11, "previous_price": 161.29, "volume_ratio": 13.0}},
            {"delay_seconds": 3, "event": {"type": "NEWS", "headline": "Estimated recall cost: $3.2B — AMD to restate Q3 guidance", "summary": "Analysts model a $3.2B total recall cost including replacement hardware, logistics, and customer compensation.", "symbol": "AMD"}},
        ]
    },

    # ── 10. Broad Market Meltdown ────────────────────────────────────────────
    {
        "id": "black_monday",
        "events": [
            {"delay_seconds": 1, "event": {"type": "NEWS", "headline": "BREAKING: US credit rating downgraded to AA by Moody's — market circuit breakers triggered", "summary": "Moody's downgraded US sovereign debt citing $35T national debt and dysfunction in Congress. S&P 500 futures limit down -7%. Circuit breakers halted futures trading.", "symbol": None}},
            {"delay_seconds": 3, "event": {"type": "PRICE_MOVEMENT", "symbol": "NVDA", "change_percent": -8.5, "price": 110.24, "previous_price": 120.48, "volume_ratio": 7.5}},
            {"delay_seconds": 2, "event": {"type": "PRICE_MOVEMENT", "symbol": "AAPL", "change_percent": -7.1, "price": 178.66, "previous_price": 192.31, "volume_ratio": 6.9}},
            {"delay_seconds": 2, "event": {"type": "PRICE_MOVEMENT", "symbol": "MSFT", "change_percent": -6.8, "price": 399.46, "previous_price": 428.57, "volume_ratio": 6.4}},
            {"delay_seconds": 2, "event": {"type": "PRICE_MOVEMENT", "symbol": "TSLA", "change_percent": -11.2, "price": 221.99, "previous_price": 250.00, "volume_ratio": 9.8}},
            {"delay_seconds": 2, "event": {"type": "PRICE_MOVEMENT", "symbol": "AMD",  "change_percent": -9.3, "price": 146.30, "previous_price": 161.29, "volume_ratio": 8.0}},
        ]
    },
]

# Track which scenarios have been used to ensure rotation
_used_indices: list[int] = []


def _get_next_crash() -> dict:
    """Return the next unused crash scenario, cycling through all 10 before repeating."""
    global _used_indices
    available = [i for i in range(len(_ALL_CRASHES)) if i not in _used_indices]
    if not available:
        _used_indices = []
        available = list(range(len(_ALL_CRASHES)))
    idx = random.choice(available)
    _used_indices.append(idx)
    return _ALL_CRASHES[idx]


# Build the SCENARIOS dict — rapid_crash rotates through all 10 each call
def get_scenario_events(scenario_id: str) -> list:
    """Return the event list for a given scenario id."""
    if scenario_id == "rapid_crash":
        return _get_next_crash()["events"]
    return SCENARIOS_STATIC.get(scenario_id, [])


SCENARIOS_STATIC = {
    "normal_market": [
        {"delay_seconds": 1,  "event": {"type": "PRICE_MOVEMENT", "symbol": "NVDA", "change_percent": 0.4,  "price": 120.96, "previous_price": 120.48, "volume_ratio": 1.1}},
        {"delay_seconds": 2,  "event": {"type": "PRICE_MOVEMENT", "symbol": "AAPL", "change_percent": -0.3, "price": 191.73, "previous_price": 192.31, "volume_ratio": 0.9}},
        {"delay_seconds": 2,  "event": {"type": "PRICE_MOVEMENT", "symbol": "MSFT", "change_percent": 0.2,  "price": 429.43, "previous_price": 428.57, "volume_ratio": 0.8}},
    ],
    "breaking_news": [
        {"delay_seconds": 2, "event": {"type": "NEWS", "headline": "US announces strict new semiconductor export restrictions to China", "summary": "The Commerce Department announced sweeping new regulations restricting the sale of advanced AI chips.", "symbol": "NVDA"}},
        {"delay_seconds": 4, "event": {"type": "PRICE_MOVEMENT", "symbol": "NVDA", "change_percent": -6.5, "price": 112.65, "previous_price": 120.48, "volume_ratio": 5.8}},
    ],
    "alert_acknowledgement": [
        {"delay_seconds": 1, "event": {"type": "PRICE_MOVEMENT", "symbol": "TSLA", "change_percent": -12.5, "price": 218.75, "previous_price": 250.00, "volume_ratio": 10.2}},
    ]
}

# Unified SCENARIOS dict used by the engine
SCENARIOS = {
    "rapid_crash": [],          # populated dynamically via get_scenario_events()
    **SCENARIOS_STATIC,
    # Expose all 10 named crashes individually too
    **{c["id"]: c["events"] for c in _ALL_CRASHES},
}
