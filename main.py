from fastapi import FastAPI
from pydantic import BaseModel
import yfinance as yf
import backtrader as bt
import pandas as pd
import json

app = FastAPI()

# --- Modelo de entrada ---
class StrategyData(BaseModel):
    type: str
    code: str | None = None
    rules: dict | None = None

# --- Estrategia básica para Backtrader ---
class SimpleStrategy(bt.Strategy):
    params = dict(period=14)

    def __init__(self):
        self.rsi = bt.indicators.RSI(period=self.params.period)

    def next(self):
        if not self.position:
            if self.rsi < 30:
                self.buy()
        else:
            if self.rsi > 70:
                self.sell()

@app.get("/")
def root():
    return {"message": "FastAPI Backtesting Service Ready 🚀"}

@app.post("/backtest")
def run_backtest(strategy: StrategyData):
    try:
        # Descarga datos de prueba (BTC-USD 2023)
        data = yf.download("BTC-USD", start="2023-01-01", end="2023-12-31")
        data_bt = bt.feeds.PandasData(dataname=data)

        cerebro = bt.Cerebro()
        cerebro.adddata(data_bt)
        cerebro.addstrategy(SimpleStrategy)
        cerebro.broker.set_cash(10000)
        cerebro.run()

        final_value = cerebro.broker.getvalue()
        profit = (final_value - 10000) / 10000 * 100

        # Resultados simulados
        result = {
            "profit_factor": round(1.5 + profit / 100, 2),
            "max_drawdown": round(15.0, 2),
            "num_trades": 50,
            "final_value": final_value,
        }
        return result
    except Exception as e:
        return {"error": str(e)}
