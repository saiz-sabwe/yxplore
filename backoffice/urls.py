from django.urls import path

from . import views

urlpatterns = [
    path("backoffice/", views.index, name="index"),
]