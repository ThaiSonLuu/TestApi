"""
Health Predictor Server - Main Application
=========================================
Chương trình chính với menu tương tác để quản lý database
"""

import sys
import os

# Thêm src vào path để import được modules
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.database import connect, disconnect, get_connection_status, insert_model_info


def display_menu():
    """Hiển thị menu chính"""
    print("\n" + "=" * 50)
    print("🏥 HEALTH PREDICTOR SERVER - MENU CHÍNH")
    print("=" * 50)
    print(f"📊 Trạng thái database: {get_connection_status()}")
    print("-" * 50)
    print("1. Kết nối/Ngắt kết nối Database")
    print("2. Insert bản ghi Model Info")
    print("0. Thoát chương trình")
    print("-" * 50)


def handle_database_connection():
    """Xử lý kết nối/ngắt kết nối database"""
    status = get_connection_status()

    if status == "Đang kết nối":
        print("\n🔌 Database đang kết nối. Bạn có muốn ngắt kết nối không?")
        choice = input("Nhập 'y' để ngắt kết nối, 'n' để hủy: ").lower().strip()
        if choice == "y":
            if disconnect():
                print("✅ Đã ngắt kết nối database thành công!")
            else:
                print("❌ Có lỗi khi ngắt kết nối database!")
        else:
            print("⏭️  Hủy thao tác ngắt kết nối")
    else:
        print("\n🔗 Database chưa kết nối. Đang thực hiện kết nối...")
        if connect():
            print("✅ Kết nối database thành công!")
        else:
            print("❌ Kết nối database thất bại!")


def handle_insert_model_info():
    """Xử lý insert bản ghi model info"""
    if get_connection_status() != "Đang kết nối":
        print("❌ Database chưa được kết nối! Vui lòng kết nối database trước.")
        return

    print("\n📝 NHẬP THÔNG TIN MODEL")
    print("-" * 30)

    try:
        # Input model information
        model_name = input("Tên model: ").strip()
        if not model_name:
            print("❌ Tên model không được để trống!")
            return

        model_version = input("Phiên bản model (ví dụ: 1.0.0): ").strip()
        if not model_version:
            model_version = "1.0.0"

        accuracy_str = input("Độ chính xác (0-1, ví dụ: 0.85): ").strip()
        try:
            accuracy = float(accuracy_str)
            if accuracy < 0 or accuracy > 1:
                print("❌ Độ chính xác phải từ 0 đến 1!")
                return
        except ValueError:
            print("❌ Độ chính xác phải là số!")
            return

        cv_score_str = input("CV Score (0-1, ví dụ: 0.82): ").strip()
        try:
            cv_score = float(cv_score_str)
            if cv_score < 0 or cv_score > 1:
                print("❌ CV Score phải từ 0 đến 1!")
                return
        except ValueError:
            print("❌ CV Score phải là số!")
            return

        model_file_path = input(
            "Đường dẫn file model (ví dụ: data/model.pkl): "
        ).strip()
        if not model_file_path:
            model_file_path = "data/health_prediction_model.pkl"

        feature_names_str = input(
            "Tên features (cách nhau bởi dấu phẩy, có thể bỏ trống): "
        ).strip()
        feature_names = None
        if feature_names_str:
            feature_names = [name.strip() for name in feature_names_str.split(",")]

        # Confirm before insert
        print(f"\n📋 XÁC NHẬN THÔNG TIN:")
        print(f"  Tên model: {model_name}")
        print(f"  Phiên bản: {model_version}")
        print(f"  Độ chính xác: {accuracy}")
        print(f"  CV Score: {cv_score}")
        print(f"  File path: {model_file_path}")
        print(f"  Features: {feature_names}")

        confirm = input("\nXác nhận insert? (y/n): ").lower().strip()
        if confirm != "y":
            print("⏭️  Hủy thao tác insert")
            return

        # Insert to database
        print("\n🔄 Đang insert vào database...")
        if insert_model_info(
            model_name,
            model_version,
            accuracy,
            cv_score,
            model_file_path,
            feature_names,
        ):
            print("✅ Insert model info thành công!")
        else:
            print("❌ Insert model info thất bại!")

    except KeyboardInterrupt:
        print("\n⚠️  Hủy thao tác insert")
    except Exception as e:
        print(f"\n❌ Có lỗi xảy ra: {e}")


def main():
    """Hàm main chính"""
    print("🚀 Khởi động Health Predictor Server...")

    while True:
        try:
            display_menu()
            choice = input("\n👉 Nhập lựa chọn của bạn: ").strip()

            if choice == "0":
                print("\n👋 Đang thoát chương trình...")
                # Ngắt kết nối database trước khi thoát (nếu đang kết nối)
                if get_connection_status() == "Đang kết nối":
                    print("🔌 Ngắt kết nối database trước khi thoát...")
                    disconnect()
                print("✅ Thoát chương trình thành công!")
                break

            elif choice == "1":
                handle_database_connection()

            elif choice == "2":
                handle_insert_model_info()

            else:
                print("❌ Lựa chọn không hợp lệ! Vui lòng chọn 0, 1 hoặc 2.")

        except KeyboardInterrupt:
            print("\n\n⚠️  Phát hiện Ctrl+C - Đang thoát chương trình...")
            if get_connection_status() == "Đang kết nối":
                print("🔌 Ngắt kết nối database...")
                disconnect()
            print("👋 Tạm biệt!")
            break

        except Exception as e:
            print(f"\n❌ Có lỗi xảy ra: {e}")
            print("🔄 Chương trình sẽ tiếp tục...")


if __name__ == "__main__":
    main()
