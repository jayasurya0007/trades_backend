import csv
import random
from flask import Flask, jsonify
import time
from threading import Lock
import os

app = Flask(__name__)

# Global variables with thread-safe access
trade_records = []
last_sent_records = []
data_lock = Lock()
last_update_time = 0

def load_trade_records():
    """Load trade records from the CSV file"""
    global trade_records
    with open('trade_records_sample.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        trade_records = list(csv_reader)

def get_random_records():
    """Get 10 random records from the trade records"""
    if len(trade_records) < 10:
        return trade_records.copy()
    return random.sample(trade_records, 10)

def maybe_update_records():
    """Check if we should update records (every 10 minutes)"""
    global last_sent_records, last_update_time
    current_time = time.time()
    
    with data_lock:
        if current_time - last_update_time >= 600:  # 10 minutes in seconds
            last_sent_records = get_random_records()
            last_update_time = current_time
            print(f"Updated records at {time.strftime('%Y-%m-%d %H:%M:%S')}")

@app.route('/get_records', methods=['GET'])
def get_records():
    """Endpoint to get the current set of random records"""
    maybe_update_records()  # Check if we need to update first
    with data_lock:
        return jsonify(last_sent_records)

# Initialize when starting
load_trade_records()
with data_lock:
    last_sent_records = get_random_records()
    last_update_time = time.time()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)