import csv
import random
from flask import Flask, jsonify
import time
from threading import Lock
import os
from datetime import datetime, timedelta
import sqlite3
import copy

app = Flask(__name__)

# Global variables with thread-safe access
trade_pairs = []
last_sent_records = []
data_lock = Lock()
last_update_time = 0
ticker_data = []

# SQLite setup for persistent trade IDs
def init_db():
    """Initialize SQLite DB for persistent trade IDs"""
    db_path = os.path.join(os.getcwd(), 'trade_ids.db')
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS counters (
            name TEXT PRIMARY KEY, 
            value INTEGER
        )
    ''')
    conn.execute('INSERT OR IGNORE INTO counters VALUES ("trade_id", 0)')
    conn.commit()
    conn.close()

def generate_unique_trade_id():
    """Generate IDs that persist across restarts"""
    with sqlite3.connect('trade_ids.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE counters SET value = value + 1 WHERE name = "trade_id"')
        new_id = cursor.execute('SELECT value FROM counters WHERE name = "trade_id"').fetchone()[0]
    return f"tid{new_id:08d}"

def load_ticker_data():
    """Load ticker and price data from the CSV file"""
    global ticker_data
    try:
        with open('tickers.csv', mode='r') as file:
            csv_reader = csv.DictReader(file)
            ticker_data = list(csv_reader)
    except FileNotFoundError:
        print("Error: tickers.csv not found.")
        ticker_data = []

def introduce_mismatch(buy_trade, sell_trade):
    """Introduce a mismatch in one or more fields"""
    mismatch_type = random.choice(['quantity', 'price', 'date', 'timestamp', 'multiple'])

    if mismatch_type == 'quantity':
        diff = random.randint(1, max(1, buy_trade['quantity'] // 20))
        sell_trade['quantity'] = buy_trade['quantity'] + (diff if random.choice([True, False]) else -diff)

    elif mismatch_type == 'price':
        diff = buy_trade['price'] * random.uniform(0.001, 0.01)
        sell_trade['price'] = round(buy_trade['price'] + (diff if random.choice([True, False]) else -diff), 2)

    elif mismatch_type == 'date':
        sell_trade['date'] = (datetime.strptime(buy_trade['date'], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

    elif mismatch_type == 'timestamp':
        minutes_diff = random.randint(1, 30)
        sell_trade['trade_timestamp'] = (datetime.strptime(buy_trade['trade_timestamp'], '%Y-%m-%d %H:%M:%S') + timedelta(minutes=minutes_diff)).strftime('%Y-%m-%d %H:%M:%S')

    elif mismatch_type == 'multiple':
        introduce_mismatch(buy_trade, sell_trade)
        introduce_mismatch(buy_trade, sell_trade)

    return buy_trade, sell_trade

def generate_trade_pairs(count=15):
    """Generate pairs of buy/sell trades with controlled mismatches"""
    global ticker_data
    all_trades = []

    mismatch_indices = set(random.sample(range(count), int(count * 0.3)))  # 30% mismatch

    for i in range(count):
        ticker_info = random.choice(ticker_data)
        quantity = random.randint(1, 500) 
        broker1 = f"BKR{random.randint(1, 15):03d}"
        broker2 = f"BKR{random.randint(1, 15):03d}"
        while broker2 == broker1:
            broker2 = f"BKR{random.randint(1, 15):03d}"

        trade_id = generate_unique_trade_id()
        now = datetime.now()
        curr_date = now.strftime('%Y-%m-%d')
        curr_timestamp = now.strftime('%Y-%m-%d %H:%M:%S')

        buy_trade = {
            'trade_id': trade_id,
            'ticker': ticker_info['ticker'],
            'broker_id': broker1,
            'contra_broker_id': broker2,
            'quantity': quantity,
            'price': round(float(ticker_info['price']), 2),
            'order_type': 'BUY',
            'date': curr_date,
            'trade_timestamp': curr_timestamp
        }

        sell_trade = {
            'trade_id': trade_id,
            'ticker': ticker_info['ticker'],
            'broker_id': broker2,
            'contra_broker_id': broker1,
            'quantity': quantity,
            'price': round(float(ticker_info['price']), 2),
            'order_type': 'SELL',
            'date': curr_date,
            'trade_timestamp': curr_timestamp
        }

        # Introduce mismatch for 30% of trade pairs
        if i in mismatch_indices:
            buy_trade, sell_trade = introduce_mismatch(copy.deepcopy(buy_trade), copy.deepcopy(sell_trade))

        all_trades.extend([buy_trade, sell_trade])

    random.shuffle(all_trades)
    return all_trades

def maybe_update_records():
    """Check if we should update records (every 10 minutes)"""
    global last_sent_records, last_update_time, trade_pairs
    current_time = time.time()
    UPDATE_INTERVAL_SECONDS = 180
    with data_lock:
        if current_time - last_update_time >= UPDATE_INTERVAL_SECONDS:
            trade_pairs = generate_trade_pairs(15)
            last_sent_records = trade_pairs.copy()
            last_update_time = current_time
            print(f"Updated {len(trade_pairs)} records at {time.strftime('%Y-%m-%d %H:%M:%S')}")

@app.route('/get_records', methods=['GET'])
def get_records():
    """Endpoint to get the current set of trade records"""
    maybe_update_records()
    with data_lock:
        return jsonify(last_sent_records)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})

# Initialize
init_db()
load_ticker_data()
with data_lock:
    trade_pairs = generate_trade_pairs(15)
    last_sent_records = trade_pairs.copy()
    last_update_time = time.time()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
