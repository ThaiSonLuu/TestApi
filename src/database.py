"""
Database Handler
===============
Xử lý kết nối database đơn giản
"""

import psycopg2
import logging
from datetime import datetime
from .config import DATABASE_CONFIG

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global connection variable
connection = None

def connect():
    """Kết nối tới database"""
    global connection
    try:
        if connection is None or connection.closed:
            connection = psycopg2.connect(
                host=DATABASE_CONFIG["host"],
                port=DATABASE_CONFIG["port"],
                database=DATABASE_CONFIG["database"],
                user=DATABASE_CONFIG["user"],
                password=DATABASE_CONFIG["password"]
            )
            logger.info("✅ Kết nối database thành công!")
            return True
        else:
            logger.info("✅ Database đã được kết nối từ trước!")
            return True
    except psycopg2.Error as e:
        logger.error(f"❌ Lỗi kết nối database: {e}")
        return False

def disconnect():
    """Ngắt kết nối database"""
    global connection
    try:
        if connection and not connection.closed:
            connection.close()
            logger.info("🔌 Đã ngắt kết nối database")
            connection = None
            return True
        else:
            logger.info("🔌 Database chưa được kết nối")
            return True
    except psycopg2.Error as e:
        logger.error(f"❌ Lỗi ngắt kết nối database: {e}")
        return False

def get_connection_status():
    """Kiểm tra trạng thái kết nối"""
    global connection
    if connection is None:
        return "Chưa kết nối"
    elif connection.closed:
        return "Đã ngắt kết nối"
    else:
        return "Đang kết nối"

def insert_model_info(model_name, model_version, accuracy, cv_score, model_file_path, feature_names=None):
    """
    Insert bản ghi mới vào bảng model_info
    
    Args:
        model_name: Tên model
        model_version: Phiên bản model  
        accuracy: Độ chính xác
        cv_score: Cross validation score
        model_file_path: Đường dẫn file model
        feature_names: Danh sách tên features (optional)
    
    Returns:
        True if successful, False otherwise
    """
    global connection
    
    if connection is None or connection.closed:
        logger.error("❌ Database chưa được kết nối")
        return False
    
    try:
        with connection.cursor() as cursor:
            # Deactivate previous models
            cursor.execute("UPDATE model_info SET is_active = FALSE WHERE is_active = TRUE")
            
            # Insert new model info
            insert_query = """
            INSERT INTO model_info (model_name, model_version, accuracy, cv_score, 
                                  feature_names, model_file_path, is_active, trained_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            feature_names_json = str(feature_names) if feature_names else None
            
            cursor.execute(insert_query, (
                model_name, 
                model_version, 
                accuracy, 
                cv_score,
                feature_names_json, 
                model_file_path, 
                True,  # is_active
                datetime.now()
            ))
            
            model_id = cursor.fetchone()[0]
            connection.commit()
            
            logger.info(f"✅ Đã insert model info với ID: {model_id}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Lỗi insert model info: {e}")
        connection.rollback()
        return False 