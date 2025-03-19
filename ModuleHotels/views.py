from django.shortcuts import render

# Create your views here.

def index(request):
    context = {
        "title": 'titre de la vue'
    }
    return render(request, "backoffice/index.html", context)