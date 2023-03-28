import requests
import schedule
import csv
import time
from datetime import datetime, timedelta

API_KEY = '**'
BASE_URL = 'https://gtschool.instructure.com/api/v1'
COURSE_ID = '1'

# Function to authenticate and make API calls to the Canvas API
def canvas_api_request(endpoint, method='GET', data=None):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    url = f'{BASE_URL}{endpoint}'
    response = requests.request(method, url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# Function to retrieve all quizzes for the course
def get_quizzes():
    endpoint = f'/courses/{COURSE_ID}/quizzes'
    return canvas_api_request(endpoint)

# Function to retrieve all quiz submissions for a quiz
def get_quiz_submissions(quiz_id):
    endpoint = f'/courses/{COURSE_ID}/quizzes/{quiz_id}/submissions'
    return canvas_api_request(endpoint)

def get_all_quizzes(course_id):
    quizzes = canvas_api_request(f'/courses/{course_id}/quizzes')
    return quizzes

def get_all_quiz_submissions(course_id, quiz_id):
    submissions = canvas_api_request(f'/courses/{course_id}/quizzes/{quiz_id}/submissions')
    return submissions


def main():
    course_id=COURSE_ID
    quizzes = get_all_quizzes(course_id)


    with open('quiz_submissions.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['course_id','quiz_id', 'quiz_title', 'submission_id', 'user_id']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for quiz in quizzes:
            print(f"Quiz ID: {quiz['id']}, Title: {quiz['title']}")
            submissions = get_all_quiz_submissions(course_id, quiz['id'])

            for submission in submissions['quiz_submissions']:
                print(f"  Submission ID: {submission['id']}, User ID: {submission['user_id']}")

                writer.writerow({
                    'course_id': course_id, # Add this line to the CSV file
                    'quiz_id': quiz['id'],
                    'quiz_title': quiz['title'],
                    'submission_id': submission['id'],
                    'user_id': submission['user_id']
                })


main()
def get_submission_events(course_id, quiz_id, submission_id):
    events = canvas_api_request(f'/courses/{course_id}/quizzes/{quiz_id}/submissions/{submission_id}/events')
    return events

def get_all_quiz_submission_info(course_id, quiz_id, submission_id):
    questions = get_submission_questions(quiz_id, submission_id)
    events = get_submission_events(course_id, quiz_id, submission_id)

    return {
        'questions': questions,
        'events': events
    }

def get_submission_questions(course_id, quiz_id):
    questions = canvas_api_request(f'/courses/{course_id}/quizzes/{quiz_id}/questions')
    return questions


def extract_answers_from_events(events):
    answers = {}
    
    for event in events:
        if event['event_type'] == 'question_answered':
            data = event['data']
            for message in data:
                if 'event_data' in message:
                    event_data = message['event_data']
                    question_id = event_data['quiz_question_id']
                    answer = event_data['answer']
                    answers[question_id] = answer

    return answers
print(extract_answers_from_events(get_submission_events(1, 120,145)))
"""#get_quiz_data all the quiz submissions for a course into a csv file then creates a new csv for each submission with the answers to each question
def get_quiz_data():
    course_id=COURSE_ID
    quizzes = get_all_quizzes(course_id)
    with open('quiz_submissions.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['course_id','quiz_id', 'quiz_title', 'submission_id', 'user_id']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for quiz in quizzes:
            print(f"Quiz ID: {quiz['id']}, Title: {quiz['title']}")
            submissions = get_all_quiz_submissions(course_id, quiz['id'])

            for submission in submissions['quiz_submissions']:
                print(f"  Submission ID: {submission['id']}, User ID: {submission['user_id']}")

                writer.writerow({
                    'course_id': course_id, # Add this line to the CSV file
                    'quiz_id': quiz['id'],
                    'quiz_title': quiz['title'],
                    'submission_id': submission['id'],
                    'user_id': submission['user_id']
                })
    with open('quiz_submissions.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            course_id = row['course_id']
            quiz_id = row['quiz_id']
            quiz_title = row['quiz_title']
            submission_id = row['submission_id']
            user_id = row['user_id']
            quiz_data = get_all_quiz_submission_info(course_id, quiz_id, submission_id)
            questions = quiz_data['questions']
            events = quiz_data['events']
            answers = extract_answers_from_events(events)
            with open(f'{quiz_title}_{submission_id}.csv', 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['question_id', 'question_text', 'answer']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for question in questions:
                    question_id = question['id']
                    question_text = question['question_name']
                    answer = answers.get(str(question_id), '')
                    writer.writerow({
                        'question_id': question_id,
                        'question_text': question_text,
                        'answer': answer
                    })
get_quiz_data()
"""
