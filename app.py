import os
import asyncio
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from flask import Flask, request, jsonify
from dotenv import load_dotenv
import sqlite3

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, Update
from aiogram.enums import ParseMode

import stripe
from paystackease import PayStackBase
import requests

# Load environment variables
load_dotenv()

# Configure logging (modern best practice over print statements)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Payment setups (using env vars for secrets)
#stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
#paystack_client = PayStackBase(secret_key=os.getenv('PAYSTACK_SECRET_KEY'))

# Bot & Dispatcher setup (aiogram 3.x modern style)
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dp = Dispatcher()

# Router for modular handlers
router = Router(name="main_router")

@router.message(Command("start"))
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Open App",
                web_app=WebAppInfo(url=os.getenv('MINI_APP_URL', 'http://localhost:3000'))
            )
        ]
    ])
    await message.reply(
        "Welcome to 1 TAP = 1 HOPE! Tap to help kids.",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML  # Modern: use parse_mode for formatting if needed
    )

dp.include_router(router)

# DB class for better management (context manager for connections)
class Database:
    def __init__(self, db_name: str = 'hope.db'):
        self.db_name = db_name

    def __enter__(self) -> sqlite3.Cursor:
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        self.conn.close()

# DB Initialization (idempotent, modern schema with indexes)
def init_db():
    with Database() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS taps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                status TEXT DEFAULT 'pending'
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_taps_user_id ON taps (user_id)
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sponsors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                pledge_amount REAL NOT NULL,
                currency TEXT NOT NULL,
                frequency TEXT,
                category TEXT,
                verified BOOLEAN DEFAULT 0,
                balance REAL DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sponsors_email ON sponsors (email)
        ''')
    logger.info("Database initialized successfully")

# Startup callback
async def on_startup():
    logger.info("Bot startup complete")

# Polling function
async def run_bot():
    await on_startup()
    await dp.start_polling(bot, allowed_updates=['message'])

# === Flask Endpoints (with error handling) ===

@app.route('/tap', methods=['POST'])
def tap() -> Dict[str, Any]:
    try:
        data = request.json
        user_id = data.get('user_id')
        client_timestamp = data.get('timestamp')

        if not user_id:
            return jsonify({'message': 'No user ID'}), 400

        with Database() as cursor:
            # Anti-fraud: 24h limit
            cursor.execute("SELECT timestamp FROM taps WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
            last_tap = cursor.fetchone()
            if last_tap and datetime.fromisoformat(last_tap[0]) > datetime.now() - timedelta(hours=24):
                return jsonify({'message': 'Tap limit reached'}), 429

            # Anti-fraud: 3-5 sec delay
            if datetime.now().timestamp() - client_timestamp / 1000 < 3:
                return jsonify({'message': 'Too fast'}), 400

            # Insert tap
            cursor.execute("INSERT INTO taps (user_id, timestamp, status) VALUES (?, ?, ?)",
                           (user_id, datetime.now().isoformat(), 'pending'))

        logger.info(f"Tap registered for user {user_id}")
        return jsonify({'message': 'Tap registered! You helped today 🎉'})

    except Exception as e:
        logger.error(f"Error in /tap: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@app.route('/sponsor', methods=['POST'])
def sponsor() -> Dict[str, Any]:
    try:
        data = request.json
        # TODO: Implement OTP verification
        intent = stripe.PaymentIntent.create(
            amount=int(data['pledge_amount'] * 100),
            currency=data['currency'].lower(),
            payment_method_types=['card'],
            receipt_email=data['email']
        )
        return jsonify({'client_secret': intent['client_secret']})
    except Exception as e:
        logger.error(f"Error in /sponsor: {str(e)}")
        return jsonify({'message': 'Payment error'}), 500

@app.route('/sponsor_paystack', methods=['POST'])
def sponsor_paystack() -> Dict[str, Any]:
    try:
        data = request.json
        response = paystack_client.transactions.initiate(
            email=data['email'],
            amount=data['pledge_amount'],
            currency=data['currency']
        )
        return jsonify({'url': response['authorization_url']})
    except Exception as e:
        logger.error(f"Error in /sponsor_paystack: {str(e)}")
        return jsonify({'message': 'Payment error'}), 500

@app.route('/ton_payment', methods=['POST'])
def ton_payment() -> Dict[str, Any]:
    try:
        data = request.json
        tx_hash = data['tx_hash']
        response = requests.get(f'https://tonapi.io/v2/transactions/{tx_hash}')
        if response.status_code == 200 and 'success' in response.json():
            with Database() as cursor:
                cursor.execute("UPDATE sponsors SET balance = balance + ? WHERE id = ?", (data['amount'], data['sponsor_id']))
            logger.info(f"TON payment verified for sponsor {data['sponsor_id']}")
            return jsonify({'message': 'TON payment verified!'})
        return jsonify({'message': 'Invalid TX'}), 400
    except Exception as e:
        logger.error(f"Error in /ton_payment: {str(e)}")
        return jsonify({'message': 'Server error'}), 500

@app.route('/webhook', methods=['POST'])
async def webhook() -> Dict[str, Any]:
    try:
        update = Update(**request.json)
        await dp.process_update(update)
        return jsonify(success=True)
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        return jsonify(success=False), 500

# Run the app
if __name__ == '__main__':
    init_db()

    # For local dev: polling in background
    threading.Thread(
        target=lambda: asyncio.run(run_bot()),
        daemon=True
    ).start()

    app.run(port=5000, debug=True, threaded=True)  # threaded=True for better local concurrency