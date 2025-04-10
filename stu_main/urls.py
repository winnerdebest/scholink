from django.urls import path
from .views import *


urlpatterns = [
    path('', student_dashboard, name='student_dashboard'),
    path("create-post/", create_post, name="create_post"),
    path('profile/', profile, name='profile'),
    path("post/<int:post_id>/like/", like_post, name="like_post"),
    path("post/<int:post_id>/dislike/", dislike_post, name="dislike_post"),

    path('assignments/', assignments, name='assignments'),
    path('assignment/<int:assignment_id>/', take_assignment, name='take-assignment'),
    path('assignment/<int:assignment_id>/question/<int:question_index>/', get_assignment_question, name='get-assignment-question'),
    path('assignment/save-answer/', save_assignment_answer, name='save-assignment-answer'),
    path('assignment/<int:assignment_id>/result/', assignment_result, name='assignment-result'),
]
