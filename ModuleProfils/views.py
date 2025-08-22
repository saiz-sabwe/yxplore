
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.core.exceptions import ValidationError
from .models import ClientProfile, MerchantProfile, AdminProfile, KYCValidation, UserProfileManager, ProfileUtils
import re
import json


# Create your views here.
def index(request):
    """Vue simple pour la page d'accueil du module profils"""
    return render(request, 'ModuleProfils/index.html', {
        'title': 'Module Profils - YXPLORE'
    })

class AuthView(View):
    """Vue pour l'authentification des utilisateurs"""

    def get(self, request, param=None):
        if param == "login":
            return self.afficherLogin(request)
        elif param == "register":
            return self.afficherRegister(request)
        elif param == "way":
            return self.afficherWay(request)
        else:
            return redirect('profils:index')

    def post(self, request, param=None):
        response_data = {}
        print("******request: ", request.POST)

        if request.META.get('HTTP_X_REQUESTED_WITH') == "XMLHttpRequest":
            action = request.POST.get('op', '')
            print("******action: ", action)
            
            if action == "login" or action == "connexion":
                return self.authentifierUtilisateur(request)
            elif action == "register" or action == "inscription":
                return self.creerUtilisateur(request)
            else:
                response_data['resultat'] = "FAIL"
                response_data['message'] = "Action non reconnue"
                return JsonResponse(response_data, status=400)
        else:
            response_data['resultat'] = "FAIL"
            response_data['message'] = "Requête AJAX requise"
            return JsonResponse(response_data, status=400)

    def afficherLogin(self, request):
        """Affiche la page de connexion"""
        if request.user.is_authenticated:
            return redirect('profils:index')
        
        return render(request, 'YXPLORE_NODE/auth/sign-in.html', {
            'title': 'Connexion - YXPLORE'
        })

    def afficherRegister(self, request):
        """Affiche la page d'inscription"""
        if request.user.is_authenticated:
            return redirect('profils:index')
        
        return render(request, 'YXPLORE_NODE/auth/sign-up.html', {
            'title': 'Inscription - YXPLORE'
        })

    def afficherWay(self, request):
        """Affiche la page way"""
        return render(request, 'ModuleProfils/index.html', {
            'title': 'Way - YXPLORE'
        })

    def authentifierUtilisateur(self, request):
        """Authentifie un utilisateur"""
        try:
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            
            if not username or not password:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Nom d\'utilisateur et mot de passe requis'
                })
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                auth_login(request, user)
                return JsonResponse({
                    'resultat': 'SUCCESS',
                    'message': 'Connexion réussie',
                    'redirect_url': reverse('profils:index')
                })
            else:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Nom d\'utilisateur ou mot de passe incorrect'
                })
                
        except Exception as e:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': f'Erreur lors de l\'authentification: {str(e)}'
            })

    def creerUtilisateur(self, request):
        """Crée un nouvel utilisateur"""
        try:
            username = request.POST.get('username', request.POST.get('email', ''))
            email = request.POST.get('email', '')
            password = request.POST.get('password', '')
            profile_type = request.POST.get('account_type', request.POST.get('profile_type', 'client'))
            
            if not username or not email or not password:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Tous les champs sont requis'
                })
            
            # VÉRIFICATION D'UNICITÉ : Un utilisateur ne peut pas être à la fois client et merchant
            if profile_type == 'client':
                # Vérifier si l'utilisateur a déjà un profil merchant
                if User.objects.filter(username=username).exists():
                    existing_user = User.objects.get(username=username)
                    if MerchantProfile.user_has_profile(existing_user):
                        return JsonResponse({
                            'resultat': 'FAIL',
                            'message': 'Un utilisateur ne peut pas être à la fois client et marchand. Supprimez d\'abord le profil marchand.'
                        })
            elif profile_type == 'merchant':
                # Vérifier si l'utilisateur a déjà un profil client
                if User.objects.filter(username=username).exists():
                    existing_user = User.objects.get(username=username)
                    if ClientProfile.user_has_profile(existing_user):
                        return JsonResponse({
                            'resultat': 'FAIL',
                            'message': 'Un utilisateur ne peut pas être à la fois marchand et client. Supprimez d\'abord le profil client.'
                        })
            
            # Vérifier si l'utilisateur existe déjà
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Ce nom d\'utilisateur existe déjà'
                })
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Cet email est déjà utilisé'
                })
            
            # Créer l'utilisateur avec son profil selon le type
            if profile_type == 'client':
                user, profile = ClientProfile.create_user_with_profile(
                    username=username, email=email, password=password
                )
            elif profile_type == 'merchant':
                company_name = request.POST.get('company_name', 'Entreprise')
                user, profile = MerchantProfile.create_user_with_profile(
                    username=username, email=email, password=password, 
                    company_name=company_name
                )
            elif profile_type == 'admin':
                user, profile = AdminProfile.create_user_with_profile(
                    username=username, email=email, password=password
                )
            else:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Type de profil invalide'
                }, status=400)
            
            # Connecter l'utilisateur
            auth_login(request, user)
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'Compte créé avec succès',
                'redirect_url': reverse('profils:index')
            })
                
        except Exception as e:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': f'Erreur lors de la création du compte: {str(e)}'
            })

class KYCView(View):
    """Vue pour la gestion KYC des profils client et merchant"""

    def get(self, request, param=None, client_id=None, merchant_id=None, profile_id=None):
        if param == "client":
            return self.afficherKYCClient(request, client_id)
        elif param == "merchant":
            return self.afficherKYCMerchant(request, merchant_id)
        elif param == "admin":
            return self.afficherKYCAdmin(request)
        elif param == "validation":
            return self.afficherValidationKYC(request, profile_id)
        elif param == "general":
            return self.afficherKYCGeneral(request)
        else:
            return self.afficherKYCGeneral(request)

    def post(self, request, param=None, **kwargs):
        response_data = {}

        # Debug: Afficher les en-têtes et données reçues
        print(f"DEBUG KYC POST: HTTP_X_REQUESTED_WITH = {request.META.get('HTTP_X_REQUESTED_WITH')}")
        print(f"DEBUG KYC POST: Action = {request.POST.get('op', 'NO_OP')}")
        print(f"DEBUG KYC POST: Profile type = {request.POST.get('profile_type', 'NO_TYPE')}")

        if request.META.get('HTTP_X_REQUESTED_WITH') == "XMLHttpRequest":
            action = request.POST.get('op', '')
            
            if action == "submit_kyc":
                return self.soumettreKYC(request)
            elif action == "validate_kyc":
                return self.validerKYC(request)
            elif action == "reject_kyc":
                return self.rejeterKYC(request)
            elif action == "approve_document":
                return self.approuverDocument(request)
            elif action == "reject_document":
                return self.rejeterDocument(request)
            elif action == "update_profile":
                return self.mettreAJourProfil(request)
            elif action == "profile_data":
                return self.recupererDonneesProfil(request)
            else:
                response_data['resultat'] = "FAIL"
                response_data['message'] = "Action non reconnue"
                return JsonResponse(response_data, status=400)
        else:
            # Si ce n'est pas reconnu comme AJAX mais que l'opération est submit_kyc, traiter quand même
            action = request.POST.get('op', '')
            if action == "submit_kyc":
                print("DEBUG: Traitement de submit_kyc même sans en-tête AJAX")
                return self.soumettreKYC(request)
            
            response_data['resultat'] = "FAIL"
            response_data['message'] = "Requête AJAX requise"
            return JsonResponse(response_data, status=400)

    def afficherKYCGeneral(self, request):
        """Affiche la page générale de gestion KYC"""
        if not request.user.is_authenticated:
            return redirect('profils:login')
        
        context = {
            'title': 'Gestion KYC - YXPLORE',
            'user': request.user
        }
        return render(request, 'ModuleProfils/kyc/general.html', context)

    def afficherKYCClient(self, request, client_id=None):
        """Affiche le KYC d'un client spécifique ou du client connecté"""
        if not request.user.is_authenticated:
            return redirect('profils:login')
        
        if client_id and AdminProfile.user_has_profile(request.user):
            # Admin qui consulte un client spécifique
            try:
                client_profile = ClientProfile.objects.get(id=client_id)
                profile_user = client_profile.user
            except ClientProfile.DoesNotExist:
                return JsonResponse({'resultat': 'FAIL', 'message': 'Client non trouvé'}, status=404)
        else:
            # Client qui consulte son propre profil
            # Vérifier d'abord si l'utilisateur est un client
            if not ClientProfile.user_has_profile(request.user):
                return redirect('profils:index')
            
            # Utiliser les nouvelles classes utilitaires
            client_profile = ClientProfile.get_profile_for_user(request.user)
            if not client_profile:
                # L'utilisateur n'est pas un client, rediriger vers l'index
                return redirect('profils:index')
        
        context = {
            'title': f'KYC Client - {request.user.username}',
            'profile': client_profile,
            'profile_user': request.user,
            'is_admin_view': client_id is not None and AdminProfile.user_has_profile(request.user)
        }
        return render(request, 'ModuleProfils/kyc/client.html', context)

    def afficherKYCMerchant(self, request, merchant_id=None):
        """Affiche le KYC d'un marchand spécifique ou du marchand connecté"""
        if not request.user.is_authenticated:
            return redirect('profils:login')
        
        if merchant_id and AdminProfile.user_has_profile(request.user):
            # Admin qui consulte un marchand spécifique
            try:
                merchant_profile = MerchantProfile.objects.get(id=merchant_id)
                profile_user = merchant_profile.user
            except MerchantProfile.DoesNotExist:
                return JsonResponse({'resultat': 'FAIL', 'message': 'Marchand non trouvé'}, status=404)
        else:
            # Marchand qui consulte son propre profil
            # Vérifier d'abord si l'utilisateur est un marchand
            if not MerchantProfile.user_has_profile(request.user):
                return redirect('profils:index')
            
            # Utiliser les nouvelles classes utilitaires
            merchant_profile = MerchantProfile.get_profile_for_user(request.user)
            if not merchant_profile:
                # L'utilisateur n'est pas un marchand, rediriger vers l'index
                return redirect('profils:index')
        
        context = {
            'title': f'KYC Marchand - {request.user.username}',
            'profile': merchant_profile,
            'profile_user': request.user,
            'is_admin_view': merchant_id is not None and AdminProfile.user_has_profile(request.user)
        }
        return render(request, 'ModuleProfils/kyc/merchant.html', context)

    def afficherKYCAdmin(self, request):
        """Affiche la page d'administration KYC pour les admins"""
        if not request.user.is_authenticated or not AdminProfile.user_has_profile(request.user):
            return redirect('profils:index')
        
        # Récupérer les profils en attente de validation
        pending_clients = ClientProfile.objects.filter(kyc_status=ClientProfile.KYC_PENDING)
        pending_merchants = MerchantProfile.objects.filter(kyc_status=MerchantProfile.KYC_PENDING)
        
        context = {
            'title': 'Administration KYC - YXPLORE',
            'pending_clients': pending_clients,
            'pending_merchants': pending_merchants,
            'admin_user': request.user
        }
        return render(request, 'ModuleProfils/kyc/admin.html', context)

    def afficherValidationKYC(self, request, profile_id):
        """Affiche la page de validation KYC pour un profil spécifique"""
        if not request.user.is_authenticated or not AdminProfile.user_has_profile(request.user):
            return redirect('profils:index')
        
        try:
            # Essayer de trouver le profil (client ou merchant)
            try:
                profile = ClientProfile.objects.get(id=profile_id)
                profile_type = 'client'
            except ClientProfile.DoesNotExist:
                try:
                    profile = MerchantProfile.objects.get(id=profile_id)
                    profile_type = 'merchant'
                except MerchantProfile.DoesNotExist:
                    return JsonResponse({'resultat': 'FAIL', 'message': 'Profil non trouvé'}, status=404)
            
            context = {
                'title': f'Validation KYC - {profile_type.title()}',
                'profile': profile,
                'profile_type': profile_type,
                'admin_user': request.user
            }
            return render(request, 'ModuleProfils/kyc/validation.html', context)
            
        except Exception as e:
            return JsonResponse({'resultat': 'FAIL', 'message': str(e)}, status=500)

    def recupererDonneesProfil(self, request):
        """Récupère les données du profil pour l'affichage AJAX"""
        if not request.user.is_authenticated:
            return JsonResponse({'resultat': 'FAIL', 'message': 'Non authentifié'}, status=401)
        
        try:
            profile_data = {}
            
            # Utiliser les nouvelles classes utilitaires pour déterminer le type de profil
            user_type = UserProfileManager.determine_user_type(request.user)
            if user_type == 'client':
                client_profile = ClientProfile.get_profile_for_user(request.user)
                profile_data = {
                    'profile_type': 'client',
                    'display_name': client_profile.get_full_name(),
                    'kyc_status': client_profile.kyc_status,
                    'kyc_completion_percentage': client_profile.get_kyc_completion_percentage(),
                    'missing_fields': client_profile.get_missing_kyc_fields(),
                    'documents': self.getClientDocuments(client_profile)
                }
            elif user_type == 'merchant':
                merchant_profile = MerchantProfile.get_profile_for_user(request.user)
                profile_data = {
                    'profile_type': 'merchant',
                    'display_name': merchant_profile.get_company_display_name(),
                    'kyc_status': merchant_profile.kyc_status,
                    'kyc_completion_percentage': merchant_profile.get_kyc_completion_percentage(),
                    'missing_fields': merchant_profile.get_missing_kyc_fields(),
                    'documents': self.getMerchantDocuments(merchant_profile)
                }
            else:
                return JsonResponse({'resultat': 'FAIL', 'message': 'Aucun profil trouvé'}, status=404)
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'profile': profile_data
            })
            
        except Exception as e:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': f'Erreur lors de la récupération: {str(e)}'
            }, status=500)

    def getClientDocuments(self, client_profile):
        """Récupère les documents d'un profil client"""
        documents = []
        
        if client_profile.document:
            documents.append({
                'id': f'client_{client_profile.id}_id',
                'name': 'Document d\'identité',
                'type': 'Document d\'identité',
                'url': client_profile.document.url,
                'status': 'pending',
                'upload_date': client_profile.create.strftime('%d/%m/%Y')
            })
        
        return documents

    def getMerchantDocuments(self, merchant_profile):
        """Récupère les documents d'un profil merchant"""
        documents = []
        
        if merchant_profile.business_license:
            documents.append({
                'id': f'merchant_{merchant_profile.id}_license',
                'name': 'Licence commerciale',
                'type': 'Licence commerciale',
                'url': merchant_profile.business_license.url,
                'status': 'pending',
                'upload_date': merchant_profile.create.strftime('%d/%m/%Y')
            })
        
        if merchant_profile.company_registration_doc:
            documents.append({
                'id': f'merchant_{merchant_profile.id}_registration',
                'name': 'Document d\'enregistrement',
                'type': 'Document d\'enregistrement',
                'url': merchant_profile.company_registration_doc.url,
                'status': 'pending',
                'upload_date': merchant_profile.create.strftime('%d/%m/%Y')
            })
        
        if merchant_profile.tax_certificate:
            documents.append({
                'id': f'merchant_{merchant_profile.id}_tax',
                'name': 'Certificat fiscal',
                'type': 'Certificat fiscal',
                'url': merchant_profile.tax_certificate.url,
                'status': 'pending',
                'upload_date': merchant_profile.create.strftime('%d/%m/%Y')
            })
        
        return documents

    def soumettreKYC(self, request):
        """Soumet un formulaire KYC (client ou merchant)"""
        try:
            profile_type = request.POST.get('profile_type')
            
            if profile_type == 'client':
                return self.soumettreKYCClient(request)
            elif profile_type == 'merchant':
                return self.soumettreKYCMerchant(request)
            else:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Type de profil invalide'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': f'Erreur lors de la soumission: {str(e)}'
            }, status=500)

    def soumettreKYCClient(self, request):
        """Soumet le KYC d'un client"""
        try:
            print("DEBUG: Début soumettreKYCClient")
            
            # Récupérer le profil client
            client_profile = ClientProfile.get_profile_for_user(request.user)
            print(f"DEBUG: Client profile trouvé: {client_profile}")
            
            if not client_profile:
                print("DEBUG: Aucun profil client trouvé")
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Profil client non trouvé'
                }, status=404)
            
            # Préparer les données KYC
            kyc_data = {
                'nom': request.POST.get('nom', '').strip(),
                'prenom': request.POST.get('prenom', '').strip(),
                'phone': request.POST.get('phone', '').strip(),
                'address': request.POST.get('address', '').strip(),
                'birth_date': request.POST.get('birth_date'),
                'nationality': request.POST.get('nationality', '').strip(),
            }
            print(f"DEBUG: Données KYC: {kyc_data}")
            
            # Gérer l'upload du document d'identité
            if 'document' in request.FILES:
                kyc_data['document'] = request.FILES['document']
                print("DEBUG: Document d'identité trouvé")
            
            # Mettre à jour le profil KYC via le modèle
            print("DEBUG: Avant update_kyc_data")
            updated_profile = client_profile.update_kyc_data(**kyc_data)
            print("DEBUG: Après update_kyc_data")
            
            response = JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'Profil KYC mis à jour avec succès !'
            })
            print(f"DEBUG: Réponse JSON créée: {response}")
            
            return response
                
        except Exception as e:
            print(f"DEBUG: Exception dans soumettreKYCClient: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'resultat': 'FAIL',
                'message': f'Erreur lors de la mise à jour: {str(e)}'
            }, status=500)

    def soumettreKYCMerchant(self, request):
        """Soumet le KYC d'un marchand"""
        try:
            # Récupérer le profil merchant
            merchant_profile = MerchantProfile.get_profile_for_user(request.user)
            
            # Préparer les données KYC
            kyc_data = {
                'company_name': request.POST.get('company_name', '').strip(),
                'contact_person': request.POST.get('contact_person', '').strip(),
                'contact_phone': request.POST.get('contact_phone', '').strip(),
                'contact_email': request.POST.get('contact_email', '').strip(),
                'company_address': request.POST.get('company_address', '').strip(),
                'company_city': request.POST.get('company_city', '').strip(),
                'company_country': request.POST.get('company_country', '').strip(),
                'company_postal_code': request.POST.get('company_postal_code', '').strip(),
                'business_type': request.POST.get('business_type', '').strip(),
                'company_registration': request.POST.get('company_registration', '').strip(),
                'tax_id': request.POST.get('tax_id', '').strip(),
            }
            
            # Gérer les uploads de documents
            for doc_field in ['business_license', 'company_registration_doc', 'tax_certificate']:
                if doc_field in request.FILES:
                    kyc_data[doc_field] = request.FILES[doc_field]
            
            # Mettre à jour le profil KYC via le modèle
            updated_profile = merchant_profile.update_kyc_data(**kyc_data)
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'Profil KYC mis à jour avec succès !'
            })
                
        except Exception as e:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': f'Erreur lors de la mise à jour: {str(e)}'
            }, status=500)

    def validerKYC(self, request):
        """Valide un KYC (pour les admins)"""
        if not request.user.is_authenticated or not AdminProfile.user_has_profile(request.user):
            return JsonResponse({
                'resultat': 'FAIL',
                'message': 'Accès non autorisé'
            }, status=403)
        
        try:
            profile_id = request.POST.get('profile_id')
            kyc_level = int(request.POST.get('kyc_level', 1))
            notes = request.POST.get('notes', '')
            
            # Essayer de trouver le profil
            try:
                profile = ClientProfile.objects.get(id=profile_id)
                profile_type = 'client'
            except ClientProfile.DoesNotExist:
                try:
                    profile = MerchantProfile.objects.get(id=profile_id)
                    profile_type = 'merchant'
                except MerchantProfile.DoesNotExist:
                    return JsonResponse({
                        'resultat': 'FAIL',
                        'message': 'Profil non trouvé'
                    }, status=404)
            
            # Valider le KYC
            KYCValidation.approve_validation(
                validation_id=profile_id,
                admin_user=request.user,
                notes=notes
            )
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': f'KYC niveau {kyc_level} validé avec succès !'
            })
            
        except Exception as e:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': f'Erreur lors de la validation: {str(e)}'
            }, status=500)

    def rejeterKYC(self, request):
        """Rejette un KYC (pour les admins)"""
        if not request.user.is_authenticated or not AdminProfile.user_has_profile(request.user):
            return JsonResponse({
                'resultat': 'FAIL',
                'message': 'Accès non autorisé'
            }, status=403)
        
        try:
            profile_id = request.POST.get('profile_id')
            notes = request.POST.get('notes', '')
            
            if not notes:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Raison du rejet requise'
                }, status=400)
            
            # Essayer de trouver le profil
            try:
                profile = ClientProfile.objects.get(id=profile_id)
                profile_type = 'client'
            except ClientProfile.DoesNotExist:
                try:
                    profile = MerchantProfile.objects.get(id=profile_id)
                    profile_type = 'merchant'
                except MerchantProfile.DoesNotExist:
                    return JsonResponse({
                        'resultat': 'FAIL',
                        'message': 'Profil non trouvé'
                    }, status=404)
            
            # Rejeter le KYC via le modèle
            profile.update_kyc_status(profile.KYC_REJECTED, request.user)
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'KYC rejeté avec succès'
            })
            
        except Exception as e:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': f'Erreur lors du rejet: {str(e)}'
            }, status=500)

    def approuverDocument(self, request):
        """Approuve un document (pour les admins)"""
        if not request.user.is_authenticated or not AdminProfile.user_has_profile(request.user):
            return JsonResponse({
                'resultat': 'FAIL',
                'message': 'Accès non autorisé'
            }, status=403)
        
        try:
            document_id = request.POST.get('document_id')
            # Logique d'approbation de document
            # À implémenter selon vos besoins
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'Document approuvé avec succès'
            })
            
        except Exception as e:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': f'Erreur lors de l\'approbation: {str(e)}'
            }, status=500)

    def rejeterDocument(self, request):
        """Rejette un document (pour les admins)"""
        if not request.user.is_authenticated or not AdminProfile.user_has_profile(request.user):
            return JsonResponse({
                'resultat': 'FAIL',
                'message': 'Accès non autorisé'
            }, status=403)
        
        try:
            document_id = request.POST.get('document_id')
            notes = request.POST.get('notes', '')
            
            if not notes:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Raison du rejet requise'
                }, status=400)
            
            # Logique de rejet de document
            # À implémenter selon vos besoins
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'Document rejeté avec succès'
            })
            
        except Exception as e:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': f'Erreur lors du rejet: {str(e)}'
            }, status=500)

    def mettreAJourProfil(self, request):
        """Met à jour les informations de base du profil"""
        try:
            profile_type = request.POST.get('profile_type')
            
            if profile_type == 'client':
                return self.mettreAJourProfilClient(request)
            elif profile_type == 'merchant':
                return self.mettreAJourProfilMerchant(request)
            else:
                return JsonResponse({
                    'resultat': 'FAIL',
                    'message': 'Type de profil invalide'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': f'Erreur lors de la mise à jour: {str(e)}'
            }, status=500)

    def mettreAJourProfilClient(self, request):
        """Met à jour le profil client"""
        try:
            client_profile = ClientProfile.get_profile_for_user(request.user)
            
            # Préparer les données de mise à jour
            profile_data = {
                'nom': request.POST.get('nom', '').strip(),
                'prenom': request.POST.get('prenom', '').strip(),
                'phone': request.POST.get('phone', '').strip(),
                'address': request.POST.get('address', '').strip(),
                'preferred_language': int(request.POST.get('preferred_language', 0))
            }
            
            # Mettre à jour le profil via le modèle
            updated_profile = client_profile.complete_profile_data(**profile_data)
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'Profil mis à jour avec succès !'
            })
                
        except Exception as e:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': f'Erreur lors de la mise à jour: {str(e)}'
            }, status=500)

    def mettreAJourProfilMerchant(self, request):
        """Met à jour le profil merchant"""
        try:
            merchant_profile = MerchantProfile.get_profile_for_user(request.user)
            
            # Préparer les données de mise à jour
            profile_data = {
                'company_name': request.POST.get('company_name', '').strip(),
                'contact_person': request.POST.get('contact_person', '').strip(),
                'contact_phone': request.POST.get('contact_phone', '').strip(),
                'company_address': request.POST.get('company_address', '').strip(),
                'company_city': request.POST.get('company_city', '').strip(),
                'company_country': request.POST.get('company_country', '').strip(),
                'company_postal_code': request.POST.get('company_postal_code', '').strip()
            }
            
            # Mettre à jour le profil via le modèle
            updated_profile = merchant_profile.complete_company_data(**profile_data)
            
            return JsonResponse({
                'resultat': 'SUCCESS',
                'message': 'Profil mis à jour avec succès !'
            })
                
        except Exception as e:
            return JsonResponse({
                'resultat': 'FAIL',
                'message': f'Erreur lors de la mise à jour: {str(e)}'
            }, status=500)
