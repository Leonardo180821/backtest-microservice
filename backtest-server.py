from flask import Flask, request, jsonify
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA

app = Flask(__name__)
@app.route('/backtest', methods=['POST'])
def backtest():
    data = request.get_json()
    rules = data.get('strategy', {})
    symbol = rules.get('symbol', 'BTC-USD')
    timeframe = rules.get('interval', '1h')

    # Descargar datos históricos ilimitados
    df = yf.download(symbol, period='2y', interval=timeframe)
    if df.empty:
        return jsonify({'error': 'No data found'}), 400

    # Estrategia de ejemplo (puedes reemplazarla con JSON de n8n)
    class TestStrategy(Strategy):
        def init(self):
            self.ma1 = self.I(SMA, self.data.Close, 10)
            self.ma2 = self.I(SMA, self.data.Close, 20)
        def next(self):
            if crossover(self.ma1, self.ma2):
                self.buy()
            elif crossover(self.ma2, self.ma1):
                self.sell()

    bt = Backtest(df, TestStrategy, cash=10000, commission=.002)
    stats = bt.run()

    result = {
        'symbol': symbol,
        'timeframe': timeframe,
        'profit_factor': stats['Profit Factor'],
        'max_drawdown': stats['Max. Drawdown [%]'],
        'num_trades': stats['# Trades'],
        'return': stats['Return [%]']
    }

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)