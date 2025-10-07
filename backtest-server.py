from flask import Flask, request, jsonify
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA
import os # Importar os para obtener el puerto de Render

app = Flask(__name__)

@app.route('/backtest', methods=['POST'])
def backtest():
    data = request.get_json()
    rules = data.get('strategy', {})
    symbol = rules.get('symbol', 'BTC-USD')
    timeframe = rules.get('interval', '1h')

    # Descargar datos históricos
    # Nota: El servidor está configurado a 2 años por defecto.
    df = yf.download(symbol, period='2y', interval=timeframe)
    
    # =======================================================
    # === CORRECCIÓN CRÍTICA PARA EL ERROR 500 (TypeError) ===
    # Esto aplanará el índice de columnas si es un MultiIndex, 
    # solucionando la incompatibilidad con backtesting.py.
    # El log 500 anterior indicaba que esta sección era necesaria.
    if isinstance(df.columns, yf.MultiIndex):
        df.columns = df.columns.to_flat_index() 
    
    # Aseguramos que las columnas se llamen 'Close', etc. sin tuplas.
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    # =======================================================
    
    if df.empty:
        return jsonify({'error': 'No data found'}), 400

    # Estrategia de ejemplo (Aún es estática, pero ya debería funcionar)
    class TestStrategy(Strategy):
        
        # Parámetros por defecto para las SMAs
        ma1_period = 10 
        ma2_period = 50 

        def init(self):
            # Inicializar las medias móviles (SMA)
            self.ma1 = self.I(SMA, self.data.Close, self.ma1_period)
            self.ma2 = self.I(SMA, self.data.Close, self.ma2_period)

        def next(self):
            # Lógica de entrada/salida (la SMA 10 cruza la SMA 50)
            if crossover(self.ma1, self.ma2):
                self.buy()
            elif crossover(self.ma2, self.ma1):
                self.sell()

    # Ejecutar el backtest
    bt = Backtest(df, TestStrategy, cash=10000, commission=.002)
    stats = bt.run()

    # Devolver los resultados
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
    # Usar el puerto proporcionado por Render
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)