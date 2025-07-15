import sys
import traceback
from flask import Flask, jsonify
from src.controller.user_controller import user_api
from src.controller.auth_controller import auth_api
from src.data.database.database import DatabaseClient

app = Flask(__name__)


# Kết nối database khi app khởi động
@app.before_request
def init_db():
    DatabaseClient.connect()


# Đăng ký blueprint cho user API
@app.route("/")
def home():
    return "Health predictor is running ..."


# Xử lý lỗi toàn cục
@app.errorhandler(Exception)
def handle_exception(e):
    traceback.print_exc(file=sys.stdout)
    code = getattr(e, "code", 500)
    message = str(e)
    return jsonify({"error_code": code, "error_message": message}), code


app.register_blueprint(user_api)
app.register_blueprint(auth_api)

if __name__ == "__main__":
    app.run(debug=True)
