# 🔄 Trade Data Generator (AWS Lambda + CloudWatch)

This project is a serverless backend that generates **synthetic buy/sell trade data** in AWS Lambda using Python. The function runs **every 3 minutes**, triggered via **Amazon CloudWatch (EventBridge)**, and produces data with randomized mismatches to simulate reconciliation scenarios.

---

## 📌 Key Features

- ⚙️ **Scheduled Execution**: Runs every 3 minutes using a CloudWatch (EventBridge) rule.
- 🔁 **Random Trade Pair Generation**: Generates 15 unique trade pairs (30 records total), 30% with mismatches.
- 🧠 **Mismatches for Testing**: Controlled mismatches in fields like quantity, price, timestamp, and date.
- 💾 **SQLite Persistence**: Uses a local SQLite DB (`trade_ids.db`) to persist unique trade IDs across invocations.
- 📈 **Ticker-Based Prices**: Loads data from a `tickers.csv` file to simulate realistic stock pricing.
- ✅ **Serverless-Ready**: Built for deployment in AWS Lambda as a scheduled job (not API-based).
  
---

## 📁 Project Structure

trade-generator/
│
├── app.py # Main logic to generate and print trade data
├── tickers.csv # Source for ticker names and prices
├── trade_ids.db # SQLite file storing persistent trade_id counter
├── Dockerfile # For container-based Lambda deployment
├── requirements.txt # Python dependencies
└── README.md # Project documentation



---

## ⏰ CloudWatch Trigger Setup

The Lambda function is triggered every **3 minutes** using **Amazon EventBridge (CloudWatch Events)**:

1. **Rule Configuration**:
   - Schedule expression: `rate(3 minutes)`
   - Target: your Lambda function

2. **Permissions**:
   Ensure the Lambda function's role allows invocation from `events.amazonaws.com`.

---

## 🐍 Example Output (printed to logs)

```json
[
  {
    "trade_id": "tid00000021",
    "ticker": "AAPL",
    "broker_id": "BKR005",
    "contra_broker_id": "BKR011",
    "quantity": 250,
    "price": 154.00,
    "order_type": "BUY",
    "date": "2025-07-21",
    "trade_timestamp": "2025-07-21 10:33:00"
  },
  {
    "trade_id": "tid00000021",
    "ticker": "AAPL",
    "broker_id": "BKR011",
    "contra_broker_id": "BKR005",
    "quantity": 251,  # Mismatch example
    "price": 154.00,
    "order_type": "SELL",
    "date": "2025-07-21",
    "trade_timestamp": "2025-07-21 10:33:00"
  },
  ...
]
