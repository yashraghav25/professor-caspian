# PRD: SentinelAI
## Autonomous Portfolio Monitoring, Impact Analysis & Multi-Channel Alerting Agent

### Hackathon Project

---

# 1. Product Overview

## 1.1 Product Name

**SentinelAI**

### Tagline

> Your portfolio doesn't need another dashboard. It needs an agent that knows when you actually need to pay attention.

---

# 2. Product Vision

SentinelAI is an autonomous financial monitoring agent that continuously observes:

1. The user's stock portfolio.
2. Market price movements.
3. Financial news.
4. News-to-stock relationships.
5. Portfolio exposure.
6. The severity and urgency of market events.

When a material event occurs, SentinelAI determines whether the user needs to know about it.

If the event is sufficiently important, SentinelAI communicates with the user through Caspian.

The agent should not simply send notifications.

It should:

- detect events
- understand events
- determine portfolio relevance
- estimate severity
- decide whether the user should be interrupted
- select an appropriate communication channel
- send the notification
- track whether the user acknowledged it
- escalate if necessary
- stop escalation when the user acknowledges the event

The core idea is:

> **An autonomous financial sentinel that protects the user's attention rather than flooding it with notifications.**

---

# 3. Problem Statement

Traditional investment applications expose users to large amounts of information:

- stock price movements
- financial news
- earnings announcements
- geopolitical events
- interest-rate decisions
- regulatory changes
- company announcements
- sector-level events

The problem is not lack of information.

The problem is:

> **Which information actually matters to this particular user's portfolio right now?**

A 5% movement in a stock the user does not own is irrelevant.

A 2% movement in a stock representing 30% of the user's portfolio may be highly relevant.

Similarly, a news article about semiconductor export restrictions becomes significantly more important if the user owns NVIDIA and AMD.

SentinelAI connects external events to the user's actual portfolio.

---

# 4. Core Product Principle

The system must NOT behave like:

```text
Market data
    ↓
Notification
```

It must behave like:

```text
Market / News Event
        ↓
Event Detection
        ↓
Portfolio Relevance
        ↓
Impact Analysis
        ↓
Severity Evaluation
        ↓
Agent Decision
        ↓
Communication Strategy
        ↓
Caspian
        ↓
User
        ↓
Acknowledgement / Escalation
```

The agent should only interrupt the user when the expected value of the information is high enough.

---

# 5. Hackathon Constraints

The project must be designed around the following constraints.

## 5.1 Budget

Target infrastructure cost:

**₹0**

The project must function using:

- free API tiers
- free databases
- free hosting tiers where practical
- local development
- deterministic simulation

Do NOT make the live demo dependent on paid market-data infrastructure.

---

## 5.2 Simulation First

The system must include a first-class market event simulator.

The simulator must generate events using exactly the same event schema consumed by the production event pipeline.

The system therefore supports:

```text
REAL DATA PROVIDER
        ↓
   Event Schema
        ↓
   Event Engine
```

and:

```text
SIMULATOR
        ↓
   Event Schema
        ↓
   Event Engine
```

The downstream system must not know or care whether an event came from a real provider or the simulator.

This is critical.

The simulator is not a fake implementation.

It is an event-injection and deterministic testing system.

---

# 6. Target Users

Primary user:

An individual investor who owns a portfolio of stocks and wants to be informed about significant developments without constantly monitoring financial applications.

The MVP should support:

- US stocks
- portfolio positions
- percentage allocation
- market price monitoring
- financial news
- personalized alerts

---

# 7. Core User Journey

## 7.1 Portfolio Setup

User opens SentinelAI.

User creates a portfolio:

```text
Portfolio Value: $100,000

NVDA   20%
AAPL   15%
MSFT   12%
TSLA    8%
AMD     5%
CASH   40%
```

The system stores:

- ticker
- quantity
- average price
- current price
- position value
- portfolio weight

---

# 8. Normal Operation

The system receives market events.

Example:

```text
NVDA +0.4%
AAPL -0.2%
MSFT +0.3%
```

No alert should be generated.

The system should recognize that these events are below the user's attention threshold.

Dashboard:

```text
Portfolio Status
NORMAL
```

---

# 9. Significant Price Movement

Simulation generates:

```text
NVDA -5.2%
```

SentinelAI calculates:

```text
NVDA portfolio weight = 20%

Price movement = -5.2%

Approximate portfolio contribution:
20% × -5.2%
≈ -1.04 percentage points
```

Severity becomes:

```text
WARNING
```

The agent sends:

```text
Email
```

through Caspian.

Example notification:

> Portfolio Alert
>
> NVIDIA has fallen 5.2%.
>
> NVIDIA represents approximately 20% of your portfolio, resulting in roughly 1 percentage point of portfolio impact.
>
> The movement has crossed your configured attention threshold.

---

# 10. Rapid Deterioration

The simulator generates:

```text
NVDA -4%
NVDA -5%
NVDA -7%
NVDA -10%
```

The system must detect:

- large movement
- movement velocity
- repeated deterioration
- portfolio exposure

Severity transitions:

```text
NORMAL
   ↓
WATCHING
   ↓
WARNING
   ↓
HIGH
   ↓
CRITICAL
```

The system must NOT send a notification for every price event.

Instead:

```text
WARNING
→ notification

subsequent worsening
→ update internal state

CRITICAL
→ escalate
```

This prevents notification spam.

---

# 11. News Event

The simulator or news adapter introduces:

> "US announces new semiconductor export restrictions."

The system sends the article/headline to the AI analysis layer.

The AI should identify:

```json
{
  "entities": [
    "NVIDIA",
    "AMD",
    "TSMC"
  ],
  "sectors": [
    "Semiconductors"
  ],
  "sentiment": "negative",
  "impact": "high",
  "confidence": 0.91,
  "reason": "The announcement may restrict semiconductor exports and affect companies with exposure to the affected markets."
}
```

The portfolio engine then checks:

```text
NVDA = 20%
AMD = 5%

Total semiconductor exposure = 25%
```

The system concludes:

```text
Portfolio relevance = HIGH
```

The agent sends:

> Important Portfolio Event
>
> New semiconductor export restrictions may materially affect companies in your portfolio.
>
> Your portfolio has approximately 25% exposure to NVIDIA and AMD.
>
> Estimated relevance: HIGH
>
> Confidence: 91%

---

# 12. Important Product Rule

The LLM must NOT invent financial numbers.

The following must be deterministic:

- prices
- quantities
- portfolio values
- portfolio weights
- percentage changes
- portfolio impact
- thresholds
- severity thresholds
- notification cooldowns
- escalation timers

The LLM may perform:

- news interpretation
- entity extraction
- sector identification
- qualitative impact assessment
- explanation generation
- natural language responses

Architecture:

```text
                  EVENT
                    ↓
          Deterministic Analysis
                    ↓
              Portfolio Data
                    ↓
               LLM Analysis
                    ↓
          Deterministic Severity
                    ↓
              Agent Decision
```

---

# 13. Caspian Integration

Caspian is the communication layer.

The application must NOT implement separate communication logic for every channel.

Use Caspian's unified handler.

Caspian currently provides a shared `on_message` handler and `message.reply()` abstraction across channels.

Primary hackathon channels:

1. Email
2. Telegram

Optional:

3. Discord

Potential future channels:

- WhatsApp
- SMS
- phone
- Slack

The implementation must query Caspian's live channel availability rather than hardcoding unsupported channels.

Caspian documents `/v1/channels` as the mechanism for discovering currently available channels.

---

# 14. Communication Escalation

Communication should depend on severity and acknowledgement.

Example:

```text
INFO
↓
Dashboard only

LOW
↓
No external notification

WARNING
↓
Email

HIGH
↓
Email + Telegram

CRITICAL
↓
Email
↓
wait for acknowledgement
↓
Telegram
↓
wait
↓
optional additional channel
```

The system must not immediately spam every channel.

---

# 15. Acknowledgement System

The user must be able to acknowledge an alert.

Example:

User receives Telegram message:

> CRITICAL: NVIDIA has fallen 12.4%. Your portfolio has 20% NVIDIA exposure.

User replies:

> I've seen it.

Caspian receives the inbound message.

The agent identifies the active alert.

State:

```text
CRITICAL
   ↓
ACKNOWLEDGED
```

No further escalation should occur.

This is a core feature.

---

# 16. Alert State Machine

Implement an explicit state machine.

States:

```text
NORMAL
WATCHING
WARNING
HIGH
CRITICAL
ACKNOWLEDGED
RESOLVED
```

Example:

```text
NORMAL
  |
  | material event
  v
WATCHING
  |
  | severity threshold exceeded
  v
WARNING
  |
  | significant deterioration
  v
HIGH
  |
  | critical threshold
  v
CRITICAL
  |
  | user acknowledges
  v
ACKNOWLEDGED
  |
  | event ends
  v
RESOLVED
```

Do not implement this as scattered `if` statements.

Create a centralized state transition mechanism.

---

# 17. Notification State Machine

Each notification should have its own state.

```text
PENDING
  ↓
SENT
  ↓
DELIVERED
  ↓
ACKNOWLEDGED
```

Failure:

```text
SENT
 ↓
FAILED
 ↓
RETRY
```

Escalation:

```text
EMAIL_SENT
    ↓
NO_ACK
    ↓
TELEGRAM_SENT
    ↓
NO_ACK
    ↓
NEXT_CHANNEL
```

---

# 18. Notification Deduplication

The same underlying event must not generate repeated alerts.

Every event must have:

```text
event_id
```

Every alert must reference:

```text
event_id
```

Use idempotent processing.

If:

```text
event_123
```

is processed twice, it must not generate two identical notifications.

---

# 19. Alert Cooldown

Implement notification suppression.

Example:

```text
NVDA -3%
→ no alert

NVDA -5%
→ WARNING alert

NVDA -5.5%
→ suppressed

NVDA -6%
→ suppressed

NVDA -9%
→ severity changed
→ escalation
```

The important trigger is not simply every movement.

It is:

> **material state transition**

---

# 20. Attention Budget

Implement an optional attention-management layer.

The system should prefer:

```text
5 small related events
        ↓
1 summarized notification
```

instead of:

```text
event 1 → notification
event 2 → notification
event 3 → notification
event 4 → notification
event 5 → notification
```

This is one of the core product differentiators.

---

# 21. Technology Stack

## Backend

Use:

**Python 3.12+**

Framework:

**FastAPI**

Reason:

- excellent API development
- natural fit for AI/ML engineer
- async support
- type validation
- easy integration with Caspian
- easy integration with financial Python libraries

---

## Agent Layer

Recommended:

**LangGraph**

Use it for:

- agent state
- structured workflows
- conditional transitions
- human-in-the-loop
- persistent state concepts

Do NOT build a complicated multi-agent architecture.

One primary Sentinel Agent is sufficient.

Optional internal components:

```text
News Analyst
Portfolio Impact Analyzer
Notification Planner
```

These can be Python modules/functions rather than separate agents.

---

## LLM

Create an abstraction:

```python
class LLMProvider:
    async def analyze_news(...)
    async def explain_event(...)
    async def respond_to_user(...)
```

The provider must be replaceable.

Support whichever free/hackathon-provided model is available.

The system should not depend structurally on a specific model.

Use structured JSON output.

---

## Market Data

Create:

```text
MarketDataProvider
```

Implement:

```text
SimulationMarketProvider
```

and optionally:

```text
YahooFinanceProvider
FinnhubProvider
AlphaVantageProvider
```

The simulation provider is mandatory.

Real providers are optional.

---

## News

Create:

```text
NewsProvider
```

Implement:

```text
SimulationNewsProvider
```

and optionally:

```text
FinnhubNewsProvider
GNewsProvider
NewsAPIProvider
```

The simulation provider is mandatory.

---

## Database

Use:

**PostgreSQL**

Recommended free provider:

**Supabase**

Database responsibilities:

- users
- portfolios
- holdings
- events
- news events
- alerts
- notifications
- agent state
- user preferences

---

## Redis

Redis is optional.

Use Redis only for:

- short-lived state
- cooldowns
- rate limiting
- queueing

Do not make Redis mandatory for the MVP.

PostgreSQL should remain the source of truth.

---

## Frontend

Use:

**Next.js + TypeScript**

Styling:

**Tailwind CSS**

Charts:

**Recharts**

The frontend is primarily an observability dashboard, not the main product interface.

---

# 22. High-Level Architecture

```text
                         ┌─────────────────────┐
                         │   Next.js Dashboard │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │       Backend       │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       Portfolio Service      Event Engine          Agent Layer
              │                     │                     │
              │                     │                     │
              ▼                     ▼                     ▼
         PostgreSQL            Event Bus             LLM
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                         ▼                     ▼
                 Market Events            News Events
                         │                     │
                         └──────────┬──────────┘
                                    ▼
                           Impact Analysis
                                    │
                                    ▼
                           Severity Engine
                                    │
                                    ▼
                         Notification Planner
                                    │
                                    ▼
                              Caspian SDK
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
                  Email         Telegram         Discord
```

---

# 23. Event-Driven Architecture

Every incoming market/news event should be converted to a canonical event.

Example:

```json
{
  "event_id": "evt_001",
  "event_type": "PRICE_MOVEMENT",
  "source": "simulation",
  "symbol": "NVDA",
  "payload": {
    "price": 108.42,
    "previous_price": 120.10,
    "change_percent": -9.72,
    "volume_ratio": 3.8
  },
  "occurred_at": "2026-08-08T10:30:00Z"
}
```

News:

```json
{
  "event_id": "news_001",
  "event_type": "NEWS",
  "source": "simulation",
  "payload": {
    "headline": "New semiconductor export restrictions announced",
    "summary": "...",
    "source_name": "Demo News Feed"
  },
  "occurred_at": "2026-08-08T10:32:00Z"
}
```

---

# 24. Event Processing Pipeline

Implement:

```text
1. Receive event
2. Validate event
3. Persist event
4. Deduplicate
5. Determine affected symbols/sectors
6. Load relevant portfolios
7. Calculate deterministic portfolio impact
8. Run AI analysis if necessary
9. Calculate severity
10. Determine state transition
11. Decide whether notification is required
12. Determine communication channel
13. Send via Caspian
14. Persist notification
15. Wait for acknowledgement/escalation
```

---

# 25. Market Event Processing

For price events calculate:

```text
price_change_percent
position_value
portfolio_weight
portfolio_contribution
movement_velocity
```

Example:

```text
NVDA:
portfolio weight = 0.20
price change = -0.10

portfolio contribution:
0.20 × -0.10 = -0.02

≈ -2% portfolio contribution
```

The calculation must happen in deterministic backend code.

---

# 26. Velocity Detection

A rapid movement should have greater severity than a slow movement.

Example:

```text
-5% over 6 hours
```

is different from:

```text
-5% over 3 minutes
```

Track:

```text
percentage change
time interval
rate of change
```

Use a simple normalized velocity metric for MVP.

Do not attempt sophisticated quantitative finance models.

---

# 27. Portfolio Exposure

For every holding:

```text
position_value =
quantity × current_price
```

Then:

```text
portfolio_weight =
position_value / total_portfolio_value
```

Maintain:

```text
symbol
quantity
average_price
current_price
position_value
weight
```

---

# 28. News Analysis Pipeline

```text
Headline
   ↓
LLM
   ↓
Entity extraction
   ↓
Sector classification
   ↓
Sentiment
   ↓
Impact
   ↓
Confidence
```

Structured output:

```json
{
  "entities": ["NVIDIA", "AMD"],
  "sectors": ["Semiconductors"],
  "sentiment": "negative",
  "impact": "high",
  "confidence": 0.91,
  "reasoning_summary": "..."
}
```

---

# 29. News-to-Portfolio Matching

Use deterministic matching after LLM extraction.

Example:

```text
News entities:
NVIDIA
AMD
TSMC

Portfolio:
NVIDIA
AAPL
MSFT

Intersection:
NVIDIA
```

Then calculate:

```text
direct exposure
sector exposure
portfolio relevance
```

For MVP, direct ticker/entity matching is sufficient.

Optional enhancement:

Sector matching.

Example:

```text
News:
Semiconductor export restrictions

Portfolio:
NVDA
AMD

Sector mapping:
NVDA → Semiconductors
AMD → Semiconductors
```

---

# 30. Severity Engine

Severity should be deterministic.

Inputs:

```text
price movement
movement velocity
portfolio exposure
news impact
AI confidence
event novelty
```

Produce:

```text
score: 0-100
level:
INFO
LOW
WARNING
HIGH
CRITICAL
```

Example:

```text
0-20    INFO
21-40   LOW
41-60   WARNING
61-80   HIGH
81-100  CRITICAL
```

These thresholds should be configurable.

---

# 31. Severity Scoring Example

Example:

```text
Price movement:       30
Velocity:             15
Portfolio exposure:   25
News impact:          20
Confidence:           10

Total:                100
```

This is a demo heuristic, not a financial risk model.

The UI should label it:

> Sentinel Severity Score

not:

> Statistically optimal financial risk score.

---

# 32. Agent Responsibilities

The Sentinel Agent should:

1. Understand incoming user messages.
2. Explain alerts.
3. Explain why an event matters.
4. Retrieve portfolio context.
5. Retrieve active alerts.
6. Acknowledge alerts.
7. Answer portfolio questions.
8. Coordinate notification actions.
9. Respect communication policies.

Example user message:

> Why did you alert me?

Agent retrieves:

```text
alert
portfolio
news
analysis
```

and responds:

> I alerted you because NVIDIA represents 20% of your portfolio and the stock has fallen 10.2%. A related semiconductor export announcement was also detected.

---

# 33. Agent Tools

Expose explicit tools:

```text
get_portfolio()
get_holding(symbol)
get_active_alerts()
get_alert(alert_id)
get_recent_market_events()
get_news_event(event_id)
acknowledge_alert(alert_id)
get_notification_history()
```

Potential action:

```text
send_notification()
```

However, sending should ideally go through a deterministic Notification Service rather than allowing the LLM to directly send arbitrary messages.

---

# 34. Agent Safety

The agent must NEVER:

- execute stock trades
- recommend buying/selling as a direct automated action
- fabricate market data
- fabricate portfolio values
- claim certainty about future stock prices
- invent news
- bypass user acknowledgement
- expose API keys

The product is:

**portfolio monitoring and decision support**

not:

**automated investment execution.**

---

# 35. Database Schema

## users

```text
id
email
name
created_at
```

## portfolios

```text
id
user_id
name
base_currency
created_at
updated_at
```

## holdings

```text
id
portfolio_id
symbol
quantity
average_price
created_at
updated_at
```

## market_events

```text
id
event_id
source
event_type
symbol
payload
occurred_at
processed_at
created_at
```

## news_events

```text
id
event_id
headline
summary
source
url
ai_analysis
created_at
```

## alerts

```text
id
alert_id
user_id
portfolio_id
event_id
severity_score
severity_level
title
reason
status
acknowledged_at
created_at
updated_at
```

## notifications

```text
id
alert_id
channel
status
provider_message_id
sent_at
acknowledged_at
failure_reason
retry_count
```

## agent_state

```text
id
user_id
conversation_id
state
context
updated_at
```

## notification_preferences

```text
id
user_id
warning_channel
high_channel
critical_channel
cooldown_seconds
escalation_enabled
```

---

# 36. Backend API

Implement:

```text
GET /health
```

Health check.

```text
GET /api/portfolio
```

Return portfolio.

```text
POST /api/portfolio
```

Create portfolio.

```text
POST /api/portfolio/holdings
```

Add holding.

```text
DELETE /api/portfolio/holdings/{id}
```

Remove holding.

```text
GET /api/events
```

Recent events.

```text
GET /api/alerts
```

Active/recent alerts.

```text
GET /api/alerts/{id}
```

Alert details.

```text
POST /api/alerts/{id}/acknowledge
```

Acknowledge alert.

```text
GET /api/notifications
```

Notification history.

---

# 37. Simulation API

Mandatory.

```text
GET /api/simulation/scenarios
```

Return available scenarios.

```text
POST /api/simulation/start/{scenario}
```

Start scenario.

```text
POST /api/simulation/stop
```

Stop simulation.

```text
POST /api/simulation/reset
```

Reset state.

```text
POST /api/simulation/events
```

Inject a custom event.

Example:

```json
{
  "type": "PRICE_MOVEMENT",
  "symbol": "NVDA",
  "change_percent": -8
}
```

---

# 38. Required Simulation Scenarios

Implement at least four.

## Scenario 1: Normal Market

Purpose:

Demonstrate that the agent does NOT overreact.

Events:

```text
NVDA +0.4%
AAPL -0.3%
MSFT +0.2%
```

Expected:

```text
No notification
```

---

## Scenario 2: Rapid Stock Crash

```text
NVDA -2%
NVDA -4%
NVDA -7%
NVDA -11%
```

Expected:

```text
NORMAL
→ WATCHING
→ WARNING
→ HIGH
→ CRITICAL
```

Expected communication:

```text
Email
→ escalation
→ Telegram
```

---

## Scenario 3: Breaking News

News:

> New semiconductor export restrictions announced.

Portfolio:

```text
NVDA 20%
AMD 5%
```

Expected:

```text
News detected
→ AI analysis
→ semiconductor exposure detected
→ high portfolio relevance
→ notification
```

---

## Scenario 4: Alert Acknowledgement

Start Scenario 2.

Send critical notification.

User replies:

> I've seen it.

Expected:

```text
CRITICAL
→ ACKNOWLEDGED
```

No further escalation.

---

# 39. Optional Advanced Scenario

## Sector Shock

News:

> Federal regulators announce major restrictions affecting pharmaceutical companies.

Portfolio:

```text
LLY
JNJ
PFE
```

Agent identifies sector exposure.

Expected:

```text
News
→ Pharmaceutical sector
→ portfolio sector exposure
→ high relevance
→ alert
```

---

# 40. Frontend Pages

## Dashboard

Primary page.

Sections:

### Portfolio Summary

```text
Portfolio Value
Today's P/L
Total P/L
Risk Status
```

### Holdings

Table:

```text
Symbol
Price
Change
Quantity
Value
Weight
Impact
```

### Active Alerts

Cards:

```text
CRITICAL
NVDA
-11.2%

Portfolio Impact
-2.2%

Reason
Rapid price deterioration + relevant semiconductor news
```

### Event Timeline

```text
14:30 NVDA -2%
14:31 NVDA -4%
14:32 News detected
14:32 Impact HIGH
14:33 Email sent
14:34 NVDA -9%
14:34 Severity CRITICAL
14:34 Telegram escalation
```

---

# 41. Alert Detail View

Display:

```text
Alert Severity
Event
Affected Holdings
Portfolio Exposure
Market Movement
News
AI Analysis
Notification History
Current State
```

Example:

```text
CRITICAL

NVIDIA

Price:
$108.42

Change:
-9.72%

Portfolio Exposure:
20%

Estimated Portfolio Contribution:
-1.94%

Related News:
Semiconductor export restrictions

AI Confidence:
91%

State:
CRITICAL

Notifications:
✓ Email
✓ Telegram
```

---

# 42. Simulation Control Panel

This is extremely important for the demo.

Add:

```text
Simulation Controls

[ Normal Market ]

[ NVDA Crash ]

[ Semiconductor Crisis ]

[ Fed Shock ]

[ Custom Event ]
```

When a scenario runs:

```text
Simulation:
SEMICONDUCTOR CRISIS

Progress:
████████░░ 80%

Current event:
NVDA -9%

Agent status:
CRITICAL
```

The dashboard should update live.

---

# 43. Agent Activity Panel

Show:

```text
AGENT ACTIVITY

14:32:10
Detected price movement

14:32:11
Portfolio exposure calculated

14:32:12
Related news detected

14:32:13
AI impact analysis completed

14:32:13
Severity: HIGH

14:32:14
Email notification sent

14:34:02
Severity increased: CRITICAL

14:34:03
Escalating via Telegram
```

This is excellent for the hackathon demo because judges can see the agent's internal workflow.

Do not expose hidden chain-of-thought.

Display structured system events and concise decision reasons only.

---

# 44. Communication Timeline

Display:

```text
ALERT ESCALATION

✓ Email
  Sent 14:32

✓ Telegram
  Sent 14:34

✓ User acknowledged
  14:35

Escalation stopped
```

This directly demonstrates Caspian.

---

# 45. UI Design

Visual style:

- dark financial terminal aesthetic
- clean typography
- minimal gradients
- high information density
- green/red market indicators
- severity indicators
- live event animations
- responsive design

Do NOT make the UI look like a generic SaaS landing page.

The product should visually communicate:

```text
financial monitoring
+
AI agent
+
real-time events
```

---

# 46. Caspian Architecture

Create:

```text
app/caspian/
    client.py
    handlers.py
    channels.py
    notification_adapter.py
```

The Caspian client should be initialized once.

Use a shared handler.

Conceptually:

```python
@client.on_message
def handle_message(message):
    return agent.handle_message(message)
```

The business logic must not depend directly on Telegram/Email/Discord.

Use:

```text
Caspian
   ↓
CommunicationAdapter
   ↓
NotificationService
```

---

# 47. Caspian Channel Discovery

On startup:

```text
GET /v1/channels
```

The backend should detect available channels.

Expose them to the frontend.

Example:

```json
{
  "email": true,
  "telegram": true,
  "discord": true
}
```

Only display enabled channels.

Do not hardcode unsupported channels.

---

# 48. Environment Variables

Create:

```text
CASPIAN_API_KEY=
CASPIAN_BASE_URL=https://api.trycaspianai.com

DATABASE_URL=

LLM_API_KEY=
LLM_MODEL=

NEWS_API_KEY=
MARKET_API_KEY=

REDIS_URL=

NEXT_PUBLIC_API_URL=
```

All secrets must remain server-side.

Never expose:

```text
CASPIAN_API_KEY
LLM_API_KEY
NEWS_API_KEY
MARKET_API_KEY
```

to the browser.

---

# 49. Repository Structure

Use a monorepo.

```text
sentinel-ai/

├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── portfolio.py
│   │   │   ├── alerts.py
│   │   │   ├── events.py
│   │   │   ├── simulation.py
│   │   │   └── notifications.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── logging.py
│   │   │
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── portfolio.py
│   │   │   ├── holding.py
│   │   │   ├── event.py
│   │   │   ├── alert.py
│   │   │   └── notification.py
│   │   │
│   │   ├── services/
│   │   │   ├── portfolio_service.py
│   │   │   ├── event_service.py
│   │   │   ├── impact_service.py
│   │   │   ├── severity_service.py
│   │   │   ├── alert_service.py
│   │   │   └── notification_service.py
│   │   │
│   │   ├── agent/
│   │   │   ├── graph.py
│   │   │   ├── state.py
│   │   │   ├── tools.py
│   │   │   └── prompts.py
│   │   │
│   │   ├── providers/
│   │   │   ├── market/
│   │   │   │   ├── base.py
│   │   │   │   ├── simulator.py
│   │   │   │   └── yahoo.py
│   │   │   │
│   │   │   ├── news/
│   │   │   │   ├── base.py
│   │   │   │   ├── simulator.py
│   │   │   │   └── provider.py
│   │   │   │
│   │   │   └── llm/
│   │   │       ├── base.py
│   │   │       └── provider.py
│   │   │
│   │   ├── caspian/
│   │   │   ├── client.py
│   │   │   ├── handlers.py
│   │   │   └── adapter.py
│   │   │
│   │   ├── simulation/
│   │   │   ├── scenarios/
│   │   │   ├── engine.py
│   │   │   └── events.py
│   │   │
│   │   └── tests/
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── hooks/
│   ├── types/
│   └── package.json
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── demo.md
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

# 50. Backend Module Responsibilities

## Event Service

Responsibilities:

- ingest events
- validate events
- persist events
- deduplicate events
- dispatch events

---

## Portfolio Service

Responsibilities:

- retrieve holdings
- calculate portfolio value
- calculate exposure
- calculate portfolio impact

---

## Impact Service

Responsibilities:

- determine affected holdings
- combine market and news signals
- calculate relevance

---

## Severity Service

Responsibilities:

- calculate severity score
- determine severity level
- determine state transitions

---

## Alert Service

Responsibilities:

- create alerts
- update alerts
- acknowledge alerts
- resolve alerts
- suppress duplicate alerts

---

## Notification Service

Responsibilities:

- determine channel
- send through Caspian
- retry failures
- track delivery
- escalate
- stop escalation

---

# 51. AI/ML Engineer Responsibilities

The AI/ML engineer owns:

### 1. News understanding

Build structured news analysis.

### 2. Entity extraction

Identify:

```text
companies
tickers
sectors
industries
events
```

### 3. Impact classification

Output:

```text
positive
neutral
negative

impact:
low
medium
high

confidence:
0-1
```

### 4. Agent workflow

Build the LangGraph agent.

### 5. Prompt engineering

Create:

```text
news_analysis_prompt
alert_explanation_prompt
user_assistant_prompt
```

### 6. Evaluation

Create a small set of known news scenarios and expected outputs.

---

# 52. Systems Engineer Responsibilities

The systems engineer owns:

### 1. Event architecture

- event schemas
- event ingestion
- event processing
- idempotency
- event persistence

### 2. Portfolio engine

- position calculations
- exposure
- impact

### 3. Severity engine

- deterministic scoring
- state transitions

### 4. Notification engine

- notification routing
- escalation
- retries
- cooldowns

### 5. Caspian integration

- channels
- inbound messages
- outbound notifications
- acknowledgement

### 6. Simulation framework

- event generator
- scenarios
- replay
- deterministic execution

### 7. Backend APIs

FastAPI endpoints.

---

# 53. Shared Responsibilities

Both engineers should collaborate on:

- overall architecture
- database schema
- agent integration
- frontend
- testing
- demo
- deployment
- README
- presentation

---

# 54. Development Phases

## Phase 1: Skeleton

Build:

```text
FastAPI
PostgreSQL
Next.js
Caspian
```

Confirm:

```text
FastAPI → Caspian → Email
```

before building anything complicated.

---

# 55. Phase 2: Portfolio

Implement:

```text
create portfolio
add holdings
calculate value
calculate weights
```

Dashboard displays holdings.

---

# 56. Phase 3: Event Engine

Implement:

```text
Event
→ persistence
→ processing
→ portfolio impact
```

Create simulator.

Test:

```text
NVDA -5%
```

---

# 57. Phase 4: Severity Engine

Implement:

```text
NORMAL
WATCHING
WARNING
HIGH
CRITICAL
```

Test state transitions.

---

# 58. Phase 5: Notifications

Implement:

```text
WARNING
→ email

HIGH
→ email + Telegram

CRITICAL
→ escalation
```

Use Caspian.

---

# 59. Phase 6: News AI

Implement:

```text
headline
→ LLM
→ entities
→ sector
→ sentiment
→ impact
→ confidence
```

Connect to portfolio.

---

# 60. Phase 7: Agent

Implement user interaction:

```text
Why did you alert me?

What happened to NVDA?

What is my exposure?

What alerts are active?

I've seen this.
```

---

# 61. Phase 8: Polish

Add:

- live dashboard
- timeline
- agent activity
- simulation controls
- notification history
- animations
- clean UI

---

# 62. Testing Strategy

## Unit Tests

Test:

```text
portfolio calculations
severity scoring
state transitions
deduplication
cooldowns
notification routing
```

---

## Integration Tests

Test:

```text
simulation
→ event ingestion
→ portfolio impact
→ severity
→ alert
→ notification
```

---

## Agent Tests

Create fixtures:

```text
news headline
expected entities
expected sentiment
expected impact
```

Do not require exact wording.

Validate structured output.

---

# 63. Deterministic Demo Mode

The entire demo must run from:

```text
POST /api/simulation/start/semiconductor-crisis
```

It must produce the same sequence every time.

Example:

```text
t=0s
NVDA -2%

t=5s
NVDA -5%

t=10s
News arrives

t=15s
NVDA -8%

t=20s
NVDA -12%

t=25s
CRITICAL

t=30s
Escalation
```

This guarantees a reliable presentation.

---

# 64. Demo Script

The demo should take approximately 3 minutes.

## Step 1

Show portfolio.

```text
$100,000

NVDA 20%
AMD   5%
AAPL 15%
MSFT 12%
```

Explain:

> SentinelAI is monitoring the user's portfolio and external events.

---

## Step 2

Start:

```text
Semiconductor Crisis
```

Dashboard shows:

```text
NVDA -2%
```

No notification.

Explain:

> We deliberately do not alert the user for every small movement.

---

## Step 3

NVDA drops further.

```text
NVDA -5%
```

Severity:

```text
WARNING
```

Email appears.

---

## Step 4

Inject:

> New semiconductor export restrictions announced.

AI analyzes:

```text
NVIDIA
AMD
Semiconductor sector
Negative
High impact
91% confidence
```

Agent recognizes:

```text
25% portfolio exposure
```

Alert appears.

---

## Step 5

NVDA crashes further.

```text
-12%
```

Severity:

```text
CRITICAL
```

Agent escalates through Caspian.

Email → Telegram.

---

## Step 6

User replies:

> I've seen it.

Agent recognizes acknowledgement.

```text
CRITICAL
→ ACKNOWLEDGED
```

Escalation stops.

---

# 65. The Hackathon "Wow" Moment

The presentation should emphasize this:

> The agent did not simply detect a stock crash.

It understood:

```text
What happened?
      ↓
Why did it happen?
      ↓
Does it affect this user?
      ↓
How much exposure does the user have?
      ↓
How severe is it?
      ↓
Does the user need to be interrupted?
      ↓
Which channel should be used?
      ↓
Has the user acknowledged it?
      ↓
Should escalation continue?
```

That is the agent.

---

# 66. What NOT to Build

Do NOT build:

- automated trading
- brokerage integration
- real-money transactions
- complex quantitative forecasting
- stock price prediction model
- Kubernetes
- Kafka
- microservices
- vector database unless actually required
- custom ML model for stock prediction
- elaborate authentication system
- production billing
- complicated RAG infrastructure

The hackathon is about:

**agentic portfolio monitoring + Caspian communication.**

Do not accidentally build Robinhood.

---

# 67. Optional Advanced Features

Only implement after the core workflow works.

## Personalized Notification Policy

Allow:

```text
Notify me for:
- >5% movement
- high portfolio impact
- major news
```

---

## Quiet Hours

Example:

```text
Do not notify between:
11 PM - 7 AM
```

unless severity is CRITICAL.

---

## Multi-Stock Correlation

If:

```text
NVDA -5%
AMD -6%
TSM -4%
```

and all belong to the same sector:

Generate one consolidated alert.

Instead of three messages:

> Semiconductor sector is experiencing a significant coordinated decline. Your portfolio has 28% semiconductor exposure.

---

## Alert Summary

Instead of:

```text
5 separate events
```

generate:

```text
Portfolio Alert Summary

3 holdings affected
Semiconductor sector
Estimated portfolio impact: -2.7%
Severity: HIGH
```

---

# 68. Production Architecture Future

The MVP should be capable of evolving into:

```text
                Market Streams
                     │
                     ▼
              Event Ingestion
                     │
                     ▼
                Event Bus
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    Portfolio     News         Risk
    Processor    Processor    Processor
        │            │            │
        └────────────┼────────────┘
                     ▼
               Agent Runtime
                     │
                     ▼
             Durable Workflow
                     │
                     ▼
              Notification
                 Policy
                     │
                     ▼
                  Caspian
```

But this is future architecture.

Do not implement it now.

---

# 69. Observability

Every important operation should emit structured logs:

```text
event_received
event_processed
portfolio_impact_calculated
news_analysis_completed
severity_changed
alert_created
notification_sent
notification_failed
notification_escalated
alert_acknowledged
alert_resolved
```

Each should include:

```text
event_id
alert_id
user_id
timestamp
```

This makes debugging dramatically easier.

---

# 70. Correlation IDs

Use:

```text
event_id
alert_id
notification_id
conversation_id
```

Example:

```text
event_123
   ↓
alert_456
   ↓
notification_789
   ↓
conversation_abc
```

This allows the entire lifecycle of an event to be traced.

---

# 71. Reliability Requirements

The backend must tolerate:

- duplicate events
- delayed events
- failed LLM requests
- failed notifications
- unavailable market APIs
- unavailable news APIs
- Caspian failures
- malformed LLM responses

For LLM failures:

```text
LLM unavailable
      ↓
event still persisted
      ↓
fallback:
"News analysis temporarily unavailable"
```

The entire system must not crash because one LLM call failed.

---

# 72. LLM Output Validation

Never directly trust raw model output.

Use structured schema:

```python
class NewsAnalysis(BaseModel):
    entities: list[str]
    sectors: list[str]
    sentiment: Literal["positive", "neutral", "negative"]
    impact: Literal["low", "medium", "high"]
    confidence: float
    reason: str
```

Validate the model output.

If invalid:

```text
retry
```

If still invalid:

```text
mark analysis unavailable
```

---

# 73. Security Requirements

Never commit:

```text
.env
API keys
Caspian tokens
Telegram tokens
LLM keys
database credentials
```

Provide:

```text
.env.example
```

Use:

```text
.env
```

locally.

---

# 74. API Error Handling

All API responses should follow a consistent format.

Example:

```json
{
  "success": false,
  "error": {
    "code": "PORTFOLIO_NOT_FOUND",
    "message": "Portfolio not found"
  }
}
```

---

# 75. Code Quality

Use:

- Python type hints
- Pydantic models
- async FastAPI
- clear service boundaries
- dependency injection where useful
- structured logging
- tests for critical financial calculations

Avoid:

- giant `main.py`
- business logic inside API routes
- LLM calls directly inside database models
- hardcoded thresholds
- hardcoded notification providers
- duplicated channel-specific logic

---

# 76. Configuration

Thresholds should be configurable:

```text
WARNING_PRICE_CHANGE=5
HIGH_PRICE_CHANGE=8
CRITICAL_PRICE_CHANGE=12

WARNING_PORTFOLIO_IMPACT=1
HIGH_PORTFOLIO_IMPACT=2
CRITICAL_PORTFOLIO_IMPACT=4

ALERT_COOLDOWN_SECONDS=300
ESCALATION_DELAY_SECONDS=120
```

For the hackathon, values can be tuned to make the simulation visually compelling.

---

# 77. MVP Definition

The MVP is complete when all of these work:

```text
✓ User portfolio exists
✓ Holdings are stored
✓ Portfolio value is calculated
✓ Simulator generates price events
✓ Events are persisted
✓ Events are deduplicated
✓ Portfolio impact is calculated
✓ Severity is calculated
✓ Alerts are generated
✓ Email notification works through Caspian
✓ Telegram notification works through Caspian
✓ News scenario works
✓ LLM analyzes news
✓ News is matched to portfolio
✓ Critical alerts escalate
✓ User can acknowledge alert
✓ Escalation stops
✓ Dashboard shows events
✓ Dashboard shows alert state
✓ Simulation can be replayed
```

Everything else is secondary.

---

# 78. Definition of Done

The project should be considered hackathon-ready when:

### Technical

- backend starts with one command
- frontend starts with one command
- database initializes automatically
- simulation works deterministically
- Caspian connection works
- at least two communication channels work
- critical event workflow works end-to-end
- no API secrets are committed

### Product

A judge can understand the product within 30 seconds.

### Demo

The entire scenario can be reproduced in under 3 minutes.

### Reliability

The demo does not depend on live market conditions.

---

# 79. Recommended Final Stack

Use exactly this unless a technical blocker appears:

```text
Frontend
Next.js
TypeScript
Tailwind CSS
Recharts

Backend
Python
FastAPI
Pydantic
SQLAlchemy

Agent
LangGraph
LLM API

Database
PostgreSQL
Supabase

Cache / optional queue
Redis

Communication
Caspian SDK

Market Data
yfinance / Finnhub adapter

News
Finnhub / GNews adapter

Simulation
Custom Python event simulator

Deployment
Vercel
+
Render/Railway/Cloud Run/free-tier equivalent

Testing
pytest
httpx

Observability
structured Python logging
```

---

# 80. Most Important Architectural Principle

The entire project must preserve this abstraction:

```text
              ┌──────────────────┐
              │  REAL PROVIDERS   │
              └────────┬─────────┘
                       │
                       ▼
                ┌─────────────┐
                │ Event Schema│
                └──────┬──────┘
                       │
                       ▼
              ┌─────────────────┐
              │  EVENT ENGINE   │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ IMPACT ANALYSIS │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ SEVERITY ENGINE │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  AGENT / POLICY │
              └────────┬────────┘
                       │
                       ▼
                 ┌───────────┐
                 │  CASPIAN  │
                 └───────────┘
```

The simulator plugs into exactly where the real providers plug in:

```text
              ┌──────────────────┐
              │   SIMULATOR      │
              └────────┬─────────┘
                       │
                       ▼
                ┌─────────────┐
                │ Event Schema│
                └─────────────┘
```

Therefore the hackathon implementation is not a toy architecture.

It is a production-shaped architecture with a deterministic data source for demonstration.

---

# 81. Antigravity Implementation Instructions

Build the project incrementally.

Do NOT generate the entire application in one pass.

Implement in this order:

```text
1. Repository structure
2. FastAPI application
3. PostgreSQL models
4. Portfolio CRUD
5. Event schema
6. Event persistence
7. Simulation engine
8. Portfolio impact calculation
9. Severity engine
10. Alert state machine
11. Caspian integration
12. Email notification
13. Telegram notification
14. Notification escalation
15. News provider
16. LLM analysis
17. News-to-portfolio matching
18. LangGraph agent
19. Agent/Caspian inbound messages
20. Next.js dashboard
21. Live event updates
22. Simulation UI
23. Alert timeline
24. Testing
25. Deployment
26. Demo hardening
```

After every major phase, run tests and verify the existing functionality before continuing.

Do not rewrite working modules unnecessarily.

Do not introduce a new dependency unless it solves a concrete problem.

Do not introduce microservices.

Do not introduce Kafka.

Do not introduce Kubernetes.

Do not introduce a vector database.

Do not introduce a second backend language.

Do not build automated trading.

The goal is a reliable, polished autonomous portfolio sentinel that demonstrates genuine agentic behavior and makes Caspian central to the product.

---

# 82. Final Product Definition

SentinelAI should ultimately demonstrate:

```text
                MARKET
                  │
                  ▼
              EVENT
                  │
                  ▼
           "Does this matter?"
                  │
                  ▼
        USER PORTFOLIO CONTEXT
                  │
                  ▼
          "How much does it matter?"
                  │
                  ▼
              SEVERITY
                  │
                  ▼
          "Does the user need
           to know right now?"
                  │
                  ▼
           COMMUNICATION PLAN
                  │
                  ▼
               CASPIAN
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
      Email    Telegram   Discord
                  │
                  ▼
            USER RESPONSE
                  │
                  ▼
          ACKNOWLEDGED?
           /           \
         YES            NO
          │              │
          ▼              ▼
       STOP          ESCALATE
                         │
                         ▼
                      CASPIAN
```

The product is not "AI predicts stocks."

The product is not "AI reads financial news."

The product is not "AI sends WhatsApp messages."

The product is:

> **An autonomous agent that continuously determines when a market event becomes important to a specific investor, explains why, and uses Caspian's communication infrastructure to reach that investor with the appropriate urgency.**

That is the core product and the core hackathon story.