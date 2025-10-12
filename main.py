from fastapi import FastAPI
from pydantic import BaseModel, field_validator
from typing import Any, Dict, List, Union
import yfinance as yf
import backtrader as bt
import pandas as pd

app = FastAPI()


@app.get("/")
def root():
    return {"message": "FastAPI Backtesting Service Ready 🚀"}


# ✅ Modelo con validador para evitar el error 'tuple' object has no attribute lower'
class StrategyData(BaseModel):
    type: Union[str, List[str], tuple]
    code: str | None = None
    rules: Dict[str, Any] | None = None

    @field_validator("type", mode="before")
    def ensure_str(cls, v):
        """Asegura que 'type' siempre sea string."""
        if isinstance(v, (list, tuple)):
            v = v[0]
        return str(v)


@app.post("/backtest")
def run_backtest(strategy: StrategyData):
    # 🔧 Normaliza el tipo
    strategy_type = strategy.type.lower() if isinstance(strategy.type, str) else "json"

    # 🔹 (Opcional) lógica diferente si es Pine Script o reglas JSON
    if strategy_type == "pine":
        print("▶ Ejecutando estrategia tipo Pine Script")
    else:
        print("▶ Ejecutando estrategia tipo JSON/rules")

    # === Simulación simple de backtest ===
    data = yf.download("BTC-USD", start="2023-01-01", end="2023-12-31")
    data_bt = bt.feeds.PandasData(dataname=data)

    cerebro = bt.Cerebro()
    cerebro.adddata(data_bt)
    cerebro.addstrategy(bt.Strategy)
    cerebro.broker.set_cash(10000)
    cerebro.run()

    final_value = cerebro.broker.getvalue()
    profit = (final_value - 10000) / 10000 * 100

    # === Devuelve métricas simuladas ===
    return {
        "profit_factor": round(1.5 + profit / 100, 2),
        "max_drawdown": 15.0,
        "num_trades": 50,
        "final_value": round(final_value, 2),
        "strategy_type": strategy_type,
    }
