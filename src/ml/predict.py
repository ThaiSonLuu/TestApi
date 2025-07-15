import pandas as pd
import numpy as np
import joblib
import json
import argparse
from datetime import datetime
from .train_model import HealthPredictionTrainer


class HealthPredictor:
    def __init__(self, model_file="data/health_prediction_model.pkl"):
        self.trainer = HealthPredictionTrainer()
        self.model_file = model_file
        self.load_model()

    def load_model(self):
        """Load model đã train"""
        try:
            self.model_data = self.trainer.load_model(self.model_file)
            print("✅ Model loaded successfully!")
        except FileNotFoundError:
            print(f"❌ Model file {self.model_file} not found!")
            print("Please run 'python train_model.py' first to train the model.")
            exit(1)

    def predict_single(self, patient_data):
        """Dự đoán cho 1 bệnh nhân"""
        # Tạo DataFrame từ input
        df = pd.DataFrame([patient_data])

        # Đảm bảo có đủ features
        for feature in self.trainer.feature_names:
            if feature not in df.columns:
                df[feature] = 0  # Default value

        # Sắp xếp columns theo thứ tự training
        df = df[self.trainer.feature_names]

        # Scale features
        X_scaled = self.trainer.scaler.transform(df)

        # Prediction
        prediction = self.trainer.model.predict(X_scaled)
        probabilities = self.trainer.model.predict_proba(X_scaled)[0]

        # Convert prediction back to disease name
        predicted_disease = self.trainer.disease_encoder.inverse_transform(prediction)[
            0
        ]
        max_probability = max(probabilities)

        # Get all probabilities
        all_probabilities = {}
        for i, disease in enumerate(self.trainer.disease_encoder.classes_):
            all_probabilities[disease] = float(probabilities[i])

        # Sort by probability
        sorted_probabilities = sorted(
            all_probabilities.items(), key=lambda x: x[1], reverse=True
        )

        result = {
            "predicted_disease": predicted_disease,
            "confidence": float(max_probability),
            "all_probabilities": all_probabilities,
            "top_3_predictions": sorted_probabilities[:3],
            "prediction_time": datetime.now().isoformat(),
        }

        return result

    def predict_batch(self, patients_data):
        """Dự đoán cho nhiều bệnh nhân"""
        results = []
        for i, patient in enumerate(patients_data):
            try:
                result = self.predict_single(patient)
                result["patient_id"] = i
                results.append(result)
            except Exception as e:
                print(f"Error predicting for patient {i}: {e}")
                results.append({"patient_id": i, "error": str(e)})
        return results

    def create_sample_patient(self):
        """Tạo dữ liệu bệnh nhân mẫu"""
        return {
            "age": 30,
            "gender": 1,  # 1 = male, 0 = female
            "temperature": 38.2,  # body temperature
            "fever": 1,  # có sốt
            "cough": 1,  # ho
            "headache": 0,  # không đau đầu
            "sore_throat": 1,  # đau họng
            "runny_nose": 0,  # không sổ mũi
            "fatigue": 1,  # mệt mỏi
            "body_aches": 1,  # đau nhức cơ thể
            "weather_temp": 22,  # nhiệt độ thời tiết
            "humidity": 70,  # độ ẩm %
            "air_quality": 3,  # chất lượng không khí 1-5
            "season": 1,  # mùa (0=winter, 1=spring, 2=summer, 3=fall)
            "month": 4,  # tháng
            "recent_travel": 0,  # không đi du lịch gần đây
            "contact_sick": 1,  # tiếp xúc với người bệnh
        }

    def interactive_input(self):
        """Nhập liệu tương tác"""
        print("\n🩺 Nhập thông tin bệnh nhân:")
        print("-" * 30)

        patient_data = {}

        # Basic info
        patient_data["age"] = int(input("Tuổi: "))
        gender = input("Giới tính (nam/nữ): ").lower()
        patient_data["gender"] = 1 if gender.startswith("nam") else 0

        # Symptoms
        print("\nTriệu chứng (y/n):")
        symptoms = [
            "fever",
            "cough",
            "headache",
            "sore_throat",
            "runny_nose",
            "fatigue",
            "body_aches",
        ]
        symptom_names = [
            "Sốt",
            "Ho",
            "Đau đầu",
            "Đau họng",
            "Sổ mũi",
            "Mệt mỏi",
            "Đau nhức cơ thể",
        ]

        for symptom, name in zip(symptoms, symptom_names):
            answer = input(f"{name}: ").lower()
            patient_data[symptom] = (
                1 if answer.startswith("y") or answer.startswith("c") else 0
            )

        # Body temperature
        temp = input("\nNhiệt độ cơ thể (°C, enter để bỏ qua): ")
        patient_data["temperature"] = float(temp) if temp else 37.0

        # Weather
        print("\nThông tin thời tiết:")
        weather_temp = input("Nhiệt độ thời tiết (°C): ")
        patient_data["weather_temp"] = float(weather_temp) if weather_temp else 25.0

        humidity = input("Độ ẩm (%): ")
        patient_data["humidity"] = int(humidity) if humidity else 60

        air_quality = input("Chất lượng không khí (1-5): ")
        patient_data["air_quality"] = int(air_quality) if air_quality else 2

        # Other info
        travel = input("\nĐi du lịch gần đây (y/n): ").lower()
        patient_data["recent_travel"] = (
            1 if travel.startswith("y") or travel.startswith("c") else 0
        )

        contact = input("Tiếp xúc với người bệnh (y/n): ").lower()
        patient_data["contact_sick"] = (
            1 if contact.startswith("y") or contact.startswith("c") else 0
        )

        # Season and month
        month = int(input("Tháng hiện tại (1-12): ") or datetime.now().month)
        patient_data["month"] = month

        # Convert month to season
        season_map = {
            12: 0,
            1: 0,
            2: 0,  # winter
            3: 1,
            4: 1,
            5: 1,  # spring
            6: 2,
            7: 2,
            8: 2,  # summer
            9: 3,
            10: 3,
            11: 3,
        }  # fall
        patient_data["season"] = season_map[month]

        return patient_data

    def predict(self):
        """Main prediction function"""
        parser = argparse.ArgumentParser(description="Health Prediction Service")
        parser.add_argument(
            "--model",
            default="data/health_prediction_model.pkl",
            help="Path to trained model file",
        )
        parser.add_argument(
            "--interactive", "-i", action="store_true", help="Interactive input mode"
        )
        parser.add_argument(
            "--sample", "-s", action="store_true", help="Use sample patient data"
        )
        parser.add_argument("--json", help="JSON file with patient data")

        args = parser.parse_args()

        print("🏥 Health Prediction Service")
        print("=" * 40)

        # Initialize predictor
        predictor = HealthPredictor(args.model)

        # Get patient data
        if args.interactive:
            patient_data = self.interactive_input()
        elif args.json:
            with open(args.json, "r") as f:
                patient_data = json.load(f)
        elif args.sample:
            patient_data = predictor.create_sample_patient()
            print("📋 Using sample patient data:")
            for key, value in patient_data.items():
                print(f"  {key}: {value}")
        else:
            print("⚠️  No input method specified. Using sample data.")
            patient_data = predictor.create_sample_patient()

        # Make prediction
        print(f"\n🔮 Making prediction...")
        result = predictor.predict_single(patient_data)

        # Display results
        print(f"\n📊 Prediction Results:")
        print(f"Predicted Disease: {result['predicted_disease']}")
        print(
            f"Confidence: {result['confidence']:.4f} ({result['confidence']*100:.1f}%)"
        )

        print(f"\n🏆 Top 3 Predictions:")
        for i, (disease, prob) in enumerate(result["top_3_predictions"], 1):
            print(f"  {i}. {disease}: {prob:.4f} ({prob*100:.1f}%)")

        print(f"\n⏰ Prediction Time: {result['prediction_time']}")

        # Save result
        result_file = (
            f"data/prediction_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(result_file, "w") as f:
            json.dump(
                {"input_data": patient_data, "prediction_result": result}, f, indent=2
            )

        print(f"💾 Result saved to {result_file}")
