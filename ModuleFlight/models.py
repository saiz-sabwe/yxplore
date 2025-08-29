from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from decimal import Decimal
import uuid
import random
import string
from datetime import datetime
from ModuleProfils.models import ClientProfile, MerchantProfile, UserProfileManager
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class FlightUserManager:
    """Gestionnaire pour les vérifications d'utilisateur du module Flight"""
    
    @staticmethod
    def user_is_merchant(user):
        """Vérifie si l'utilisateur est un marchand"""
        return MerchantProfile.user_has_profile(user)
    
    @staticmethod
    def user_is_client(user):
        """Vérifie si l'utilisateur est un client"""
        return ClientProfile.user_has_profile(user)
    
    @staticmethod
    def get_user_profile(user):
        """Retourne le profil de l'utilisateur"""
        return UserProfileManager.get_primary_profile(user)
    
    @staticmethod
    def get_user_type(user):
        """Retourne le type d'utilisateur"""
        return UserProfileManager.determine_user_type(user)


class TravelAgency(models.Model):
    """Modèle pour les agences de voyages (établissements)"""
    
    # UUID pour identification externe
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    
    name = models.CharField(max_length=200, verbose_name="Nom de l'agence")
    country = models.CharField(max_length=100, verbose_name="Pays")
    city = models.CharField(max_length=100, verbose_name="Ville")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse")
    iata_code = models.CharField(
        max_length=3, 
        blank=True, 
        null=True, 
        verbose_name="Code IATA",
        help_text="Code IATA de l'agence (optionnel)"
    )
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    
    # Champs standards
    is_active = models.BooleanField(verbose_name="Actif?", default=True)
    create = models.DateTimeField(verbose_name="Date de création", auto_now_add=True)
    last_update = models.DateTimeField(verbose_name="Dernière mise à jour", auto_now=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="travelagency_createby", verbose_name="Créé par")
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="travelagency_updateby", verbose_name="Mis à jour par")

    class Meta:
        verbose_name = "Agence de voyage"
        verbose_name_plural = "Agences de voyage"
        ordering = ['-create']

    def __str__(self):
        return f"{self.name} ({self.city}, {self.country})"
    
    @classmethod
    def get_active_agencies(cls):
        """Retourne toutes les agences actives"""
        return cls.objects.filter(is_active=True)
    
    @classmethod
    def get_agency_by_id(cls, agency_id):
        """Retourne une agence active par son ID"""
        try:
            return cls.objects.get(id=agency_id, is_active=True)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_agency_by_uuid(cls, agency_uuid):
        """Retourne une agence active par son UUID"""
        try:
            return cls.objects.get(uuid=agency_uuid, is_active=True)
        except cls.DoesNotExist:
            return None
    
    @classmethod 
    def get_agencies_for_user(cls, user):
        """Retourne les agences visibles pour un utilisateur selon son profil"""
        if FlightUserManager.user_is_merchant(user):
            # Un marchand ne voit que ses agences
            return cls.objects.filter(
                merchantagency__merchant=user.merchantprofile_profile,
                merchantagency__is_active=True
            ).distinct()
        else:
            # Un client voit toutes les agences actives
            return cls.get_active_agencies()
    
    @classmethod
    def get_default_agency(cls):
        """Retourne l'agence par défaut ou en crée une si elle n'existe pas"""
        try:
            # Essayer de récupérer l'agence par défaut
            default_agency = cls.objects.filter(is_active=True).first()
            if default_agency:
                return default_agency
            
            # Si aucune agence n'existe, en créer une par défaut
            default_agency = cls.objects.create(
                name="YXplore Travel Agency",
                country="France",
                city="Paris",
                address="123 Avenue des Champs-Élysées, 75008 Paris",
                iata_code="YXA",
                phone="+33 1 23 45 67 89",
                email="contact@yxplore-travel.com",
                is_active=True
            )
            logger.info(f"Agence par défaut créée: {default_agency}")
            return default_agency
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'agence par défaut: {e}")
            # Retourner None en cas d'erreur
            return None
    
    def get_responsible_merchants(self):
        """Retourne les marchands responsables de cette agence"""
        return MerchantProfile.objects.filter(
            merchantagency__agency=self,
            merchantagency__is_responsible=True
        )
    
    def deactivate(self, updated_by=None):
        """Désactive l'agence"""
        self.is_active = False
        if updated_by:
            self.update_by = updated_by
        self.save()
        return True


class MerchantAgency(models.Model):
    """Relation entre un marchand et une agence de voyage"""
    
    # Constantes pour les rôles
    ROLE_MANAGER = 'MANAGER'
    ROLE_AGENT = 'AGENT'
    ROLE_SUPERVISOR = 'SUPERVISOR'
    
    ROLE_CHOICES = [
        (ROLE_MANAGER, 'Responsable'),
        (ROLE_AGENT, 'Agent'),
        (ROLE_SUPERVISOR, 'Superviseur'),
    ]
    
    # UUID pour identification externe
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    
    merchant = models.ForeignKey(
        MerchantProfile, 
        on_delete=models.CASCADE,
        verbose_name="Marchand"
    )
    agency = models.ForeignKey(
        TravelAgency, 
        on_delete=models.CASCADE,
        verbose_name="Agence"
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default=ROLE_AGENT,
        verbose_name="Rôle"
    )
    is_responsible = models.BooleanField(
        default=False, 
        verbose_name="Responsable principal"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    # Champs standards
    is_active = models.BooleanField(verbose_name="Actif?", default=True)
    create = models.DateTimeField(verbose_name="Date de création", auto_now_add=True)
    last_update = models.DateTimeField(verbose_name="Dernière mise à jour", auto_now=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="merchantagency_createby", verbose_name="Créé par")
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="merchantagency_updateby", verbose_name="Mis à jour par")

    class Meta:
        verbose_name = "Affectation Marchand-Agence"
        verbose_name_plural = "Affectations Marchand-Agence"
        unique_together = ['merchant', 'agency']
        ordering = ['-create']

    def __str__(self):
        return f"{self.merchant.user.username} - {self.agency.name} ({self.role})"
    
    @classmethod
    def get_agencies_for_merchant(cls, user):
        """Retourne les agences d'un marchand"""
        if not FlightUserManager.user_is_merchant(user):
            return cls.objects.none()
        
        return cls.objects.filter(
            merchant=user.merchantprofile_profile,
            is_active=True
        ).select_related('agency')
    
    @classmethod
    def get_merchants_for_agency(cls, agency):
        """Retourne les marchands d'une agence"""
        return cls.objects.filter(
            agency=agency,
            is_active=True
        ).select_related('merchant')
    
    @classmethod
    def get_all_active_assignments(cls):
        """Retourne toutes les affectations actives"""
        return cls.objects.filter(is_active=True).select_related('agency', 'merchant__user')
    
    @classmethod
    def assign_merchant_to_agency(cls, merchant, agency, role=None, is_responsible=False, created_by=None):
        """Assigne un marchand à une agence"""
        try:
            assignment, created = cls.objects.get_or_create(
                merchant=merchant,
                agency=agency,
                defaults={
                    'role': role or cls.ROLE_AGENT,
                    'is_responsible': is_responsible,
                    'is_active': True,
                    'create_by': created_by
                }
            )
            if not created:
                assignment.role = role or cls.ROLE_AGENT
                assignment.is_responsible = is_responsible
                assignment.is_active = True
                assignment.update_by = created_by
                assignment.save()
            return assignment
        except Exception as e:
            raise ValidationError(f"Erreur lors de l'affectation: {str(e)}")
    
    def remove_assignment(self, updated_by=None):
        """Retire l'affectation"""
        self.is_active = False
        if updated_by:
            self.update_by = updated_by
        self.save()
        return True


class FlightBooking(models.Model):
    """Modèle pour les réservations de vols"""
    
    # Constantes pour les statuts
    STATUS_PENDING = 'PENDING'
    STATUS_CONFIRMED = 'CONFIRMED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_EXPIRED = 'EXPIRED'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_CONFIRMED, 'Confirmé'),
        (STATUS_CANCELLED, 'Annulé'),
        (STATUS_EXPIRED, 'Expiré'),
    ]
    
    # Constantes pour les statuts de paiement
    PAYMENT_UNPAID = 'UNPAID'
    PAYMENT_PAID = 'PAID'
    PAYMENT_REFUNDED = 'REFUNDED'
    PAYMENT_FAILED = 'FAILED'
    
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_UNPAID, 'Non payé'),
        (PAYMENT_PAID, 'Payé'),
        (PAYMENT_REFUNDED, 'Remboursé'),
        (PAYMENT_FAILED, 'Échec'),
    ]
    
    # UUID pour identification externe
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    
    booking_reference = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Référence de réservation"
    )
    
    # Relations
    client = models.ForeignKey(
        ClientProfile, 
        on_delete=models.CASCADE,
        verbose_name="Client"
    )
    agency = models.ForeignKey(
        TravelAgency, 
        on_delete=models.CASCADE,
        verbose_name="Agence"
    )
    merchant = models.ForeignKey(
        MerchantProfile, 
        on_delete=models.CASCADE,
        verbose_name="Marchand responsable"
    )
    
    # Données Duffel API v2
    duffel_offer_id = models.CharField(
        max_length=255, 
        verbose_name="ID offre Duffel",
        help_text="Identifiant de l'offre Duffel (format: off_xxxxx)"
    )
    duffel_order_id = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="ID commande Duffel",
        help_text="Identifiant de la commande Duffel (format: ord_xxxxx)"
    )
    duffel_offer_request_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID demande d'offre Duffel",
        help_text="Identifiant de l'offer_request Duffel (format: orq_xxxxx)"
    )
    duffel_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID intention de paiement Duffel",
        help_text="Identifiant du payment intent Duffel (format: pit_xxxxx)"
    )
    
    # Informations vol
    origin = models.CharField(max_length=10, verbose_name="Origine (code aéroport)")
    destination = models.CharField(max_length=10, verbose_name="Destination (code aéroport)")
    departure_date = models.DateTimeField(verbose_name="Date de départ")
    return_date = models.DateTimeField(blank=True, null=True, verbose_name="Date de retour")
    passenger_count = models.PositiveIntegerField(default=1, verbose_name="Nombre de passagers")
    
    # Informations financières
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Prix total"
    )
    currency = models.CharField(max_length=3, default='EUR', verbose_name="Devise")
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('5.00'),
        verbose_name="Taux de commission (%)"
    )
    
    # Statuts
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=STATUS_PENDING,
        verbose_name="Statut"
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default=PAYMENT_UNPAID,
        verbose_name="Statut de paiement"
    )
    
    # Métadonnées Duffel API v2
    passenger_data = models.JSONField(
        default=dict, 
        verbose_name="Données des passagers",
        help_text="Données passagers conformes API Duffel (avec IDs)"
    )
    duffel_offer_data = models.JSONField(
        default=dict, 
        verbose_name="Cache offre Duffel",
        help_text="Données complètes de l'offre Duffel"
    )
    duffel_order_data = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Cache commande Duffel",
        help_text="Données complètes de la commande Duffel"
    )
    
    # Champs API Duffel v2 spécifiques
    duffel_live_mode = models.BooleanField(
        default=False,
        verbose_name="Mode production Duffel",
        help_text="True si réservation en mode production"
    )
    duffel_expires_at = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Expiration offre Duffel"
    )
    duffel_conditions = models.JSONField(
        default=dict,
        verbose_name="Conditions Duffel",
        help_text="Conditions de changement et remboursement"
    )
    
    # Timestamps spécifiques
    confirmed_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    # Champs standards
    is_active = models.BooleanField(verbose_name="Actif?", default=True)
    create = models.DateTimeField(verbose_name="Date de création", auto_now_add=True)
    last_update = models.DateTimeField(verbose_name="Dernière mise à jour", auto_now=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="flightbooking_createby", verbose_name="Créé par")
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="flightbooking_updateby", verbose_name="Mis à jour par")

    class Meta:
        verbose_name = "Réservation de vol"
        verbose_name_plural = "Réservations de vol"
        ordering = ['-create']

    def __str__(self):
        return f"{self.booking_reference} - {self.client.user.username} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Génère automatiquement la référence de réservation"""
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        """Génère une référence de réservation unique"""
        import random
        import string
        
        while True:
            ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not FlightBooking.objects.filter(booking_reference=ref).exists():
                return ref
    
    @classmethod
    def get_bookings_for_user(cls, user):
        """Retourne les réservations pour un utilisateur selon son profil"""
        if FlightUserManager.user_is_client(user):
            return cls.objects.filter(client=user.clientprofile_profile)
        elif FlightUserManager.user_is_merchant(user):
            return cls.objects.filter(merchant=user.merchantprofile_profile)
        else:
            return cls.objects.none()
    
    @classmethod
    def get_client_bookings(cls, user):
        """Retourne les réservations d'un client"""
        if not FlightUserManager.user_is_client(user):
            return cls.objects.none()
        return cls.objects.filter(client=user.clientprofile_profile)
    
    @classmethod
    def get_merchant_bookings(cls, user):
        """Retourne les réservations d'un marchand"""
        if not FlightUserManager.user_is_merchant(user):
            return cls.objects.none()
        return cls.objects.filter(merchant=user.merchantprofile_profile)
    
    @classmethod
    def get_bookings_by_client(cls, client_profile):
        """Retourne les réservations d'un profil client spécifique"""
        return cls.objects.filter(client=client_profile).order_by('-create')
    
    @classmethod
    def get_bookings_by_merchant(cls, merchant_profile):
        """Retourne les réservations d'un profil marchand spécifique"""
        return cls.objects.filter(merchant=merchant_profile).order_by('-create')
    
    @classmethod
    def get_all_bookings_ordered(cls):
        """Retourne toutes les réservations ordonnées par date de création"""
        return cls.objects.all().order_by('-create')
    
    @classmethod
    def get_booking_by_uuid_for_user(cls, booking_uuid, user):
        """Retourne une réservation par UUID pour un utilisateur spécifique"""
        try:
            if FlightUserManager.user_is_client(user):
                return cls.objects.get(
                    uuid=booking_uuid,
                    client=user.clientprofile_profile
                )
            elif FlightUserManager.user_is_merchant(user):
                return cls.objects.get(
                    uuid=booking_uuid,
                    merchant=user.merchantprofile_profile
                )
            else:
                return None
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def create_booking(cls, client, agency, merchant, duffel_offer_id, flight_details, passenger_data=None, created_by=None):
        """Crée une nouvelle réservation de vol"""
        try:
            booking = cls.objects.create(
                client=client,
                agency=agency,
                merchant=merchant,
                duffel_offer_id=duffel_offer_id,
                origin=flight_details.get('origin', ''),
                destination=flight_details.get('destination', ''),
                departure_date=flight_details.get('departure_date'),
                return_date=flight_details.get('return_date'),
                passenger_count=flight_details.get('passenger_count', 1),
                price=flight_details.get('price', 0),
                currency=flight_details.get('currency', 'EUR'),
                passenger_data=passenger_data or {},
                flight_data=flight_details,
                status=cls.STATUS_PENDING,
                create_by=created_by
            )
            return booking
        except Exception as e:
            raise ValidationError(f"Erreur lors de la création de la réservation: {str(e)}")
    
    def confirm_booking(self, duffel_booking_id=None, updated_by=None):
        """Confirme la réservation"""
        self.status = self.STATUS_CONFIRMED
        self.confirmed_at = datetime.now()
        if duffel_booking_id:
            self.duffel_booking_id = duffel_booking_id
        if updated_by:
            self.update_by = updated_by
        self.save()
        return True
    
    def cancel_booking(self, updated_by=None):
        """Annule la réservation"""
        if self.status == self.STATUS_CONFIRMED:
            raise ValidationError("Impossible d'annuler une réservation confirmée")
        
        self.status = self.STATUS_CANCELLED
        if updated_by:
            self.update_by = updated_by
        self.save()
        return True
    
    def mark_paid(self, payment_method='FAKE', updated_by=None):
        """Marque la réservation comme payée"""
        if self.payment_status == self.PAYMENT_PAID:
            raise ValidationError("Cette réservation est déjà payée")
        
        self.payment_status = self.PAYMENT_PAID
        self.paid_at = datetime.now()
        
        # Confirme automatiquement la réservation si elle était en attente
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_CONFIRMED
            self.confirmed_at = datetime.now()
        
        if updated_by:
            self.update_by = updated_by
        self.save()
        return True
    
    def calculate_commission(self):
        """Calcule la commission sur cette réservation"""
        if self.price is None:
            return Decimal('0.00')
        return (self.price * self.commission_rate) / 100
    
    def get_total_with_commission(self):
        """Retourne le prix total avec commission"""
        if self.price is None:
            return Decimal('0.00')
        return self.price + self.calculate_commission()
    
    def is_cancellable(self):
        """Vérifie si la réservation peut être annulée"""
        return self.status in [self.STATUS_PENDING] and self.payment_status == self.PAYMENT_UNPAID
    
    def is_refundable(self):
        """Vérifie si la réservation peut être remboursée"""
        return self.status == self.STATUS_CONFIRMED and self.payment_status == self.PAYMENT_PAID
    
    @classmethod
    def get_bookings_by_client(cls, client):
        """Retourne toutes les réservations d'un client"""
        return cls.objects.filter(client=client).order_by('-created_at')
    
    @classmethod
    def get_bookings_by_agency(cls, agency):
        """Retourne toutes les réservations d'une agence"""
        return cls.objects.filter(agency=agency).order_by('-created_at')
    
    @classmethod
    def get_bookings_by_merchant(cls, merchant):
        """Retourne toutes les réservations gérées par un marchand"""
        return cls.objects.filter(merchant=merchant).order_by('-created_at')


class Passenger(models.Model):
    """Modèle pour les passagers d'une réservation"""
    
    # Constantes pour le type de passager
    TYPE_ADULT = 'adult'
    TYPE_CHILD = 'child'
    TYPE_INFANT = 'infant'
    
    TYPE_CHOICES = [
        (TYPE_ADULT, 'Adulte'),
        (TYPE_CHILD, 'Enfant'),
        (TYPE_INFANT, 'Bébé'),
    ]
    
    # Constantes pour le genre
    GENDER_MALE = 'm'
    GENDER_FEMALE = 'f'
    GENDER_OTHER = 'x'
    
    GENDER_CHOICES = [
        (GENDER_MALE, 'Masculin'),
        (GENDER_FEMALE, 'Féminin'),
        (GENDER_OTHER, 'Autre'),
    ]
    
    # Constantes pour la civilité
    TITLE_MR = 'mr'
    TITLE_MRS = 'mrs'
    TITLE_MS = 'ms'
    
    TITLE_CHOICES = [
        (TITLE_MR, 'M.'),
        (TITLE_MRS, 'Mme'),
        (TITLE_MS, 'Mlle'),
    ]

    # Champs de base
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    is_active = models.BooleanField(verbose_name="Actif?", default=True)
    create = models.DateTimeField(verbose_name="Date de création", auto_now_add=True)
    last_update = models.DateTimeField(verbose_name="Dernière mise à jour", auto_now=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="passenger_createby", verbose_name="Créé par")
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="passenger_updateby", verbose_name="Mis à jour par")

    # Champs du passager
    booking = models.ForeignKey(FlightBooking, on_delete=models.CASCADE, related_name='passengers', verbose_name="Réservation")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type de passager")
    title = models.CharField(max_length=10, choices=TITLE_CHOICES, verbose_name="Civilité")
    given_name = models.CharField(max_length=100, verbose_name="Prénom")
    family_name = models.CharField(max_length=100, verbose_name="Nom de famille")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Genre")
    date_of_birth = models.DateField(verbose_name="Date de naissance")
    nationality = models.CharField(max_length=2, verbose_name="Nationalité")
    country_code = models.CharField(max_length=2, null=True, blank=True, verbose_name="Pays de résidence")
    
    # Informations de contact
    email = models.EmailField(null=True, blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Téléphone")
    
    # Informations Duffel
    duffel_passenger_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="ID passager Duffel")
    duffel_fare_basis_code = models.CharField(max_length=50, null=True, blank=True, verbose_name="Code de base tarifaire Duffel")

    class Meta:
        verbose_name = "Passager"
        verbose_name_plural = "Passagers"
        ordering = ['-create']
        unique_together = ['booking', 'given_name', 'family_name', 'date_of_birth']

    def __str__(self):
        return f"{self.get_title_display()} {self.given_name} {self.family_name} ({self.get_type_display()})"

    @classmethod
    def get_passengers_for_booking(cls, booking):
        """Récupère tous les passagers d'une réservation"""
        return cls.objects.filter(booking=booking, is_active=True).order_by('type', 'create')

    def get_full_name(self):
        """Retourne le nom complet du passager"""
        return f"{self.given_name} {self.family_name}"

    def get_age(self):
        """Calcule l'âge du passager"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))


class FlightBookingDetail(models.Model):
    """Modèle pour les détails techniques d'une réservation"""
    
    # Champs de base
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    is_active = models.BooleanField(verbose_name="Actif?", default=True)
    create = models.DateTimeField(verbose_name="Date de création", auto_now_add=True)
    last_update = models.DateTimeField(verbose_name="Dernière mise à jour", auto_now=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="flightbookingdetail_createby", verbose_name="Créé par")
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="flightbookingdetail_updateby", verbose_name="Mis à jour par")

    # Champs de la réservation
    booking = models.OneToOneField(FlightBooking, on_delete=models.CASCADE, related_name='details', verbose_name="Réservation")
    
    # Données Duffel complètes
    duffel_data = models.JSONField(verbose_name="Données Duffel complètes")
    
    # Informations de vol
    origin = models.CharField(max_length=10, null=True, blank=True, verbose_name="Aéroport d'origine")
    destination = models.CharField(max_length=10, null=True, blank=True, verbose_name="Aéroport de destination")
    departure_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de départ")
    return_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de retour")
    
    # Informations de l'offre
    fare_brand_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Nom de la marque tarifaire")
    cabin_class = models.CharField(max_length=20, null=True, blank=True, verbose_name="Classe de cabine")
    
    # Métadonnées
    notes = models.TextField(blank=True, verbose_name="Notes techniques")

    class Meta:
        verbose_name = "Détail de réservation de vol"
        verbose_name_plural = "Détails de réservation de vol"
        ordering = ['-create']

    def __str__(self):
        return f"Détails de la réservation {self.booking.booking_reference}"

    def extract_flight_info(self):
        """Extrait les informations de vol des données Duffel"""
        if not self.duffel_data:
            return {}
        
        try:
            slices = self.duffel_data.get('slices', [])
            if slices:
                first_slice = slices[0]
                segments = first_slice.get('segments', [])
                if segments:
                    first_segment = segments[0]
                    return {
                        'origin': first_segment.get('origin', {}).get('iata_code'),
                        'destination': first_segment.get('destination', {}).get('iata_code'),
                        'departure_date': first_segment.get('departing_at'),
                        'return_date': segments[-1].get('arriving_at') if len(segments) > 1 else None,
                        'fare_brand_name': first_slice.get('fare_brand_name'),
                        'cabin_class': segments[0].get('passengers', [{}])[0].get('cabin_class') if segments[0].get('passengers') else None
                    }
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des informations de vol: {str(e)}")
        
        return {}