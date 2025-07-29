# ModuleFlight/urls.py
from django.urls import path

from ModuleFlight.views import FlightView

app_name = 'hotels'

urlpatterns = [
    # Liste des hôtels

    path('', FlightView.as_view(), {'param': 'hotel'}, name='hotel'),

]
