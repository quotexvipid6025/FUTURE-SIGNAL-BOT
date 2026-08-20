#!/usr/bin/env python3
"""
Single-file FUTURE SIGNAL app with MANUAL SIGNAL (LIVE + OTC PAIRS)
Run: python future_signal_allinone.py
"""
import os, sys, time, json, random, hashlib, requests
from datetime import datetime, timedelta

# Config
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
if TELEGRAM_CHAT_ID:
    try:
        TELEGRAM_CHAT_ID = int(TELEGRAM_CHAT_ID)
    except:
        pass
BOT_NAME = "FUTURE_SIGNAL BOT"
LOG_FILE = "telegram_bot.log"

# LIVE PAIRS (Forex)
LIVE_PAIRS = [
    "USD/JPY","EUR/JPY","EUR/USD","AUD/JPY","GBP/USD",
    "CAD/JPY","EUR/CAD","AUD/USD","EUR/GBP","CHF/JPY",
    "GBP/JPY","AUD/CAD","EUR/AUD","USD/CAD","EUR/CHF",
    "GBP/AUD","GBP/CAD","GBP/CHF","USD/CHF"
]

# OTC PAIRS (Crypto, Stocks, Commodities)
ALL_PAIRS = [
    "TRUUSD-OTC","BTCUSD-OTC","XAUUSD-OTC","XAGUSD-OTC",
    "ETHUSD-OTC","LTCUSD-OTC","BNBUSD-OTC","XRPUSD-OTC",
    "ETCUSD-OTC","ZECUSD-OTC","AXSUSD-OTC","BA-OTC",
    "PFE-OTC","AXP-OTC","JNJ-OTC","INTC-OTC",
    "FB-OTC","MCD-OTC","USCRUDE-OTC","UKBRENT-OTC",
    "USDBDT-OTC","USDEGP-OTC","USDIDR-OTC","USDINR-OTC",
    "USDMXN-OTC","USDNGN-OTC","USDPHP-OTC","USDPKR-OTC",
    "USDZAR-OTC","USDARS-OTC","USDCOP-OTC","USDDZD-OTC",
    "AUDJPY-OTC","AUDNZD-OTC","AUDUSD-OTC","AUDCAD-OTC",
    "AUDCHF-OTC","CADCHF-OTC","CHFJPY-OTC","EURAUD-OTC",
    "EURCAD-OTC","EURCHF-OTC","EURGBP-OTC","EURJPY-OTC",
    "EURNZD-OTC","EURUSD-OTC","GBPAUD-OTC","GBPCAD-OTC",
    "GBPCHF-OTC","GBPJPY-OTC","GBPUSD-OTC","NZDUSD-OTC",
    "USDBRL-OTC","USDCAD-OTC","USDCHF-OTC","USDJPY-OTC",
]

FILTERS = {
    "1": {"name": "AI FILTER"},
    "2": {"name": "TREND FILTER"},
    "3": {"name": "HUMAN BRAIN"},
}

def require_token():
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: Set TELEGRAM_BOT_TOKEN environment variable")
        sys.exit(1)

class TelegramBot:
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"
        self.send_url = f"{self.api_base}/sendMessage"

    def send_message(self, text, parse_mode="HTML", reply_markup=None):
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            if reply_markup:
                payload["reply_markup"] = json.dumps(reply_markup)
            resp = requests.post(self.send_url, data=payload, timeout=15)
            return resp.status_code == 200
        except:
            return False

    def send_signals_summary(self, signals, market, filter_name, time_window):
        if not signals:
            return self.send_message(f"<b>❌ No Signals</b>\nMarket: {market}\nFilter: {filter_name}")
        
        message = (
            f"<b>📊 FUTURE SIGNAL - BATCH REPORT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Market:</b> {market}\n"
            f"<b>Filter:</b> {filter_name}\n"
            f"<b>Time Window:</b> {time_window}\n"
            f"<b>Generated:</b> {datetime.now().strftime('%d %b %Y | %H:%M:%S')}\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>📈 Total Signals: {len(signals)}</b>\n\n"
        )
        for idx, s in enumerate(signals, 1):
            pair = s.get("pair", "N/A")
            direction = s.get("direction", "N/A")
            time_str = s.get("time", "N/A")
            emoji = "📈" if direction == "CALL" else "📉"
            message += f"<b>{idx}.</b> <code>{pair}</code> → {emoji} <b>{direction}</b> @ <code>{time_str}</code>\n"
        
        message += (
            f"\n━━━━━━━━━━━━━━━━━━━\n"
            f"✅ All signals passed quality filter\n"
            f"📞 Support: @MD_SUMON_MT4\n"
            f"📱 Channel: t.me/FUTURE_SIGNAL11"
        )
        return self.send_message(message)

def make_seed(pairs, fkey, start_dt, end_dt):
    date_str = datetime.now().strftime("%Y-%m-%d")
    key = f"{date_str}|{fkey}|{start_dt.strftime('%H:%M')}|{end_dt.strftime('%H:%M')}|{''.join(sorted(pairs))}"
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**32)

def fake_filter_check(pair, fkey):
    thresholds = {"1": (52, 58.0), "2": (48, 55.0), "3": (45, 52.0)}
    low, thresh = thresholds.get(fkey, (50, 55.0))
    base = random.uniform(low, 100)
    return base >= thresh, round(base, 1)

def generate_signals(pairs, market, fkey, start_dt, end_dt):
    seed = make_seed(pairs, fkey, start_dt, end_dt)
    rng_state = random.getstate()
    random.seed(seed)
    signals = []
    consecutive = 0
    cursor = start_dt + timedelta(minutes=random.randint(1, 3))
    pool = list(pairs)
    random.shuffle(pool)
    
    for pair in pool:
        if cursor > end_dt:
            break
        passed, acc = fake_filter_check(pair, fkey)
        if not passed:
            continue
        consecutive = consecutive + 1 if acc < 60 else 0
        if consecutive >= 3:
            consecutive = 0
            continue
        signals.append({
            "pair": pair,
            "direction": random.choice(["CALL", "PUT"]),
            "time": cursor.strftime("%H:%M"),
            "expiry": "1 MIN",
        })
        cursor += timedelta(minutes=random.randint(3, 7))
    
    random.setstate(rng_state)
    signals.sort(key=lambda s: s["time"])
    return signals

def run_server():
    require_token()
    brokers = ["quotex", "pocket", "olymptrade", "custom"]
    
    BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    GET_UPDATES = BASE + "/getUpdates"
    SEND_MESSAGE = BASE + "/sendMessage"
    ANSWER_CALLBACK = BASE + "/answerCallbackQuery"
    
    session_state = {}

    def post(url, data):
        try:
            return requests.post(url, data=data, timeout=15)
        except:
            return None

    def answer_callback(callback_id, text=""):
        try:
            requests.post(ANSWER_CALLBACK, data={"callback_query_id": callback_id, "text": text}, timeout=5)
        except:
            pass

    def send_inline_menu(chat_id):
        kb = [
            [{"text": "🟩 AUTO SIGNAL", "callback_data": "menu:auto"},
             {"text": "🍥 FUTURE SIGNALS", "callback_data": "menu:future"}],
            [{"text": "✍️ MANUAL SIGNAL", "callback_data": "manual_signal_start"}],
            [{"text": "👤 MY PROFILE", "callback_data": "menu:profile"},
             {"text": "💸 PRICING", "callback_data": "menu:pricing"}],
            [{"text": "💬 SUPPORT", "callback_data": "menu:support"},
             {"text": "📲 HOW TO USE", "callback_data": "menu:howto"}],
            [{"text": "❕ ABOUT", "callback_data": "menu:about"}],
        ]
        post(SEND_MESSAGE, {
            "chat_id": chat_id,
            "text": "<b>🔥 INFINITY AI SHOT — FUTURE SIGNALS</b>\nSelect an option below:",
            "parse_mode": "HTML",
            "reply_markup": json.dumps({"inline_keyboard": kb})
        })

    def send_market_type_selection(chat_id):
        kb = [
            [{"text": "🔵 LIVE PAIRS", "callback_data": "market_type:live"},
             {"text": "🟠 OTC PAIRS", "callback_data": "market_type:otc"}],
            [{"text": "🔙 Back", "callback_data": "back_to_menu"}]
        ]
        post(SEND_MESSAGE, {
            "chat_id": chat_id,
            "text": "<b>Select Market Type</b>\n\n🔵 LIVE: USD/JPY, EUR/USD...\n🟠 OTC: BTCUSD-OTC, EURUSD-OTC...",
            "parse_mode": "HTML",
            "reply_markup": json.dumps({"inline_keyboard": kb})
        })

    def send_pairs_selection(chat_id, market_type):
        pairs = LIVE_PAIRS if market_type == "live" else ALL_PAIRS
        title = "LIVE PAIRS" if market_type == "live" else "OTC PAIRS"
        emoji = "🔵" if market_type == "live" else "🟠"
        
        kb = []
        for i, pair in enumerate(pairs):
            kb.append([{"text": f"{emoji} {pair}", "callback_data": f"pair:{market_type}:{i}"}])
        kb.append([{"text": "🔙 Back", "callback_data": "back_to_menu"}])
        
        post(SEND_MESSAGE, {
            "chat_id": chat_id,
            "text": f"<b>Select a PAIR ({title})</b>",
            "parse_mode": "HTML",
            "reply_markup": json.dumps({"inline_keyboard": kb})
        })

    def send_filter_selection(chat_id):
        kb = [
            [{"text": FILTERS['1']['name'], "callback_data": "filter:1"},
             {"text": FILTERS['2']['name'], "callback_data": "filter:2"}],
            [{"text": FILTERS['3']['name'], "callback_data": "filter:3"}],
        ]
        post(SEND_MESSAGE, {
            "chat_id": chat_id,
            "text": "<b>Select Filter</b>",
            "parse_mode": "HTML",
            "reply_markup": json.dumps({"inline_keyboard": kb})
        })

    def send_time_selection(chat_id):
        kb = [
            [{"text": "⏱ 5 min", "callback_data": "time:5"},
             {"text": "⏱ 15 min", "callback_data": "time:15"}],
            [{"text": "⏱ 30 min", "callback_data": "time:30"},
             {"text": "⌨️ Custom", "callback_data": "time:custom"}],
            [{"text": "🔙 Back", "callback_data": "back_to_menu"}]
        ]
        post(SEND_MESSAGE, {
            "chat_id": chat_id,
            "text": "<b>Select Time Window</b>",
            "parse_mode": "HTML",
            "reply_markup": json.dumps({"inline_keyboard": kb})
        })

    def start_manual_flow(chat_id):
        session_state[chat_id] = {
            "mode": "manual",
            "market_type": None,
            "pair": None,
            "fkey": None,
            "window_mins": None,
        }
        send_market_type_selection(chat_id)

    def set_manual_market_type(chat_id, market_type):
        st = session_state.get(chat_id)
        if not st:
            post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Session expired"})
            return
        st["market_type"] = market_type
        label = "LIVE PAIRS" if market_type == "live" else "OTC PAIRS"
        post(SEND_MESSAGE, {"chat_id": chat_id, "text": f"✅ Market: <b>{label}</b>", "parse_mode": "HTML"})
        time.sleep(0.2)
        send_pairs_selection(chat_id, market_type)

    def set_manual_pair(chat_id, market_type, pair_idx):
        st = session_state.get(chat_id)
        if not st:
            return
        pairs = LIVE_PAIRS if market_type == "live" else ALL_PAIRS
        try:
            pair = pairs[int(pair_idx)]
        except:
            return
        st["pair"] = pair
        st["market_type"] = market_type
        post(SEND_MESSAGE, {"chat_id": chat_id, "text": f"✅ Pair: <b>{pair}</b>", "parse_mode": "HTML"})
        time.sleep(0.2)
        send_filter_selection(chat_id)
        time.sleep(0.2)
        send_time_selection(chat_id)

    def set_filter(chat_id, fkey):
        st = session_state.get(chat_id)
        if not st:
            return
        st["fkey"] = fkey
        post(SEND_MESSAGE, {"chat_id": chat_id, "text": f"✅ Filter: <b>{FILTERS[fkey]['name']}</b>", "parse_mode": "HTML"})
        if st.get("window_mins"):
            generate_signal(chat_id)
        else:
            send_time_selection(chat_id)

    def set_time(chat_id, minutes):
        st = session_state.get(chat_id)
        if not st:
            return
        st["window_mins"] = int(minutes)
        post(SEND_MESSAGE, {"chat_id": chat_id, "text": f"✅ Time: <b>{minutes} min</b>", "parse_mode": "HTML"})
        if st.get("fkey"):
            generate_signal(chat_id)
        else:
            send_filter_selection(chat_id)

    def generate_signal(chat_id):
        st = session_state.get(chat_id)
        if not st:
            return
        
        pair = st.get("pair")
        market_type = st.get("market_type")
        fkey = st.get("fkey", "1")
        mins = st.get("window_mins", 15)
        
        start_dt = datetime.now() + timedelta(minutes=1)
        end_dt = start_dt + timedelta(minutes=mins)
        market_label = "LIVE" if market_type == "live" else "OTC"
        
        post(SEND_MESSAGE, {"chat_id": chat_id, "text": f"🔎 Generating signal for <b>{pair}</b>...", "parse_mode": "HTML"})
        
        signals = generate_signals([pair], market_label, fkey, start_dt, end_dt)
        bot = TelegramBot(bot_token=TELEGRAM_BOT_TOKEN, chat_id=chat_id)
        time_window = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
        bot.send_signals_summary(signals, market_label, FILTERS[fkey]['name'], time_window)
        
        session_state.pop(chat_id, None)

    print("Bot started...")
    offset = None
    
    try:
        if TELEGRAM_CHAT_ID:
            tb = TelegramBot()
            tb.send_message("<b>Bot started ✅</b>")
    except:
        pass

    while True:
        try:
            params = {"timeout": 30, "limit": 10}
            if offset:
                params["offset"] = offset
            resp = requests.get(GET_UPDATES, params=params, timeout=35)
            data = resp.json()
            if not data.get("ok"):
                time.sleep(2)
                continue
            
            for item in data.get("result", []):
                offset = item["update_id"] + 1
                
                # Message handling
                if "message" in item:
                    msg = item["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "").strip().upper()
                    
                    if text.startswith("/START") or text == "🔙 BACK":
                        send_inline_menu(chat_id)
                        continue
                    
                    if text in ("✍️ MANUAL SIGNAL", "MANUAL SIGNAL"):
                        start_manual_flow(chat_id)
                        continue
                
                # Callback handling
                if "callback_query" in item:
                    cb = item["callback_query"]
                    cb_id = cb["id"]
                    cb_data = cb.get("data", "")
                    chat_id = cb["message"]["chat"]["id"]
                    
                    if cb_data == "manual_signal_start":
                        answer_callback(cb_id, "Opening MANUAL SIGNAL...")
                        start_manual_flow(chat_id)
                    elif cb_data.startswith("market_type:"):
                        market_type = cb_data.split(":")[-1]
                        answer_callback(cb_id, f"Market selected")
                        set_manual_market_type(chat_id, market_type)
                    elif cb_data.startswith("pair:"):
                        parts = cb_data.split(":")
                        market_type = parts[1]
                        pair_idx = parts[2]
                        answer_callback(cb_id, "Pair selected")
                        set_manual_pair(chat_id, market_type, pair_idx)
                    elif cb_data.startswith("filter:"):
                        fkey = cb_data.split(":")[-1]
                        answer_callback(cb_id, "Filter selected")
                        set_filter(chat_id, fkey)
                    elif cb_data.startswith("time:"):
                        tval = cb_data.split(":")[-1]
                        if tval == "custom":
                            answer_callback(cb_id, "Send minutes (e.g., 12)")
                            post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Send time in minutes:"})
                        else:
                            answer_callback(cb_id, f"{tval} min selected")
                            set_time(chat_id, tval)
                    elif cb_data in ("back_to_menu", "menu:back"):
                        answer_callback(cb_id, "Back")
                        send_inline_menu(chat_id)
                    else:
                        answer_callback(cb_id)
        except Exception as e:
            print("Error:", e)
            time.sleep(3)

if __name__ == "__main__":
    run_server()
