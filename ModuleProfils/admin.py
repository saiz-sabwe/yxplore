from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import ClientProfile, MerchantProfile, AdminProfile, KYCValidation

# Inline pour les profils
class ClientProfileInline(admin.StackedInline):
    model = ClientProfile
    can_delete = False
    verbose_name_plural = 'Profil Client'
    fk_name = 'user'

class MerchantProfileInline(admin.StackedInline):
    model = MerchantProfile
    can_delete = False
    verbose_name_plural = 'Profil Marchand'
    fk_name = 'user'

class AdminProfileInline(admin.StackedInline):
    model = AdminProfile
    can_delete = False
    verbose_name_plural = 'Profil Administrateur'
    fk_name = 'user'

# Admin personnalisé pour User
class UserAdmin(BaseUserAdmin):
    inlines = (ClientProfileInline, MerchantProfileInline, AdminProfileInline)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

# Admin pour ClientProfile
@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'nom', 'prenom', 'phone', 'kyc_status', 'is_active', 'create']
    list_filter = ['kyc_status', 'is_active', 'preferred_language', 'create']
    search_fields = ['user__username', 'user__email', 'nom', 'prenom', 'phone']
    readonly_fields = ['create', 'last_update', 'create_by', 'update_by']
    
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user', 'is_active')
        }),
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'phone', 'address', 'birth_date', 'nationality')
        }),
        ('KYC', {
            'fields': ('kyc_status', 'id_document')
        }),
        ('Préférences', {
            'fields': ('preferred_language',)
        }),
        ('Métadonnées', {
            'fields': ('create', 'last_update', 'create_by', 'update_by'),
            'classes': ('collapse',)
        }),
    )

# Admin pour MerchantProfile
@admin.register(MerchantProfile)
class MerchantProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'business_type', 'kyc_status', 'is_verified', 'is_active', 'create']
    list_filter = ['kyc_status', 'is_verified', 'business_type', 'is_active', 'create']
    search_fields = ['user__username', 'company_name', 'contact_person', 'contact_email']
    readonly_fields = ['create', 'last_update', 'create_by', 'update_by']
    
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user', 'is_active')
        }),
        ('Informations entreprise', {
            'fields': ('company_name', 'company_registration', 'tax_id', 'business_type')
        }),
        ('Contact', {
            'fields': ('contact_person', 'contact_phone', 'contact_email')
        }),
        ('Adresse', {
            'fields': ('company_address', 'company_city', 'company_country', 'company_postal_code')
        }),
        ('KYC', {
            'fields': ('kyc_status', 'business_license', 'tax_certificate', 'company_registration_doc')
        }),
        ('Statut commercial', {
            'fields': ('is_verified', 'commission_rate')
        }),
        ('Métadonnées', {
            'fields': ('create', 'last_update', 'create_by', 'update_by'),
            'classes': ('collapse',)
        }),
    )

# Admin pour AdminProfile
@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'admin_level', 'department', 'is_active', 'create']
    list_filter = ['admin_level', 'department', 'is_active', 'create']
    search_fields = ['user__username', 'department']
    readonly_fields = ['create', 'last_update', 'create_by', 'update_by']
    
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user', 'is_active')
        }),
        ('Niveau d\'administration', {
            'fields': ('admin_level', 'department')
        }),
        ('Permissions', {
            'fields': ('can_manage_users', 'can_manage_merchants', 'can_validate_kyc', 
                      'can_access_financial_data', 'can_manage_system')
        }),
        ('Contact admin', {
            'fields': ('admin_phone', 'admin_extension')
        }),
        ('Métadonnées', {
            'fields': ('create', 'last_update', 'create_by', 'update_by'),
            'classes': ('collapse',)
        }),
    )

# Admin pour KYCValidation
@admin.register(KYCValidation)
class KYCValidationAdmin(admin.ModelAdmin):
    list_display = ['profile_type', 'profile_id', 'kyc_level', 'status', 'validated_by', 'validated_at']
    list_filter = ['profile_type', 'kyc_level', 'status', 'validated_at']
    search_fields = ['profile_type', 'validated_by__username']
    readonly_fields = ['validated_at']
    
    fieldsets = (
        ('Informations de validation', {
            'fields': ('profile_type', 'profile_id', 'kyc_level', 'status')
        }),
        ('Validation', {
            'fields': ('validated_by', 'validated_at', 'notes')
        }),
    )

# Désenregistrer l'admin User par défaut et enregistrer le nôtre
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

