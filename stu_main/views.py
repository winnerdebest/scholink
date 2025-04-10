from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
from .models import *
from exams.models import *


@login_required
def student_dashboard(request):
    user = request.user
    student = user.student_profile if hasattr(user, 'student_profile') else None

    if student:
        # Filter posts by the student's class
        posts = StudentPost.objects.filter(student__student_class=student.student_class).order_by('-created_at')
    else:
        posts = StudentPost.objects.none()  # If no student profile, show no posts

    context = {
        'user': user,
        'student': student,
        'posts': posts,
    }
    return render(request, 'dashboard.html', context)


@login_required
def create_post(request):
    if request.method == "POST":
        content = request.POST.get("content")
        if content and hasattr(request.user, 'student_profile'):
            post = StudentPost.objects.create(
                student=request.user.student_profile, 
                content=content
            )
            return render(request, "partials/post_item.html", {"post": post})
        return JsonResponse({"error": "Invalid request"}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


@login_required
def like_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(StudentPost, id=post_id)
        student = request.user.student_profile

        if student in post.likes.all():
            post.likes.remove(student)
            liked = False
        else:
            post.likes.add(student)
            post.dislikes.remove(student)
            liked = True

        return JsonResponse({
            "liked": liked, 
            "disliked": student in post.dislikes.all(),
            "total_likes": post.likes.count(), 
            "total_dislikes": post.dislikes.count()
        })
    return HttpResponseBadRequest()


@login_required
def dislike_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(StudentPost, id=post_id)
        student = request.user.student_profile

        if student in post.dislikes.all():
            post.dislikes.remove(student)
            disliked = False
        else:
            post.dislikes.add(student)
            post.likes.remove(student)
            disliked = True

        return JsonResponse({
            "liked": student in post.likes.all(),
            "disliked": disliked, 
            "total_likes": post.likes.count(), 
            "total_dislikes": post.dislikes.count()
        })
    return HttpResponseBadRequest()


@login_required
def profile(request):
    # Get the current user's student profile
    user = request.user
    student = user.student_profile if hasattr(user, 'student_profile') else None
    
    # If the student profile exists, fetch the guardian information
    guardian = None
    if student:
        guardian = Guardian.objects.filter(students=student).first()  
        
    rank = "1st"  
    
    context = {
        'student': student,
        'guardian': guardian,
        'rank': rank
    }
    
    return render(request, 'profile.html', context)




@login_required
def assignments(request):
    user = request.user
    student = user.student_profile if hasattr(user, 'student_profile') else None

    if student and hasattr(student, 'student_class'):
        try:
            class_subjects = ClassSubject.objects.filter(school_class=student.student_class)

            # Get all active assignments for the student's class
            all_active_assignments = Assignment.objects.filter(
                class_subject__in=class_subjects,
                is_active=True
            ).order_by('-created_at')

            # Get all submitted records by the student - use user instead of student
            submitted_records = StudentAssignmentRecord.objects.filter(
                student=user,  # Changed from student to user
                is_submitted=True
            ).select_related('assignment', 'assignment__class_subject', 
                           'assignment__class_subject__subject', 
                           'assignment__class_subject__school_class').order_by('-submitted_at')

            # Get the IDs of assignments already submitted
            submitted_assignment_ids = submitted_records.values_list('assignment_id', flat=True)

            # Exclude submitted assignments from the active ones
            unsubmitted_assignments = all_active_assignments.exclude(id__in=submitted_assignment_ids)

        except Exception as e:
            unsubmitted_assignments = []
            submitted_records = []
            messages.error(request, f"Error loading assignments: {str(e)}")
    else:
        unsubmitted_assignments = []
        submitted_records = []
        if not student:
            messages.warning(request, "No student profile found for this user.")
        elif not hasattr(student, 'student_class'):
            messages.warning(request, "You are not assigned to any class.")

    context = {
        'student': student,
        'assignments': unsubmitted_assignments,  # active + not submitted
        'submitted_records': submitted_records,  # fully submitted
    }

    return render(request, 'assignments.html', context)


@login_required
def take_assignment(request, assignment_id):
    """
    Load the assignment and its questions.
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    questions = assignment.questions.all()  # Uses the reverse relationship

    return render(request, "assignments/take_assignment.html", {
        "assignment": assignment,
        "questions": questions
    })


@login_required
def get_assignment_question(request, assignment_id, question_index):
    """
    Return one question for HTMX/AJAX.
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    questions = list(assignment.questions.all())

    if 0 <= question_index < len(questions):
        question = questions[question_index]
        return render(request, "assignments/question_component.html", {
            "question": question
        })

    return JsonResponse({"error": "Invalid question index"}, status=400)


@csrf_exempt
@login_required
def save_assignment_answer(request):
    """
    Save student answers and submit assignment.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            answers = data.get("answers", {})

            if not answers:
                return JsonResponse({"error": "No answers submitted"}, status=400)

            # Get the student user object
            student = request.user

            # Get the first question to find the assignment
            first_question_id = list(answers.keys())[0]
            first_question = get_object_or_404(Question, id=first_question_id)
            assignment = first_question.assignment

            record, created = StudentAssignmentRecord.objects.get_or_create(
                student=student,
                assignment=assignment,
                defaults={"responses": {}, "score": 0, "is_submitted": False}
            )

            # Update the responses field with the answers
            record.responses = answers  # Replace entirely instead of updating
            record.save()

            return JsonResponse({"message": "Assignment submitted successfully"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid data"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)


@login_required
def assignment_result(request, assignment_id):
    """
    Show student result after grading.
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = request.user
    record = get_object_or_404(StudentAssignmentRecord, student=student, assignment=assignment)

    questions = assignment.questions.all()
    total_questions = questions.count()
    responses = record.responses or {}

    correct_count = 0
    result_details = []

    for question in questions:
        qid = str(question.id)
        student_answer = responses.get(qid)
        correct_answer = question.correct_answer
        is_correct = student_answer == correct_answer

        if is_correct:
            correct_count += 1

        result_details.append({
            "question": question,
            "student_answer": student_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

    score_percent = (correct_count / total_questions) * 100 if total_questions > 0 else 0

    if not record.is_submitted:
        record.score = score_percent
        record.is_submitted = True
        record.save()

    return render(request, "assignments/assignment_result.html", {
        "assignment": assignment,
        "result_details": result_details,
        "correct_count": correct_count,
        "total_questions": total_questions,
        "score_percent": score_percent,
        "record": record
    })
