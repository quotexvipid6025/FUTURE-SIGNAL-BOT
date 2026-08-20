#!/usr/bin/env python3
"""
Combined Inline + Reply keyboard Telegram bot server with interactive filter/time flow.
Now includes MARKET selection (LIVE / OTC) before broker selection.
Also includes MANUAL SIGNAL with pair selection.
"""
import os
import time
import json
import requests
from datetime import datetime, timedelta

from telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from telegram_bot import TelegramBot
from future_signal import generate_signals, ALL_PAIRS, BLACKOUT_PAIRS, FILTERS, LIVE_PAIRS

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID))

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
GET_UPDATES = BASE_URL + "/getUpdates"
SEND_MESSAGE = BASE_URL + "/sendMessage"
ANSWER_CALLBACK = BASE_URL + "/answerCallbackQuery"

# ----------------------------
# BROKER PAIRS CONFIGURATION
# ----------------------------
BROKER_PAIRS = {
    "quotex": list(ALL_PAIRS),
    "pocket": list(ALL_PAIRS),
    "olymptrade": list(ALL_PAIRS),
    "custom": ["BTCUSD-OTC", "XAUUSD-OTC", "ETHUSD-OTC"]
}
BROKER_LABEL_TO_KEY = {k.upper(): k for k in BROKER_PAIRS.keys()}

# ----------------------------
# UI: text + keyboards
# ----------------------------
MENU_TEXT = (
    "<b>🔥 MD_SUMON_MT4 — FUTURE SIGNALS</b>\n"
    "────────────────────────────────────\n"
    "Select an option below to begin:"
)

MAIN_MENU_INLINE = [
    [{"text": "🍥 FUTURE SIGNALS", "callback_data": "menu:future"},
     {"text": "✍️ MANUAL SIGNAL", "callback_data": "menu:manual"}],
    [{"text": "👤 MY PROFILE", "callback_data": "menu:profile"},
     {"text": "💬 SUPPORT", "callback_data": "menu:support"},],
    [{"text": "❕ ABOUT", "callback_data": "menu:about"}],
]

MAIN_MENU_REPLY = [
    ["🍥 FUTURE SIGNALS","✍️ MANUAL SIGNAL"],
    ["👤 MY PROFILE","💬 SUPPORT"],
    ["❕ ABOUT"]
]

# MARKET selection (LIVE / OTC)
MARKET_INLINE = [
    [{"text": "📈 LIVE MARKET", "callback_data": "market:LIVE"},
     {"text": "🟣 OTC MARKET",  "callback_data": "market:OTC"}],
    [{"text": "🔙 Back", "callback_data": "menu:back"}],
]

# Filter selection keyboard (uses FILTERS from future_signal.py)
FILTER_INLINE = [
    [{"text": f"{FILTERS['1']['name']}", "callback_data": "select:filter:1"},
     {"text": f"{FILTERS['2']['name']}", "callback_data": "select:filter:2"}],
    [{"text": f"{FILTERS['3']['name']}", "callback_data": "select:filter:3"}],
]

# Time presets
TIME_INLINE = [
    [{"text": "⏱ 5 min", "callback_data": "select:time:5"},
     {"text": "⏱ 15 min", "callback_data": "select:time:15"}],
    [{"text": "⏱ 30 min", "callback_data": "select:time:30"},
     {"text": "⌨️ Custom (min)", "callback_data": "select:time:custom"}],
    [{"text": "🔙 Back", "callback_data": "menu:back"}]
]

# ----------------------------
# Session state (in-memory)
# ----------------------------
session_state = {}

# ----------------------------
# Helpers for Telegram API
# ----------------------------
def post(url, data):
    try:
        return requests.post(url, data=data, timeout=15)
    except Exception as e:
        print("HTTP POST error:", e)
        return None

def answer_callback(callback_id, text=""):
    try:
        requests.post(ANSWER_CALLBACK, data={"callback_query_id": callback_id, "text": text}, timeout=5)
    except Exception:
        pass

def send_inline_menu(chat_id):
    payload = {
        "chat_id": chat_id,
        "text": MENU_TEXT,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": json.dumps({"inline_keyboard": MAIN_MENU_INLINE}),
    }
    return post(SEND_MESSAGE, payload)

def send_reply_menu(chat_id):
    payload = {
        "chat_id": chat_id,
        "text": "Tap an option below or use the inline buttons above:",
        "parse_mode": "HTML",
        "reply_markup": json.dumps({"keyboard": MAIN_MENU_REPLY, "resize_keyboard": True}),
    }
    return post(SEND_MESSAGE, payload)

def send_menu_both(chat_id):
    send_inline_menu(chat_id)
    time.sleep(0.25)
    send_reply_menu(chat_id)

def send_market_selection(chat_id):
    post(SEND_MESSAGE, {
        "chat_id": chat_id,
        "text": "<b>Select Market</b>\nChoose LIVE or OTC:",
        "parse_mode": "HTML",
        "reply_markup": json.dumps({"inline_keyboard": MARKET_INLINE})
    })

def send_broker_selection_both(chat_id):
    kb = []
    for key in BROKER_PAIRS.keys():
        kb.append([{"text": key.upper(), "callback_data": f"broker:{key}"}])
    kb.append([{"text": "🔙 Back", "callback_data": "menu:back"}])
    post(SEND_MESSAGE, {"chat_id": chat_id, "text": "<b>Select Broker for FUTURE SIGNALS</b>", "parse_mode": "HTML",
                       "reply_markup": json.dumps({"inline_keyboard": kb})})
    time.sleep(0.25)
    rows = [[k.upper() for k in BROKER_PAIRS.keys()]]
    rows.append(["🔙 Back"])
    post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Or tap a broker below:", "parse_mode": "HTML",
                       "reply_markup": json.dumps({"keyboard": rows, "resize_keyboard": True})})

def send_filter_selection(chat_id):
    post(SEND_MESSAGE, {"chat_id": chat_id, "text": "<b>Select Filter</b>", "parse_mode": "HTML",
                       "reply_markup": json.dumps({"inline_keyboard": FILTER_INLINE})})

def send_time_selection(chat_id):
    post(SEND_MESSAGE, {"chat_id": chat_id, "text": "<b>Select Time Window</b>", "parse_mode": "HTML",
                       "reply_markup": json.dumps({"inline_keyboard": TIME_INLINE})})

def send_manual_market_selection(chat_id):
    """MANUAL SIGNAL এর জন্য মার্কেট সিলেকশন"""
    kb = [
        [{"text": "🔵 LIVE PAIRS", "callback_data": "manual:market:live"},
         {"text": "🟠 OTC PAIRS", "callback_data": "manual:market:otc"}],
        [{"text": "🔙 Back", "callback_data": "menu:back"}],
    ]
    post(SEND_MESSAGE, {
        "chat_id": chat_id,
        "text": "<b>Select Market Type for MANUAL SIGNAL</b>\n\n🔵 LIVE: USD/JPY, EUR/USD...\n🟠 OTC: BTCUSD-OTC, EURUSD-OTC...",
        "parse_mode": "HTML",
        "reply_markup": json.dumps({"inline_keyboard": kb})
    })

def send_manual_pairs_selection(chat_id, market_type):
    """নির্বাচিত মার্কেটের PAIRS দেখান"""
    pairs = LIVE_PAIRS if market_type == "live" else ALL_PAIRS
    title = "LIVE PAIRS" if market_type == "live" else "OTC PAIRS"
    emoji = "🔵" if market_type == "live" else "🟠"
    
    kb = []
    for i, pair in enumerate(pairs):
        kb.append([{"text": f"{emoji} {pair}", "callback_data": f"manual:pair:{market_type}:{i}"}])
    kb.append([{"text": "🔙 Back", "callback_data": "menu:back"}])
    
    post(SEND_MESSAGE, {
        "chat_id": chat_id,
        "text": f"<b>Select a PAIR ({title})</b>",
        "parse_mode": "HTML",
        "reply_markup": json.dumps({"inline_keyboard": kb})
    })

def clear_session(chat_id):
    if chat_id in session_state:
        del session_state[chat_id]

# ----------------------------
# Core flow helpers
# ----------------------------
def start_selection_flow(chat_id, broker_key):
    # preserve existing session market if present
    st = session_state.get(chat_id, {})
    st.update({"broker": broker_key, "fkey": None, "window_mins": None, "awaiting_custom_minutes": False})
    session_state[chat_id] = st
    send_filter_selection(chat_id)
    time.sleep(0.15)
    send_time_selection(chat_id)

def set_filter_and_maybe_generate(chat_id, fkey):
    st = session_state.get(chat_id)
    if not st:
        post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Session expired, please select broker again."})
        return
    st["fkey"] = fkey
    post(SEND_MESSAGE, {"chat_id": chat_id, "text": f"✅ Filter: <b>{FILTERS.get(fkey, {}).get('name', fkey)}</b>", "parse_mode": "HTML"})
    if st.get("window_mins"):
        do_generate_for_session(chat_id)
    else:
        send_time_selection(chat_id)

def set_time_and_maybe_generate(chat_id, minutes):
    st = session_state.get(chat_id)
    if not st:
        post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Session expired, please select broker again."})
        return
    st["window_mins"] = minutes
    st["awaiting_custom_minutes"] = False
    post(SEND_MESSAGE, {"chat_id": chat_id, "text": f"✅ Time Window: <b>{minutes} minutes</b>", "parse_mode": "HTML"})
    if st.get("fkey"):
        do_generate_for_session(chat_id)
    else:
        send_filter_selection(chat_id)

def do_generate_for_session(chat_id):
    st = session_state.get(chat_id)
    if not st:
        post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Session expired before generation."})
        return
    
    # Check if MANUAL mode
    if st.get("manual_mode"):
        pair = st.get("manual_pair")
        market_type = st.get("manual_market", "otc")
        fkey = st.get("fkey") or "1"
        mins = int(st.get("window_mins") or 15)
        start_dt = datetime.now() + timedelta(minutes=1)
        end_dt = start_dt + timedelta(minutes=mins)
        market_label = "LIVE" if market_type == "live" else "OTC"
        
        post(SEND_MESSAGE, {"chat_id": chat_id, "text": f"🔎 Generating signal for <b>{pair}</b> ({market_label})...", "parse_mode": "HTML"})
        signals = generate_signals([pair], market_label, fkey, start_dt, end_dt)
        bot = TelegramBot(bot_token=BOT_TOKEN, chat_id=chat_id)
        time_window = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
        bot.send_signals_summary(signals, market_label, FILTERS.get(fkey, {}).get("name", fkey), time_window)
        clear_session(chat_id)
    else:
        # FUTURE SIGNALS mode
        broker = st.get("broker")
        fkey = st.get("fkey") or "1"
        mins = int(st.get("window_mins") or 15)
        start_dt = datetime.now() + timedelta(minutes=1)
        end_dt = start_dt + timedelta(minutes=mins)
        market = st.get("market", "OTC")
        
        # choose pairs by market
        if market == "LIVE":
            pairs = list(LIVE_PAIRS)
        else:
            pairs = BROKER_PAIRS.get(broker, list(ALL_PAIRS))
        
        post(SEND_MESSAGE, {"chat_id": chat_id, "text": f"🔎 Generating FUTURE SIGNALS for {market} ({mins}m) using Filter {fkey}...", "parse_mode": "HTML"})
        signals = generate_signals(pairs, market, fkey, start_dt, end_dt)
        bot = TelegramBot(bot_token=BOT_TOKEN, chat_id=chat_id)
        time_window = f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}"
        bot.send_signals_summary(signals, market, FILTERS.get(fkey, {}).get("name", fkey), time_window)
        clear_session(chat_id)

# ----------------------------
# Polling loop
# ----------------------------
def normalize_text(t):
    if not t: return ""
    return t.strip().upper()

def run_polling():
    print("Combined Inline+Reply bot (interactive) polling started...")
    offset = None
    try:
        send_menu_both(CHAT_ID)
    except Exception:
        pass

    while True:
        try:
            params = {"timeout": 30, "limit": 10}
            if offset:
                params["offset"] = offset
            resp = requests.get(GET_UPDATES, params=params, timeout=35)
            data = resp.json()
            if not data.get("ok"):
                time.sleep(2); continue
            for item in data.get("result", []):
                offset = item["update_id"] + 1
                if "message" in item:
                    msg = item["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "")
                    if not text:
                        continue
                    txt = normalize_text(text)
                    if txt.startswith("/START"):
                        send_menu_both(chat_id); continue
                    if txt == "🔙 BACK":
                        send_menu_both(chat_id); continue
                    if txt in ("🍥 FUTURE SIGNALS", "FUTURE SIGNALS"):
                        post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Opening FUTURE SIGNALS..."})
                        send_market_selection(chat_id); continue
                    if txt in ("✍️ MANUAL SIGNAL", "MANUAL SIGNAL"):
                        post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Opening MANUAL SIGNAL..."})
                        send_manual_market_selection(chat_id); continue
                    if txt in BROKER_LABEL_TO_KEY:
                        bkey = BROKER_LABEL_TO_KEY[txt]
                        post(SEND_MESSAGE, {"chat_id": chat_id, "text": f"Selected broker: {txt}. Please choose filter & time."})
                        start_selection_flow(chat_id, bkey); continue
                    st = session_state.get(chat_id)
                    if st and st.get("awaiting_custom_minutes"):
                        try:
                            m = int(text.strip())
                            if m <= 0:
                                raise ValueError()
                            set_time_and_maybe_generate(chat_id, m)
                        except Exception:
                            post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Invalid minutes. Send a positive integer (e.g., 15)."})
                        continue
                    # other reply actions
                    if txt in ("🟩 AUTO SIGNAL", "AUTO SIGNAL"):
                        post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Auto Signal not implemented in this demo."}); continue
                    if txt in ("👤 MY PROFILE", "MY PROFILE"):
                        post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Profile page placeholder."}); continue
                    if txt in ("💬 SUPPORT", "SUPPORT"):
                        post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Contact @MD_SUMON_MT4 for support."}); continue
                    if txt in ("❕ ABOUT", "ABOUT"):
                        post(SEND_MESSAGE, {"chat_id": chat_id, "text": "About placeholder."}); continue

                if "callback_query" in item:
                    cb = item["callback_query"]
                    cb_id = cb["id"]
                    cb_data = cb.get("data", "")
                    chat_id = cb["message"]["chat"]["id"]
                    if cb_data == "menu:future":
                        answer_callback(cb_id, "Opening FUTURE SIGNALS...")
                        send_market_selection(chat_id)
                    elif cb_data == "menu:manual":
                        answer_callback(cb_id, "Opening MANUAL SIGNAL...")
                        send_manual_market_selection(chat_id)
                    elif cb_data.startswith("market:"):
                        _, mkt = cb_data.split(":", 1)
                        st = session_state.get(chat_id, {})
                        st["market"] = mkt  # LIVE or OTC
                        session_state[chat_id] = st
                        answer_callback(cb_id, f"{mkt} selected")
                        send_broker_selection_both(chat_id)
                    elif cb_data.startswith("manual:market:"):
                        _, _, market_type = cb_data.split(":", 2)
                        st = session_state.get(chat_id, {})
                        st["manual_market"] = market_type
                        st["manual_mode"] = True
                        session_state[chat_id] = st
                        answer_callback(cb_id, f"Market {'LIVE' if market_type == 'live' else 'OTC'} selected")
                        send_manual_pairs_selection(chat_id, market_type)
                    elif cb_data.startswith("manual:pair:"):
                        parts = cb_data.split(":")
                        market_type = parts[2]
                        pair_idx = int(parts[3])
                        pairs = LIVE_PAIRS if market_type == "live" else ALL_PAIRS
                        try:
                            pair = pairs[pair_idx]
                            st = session_state.get(chat_id, {})
                            st["manual_pair"] = pair
                            st["manual_market"] = market_type
                            st["manual_mode"] = True
                            session_state[chat_id] = st
                            answer_callback(cb_id, f"Pair {pair} selected")
                            post(SEND_MESSAGE, {"chat_id": chat_id, "text": f"✅ Pair: <b>{pair}</b>\n\nNow choose Filter & Time", "parse_mode": "HTML"})
                            time.sleep(0.2)
                            send_filter_selection(chat_id)
                            time.sleep(0.2)
                            send_time_selection(chat_id)
                        except:
                            answer_callback(cb_id, "Invalid pair")
                    elif cb_data.startswith("broker:"):
                        _, bkey = cb_data.split(":", 1)
                        answer_callback(cb_id, f"Selected {bkey.upper()}")
                        post(SEND_MESSAGE, {"chat_id": chat_id, "text": f"✅ Broker: <b>{bkey.upper()}</b>\n\nChoose filter & time", "parse_mode": "HTML"})
                        start_selection_flow(chat_id, bkey)
                    elif cb_data.startswith("select:filter:"):
                        _, _, fkey = cb_data.split(":", 2)
                        answer_callback(cb_id, f"Filter {fkey} selected")
                        set_filter_and_maybe_generate(chat_id, fkey)
                    elif cb_data.startswith("select:time:"):
                        _, _, tval = cb_data.split(":", 2)
                        if tval == "custom":
                            st = session_state.get(chat_id)
                            if not st:
                                post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Session expired; please select again."})
                            else:
                                st["awaiting_custom_minutes"] = True
                                answer_callback(cb_id, "Send custom minutes as a message (e.g., 12)")
                                post(SEND_MESSAGE, {"chat_id": chat_id, "text": "Send custom window duration in minutes (e.g., 12):"})
                        else:
                            minutes = int(tval)
                            answer_callback(cb_id, f"{minutes} min selected")
                            set_time_and_maybe_generate(chat_id, minutes)
                    elif cb_data == "menu:back":
                        answer_callback(cb_id, "Back to menu")
                        send_menu_both(chat_id)
                    else:
                        answer_callback(cb_id, "Option received")

        except Exception as e:
            print("Polling error:", e)
            time.sleep(3)

if __name__ == "__main__":
    run_polling()
