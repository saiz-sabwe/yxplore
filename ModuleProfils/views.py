
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import ClientProfile, MerchantProfile, AdminProfile
import re



# Create your views here.
def index(request):
    """Vue simple pour la page d'accueil du module profils"""
    return render(request, 'ModuleProfils/index.html', {
        'title': 'Module Profils - YXPLORE'
    })
class AuthView(View):

    def get(self, request, param=None):
        if param == "login":
            return self.login(request)
        elif param == "register":
            return self.register(request)
        else:
            return None

    def post(self, request, param=None):
        response_data = {}
        print("******request: ", request.POST)

        if request.META.get('HTTP_X_REQUESTED_WITH') == "XMLHttpRequest":
            action = request.POST.get('op', '')
            print("******action: ", action)
            if action == "connexion":
                return self.connexion(request)
            elif action == "inscription":
                return self.inscription(request)
            else:
                response_data['resultat'] = "FAIL"
                response_data['message'] = "Action non reconnue"
                return JsonResponse(response_data, status=400)

        else:
            response_data['resultat'] = "FAIL"
            response_data['message'] = "Requête AJAX requise"
            return JsonResponse(response_data, status=400)

    def login(self, request):

        print("******login request: ")
        context = {

        }

        return render(request, "YXPLORE_NODE/auth/sign-in.html", context)

    def register(self, request):

        context = {

        }

        return render(request, "YXPLORE_NODE/auth/sign-up.html", context)

    def connexion(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': 'Nom d\'utilisateur et mot de passe requis.'
            }, status=400)

        # Essayer d'abord l'authentification avec le username
        user = authenticate(request, username=username, password=password)
        
        # Si échec et que le username ressemble à un email, essayer de trouver l'utilisateur par email
        if user is None and '@' in username:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is None:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': 'Email/nom d\'utilisateur ou mot de passe invalide.'
            }, status=400)

        if not user.is_active:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': 'Votre compte est désactivé.'
            }, status=403)

        auth_login(request, user)

        # Déterminer le type de profil et la redirection
        redirect_url = self.get_user_redirect_url(user)

        return JsonResponse({
            'resultat': 'SUCCESS',
            'message': 'Connexion réussie !',
            'redirect_url': redirect_url,
        }, status=200)

    def get_user_redirect_url(self, user):
        """Détermine l'URL de redirection basée sur le type de profil utilisateur"""
        
        # Vérifier si l'utilisateur a un profil client
        if hasattr(user, 'clientprofile_profile'):
            return reverse('profils:index')  # Dashboard client à créer
        
        # Vérifier si l'utilisateur a un profil marchand
        elif hasattr(user, 'merchantprofile_profile'):
            return reverse('profils:index')  # Dashboard marchand à créer
        
        # Vérifier si l'utilisateur a un profil admin
        elif hasattr(user, 'adminprofile_profile'):
            return '/admin/'  # Interface d'administration Django
        
        # Si l'utilisateur n'a pas de profil spécifique, rediriger vers l'index
        else:
            return reverse('profils:index')

    def inscription(self, request):
        """Gestion de l'inscription des utilisateurs avec choix du type de compte"""
        try:
            # Récupération des données
            account_type = request.POST.get('account_type', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip()

            # Validation des données de base
            if not account_type or not email or not password:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Tous les champs sont requis.'
                }, status=400)

            # Validation du type de compte
            if account_type not in ['client', 'merchant']:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Type de compte invalide.'
                }, status=400)

            # Validation de l'email
            if not self.validate_email(email):
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Format d\'email invalide.'
                }, status=400)

            # Validation du mot de passe
            if len(password) < 6:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Le mot de passe doit contenir au moins 6 caractères.'
                }, status=400)

            # Vérification de l'unicité de l'email
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Cette adresse email est déjà utilisée.'
                }, status=409)

            # Générer un nom d'utilisateur unique basé sur l'email
            username = self.generate_username_from_email(email)

            # Création de l'utilisateur et du profil
            with transaction.atomic():
                # Créer l'utilisateur Django
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name='',  # Vide par défaut
                    last_name=''    # Vide par défaut
                )

                # Créer le profil correspondant au type de compte choisi
                if account_type == 'client':
                    ClientProfile.create_from_user_data(
                        user=user,
                        first_name='',  # À compléter lors du KYC
                        last_name='',   # À compléter lors du KYC
                        phone=None      # À compléter lors du KYC
                    )
                elif account_type == 'merchant':
                    # Générer un nom d'entreprise temporaire basé sur l'email
                    temp_company_name = f"Entreprise de {email.split('@')[0]}"
                    MerchantProfile.create_from_registration_data(
                        user=user,
                        company_name=temp_company_name,  # Nom temporaire
                        business_type=MerchantProfile.BUSINESS_TRAVEL_AGENCY,  # Par défaut
                        contact_phone=None  # À compléter lors du KYC
                    )

                # Connecter automatiquement l'utilisateur
                auth_login(request, user)

            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'Votre compte a été créé avec succès !',
                'redirect_url': self.get_user_redirect_url(user)
            }, status=201)

        except Exception as e:
            print(f"Erreur lors de l'inscription: {e}")
            return JsonResponse({
                'resultat': 'FAIL',
                'message': 'Une erreur est survenue lors de la création du compte.'
            }, status=500)

    def generate_username_from_email(self, email):
        """Génère un nom d'utilisateur unique basé sur l'email"""
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
            
        return username

    def validate_email(self, email):
        """Validation simple de l'email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
