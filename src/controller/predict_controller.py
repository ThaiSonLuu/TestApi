from flask import Blueprint, request, jsonify
from datetime import datetime
import random
import logging

from src.data.dao.users_dao import UsersDAO
from src.data.dao.medical_record_dao import MedicalRecordDAO
from src.data.dao.symptoms_dao import SymptomsDAO
from src.data.dao.diseases_dao import DiseasesDAO
from src.data.database.database import DatabaseClient
from src.ml.predict import HealthPredictor

predict_api = Blueprint("predict_api", __name__)

health_predictor_instance = HealthPredictor()


def get_current_season():
    """Determines the current season based on the month."""
    month = datetime.now().month
    if month in (12, 1, 2):
        return "winter"
    elif month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    else:
        return "autumn"


@predict_api.route("/predict", methods=["POST"])
def predict():
    if health_predictor_instance is None:
        return (
            jsonify(
                {
                    "error_code": 503,
                    "error_message": "Prediction model is not available. Please train the model first.",
                }
            ),
            503,
        )

    data = request.json
    user_id = data.get("user_id")
    symptom_codes = data.get("symptom_codes")

    if not user_id or not isinstance(user_id, int):
        return (
            jsonify({"error_code": 400, "error_message": "Missing or invalid user_id"}),
            400,
        )
    if not symptom_codes or not isinstance(symptom_codes, list):
        return (
            jsonify(
                {
                    "error_code": 400,
                    "error_message": "Missing or invalid symptom_codes list",
                }
            ),
            400,
        )

    user = UsersDAO.get_user_by_id(user_id)
    if not user:
        return jsonify({"error_code": 404, "error_message": "User not found"}), 404

    conn = DatabaseClient.connection
    cursor = conn.cursor()

    try:
        # --- 1. Perform Prediction ---
        weather_temp = round(random.uniform(10.0, 40.0), 1)
        humidity = random.randint(30, 90)
        air_quality_index = random.randint(1, 5)
        season_name = get_current_season()

        patient_features = {
            "age": (
                datetime.now().year - user.date_of_birth.year
                if user.date_of_birth
                else 30
            ),
            "gender": {"male": 1, "female": 0, "other": 2}.get(user.gender, 2),
            "weather_temp": weather_temp,
            "humidity": humidity,
            "air_quality_index": air_quality_index,
            "season": {"spring": 0, "summer": 1, "autumn": 2, "winter": 3}.get(
                season_name, 0
            ),
        }
        for code in symptom_codes:
            patient_features[code] = 1

        prediction_result = health_predictor_instance.predict_single(patient_features)
        if not prediction_result:
            raise Exception("Prediction failed")

        # --- 2. Create Medical Record ---
        record_id = MedicalRecordDAO.create_medical_record(
            user_id=user_id,
            weather_temp=weather_temp,
            humidity=humidity,
            air_quality_index=air_quality_index,
            season=season_name,
            cursor=cursor,
        )

        # --- 3. Add Symptoms ---
        symptom_map = SymptomsDAO.get_symptom_ids_by_codes(symptom_codes)
        symptom_ids = list(symptom_map.values())
        if len(symptom_ids) != len(symptom_codes):
            found_codes = list(symptom_map.keys())
            invalid_codes = [code for code in symptom_codes if code not in found_codes]
            raise ValueError(f"Invalid symptom codes provided: {invalid_codes}")

        MedicalRecordDAO.add_symptoms_to_record(record_id, symptom_ids, cursor=cursor)

        # --- 4. Add Top 3 Disease Predictions ---
        top_3_predictions = prediction_result.get("sorted_predictions", [])

        if top_3_predictions:
            top_3_disease_codes = [pred[0] for pred in top_3_predictions]
            disease_map = DiseasesDAO.get_disease_ids_by_codes(top_3_disease_codes)

            disease_predictions_to_save = {
                disease_map[code]: prob
                for code, prob in top_3_predictions
                if code in disease_map
            }

            if disease_predictions_to_save:
                MedicalRecordDAO.add_diseases_to_record(
                    record_id, disease_predictions_to_save, cursor=cursor
                )

        # --- 5. Commit Transaction ---
        conn.commit()

        prediction_result["medical_record_id"] = record_id
        return jsonify(prediction_result), 200

    except Exception as e:
        conn.rollback()
        logging.error(f"Prediction and record creation failed: {e}")
        return (
            jsonify(
                {
                    "error_code": 500,
                    "error_message": f"An internal error occurred: {e}",
                }
            ),
            500,
        )
    finally:
        cursor.close()
