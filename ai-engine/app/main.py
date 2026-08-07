from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
import statistics
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from statsmodels.tsa.arima.model import ARIMA
import warnings
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


app = FastAPI(title="StockSense AI Engine")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="StockSense AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ai-engine"}


class SalesDataPoint(BaseModel):
    date: str
    quantity: int


class ForecastRequest(BaseModel):
    product_sku: str
    history: List[SalesDataPoint]
    forecast_days: int = 30


@app.post("/forecast")
def forecast_demand(request: ForecastRequest):
    if len(request.history) < 2:
        return {
            "product_sku": request.product_sku,
            "error": "Not enough historical data to forecast. Need at least 2 data points.",
            "data_points_provided": len(request.history),
            "model_used": "none",
        }

    quantities = [point.quantity for point in request.history]
    avg_daily_demand = statistics.mean(quantities)
    std_dev = statistics.stdev(quantities) if len(quantities) > 1 else 0

    last_date = max(datetime.strptime(p.date, "%Y-%m-%d") for p in request.history)

    predictions = []
    for i in range(1, request.forecast_days + 1):
        forecast_date = last_date + timedelta(days=i)
        predictions.append({
            "date": forecast_date.strftime("%Y-%m-%d"),
            "predicted_quantity": round(avg_daily_demand, 1),
            "lower_bound": max(0, round(avg_daily_demand - std_dev, 1)),
            "upper_bound": round(avg_daily_demand + std_dev, 1),
        })

    return {
        "product_sku": request.product_sku,
        "data_points_used": len(request.history),
        "forecast_days": request.forecast_days,
        "model_used": "moving_average_baseline",
        "note": "This is a simple baseline forecast. Prophet/ARIMA/XGBoost models are planned once more historical sales data accumulates and the Windows build environment is resolved.",
        "predictions": predictions,
    }


@app.post("/forecast/random-forest")
def forecast_random_forest(request: ForecastRequest):
    if len(request.history) < 5:
        return {
            "product_sku": request.product_sku,
            "error": "Random Forest needs at least 5 data points to train meaningfully.",
            "data_points_provided": len(request.history),
            "model_used": "none",
        }

    sorted_history = sorted(request.history, key=lambda p: p.date)
    quantities = [p.quantity for p in sorted_history]

    # Feature: day index (0, 1, 2, ...) — simple time-based feature
    X = np.array(range(len(quantities))).reshape(-1, 1)
    y = np.array(quantities)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    last_date = datetime.strptime(sorted_history[-1].date, "%Y-%m-%d")
    last_index = len(quantities) - 1

    predictions = []
    for i in range(1, request.forecast_days + 1):
        forecast_date = last_date + timedelta(days=i)
        future_index = np.array([[last_index + i]])
        predicted = model.predict(future_index)[0]

        # Get prediction spread across individual trees for a rough confidence band
        tree_predictions = [tree.predict(future_index)[0] for tree in model.estimators_]
        lower = max(0, np.percentile(tree_predictions, 10))
        upper = np.percentile(tree_predictions, 90)

        predictions.append({
            "date": forecast_date.strftime("%Y-%m-%d"),
            "predicted_quantity": round(max(0, predicted), 1),
            "lower_bound": round(lower, 1),
            "upper_bound": round(upper, 1),
        })

    return {
        "product_sku": request.product_sku,
        "data_points_used": len(request.history),
        "forecast_days": request.forecast_days,
        "model_used": "random_forest",
        "predictions": predictions,
    }
    
@app.post("/forecast/xgboost")
def forecast_xgboost(request: ForecastRequest):
    if len(request.history) < 5:
        return {
            "product_sku": request.product_sku,
            "error": "XGBoost needs at least 5 data points to train meaningfully.",
            "data_points_provided": len(request.history),
            "model_used": "none",
        }

    sorted_history = sorted(request.history, key=lambda p: p.date)
    quantities = [p.quantity for p in sorted_history]

    X = np.array(range(len(quantities))).reshape(-1, 1)
    y = np.array(quantities)

    model = XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
    model.fit(X, y)

    last_date = datetime.strptime(sorted_history[-1].date, "%Y-%m-%d")
    last_index = len(quantities) - 1

    predictions = []
    for i in range(1, request.forecast_days + 1):
        forecast_date = last_date + timedelta(days=i)
        future_index = np.array([[last_index + i]])
        predicted = model.predict(future_index)[0]

        predictions.append({
            "date": forecast_date.strftime("%Y-%m-%d"),
            "predicted_quantity": round(max(0, float(predicted)), 1),
        })

    return {
        "product_sku": request.product_sku,
        "data_points_used": len(request.history),
        "forecast_days": request.forecast_days,
        "model_used": "xgboost",
        "predictions": predictions,
    }
    
@app.post("/forecast/arima")
def forecast_arima(request: ForecastRequest):
    if len(request.history) < 8:
        return {
            "product_sku": request.product_sku,
            "error": "ARIMA needs at least 8 data points to fit a meaningful model.",
            "data_points_provided": len(request.history),
            "model_used": "none",
        }

    sorted_history = sorted(request.history, key=lambda p: p.date)
    quantities = [float(p.quantity) for p in sorted_history]
    last_date = datetime.strptime(sorted_history[-1].date, "%Y-%m-%d")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # (p,d,q) = (1,1,1): a simple, generally stable starting configuration —
            # 1 autoregressive term, 1 differencing pass to handle trend, 1 moving-average term
            model = ARIMA(quantities, order=(1, 1, 1))
            fitted = model.fit()
            forecast_result = fitted.get_forecast(steps=request.forecast_days)
            mean_forecast = forecast_result.predicted_mean
            conf_int = forecast_result.conf_int(alpha=0.2)  # 80% confidence interval
    except Exception as e:
        return {
            "product_sku": request.product_sku,
            "error": f"ARIMA failed to fit this data: {str(e)}",
            "model_used": "none",
        }

    predictions = []
    for i in range(request.forecast_days):
        forecast_date = last_date + timedelta(days=i + 1)
        predictions.append({
            "date": forecast_date.strftime("%Y-%m-%d"),
            "predicted_quantity": round(max(0, float(mean_forecast[i])), 1),
            "lower_bound": round(max(0, float(conf_int[i][0])), 1),
            "upper_bound": round(max(0, float(conf_int[i][1])), 1),
        })

    return {
        "product_sku": request.product_sku,
        "data_points_used": len(request.history),
        "forecast_days": request.forecast_days,
        "model_used": "arima",
        "order_used": "(1,1,1)",
        "predictions": predictions,
    }


class VendorMetrics(BaseModel):
    vendor_id: int
    vendor_name: str
    on_time_rate: float  # 0-100
    average_lead_time_days: float
    total_orders: int


class VendorClusterRequest(BaseModel):
    vendors: List[VendorMetrics]
    n_clusters: int = 3


@app.post("/vendor-clusters")
def cluster_vendors(request: VendorClusterRequest):
    if len(request.vendors) < request.n_clusters:
        return {
            "error": f"Need at least {request.n_clusters} vendors to form {request.n_clusters} clusters.",
            "vendors_provided": len(request.vendors),
        }

    features = np.array([
        [v.on_time_rate, v.average_lead_time_days, v.total_orders]
        for v in request.vendors
    ])

    # Scale features so lead-time-days and order-count don't dominate
    # on_time_rate just because their raw numbers are bigger
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=request.n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(scaled_features)

    # Rank clusters by their average on_time_rate, so cluster 0 = best tier
    cluster_avg_performance = {}
    for cluster_id in set(cluster_labels):
        members = [request.vendors[i] for i in range(len(request.vendors)) if cluster_labels[i] == cluster_id]
        avg_on_time = sum(m.on_time_rate for m in members) / len(members)
        cluster_avg_performance[cluster_id] = avg_on_time

    ranked_clusters = sorted(cluster_avg_performance, key=cluster_avg_performance.get, reverse=True)
    tier_names = ["Top Tier", "Mid Tier", "Needs Improvement", "Lowest Tier"]
    cluster_to_tier = {
        cluster_id: tier_names[i] if i < len(tier_names) else f"Tier {i+1}"
        for i, cluster_id in enumerate(ranked_clusters)
    }

    results = []
    for i, vendor in enumerate(request.vendors):
        cluster_id = int(cluster_labels[i])
        results.append({
            "vendor_id": vendor.vendor_id,
            "vendor_name": vendor.vendor_name,
            "cluster": cluster_id,
            "tier": cluster_to_tier[cluster_id],
            "on_time_rate": vendor.on_time_rate,
            "average_lead_time_days": vendor.average_lead_time_days,
        })

    return {
        "n_clusters": request.n_clusters,
        "vendors": results,
    }
    
    
def calculate_mape(actual, predicted):
    """Mean Absolute Percentage Error — lower is better. Skips zero-actual points to avoid divide-by-zero."""
    errors = []
    for a, p in zip(actual, predicted):
        if a != 0:
            errors.append(abs((a - p) / a))
    return (sum(errors) / len(errors) * 100) if errors else None


def calculate_rmse(actual, predicted):
    """Root Mean Squared Error — lower is better, penalizes large misses more than small ones."""
    squared_errors = [(a - p) ** 2 for a, p in zip(actual, predicted)]
    return (sum(squared_errors) / len(squared_errors)) ** 0.5


def run_model_on_history(model_name, train_quantities, test_length):
    """Trains a given model on train_quantities and returns test_length predictions."""
    X = np.array(range(len(train_quantities))).reshape(-1, 1)
    y = np.array(train_quantities)
    last_index = len(train_quantities) - 1
    future_X = np.array([[last_index + i] for i in range(1, test_length + 1)])

    if model_name == "moving_average":
        avg = statistics.mean(train_quantities)
        return [avg] * test_length

    elif model_name == "random_forest":
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        return [float(v) for v in model.predict(future_X)]

    elif model_name == "xgboost":
        model = XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
        model.fit(X, y)
        return [float(v) for v in model.predict(future_X)]

    elif model_name == "arima":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = ARIMA(train_quantities, order=(1, 1, 1))
            fitted = model.fit()
            return [float(v) for v in fitted.get_forecast(steps=test_length).predicted_mean]

    return None


class ModelSelectionRequest(BaseModel):
    product_sku: str
    history: List[SalesDataPoint]
    test_size: int = 3


@app.post("/select-best-model")
def select_best_model(request: ModelSelectionRequest):
    min_required = request.test_size + 8  # need enough left over to train ARIMA after holding out test data
    if len(request.history) < min_required:
        return {
            "product_sku": request.product_sku,
            "error": f"Need at least {min_required} data points to backtest fairly (train + {request.test_size}-point holdout).",
            "data_points_provided": len(request.history),
        }

    sorted_history = sorted(request.history, key=lambda p: p.date)
    quantities = [float(p.quantity) for p in sorted_history]

    train = quantities[:-request.test_size]
    test = quantities[-request.test_size:]

    candidates = ["moving_average", "random_forest", "xgboost", "arima"]
    results = []

    for model_name in candidates:
        try:
            predictions = run_model_on_history(model_name, train, len(test))
            mape = calculate_mape(test, predictions)
            rmse = calculate_rmse(test, predictions)
            results.append({
                "model": model_name,
                "mape_percent": round(mape, 2) if mape is not None else None,
                "rmse": round(rmse, 2),
            })
        except Exception as e:
            results.append({"model": model_name, "error": str(e)})

    valid_results = [r for r in results if "rmse" in r]
    best_model = min(valid_results, key=lambda r: r["rmse"]) if valid_results else None

    return {
        "product_sku": request.product_sku,
        "test_size": request.test_size,
        "training_points": len(train),
        "model_comparison": results,
        "recommended_model": best_model["model"] if best_model else None,
    }
    
class ReorderRecommendationRequest(BaseModel):
    product_sku: str
    history: List[SalesDataPoint]
    current_stock: int
    reorder_level: int
    vendor_lead_time_days: int
    safety_stock_days: int = 7



@app.post("/recommend-reorder")
def recommend_reorder(request: ReorderRecommendationRequest):
    sorted_history = sorted(request.history, key=lambda p: p.date)

    # Detect the real interval between data points (e.g. daily vs weekly sales records)
    if len(sorted_history) >= 2:
        d1 = datetime.strptime(sorted_history[0].date, "%Y-%m-%d")
        d2 = datetime.strptime(sorted_history[1].date, "%Y-%m-%d")
        interval_days = max(1, (d2 - d1).days)
    else:
        interval_days = 1

    forecast_window_days = request.vendor_lead_time_days + request.safety_stock_days
    forecast_steps = max(1, round(forecast_window_days / interval_days))

    if len(request.history) >= 8:
        forecast_response = forecast_arima(ForecastRequest(
            product_sku=request.product_sku, history=request.history, forecast_days=forecast_steps,
        ))
        model_used = forecast_response.get("model_used", "arima")
    elif len(request.history) >= 5:
        forecast_response = forecast_random_forest(ForecastRequest(
            product_sku=request.product_sku, history=request.history, forecast_days=forecast_steps,
        ))
        model_used = forecast_response.get("model_used", "random_forest")
    elif len(request.history) >= 2:
        forecast_response = forecast_demand(ForecastRequest(
            product_sku=request.product_sku, history=request.history, forecast_days=forecast_steps,
        ))
        model_used = forecast_response.get("model_used", "moving_average_baseline")
    else:
        return {"product_sku": request.product_sku, "error": "Not enough sales history to forecast demand.", "data_points_provided": len(request.history)}

    if "error" in forecast_response:
        return {"product_sku": request.product_sku, "error": forecast_response["error"]}

    predicted_demand_over_window = sum(p["predicted_quantity"] for p in forecast_response["predictions"])

    lead_time_steps = max(1, round(request.vendor_lead_time_days / interval_days))
    projected_stock_at_delivery = request.current_stock - sum(
        p["predicted_quantity"] for p in forecast_response["predictions"][:lead_time_steps]
    )

    recommended_order_quantity = max(0, round(predicted_demand_over_window - request.current_stock + request.reorder_level))
    should_reorder_now = projected_stock_at_delivery <= request.reorder_level

    return {
        "product_sku": request.product_sku,
        "model_used": model_used,
        "detected_data_interval_days": interval_days,
        "current_stock": request.current_stock,
        "reorder_level": request.reorder_level,
        "vendor_lead_time_days": request.vendor_lead_time_days,
        "predicted_demand_during_lead_time_and_buffer": round(predicted_demand_over_window, 1),
        "projected_stock_at_delivery_date": round(projected_stock_at_delivery, 1),
        "should_reorder_now": should_reorder_now,
        "recommended_order_quantity": recommended_order_quantity,
        "reasoning": (
            f"Sales data appears to be recorded roughly every {interval_days} day(s). "
            f"Based on {model_used} forecast, expected demand over the next "
            f"{forecast_window_days} days (lead time + safety buffer) is "
            f"{round(predicted_demand_over_window, 1)} units. "
            f"With {request.current_stock} currently in stock, projected stock at "
            f"delivery is {round(projected_stock_at_delivery, 1)}, "
            f"{'below' if should_reorder_now else 'above'} the reorder level of {request.reorder_level}."
        ),
    }