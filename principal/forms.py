from django import forms
from stu_main.models import *

class StudentCreationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    student_class = forms.ModelChoiceField(queryset=Class.objects.all(), required=True)
    photo = forms.ImageField(required=False)
    phone_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'photo', 'phone_number', 'student_class']
