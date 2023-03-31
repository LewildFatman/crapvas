import requests
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import psycopg2
import sqlite3
import logging

API_KEY = 'your_canvas_api_key'
BASE_URL = 'https://gtschool.instructure.com/api/v1'
COURSE_ID = '1'

# Add your Google Sheets API credentials
SERVICE_ACCOUNT_FILE = 'path/to/your/credentials.json'
SPREADSHEET_ID = 'your-spreadsheet-id'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to authenticate and make API calls to the Canvas API
def canvas_api_request(endpoint, method='GET', data=None):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    url = f'{BASE_URL}{endpoint}'
    try:
        response = requests.request(method, url, headers=headers, json=data)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Canvas API request failed: {e}")
        return []

    json_data = response.json()
    if 'Link' in response.headers:
        links = response.headers['Link'].split(',')
        for link in links:
            if 'rel="next"' in link:
                next_url = link[link.index('<') + 1:link.index('>')]
                endpoint = next_url.replace(BASE_URL, '')
                json_data.extend(canvas_api_request(endpoint, method, data))

    return json_data

# Function to append data to Google Sheets
def append_data_to_gsheet(spreadsheet_id, range_name, data):
    try:
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        service = build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        logger.error(f"Failed to set up Google Sheets API: {e}")
        return None

    body = {
        'range': range_name,
        'values': data,
        'majorDimension': 'ROWS'
    }
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
    except Exception as e:
        logger.error(f"Failed to append data to Google Sheets: {e}")
        return None

    return result

# Function to retrieve all quizzes for the course
def get_quizzes():
    endpoint = f'/courses/{COURSE_ID}/quizzes'
    return canvas_api_request(endpoint)

# Function to retrieve all quiz submissions for a quiz
def get_quiz_submissions(quiz_id):
    endpoint = f'/courses/{COURSE_ID}/quizzes/{quiz_id}/submissions'
    return canvas_api_request(endpoint)


def extract_correct_answers(json_data):
    quiz_submission_events = json_data["quiz_submission_events"]
    correct_answers_list = []

    for event in quiz_submission_events:
        if event["event_type"] == "submission_created":
            quiz_data = event["event_data"]["quiz_data"]

            for question in quiz_data:
                question_text = question["question_text"]
                answers = question["answers"]

                for answer in answers:
                    if answer["weight"] == 100:
                        correct_answers_list.append({"question": question_text, "correct_answer": answer["text"]})
                        break

    return correct_answers_list

def find_sister_value(dicts, target_key, target_value, sister_key):
    for dictionary in dicts:
        if dictionary.get(target_key) == target_value:
            return dictionary.get(sister_key)
    return None


def get_student_answers(json_data):
    dicts=get_all_values_for_key(json_data, "answer")
    questdicts=get_all_values_for_key(json_data, 'question_text')
    questionids=[dict['quiz_question_id'] for dict in dicts]
    questions={str(id['id']): id['question_text'] for id in questdicts}
    answers={id['quiz_question_id']: id['answer'] for id in dicts}
    questionswithanswers={questions[id]:answers[id] for id in questionids}
    return questionswithanswers



def testtocsv(json_data):
    questions = extract_questions_and_answers(json_data)
    data = [['question', 'answer', 'correct']]
    
    for question in questions:
        for answer in question["answers"]:
            data.append([
                question["question"],
                answer["answer"],
                answer["correct"]
            ])

    append_data_to_gsheet(SPREADSHEET_ID, 'Sheet1!A1', data)

def correct_answers_to_csv(json_data):
    correct_answers = extract_correct_answers(json_data)
    data = [['question', 'correct_answer']]
    
    for answer in correct_answers:
        data.append([
            answer["question"],
            answer["correct_answer"]
        ])

    append_data_to_gsheet(SPREADSHEET_ID, 'Sheet1!A1', data)

# Update the PostgreSQL database with the fetched data
def update_postgresql_database(quizzes_data):
    # Replace these values with your PostgreSQL credentials
    db_host = "your_host"
    db_port = "your_port"
    db_name = "your_database_name"
    db_user = "your_user"
    db_password = "your_password"

    try:
        connection = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
    except psycopg2.Error as e:
        logger.error(f"Error connecting to PostgreSQL database: {e}")
        return

    cursor = connection.cursor()

    #
CRONITOR_API_KEY = 'your_cronitor_api_key'

# Add your Space Alert API key
SPACE_ALERT_API_KEY = 'your_space_alert_api_key'

# ... (existing functions)

def send_email(subject, body):
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_TO

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        logger.error(f"Error sending email: {e}")

def main():
    monitor = Monitor(api_key=CRONITOR_API_KEY)
    space_alert = SpaceAlert(api_key=SPACE_ALERT_API_KEY)

    try:
        with monitor.job('fetch_and_update_data'):
            fetch_and_update_data(COURSE_ID)
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        send_email("Error in Canvas Data Sync", f"An error occurred while fetching and updating Canvas data:\n\n{e}")
        space_alert.alert(f"An error occurred while fetching and updating Canvas data:\n\n{e}")

if __name__ == "__main__":
    main()
