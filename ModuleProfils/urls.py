from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views
from .views import AuthView

app_name = 'profils'

urlpatterns = [
    path('', views.index, name='index'),

    path('login/', AuthView.as_view(), {'param': 'login'}, name='login'),
    path('register/', AuthView.as_view(), {'param': 'register'}, name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('way/', AuthView.as_view(), name="way"),
]
