import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
import json
from datetime import datetime
import os


class HealthPredictionTrainer:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.disease_encoder = LabelEncoder()
        self.feature_names = []

    def create_sample_data(self):
        """Tạo dữ liệu mẫu cho training"""
        np.random.seed(datetime.now().second)

        # Tạo 1000 mẫu dữ liệu
        n_samples = 1000

        data = {
            "age": np.random.randint(5, 80, n_samples),
            "gender": np.random.choice([0, 1], n_samples),  # 0: female, 1: male
            "temperature": np.random.normal(37.0, 1.5, n_samples),  # body temp
            "fever": np.random.choice([0, 1], n_samples),
            "cough": np.random.choice([0, 1], n_samples),
            "headache": np.random.choice([0, 1], n_samples),
            "sore_throat": np.random.choice([0, 1], n_samples),
            "runny_nose": np.random.choice([0, 1], n_samples),
            "fatigue": np.random.choice([0, 1], n_samples),
            "body_aches": np.random.choice([0, 1], n_samples),
            # Weather features
            "weather_temp": np.random.normal(25, 10, n_samples),  # celsius
            "humidity": np.random.randint(30, 95, n_samples),  # %
            "air_quality": np.random.randint(1, 5, n_samples),  # 1-5 scale
            "season": np.random.randint(0, 4, n_samples),  # 0-3 for seasons
            "month": np.random.randint(1, 13, n_samples),
            # Location/travel
            "recent_travel": np.random.choice([0, 1], n_samples),
            "contact_sick": np.random.choice([0, 1], n_samples),
        }

        df = pd.DataFrame(data)

        # Tạo labels (diseases) dựa trên logic đơn giản
        diseases = []
        for i in range(n_samples):
            # Common Cold - nhiều khi có cough + runny_nose + cold weather
            if (
                df.iloc[i]["cough"]
                and df.iloc[i]["runny_nose"]
                and df.iloc[i]["weather_temp"] < 15
            ):
                diseases.append("Common Cold")

            # Flu - fever + body_aches + fatigue
            elif (
                df.iloc[i]["fever"]
                and df.iloc[i]["body_aches"]
                and df.iloc[i]["fatigue"]
            ):
                diseases.append("Seasonal Flu")

            # Allergic Rhinitis - runny_nose + season spring/summer + bad air quality
            elif (
                df.iloc[i]["runny_nose"]
                and df.iloc[i]["season"] in [1, 2]
                and df.iloc[i]["air_quality"] >= 3
            ):
                diseases.append("Allergic Rhinitis")

            # Heat Exhaustion - high temp + fatigue + hot weather
            elif (
                df.iloc[i]["fatigue"]
                and df.iloc[i]["weather_temp"] > 35
                and df.iloc[i]["headache"]
            ):
                diseases.append("Heat Exhaustion")

            # Gastroenteritis - random assignment for remaining
            elif np.random.random() < 0.2:
                diseases.append("Gastroenteritis")

            else:
                diseases.append("Healthy")

        df["disease"] = diseases

        print(f"✅ Created {n_samples} training samples")
        print(f"Disease distribution:")
        print(df["disease"].value_counts())

        return df

    def prepare_features(self, df):
        """Chuẩn bị features để training"""
        # Lấy feature columns (loại bỏ target)
        feature_cols = [col for col in df.columns if col != "disease"]
        X = df[feature_cols]
        y = df["disease"]

        # Encode target labels
        y_encoded = self.disease_encoder.fit_transform(y)

        # Lưu feature names
        self.feature_names = feature_cols

        return X, y_encoded, y

    def train(self, data_file=None):
        """Train mô hình"""
        print("🤖 Starting model training...")

        if data_file and os.path.exists(data_file):
            print(f"📁 Loading data from {data_file}")
            df = pd.read_csv(data_file)
        else:
            print("📊 Creating sample data...")
            df = self.create_sample_data()
            # Save sample data
            os.makedirs("data", exist_ok=True)
            df.to_csv("data/health_data_sample.csv", index=False)
            print("💾 Sample data saved to data/health_data_sample.csv")

        # Prepare features
        X, y_encoded, y_original = self.prepare_features(df)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        print("🎯 Training Random Forest model...")
        self.model = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42, class_weight="balanced"
        )

        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)

        # Cross validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)

        print(f"\n📈 Training Results:")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"CV Score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

        # Feature importance
        feature_importance = dict(
            zip(self.feature_names, self.model.feature_importances_)
        )
        sorted_features = sorted(
            feature_importance.items(), key=lambda x: x[1], reverse=True
        )

        print(f"\n🔍 Top 5 Important Features:")
        for feature, importance in sorted_features[:5]:
            print(f"  {feature}: {importance:.4f}")

        # Classification report
        print(f"\n📊 Detailed Classification Report:")
        disease_names = self.disease_encoder.classes_
        print(classification_report(y_test, y_pred, target_names=disease_names))

        return accuracy, cv_scores.mean()

    def save_model(self, filename=None):
        """Lưu mô hình đã train"""
        if filename is None:
            filename = "data/health_prediction_model.pkl"

        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "disease_encoder": self.disease_encoder,
            "feature_names": self.feature_names,
            "trained_at": datetime.now().isoformat(),
            "model_type": "RandomForestClassifier",
        }

        joblib.dump(model_data, filename)
        print(f"💾 Model saved to {filename}")

    def load_model(self, filename="data/health_prediction_model.pkl"):
        """Load mô hình đã train"""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Model file {filename} not found")

        model_data = joblib.load(filename)
        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.disease_encoder = model_data["disease_encoder"]
        self.feature_names = model_data["feature_names"]

        print(f"📂 Model loaded from {filename}")
        print(f"Trained at: {model_data.get('trained_at', 'Unknown')}")
        return model_data


def main():
    """Main training function"""
    print("🏥 Health Prediction Model Training")
    print("=" * 50)

    trainer = HealthPredictionTrainer()

    # Train model
    accuracy, cv_score = trainer.train()

    # Save model
    trainer.save_model()

    print("\n✅ Training completed successfully!")
    print(f"Final accuracy: {accuracy:.4f}")
    print(f"Cross-validation score: {cv_score:.4f}")

    # Test prediction với sample data
    print("\n🧪 Testing prediction with sample data...")
    sample_input = {
        "age": 25,
        "gender": 1,
        "temperature": 38.5,
        "fever": 1,
        "cough": 1,
        "headache": 0,
        "sore_throat": 1,
        "runny_nose": 0,
        "fatigue": 1,
        "body_aches": 1,
        "weather_temp": 20,
        "humidity": 65,
        "air_quality": 2,
        "season": 1,
        "month": 3,
        "recent_travel": 0,
        "contact_sick": 1,
    }

    # Create dataframe from sample
    sample_df = pd.DataFrame([sample_input])
    sample_scaled = trainer.scaler.transform(sample_df)
    prediction = trainer.model.predict(sample_scaled)
    probabilities = trainer.model.predict_proba(sample_scaled)[0]

    predicted_disease = trainer.disease_encoder.inverse_transform(prediction)[0]

    print(f"Sample prediction: {predicted_disease}")
    print("Probabilities for all diseases:")
    for i, disease in enumerate(trainer.disease_encoder.classes_):
        print(f"  {disease}: {probabilities[i]:.4f}")


if __name__ == "__main__":
    main()
