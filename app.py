import csv
import random
from flask import Flask, jsonify
import time
from threading import Lock
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Global variables with thread-safe access
trade_pairs = []
last_sent_records = []
data_lock = Lock()
last_update_time = 0
ticker_data = []
trade_id_counter = 0  # Counter for generating unique trade IDs

def load_ticker_data():
    """Load ticker and price data from the CSV file"""
    global ticker_data
    with open('tickers.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        ticker_data = list(csv_reader)

def generate_unique_trade_id():
    """Generate a unique trade ID for each pair"""
    global trade_id_counter
    trade_id_counter += 1
    return f"tid{trade_id_counter:08d}"

def introduce_mismatch(trade_pair):
    """Introduce realistic mismatches in about 30% of trade pairs"""
    if random.random() > 0.3:  # 70% chance of no mismatch
        return trade_pair
    
    mismatch_type = random.choice(['quantity', 'price', 'date', 'timestamp', 'multiple'])
    buy_trade, sell_trade = trade_pair
    
    if mismatch_type == 'quantity':
        # Small quantity difference (1-5% of original quantity)
        diff = random.randint(1, max(1, buy_trade['quantity'] // 20))
        if random.choice([True, False]):
            sell_trade['quantity'] = buy_trade['quantity'] - diff
        else:
            sell_trade['quantity'] = buy_trade['quantity'] + diff
    
    elif mismatch_type == 'price':
        # Small price difference (0.1-1% of original price)
        diff = buy_trade['price'] * random.uniform(0.001, 0.01)
        if random.choice([True, False]):
            sell_trade['price'] = buy_trade['price'] - diff
        else:
            sell_trade['price'] = buy_trade['price'] + diff
        sell_trade['price'] = round(sell_trade['price'], 2)
    
    elif mismatch_type == 'date':
        # Date off by 1 day (business logic error)
        original_date = datetime.strptime(buy_trade['date'], '%Y-%m-%d')
        sell_trade['date'] = (original_date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    elif mismatch_type == 'timestamp':
        # Timestamp difference (1-30 minutes)
        original_ts = datetime.strptime(buy_trade['trade_timestamp'], '%Y-%m-%d %H:%M:%S')
        minutes_diff = random.randint(1, 30)
        sell_trade['trade_timestamp'] = (original_ts + timedelta(minutes=minutes_diff)).strftime('%Y-%m-%d %H:%M:%S')
    
    else:  # multiple mismatches
        # Apply 2 random mismatches
        for _ in range(2):
            trade_pair = introduce_mismatch(trade_pair)
    
    return (buy_trade, sell_trade)

def generate_trade_pairs(count=10):
    """Generate pairs of buy/sell trades with unique trade_ids"""
    global ticker_data
    all_trades = []
    
    for _ in range(count):
        # Select random ticker
        ticker_info = random.choice(ticker_data)
        ticker = ticker_info['ticker']
        price = float(ticker_info['price'])
        
        # Generate random quantities (between 10 and 1000, in multiples of 10)
        quantity = random.randint(1, 100) * 10
        
        # Generate broker IDs
        broker1 = f"BKR{random.randint(1, 50):03d}"
        broker2 = f"BKR{random.randint(1, 50):03d}"
        while broker2 == broker1:  # Ensure different brokers
            broker2 = f"BKR{random.randint(1, 50):03d}"
        
        # Current date and timestamp
        curr_date = datetime.now().strftime('%Y-%m-%d')
        curr_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Generate unique trade ID for this pair
        trade_id = generate_unique_trade_id()
        
        # Create buy trade
        buy_trade = {
            'trade_id': trade_id,
            'ticker': ticker,
            'broker_id': broker1,
            'contra_broker_id': broker2,
            'quantity': quantity,
            'price': price,
            'order_type': 'buy',
            'date': curr_date,
            'trade_timestamp': curr_timestamp
        }
        
        # Create corresponding sell trade
        sell_trade = {
            'trade_id': trade_id,
            'ticker': ticker,
            'broker_id': broker2,
            'contra_broker_id': broker1,
            'quantity': quantity,
            'price': price,
            'order_type': 'sell',
            'date': curr_date,
            'trade_timestamp': curr_timestamp
        }
        
        # Introduce mismatches in ~30% of pairs
        trade_pair = introduce_mismatch((buy_trade.copy(), sell_trade.copy()))
        
        all_trades.extend(trade_pair)
    
    # Shuffle the trades so mismatched pairs aren't always consecutive
    random.shuffle(all_trades)
    return all_trades

def maybe_update_records():
    """Check if we should update records (every 10 minutes)"""
    global last_sent_records, last_update_time, trade_pairs
    current_time = time.time()
    
    with data_lock:
        if current_time - last_update_time >= 600:  # 10 minutes in seconds
            trade_pairs = generate_trade_pairs(15)  # Generate 15 pairs (30 trades)
            last_sent_records = trade_pairs.copy()
            last_update_time = current_time
            print(f"Updated {len(trade_pairs)} records at {time.strftime('%Y-%m-%d %H:%M:%S')}")

@app.route('/get_records', methods=['GET'])
def get_records():
    """Endpoint to get the current set of trade records"""
    maybe_update_records()  # Check if we need to update first
    with data_lock:
        return jsonify(last_sent_records)

# Initialize when starting
load_ticker_data()
with data_lock:
    trade_pairs = generate_trade_pairs(15)  # Initial generation of 15 pairs (30 trades)
    last_sent_records = trade_pairs.copy()
    last_update_time = time.time()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)