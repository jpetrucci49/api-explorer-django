from django.urls import path
from . import views

urlpatterns = [
    path('github', views.get_github_user, name='get_github_user'),
    path('analyze', views.analyze, name='analyze'),
    path('clear-cache', views.clear_cache, name='clear_cache'),
]