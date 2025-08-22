# ModuleProfils/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import UserProfileManager, ProfileUtils

def role_required(allowed_roles):
    """
    Décorateur pour vérifier que l'utilisateur a un rôle spécifique
    
    Usage:
    @role_required(['client'])
    @role_required(['merchant', 'admin'])
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            user_role = get_user_role(user)
            
            if user_role not in allowed_roles:
                if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                    return JsonResponse({
                        'resultat': 'FAIL',
                        'message': 'Accès non autorisé pour ce rôle.'
                    }, status=403)
                else:
                    return redirect(reverse('profils:index'))
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def client_required(view_func):
    """Décorateur pour les vues accessibles uniquement aux clients"""
    return role_required(['client'])(view_func)

def merchant_required(view_func):
    """Décorateur pour les vues accessibles uniquement aux marchands"""
    return role_required(['merchant'])(view_func)

def admin_required(view_func):
    """Décorateur pour les vues accessibles uniquement aux admins"""
    return role_required(['admin'])(view_func)

def kyc_approved_required(view_func):
    """Décorateur pour vérifier que le KYC est approuvé"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        profile = get_user_profile(user)
        
        if not profile:
            return redirect(reverse('profils:index'))
            
        # Vérifier le statut KYC selon le type de profil
        if UserProfileManager.user_has_kyc_features(user):
            kyc_status = UserProfileManager.get_user_kyc_status(user)
            if kyc_status == 0:  # KYC_PENDING
                if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                    return JsonResponse({
                        'resultat': 'FAIL',
                        'message': 'Votre compte doit être vérifié (KYC) pour accéder à cette fonctionnalité.'
                    }, status=403)
                else:
                    return redirect(reverse('profils:kyc_pending'))
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def get_user_role(user):
    """Obtenir le rôle de l'utilisateur"""
    if not user.is_authenticated:
        return None
    
    user_type = UserProfileManager.determine_user_type(user)
    return user_type if user_type else 'unknown'

def get_user_profile(user):
    """Obtenir le profil de l'utilisateur"""
    if not user.is_authenticated:
        return None
    
    return UserProfileManager.get_primary_profile(user)
