import psycopg2
import logging
import random
import enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_CONFIG = {
    "host": "localhost",
    "port": 2510,
    "database": "health_predictor",
    "user": "health_predictor_user",
    "password": "health_predictor_password",
}


class ConnectionStatus(enum.Enum):
    NOT_CONNECTED = "Not connected"
    DISCONNECTED = "Disconnected"
    CONNECTED = "Connected"


class DatabaseClient:
    connection = None

    @staticmethod
    def connect():
        try:
            if DatabaseClient.connection is None or DatabaseClient.connection.closed:
                DatabaseClient.connection = psycopg2.connect(
                    host=DATABASE_CONFIG["host"],
                    port=DATABASE_CONFIG["port"],
                    database=DATABASE_CONFIG["database"],
                    user=DATABASE_CONFIG["user"],
                    password=DATABASE_CONFIG["password"],
                )
                return True
        except psycopg2.Error as e:
            logger.error(f"Error connecting to database: {e}")
            return False

    @staticmethod
    def disconnect():
        try:
            if DatabaseClient.connection and not DatabaseClient.connection.closed:
                DatabaseClient.connection.close()
                DatabaseClient.connection = None
                return True
            else:
                return True
        except psycopg2.Error as e:
            logger.error(f"Error disconnecting from database: {e}")
            return False

    @staticmethod
    def get_connection_status():
        if DatabaseClient.connection is None:
            return ConnectionStatus.NOT_CONNECTED
        elif DatabaseClient.connection.closed:
            return ConnectionStatus.DISCONNECTED
        else:
            return ConnectionStatus.CONNECTED
