from rest_framework import serializers
from .models import TravelAgency, MerchantAgency, FlightBooking
from ModuleProfils.models import ClientProfile, MerchantProfile


class TravelAgencySerializer(serializers.ModelSerializer):
    """Serializer pour les agences de voyage"""
    
    responsible_merchants = serializers.SerializerMethodField()
    
    class Meta:
        model = TravelAgency
        fields = [
            'uuid', 'name', 'country', 'city', 'address', 'iata_code',
            'phone', 'email', 'is_active', 'create', 'last_update',
            'create_by', 'update_by', 'responsible_merchants'
        ]
        read_only_fields = ['uuid', 'create', 'last_update']
    
    def get_responsible_merchants(self, obj):
        """Retourne les marchands responsables de cette agence"""
        merchants = obj.get_responsible_merchants()
        return [
            {
                'uuid': str(merchant.uuid),
                'username': merchant.user.username,
                'email': merchant.user.email
            }
            for merchant in merchants
        ]
    
    def validate_iata_code(self, value):
        """Valide le code IATA"""
        if value and len(value) != 3:
            raise serializers.ValidationError("Le code IATA doit contenir exactement 3 caractères")
        return value.upper() if value else value


class MerchantAgencySerializer(serializers.ModelSerializer):
    """Serializer pour les affectations marchand-agence"""
    
    merchant_username = serializers.CharField(source='merchant.user.username', read_only=True)
    merchant_email = serializers.CharField(source='merchant.user.email', read_only=True)
    agency_name = serializers.CharField(source='agency.name', read_only=True)
    agency_city = serializers.CharField(source='agency.city', read_only=True)
    
    class Meta:
        model = MerchantAgency
        fields = [
            'uuid', 'merchant', 'agency', 'role', 'is_responsible',
            'assigned_at', 'is_active', 'create', 'last_update',
            'create_by', 'update_by', 'merchant_username', 'merchant_email',
            'agency_name', 'agency_city'
        ]
        read_only_fields = ['uuid', 'assigned_at', 'create', 'last_update']
    
    def validate(self, data):
        """Validation des données d'affectation"""
        merchant = data.get('merchant')
        agency = data.get('agency')
        
        # Vérifier que le marchand et l'agence sont actifs
        if merchant and not merchant.user.is_active:
            raise serializers.ValidationError("Le marchand doit être actif")
        
        if agency and not agency.is_active:
            raise serializers.ValidationError("L'agence doit être active")
        
        return data


class FlightBookingSerializer(serializers.ModelSerializer):
    """Serializer pour les réservations de vol"""
    
    client_username = serializers.CharField(source='client.user.username', read_only=True)
    client_email = serializers.CharField(source='client.user.email', read_only=True)
    agency_name = serializers.CharField(source='agency.name', read_only=True)
    merchant_username = serializers.CharField(source='merchant.user.username', read_only=True)
    commission_amount = serializers.SerializerMethodField()
    total_with_commission = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    can_refund = serializers.SerializerMethodField()
    
    class Meta:
        model = FlightBooking
        fields = [
            'uuid', 'booking_reference', 'client', 'agency', 'merchant',
            'duffel_offer_id', 'duffel_booking_id', 'origin', 'destination',
            'departure_date', 'return_date', 'passenger_count', 'price',
            'currency', 'commission_rate', 'status', 'payment_status',
            'passenger_data', 'flight_data', 'create', 'last_update',
            'create_by', 'update_by', 'confirmed_at', 'paid_at', 
            'client_username', 'client_email', 'agency_name', 'merchant_username', 
            'commission_amount', 'total_with_commission', 'can_cancel', 'can_refund'
        ]
        read_only_fields = [
            'uuid', 'booking_reference', 'create', 'last_update',
            'confirmed_at', 'paid_at', 'duffel_booking_id'
        ]
    
    def get_commission_amount(self, obj):
        """Calcule le montant de la commission"""
        return obj.calculate_commission()
    
    def get_total_with_commission(self, obj):
        """Calcule le total avec commission"""
        return obj.get_total_with_commission()
    
    def get_can_cancel(self, obj):
        """Vérifie si la réservation peut être annulée"""
        return obj.is_cancellable()
    
    def get_can_refund(self, obj):
        """Vérifie si la réservation peut être remboursée"""
        return obj.is_refundable()
    
    def validate_passenger_count(self, value):
        """Valide le nombre de passagers"""
        if value < 1:
            raise serializers.ValidationError("Le nombre de passagers doit être supérieur à 0")
        if value > 9:
            raise serializers.ValidationError("Le nombre de passagers ne peut pas dépasser 9")
        return value
    
    def validate_price(self, value):
        """Valide le prix"""
        if value < 0:
            raise serializers.ValidationError("Le prix ne peut pas être négatif")
        return value
    
    def validate(self, data):
        """Validation des données de réservation"""
        # Vérifier que la date de départ est dans le futur
        departure_date = data.get('departure_date')
        if departure_date:
            from datetime import datetime
            if departure_date <= datetime.now():
                raise serializers.ValidationError("La date de départ doit être dans le futur")
        
        # Vérifier que la date de retour est après la date de départ
        return_date = data.get('return_date')
        if return_date and departure_date:
            if return_date <= departure_date:
                raise serializers.ValidationError("La date de retour doit être après la date de départ")
        
        return data


class FlightBookingCreateSerializer(serializers.Serializer):
    """Serializer pour la création de réservation via API Duffel"""
    
    duffel_offer_id = serializers.CharField(max_length=255)
    agency_uuid = serializers.UUIDField()
    passenger_data = serializers.JSONField(required=False, default=dict)
    
    def validate_agency_uuid(self, value):
        """Valide que l'agence existe et est active"""
        try:
            agency = TravelAgency.objects.get(uuid=value, is_active=True)
            return value
        except TravelAgency.DoesNotExist:
            raise serializers.ValidationError("Agence introuvable ou inactive")
    
    def validate_passenger_data(self, value):
        """Valide les données des passagers"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Les données des passagers doivent être un objet JSON")
        return value


class FlightSearchSerializer(serializers.Serializer):
    """Serializer pour la recherche de vols"""
    
    origin = serializers.CharField(max_length=10, help_text="Code IATA de l'aéroport de départ")
    destination = serializers.CharField(max_length=10, help_text="Code IATA de l'aéroport d'arrivée")
    departure_date = serializers.DateField(help_text="Date de départ (YYYY-MM-DD)")
    return_date = serializers.DateField(required=False, help_text="Date de retour (optionnel)")
    passengers = serializers.IntegerField(min_value=1, max_value=9, default=1)
    cabin_class = serializers.ChoiceField(
        choices=['economy', 'premium_economy', 'business', 'first'],
        default='economy'
    )
    
    def validate(self, data):
        """Validation des données de recherche"""
        from datetime import date
        
        departure_date = data.get('departure_date')
        return_date = data.get('return_date')
        
        # Vérifier que la date de départ est dans le futur
        if departure_date <= date.today():
            raise serializers.ValidationError("La date de départ doit être dans le futur")
        
        # Vérifier que la date de retour est après la date de départ
        if return_date and return_date <= departure_date:
            raise serializers.ValidationError("La date de retour doit être après la date de départ")
        
        return data
    
    def validate_origin(self, value):
        """Valide le code IATA d'origine"""
        return value.upper()
    
    def validate_destination(self, value):
        """Valide le code IATA de destination"""
        return value.upper()


class FlightOfferSerializer(serializers.Serializer):
    """Serializer pour les offres de vol (provenant de Duffel)"""
    
    id = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    departure_time = serializers.DateTimeField()
    arrival_time = serializers.DateTimeField()
    duration = serializers.CharField()
    stops = serializers.IntegerField()
    airline = serializers.CharField()
    aircraft = serializers.CharField()
    origin = serializers.CharField()
    destination = serializers.CharField()
    cabin_class = serializers.CharField()
    baggage_allowance = serializers.JSONField()
    cancellation_policy = serializers.JSONField()
    
    class Meta:
        # Ce serializer est read-only car il représente des données externes
        read_only_fields = '__all__'
