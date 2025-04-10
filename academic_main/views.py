from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import *
from exams.models import *


def user_login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            # Find the user by email
            user = CustomUser.objects.get(email=email)
            
            # Authenticate the user
            user = authenticate(request, username=user.username, password=password)

            if user is not None:
                login(request, user)
                
                # Redirect to different dashboards based on user_type
                if user.user_type == 'student':
                    return redirect('student_dashboard')
                #elif user.user_type == 'teacher':
                 #   return redirect('teachers:teacher_dashboard')
                #elif user.user_type == 'admin':
                    #return redirect('admin_dashboard:admin_dashboard')
                #elif user.user_type == 'principal':
                    #return redirect('principals:principal_dashboard')
                else:
                    messages.error(request, "Invalid user type.")
                    return redirect('user_login')
            else:
                messages.error(request, "Invalid credentials. Please try again.")
        except CustomUser.DoesNotExist:
            messages.error(request, "No user found with this email.")

    return render(request, "login.html")


@login_required
def user_logout_view(request):
    logout(request)
    return redirect('user_login')

