from django.urls import path
from . import views

app_name = 'taskhero'

urlpatterns = [
    path('', views.home, name='home'),
    path('task-detail/<int:task_pk>/', views.task_detail, name='task_detail'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-task/', views.create_task, name='create_task'),
    path('update-task/<int:task_pk>', views.update_task, name='update_task'),
    path('confirm-delete/<int:task_pk>', views.confirm_delete, name='confirm_delete'),
    path('delete-task/<int:task_pk>', views.delete, name='delete'),
    path('completed/<int:task_pk>', views.mark_completed, name='mark_completed'),
]