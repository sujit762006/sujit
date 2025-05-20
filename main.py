
from flask import Flask, request, jsonify, render_template
import requests
import pandas as pd
import ta

app = Flask(__name__)

API_KEY = "6bf49262e9f248a4b1f7bd78eb5b30b5"
CURRENCY_PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "USD/CHF", "NZD/USD"]
TIMEFRAMES = {
    "1min": "1 Minute",
    "5min": "5 Minutes",
    "15min": "15 Minutes"
}

@app.route('/')
def index():
    return render_template('index.html', pairs=CURRENCY_PAIRS, timeframes=TIMEFRAMES)

def fetch_data(symbol, interval):
    base, quote = symbol.split("/")
    url = f"https://api.twelvedata.com/time_series?symbol={base}/{quote}&interval={interval}&apikey={API_KEY}&outputsize=100"
    response = requests.get(url)
    data = response.json()
    if "values" in data:
        df = pd.DataFrame(data["values"])
        df = df.astype(float)
        df = df[::-1]
        return df
    else:
        return None

def analyze_data(df):
    df["rsi"] = ta.momentum.RSIIndicator(close=df["close"]).rsi()
    df["ema"] = ta.trend.EMAIndicator(close=df["close"], window=20).ema_indicator()
    df["macd"] = ta.trend.MACD(close=df["close"]).macd()

    latest = df.iloc[-1]
    if latest["rsi"] < 30 and latest["close"] > latest["ema"] and latest["macd"] > 0:
        return "BUY"
    elif latest["rsi"] > 70 and latest["close"] < latest["ema"] and latest["macd"] < 0:
        return "SELL"
    else:
        return "HOLD"

@app.route('/signal', methods=['POST'])
def get_signal():
    data = request.json
    symbol = data['symbol']
    timeframe = data['timeframe']
    df = fetch_data(symbol, timeframe)
    if df is not None:
        signal = analyze_data(df)
        return jsonify({"signal": signal})
    else:
        return jsonify({"error": "Failed to fetch data"}), 400

if __name__ == '__main__':
    app.run(debug=True)
