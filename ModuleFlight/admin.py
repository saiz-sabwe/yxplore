from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import TravelAgency, MerchantAgency, FlightBooking, Passenger, FlightBookingDetail


@admin.register(TravelAgency)
class TravelAgencyAdmin(admin.ModelAdmin):
    """Administration des agences de voyage"""
    
    list_display = [
        'name', 'city', 'country', 'iata_code', 
        'responsible_merchants_count', 'bookings_count', 'is_active', 'create'
    ]
    list_filter = ['is_active', 'country', 'create', 'create_by']
    search_fields = ['name', 'city', 'country', 'iata_code', 'email']
    ordering = ['name']
    readonly_fields = ['id', 'uuid', 'create', 'last_update']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'iata_code', 'is_active')
        }),
        ('Localisation', {
            'fields': ('country', 'city', 'address')
        }),
        ('Contact', {
            'fields': ('phone', 'email')
        }),
        ('Métadonnées', {
            'fields': ('id', 'uuid', 'create', 'last_update', 'create_by', 'update_by'),
            'classes': ['collapse']
        }),
    )
    
    def responsible_merchants_count(self, obj):
        """Compte le nombre de marchands responsables"""
        count = obj.get_responsible_merchants().count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return format_html(
            '<span style="color: red;">Aucun</span>'
        )
    responsible_merchants_count.short_description = "Marchands responsables"
    
    def bookings_count(self, obj):
        """Compte le nombre de réservations"""
        count = FlightBooking.objects.filter(agency=obj).count()
        if count > 0:
            url = reverse('admin:ModuleFlight_flightbooking_changelist') + f'?agency__id__exact={obj.id}'
            return format_html(
                '<a href="{}" style="color: blue; font-weight: bold;">{} réservations</a>',
                url, count
            )
        return "Aucune"
    bookings_count.short_description = "Réservations"
    
    actions = ['activate_agencies', 'deactivate_agencies']
    
    def activate_agencies(self, request, queryset):
        """Action pour activer les agences sélectionnées"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} agence(s) activée(s) avec succès.")
    activate_agencies.short_description = "Activer les agences sélectionnées"
    
    def deactivate_agencies(self, request, queryset):
        """Action pour désactiver les agences sélectionnées"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} agence(s) désactivée(s) avec succès.")
    deactivate_agencies.short_description = "Désactiver les agences sélectionnées"


@admin.register(MerchantAgency)
class MerchantAgencyAdmin(admin.ModelAdmin):
    """Administration des affectations marchand-agence"""
    
    list_display = [
        'merchant_name', 'agency_name', 'role', 'is_responsible', 
        'is_active', 'create'
    ]
    list_filter = ['role', 'is_responsible', 'is_active', 'create', 'create_by']
    search_fields = [
        'merchant__user__username', 'merchant__user__email',
        'agency__name', 'agency__city'
    ]
    ordering = ['-create']
    readonly_fields = ['id', 'uuid', 'assigned_at', 'create', 'last_update']
    
    fieldsets = (
        ('Affectation', {
            'fields': ('merchant', 'agency', 'role', 'is_responsible', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('id', 'uuid', 'assigned_at', 'create', 'last_update', 'create_by', 'update_by'),
            'classes': ['collapse']
        }),
    )
    
    def merchant_name(self, obj):
        """Nom du marchand"""
        return f"{obj.merchant.user.username} ({obj.merchant.user.email})"
    merchant_name.short_description = "Marchand"
    
    def agency_name(self, obj):
        """Nom de l'agence"""
        return f"{obj.agency.name} - {obj.agency.city}"
    agency_name.short_description = "Agence"
    
    actions = ['activate_assignments', 'deactivate_assignments', 'make_responsible']
    
    def activate_assignments(self, request, queryset):
        """Action pour activer les affectations"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} affectation(s) activée(s).")
    activate_assignments.short_description = "Activer les affectations"
    
    def deactivate_assignments(self, request, queryset):
        """Action pour désactiver les affectations"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} affectation(s) désactivée(s).")
    deactivate_assignments.short_description = "Désactiver les affectations"
    
    def make_responsible(self, request, queryset):
        """Action pour rendre responsable"""
        count = queryset.update(is_responsible=True)
        self.message_user(request, f"{count} marchand(s) rendu(s) responsable(s).")
    make_responsible.short_description = "Rendre responsable"


@admin.register(FlightBooking)
class FlightBookingAdmin(admin.ModelAdmin):
    """Administration des réservations de vol"""
    
    list_display = [
        'booking_reference', 'client_name', 'agency_name', 
        'origin_destination', 'departure_date', 'price_display',
        'status_display', 'payment_status_display', 'duffel_mode_display', 'create'
    ]
    list_filter = [
        'status', 'payment_status', 'currency', 'create', 'duffel_live_mode',
        'departure_date', 'agency', 'merchant', 'create_by'
    ]
    search_fields = [
        'booking_reference', 'client__user__username', 'client__user__email',
        'agency__name', 'origin', 'destination', 'duffel_offer_id', 
        'duffel_order_id', 'duffel_offer_request_id'
    ]
    ordering = ['-create']
    readonly_fields = [
        'id', 'uuid', 'booking_reference', 'create', 'last_update',
        'confirmed_at', 'paid_at', 'commission_amount', 'total_with_commission',
        'formatted_passenger_data', 'formatted_flight_data'
    ]
    
    fieldsets = (
        ('Informations générales', {
            'fields': (
                'booking_reference', 'status', 'payment_status',
                'client', 'agency', 'merchant'
            )
        }),
        ('Détails du vol', {
            'fields': (
                'origin', 'destination', 'departure_date', 'return_date',
                'passenger_count'
            )
        }),
        ('Informations Duffel API v2', {
            'fields': (
                'duffel_offer_id', 'duffel_order_id', 'duffel_offer_request_id',
                'duffel_live_mode', 'duffel_expires_at', 'duffel_payment_intent_id'
            ),
            'classes': ['collapse']
        }),
        ('Informations financières', {
            'fields': (
                'price', 'currency', 'commission_rate',
                'commission_amount', 'total_with_commission'
            )
        }),
        ('Données passagers', {
            'fields': ('formatted_passenger_data',),
            'classes': ['collapse']
        }),
        ('Données de vol', {
            'fields': ('formatted_flight_data',),
            'classes': ['collapse']
        }),
        ('Métadonnées', {
            'fields': (
                'id', 'uuid', 'create', 'last_update', 'create_by', 'update_by',
                'confirmed_at', 'paid_at'
            ),
            'classes': ['collapse']
        }),
    )
    
    def client_name(self, obj):
        """Nom du client"""
        return f"{obj.client.user.username} ({obj.client.user.email})"
    client_name.short_description = "Client"
    
    def agency_name(self, obj):
        """Nom de l'agence"""
        return f"{obj.agency.name} - {obj.agency.city}"
    agency_name.short_description = "Agence"
    
    def origin_destination(self, obj):
        """Origine et destination"""
        return f"{obj.origin} → {obj.destination}"
    origin_destination.short_description = "Trajet"
    
    def price_display(self, obj):
        """Affichage du prix avec devise"""
        return f"{obj.price} {obj.currency}"
    price_display.short_description = "Prix"
    
    def duffel_mode_display(self, obj):
        """Affiche le mode Duffel"""
        if obj.duffel_live_mode:
            return format_html('<span style="color: red; font-weight: bold;">LIVE</span>')
        else:
            return format_html('<span style="color: orange; font-weight: bold;">TEST</span>')
    duffel_mode_display.short_description = "Mode Duffel"
    
    def status_display(self, obj):
        """Affichage coloré du statut"""
        colors = {
            FlightBooking.STATUS_PENDING: 'orange',
            FlightBooking.STATUS_CONFIRMED: 'green',
            FlightBooking.STATUS_CANCELLED: 'red',
            FlightBooking.STATUS_EXPIRED: 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = "Statut"
    
    def payment_status_display(self, obj):
        """Affichage coloré du statut de paiement"""
        colors = {
            'UNPAID': 'red',
            'PAID': 'green',
            'REFUNDED': 'blue',
            'FAILED': 'darkred'
        }
        color = colors.get(obj.payment_status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_display.short_description = "Paiement"
    
    def commission_amount(self, obj):
        """Montant de la commission"""
        return f"{obj.calculate_commission()} {obj.currency}"
    commission_amount.short_description = "Commission"
    
    def total_with_commission(self, obj):
        """Total avec commission"""
        return f"{obj.get_total_with_commission()} {obj.currency}"
    total_with_commission.short_description = "Total TTC"
    
    def formatted_passenger_data(self, obj):
        """Données des passagers formatées"""
        if obj.passenger_data:
            formatted = json.dumps(obj.passenger_data, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted)
        return "Aucune donnée"
    formatted_passenger_data.short_description = "Données passagers"
    
    def formatted_flight_data(self, obj):
        """Données de vol formatées"""
        if obj.flight_data:
            formatted = json.dumps(obj.flight_data, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted[:1000] + '...' if len(formatted) > 1000 else formatted)
        return "Aucune donnée"
    formatted_flight_data.short_description = "Données de vol"
    
    actions = ['mark_as_confirmed', 'mark_as_paid', 'cancel_bookings']
    
    def mark_as_confirmed(self, request, queryset):
        """Action pour confirmer les réservations"""
        count = 0
        for booking in queryset:
            if booking.status == FlightBooking.STATUS_PENDING:
                booking.confirm_booking()
                count += 1
        self.message_user(request, f"{count} réservation(s) confirmée(s).")
    mark_as_confirmed.short_description = "Confirmer les réservations"
    
    def mark_as_paid(self, request, queryset):
        """Action pour marquer comme payé"""
        count = 0
        for booking in queryset:
            if booking.payment_status == 'UNPAID':
                try:
                    booking.mark_paid()
                    count += 1
                except:
                    pass
        self.message_user(request, f"{count} réservation(s) marquée(s) comme payée(s).")
    mark_as_paid.short_description = "Marquer comme payé"
    
    def cancel_bookings(self, request, queryset):
        """Action pour annuler les réservations"""
        count = 0
        for booking in queryset:
            if booking.is_cancellable():
                try:
                    booking.cancel_booking()
                    count += 1
                except:
                    pass
        self.message_user(request, f"{count} réservation(s) annulée(s).")
    cancel_bookings.short_description = "Annuler les réservations"


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    """Administration des passagers"""
    
    list_display = [
        'full_name', 'type_display', 'booking_reference', 'agency_name',
        'gender', 'date_of_birth', 'nationality', 'is_active', 'create'
    ]
    list_filter = [
        'type', 'gender', 'nationality', 'is_active', 'create', 'create_by'
    ]
    search_fields = [
        'given_name', 'family_name', 'booking__booking_reference',
        'booking__agency__name', 'nationality'
    ]
    ordering = ['-create']
    readonly_fields = ['id', 'uuid', 'create', 'last_update']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': (
                'type', 'title', 'given_name', 'family_name', 'gender',
                'date_of_birth', 'nationality', 'country_code'
            )
        }),
        ('Contact', {
            'fields': ('email', 'phone')
        }),
        ('Réservation', {
            'fields': ('booking',)
        }),
        ('Informations Duffel', {
            'fields': (
                'duffel_passenger_id', 'duffel_identity_document_id'
            ),
            'classes': ['collapse']
        }),
        ('Métadonnées', {
            'fields': (
                'id', 'uuid', 'is_active', 'create', 'last_update', 'create_by', 'update_by'
            ),
            'classes': ['collapse']
        }),
    )
    
    def full_name(self, obj):
        """Nom complet du passager"""
        return f"{obj.title} {obj.given_name} {obj.family_name}"
    full_name.short_description = "Nom complet"
    
    def type_display(self, obj):
        """Type de passager avec icône"""
        icons = {
            'adult': '👤',
            'child': '👶',
            'infant': '🍼'
        }
        icon = icons.get(obj.type, '👤')
        return f"{icon} {obj.get_type_display()}"
    type_display.short_description = "Type"
    
    def booking_reference(self, obj):
        """Référence de la réservation"""
        if obj.booking:
            url = reverse('admin:ModuleFlight_flightbooking_change', args=[obj.booking.id])
            return format_html(
                '<a href="{}">{}</a>',
                url, obj.booking.booking_reference
            )
        return "N/A"
    booking_reference.short_description = "Réservation"
    
    def agency_name(self, obj):
        """Nom de l'agence"""
        if obj.booking and obj.booking.agency:
            return obj.booking.agency.name
        return "N/A"
    agency_name.short_description = "Agence"
    
    actions = ['activate_passengers', 'deactivate_passengers']
    
    def activate_passengers(self, request, queryset):
        """Action pour activer les passagers"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} passager(s) activé(s).")
    activate_passengers.short_description = "Activer les passagers"
    
    def deactivate_passengers(self, request, queryset):
        """Action pour désactiver les passagers"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} passager(s) désactivé(s).")
    deactivate_passengers.short_description = "Désactiver les passagers"


@admin.register(FlightBookingDetail)
class FlightBookingDetailAdmin(admin.ModelAdmin):
    """Administration des détails de réservation"""
    
    list_display = [
        'booking_reference', 'agency_name', 'origin_destination',
        'departure_date', 'return_date', 'cabin_class', 'is_active', 'create'
    ]
    list_filter = [
        'cabin_class', 'is_active', 'create', 'create_by'
    ]
    search_fields = [
        'booking__booking_reference', 'booking__agency__name',
        'origin', 'destination', 'fare_brand_name'
    ]
    ordering = ['-create']
    readonly_fields = [
        'id', 'uuid', 'create', 'last_update', 'formatted_duffel_data'
    ]
    
    fieldsets = (
        ('Réservation', {
            'fields': ('booking',)
        }),
        ('Informations de vol', {
            'fields': (
                'origin', 'destination', 'departure_date', 'return_date',
                'fare_brand_name', 'cabin_class'
            )
        }),
        ('Données Duffel', {
            'fields': ('formatted_duffel_data',),
            'classes': ['collapse']
        }),
        ('Métadonnées', {
            'fields': (
                'id', 'uuid', 'is_active', 'create', 'last_update', 'create_by', 'update_by'
            ),
            'classes': ['collapse']
        }),
    )
    
    def booking_reference(self, obj):
        """Référence de la réservation"""
        if obj.booking:
            url = reverse('admin:ModuleFlight_flightbooking_change', args=[obj.booking.id])
            return format_html(
                '<a href="{}">{}</a>',
                url, obj.booking.booking_reference
            )
        return "N/A"
    booking_reference.short_description = "Réservation"
    
    def agency_name(self, obj):
        """Nom de l'agence"""
        if obj.booking and obj.booking.agency:
            return obj.booking.agency.name
        return "N/A"
    agency_name.short_description = "Agence"
    
    def origin_destination(self, obj):
        """Origine et destination"""
        if obj.origin and obj.destination:
            return f"{obj.origin} → {obj.destination}"
        return "N/A"
    origin_destination.short_description = "Trajet"
    
    def formatted_duffel_data(self, obj):
        """Données Duffel formatées"""
        if obj.duffel_data:
            formatted = json.dumps(obj.duffel_data, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted)
        return "Aucune donnée"
    formatted_duffel_data.short_description = "Données Duffel"
    
    actions = ['activate_details', 'deactivate_details']
    
    def activate_details(self, request, queryset):
        """Action pour activer les détails"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} détail(s) activé(s).")
    activate_details.short_description = "Activer les détails"
    
    def deactivate_details(self, request, queryset):
        """Action pour désactiver les détails"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} détail(s) désactivé(s).")
    deactivate_details.short_description = "Désactiver les détails"


# Configuration de l'interface d'administration
admin.site.site_header = "YXPLORE - Module Flight"
admin.site.site_title = "Administration Flight"
admin.site.index_title = "Gestion des vols et réservations"