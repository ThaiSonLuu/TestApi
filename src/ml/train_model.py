import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, hamming_loss
import joblib
from datetime import datetime
import os
import warnings
from ..data.dao.medical_record_dao import MedicalRecordDAO
from ..data.database.database import DatabaseClient

# Ignore warnings for labels with no predicted samples
warnings.filterwarnings(
    "ignore", category=UserWarning, module="sklearn.metrics._classification"
)


class HealthPredictionTrainer:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_columns = []
        self.feature_names = []

    def get_label_columns(self):
        """Gets the list of disease codes to identify label columns."""
        conn = DatabaseClient.connection
        try:
            diseases_df = pd.read_sql("SELECT code FROM diseases", conn)
            return diseases_df["code"].tolist()
        except Exception as e:
            print(f"❌ Error loading disease codes from database: {e}")
            return []

    def prepare_features_and_labels(self, df: pd.DataFrame):
        """Chuẩn bị features và labels cho multi-label training."""
        print("🔬 Preparing features and labels for multi-label training...")

        self.label_columns = self.get_label_columns()
        if not self.label_columns:
            print("❌ Could not determine label columns. Stopping.")
            return None, None

        # Ensure all potential label columns are in the DataFrame
        for col in self.label_columns:
            if col not in df.columns:
                df[col] = 0

        # Separate features (X) from labels (Y)
        self.feature_names = [
            col for col in df.columns if col not in self.label_columns
        ]
        X = df[self.feature_names]
        Y = df[self.label_columns]

        print(
            f"Identified {len(self.feature_names)} features and {len(self.label_columns)} labels."
        )
        return X, Y

    def _train(self):
        """Train mô hình multi-label."""
        print("🤖 Starting multi-label model training...")

        df = MedicalRecordDAO.get_training_data()

        if df is None or df.empty:
            print("❌ Training stopped due to lack of data.")
            return None, 0

        X, Y = self.prepare_features_and_labels(df)

        if X is None or Y.empty:
            print("❌ Training stopped due to feature/label preparation failure.")
            return None, 0

        # Split data (stratify is not supported for multi-label)
        X_train, X_test, y_train, y_test = train_test_split(
            X, Y, test_size=0.2, random_state=42
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        print("🎯 Training Random Forest model for multi-label classification...")
        self.model = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42, class_weight="balanced"
        )
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        subset_accuracy = accuracy_score(y_test, y_pred)
        h_loss = hamming_loss(y_test, y_pred)

        print("\n📈 Multi-Label Training Results:")
        print(f"Subset Accuracy (Exact Match): {subset_accuracy:.4f}")
        print(f"Hamming Loss (Label Mismatch Ratio): {h_loss:.4f}")

        print("\n📊 Detailed Classification Report (per-label):")
        print(classification_report(y_test, y_pred, target_names=self.label_columns))

        return subset_accuracy, h_loss

    def save_model(self, filename=None):
        """Lưu mô hình đã train."""
        if filename is None:
            filename = "data/health_prediction_model.pkl"
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "label_columns": self.label_columns,
            "feature_names": self.feature_names,
            "trained_at": datetime.now().isoformat(),
            "model_type": "RandomForestClassifier_MultiLabel",
        }
        joblib.dump(model_data, filename)
        print(f"💾 Model saved to {filename}")

    def load_model(self, filename="data/health_prediction_model.pkl"):
        """Load mô hình đã train."""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Model file {filename} not found")

        model_data = joblib.load(filename)
        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.label_columns = model_data["label_columns"]
        self.feature_names = model_data["feature_names"]

        print(f"📂 Model loaded from {filename}")
        print(f"Trained at: {model_data.get('trained_at', 'Unknown')}")
        return model_data

    def train_model(self):
        """Main training function."""
        print("🏥 Health Prediction Model Training (Multi-Label)")
        print("=" * 50)

        accuracy, h_loss = self._train()

        if accuracy is not None:
            self.save_model()
            print("\n✅ Training completed successfully!")
            print(f"Final Subset Accuracy: {accuracy:.4f}")
            print(f"Final Hamming Loss: {h_loss:.4f}")
        else:
            print("\n❌ Training failed.")
