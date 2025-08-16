from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


# ========== EXTENSIONS DU MODÈLE USER ==========

def get_user_profile(self):
    """Retourne le profil de l'utilisateur"""
    if hasattr(self, 'clientprofile_profile'):
        return self.clientprofile_profile
    elif hasattr(self, 'merchantprofile_profile'):
        return self.merchantprofile_profile
    elif hasattr(self, 'adminprofile_profile'):
        return self.adminprofile_profile
    return None

def get_user_type(self):
    """Retourne le type d'utilisateur"""
    if hasattr(self, 'clientprofile_profile'):
        return 'client'
    elif hasattr(self, 'merchantprofile_profile'):
        return 'merchant'
    elif hasattr(self, 'adminprofile_profile'):
        return 'admin'
    return None

def is_client(self):
    """Vérifie si l'utilisateur est un client"""
    return hasattr(self, 'clientprofile_profile')

def is_merchant(self):
    """Vérifie si l'utilisateur est un marchand"""
    return hasattr(self, 'merchantprofile_profile')

def is_admin_user(self):
    """Vérifie si l'utilisateur est un administrateur"""
    return hasattr(self, 'adminprofile_profile')

def get_display_name(self):
    """Retourne le nom d'affichage de l'utilisateur"""
    profile = self.get_user_profile()
    if profile:
        if hasattr(profile, 'get_full_name'):
            return profile.get_full_name()
        elif hasattr(profile, 'get_company_display_name'):
            return profile.get_company_display_name()
        elif hasattr(profile, 'get_admin_display_name'):
            return profile.get_admin_display_name()
    
    # Fallback sur first_name + last_name ou username
    full_name = f"{self.first_name} {self.last_name}".strip()
    return full_name or self.username

def get_kyc_status(self):
    """Retourne le statut KYC de l'utilisateur"""
    profile = self.get_user_profile()
    if profile and hasattr(profile, 'kyc_status'):
        return profile.kyc_status
    return None

def is_kyc_approved(self):
    """Vérifie si le KYC de l'utilisateur est approuvé"""
    profile = self.get_user_profile()
    if profile and hasattr(profile, 'is_kyc_approved'):
        return profile.is_kyc_approved()
    return False

# Ajouter les méthodes au modèle User
User.add_to_class('get_user_profile', get_user_profile)
User.add_to_class('get_user_type', get_user_type)
User.add_to_class('is_client', is_client)
User.add_to_class('is_merchant', is_merchant)
User.add_to_class('is_admin_user', is_admin_user)
User.add_to_class('get_display_name', get_display_name)
User.add_to_class('get_kyc_status', get_kyc_status)
User.add_to_class('is_kyc_approved', is_kyc_approved)


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
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='clientprofile_profile')
    nom = models.CharField(max_length=255, verbose_name="Nom", null=True, blank=True)
    prenom = models.CharField(max_length=255, verbose_name="Prénom", null=True, blank=True)
    phone = models.CharField(max_length=20, verbose_name="Téléphone", null=True, blank=True)
    address = models.TextField(verbose_name="Adresse", null=True, blank=True)
    birth_date = models.DateField(verbose_name="Date de naissance", null=True, blank=True)
    nationality = models.CharField(max_length=100, verbose_name="Nationalité", null=True, blank=True)
    kyc_status = models.IntegerField(verbose_name="Statut KYC", choices=KYC_STATUS_CHOICES, default=KYC_PENDING)
    id_document = models.FileField(upload_to='kyc/clients/documents/', validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])], verbose_name="Document d'identité", null=True, blank=True)
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
        return self.kyc_status == self.KYC_PENDING and self.id_document
    
    def get_kyc_completion_percentage(self):
        """Retourne le pourcentage de completion du profil KYC"""
        required_fields = ['nom', 'prenom', 'phone', 'address', 'birth_date', 'nationality', 'id_document']
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
            'id_document': 'Document d\'identité'
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
    
    # Méthodes de création et mise à jour
    @classmethod
    def create_profile(cls, user, **extra_fields):
        """Crée un profil client avec les données de base"""
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
            if hasattr(self, field) and value:
                setattr(self, field, value)
        self.save()
        return self


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
    business_license = models.FileField(upload_to='kyc/merchants/licenses/', validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])], verbose_name="Licence commerciale", null=True, blank=True)
    tax_certificate = models.FileField(upload_to='kyc/merchants/tax/', validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])], verbose_name="Certificat fiscal", null=True, blank=True)
    company_registration_doc = models.FileField(upload_to='kyc/merchants/registration/', validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])], verbose_name="Document d'enregistrement", null=True, blank=True)
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
        from django.db.models import Avg
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
    
    # Méthodes de création et mise à jour
    @classmethod
    def create_profile(cls, user, company_name, business_type=None, **extra_fields):
        """Crée un profil marchand avec les données de base"""
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
            if hasattr(self, field) and value:
                setattr(self, field, value)
        self.save()
        return self


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
        if self.profile_type == self.PROFILE_CLIENT:
            try:
                return ClientProfile.objects.get(id=self.profile_id)
            except ClientProfile.DoesNotExist:
                return None
        elif self.profile_type == self.PROFILE_MERCHANT:
            try:
                return MerchantProfile.objects.get(id=self.profile_id)
            except MerchantProfile.DoesNotExist:
                return None
        return None
    
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
        from django.utils import timezone
        from datetime import timedelta
        
        since_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(validated_at__gte=since_date)
    
    @classmethod
    def get_validations_by_admin(cls, admin_user):
        """Retourne les validations effectuées par un administrateur"""
        return cls.objects.filter(validated_by=admin_user)
    
    @classmethod
    def get_validation_stats(cls):
        """Retourne les statistiques de validation"""
        from django.db.models import Count
        
        stats = cls.objects.aggregate(
            total=Count('id'),
            pending=Count('id', filter=models.Q(status=cls.VALIDATION_PENDING)),
            approved=Count('id', filter=models.Q(status=cls.VALIDATION_APPROVED)),
            rejected=Count('id', filter=models.Q(status=cls.VALIDATION_REJECTED))
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
                'KYC1': ['id_document', 'personal_info'],
                'requirements': 'Document d\'identité et informations personnelles'
            },
            'merchant': {
                'KYC1': ['business_license', 'company_registration_doc'],
                'KYC2': ['tax_certificate', 'complete_profile'],
                'requirements': 'Documents légaux et profil complet'
            }
        }
    
    # Méthodes de création et validation
    @classmethod
    def create_validation(cls, profile_instance, kyc_level, validated_by=None, notes=None):
        """Crée une validation KYC pour un profil"""
        if profile_instance.__class__.__name__ == 'ClientProfile':
            profile_type = cls.PROFILE_CLIENT
        elif profile_instance.__class__.__name__ == 'MerchantProfile':
            profile_type = cls.PROFILE_MERCHANT
        else:
            raise ValueError("Type de profil non supporté")
        
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
