from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.decorators.http import require_POST

#importing all models from other apps 
from academic_main.models import *
from exams.models import *
from assignments.models import *
from stu_main.models import *

#importing forms
from .forms import *


@login_required
def teacher_dashboard(request):
    teacher = request.user

    # Fetch all ClassSubjects assigned to this teacher
    assigned_subjects = ClassSubject.objects.filter(teacher=teacher).select_related('subject', 'school_class')

    # Group by class, then collect all subjects the teacher teaches in that class
    class_data = {}
    for cs in assigned_subjects:
        class_name = cs.school_class.name
        if class_name not in class_data:
            class_data[class_name] = {
                'class_obj': cs.school_class,
                'subjects': [cs.subject.name]
            }
        else:
            class_data[class_name]['subjects'].append(cs.subject.name)

    return render(request, 'dashboard/dashboard.html', {
        'class_data': class_data
    })


@login_required
def teacher_class_detail(request, class_id):
    teacher = request.user
    school_class = get_object_or_404(Class, id=class_id)

    # Get only the subjects THIS teacher handles for that class
    class_subjects = ClassSubject.objects.filter(
        teacher=teacher,
        school_class=school_class
    ).select_related('subject')

    return render(request, 'dashboard/teacher_class_detail.html', {
        'school_class': school_class,
        'class_subjects': class_subjects
    })



@login_required
def subject_detail_view(request, class_subject_id):
    class_subject = get_object_or_404(ClassSubject, id=class_subject_id)

    active_term = ActiveTerm.get_active_term()
    
    assignments = Assignment.objects.filter(class_subject=class_subject).order_by('-created_at')
    exams = Exam.objects.filter(class_subject=class_subject).order_by('-created_at')

    student_assignment_records = StudentAssignmentRecord.objects.filter(assignment__in=assignments)
    student_exam_records = StudentExamRecord.objects.filter(exam__in=exams)

    query = request.GET.get('q')
    if query:
        student_assignment_records = student_assignment_records.filter(
            Q(student__username__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query)
        )
        student_exam_records = student_exam_records.filter(
            Q(student__username__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query)
        )

    context = {
        "class_subject": class_subject,
        "assignments": assignments,
        "exams": exams,
        "assignment_records": student_assignment_records,
        "exam_records": student_exam_records,
        "active_term": active_term,
    }
    return render(request, "dashboard"
    "/class_subject_detail.html", context)




@require_POST
def toggle_assignment_active(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    assignment.is_active = not assignment.is_active
    assignment.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))

@require_POST
def toggle_exam_active(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    exam.is_active = not exam.is_active
    exam.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))



@login_required
def create_exam(request, class_subject_id, term_id):
    class_subject = get_object_or_404(ClassSubject, id=class_subject_id)
    term = get_object_or_404(Term, id=term_id)

    if request.method == 'POST':
        form = ExamForm(request.POST)
        question_formset = QuestionFormSet(request.POST, request.FILES, prefix='questions')

        if form.is_valid() and question_formset.is_valid():
            exam = form.save(commit=False)
            exam.class_subject = class_subject
            exam.term = term
            exam.save()

            for question_form in question_formset:
                if question_form.cleaned_data:  # skip empty forms
                    question = question_form.save(commit=False)
                    question.exam = exam
                    question.created_by = request.user
                    question.save()

            return redirect('teacher:class_subject_detail', class_subject_id)

    else:
        form = ExamForm()
        question_formset = QuestionFormSet(queryset=Question.objects.none(), prefix='questions')

    return render(request, 'dashboard/create_exam.html', {
        'form': form,
        'question_formset': question_formset,
        'class_subject': class_subject,
        'term': term,
    })


@login_required
def create_assignment(request, class_subject_id, term_id):
    class_subject = get_object_or_404(ClassSubject, id=class_subject_id)
    term = get_object_or_404(Term, id=term_id)

    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        question_formset = QuestionFormSet(request.POST, request.FILES, prefix='questions')

        if form.is_valid() and question_formset.is_valid():
            assignment = form.save(commit=False)
            assignment.class_subject = class_subject
            assignment.term = term
            assignment.save()

            for question_form in question_formset:
                if question_form.cleaned_data:  # skip empty forms
                    question = question_form.save(commit=False)
                    question.assignment = assignment
                    question.created_by = request.user
                    question.save()

            return redirect('teacher:class_subject_detail', class_subject_id)

    else:
        form = AssignmentForm()
        question_formset = QuestionFormSet(queryset=Question.objects.none(), prefix='questions')

    return render(request, 'dashboard/create_assignment.html', {
        'form': form,
        'question_formset': question_formset,
        'class_subject': class_subject,
        'term': term,
    })