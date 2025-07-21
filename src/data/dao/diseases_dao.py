from ..database.database import DatabaseClient


class DiseasesDAO:
    @staticmethod
    def get_disease_ids_by_codes(disease_codes: list[str]) -> dict[str, int]:
        """Fetches a dictionary mapping disease codes to their IDs."""
        if not disease_codes:
            return {}
        conn = DatabaseClient.connection
        with conn.cursor() as cursor:
            query = "SELECT id, code FROM diseases WHERE code = ANY(%s)"
            cursor.execute(query, (disease_codes,))
            rows = cursor.fetchall()
            return {code: id for id, code in rows}
