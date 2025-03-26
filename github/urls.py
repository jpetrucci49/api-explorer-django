from django.urls import path
from . import views

urlpatterns = [
    path('github', views.get_github_user, name='get_github_user'),
]