from django.urls import path
from . import views

urlpatterns = [
    path('api/todos/', views.todo_list, name='todo_list'),
    path('api/todos/<str:todo_id>/', views.todo_detail, name='todo_detail'),
    path('api/todos/contexts/', views.todo_contexts, name='todo_contexts'),
]