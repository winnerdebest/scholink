from django.urls import path
from .views import *


urlpatterns = [
    path("<int:exam_id>/", take_exam, name="take_exam"),
    path("<int:exam_id>/question/<int:question_index>/", get_question, name="get_question"),
    path("save-answer/", save_answer, name="save-answer"),
    path('<int:exam_id>/result/', exam_result, name='exam-result'),
]
