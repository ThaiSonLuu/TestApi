import pandas as pd
from datetime import datetime
from ..database.database import DatabaseClient


class MedicalRecordDAO:
    @staticmethod
    def get_training_data() -> pd.DataFrame | None:
        """
        Tải và xử lý dữ liệu training từ database cho bài toán multi-label.
        Mỗi bản ghi có thể có nhiều bệnh (label), sử dụng disease.code cho tên cột.
        """
        print("🗃️ Loading and processing multi-label training data from database...")
        conn = DatabaseClient.connection
        query = """
            WITH record_symptoms_agg AS (
                SELECT
                    r.id AS record_id,
                    array_agg(s.code) AS symptoms
                FROM medical_records r
                LEFT JOIN record_symptoms rs ON r.id = rs.record_id
                LEFT JOIN symptoms s ON rs.symptom_id = s.id
                GROUP BY r.id
            ),
            record_diseases_agg AS (
                -- Lấy tất cả mã bệnh của một record
                SELECT
                    r.id AS record_id,
                    array_agg(d.code) AS diseases
                FROM medical_records r
                LEFT JOIN record_diseases rd ON r.id = rd.record_id
                LEFT JOIN diseases d ON rd.disease_id = d.id
                WHERE d.code IS NOT NULL
                GROUP BY r.id
            )
            SELECT
                mr.id,
                u.date_of_birth,
                u.gender,
                mr.weather_temp,
                mr.humidity,
                mr.air_quality_index,
                mr.season,
                COALESCE(rsa.symptoms, '{}') AS symptoms,
                rda.diseases
            FROM medical_records mr
            JOIN users u ON mr.user_id = u.id
            JOIN record_symptoms_agg rsa ON mr.id = rsa.record_id
            JOIN record_diseases_agg rda ON mr.id = rda.record_id
            WHERE rda.diseases IS NOT NULL AND array_length(rda.diseases, 1) > 0;
        """

        try:
            df = pd.read_sql(query, conn)
            if df.empty:
                print("⚠️ No training data found in the database.")
                return None
            print(f"✅ Loaded {len(df)} raw records from the database.")
        except Exception as e:
            print(f"❌ Error loading data from database: {e}")
            return None

        # --- Feature Engineering ---
        current_year = datetime.now().year
        df["age"] = df["date_of_birth"].apply(
            lambda dob: current_year - dob.year if pd.notna(dob) else None
        )
        df["gender"] = df["gender"].map({"male": 1, "female": 0, "other": 2}).fillna(2)
        df["season"] = (
            df["season"].map({"spring": 0, "summer": 1, "autumn": 2, "winter": 3}).fillna(0)
        )

        # --- One-Hot Encode Symptoms and Diseases ---
        try:
            symptoms_df = pd.read_sql("SELECT code FROM symptoms", conn)
            all_symptom_codes = symptoms_df["code"].tolist()

            diseases_df = pd.read_sql("SELECT code FROM diseases", conn)
            all_disease_codes = diseases_df["code"].tolist()
        except Exception as e:
            print(f"❌ Error loading symptom or disease codes from database: {e}")
            return None

        for symptom_code in all_symptom_codes:
            df[symptom_code] = df["symptoms"].apply(lambda x: 1 if symptom_code in x else 0)

        for disease_code in all_disease_codes:
            df[disease_code] = df["diseases"].apply(lambda x: 1 if disease_code in x else 0)

        # --- Clean up ---
        df = df.drop(columns=["date_of_birth", "symptoms", "diseases", "id"])
        df = df.dropna(subset=["age"])

        print("✅ Data processing and feature engineering complete for multi-label format.")
        return df

    @staticmethod
    def create_medical_record(
        user_id, weather_temp, humidity, air_quality_index, season, cursor=None
    ):
        """
        Creates a new medical record. Can use an existing cursor or create a new one.
        """
        conn = DatabaseClient.connection
        
        # If a cursor is not provided, create one and manage the transaction locally.
        if cursor is None:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO medical_records
                        (user_id, record_type, status, weather_temp, humidity, air_quality_index, season)
                    VALUES (%s, 'system_prediction', 'completed', %s, %s, %s, %s)
                    RETURNING id
                """
                cur.execute(query, (user_id, weather_temp, humidity, air_quality_index, season))
                record_id = cur.fetchone()[0]
                conn.commit()
                return record_id
        
        # If a cursor is provided, use it without committing.
        query = """
            INSERT INTO medical_records
                (user_id, record_type, status, weather_temp, humidity, air_quality_index, season)
            VALUES (%s, 'system_prediction', 'completed', %s, %s, %s, %s)
            RETURNING id
        """
        cursor.execute(query, (user_id, weather_temp, humidity, air_quality_index, season))
        return cursor.fetchone()[0]

    @staticmethod
    def add_symptoms_to_record(record_id, symptom_ids: list[int], cursor=None):
        """
        Adds symptoms to a record. Can use an existing cursor.
        """
        if not symptom_ids:
            return
            
        conn = DatabaseClient.connection

        if cursor is None:
            with conn.cursor() as cur:
                args = [(record_id, symptom_id) for symptom_id in symptom_ids]
                query = "INSERT INTO record_symptoms (record_id, symptom_id) VALUES (%s, %s)"
                cur.executemany(query, args)
                conn.commit()
            return

        args = [(record_id, symptom_id) for symptom_id in symptom_ids]
        query = "INSERT INTO record_symptoms (record_id, symptom_id) VALUES (%s, %s)"
        cursor.executemany(query, args)

    @staticmethod
    def add_diseases_to_record(record_id, disease_predictions: dict, cursor=None):
        """
        Adds disease predictions to a record. Can use an existing cursor.
        """
        if not disease_predictions:
            return

        conn = DatabaseClient.connection
        
        if cursor is None:
            with conn.cursor() as cur:
                args = [(record_id, disease_id, prob) for disease_id, prob in disease_predictions.items()]
                query = "INSERT INTO record_diseases (record_id, disease_id, probability) VALUES (%s, %s, %s)"
                cur.executemany(query, args)
                conn.commit()
            return

        args = [(record_id, disease_id, prob) for disease_id, prob in disease_predictions.items()]
        query = "INSERT INTO record_diseases (record_id, disease_id, probability) VALUES (%s, %s, %s)"
        cursor.executemany(query, args)
