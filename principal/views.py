from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from stu_main.models import *
from academic_main.decorators import role_required
from django.contrib import messages
from .forms import StudentCreationForm
from .utils import generate_username, generate_readable_password
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # For search



User = get_user_model()


@login_required
@role_required('principal')
def principal_dashboard(request):
    total_students = Student.objects.count()
    total_teachers = User.objects.filter(user_type="teacher").count()
    total_classes = Class.objects.count()
    total_subjects = Subject.objects.count()

    context = {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classes": total_classes,
        "total_subjects": total_subjects,
    }

    return render(request, 'principal/dashboard.html', context )


import logging

logger = logging.getLogger(__name__)


@login_required
@role_required('principal')
def create_student(request):
    if request.method == "POST":
        form = StudentCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # Log cleaned data
            logger.debug("Form is valid. Cleaned data: %s", form.cleaned_data)
            
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']

            username = generate_username(first_name, last_name)
            password = generate_readable_password()

            logger.debug("Generated username: %s", username)
            logger.debug("Generated password: %s", password)

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                user_type="student"
            )

            student = form.save(commit=False)
            student.user = user
            student.save()

            logger.debug("Student created: %s", student.user.get_full_name())

            # Create Guardians
            guardian_names = request.POST.getlist('guardian_name')
            guardian_emails = request.POST.getlist('guardian_email')
            guardian_phones = request.POST.getlist('guardian_phone')

            logger.debug("Guardian names: %s", guardian_names)
            logger.debug("Guardian emails: %s", guardian_emails)
            logger.debug("Guardian phones: %s", guardian_phones)

            guardians = []
            for name, email, phone in zip(guardian_names, guardian_emails, guardian_phones):
                if name and email and phone:
                    guardian, _ = Guardian.objects.get_or_create(
                        email=email,
                        defaults={"name": name, "phone_number": phone}
                    )
                    student.guardians.add(guardian)
                    guardians.append(guardian)
                    logger.debug("Created guardian: %s with email %s", guardian.name, guardian.email)
                else:
                    logger.warning("Guardian information is missing for name: %s, email: %s, phone: %s", name, email, phone)

            context = {
                "student": student,
                "username": username,
                "password": password,
                "guardians": guardians
            }

            logger.debug("Context passed to success page: %s", context)

            return render(request, "students/student_success.html", context)

        else:
            # Log form errors
            logger.error("Form is not valid. Errors: %s", form.errors)
            messages.error(request, "Please correct the errors below.")

    else:
        form = StudentCreationForm()

    return render(request, "students/create_student.html", {"form": form})

@login_required
@role_required('principal')
def edit_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    user = student.user

    if request.method == "POST":
        form = StudentCreationForm(request.POST, request.FILES, instance=student)

        if form.is_valid():
            form.save()

            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()

            
            guardian_names = request.POST.getlist('guardian_name')
            guardian_emails = request.POST.getlist('guardian_email')
            guardian_phones = request.POST.getlist('guardian_phone')

            student.guardians.clear()
            for name, email, phone in zip(guardian_names, guardian_emails, guardian_phones):
                if name and email and phone:
                    guardian, _ = Guardian.objects.get_or_create(
                        email=email,
                        defaults={"name": name, "phone_number": phone}
                    )
                    student.guardians.add(guardian)

            messages.success(request, "Student updated successfully.")
            return redirect("principal:student_list", )
        else:
            messages.error(request, "Please correct the errors below.")

    else:
        # Prepopulate user fields
        initial_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        }
        form = StudentCreationForm(instance=student, initial=initial_data)

    return render(request, "students/edit_student.html", {
        "form": form,
        "student": student,
    })


@login_required
@role_required('principal')
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        user = student.user 
        student.delete()
        user.delete()  
        messages.success(request, "Student deleted successfully.")
        return redirect("principal:student_list")

    return render(request, "students/delete_student_confirm.html", {"student": student})


@login_required
@role_required('principal')
def student_list(request):
    query = request.GET.get('q', '')  

    students = Student.objects.select_related('user').all()
    
    if query:
        students = students.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(student_class__name__icontains=query)  
        )

    paginator = Paginator(students, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "students": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "query": query,
    }
    return render(request, "students/student_list.html", context)


@login_required
@role_required('principal')
def create_teacher(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')

        if not first_name or not last_name or not email:
            messages.error(request, "Please fill in all required fields.")
            return render(request, "teachers/create_teacher.html")

        username = generate_username(first_name, last_name)
        password = generate_readable_password()

        # Create the teacher user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            user_type="teacher"
        )

        context = {
            "teacher": user,
            "username": username,
            "password": password,
        }

        return render(request, "teachers/teacher_success.html", context)

    return render(request, "teachers/create_teacher.html")


@login_required
@role_required('principal')
def edit_teacher(request, pk):
    teacher = get_object_or_404(User, pk=pk, user_type="teacher")

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')

        if not first_name or not last_name or not email:
            messages.error(request, "Please fill in all fields.")
        else:
            teacher.first_name = first_name
            teacher.last_name = last_name
            teacher.email = email
            teacher.save()
            messages.success(request, "Teacher updated successfully.")
            return redirect("principal:teacher_list")

    return render(request, "teachers/edit_teacher.html", {"teacher": teacher})


@login_required
@role_required('principal')
def delete_teacher(request, pk):
    teacher = get_object_or_404(User, pk=pk, user_type="teacher")

    if request.method == "POST":
        teacher.delete()
        messages.success(request, "Teacher deleted successfully.")
        return redirect("principal:teacher_list")

    return render(request, "teachers/delete_teacher_confirm.html", {"teacher": teacher})


@login_required
@role_required('principal')
def teacher_list(request):
    query = request.GET.get('q', '')

    teachers = User.objects.filter(user_type='teacher')

    if query:
        teachers = teachers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )

    paginator = Paginator(teachers, 10)  # 10 teachers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "teachers": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "query": query,
    }
    return render(request, "teachers/teacher_list.html", context)


@login_required
@role_required('principal')
def class_list(request):
    classes = Class.objects.all()
    return render(request, "classes/class_list.html", {"classes": classes})


@login_required
@role_required('principal')
def create_class(request):
    if request.method == "POST":
        name = request.POST.get("name")
        form_master_id = request.POST.get("form_master")

        if not name:
            messages.error(request, "Class name is required.")
        else:
            form_master = None
            if form_master_id:
                form_master = CustomUser.objects.filter(id=form_master_id, user_type='teacher').first()

            class_instance = Class.objects.create(
                name=name,
                form_master=form_master
            )
            messages.success(request, f"Class '{class_instance.name}' created successfully.")
            return redirect("principal:class_list")  # Update this if your class list URL is different

    teachers = CustomUser.objects.filter(user_type='teacher')
    return render(request, "classes/create_class.html", {"teachers": teachers})


@login_required
@role_required('principal')
def edit_class(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id)

    if request.method == "POST":
        name = request.POST.get("name")
        form_master_id = request.POST.get("form_master")

        if not name:
            messages.error(request, "Class name is required.")
        else:
            class_instance.name = name
            if form_master_id:
                class_instance.form_master = CustomUser.objects.filter(id=form_master_id, user_type='teacher').first()
            else:
                class_instance.form_master = None
            class_instance.save()
            messages.success(request, f"Class '{class_instance.name}' updated successfully.")
            return redirect("principal:class_list")  

    teachers = CustomUser.objects.filter(user_type='teacher')
    return render(request, "classes/edit_class.html", {"class_instance": class_instance, "teachers": teachers})


@login_required
@role_required('principal')
def delete_class(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id)
    
    if request.method == "POST":
        class_instance.delete()
        messages.success(request, "Class deleted successfully.")
        return redirect("class_list")

    return render(request, "classes/delete_class.html", {"class_instance": class_instance})


@login_required
@role_required('principal')
def class_detail(request, class_id):
    school_class = get_object_or_404(Class, id=class_id)
    class_subjects = ClassSubject.objects.select_related("subject", "teacher").filter(school_class=school_class)

    return render(request, "classes/class_detail.html", {
        "class": school_class,
        "class_subjects": class_subjects
    })


@login_required
@role_required('principal')
def assign_subject_to_class(request, class_id):
    school_class = get_object_or_404(Class, id=class_id)
    teachers = CustomUser.objects.filter(user_type="teacher")
    subjects = Subject.objects.all()

    if request.method == "POST":
        subject_id = request.POST.get("subject")
        teacher_id = request.POST.get("teacher")

        if not subject_id or not teacher_id:
            messages.error(request, "Please select both a subject and a teacher.")
            return redirect("principal:assign_subject", class_id=class_id)

        subject = get_object_or_404(Subject, id=subject_id)
        teacher = get_object_or_404(CustomUser, id=teacher_id)

        # Prevent duplicate assignment
        if ClassSubject.objects.filter(subject=subject, school_class=school_class).exists():
            messages.warning(request, f"{subject.name} is already assigned to this class.")
        else:
            ClassSubject.objects.create(subject=subject, school_class=school_class, teacher=teacher)
            messages.success(request, f"{subject.name} assigned to {school_class.name}.")

        return redirect("principal:class_detail", class_id=class_id)

    return render(request, "classes/assign_subject.html", {
        "school_class": school_class,
        "subjects": subjects,
        "teachers": teachers
    })


@login_required
@role_required('principal')
def edit_class_subject(request, classsubject_id):
    class_subject = get_object_or_404(ClassSubject, id=classsubject_id)
    teachers = CustomUser.objects.filter(user_type="teacher")

    if request.method == "POST":
        teacher_id = request.POST.get("teacher")
        if not teacher_id:
            messages.error(request, "Please select a teacher.")
        else:
            teacher = get_object_or_404(CustomUser, id=teacher_id)
            class_subject.teacher = teacher
            class_subject.save()
            messages.success(request, f"{class_subject.subject.name} teacher updated.")
            return redirect("principal:class_detail", class_id=class_subject.school_class.id)

    return render(request, "classes/edit_class_subject.html", {
        "class_subject": class_subject,
        "teachers": teachers
    })


@login_required
@role_required('principal')
def delete_class_subject(request, classsubject_id):
    class_subject = get_object_or_404(ClassSubject, id=classsubject_id)
    class_id = class_subject.school_class.id

    if request.method == "POST":
        class_subject.delete()
        messages.success(request, "Subject assignment deleted.")
        return redirect("principal:class_detail", class_id=class_id)

    return render(request, "classes/delete_class_subject.html", {
        "class_subject": class_subject
    })


@login_required
@role_required('principal')
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, "principal/subject_list.html", {"subjects": subjects})


@login_required
@role_required('principal')
def create_subject(request):
    if request.method == "POST":
        name = request.POST.get("name")
        code = request.POST.get("code")
        description = request.POST.get("description")

        if not name:
            messages.error(request, "Subject name is required.")
            return render(request, "subjects/create_subject.html")

        Subject.objects.create(name=name, code=code, description=description)
        messages.success(request, "Subject created successfully.")
        return redirect("principal:subject_list")

    return render(request, "principal/create_or_edit_subject.html")


@login_required
@role_required('principal')
def edit_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)

    if request.method == "POST":
        subject.name = request.POST.get("name")
        subject.code = request.POST.get("code")
        subject.description = request.POST.get("description")
        subject.save()
        messages.success(request, "Subject updated successfully.")
        return redirect("principal:subject_list")

    return render(request, "principal/create_or_edit_subject.html", {"subject": subject})


@login_required
@role_required('principal')
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, "Subject deleted successfully.")
    return redirect("principal:subject_list")