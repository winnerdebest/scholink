from django.urls import path
from .views import *


urlpatterns = [
    path('', student_dashboard, name='student_dashboard'),
    path("create-post/", create_post, name="create_post"),
    path('profile/', profile, name='profile'),
    path("post/<int:post_id>/like/", like_post, name="like_post"),
    path("post/<int:post_id>/dislike/", dislike_post, name="dislike_post"),

]
