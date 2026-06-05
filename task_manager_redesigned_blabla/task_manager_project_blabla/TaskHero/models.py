from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone

# Create your models here.

User = get_user_model()
class Task(models.Model):
    class Status(models.TextChoices):
        TO_DO = 'td', 'To Do'
        IN_PROGRESS = 'ip', 'In Progress'
        COMPLETED = 'cmp', 'Completed'
    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'mid', 'Medium'
        HIGH = 'high', 'High'
    title = models.CharField(max_length=100)
    description = models.TextField()
    due_date = models.DateField()
    status = models.CharField(max_length=3, choices=Status, default=Status.TO_DO)
    priority = models.CharField(max_length=4, choices=Priority, default=Priority.MEDIUM)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)

    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    @property
    def is_overdue(self):
        if self.due_date and self.status != self.Status.COMPLETED:
            return self.due_date < timezone.now().date()
        return False
