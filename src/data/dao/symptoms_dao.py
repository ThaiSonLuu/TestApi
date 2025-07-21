from ..database.database import DatabaseClient


class SymptomsDAO:
    @staticmethod
    def get_symptom_ids_by_codes(symptom_codes: list[str]) -> dict[str, int]:
        """Fetches a dictionary mapping symptom codes to their IDs."""
        if not symptom_codes:
            return {}
        conn = DatabaseClient.connection
        with conn.cursor() as cursor:
            query = "SELECT id, code FROM symptoms WHERE code = ANY(%s)"
            cursor.execute(query, (symptom_codes,))
            rows = cursor.fetchall()
            return {code: id for id, code in rows}
