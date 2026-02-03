from database import get_db_connection

class Grade:
    @staticmethod
    def get_by_student(email):
        conn = get_db_connection()
        grades = conn.execute(
            "SELECT course, grade FROM grades WHERE student_email = ?",
            (email,)
        ).fetchall()
        conn.close()
        return grades
