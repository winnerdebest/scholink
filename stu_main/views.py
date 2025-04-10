from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
from .models import *
from exams.models import *

from .decorators import student_required

 


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


@login_required
@student_required
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
@student_required
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
@student_required
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
@student_required
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
@student_required
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

