# Dynamic-Delta-Hedged-Weekly-Short-Strangle-Trading-Engine
A fully automated, event-driven options trading engine designed to execute a **Dynamic Delta Hedged Weekly Short Strangle** strategy on NIFTY index options. This can be also implemented on other index and stocks.
# 📈 Dynamic Delta Hedged Weekly Short Strangle Trading Engine

A fully automated, event-driven options trading engine designed to execute a **Dynamic Delta Hedged Weekly Short Strangle** strategy on NIFTY index options.

Unlike conventional algorithmic trading bots that repeatedly poll broker APIs, this engine is designed around a **WebSocket-driven architecture**, allowing the strategy to receive live premium updates with minimal latency while continuously managing option positions based on real-time market conditions.

The primary objective behind the project was not only to automate a trading strategy but also to design a scalable trading engine whose architecture can later be integrated into a complete Order Management System (OMS).

---

# 🚀 Project Objective

The objective of this project is to build a professional trading engine capable of

- Executing a Delta Hedged Weekly Short Strangle automatically
- Monitoring option premiums in real time
- Managing complete order life cycles
- Performing automatic position adjustments
- Minimizing API requests using WebSockets
- Maintaining modularity for future scalability

The architecture has been developed with software engineering principles rather than writing a single procedural trading script.

---

# 🏗 System Architecture

```
                        Live Market
                            │
                            ▼
                  SmartAPI WebSocket
                            │
                            ▼
                 Live Premium Engine
                            │
                            ▼
                 Strategy Decision Layer
                            │
                            ▼
                  Delta Calculation Engine
                            │
                            ▼
                 Position Management Layer
                            │
                            ▼
                  SmartAPI Order Engine
                            │
                            ▼
                  Orderbook Management
                            │
                            ▼
                 Continuous Monitoring
```

Every component performs a single responsibility making the overall architecture modular, maintainable and scalable.

---

# ⚙ Strategy Overview

The trading engine executes a **Delta Hedged Weekly Short Strangle**.

## Initial Position

The engine automatically

- Calculates the ATM Strike
- Sells ATM Call Option
- Sells ATM Put Option
- Purchases hedge options using Delta based selection

The hedge options reduce tail risk while allowing the strategy to maintain market neutrality.

---

# 📊 Dynamic Position Adjustment

Unlike conventional short strangles that remain fixed until expiry, this engine continuously monitors option Greeks.

Whenever the Delta of an open short option exceeds the predefined threshold, the strategy

- Closes the tested option
- Exits the opposite short leg
- Recalculates the market
- Creates an entirely new Delta Hedged Short Strangle

This enables the engine to dynamically adapt to changing market conditions.

---

# 🧠 Core Engineering Philosophy

Instead of developing one large script containing all logic, the project separates different responsibilities into independent modules.

## Market Data Layer

Responsible only for receiving live premiums from SmartAPI WebSocket.

Advantages

- No continuous REST polling
- Lower latency
- Lower API usage
- Faster reaction time

---

## Strategy Layer

Responsible only for

- Strike Selection
- Delta Monitoring
- Entry Logic
- Exit Logic
- Rolling Logic

No broker-related functionality is mixed into this layer.

---

## Order Management Layer

Responsible only for

- Order Creation
- Order Execution
- Position Updates
- Order Status Management

Separating execution from strategy allows broker replacement without changing strategy logic.

---

## Risk Management Layer

Responsible for

- Delta Hedge Selection
- Continuous Position Monitoring
- Position Adjustment
- Automatic Position Exit

---

# 🔄 Internal Execution Workflow

```
Market Opens
      │
      ▼
Receive Live Spot Price
      │
      ▼
Calculate ATM Strike
      │
      ▼
Fetch Greeks
      │
      ▼
Select Hedge Options
      │
      ▼
Place Initial Orders
      │
      ▼
Receive Live Premiums
      │
      ▼
Monitor Delta Continuously
      │
      ▼
Delta Threshold Reached?
      │
   Yes ▼
Exit Current Position
      │
      ▼
Recalculate New ATM
      │
      ▼
Create Fresh Short Strangle
      │
      ▼
Repeat Until Expiry
      │
      ▼
Square Off Remaining Positions
```

---

# 🌐 Event Driven Architecture

One of the major engineering decisions behind this project was adopting an **event-driven architecture**.

Traditional trading bots repeatedly perform

```
Request LTP

↓

Wait

↓

Request Again

↓

Wait
```

This results in

- Higher API usage
- Slower execution
- Increased latency

Instead, this engine receives live premium updates directly through WebSockets.

```
Broker

↓

Live Tick

↓

WebSocket

↓

Strategy Engine

↓

Immediate Decision
```

Advantages

- Near real-time execution
- Lower latency
- Reduced API requests
- Better scalability

---

# 🧩 Modular Design

Every major responsibility has been isolated.

```
Market Data

↓

Strategy

↓

Risk Management

↓

Order Management

↓

Broker Integration
```

Advantages

- Easier debugging
- Cleaner codebase
- Better maintainability
- Easy broker replacement
- Easier strategy additions

---

# ⚡ Dynamic Delta Hedging

Instead of buying fixed-distance hedge options, this engine dynamically selects hedge legs using option Greeks.

Advantages

- Better capital efficiency
- Consistent hedge exposure
- Improved downside protection
- Adaptive risk management

---

# 📦 Order Life Cycle

Every position progresses through a complete life cycle.

```
Generated

↓

Validated

↓

Executed

↓

Monitored

↓

Adjusted

↓

Closed
```

Maintaining a proper order life cycle simplifies order tracking and future OMS integration.

---

# 💡 Advantages of the Engine

✅ Event Driven Architecture

✅ Live WebSocket Premium Monitoring

✅ Delta Based Position Management

✅ Automatic Position Rolling

✅ Dynamic Hedge Selection

✅ Modular Software Architecture

✅ Lower REST API Consumption

✅ Low Latency Execution

✅ Automated Risk Management

✅ Easily Extendable for Multi-Client OMS

---

# 🛠 Technologies Used

- Python
- Angel One SmartAPI
- SmartWebSocketV2
- Requests
- JSON
- Async Programming
- WebSockets
- Option Greeks
- PyOTP

---

# 📂 Project Structure

```
Delta Hedged Weekly Short Strangle
│
├── Strategy Engine
├── SmartAPI Integration
├── WebSocket Handler
├── Live Premium Engine
├── Delta Calculation Module
├── Hedge Selection Module
├── Order Management
├── Risk Management
└── Utility Functions
```


# ⚠ Disclaimer

This project has been developed solely for educational, research and software engineering purposes.

Trading in financial markets involves significant risk. The developer assumes no responsibility for any financial losses incurred through the use of this software.

