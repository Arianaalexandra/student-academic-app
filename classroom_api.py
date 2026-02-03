from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly',
          'https://www.googleapis.com/auth/classroom.coursework.students.readonly',
          'https://www.googleapis.com/auth/classroom.rosters.readonly']

def get_classroom_service():
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('classroom', 'v1', credentials=creds)
    return service


def fetch_courses_and_students():
    service = get_classroom_service()
    data = []

    results = service.courses().list().execute()
    courses = results.get('courses', [])

    for course in courses:
        course_name = course['name']
        course_id = course['id']

        students_result = service.courses().students().list(courseId=course_id).execute()
        students = students_result.get('students', [])

        for s in students:
            profile = s['profile']
            email = profile.get('emailAddress')
            name = profile.get('name', {}).get('fullName')

            data.append({
                "course": course_name,
                "student_name": name,
                "student_email": email
            })

    return data
