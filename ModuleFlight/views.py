from django.shortcuts import render
from django.views import View


# Create your views here.

class FlightView(View):
    def get(self, request, param=None):
        if param == "hotel":
            return self.afficherHotel(request)
        else:
            return None

    def post(self, request):
        pass

    def afficherHotel(self, request):
        context = {
            'title': 'Hotel',
        }


        return render(request, "ModuleFlight/affiche.html", context)
