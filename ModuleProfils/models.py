from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from re import compile


import uuid
import os

# ========== FONCTIONS POUR CHEMINS D'UPLOAD DYNAMIQUES ==========

def client_document_path(instance, filename):
    """
    Chemin pour les documents des clients avec UUIDs
    
    Exemples de chemins générés :
    - kyc/clients/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf
    - kyc/clients/9876fedc-ba98-7654-3210-fedcba987654.jpg
    """
    # Récupérer l'extension du fichier
    ext = os.path.splitext(filename)[1]
    # Générer un UUID unique
    unique_id = str(uuid.uuid4())
    # Retourner le chemin complet avec UUID
    return f'kyc/clients/{unique_id}{ext}'

def merchant_document_path(instance, filename):
    """
    Chemin pour les documents des marchands avec UUIDs
    
    Exemples de chemins générés :
    - kyc/merchants/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf
    - kyc/merchants/9876fedc-ba98-7654-3210-fedcba987654.jpg
    """
    # Récupérer l'extension du fichier
    ext = os.path.splitext(filename)[1]
    # Générer un UUID unique
    unique_id = str(uuid.uuid4())
    # Retourner le chemin complet avec UUID
    return f'kyc/merchants/{unique_id}{ext}'


# ========== CLASSE UTILITAIRE POUR GESTION DES UPLOADS ==========

class FileUploadManager:
    """Gestionnaire d'upload de fichiers avec gestion automatique des mises à jour"""
    
    @staticmethod
    def update_file_field(instance, field_name, new_file, old_file=None):
        """
        Met à jour un champ de fichier avec gestion automatique des anciens fichiers
        
        Args:
            instance: Instance du modèle
            field_name: Nom du champ de fichier
            new_file: Nouveau fichier uploadé
            old_file: Ancien fichier (optionnel)
        """
        if new_file:
            # Supprimer l'ancien fichier s'il existe
            if old_file and hasattr(old_file, 'storage') and hasattr(old_file, 'name'):
                try:
                    old_file.storage.delete(old_file.name)
                except Exception as e:
                    print(f"Erreur lors de la suppression de l'ancien fichier: {e}")
            
            # Assigner le nouveau fichier
            setattr(instance, field_name, new_file)
            return True
        return False
    
    @staticmethod
    def update_multiple_files(instance, file_data):
        """
        Met à jour plusieurs champs de fichiers en une fois
        
        Args:
            instance: Instance du modèle
            file_data: Dict avec {field_name: new_file}
        """
        updated_fields = []
        for field_name, new_file in file_data.items():
            if new_file and hasattr(instance, field_name):
                old_file = getattr(instance, field_name, None)
                if FileUploadManager.update_file_field(instance, field_name, new_file, old_file):
                    updated_fields.append(field_name)
        return updated_fields
    
    @staticmethod
    def delete_file_field(instance, field_name):
        """Supprime un fichier et vide le champ"""
        current_file = getattr(instance, field_name)
        if current_file and hasattr(current_file, 'storage') and hasattr(current_file, 'name'):
            try:
                current_file.storage.delete(current_file.name)
                setattr(instance, field_name, None)
                return True
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier: {e}")
        return False
    
    @staticmethod
    def get_file_info(instance, field_name):
        """Retourne les informations d'un fichier"""
        file_obj = getattr(instance, field_name)
        if file_obj:
            return {
                'name': file_obj.name,
                'url': file_obj.url,
                'size': file_obj.size,
                'exists': True
            }
        return {'exists': False}
    
    @staticmethod
    def get_all_files_info(instance, file_fields):
        """Retourne les informations de tous les champs de fichiers"""
        files_info = {}
        for field_name in file_fields:
            files_info[field_name] = FileUploadManager.get_file_info(instance, field_name)
        return files_info


# ========== CONSTANTES ==========

# Types de profil
PROFILE_TYPE_CLIENT = 'client'
PROFILE_TYPE_MERCHANT = 'merchant'
PROFILE_TYPE_ADMIN = 'admin'

# Classes de profil
PROFILE_CLASS_CLIENT = 'ClientProfile'
PROFILE_CLASS_MERCHANT = 'MerchantProfile'
PROFILE_CLASS_ADMIN = 'AdminProfile'

# ========== EXEMPLES D'UTILISATION ==========
"""
Exemples d'utilisation avec les méthodes statiques :

# Approche recommandée : UserProfileManager (plus simple et cohérent)
user_type = UserProfileManager.determine_user_type(user)
primary_profile = UserProfileManager.get_primary_profile(user)
display_name = UserProfileManager.get_user_display_name(user)
capabilities = UserProfileManager.get_user_capabilities(user)

# Vérifier les fonctionnalités KYC
if UserProfileManager.user_has_kyc_features(user):
    kyc_status = UserProfileManager.get_user_kyc_status(user)
    is_approved = UserProfileManager.is_user_kyc_approved(user)

# Alternative : ProfileUtils (classe utilitaire générale)
user_type = ProfileUtils.get_user_type(user)  # 'client', 'merchant', ou 'admin'
display_name = ProfileUtils.get_display_name(user)
kyc_status = ProfileUtils.get_kyc_status(user)
is_approved = ProfileUtils.is_kyc_approved(user)

# Approche spécifique par modèle (pour des cas particuliers)
# Pour les clients
if ClientProfile.user_has_profile(user):
    client_profile = ClientProfile.get_profile_for_user(user)
    client_name = ClientProfile.get_user_display_name(user)
    client_kyc = ClientProfile.get_user_kyc_status(user)
    is_client_approved = ClientProfile.is_user_kyc_approved(user)

# Pour les marchands
if MerchantProfile.user_has_profile(user):
    merchant_profile = MerchantProfile.get_profile_for_user(user)
    merchant_name = MerchantProfile.get_user_display_name(user)
    merchant_kyc = MerchantProfile.get_user_kyc_status(user)
    is_merchant_approved = MerchantProfile.is_user_kyc_approved(user)

# Pour les admins
if AdminProfile.user_has_profile(user):
    admin_profile = AdminProfile.get_profile_for_user(user)
    admin_name = AdminProfile.get_user_display_name(user)
    can_validate = AdminProfile.user_can_validate_kyc(user)

# Gestion des validations KYC (sans __class__.__name__)
# Création d'une validation
validation = KYCValidation.create_validation(profile, kyc_level, admin_user)

# Récupération du profil depuis une validation
profile = validation.get_profile_instance()

# Utilisation des méthodes statiques utilitaires de KYCValidation
profile_type = KYCValidation.determine_profile_type(profile_instance)
profile = KYCValidation.get_profile_by_type_and_id(profile_type, profile_id)
"""

# ========== UTILITAIRES DE PROFIL ==========

class ProfileUtils:
    """Utilitaires statiques pour la gestion des profils utilisateur"""
    
    @staticmethod
    def get_client_profile(user):
        """Retourne le profil client s'il existe"""
        try:
            return user.clientprofile_profile
        except:
            return None
        
    @staticmethod
    def get_merchant_profile(user):
        """Retourne le profil marchand s'il existe"""
        try:
            return user.merchantprofile_profile
        except:
            return None
    
    @staticmethod
    def get_admin_profile(user):
        """Retourne le profil admin s'il existe"""
        try:
            return user.adminprofile_profile
        except:
            return None

    @staticmethod
    def get_user_profile(user):
        """Retourne le profil principal de l'utilisateur"""
        # Essayer client en premier
        client_profile = ProfileUtils.get_client_profile(user)
        if client_profile:
            return client_profile
        
        # Ensuite marchand
        merchant_profile = ProfileUtils.get_merchant_profile(user)
        if merchant_profile:
            return merchant_profile
        
        # Enfin admin
        admin_profile = ProfileUtils.get_admin_profile(user)
        if admin_profile:
            return admin_profile
        
        return None
    
    @staticmethod
    def get_user_type(user):
        """Retourne le type d'utilisateur"""
        if ProfileUtils.get_client_profile(user):
            return PROFILE_TYPE_CLIENT
        elif ProfileUtils.get_merchant_profile(user):
            return PROFILE_TYPE_MERCHANT
        elif ProfileUtils.get_admin_profile(user):
            return PROFILE_TYPE_ADMIN
        return None

    @staticmethod
    def get_display_name(user):
        """Retourne le nom d'affichage de l'utilisateur"""
        client_profile = ProfileUtils.get_client_profile(user)
        if client_profile:
            return client_profile.get_display_name()
        
        merchant_profile = ProfileUtils.get_merchant_profile(user)
        if merchant_profile:
            return merchant_profile.get_display_name()
        
        admin_profile = ProfileUtils.get_admin_profile(user)
        if admin_profile:
            return admin_profile.get_display_name()
        
        # Fallback
        full_name = f"{user.first_name} {user.last_name}".strip()
        return full_name or user.username
    
    @staticmethod
    def get_kyc_status(user):
        """Retourne le statut KYC de l'utilisateur"""
        client_profile = ProfileUtils.get_client_profile(user)
        if client_profile:
            return client_profile.kyc_status
        
        merchant_profile = ProfileUtils.get_merchant_profile(user)
        if merchant_profile:
            return merchant_profile.kyc_status
        
        return None
    
    @staticmethod
    def is_kyc_approved(user):
        """Vérifie si le KYC de l'utilisateur est approuvé"""
        client_profile = ProfileUtils.get_client_profile(user)
        if client_profile:
            return client_profile.is_kyc_approved()
        
        merchant_profile = ProfileUtils.get_merchant_profile(user)
        if merchant_profile:
            return merchant_profile.is_kyc_approved()
        
        return False

    @staticmethod
    def can_access_kyc_features(user):
        """Vérifie si l'utilisateur peut accéder aux fonctionnalités KYC"""
        return (ProfileUtils.get_client_profile(user) is not None or 
                ProfileUtils.get_merchant_profile(user) is not None)
    
    @staticmethod
    def get_kyc_capabilities(user):
        """Retourne les capacités KYC de l'utilisateur"""
        client_profile = ProfileUtils.get_client_profile(user)
        if client_profile:
            return {
                'can_submit_documents': True,
                'can_view_status': True,
                'can_upgrade': client_profile.is_kyc_approved(),
                'max_level': 2,
                'profile_type': PROFILE_TYPE_CLIENT
            }
        
        merchant_profile = ProfileUtils.get_merchant_profile(user)
        if merchant_profile:
            return {
                'can_submit_documents': True,
                'can_view_status': True,
                'can_upgrade': merchant_profile.is_kyc_approved(),
                'max_level': 2,
                'profile_type': PROFILE_TYPE_MERCHANT
            }
        
        admin_profile = ProfileUtils.get_admin_profile(user)
        if admin_profile:
            return {
                'can_validate': admin_profile.can_validate_kyc,
                'can_view_all': True,
                'can_manage': True,
                'profile_type': PROFILE_TYPE_ADMIN
            }
        
        return {}


class UserProfileManager:
    """Gestionnaire pour les opérations sur les profils utilisateur"""
    
    @staticmethod
    def determine_user_type(user):
        """Détermine le type de profil principal de l'utilisateur"""
        if ClientProfile.user_has_profile(user):
            return PROFILE_TYPE_CLIENT
        elif MerchantProfile.user_has_profile(user):
            return PROFILE_TYPE_MERCHANT
        elif AdminProfile.user_has_profile(user):
            return PROFILE_TYPE_ADMIN
        return None
    
    @staticmethod
    def get_primary_profile(user):
        """Retourne le profil principal de l'utilisateur"""
        user_type = UserProfileManager.determine_user_type(user)
        if user_type == PROFILE_TYPE_CLIENT:
            return ClientProfile.get_profile_for_user(user)
        elif user_type == PROFILE_TYPE_MERCHANT:
            return MerchantProfile.get_profile_for_user(user)
        elif user_type == PROFILE_TYPE_ADMIN:
            return AdminProfile.get_profile_for_user(user)
        return None
    
    @staticmethod
    def get_user_display_name(user):
        """Retourne le nom d'affichage principal de l'utilisateur"""
        user_type = UserProfileManager.determine_user_type(user)
        if user_type == PROFILE_TYPE_CLIENT:
            return ClientProfile.get_user_display_name(user)
        elif user_type == PROFILE_TYPE_MERCHANT:
            return MerchantProfile.get_user_display_name(user)
        elif user_type == PROFILE_TYPE_ADMIN:
            return AdminProfile.get_user_display_name(user)
        
        # Fallback
        full_name = f"{user.first_name} {user.last_name}".strip()
        return full_name or user.username
    
    @staticmethod
    def user_has_kyc_features(user):
        """Vérifie si l'utilisateur peut accéder aux fonctionnalités KYC"""
        return (ClientProfile.user_has_profile(user) or 
                MerchantProfile.user_has_profile(user))
    
    @staticmethod
    def get_user_kyc_status(user):
        """Retourne le statut KYC de l'utilisateur"""
        if ClientProfile.user_has_profile(user):
            return ClientProfile.get_user_kyc_status(user)
        elif MerchantProfile.user_has_profile(user):
            return MerchantProfile.get_user_kyc_status(user)
        return None
    
    @staticmethod
    def user_exists_by_username(username):
        """Vérifie si un utilisateur existe par nom d'utilisateur"""
        from django.contrib.auth.models import User
        return User.objects.filter(username=username).exists()
    
    @staticmethod
    def user_exists_by_email(email):
        """Vérifie si un utilisateur existe par email"""
        from django.contrib.auth.models import User
        return User.objects.filter(email=email).exists()
    
    @staticmethod
    def get_user_by_username(username):
        """Retourne un utilisateur par nom d'utilisateur"""
        from django.contrib.auth.models import User
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @staticmethod
    def is_user_kyc_approved(user):
        """Vérifie si le KYC de l'utilisateur est approuvé"""
        if ClientProfile.user_has_profile(user):
            return ClientProfile.is_user_kyc_approved(user)
        elif MerchantProfile.user_has_profile(user):
            return MerchantProfile.is_user_kyc_approved(user)
        return False

    @staticmethod
    def get_user_capabilities(user):
        """Retourne les capacités complètes de l'utilisateur"""
        capabilities = {
            'user_type': UserProfileManager.determine_user_type(user),
            'has_profile': UserProfileManager.get_primary_profile(user) is not None,
            'display_name': UserProfileManager.get_user_display_name(user),
            'kyc_features': UserProfileManager.user_has_kyc_features(user),
            'kyc_status': UserProfileManager.get_user_kyc_status(user),
            'kyc_approved': UserProfileManager.is_user_kyc_approved(user)
        }
        
        # Ajouter les capacités spécifiques au profil
        if AdminProfile.user_has_profile(user):
            capabilities['can_validate_kyc'] = AdminProfile.user_can_validate_kyc(user)
        
        return capabilities


# ========== MODÈLES PRINCIPAUX ==========


class ClientProfile(models.Model):
    # Constantes pour les choix
    KYC_PENDING = 0
    KYC1_APPROVED = 1
    KYC2_APPROVED = 2
    KYC_REJECTED = 3
    
    KYC_STATUS_CHOICES = [
        (KYC_PENDING, 'En attente'),
        (KYC1_APPROVED, 'KYC1 Approuvé'),
        (KYC2_APPROVED, 'KYC2 Approuvé'),
        (KYC_REJECTED, 'Rejeté'),
    ]
    
    LANG_FR = 0
    LANG_EN = 1
    LANG_AR = 2
    
    LANGUAGE_CHOICES = [
        (LANG_FR, 'Français'),
        (LANG_EN, 'English'),
        (LANG_AR, 'العربية'),
    ]
    
    # Champs du modèle
    # UUID pour identification externe
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='clientprofile_profile')
    nom = models.CharField(max_length=255, verbose_name="Nom", null=True, blank=True)
    prenom = models.CharField(max_length=255, verbose_name="Prénom", null=True, blank=True)
    phone = models.CharField(max_length=20, verbose_name="Téléphone", null=True, blank=True)
    address = models.TextField(verbose_name="Adresse", null=True, blank=True)
    birth_date = models.DateField(verbose_name="Date de naissance", null=True, blank=True)
    nationality = models.CharField(max_length=100, verbose_name="Nationalité", null=True, blank=True)
    kyc_status = models.IntegerField(verbose_name="Statut KYC", choices=KYC_STATUS_CHOICES, default=KYC_PENDING)
    document = models.FileField(upload_to=client_document_path, validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])], verbose_name="Document d'identité", null=True, blank=True)
    preferred_language = models.IntegerField(verbose_name="Langue préférée", choices=LANGUAGE_CHOICES, default=LANG_FR)
    is_active = models.BooleanField(verbose_name="Actif?", default=True)
    create = models.DateTimeField(verbose_name="Date de création", auto_now_add=True)
    last_update = models.DateTimeField(verbose_name="Dernière mise à jour", auto_now=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="clientprofile_createby", verbose_name="Créé par")
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="clientprofile_updateby", verbose_name="Mis à jour par")
    
    class Meta:
        verbose_name = "Profil Client"
        verbose_name_plural = "Profils Clients"
        ordering = ['-create']
    
    def __str__(self):
        return f"Client: {self.user.username} - {self.nom} {self.prenom}"
    
    # Méthodes d'instance
    def get_full_name(self):
        """Retourne le nom complet du client"""
        if self.nom and self.prenom:
            return f"{self.prenom} {self.nom}"
        return self.user.username
    
    def get_display_name(self):
        """Méthode commune pour obtenir le nom d'affichage"""
        return self.get_full_name()
    
    def get_profile_type(self):
        """Méthode commune pour obtenir le type de profil"""
        return PROFILE_TYPE_CLIENT
    
    def is_kyc_pending(self):
        """Vérifie si le KYC est en attente"""
        return self.kyc_status == self.KYC_PENDING
    
    def is_kyc_approved(self):
        """Vérifie si le KYC est approuvé (niveau 1 ou 2)"""
        return self.kyc_status in [self.KYC1_APPROVED, self.KYC2_APPROVED]
    
    def is_kyc_rejected(self):
        """Vérifie si le KYC est rejeté"""
        return self.kyc_status == self.KYC_REJECTED
    
    def can_upgrade_kyc(self):
        """Peut passer au niveau KYC suivant"""
        return self.kyc_status == self.KYC_PENDING and self.document
    
    def get_kyc_completion_percentage(self):
        """Retourne le pourcentage de completion du profil KYC"""
        required_fields = ['nom', 'prenom', 'phone', 'address', 'birth_date', 'nationality', 'document']
        completed_fields = sum(1 for field in required_fields if getattr(self, field))
        return int((completed_fields / len(required_fields)) * 100)
    
    def get_missing_kyc_fields(self):
        """Retourne la liste des champs KYC manquants"""
        required_fields = {
            'nom': 'Nom',
            'prenom': 'Prénom', 
            'phone': 'Téléphone',
            'address': 'Adresse',
            'birth_date': 'Date de naissance',
            'nationality': 'Nationalité',
            'document': 'Document d\'identité'
        }
        return [label for field, label in required_fields.items() if not getattr(self, field)]
    
    # Méthodes de classe
    @classmethod
    def get_pending_kyc_count(cls):
        """Retourne le nombre de clients en attente de validation KYC"""
        return cls.objects.filter(kyc_status=cls.KYC_PENDING).count()
    
    @classmethod
    def get_approved_clients(cls):
        """Retourne tous les clients avec KYC approuvé"""
        return cls.objects.filter(kyc_status__in=[cls.KYC1_APPROVED, cls.KYC2_APPROVED])
    
    @classmethod
    def get_clients_by_language(cls, language):
        """Retourne les clients par langue préférée"""
        return cls.objects.filter(preferred_language=language)
    
    # Méthodes statiques
    @staticmethod
    def get_available_languages():
        """Retourne la liste des langues disponibles"""
        return [{'code': choice[0], 'name': choice[1]} for choice in ClientProfile.LANGUAGE_CHOICES]
    
    @staticmethod
    def get_kyc_status_display_dict():
        """Retourne un dictionnaire des statuts KYC"""
        return dict(ClientProfile.KYC_STATUS_CHOICES)
    
    @staticmethod
    def get_profile_for_user(user):
        """Retourne le profil client pour un utilisateur donné"""
        try:
            return user.clientprofile_profile
        except:
            return None
    
    @staticmethod
    def user_has_profile(user):
        """Vérifie si l'utilisateur a un profil client"""
        try:
            return bool(user.clientprofile_profile)
        except:
            return False
    
    @staticmethod
    def get_user_display_name(user):
        """Retourne le nom d'affichage pour un utilisateur client"""
        profile = ClientProfile.get_profile_for_user(user)
        if profile:
            return profile.get_display_name()
        return None
    
    @staticmethod
    def get_user_kyc_status(user):
        """Retourne le statut KYC pour un utilisateur client"""
        profile = ClientProfile.get_profile_for_user(user)
        if profile:
            return profile.kyc_status
        return None
    
    @staticmethod
    def is_user_kyc_approved(user):
        """Vérifie si le KYC est approuvé pour un utilisateur client"""
        profile = ClientProfile.get_profile_for_user(user)
        if profile:
            return profile.is_kyc_approved()
        return False
    
    @classmethod
    def get_valid_fields(cls):
        """Retourne la liste des champs valides pour la mise à jour"""
        return ['nom', 'prenom', 'phone', 'address', 'birth_date', 'nationality', 'preferred_language']
    
    @classmethod
    def get_client_by_id(cls, client_id):
        """Retourne un profil client par son ID"""
        try:
            return cls.objects.get(id=client_id)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_pending_kyc_clients(cls):
        """Retourne tous les clients en attente de validation KYC"""
        return cls.objects.filter(kyc_status=cls.KYC_PENDING)
    
    def is_valid_field(self, field_name):
        """Vérifie si un nom de champ est valide pour ce modèle"""
        return field_name in self.__class__.get_valid_fields()
    
    def clean(self):
        """Validation personnalisée"""
        super().clean()
        
        # VÉRIFICATION D'UNICITÉ : Un utilisateur ne peut pas être à la fois client et merchant
        if self.user:
            if MerchantProfile.user_has_profile(self.user):
                raise ValidationError("Un utilisateur ne peut pas être à la fois client et marchand. Supprimez d'abord le profil marchand.")
        
        # Validation des champs obligatoires pour KYC
        if self.kyc_status != self.KYC_PENDING:
            required_fields = ['nom', 'prenom', 'phone', 'address', 'birth_date', 'nationality', 'document']
            missing_fields = [field for field in required_fields if not getattr(self, field)]
            if missing_fields:
                raise ValidationError(f"Les champs suivants sont obligatoires pour valider le KYC : {', '.join(missing_fields)}")
        
        # Validation de la date de naissance
        if self.birth_date:
            today = timezone.now().date()
            age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
            if age < 18:
                raise ValidationError("L'utilisateur doit avoir au moins 18 ans")
            if age > 120:
                raise ValidationError("L'âge semble incorrect")
        
        # Validation du numéro de téléphone
        if self.phone:
            phone_pattern = compile(r'^\+?[1-9]\d{1,14}$')
            if not phone_pattern.match(self.phone):
                raise ValidationError("Le format du numéro de téléphone est incorrect")
    
    # Méthodes de création et mise à jour
    @classmethod
    def create_profile(cls, user, **extra_fields):
        """Crée un profil client avec les données de base"""
        # VÉRIFICATION D'UNICITÉ : Un utilisateur ne peut pas être à la fois client et merchant
        if MerchantProfile.user_has_profile(user):
            raise ValidationError("Un utilisateur ne peut pas être à la fois client et marchand. Supprimez d'abord le profil marchand.")
        
        return cls.objects.create(
            user=user,
            kyc_status=cls.KYC_PENDING,
            preferred_language=cls.LANG_FR,
            is_active=True,
            **extra_fields
        )
    
    @classmethod
    def create_from_user_data(cls, user, first_name=None, last_name=None, phone=None, **kwargs):
        """Crée un profil client à partir des données utilisateur"""
        return cls.create_profile(
            user=user,
            nom=last_name or user.last_name,
            prenom=first_name or user.first_name,
            phone=phone,
            **kwargs
        )
    
    def update_kyc_status(self, new_status, admin_user=None):
        """Met à jour le statut KYC"""
        old_status = self.kyc_status
        self.kyc_status = new_status
        if admin_user:
            self.update_by = admin_user
        self.save()
        
        # Créer une validation KYC si changement
        if old_status != new_status and new_status in [self.KYC1_APPROVED, self.KYC2_APPROVED]:
            kyc_level = KYCValidation.KYC_LEVEL_1 if new_status == self.KYC1_APPROVED else KYCValidation.KYC_LEVEL_2
            KYCValidation.create_validation(self, kyc_level, admin_user)
    
    def complete_profile_data(self, **profile_data):
        """Complète les données du profil"""
        for field, value in profile_data.items():
            if self.is_valid_field(field) and value:
                setattr(self, field, value)
        self.save()
        return self
    
    def update_kyc_data(self, **kyc_data):
        """Met à jour les données KYC et gère la validation automatique"""
        # Mettre à jour les champs de base
        for field, value in kyc_data.items():
            if self.is_valid_field(field) and value is not None:
                setattr(self, field, value)
        
        # Gérer les documents avec le gestionnaire d'upload
        file_fields = {k: v for k, v in kyc_data.items() if k in ['document'] and v}
        if file_fields:
            FileUploadManager.update_multiple_files(self, file_fields)
        
        # Sauvegarder les changements
        self.save()
        
        # Validation automatique du statut KYC
        self.update_kyc_status_automatically()
        return self
    
    def update_kyc_status_automatically(self):
        """Met à jour le statut KYC selon les règles métier"""
        if self.can_upgrade_kyc():
            self.kyc_status = self.KYC1_APPROVED
        self.save()
    
    @classmethod
    def create_user_with_profile(cls, username, email, password, **profile_data):
        """Crée un utilisateur avec son profil client en une seule opération"""
        with transaction.atomic():
            # VÉRIFICATION D'UNICITÉ : S'assurer qu'aucun profil merchant n'existe déjà
            # Cette vérification est redondante car l'utilisateur est nouveau, mais c'est une sécurité
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            profile = cls.create_profile(user, **profile_data)
            return user, profile


class MerchantProfile(models.Model):
    # Constantes pour les choix
    KYC_PENDING = 0
    KYC1_APPROVED = 1
    KYC2_APPROVED = 2
    KYC_REJECTED = 3
    
    KYC_STATUS_CHOICES = [
        (KYC_PENDING, 'En attente'),
        (KYC1_APPROVED, 'KYC1 Approuvé'),
        (KYC2_APPROVED, 'KYC2 Approuvé'),
        (KYC_REJECTED, 'Rejeté'),
    ]
    
    BUSINESS_TRAVEL_AGENCY = 0
    BUSINESS_HOTEL = 1
    BUSINESS_AIRLINE = 2
    BUSINESS_CAR_RENTAL = 3
    BUSINESS_TOUR_OPERATOR = 4
    BUSINESS_OTHER = 5
    
    BUSINESS_TYPE_CHOICES = [
        (BUSINESS_TRAVEL_AGENCY, 'Agence de voyage'),
        (BUSINESS_HOTEL, 'Hôtel'),
        (BUSINESS_AIRLINE, 'Compagnie aérienne'),
        (BUSINESS_CAR_RENTAL, 'Location de voiture'),
        (BUSINESS_TOUR_OPERATOR, 'Tour opérateur'),
        (BUSINESS_OTHER, 'Autre'),
    ]
    
    # Champs du modèle
    # UUID pour identification externe
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='merchantprofile_profile')
    company_name = models.CharField(max_length=255, verbose_name="Nom de l'entreprise")
    company_registration = models.CharField(max_length=100, verbose_name="Numéro d'enregistrement", null=True, blank=True)
    tax_id = models.CharField(max_length=100, verbose_name="Numéro de TVA", null=True, blank=True)
    contact_person = models.CharField(max_length=255, verbose_name="Personne de contact")
    contact_phone = models.CharField(max_length=20, verbose_name="Téléphone de contact")
    contact_email = models.EmailField(verbose_name="Email de contact")
    company_address = models.TextField(verbose_name="Adresse de l'entreprise")
    company_city = models.CharField(max_length=100, verbose_name="Ville")
    company_country = models.CharField(max_length=100, verbose_name="Pays")
    company_postal_code = models.CharField(max_length=20, verbose_name="Code postal")
    kyc_status = models.IntegerField(verbose_name="Statut KYC", choices=KYC_STATUS_CHOICES, default=KYC_PENDING)
    business_license = models.FileField(upload_to=merchant_document_path, validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])], verbose_name="Licence commerciale", null=True, blank=True)
    tax_certificate = models.FileField(upload_to=merchant_document_path, validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])], verbose_name="Certificat fiscal", null=True, blank=True)
    company_registration_doc = models.FileField(upload_to=merchant_document_path, validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])], verbose_name="Document d'enregistrement", null=True, blank=True)
    business_type = models.IntegerField(verbose_name="Type d'entreprise", choices=BUSINESS_TYPE_CHOICES, default=BUSINESS_TRAVEL_AGENCY)
    is_verified = models.BooleanField(default=False, verbose_name="Vérifié")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Taux de commission (%)")
    is_active = models.BooleanField(verbose_name="Actif?", default=True)
    create = models.DateTimeField(verbose_name="Date de création", auto_now_add=True)
    last_update = models.DateTimeField(verbose_name="Dernière mise à jour", auto_now=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="merchantprofile_createby", verbose_name="Créé par")
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="merchantprofile_updateby", verbose_name="Mis à jour par")
    
    class Meta:
        verbose_name = "Profil Marchand"
        verbose_name_plural = "Profils Marchands"
        ordering = ['-create']
    
    def __str__(self):
        return f"Marchand: {self.company_name} - {self.user.username}"
    
    # Méthodes d'instance
    def get_company_display_name(self):
        """Retourne le nom d'affichage de l'entreprise"""
        return self.company_name or f"Entreprise de {self.user.username}"
    
    def get_display_name(self):
        """Méthode commune pour obtenir le nom d'affichage"""
        return self.get_company_display_name()
    
    def get_profile_type(self):
        """Méthode commune pour obtenir le type de profil"""
        return PROFILE_TYPE_MERCHANT
    
    def is_kyc_pending(self):
        """Vérifie si le KYC est en attente"""
        return self.kyc_status == self.KYC_PENDING
    
    def is_kyc1_approved(self):
        """Vérifie si le KYC niveau 1 est approuvé"""
        return self.kyc_status == self.KYC1_APPROVED
    
    def is_kyc2_approved(self):
        """Vérifie si le KYC niveau 2 est approuvé"""
        return self.kyc_status == self.KYC2_APPROVED
    
    def is_fully_verified(self):
        """Vérifie si le marchand est complètement vérifié (KYC2 + verified)"""
        return self.kyc_status == self.KYC2_APPROVED and self.is_verified
    
    def can_upgrade_to_kyc1(self):
        """Peut passer au KYC niveau 1"""
        return (self.kyc_status == self.KYC_PENDING and 
                self.business_license and 
                self.company_registration_doc)
    
    def can_upgrade_to_kyc2(self):
        """Peut passer au KYC niveau 2"""
        return (self.kyc_status == self.KYC1_APPROVED and 
                self.tax_certificate and 
                self.get_kyc_completion_percentage() >= 90)
    
    def get_kyc_completion_percentage(self):
        """Retourne le pourcentage de completion du profil KYC"""
        required_fields = [
            'company_name', 'contact_person', 'contact_phone', 'contact_email',
            'company_address', 'company_city', 'company_country', 'company_postal_code',
            'business_license', 'tax_certificate', 'company_registration_doc'
        ]
        completed_fields = sum(1 for field in required_fields if getattr(self, field))
        return int((completed_fields / len(required_fields)) * 100)
    
    def get_missing_kyc_fields(self):
        """Retourne la liste des champs KYC manquants"""
        required_fields = {
            'company_name': 'Nom de l\'entreprise',
            'contact_person': 'Personne de contact',
            'contact_phone': 'Téléphone de contact',
            'company_address': 'Adresse de l\'entreprise',
            'company_city': 'Ville',
            'company_country': 'Pays',
            'business_license': 'Licence commerciale',
            'tax_certificate': 'Certificat fiscal',
            'company_registration_doc': 'Document d\'enregistrement'
        }
        return [label for field, label in required_fields.items() if not getattr(self, field)]
    
    def get_commission_amount(self, base_amount):
        """Calcule le montant de commission pour un montant donné"""
        return (base_amount * self.commission_rate) / 100
    
    def get_business_type_display_name(self):
        """Retourne le nom d'affichage du type d'entreprise"""
        return dict(self.BUSINESS_TYPE_CHOICES).get(self.business_type, 'Non défini')
    
    # Méthodes de classe
    @classmethod
    def get_pending_kyc_count(cls):
        """Retourne le nombre de marchands en attente de validation KYC"""
        return cls.objects.filter(kyc_status=cls.KYC_PENDING).count()
    
    @classmethod
    def get_verified_merchants(cls):
        """Retourne tous les marchands vérifiés"""
        return cls.objects.filter(kyc_status=cls.KYC2_APPROVED, is_verified=True)
    
    @classmethod
    def get_merchants_by_business_type(cls, business_type):
        """Retourne les marchands par type d'entreprise"""
        return cls.objects.filter(business_type=business_type)
    
    @classmethod
    def get_active_merchants(cls):
        """Retourne tous les marchands actifs et vérifiés"""
        return cls.objects.filter(is_active=True, is_verified=True)
    
    @classmethod
    def get_average_commission_rate(cls):
        """Retourne le taux de commission moyen"""
        result = cls.objects.aggregate(avg_rate=Avg('commission_rate'))
        return result['avg_rate'] or 0
    
    # Méthodes statiques
    @staticmethod
    def get_available_business_types():
        """Retourne la liste des types d'entreprise disponibles"""
        return [{'code': choice[0], 'name': choice[1]} for choice in MerchantProfile.BUSINESS_TYPE_CHOICES]
    
    @staticmethod
    def get_kyc_requirements_by_level():
        """Retourne les exigences KYC par niveau"""
        return {
            'KYC1': ['business_license', 'company_registration_doc'],
            'KYC2': ['tax_certificate', 'complete_profile']
        }
    
    @staticmethod
    def get_profile_for_user(user):
        """Retourne le profil marchand pour un utilisateur donné"""
        try:
            return user.merchantprofile_profile
        except:
            return None
    
    @staticmethod
    def user_has_profile(user):
        """Vérifie si l'utilisateur a un profil marchand"""
        try:
            return bool(user.merchantprofile_profile)
        except:
            return False
    
    @staticmethod
    def get_user_display_name(user):
        """Retourne le nom d'affichage pour un utilisateur marchand"""
        profile = MerchantProfile.get_profile_for_user(user)
        if profile:
            return profile.get_display_name()
        return None
    
    @staticmethod
    def get_user_kyc_status(user):
        """Retourne le statut KYC pour un utilisateur marchand"""
        profile = MerchantProfile.get_profile_for_user(user)
        if profile:
            return profile.kyc_status
        return None
    
    @staticmethod
    def is_user_kyc_approved(user):
        """Vérifie si le KYC est approuvé pour un utilisateur marchand"""
        profile = MerchantProfile.get_profile_for_user(user)
        if profile:
            return profile.is_kyc_approved()
        return False
    
    @classmethod
    def get_valid_fields(cls):
        """Retourne la liste des champs valides pour la mise à jour"""
        return ['company_name', 'contact_person', 'contact_phone', 'contact_email', 'company_address', 
                'company_city', 'company_country', 'company_postal_code', 'business_type', 'company_registration', 'tax_id']
    
    @classmethod
    def get_merchant_by_id(cls, merchant_id):
        """Retourne un profil marchand par son ID"""
        try:
            return cls.objects.get(id=merchant_id)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_pending_kyc_merchants(cls):
        """Retourne tous les marchands en attente de validation KYC"""
        return cls.objects.filter(kyc_status=cls.KYC_PENDING)
    
    def is_valid_field(self, field_name):
        """Vérifie si un nom de champ est valide pour ce modèle"""
        return field_name in self.__class__.get_valid_fields()
    
    def clean(self):
        """Validation personnalisée"""
        super().clean()
        
        # VÉRIFICATION D'UNICITÉ : Un utilisateur ne peut pas être à la fois merchant et client
        if self.user:
            if ClientProfile.user_has_profile(self.user):
                raise ValidationError("Un utilisateur ne peut pas être à la fois marchand et client. Supprimez d'abord le profil client.")
        
        # Validation des champs obligatoires pour KYC
        if self.kyc_status != self.KYC_PENDING:
            required_fields = ['company_name', 'contact_person', 'contact_phone', 'contact_email', 
                             'company_address', 'company_city', 'company_country', 'company_postal_code']
            missing_fields = [field for field in required_fields if not getattr(self, field)]
            if missing_fields:
                raise ValidationError(f"Les champs suivants sont obligatoires pour valider le KYC : {', '.join(missing_fields)}")
        
        # Validation du numéro de téléphone
        if self.contact_phone:
            phone_pattern = compile(r'^\+?[1-9]\d{1,14}$')
            if not phone_pattern.match(self.contact_phone):
                raise ValidationError("Le format du numéro de téléphone est incorrect")
        
        # Validation de l'email
        if self.contact_email:
            try:
                validate_email(self.contact_email)
            except ValidationError:
                raise ValidationError("Le format de l'email est incorrect")
    
    # Méthodes de création et mise à jour
    @classmethod
    def create_profile(cls, user, company_name, business_type=None, **extra_fields):
        """Crée un profil marchand avec les données de base"""
        # VÉRIFICATION D'UNICITÉ : Un utilisateur ne peut pas être à la fois merchant et client
        if ClientProfile.user_has_profile(user):
            raise ValidationError("Un utilisateur ne peut pas être à la fois marchand et client. Supprimez d'abord le profil client.")
        
        return cls.objects.create(
            user=user,
            company_name=company_name,
            contact_person=f"{user.first_name} {user.last_name}".strip() or user.username,
            contact_email=user.email,
            business_type=business_type or cls.BUSINESS_TRAVEL_AGENCY,
            kyc_status=cls.KYC_PENDING,
            is_verified=False,
            commission_rate=0.00,
            is_active=True,
            **extra_fields
        )
    
    @classmethod
    def create_from_registration_data(cls, user, company_name, business_type=None, contact_phone=None, **kwargs):
        """Crée un profil marchand à partir des données d'inscription"""
        return cls.create_profile(
            user=user,
            company_name=company_name,
            business_type=business_type,
            contact_phone=contact_phone or '',
            **kwargs
        )
    
    def update_kyc_status(self, new_status, admin_user=None):
        """Met à jour le statut KYC"""
        old_status = self.kyc_status
        self.kyc_status = new_status
        if admin_user:
            self.update_by = admin_user
        self.save()
        
        # Créer une validation KYC si changement
        if old_status != new_status and new_status in [self.KYC1_APPROVED, self.KYC2_APPROVED]:
            kyc_level = KYCValidation.KYC_LEVEL_1 if new_status == self.KYC1_APPROVED else KYCValidation.KYC_LEVEL_2
            KYCValidation.create_validation(self, kyc_level, admin_user)
    
    def update_commission_rate(self, new_rate, admin_user=None):
        """Met à jour le taux de commission"""
        self.commission_rate = new_rate
        if admin_user:
            self.update_by = admin_user
        self.save()
        return self
    
    def verify_merchant(self, admin_user=None):
        """Vérifie le marchand (active is_verified)"""
        self.is_verified = True
        if admin_user:
            self.update_by = admin_user
        self.save()
        return self
    
    def complete_company_data(self, **company_data):
        """Complète les données de l'entreprise"""
        for field, value in company_data.items():
            if self.is_valid_field(field) and value:
                setattr(self, field, value)
        self.save()
        return self
    
    def update_kyc_data(self, **kyc_data):
        """Met à jour les données KYC et gère la validation automatique"""
        # Mettre à jour les champs de base
        for field, value in kyc_data.items():
            if self.is_valid_field(field) and value is not None:
                setattr(self, field, value)
        
        # Gérer les documents avec le gestionnaire d'upload
        file_fields = {k: v for k, v in kyc_data.items() if k in ['business_license', 'company_registration_doc', 'tax_certificate'] and v}
        if file_fields:
            FileUploadManager.update_multiple_files(self, file_fields)
        
        # Sauvegarder les changements
        self.save()
        
        # Validation automatique du statut KYC
        self.update_kyc_status_automatically()
        return self
    
    def update_kyc_status_automatically(self):
        """Met à jour le statut KYC selon les règles métier"""
        if self.can_upgrade_to_kyc1():
            self.kyc_status = self.KYC1_APPROVED
        elif self.can_upgrade_to_kyc2():
            self.kyc_status = self.KYC2_APPROVED
        self.save()
    
    @classmethod
    def create_user_with_profile(cls, username, email, password, company_name, **profile_data):
        """Crée un utilisateur avec son profil marchand en une seule opération"""
        with transaction.atomic():
            # VÉRIFICATION D'UNICITÉ : S'assurer qu'aucun profil client n'existe déjà
            # Cette vérification est redondante car l'utilisateur est nouveau, mais c'est une sécurité
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            profile = cls.create_profile(user, company_name, **profile_data)
            return user, profile


class AdminProfile(models.Model):
    # Constantes pour les choix
    ADMIN_SUPER = 0
    ADMIN_SYSTEM = 1
    ADMIN_KYC = 2
    ADMIN_FINANCIAL = 3
    ADMIN_SUPPORT = 4
    
    ADMIN_LEVEL_CHOICES = [
        (ADMIN_SUPER, 'Super Administrateur'),
        (ADMIN_SYSTEM, 'Administrateur Système'),
        (ADMIN_KYC, 'Administrateur KYC'),
        (ADMIN_FINANCIAL, 'Administrateur Financier'),
        (ADMIN_SUPPORT, 'Administrateur Support'),
    ]
    
    # Champs du modèle
    # UUID pour identification externe
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='adminprofile_profile')
    admin_level = models.IntegerField(verbose_name="Niveau d'administration", choices=ADMIN_LEVEL_CHOICES, default=ADMIN_SUPPORT)
    department = models.CharField(max_length=100, verbose_name="Département", null=True, blank=True)
    can_manage_users = models.BooleanField(default=False, verbose_name="Peut gérer les utilisateurs")
    can_manage_merchants = models.BooleanField(default=False, verbose_name="Peut gérer les marchands")
    can_validate_kyc = models.BooleanField(default=False, verbose_name="Peut valider le KYC")
    can_access_financial_data = models.BooleanField(default=False, verbose_name="Accès aux données financières")
    can_manage_system = models.BooleanField(default=False, verbose_name="Peut gérer le système")
    admin_phone = models.CharField(max_length=20, verbose_name="Téléphone admin", null=True, blank=True)
    admin_extension = models.CharField(max_length=10, verbose_name="Extension", null=True, blank=True)
    is_active = models.BooleanField(verbose_name="Actif?", default=True)
    create = models.DateTimeField(verbose_name="Date de création", auto_now_add=True)
    last_update = models.DateTimeField(verbose_name="Dernière mise à jour", auto_now=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="adminprofile_createby", verbose_name="Créé par")
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="adminprofile_updateby", verbose_name="Mis à jour par")
    
    class Meta:
        verbose_name = "Profil Administrateur"
        verbose_name_plural = "Profils Administrateurs"
        ordering = ['-create']
    
    def __str__(self):
        return f"Admin: {self.user.username} - {self.get_admin_level_display()}"
    
    # Méthodes d'instance
    def get_admin_display_name(self):
        """Retourne le nom d'affichage de l'administrateur"""
        full_name = f"{self.user.first_name} {self.user.last_name}".strip()
        return full_name or self.user.username
    
    def get_display_name(self):
        """Méthode commune pour obtenir le nom d'affichage"""
        return self.get_admin_display_name()
    
    def get_profile_type(self):
        """Méthode commune pour obtenir le type de profil"""
        return PROFILE_TYPE_ADMIN
    
    def is_super_admin(self):
        """Vérifie si c'est un super administrateur"""
        return self.admin_level == self.ADMIN_SUPER
    
    def is_system_admin(self):
        """Vérifie si c'est un administrateur système"""
        return self.admin_level == self.ADMIN_SYSTEM
    
    def is_kyc_admin(self):
        """Vérifie si c'est un administrateur KYC"""
        return self.admin_level == self.ADMIN_KYC
    
    def is_financial_admin(self):
        """Vérifie si c'est un administrateur financier"""
        return self.admin_level == self.ADMIN_FINANCIAL
    
    def has_permission(self, permission):
        """Vérifie si l'admin a une permission spécifique"""
        permission_map = {
            'manage_users': self.can_manage_users,
            'manage_merchants': self.can_manage_merchants,
            'validate_kyc': self.can_validate_kyc,
            'access_financial': self.can_access_financial_data,
            'manage_system': self.can_manage_system
        }
        return permission_map.get(permission, False)
    
    def get_permissions_list(self):
        """Retourne la liste des permissions de l'administrateur"""
        permissions = []
        if self.can_manage_users:
            permissions.append('Gestion des utilisateurs')
        if self.can_manage_merchants:
            permissions.append('Gestion des marchands')
        if self.can_validate_kyc:
            permissions.append('Validation KYC')
        if self.can_access_financial_data:
            permissions.append('Accès données financières')
        if self.can_manage_system:
            permissions.append('Gestion système')
        return permissions
    
    def get_contact_info(self):
        """Retourne les informations de contact"""
        contact = self.admin_phone
        if self.admin_extension:
            contact += f" ext. {self.admin_extension}"
        return contact
    
    def can_validate_kyc_level(self, kyc_level):
        """Vérifie si l'admin peut valider un niveau KYC spécifique"""
        if not self.can_validate_kyc:
            return False
        
        # Super admin et System admin peuvent tout valider
        if self.admin_level in [self.ADMIN_SUPER, self.ADMIN_SYSTEM]:
            return True
        
        # Admin KYC peut valider KYC1 et KYC2
        if self.admin_level == self.ADMIN_KYC:
            return True
        
        return False
    
    # Méthodes de classe
    @classmethod
    def get_active_admins(cls):
        """Retourne tous les administrateurs actifs"""
        return cls.objects.filter(is_active=True)
    
    @classmethod
    def get_admins_by_level(cls, admin_level):
        """Retourne les administrateurs par niveau"""
        return cls.objects.filter(admin_level=admin_level, is_active=True)
    
    @classmethod
    def create_user_with_profile(cls, username, email, password, admin_level=ADMIN_SUPPORT, **profile_data):
        """Crée un utilisateur avec son profil admin en une seule opération"""
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            profile = cls.objects.create(
                user=user,
                admin_level=admin_level,
                **profile_data
            )
            return user, profile
    
    @classmethod
    def get_kyc_validators(cls):
        """Retourne tous les administrateurs pouvant valider le KYC"""
        return cls.objects.filter(can_validate_kyc=True, is_active=True)
    
    @classmethod
    def get_admins_by_department(cls, department):
        """Retourne les administrateurs par département"""
        return cls.objects.filter(department=department, is_active=True)
    
    @classmethod
    def get_super_admins(cls):
        """Retourne tous les super administrateurs"""
        return cls.objects.filter(admin_level=cls.ADMIN_SUPER, is_active=True)
    
    # Méthodes statiques
    @staticmethod
    def get_available_admin_levels():
        """Retourne la liste des niveaux d'administration disponibles"""
        return [{'code': choice[0], 'name': choice[1]} for choice in AdminProfile.ADMIN_LEVEL_CHOICES]
    
    @staticmethod
    def get_default_permissions_by_level():
        """Retourne les permissions par défaut par niveau d'administration"""
        return {
            AdminProfile.ADMIN_SUPER: {
                'can_manage_users': True,
                'can_manage_merchants': True,
                'can_validate_kyc': True,
                'can_access_financial_data': True,
                'can_manage_system': True
            },
            AdminProfile.ADMIN_SYSTEM: {
                'can_manage_users': True,
                'can_manage_merchants': True,
                'can_validate_kyc': True,
                'can_access_financial_data': False,
                'can_manage_system': True
            },
            AdminProfile.ADMIN_KYC: {
                'can_manage_users': False,
                'can_manage_merchants': False,
                'can_validate_kyc': True,
                'can_access_financial_data': False,
                'can_manage_system': False
            },
            AdminProfile.ADMIN_FINANCIAL: {
                'can_manage_users': False,
                'can_manage_merchants': True,
                'can_validate_kyc': False,
                'can_access_financial_data': True,
                'can_manage_system': False
            },
            AdminProfile.ADMIN_SUPPORT: {
                'can_manage_users': False,
                'can_manage_merchants': False,
                'can_validate_kyc': False,
                'can_access_financial_data': False,
                'can_manage_system': False
            }
        }
    
    @staticmethod
    def get_profile_for_user(user):
        """Retourne le profil admin pour un utilisateur donné"""
        try:
            return user.adminprofile_profile
        except:
            return None
    
    @staticmethod
    def user_has_profile(user):
        """Vérifie si l'utilisateur a un profil admin"""
        try:
            return bool(user.adminprofile_profile)
        except:
            return False
    
    @staticmethod
    def get_user_display_name(user):
        """Retourne le nom d'affichage pour un utilisateur admin"""
        profile = AdminProfile.get_profile_for_user(user)
        if profile:
            return profile.get_display_name()
        return None
    
    @staticmethod
    def user_can_validate_kyc(user):
        """Vérifie si l'utilisateur admin peut valider le KYC"""
        profile = AdminProfile.get_profile_for_user(user)
        if profile:
            return profile.can_validate_kyc
        return False
    
    # Méthodes de création et mise à jour
    @classmethod
    def create_profile(cls, user, admin_level, department=None, **permissions):
        """Crée un profil administrateur avec les permissions"""
        # Récupérer les permissions par défaut selon le niveau
        default_permissions = cls.get_default_permissions_by_level().get(admin_level, {})
        
        # Merger avec les permissions spécifiées
        final_permissions = {**default_permissions, **permissions}
        
        return cls.objects.create(
            user=user,
            admin_level=admin_level,
            department=department,
            is_active=True,
            **final_permissions
        )
    
    @classmethod
    def create_super_admin(cls, user, department=None):
        """Crée un super administrateur"""
        return cls.create_profile(user, cls.ADMIN_SUPER, department)
    
    @classmethod
    def create_kyc_admin(cls, user, department=None):
        """Crée un administrateur KYC"""
        return cls.create_profile(user, cls.ADMIN_KYC, department)
    
    @classmethod
    def create_financial_admin(cls, user, department=None):
        """Crée un administrateur financier"""
        return cls.create_profile(user, cls.ADMIN_FINANCIAL, department)
    
    def update_permissions(self, **permissions):
        """Met à jour les permissions de l'administrateur"""
        valid_permissions = [
            'can_manage_users', 'can_manage_merchants', 'can_validate_kyc',
            'can_access_financial_data', 'can_manage_system'
        ]
        
        for perm, value in permissions.items():
            if perm in valid_permissions:
                setattr(self, perm, value)
        
        self.save()
        return self
    
    def change_admin_level(self, new_level, admin_user=None):
        """Change le niveau d'administration"""
        old_level = self.admin_level
        self.admin_level = new_level
        
        # Appliquer les permissions par défaut du nouveau niveau
        default_permissions = self.get_default_permissions_by_level().get(new_level, {})
        for perm, value in default_permissions.items():
            setattr(self, perm, value)
        
        if admin_user:
            self.update_by = admin_user
        
        self.save()
        return self
    
    def activate_admin(self, admin_user=None):
        """Active l'administrateur"""
        self.is_active = True
        if admin_user:
            self.update_by = admin_user
        self.save()
        return self
    
    def deactivate_admin(self, admin_user=None):
        """Désactive l'administrateur"""
        self.is_active = False
        if admin_user:
            self.update_by = admin_user
        self.save()
        return self


class KYCValidation(models.Model):
    # Constantes pour les choix
    PROFILE_CLIENT = 0
    PROFILE_MERCHANT = 1
    
    PROFILE_TYPE_CHOICES = [
        (PROFILE_CLIENT, 'Client'),
        (PROFILE_MERCHANT, 'Marchand'),
    ]
    
    KYC_LEVEL_1 = 0
    KYC_LEVEL_2 = 1
    
    KYC_LEVEL_CHOICES = [
        (KYC_LEVEL_1, 'KYC Niveau 1'),
        (KYC_LEVEL_2, 'KYC Niveau 2'),
    ]
    
    VALIDATION_PENDING = 0
    VALIDATION_APPROVED = 1
    VALIDATION_REJECTED = 2
    
    VALIDATION_STATUS_CHOICES = [
        (VALIDATION_PENDING, 'En attente'),
        (VALIDATION_APPROVED, 'Approuvé'),
        (VALIDATION_REJECTED, 'Rejeté'),
    ]
    
    # Champs du modèle
    # UUID pour identification externe
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    
    profile_type = models.IntegerField(verbose_name="Type de profil", choices=PROFILE_TYPE_CHOICES, default=PROFILE_CLIENT)
    profile_id = models.PositiveIntegerField(verbose_name="ID du profil")
    kyc_level = models.IntegerField(verbose_name="Niveau KYC", choices=KYC_LEVEL_CHOICES, default=KYC_LEVEL_1)
    status = models.IntegerField(verbose_name="Statut", choices=VALIDATION_STATUS_CHOICES, default=VALIDATION_PENDING)
    validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    validated_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(verbose_name="Notes", null=True, blank=True)
    
    class Meta:
        verbose_name = "Validation KYC"
        verbose_name_plural = "Validations KYC"
        ordering = ['-validated_at']
    
    def __str__(self):
        return f"{self.get_profile_type_display()} - {self.get_kyc_level_display()} - {self.get_status_display()}"
    
    # Méthodes d'instance
    def is_pending(self):
        """Vérifie si la validation est en attente"""
        return self.status == self.VALIDATION_PENDING
    
    def is_approved(self):
        """Vérifie si la validation est approuvée"""
        return self.status == self.VALIDATION_APPROVED
    
    def is_rejected(self):
        """Vérifie si la validation est rejetée"""
        return self.status == self.VALIDATION_REJECTED
    
    def is_for_client(self):
        """Vérifie si c'est une validation pour un client"""
        return self.profile_type == self.PROFILE_CLIENT
    
    def is_for_merchant(self):
        """Vérifie si c'est une validation pour un marchand"""
        return self.profile_type == self.PROFILE_MERCHANT
    
    def is_kyc_level_1(self):
        """Vérifie si c'est une validation KYC niveau 1"""
        return self.kyc_level == self.KYC_LEVEL_1
    
    def is_kyc_level_2(self):
        """Vérifie si c'est une validation KYC niveau 2"""
        return self.kyc_level == self.KYC_LEVEL_2
    
    def get_profile_instance(self):
        """Retourne l'instance du profil correspondant"""
        return self.get_profile_by_type_and_id(self.profile_type, self.profile_id)


    
    def get_validation_summary(self):
        """Retourne un résumé de la validation"""
        profile = self.get_profile_instance()
        profile_name = "Profil inconnu"
        
        if profile:
            if self.profile_type == self.PROFILE_CLIENT:
                profile_name = profile.get_full_name()
            elif self.profile_type == self.PROFILE_MERCHANT:
                profile_name = profile.get_company_display_name()
        
        return {
            'profile_name': profile_name,
            'kyc_level': self.get_kyc_level_display(),
            'status': self.get_status_display(),
            'validated_by': self.validated_by.username if self.validated_by else 'Système',
            'validated_at': self.validated_at,
            'notes': self.notes
        }
    
    def can_be_modified(self):
        """Vérifie si la validation peut encore être modifiée"""
        return self.status == self.VALIDATION_PENDING
    
    # Méthodes de classe
    @classmethod
    def get_pending_validations(cls):
        """Retourne toutes les validations en attente"""
        return cls.objects.filter(status=cls.VALIDATION_PENDING).order_by('-validated_at')
    
    @classmethod
    def get_validations_by_profile_type(cls, profile_type):
        """Retourne les validations par type de profil"""
        return cls.objects.filter(profile_type=profile_type)
    
    @classmethod
    def get_validations_by_level(cls, kyc_level):
        """Retourne les validations par niveau KYC"""
        return cls.objects.filter(kyc_level=kyc_level)
    
    @classmethod
    def get_recent_validations(cls, days=7):
        """Retourne les validations récentes (7 jours par défaut)"""
        since_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(validated_at__gte=since_date)
    
    @classmethod
    def get_validations_by_admin(cls, admin_user):
        """Retourne les validations effectuées par un administrateur"""
        return cls.objects.filter(validated_by=admin_user)
    
    @classmethod
    def get_validation_stats(cls):
        """Retourne les statistiques de validation"""
        stats = cls.objects.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status=cls.VALIDATION_PENDING)),
            approved=Count('id', filter=Q(status=cls.VALIDATION_APPROVED)),
            rejected=Count('id', filter=Q(status=cls.VALIDATION_REJECTED))
        )
        
        return {
            'total': stats['total'] or 0,
            'pending': stats['pending'] or 0,
            'approved': stats['approved'] or 0,
            'rejected': stats['rejected'] or 0,
            'pending_percentage': (stats['pending'] / stats['total'] * 100) if stats['total'] else 0,
            'approval_rate': (stats['approved'] / stats['total'] * 100) if stats['total'] else 0
        }
    
    # Méthodes statiques
    @staticmethod
    def get_available_profile_types():
        """Retourne la liste des types de profil disponibles"""
        return [{'code': choice[0], 'name': choice[1]} for choice in KYCValidation.PROFILE_TYPE_CHOICES]
    
    @staticmethod
    def get_available_kyc_levels():
        """Retourne la liste des niveaux KYC disponibles"""
        return [{'code': choice[0], 'name': choice[1]} for choice in KYCValidation.KYC_LEVEL_CHOICES]
    
    @staticmethod
    def get_validation_workflow():
        """Retourne le workflow de validation KYC"""
        return {
            'client': {
                'KYC1': ['document', 'personal_info'],
                'requirements': 'Document d\'identité et informations personnelles'
            },
            'merchant': {
                'KYC1': ['business_license', 'company_registration_doc'],
                'KYC2': ['tax_certificate', 'complete_profile'],
                'requirements': 'Documents légaux et profil complet'
            }
        }
    
    # Méthodes statiques utilitaires
    @staticmethod
    def determine_profile_type(profile_instance):
        """Détermine le type de profil pour la validation KYC"""
        profile_type_name = profile_instance.get_profile_type()
        
        if profile_type_name == PROFILE_TYPE_CLIENT:
            return KYCValidation.PROFILE_CLIENT
        elif profile_type_name == PROFILE_TYPE_MERCHANT:
            return KYCValidation.PROFILE_MERCHANT
        else:
            raise ValueError(f"Type de profil non supporté pour validation KYC: {profile_type_name}")
    
    @staticmethod
    def get_profile_by_type_and_id(profile_type, profile_id):
        """Retourne l'instance du profil selon le type et l'ID"""
        if profile_type == KYCValidation.PROFILE_CLIENT:
            try:
                return ClientProfile.objects.get(id=profile_id)
            except ClientProfile.DoesNotExist:
                return None
        elif profile_type == KYCValidation.PROFILE_MERCHANT:
            try:
                return MerchantProfile.objects.get(id=profile_id)
            except MerchantProfile.DoesNotExist:
                return None
        return None
    
    # Méthodes de création et validation
    @classmethod
    def create_validation(cls, profile_instance, kyc_level, validated_by=None, notes=None):
        """Crée une validation KYC pour un profil"""
        profile_type = cls.determine_profile_type(profile_instance)
        
        return cls.objects.create(
            profile_type=profile_type,
            profile_id=profile_instance.id,
            kyc_level=kyc_level,
            status=cls.VALIDATION_PENDING,
            validated_by=validated_by,
            notes=notes
        )
    
    @classmethod
    def approve_validation(cls, validation_id, admin_user, notes=None):
        """Approuve une validation KYC"""
        validation = cls.objects.get(id=validation_id)
        validation.status = cls.VALIDATION_APPROVED
        validation.validated_by = admin_user
        if notes:
            validation.notes = notes
        validation.save()
        
        # Mettre à jour le profil correspondant
        profile = validation.get_profile_instance()
        if profile:
            if validation.kyc_level == cls.KYC_LEVEL_1:
                profile.kyc_status = profile.KYC1_APPROVED
            elif validation.kyc_level == cls.KYC_LEVEL_2:
                profile.kyc_status = profile.KYC2_APPROVED
            profile.save()
        
        return validation
    
    @classmethod
    def reject_validation(cls, validation_id, admin_user, notes):
        """Rejette une validation KYC"""
        validation = cls.objects.get(id=validation_id)
        validation.status = cls.VALIDATION_REJECTED
        validation.validated_by = admin_user
        validation.notes = notes
        validation.save()
        
        # Mettre à jour le profil correspondant
        profile = validation.get_profile_instance()
        if profile:
            profile.kyc_status = profile.KYC_REJECTED
            profile.save()
        
        return validation
