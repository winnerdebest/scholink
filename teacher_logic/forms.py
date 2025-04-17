from django import forms
from academic_main.models import *
from exams.models import *
from assignments.models import *
from stu_main.models import *
from django.forms import modelformset_factory

# Tailwind utility classes
BASE_INPUT = 'w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-gray-800 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100'
BASE_CHECKBOX = 'h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded dark:bg-gray-700 dark:border-gray-600'
BASE_TEXTAREA = 'w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-gray-800 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100'
BASE_FILE = 'block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-100 file:text-primary-700 hover:file:bg-primary-200 dark:text-gray-400 dark:file:bg-primary-900 dark:file:text-primary-300'

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['duration_minutes', 'is_active']
        widgets = {
            'duration_minutes': forms.NumberInput(attrs={
                'class': BASE_INPUT,
                'placeholder': 'e.g. 45 (in minutes)',
                'min': '1',
                'max': '300'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': BASE_CHECKBOX,
            }),
        }
        labels = {
            'duration_minutes': 'Duration (minutes)',
            'is_active': 'Activate this exam',
        }
        help_texts = {
            'duration_minutes': 'Set a time between 1 and 300 minutes',
        }

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['is_active']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={
                'class': BASE_CHECKBOX,
            }),
        }
        labels = {
            'is_active': 'Activate this assignment',
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        exclude = ['exam', 'assignment', 'created_by']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': BASE_TEXTAREA,
                'rows': 3,
                'placeholder': 'Write the question here...'
            }),
            'option_a': forms.TextInput(attrs={
                'class': BASE_INPUT,
                'placeholder': 'Option A'
            }),
            'option_b': forms.TextInput(attrs={
                'class': BASE_INPUT,
                'placeholder': 'Option B'
            }),
            'option_c': forms.TextInput(attrs={
                'class': BASE_INPUT,
                'placeholder': 'Option C'
            }),
            'option_d': forms.TextInput(attrs={
                'class': BASE_INPUT,
                'placeholder': 'Option D'
            }),
            'correct_option': forms.Select(attrs={
                'class': BASE_INPUT,
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': BASE_FILE
            }),
        }
        labels = {
            'text': 'Question',
            'option_a': 'Option A',
            'option_b': 'Option B',
            'option_c': 'Option C',
            'option_d': 'Option D',
            'correct_option': 'Correct Answer',
            'image': 'Optional Image'
        }

# Enhance delete checkbox styling in the formset
class BaseQuestionFormSet(forms.BaseModelFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        if self.can_delete:
            form.fields['DELETE'].widget.attrs.update({
                'class': BASE_CHECKBOX
            })

QuestionFormSet = modelformset_factory(
    Question,
    form=QuestionForm,
    formset=BaseQuestionFormSet,
    extra=1,
    can_delete=True
)
