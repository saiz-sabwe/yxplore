# ModuleFlight/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import FlightView

app_name = 'module_flight'  # Changé pour éviter le conflit de namespace

urlpatterns = [
    # Pages principales du module Flight
    path('', FlightView.as_view(), {'param': 'search'}, name='search_flight'),
    path('search/', FlightView.as_view(), {'param': 'search'}, name='flight_search'),
    path('results/', FlightView.as_view(), {'param': 'results'}, name='flight_results'),
    path('detail/<str:offer_id>/', FlightView.as_view(), {'param': 'flight_detail'}, name='flight_detail'),
    
    # Actions AJAX
    path('book/', FlightView.as_view(), {'param': 'book'}, name='book'),
    path('pay/<uuid:booking_id>/', FlightView.as_view(), {'param': 'pay_booking'}, name='pay_booking'),
    path('cancel/', FlightView.as_view(), {'param': 'cancel'}, name='flight_cancel'),
    
    # Rétrocompatibilité
    path('Flight/', FlightView.as_view(), {'param': 'Flight'}, name='Flight'),
]

# Configuration du router DRF pour l'API REST (optionnel - décommenté si nécessaire)
try:
    from .api_views import (
        TravelAgencyViewSet, 
        MerchantAgencyViewSet, 
        FlightBookingViewSet,
        FlightSearchAPIView
    )
    
    router = DefaultRouter()
    router.register(r'agencies', TravelAgencyViewSet, basename='agency')
    router.register(r'merchant-agencies', MerchantAgencyViewSet, basename='merchant-agency')
    router.register(r'bookings', FlightBookingViewSet, basename='booking')
    
    # Ajouter les routes API
    urlpatterns += [
        path('api/', include(router.urls)),
        path('api/search/', FlightSearchAPIView.as_view(), name='api_flight_search'),
    ]
except ImportError:
    # Si les API views ne sont pas disponibles, continuer sans elles
    pass