import sys
import traceback
import time
import os
from flask import Flask, jsonify, request, g
from src.controller.user_controller import user_api
from src.controller.auth_controller import auth_api
from src.controller.predict_controller import predict_api, health_predictor_instance
from src.data.database.database import DatabaseClient
from src.ml.train_model import HealthPredictionTrainer
from src.ml.predict import HealthPredictor

app = Flask(__name__)


# --- Logging Middleware ---
@app.before_request
def log_request_info():
    """Log incoming request details."""
    g.start_time = time.time()
    print("--- New Request ---")
    print(f"Endpoint: {request.method} {request.path}")
    body = request.get_json(silent=True)
    if body:
        print(f"Body: {body}")
    else:
        if request.form:
            print(f"Form Data: {dict(request.form)}")
        else:
            print("Body: (No JSON body or form data)")


@app.after_request
def log_response_info(response):
    """Log outgoing response details."""
    duration = time.time() - g.start_time
    print(f"Status: {response.status}")
    if response.content_type == "application/json":
        response_body = response.get_data(as_text=True)
        print(f"Response Body: {response_body[:500]}")
    else:
        print(f"Response Body: (Content-Type: {response.content_type})")
    print(f"Execution Time: {duration:.4f}s")
    print("--- Request End ---")
    return response


# --- Database and Model Initialization ---
MODEL_FILE_PATH = "data/health_prediction_model.pkl"

DatabaseClient.connect()

if not os.path.exists(MODEL_FILE_PATH):
    print(f"🤔 Model file not found at '{MODEL_FILE_PATH}'. Starting training...")
    try:
        trainer = HealthPredictionTrainer()
        trainer.train_model()
        print("✅ Initial model training completed successfully.")
    except Exception as e:
        print(f"❌ Initial model training failed: {e}")
        traceback.print_exc(file=sys.stdout)
else:
    print(f"✅ Model already exists at '{MODEL_FILE_PATH}'. Skipping training.")

# Load the model into the global instance
try:
    print("🧠 Loading model into global instance...")
    health_predictor_instance.load_model()
    print("✅ Model loaded successfully into global instance.")
except FileNotFoundError:
    print("⚠️ Model could not be loaded. The /predict endpoint will be unavailable.")


# --- Routes and Blueprints ---
@app.route("/")
def home():
    return "Health predictor is running ..."


@app.errorhandler(Exception)
def handle_exception(e):
    traceback.print_exc(file=sys.stdout)
    code = getattr(e, "code", 500)
    message = str(e)
    return jsonify({"error_code": code, "error_message": message}), code


app.register_blueprint(user_api)
app.register_blueprint(auth_api)
app.register_blueprint(predict_api)

if __name__ == "__main__":
    app.run(debug=True)
