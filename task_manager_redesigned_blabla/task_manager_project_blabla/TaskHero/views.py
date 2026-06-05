from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Task
from .forms import TaskForm
# Create your views here.

def home(request):
    return render(request, 'taskhero/index.html')

@login_required
def create_task(request):
    form = TaskForm()
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.added_by = request.user
            messages.success(request, "Task created successfully!")
            messages.error(request, "Please correct the errors below.")
            task.save()
            return redirect('taskhero:dashboard')
        
    return render(request, 'taskhero/create-task.html', {'form': form})

@login_required
def task_detail(request, task_pk):
    task = get_object_or_404(Task, pk = task_pk, added_by=request.user)
    return render(request, 'taskhero/task-detail.html', {'task': task})


@login_required
def dashboard(request):
    tasks = Task.objects.filter(added_by=request.user)
    return render(request, 'taskhero/dashboard.html', {'tasks': tasks})

@login_required
def update_task(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, added_by=request.user)
    form = TaskForm(instance=task)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('taskhero:task_detail', task_pk=task.pk)
    
    context = {
        'task': task,
        'form': form
    }
    return render(request, 'taskhero/update.html', context)
        
@login_required
def confirm_delete(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, added_by=request.user)
    return render (request, 'taskhero/confirm-delete.html', {'task': task})

@login_required
def delete(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, added_by=request.user)
    if request.method == 'POST':
        task.delete()
    return redirect('taskhero:dashboard')

@login_required
def mark_completed(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk, added_by=request.user)
    task.status = 'cmp'
    task.save()
    return redirect('taskhero:task_detail', task_pk=task.pk)
