from .train_model import HealthPredictionTrainer
from .predict import HealthPredictor
from .database import connect, disconnect, get_connection_status
from .config import DATABASE_CONFIG

__version__ = "1.0.0"
__author__ = "Health Prediction Team"

__all__ = [
    "HealthPredictionTrainer",
    "HealthPredictor",
    "connect",
    "disconnect",
    "get_connection_status",
    "DATABASE_CONFIG",
]
