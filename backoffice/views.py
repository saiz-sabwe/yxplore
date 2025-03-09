from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

# Create your views here.


def index(request):
    context = {
        "title": 'titre de la vue'
    }
    return render(request, "backoffice/index.html", context)
