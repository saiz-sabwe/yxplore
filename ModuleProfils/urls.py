from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views
from .views import AuthView, KYCView

app_name = 'profils'

urlpatterns = [
    path('', views.index, name='index'),

    # Routes d'authentification
    path('login/', AuthView.as_view(), {'param': 'login'}, name='login'),
    path('register/', AuthView.as_view(), {'param': 'register'}, name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('way/', AuthView.as_view(), {'param': 'way'}, name="way"),
    
    # Routes KYC - Structure similaire à QuizView
    path('kyc/', KYCView.as_view(), {'param': 'general'}, name='kyc_general'),
    path('kyc/client/', KYCView.as_view(), {'param': 'client'}, name='kyc_client'),
    path('kyc/merchant/', KYCView.as_view(), {'param': 'merchant'}, name='kyc_merchant'),
    path('kyc/admin/', KYCView.as_view(), {'param': 'admin'}, name='kyc_admin'),
    
    # Routes KYC avec ID spécifique (pour les admins)
    path('kyc/client/<str:client_id>/', KYCView.as_view(), {'param': 'client'}, name='kyc_client_detail'),
    path('kyc/merchant/<str:merchant_id>/', KYCView.as_view(), {'param': 'merchant'}, name='kyc_merchant_detail'),
    path('kyc/validation/<str:profile_id>/', KYCView.as_view(), {'param': 'validation'}, name='kyc_validation'),
]
