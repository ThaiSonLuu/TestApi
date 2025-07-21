import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import argparse
import json
from .train_model import HealthPredictionTrainer


class HealthPredictor:
    def __init__(self, model_file="data/health_prediction_model.pkl"):
        self.trainer = HealthPredictionTrainer()
        self.model_file = model_file
        self.model_data = None

    def load_model(self):
        """Load model đã train."""
        try:
            self.model_data = self.trainer.load_model(self.model_file)
            print("✅ Model loaded successfully!")
        except Exception as e:
            print(f"Train model failed {e}")

    def predict_single(self, patient_data, threshold=0.5):
        """Dự đoán cho 1 bệnh nhân (multi-label)."""
        if not self.model_data:
            self.load_model()

        df = pd.DataFrame([patient_data])

        for feature in self.trainer.feature_names:
            if feature not in df.columns:
                df[feature] = 0

        df = df[self.trainer.feature_names]
        X_scaled = self.trainer.scaler.transform(df)

        # --- Robust Probability Extraction ---
        probabilities_per_label = self.trainer.model.predict_proba(X_scaled)
        model_classes_per_label = self.trainer.model.classes_

        positive_probabilities = []
        for i, prob_array in enumerate(probabilities_per_label):
            classes_for_this_label = model_classes_per_label[i]
            prob_for_this_sample = prob_array[0]

            if 1 in classes_for_this_label:
                class_1_index = np.where(classes_for_this_label == 1)[0][0]
                positive_probabilities.append(prob_for_this_sample[class_1_index])
            else:
                positive_probabilities.append(0.0)

        all_probabilities = dict(
            zip(self.trainer.label_columns, positive_probabilities)
        )

        predicted_diseases = {
            label: float(prob)
            for label, prob in all_probabilities.items()
            if prob >= threshold
        }

        sorted_predictions = sorted(
            all_probabilities.items(), key=lambda x: x[1], reverse=True
        )

        result = {
            "predicted_diseases": predicted_diseases,
            "all_probabilities": {k: float(v) for k, v in all_probabilities.items()},
            "sorted_predictions": [
                (label, float(prob)) for label, prob in sorted_predictions[:3]
            ],
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
