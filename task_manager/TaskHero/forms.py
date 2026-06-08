from django import forms
from .models import Task
from django.core.exceptions import ValidationError
from datetime import date


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'status', 'priority']
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Add a description (optional)', 'rows': 3}),
            'due_date':    forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status':      forms.Select(attrs={'class': 'form-control form-select'}),
            'priority':    forms.Select(attrs={'class': 'form-control form-select'}),
        }

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < date.today():
            raise ValidationError("Due date cannot be in the past.")
        return due_date
