from flask import Flask, render_template_string, request
import yfinance as yf
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots

app = Flask(__name__)
def calculate_sma(data, timeperiod):
    return data.rolling(window=timeperiod).mean()
def calculate_rsi(data, timeperiod=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=timeperiod).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=timeperiod).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
@app.route('/', methods=['GET', 'POST'])
def index():
    ticker = "AAPL"
    if request.method == 'POST':
        ticker = request.form['ticker']
    data = yf.download(ticker, start="2023-01-01", end="2024-01-01")
    data['SMA_20'] = calculate_sma(data['Close'], timeperiod=20)
    data['SMA_50'] = calculate_sma(data['Close'], timeperiod=50)
    data['RSI'] = calculate_rsi(data['Close'], timeperiod=14)
    data['Signal'] = np.where(data['SMA_20'] > data['SMA_50'], 1, 0)
    data['Position'] = data['Signal'].diff()
    data['Return'] = data['Close'].pct_change()
    data['Strategy_Return'] = data['Return'] * data['Position'].shift(1)
    data['Cumulative_Strategy_Return'] = (1 + data['Strategy_Return']).cumprod()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=(f"Price & SMAs for {ticker}", "Cumulative Strategy Return"))

    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA_20'], mode='lines', name='20-Day SMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA_50'], mode='lines', name='50-Day SMA'), row=1, col=1)

    buy_signals = data.index[data['Position'] == 1]
    sell_signals = data.index[data['Position'] == -1]
    fig.add_trace(go.Scatter(x=buy_signals, y=data['Close'][buy_signals], mode='markers', marker=dict(color='green', symbol='triangle-up', size=10), name='Buy Signal'), row=1, col=1)
    fig.add_trace(go.Scatter(x=sell_signals, y=data['Close'][sell_signals], mode='markers', marker=dict(color='red', symbol='triangle-down', size=10), name='Sell Signal'), row=1, col=1)
  
    fig.add_trace(go.Scatter(x=data.index, y=data['Cumulative_Strategy_Return'], mode='lines', name='Cumulative Strategy Return', line=dict(color='blue')), row=2, col=1)

    fig.update_layout(height=800, title_text=f"Simple Moving Average Crossover Strategy for {ticker}", showlegend=True)

    graph_html = fig.to_html(full_html=False)
    

    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Simple Moving Average Crossover Strategy</title>
    </head>
    <body>
        <h1>Simple Moving Average Crossover Strategy</h1>
        <form method="POST">
            <label for="ticker">Enter Ticker Symbol:</label>
            <input type="text" id="ticker" name="ticker" value="{{ ticker }}" required>
            <button type="submit">Submit</button>
        </form>
        <div>{{ graph_html|safe }}</div>
    </body>
    </html>
    '''
    return render_template_string(html_template, graph_html=graph_html, ticker=ticker)
if __name__ == "__main__": 
    app.run(debug=True)
