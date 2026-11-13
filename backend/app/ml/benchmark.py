from __future__ import annotations

from collections.abc import Sequence
import math
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from app.schemas import PriceBar

def _features(bars: Sequence[PriceBar]) -> pd.DataFrame:
    ordered = sorted(bars, key=lambda item: item.trading_date)
    frame = pd.DataFrame({
        "date": [bar.trading_date for bar in ordered],
        "close": [bar.adjusted_close if bar.adjusted_close is not None else bar.close for bar in ordered],
        "raw_close": [bar.close for bar in ordered],
        "open": [bar.open for bar in ordered],
        "high": [bar.high for bar in ordered],
        "low": [bar.low for bar in ordered],
        "volume": [bar.volume for bar in ordered],
    }).drop_duplicates("date").sort_values("date").set_index("date")
    close = frame["close"].astype(float)
    returns = close.pct_change()
    features = pd.DataFrame(index=frame.index)
    for period in (1, 5, 10, 20):
        features[f"return_{period}d"] = close.pct_change(period)
    for window in (10, 20):
        features[f"volatility_{window}d"] = returns.rolling(window).std()
    for window in (20, 50, 200):
        features[f"price_to_sma_{window}"] = close / close.rolling(window).mean() - 1
    delta = close.diff()
    average_gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    average_loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rs = average_gain / average_loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    rsi = rsi.mask((average_loss == 0) & (average_gain > 0), 100)
    features["rsi_14"] = rsi
    features["intraday_range"] = (frame["high"] - frame["low"]) / frame["raw_close"].replace(0, np.nan)
    features["overnight_gap"] = frame["open"] / frame["raw_close"].shift(1) - 1
    features["volume_change_1d"] = frame["volume"].pct_change()
    features["volume_ratio_20d"] = frame["volume"] / frame["volume"].rolling(20).mean()
    return features.replace([np.inf, -np.inf], np.nan)

def _pipeline(model, *, scale: bool = False) -> Pipeline:
    steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("model", model))
    return Pipeline(steps)

def benchmark_forward_returns(
    bars: Sequence[PriceBar], *, horizon_days: int = 5, n_splits: int = 4, test_size: int = 30
) -> dict:
    if horizon_days not in (5, 20, 60):
        raise ValueError("horizon_days must be one of 5, 20 or 60")
    features = _features(bars)
    close = pd.Series(
        [bar.adjusted_close if bar.adjusted_close is not None else bar.close for bar in sorted(bars, key=lambda item: item.trading_date)],
        index=[bar.trading_date for bar in sorted(bars, key=lambda item: item.trading_date)],
        dtype=float,
    )
    close = close[~close.index.duplicated(keep="last")].sort_index()
    target = close.shift(-horizon_days) / close - 1
    dataset = features.join(target.rename("target")).dropna()
    minimum = 100 + n_splits * test_size + n_splits * horizon_days
    if len(dataset) < minimum:
        raise ValueError(
            f"Not enough clean observations for a leakage-aware benchmark: need at least {minimum}, got {len(dataset)}. Increase lookback_days."
        )
    X = dataset.drop(columns=["target"])
    y = dataset["target"]
    latest_features = features.dropna().tail(1)
    if latest_features.empty:
        raise ValueError("Could not construct the latest feature row")

    models = {
        "ridge": _pipeline(Ridge(alpha=1.0), scale=True),
        "random_forest": _pipeline(RandomForestRegressor(
            n_estimators=120, min_samples_leaf=3, max_features=0.8, random_state=42, n_jobs=-1
        )),
        "extra_trees": _pipeline(ExtraTreesRegressor(
            n_estimators=120, min_samples_leaf=3, max_features=0.8, random_state=42, n_jobs=-1
        )),
        "hist_gradient_boosting": _pipeline(HistGradientBoostingRegressor(
            max_iter=120, max_leaf_nodes=15, l2_regularization=1.0, random_state=42
        )),
    }
    splitter = TimeSeriesSplit(n_splits=n_splits, test_size=test_size, gap=horizon_days)
    out_of_sample_actual = []
    for _, test_idx in splitter.split(X):
        out_of_sample_actual.extend(y.iloc[test_idx].to_numpy().tolist())
    baseline_mae = float(mean_absolute_error(out_of_sample_actual, np.zeros(len(out_of_sample_actual))))

    scores = []
    for name, pipeline in models.items():
        actual_all, predicted_all = [], []
        fold_scores = []
        for train_idx, test_idx in splitter.split(X):
            pipeline.fit(X.iloc[train_idx], y.iloc[train_idx])
            predicted = pipeline.predict(X.iloc[test_idx])
            actual = y.iloc[test_idx].to_numpy()
            actual_all.extend(actual.tolist())
            predicted_all.extend(predicted.tolist())
            fold_scores.append({
                "mae": float(mean_absolute_error(actual, predicted)),
                "rmse": float(math.sqrt(mean_squared_error(actual, predicted))),
            })
        actual_array = np.asarray(actual_all)
        predicted_array = np.asarray(predicted_all)
        scores.append({
            "model": name,
            "mae": float(mean_absolute_error(actual_array, predicted_array)),
            "rmse": float(math.sqrt(mean_squared_error(actual_array, predicted_array))),
            "directional_accuracy": float(np.mean(np.sign(actual_array) == np.sign(predicted_array))),
            "out_of_sample_r2": float(r2_score(actual_array, predicted_array)),
            "fold_metrics": fold_scores,
            "out_of_sample_predictions": int(len(actual_array)),
        })
    scores.sort(key=lambda row: row["mae"])
    selected = scores[0]
    if selected["mae"] >= baseline_mae:
        selected_name = "zero_return_baseline"
        predicted_return = 0.0
    else:
        selected_name = selected["model"]
        models[selected_name].fit(X, y)
        predicted_return = float(models[selected_name].predict(latest_features)[0])
    return {
        "horizon_trading_days": horizon_days,
        "as_of": features.dropna().index[-1].isoformat(),
        "training_observations": int(len(dataset)),
        "feature_count": int(X.shape[1]),
        "validation": {
            "method": "Expanding-window TimeSeriesSplit",
            "folds": n_splits,
            "test_size_per_fold": test_size,
            "purge_gap_trading_days": horizon_days,
            "selection_metric": "lowest out-of-sample MAE, only if better than zero-return baseline",
        },
        "zero_return_baseline_mae": baseline_mae,
        "model_scores": scores,
        "selected_model": selected_name,
        "predicted_forward_return": predicted_return,
        "predicted_forward_return_pct": predicted_return * 100,
        "disclaimer": "Experimental historical model estimate, not a forecast guarantee or investment recommendation. Backtest results do not include transaction costs or slippage.",
    }
