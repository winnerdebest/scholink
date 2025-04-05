from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from .models import *



@login_required
def student_dashboard(request):
    user = request.user
    student = user.student_profile if hasattr(user, 'student_profile') else None
    posts = StudentPost.objects.all().order_by('-created_at')
    
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


def profile(request):
    return render(request, 'profile.html')