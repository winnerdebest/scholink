from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model
from stu_main.models import *
from academic_main.decorators import role_required
from django.contrib import messages
from .forms import *
from .utils import generate_username, generate_readable_password
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch, Sum
from .models import Expense, ExpenseCategory, TeacherSalaryPayment, Announcement
from django.utils import timezone
from datetime import datetime
from django.core.paginator import Paginator
from django.db import models
from io import BytesIO
import xlsxwriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch


User = get_user_model()


@login_required
@role_required('principal')
def principal_dashboard(request):
    user = request.user
    school = getattr(user, 'school', None)

    if not school:
        return render(request, 'principal/dashboard.html', {
            "error": "No school is associated with this account."
        })

    total_students = Student.objects.filter(student_class__school=school).count()
    total_teachers = Teacher.objects.filter(school=school).distinct().count()
    total_classes = Class.objects.filter(school=school).count()
    total_subjects = Subject.objects.filter(school=school).count()

    # Get active announcements
    announcements = Announcement.objects.filter(
        school=school,
        is_active=True
    ).exclude(
        expiry_date__lt=timezone.now()
    ).order_by('-created_at')[:5]  # Get 5 most recent announcements

    # Calculate expense analytics
    try:
        # Total expenses calculation
        total_expenses = Expense.objects.filter(school=school).aggregate(
            total=models.Sum('amount'))['total']
        total_expenses = float(total_expenses) if total_expenses is not None else 0.0

        # Current month expenses
        current_month = timezone.now().month
        current_year = timezone.now().year
        current_month_expenses = Expense.objects.filter(
            school=school,
            date__month=current_month,
            date__year=current_year
        ).aggregate(total=models.Sum('amount'))['total']
        current_month_expenses = float(current_month_expenses) if current_month_expenses is not None else 0.0

        # Previous month expenses
        previous_month = (timezone.now().replace(day=1) - timezone.timedelta(days=1)).month
        previous_month_year = current_year if current_month > 1 else current_year - 1
        previous_month_expenses = Expense.objects.filter(
            school=school,
            date__month=previous_month,
            date__year=previous_month_year
        ).aggregate(total=models.Sum('amount'))['total']
        previous_month_expenses = float(previous_month_expenses) if previous_month_expenses is not None else 0.0

        # Calculate percentage change
        if previous_month_expenses > 0:
            expense_change_percentage = ((current_month_expenses - previous_month_expenses) / previous_month_expenses) * 100
        else:
            expense_change_percentage = 100 if current_month_expenses > 0 else 0

    except Exception as e:
        print(f"Error calculating expenses: {e}")
        total_expenses = 0.0
        current_month_expenses = 0.0
        expense_change_percentage = 0.0

    context = {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classes": total_classes,
        "total_subjects": total_subjects,
        "total_expenses": total_expenses,
        "current_month_expenses": current_month_expenses,
        "expense_change_percentage": expense_change_percentage,
        "announcements": announcements,
    }

    return render(request, 'principal/dashboard.html', context)



import logging

logger = logging.getLogger(__name__)


@login_required
@role_required('principal')
def create_student(request):
    school = request.user.school

    if request.method == "POST":
        form = StudentCreationForm(request.POST, request.FILES)
        if form.is_valid():
            logger.debug("Form is valid. Cleaned data: %s", form.cleaned_data)

            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']

            username = generate_username(first_name, last_name)
            password = generate_readable_password()

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

            # Ensure class belongs to the school
            if student.student_class and student.student_class.school != school:
                messages.error(request, "Selected class does not belong to your school.")
                user.delete()
                return render(request, "students/create_student.html", {"form": form})

            student.save()

            # Create guardians
            guardian_names = request.POST.getlist('guardian_name')
            guardian_emails = request.POST.getlist('guardian_email')
            guardian_phones = request.POST.getlist('guardian_phone')

            guardians = []
            for name, email, phone in zip(guardian_names, guardian_emails, guardian_phones):
                if name and email and phone:
                    guardian, _ = Guardian.objects.get_or_create(
                        email=email,
                        defaults={"name": name, "phone_number": phone}
                    )
                    student.guardians.add(guardian)
                    guardians.append(guardian)
                else:
                    logger.warning("Incomplete guardian: %s %s %s", name, email, phone)

            context = {
                "student": student,
                "username": username,
                "password": password,
                "guardians": guardians
            }

            return render(request, "students/student_success.html", context)
        else:
            logger.error("Form invalid: %s", form.errors)
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentCreationForm()
        # Limit class choices to the principal's school
        form.fields['student_class'].queryset = Class.objects.filter(school=school)

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
    school = request.user.school  # Ensure your User model is linked to a school

    query = request.GET.get('q', '')

    # Filter students by school via their student_class
    students = Student.objects.select_related('user', 'student_class').filter(
        student_class__school=school
    )

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
        salary = request.POST.get('salary')

        if not first_name or not last_name or not email:
            messages.error(request, "Please fill in all required fields.")
            return render(request, "teachers/create_teacher.html")

        username = generate_username(first_name, last_name)
        password = generate_readable_password()

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            user_type="teacher"
        )

        # Link teacher to user's school (via principal)
        Teacher.objects.create(
            user=user,
            school=request.user.school,
            salary=salary if salary else None
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
    teacher = get_object_or_404(Teacher, pk=pk)
    user = teacher.user 

    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        salary = request.POST.get('salary')

        if not first_name or not last_name or not email:
            messages.error(request, "Please fill in all required fields.")
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            teacher.salary = salary if salary else None
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
    school = request.user.school

    teachers = Teacher.objects.select_related('user', 'school').prefetch_related(
        'class_subjects__subject'
    ).filter(school=school)

    if query:
        teachers = teachers.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query)
        )

    # Calculate total salaries
    total_salaries = teachers.filter(salary__isnull=False).aggregate(
        total=models.Sum('salary')
    )['total'] or 0

    paginator = Paginator(teachers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "teachers": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "query": query,
        "total_salaries": total_salaries,
    }
    return render(request, "teachers/teacher_list.html", context)




@login_required
@role_required('principal')
def class_list(request):
    school = request.user.school
    classes = Class.objects.filter(school=school)
    return render(request, "classes/class_list.html", {"classes": classes})



@login_required
@role_required('principal')
def create_class(request):
    school = request.user.school

    if request.method == "POST":
        name = request.POST.get("name")
        form_master_id = request.POST.get("form_master")

        if not name:
            messages.error(request, "Class name is required.")
        else:
            form_master = None
            if form_master_id:
                teacher = Teacher.objects.select_related('user').filter(id=form_master_id, school=school).first()
                if not teacher:
                    messages.error(request, "Selected form master is invalid.")
                    return redirect("principal:create_class")
                form_master = teacher.user  

            class_instance = Class.objects.create(
                name=name,
                form_master=form_master,
                school=school
            )
            messages.success(request, f"Class '{class_instance.name}' created successfully.")
            return redirect("principal:class_list")

    teachers = Teacher.objects.select_related('user').filter(school=school)
    return render(request, "classes/create_class.html", {"teachers": teachers})





@login_required
@role_required('principal')
def edit_class(request, class_id):
    class_instance = get_object_or_404(Class, id=class_id)
    school = request.user.school

    if request.method == "POST":
        name = request.POST.get("name")
        form_master_id = request.POST.get("form_master")

        if not name:
            messages.error(request, "Class name is required.")
        else:
            class_instance.name = name

            if form_master_id:
                teacher = Teacher.objects.select_related('user').filter(id=form_master_id, school=school).first()
                if not teacher:
                    messages.error(request, "Selected form master is invalid.")
                    return redirect("principal:edit_class", class_id=class_id)
                class_instance.form_master = teacher.user
            else:
                class_instance.form_master = None

            class_instance.save()
            messages.success(request, f"Class '{class_instance.name}' updated successfully.")
            return redirect("principal:class_list")

    teachers = Teacher.objects.select_related('user').filter(school=school)
    return render(request, "classes/edit_class.html", {
        "class_instance": class_instance,
        "teachers": teachers
    })




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
    school = request.user.school
    school_class = get_object_or_404(Class, id=class_id, school=school)

    teachers = Teacher.objects.select_related("user").filter(school=school)
    subjects = Subject.objects.filter(school=school)

    if request.method == "POST":
        subject_id = request.POST.get("subject")
        teacher_id = request.POST.get("teacher_id")  

        if not subject_id or not teacher_id:
            messages.error(request, "Please select both a subject and a teacher.")
            return redirect("principal:assign_subject", class_id=class_id)

        subject = get_object_or_404(Subject, id=subject_id, school=school)
        teacher_instance = get_object_or_404(Teacher, id=teacher_id, school=school)
        #teacher_user = teacher_instance.user  # Get CustomUser from Teacher

        if ClassSubject.objects.filter(subject=subject, school_class=school_class).exists():
            messages.warning(request, f"{subject.name} is already assigned to this class.")
        else:
            ClassSubject.objects.create(subject=subject, school_class=school_class, teacher=teacher_instance)
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
    teachers = Teacher.objects.select_related("user").filter(school=request.user.school)

    if request.method == "POST":
        teacher_id = request.POST.get("teacher")
        if not teacher_id:
            messages.error(request, "Please select a teacher.")
        else:
            teacher = get_object_or_404(Teacher, user__id=teacher_id, school=request.user.school)
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
    school = request.user.school
    subjects = Subject.objects.filter(school=school)
    return render(request, "principal/subject_list.html", {"subjects": subjects})


@login_required
@role_required('principal')
def create_subject(request):
    school = request.user.school

    if request.method == "POST":
        name = request.POST.get("name")
        code = request.POST.get("code")
        description = request.POST.get("description")

        if not name:
            messages.error(request, "Subject name is required.")
            return render(request, "principal/create_or_edit_subject.html", {
                "name": name,
                "code": code,
                "description": description
            })

        Subject.objects.create(
            name=name,
            code=code,
            description=description,
            school=school  
        )
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



def grade_customize(request):
    return render(request, 'principal/customize_grade.html')




@login_required
@role_required("principal")
def settings_view(request):
    user = request.user
    try:
        school = user.school
    except School.DoesNotExist:
        messages.error(request, "School settings not found.")
        return redirect("dashboard")

    if request.method == "POST":
        user_form = UserSettingsForm(request.POST, instance=user)
        school_form = SchoolSettingsForm(request.POST, request.FILES, instance=school)

        if user_form.is_valid() and school_form.is_valid():
            user_form.save()
            school_form.save()
            messages.success(request, "Settings updated successfully.")
            return redirect("principal:settings")
    else:
        user_form = UserSettingsForm(instance=user)
        school_form = SchoolSettingsForm(instance=school)

    return render(request, "principal/settings.html", {
        "user_form": user_form,
        "school_form": school_form
    })



@login_required
@role_required('principal')
def expense_list(request):
    school = request.user.school
    category_filter = request.GET.get('category')
    month_filter = request.GET.get('month')

    # Base queryset for all expenses
    expenses = Expense.objects.filter(school=school).select_related('category')
    all_expenses = expenses  # Keep an unfiltered copy for totals

    # Apply filters for display only
    if category_filter and category_filter != 'all':
        expenses = expenses.filter(category__id=category_filter)
    
    if month_filter:
        try:
            year, month = map(int, month_filter.split('-'))
            expenses = expenses.filter(date__year=year, date__month=month)
        except (ValueError, TypeError):
            pass

    # Calculate totals from unfiltered queryset
    total_expenses = all_expenses.aggregate(total=models.Sum('amount'))['total'] or 0
    teacher_salaries = all_expenses.filter(category__name='Teacher Salary').aggregate(
        total=models.Sum('amount'))['total'] or 0
    other_expenses = total_expenses - teacher_salaries

    # Calculate pending salaries
    pending_payments = TeacherSalaryPayment.objects.filter(
        teacher__school=school,
        expense__payment_status='pending'
    )
    pending_salaries = sum(payment.net_salary for payment in pending_payments)

    # Get all expense categories for the filter dropdown
    categories = ExpenseCategory.objects.filter(school=school)

    # Paginate the filtered expenses
    paginator = Paginator(expenses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'expenses': page_obj,
        'categories': categories,
        'total_expenses': total_expenses,
        'teacher_salaries': teacher_salaries,
        'other_expenses': other_expenses,
        'pending_salaries': pending_salaries,
        'selected_category': category_filter,
        'selected_month': month_filter,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'paginator': paginator,
    }

    return render(request, "principal/expenses.html", context)

@login_required
@role_required('principal')
def create_expense(request):
    school = request.user.school

    if request.method == "POST":
        category_choice = request.POST.get('category_choice')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date = request.POST.get('date')
        payment_status = request.POST.get('payment_status')
        payment_date = request.POST.get('payment_date') or None
        receipt = request.FILES.get('receipt')

        try:
            # Handle category (existing or new)
            if category_choice == 'new':
                new_category_name = request.POST.get('new_category_name')
                new_category_description = request.POST.get('new_category_description')
                
                if not new_category_name:
                    raise ValueError("Category name is required when creating a new category")
                
                # Create new category
                category = ExpenseCategory.objects.create(
                    name=new_category_name,
                    description=new_category_description,
                    school=school
                )
            else:
                category_id = request.POST.get('category')
                category = ExpenseCategory.objects.get(id=category_id, school=school)

            # Create the expense
            expense = Expense.objects.create(
                school=school,
                category=category,
                amount=amount,
                description=description,
                date=date,
                payment_status=payment_status,
                payment_date=payment_date,
                receipt=receipt
            )
            messages.success(request, "Expense created successfully.")
            return redirect('principal:expense_list')
        except ExpenseCategory.DoesNotExist:
            messages.error(request, "Selected category does not exist.")
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error creating expense: {str(e)}")

    categories = ExpenseCategory.objects.filter(school=school)
    return render(request, "principal/create_edit_expense.html", {
        'categories': categories,
        'payment_status_choices': Expense.PAYMENT_STATUS,
    })

@login_required
@role_required('principal')
def edit_expense(request, expense_id):
    school = request.user.school
    expense = get_object_or_404(Expense, id=expense_id, school=school)

    if request.method == "POST":
        category_id = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date = request.POST.get('date')
        payment_status = request.POST.get('payment_status')
        payment_date = request.POST.get('payment_date') or None
        receipt = request.FILES.get('receipt')

        try:
            category = ExpenseCategory.objects.get(id=category_id, school=school)
            expense.category = category
            expense.amount = amount
            expense.description = description
            expense.date = date
            expense.payment_status = payment_status
            expense.payment_date = payment_date
            if receipt:
                expense.receipt = receipt
            expense.save()
            messages.success(request, "Expense updated successfully.")
            return redirect('principal:expense_list')
        except (ExpenseCategory.DoesNotExist, ValueError) as e:
            messages.error(request, f"Error updating expense: {str(e)}")

    categories = ExpenseCategory.objects.filter(school=school)
    return render(request, "principal/create_edit_expense.html", {
        'expense': expense,
        'categories': categories,
        'payment_status_choices': Expense.PAYMENT_STATUS,
    })

@login_required
@role_required('principal')
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, school=request.user.school)
    
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Expense deleted successfully.")
        return redirect('principal:expense_list')

    return render(request, "principal/delete_expense_confirm.html", {
        'expense': expense
    })

@login_required
@role_required('principal')
def teacher_salaries(request):
    school = request.user.school
    month_filter = request.GET.get('month')
    status_filter = request.GET.get('status')

    # Get all teachers with their latest salary payments
    teachers = Teacher.objects.filter(school=school).select_related('user')

    if month_filter:
        year, month = map(int, month_filter.split('-'))
        for teacher in teachers:
            teacher.current_month_payment = TeacherSalaryPayment.objects.filter(
                teacher=teacher,
                month__year=year,
                month__month=month
            ).first()
    else:
        # Default to current month
        current_date = timezone.now()
        for teacher in teachers:
            teacher.current_month_payment = TeacherSalaryPayment.objects.filter(
                teacher=teacher,
                month__year=current_date.year,
                month__month=current_date.month
            ).first()

    if status_filter:
        teachers = [t for t in teachers if (
            t.current_month_payment and 
            t.current_month_payment.expense.payment_status == status_filter
        )]

    paginator = Paginator(teachers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'teachers': page_obj,
        'selected_month': month_filter,
        'status': status_filter,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'paginator': paginator,
    }

    return render(request, 'principal/teacher_salary_payment.html', context)


@login_required
@role_required('principal')
def update_salary_payment(request, teacher_id):
    school = request.user.school
    teacher = get_object_or_404(Teacher, id=teacher_id, school=school)
    
    # Get or initialize salary payment
    month = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    year, month = map(int, month.split('-'))
    
    try:
        salary_payment = TeacherSalaryPayment.objects.get(
            teacher=teacher,
            month__year=year,
            month__month=month
        )
    except TeacherSalaryPayment.DoesNotExist:
        salary_payment = None

    if request.method == "POST":
        try:
            basic_salary = float(request.POST.get('basic_salary'))
            allowances = float(request.POST.get('allowances', 0))
            deductions = float(request.POST.get('deductions', 0))
            payment_status = request.POST.get('payment_status')
            payment_date = request.POST.get('payment_date')
            comments = request.POST.get('comments')
            month = request.POST.get('month')

            if not salary_payment:
                salary_payment = TeacherSalaryPayment(teacher=teacher)

            salary_payment.basic_salary = basic_salary
            salary_payment.allowances = allowances
            salary_payment.deductions = deductions
            salary_payment.comments = comments
            salary_payment.month = datetime.strptime(month, '%Y-%m').date()
            
            # Save salary payment first to create/update associated expense
            salary_payment.save()
            
            # Update expense payment status and date
            salary_payment.expense.payment_status = payment_status
            if payment_date:
                salary_payment.expense.payment_date = payment_date
            salary_payment.expense.save()

            messages.success(request, "Salary payment updated successfully.")
            return redirect('principal:teacher_salaries')

        except (ValueError, TypeError) as e:
            messages.error(request, f"Error updating salary payment: {str(e)}")

    context = {
        'teacher': teacher,
        'salary_payment': salary_payment,
        'payment_status_choices': Expense.PAYMENT_STATUS,
    }
    return render(request, 'principal/update_salary_payment.html', context)


@login_required
@role_required('principal')
def process_bulk_payment(request):
    if request.method != "POST":
        return redirect('principal:teacher_salaries')

    school = request.user.school
    selected_teachers = request.POST.get('selected_teachers', '').split(',')
    payment_date = request.POST.get('payment_date')
    comments = request.POST.get('comments')

    try:
        teachers = Teacher.objects.filter(id__in=selected_teachers, school=school)
        current_date = timezone.now()
        
        for teacher in teachers:
            try:
                salary_payment = TeacherSalaryPayment.objects.get(
                    teacher=teacher,
                    month__year=current_date.year,
                    month__month=current_date.month
                )
                
                # Update payment status and date
                salary_payment.expense.payment_status = 'paid'
                salary_payment.expense.payment_date = payment_date
                salary_payment.comments = comments
                salary_payment.expense.save()
                salary_payment.save()
                
            except TeacherSalaryPayment.DoesNotExist:
                # Create new salary payment if it doesn't exist
                salary_payment = TeacherSalaryPayment.objects.create(
                    teacher=teacher,
                    basic_salary=teacher.salary,
                    month=current_date,
                    comments=comments
                )
                salary_payment.expense.payment_status = 'paid'
                salary_payment.expense.payment_date = payment_date
                salary_payment.expense.save()

        messages.success(request, f"Successfully processed payments for {len(teachers)} teachers.")
    except Exception as e:
        messages.error(request, f"Error processing bulk payments: {str(e)}")

    return redirect('principal:teacher_salaries')

@login_required
@role_required('principal')
def export_expenses_excel(request):
    school = request.user.school
    category_filter = request.GET.get('category')
    month_filter = request.GET.get('month')
    
    expenses = Expense.objects.filter(school=school).select_related('category')
    
    if category_filter and category_filter != 'all':
        expenses = expenses.filter(category__id=category_filter)
    
    if month_filter:
        try:
            year, month = map(int, month_filter.split('-'))
            expenses = expenses.filter(date__year=year, date__month=month)
        except (ValueError, TypeError):
            pass

    # Create Excel file
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Add headers
    headers = ['Date', 'Category', 'Description', 'Amount (₦)', 'Status']
    header_format = workbook.add_format({'bold': True, 'bg_color': '#f0f0f0'})
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)

    # Add expense data
    for row, expense in enumerate(expenses, start=1):
        worksheet.write(row, 0, expense.date.strftime('%Y-%m-%d'))
        worksheet.write(row, 1, expense.category.name if expense.category else 'Uncategorized')
        worksheet.write(row, 2, expense.description)
        worksheet.write(row, 3, float(expense.amount))
        worksheet.write(row, 4, expense.get_payment_status_display())

    # Add totals
    total_row = len(expenses) + 2
    worksheet.write(total_row, 2, 'Total:', header_format)
    worksheet.write(total_row, 3, f'=SUM(D2:D{total_row})', workbook.add_format({'bold': True}))

    # Set column widths
    worksheet.set_column('A:A', 12)  # Date
    worksheet.set_column('B:B', 20)  # Category
    worksheet.set_column('C:C', 40)  # Description
    worksheet.set_column('D:D', 15)  # Amount
    worksheet.set_column('E:E', 12)  # Status

    workbook.close()
    output.seek(0)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'expenses_{timestamp}.xlsx'

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
@role_required('principal')
def export_expenses_pdf(request):
    school = request.user.school
    category_filter = request.GET.get('category')
    month_filter = request.GET.get('month')
    
    expenses = Expense.objects.filter(school=school).select_related('category')
    
    if category_filter and category_filter != 'all':
        expenses = expenses.filter(category__id=category_filter)
    
    if month_filter:
        try:
            year, month = map(int, month_filter.split('-'))
            expenses = expenses.filter(date__year=year, date__month=month)
        except (ValueError, TypeError):
            pass

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Create the expense table data
    data = [['Date', 'Category', 'Description', 'Amount (₦)', 'Status']]
    
    for expense in expenses:
        data.append([
            expense.date.strftime('%Y-%m-%d'),
            expense.category.name if expense.category else 'Uncategorized',
            expense.description,
            f"₦{expense.amount:,.2f}",
            expense.get_payment_status_display()
        ])

    # Calculate totals
    total_amount = sum(expense.amount for expense in expenses)
    data.append(['', '', 'Total:', f"₦{total_amount:,.2f}", ''])

    # Create the table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.grey),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'expenses_{timestamp}.pdf'

    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
@role_required('principal')
def create_announcement(request):
    if request.method == "POST":
        title = request.POST.get('title')
        content = request.POST.get('content')
        priority = request.POST.get('priority')
        expiry_date = request.POST.get('expiry_date')

        try:
            announcement = Announcement.objects.create(
                school=request.user.school,
                title=title,
                content=content,
                created_by=request.user,
                priority=priority,
                expiry_date=expiry_date if expiry_date else None
            )
            messages.success(request, "Announcement created successfully.")
            return redirect('principal:principal_dashboard')
        except Exception as e:
            messages.error(request, f"Error creating announcement: {str(e)}")

    return render(request, 'principal/create_announcement.html', {
        'priority_choices': Announcement.PRIORITY_CHOICES
    })

@login_required
@role_required('principal')
def edit_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, school=request.user.school)
    
    if request.method == "POST":
        announcement.title = request.POST.get('title')
        announcement.content = request.POST.get('content')
        announcement.priority = request.POST.get('priority')
        announcement.expiry_date = request.POST.get('expiry_date') or None
        announcement.is_active = request.POST.get('is_active') == 'on'
        
        try:
            announcement.save()
            messages.success(request, "Announcement updated successfully.")
            return redirect('principal:principal_dashboard')
        except Exception as e:
            messages.error(request, f"Error updating announcement: {str(e)}")

    return render(request, 'principal/edit_announcement.html', {
        'announcement': announcement,
        'priority_choices': Announcement.PRIORITY_CHOICES
    })

@login_required
@role_required('principal')
def delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, school=request.user.school)
    
    if request.method == "POST":
        announcement.delete()
        messages.success(request, "Announcement deleted successfully.")
        return redirect('principal:principal_dashboard')

    return render(request, 'principal/delete_announcement_confirm.html', {
        'announcement': announcement
    })




