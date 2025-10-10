from flask import Flask, request, jsonify
import yfinance as yf
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA
import os 
import pandas as pd # Importar pandas

app = Flask(__name__)

@app.route('/backtest', methods=['POST'])
def backtest():
    try:
        data = request.get_json()
        rules = data.get('strategy', {})
        symbol = rules.get('symbol', 'BTC-USD')
        timeframe = rules.get('interval', '1h')

        # Descargar datos históricos
        df = yf.download(symbol, period='2y', interval=timeframe)
        
        if df.empty or len(df) < 50:
            return jsonify({'error': 'No data found or insufficient data retrieved for the requested period/symbol.'}), 400

        # =======================================================
        # === MANEJO DE COMPATIBILIDAD CON PANDAS/BACKTESTING ===
        # 1. Aplanar el MultiIndex si existe (soluciona el error anterior)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.to_flat_index() 
        
        # 2. Forzar los nombres de columnas a mayúsculas y asegurarse de que sean correctos
        # yfinance a veces devuelve nombres extraños, los normalizamos aquí.
        new_columns = []
        for col in df.columns:
            # Si la columna es una tupla (después de aplanar, a veces queda ('Close', '')), toma el primer elemento.
            col_name = col[0] if isinstance(col, tuple) else col
            # Usar solo la primera palabra y forzar mayúsculas (Open, High, Low, Close, Volume)
            new_columns.append(str(col_name).split(' ')[0].capitalize())
        
        df.columns = new_columns
        
        # 3. Seleccionar solo las 5 columnas requeridas por Backtesting.py
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            return jsonify({'error': f'Data must contain the required columns: {required_cols}. Found: {df.columns.tolist()}'}), 400
            
        df = df[required_cols]
        # =======================================================

        # Estrategia de ejemplo (Aún es estática)
        class TestStrategy(Strategy):
            ma1_period = 10 
            ma2_period = 50 

            def init(self):
                self.ma1 = self.I(SMA, self.data.Close, self.ma1_period)
                self.ma2 = self.I(SMA, self.data.Close, self.ma2_period)

            def next(self):
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

    except Exception as e:
        # Esto captura cualquier error que no sea un error 500 interno de Flask 
        # y lo muestra como un error 500 con detalle.
        app.logger.error(f"Error durante el backtest: {e}")
        return jsonify({'error': 'Internal server error during backtest execution.', 'details': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)