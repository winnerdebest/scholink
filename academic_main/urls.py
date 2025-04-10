from django.urls import path
from .views import *


urlpatterns = [
    path('', user_login_view, name='user_login'),
    path('logout/', user_logout_view, name='user_logout'),
]
