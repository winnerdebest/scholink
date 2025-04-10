from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
from django.utils.timezone import now
from .models import *

from stu_main.models import CustomUser


def exam_login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')  # Get email from the form
        password = request.POST.get('password')

        try:
            # Find the user by email in the CustomUser model
            user = CustomUser.objects.get(email=email)
            
            # Authenticate using the username (CustomUser model uses username field)
            user = authenticate(request, username=user.username, password=password)

            if user and user.user_type == 'student':  # Ensure user is a student
                login(request, user)
                return redirect('available_exams')
            else:
                messages.error(request, "Only students can log in for exams.")
        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid credentials.")

    return render(request, 'exams/login.html')


@login_required(login_url='exam_login')
def available_exams_view(request):
    student = request.user
    student_class = student.student_profile.student_class

    # Get available exams
    available_exams = Exam.objects.filter(
        class_subject__school_class=student_class,
        is_active=True
    ).exclude(
        student_records__student=student,
        student_records__is_submitted=True
    )

    # Get completed exams
    completed_exams = Exam.objects.filter(
        student_records__student=student,
        student_records__is_submitted=True
    ).distinct()

    return render(request, 'exams/available_exams.html', {
        'available_exams': available_exams,
        'completed_exams': completed_exams
    })



@login_required(login_url='exam_login')
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = Question.objects.filter(exam=exam)
    
    return render(request, "exams/take_exam.html", {"exam": exam, "questions": questions})

def get_question(request, exam_id, question_index):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = list(Question.objects.filter(exam=exam))

    if 0 <= question_index < len(questions):
        return render(request, "exams/question_component.html", {"question": questions[question_index]})
    return JsonResponse({"error": "Invalid question index"}, status=400)




def save_answer(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("Received Data:", data)  # Debugging print
            answers = data.get("answers", {})

            if not answers:
                return JsonResponse({"error": "No answers provided"}, status=400)

            student = request.user
            first_question_id = list(answers.keys())[0]
            first_question = get_object_or_404(Question, id=first_question_id)
            exam = first_question.exam

            exam_record, created = StudentExamRecord.objects.get_or_create(
                student=student, exam=exam,
                defaults={"responses": {}, "score": 0, "is_submitted": False}
            )

            # Merge new answers with existing responses
            responses = exam_record.responses or {}
            responses.update(answers)  
            exam_record.responses = responses  
            exam_record.save()

            return JsonResponse({"message": "Exam submitted successfully!"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)




def exam_result(request, exam_id):
    # Get the exam and ensure the user has access
    exam = get_object_or_404(Exam, id=exam_id)
    student = request.user
    
    # Get the student's exam record
    exam_record = get_object_or_404(StudentExamRecord, 
                                    student=student, 
                                    exam=exam)
    
    # Get all questions for this exam
    questions = Question.objects.filter(exam=exam)
    
    # Calculate results
    total_questions = questions.count()
    student_responses = exam_record.responses or {}
    
    # Process each question and answer
    result_details = []
    correct_count = 0
    
    for question in questions:
        question_id = str(question.id)
        student_answer = student_responses.get(question_id, None)
        is_correct = student_answer == question.correct_answer
        
        if is_correct:
            correct_count += 1
            
        result_details.append({
            'question': question,
            'student_answer': student_answer,
            'is_correct': is_correct,
            'correct_answer': question.correct_answer,
        })
    
    # Calculate score as percentage
    score_percent = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    # Update the record with the final score if not already calculated
    if exam_record.score == 0:
        exam_record.score = score_percent
        exam_record.is_submitted = True
        exam_record.save()
    
    context = {
        'exam': exam,
        'result_details': result_details,
        'correct_count': correct_count,
        'total_questions': total_questions,
        'score_percent': score_percent,
        'exam_record': exam_record,
    }
    
    return render(request, 'exams/exam_result.html', context)