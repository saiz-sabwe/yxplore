#!/usr/bin/env python
"""
Script pour créer un utilisateur de test pour les connexions
"""
import os
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'YXPLORE_NODE.settings')
django.setup()

from django.contrib.auth.models import User
from ModuleProfils.models import ClientProfile, MerchantProfile

def create_test_users():
    """Crée des utilisateurs de test"""
    
    print("🔧 Création des utilisateurs de test...")
    
    # Utilisateur client : john@example.com
    email_john = "john@example.com"
    if not User.objects.filter(email=email_john).exists():
        user_john = User.objects.create_user(
            username="john",
            email=email_john,
            password="password123",
            first_name="John",
            last_name="Doe"
        )
        
        # Créer le profil client
        ClientProfile.create_from_user_data(
            user=user_john,
            first_name="John",
            last_name="Doe",
            phone="+33123456789"
        )
        
        print(f"✅ Client créé : {email_john} / password123")
    else:
        print(f"ℹ️  Client existe déjà : {email_john}")
    
    # Utilisateur marchand : merchant@example.com
    email_merchant = "merchant@example.com"
    if not User.objects.filter(email=email_merchant).exists():
        user_merchant = User.objects.create_user(
            username="merchant",
            email=email_merchant,
            password="password123",
            first_name="Travel",
            last_name="Corp"
        )
        
        # Créer le profil marchand
        MerchantProfile.create_from_registration_data(
            user=user_merchant,
            company_name="Travel Corp Agency",
            business_type=MerchantProfile.BUSINESS_TRAVEL_AGENCY,
            contact_phone="+33987654321"
        )
        
        print(f"✅ Marchand créé : {email_merchant} / password123")
    else:
        print(f"ℹ️  Marchand existe déjà : {email_merchant}")

def list_users():
    """Liste tous les utilisateurs"""
    print("\n📋 Liste des utilisateurs :")
    print("-" * 50)
    
    for user in User.objects.all():
        profile_type = "Aucun profil"
        if hasattr(user, 'clientprofile_profile'):
            profile_type = "Client"
        elif hasattr(user, 'merchantprofile_profile'):
            profile_type = "Marchand"
        elif hasattr(user, 'adminprofile_profile'):
            profile_type = "Admin"
            
        print(f"Username: {user.username:15} | Email: {user.email:25} | Type: {profile_type}")

def test_authentication():
    """Teste l'authentification"""
    from django.contrib.auth import authenticate
    
    print("\n🔐 Test d'authentification :")
    print("-" * 50)
    
    test_cases = [
        ("john", "password123"),
        ("john@example.com", "password123"),
        ("merchant", "password123"),
        ("merchant@example.com", "password123"),
        ("john@example.com", "wrongpassword"),
    ]
    
    for username, password in test_cases:
        user = authenticate(username=username, password=password)
        if user:
            print(f"✅ {username:25} -> Authentification réussie")
        else:
            # Test avec email
            if '@' in username:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                    if user:
                        print(f"✅ {username:25} -> Authentification réussie (via email)")
                    else:
                        print(f"❌ {username:25} -> Mot de passe incorrect")
                except User.DoesNotExist:
                    print(f"❌ {username:25} -> Utilisateur non trouvé")
            else:
                print(f"❌ {username:25} -> Authentification échouée")

if __name__ == "__main__":
    print("🚀 YXPLORE - Test des utilisateurs")
    print("=" * 50)
    
    create_test_users()
    list_users()
    test_authentication()
    
    print("\n✅ Script terminé !")
    print("💡 Vous pouvez maintenant tester la connexion avec :")
    print("   📧 Email: john@example.com")
    print("   🔑 Password: password123")
    print("   ou")
    print("   📧 Email: merchant@example.com") 
    print("   🔑 Password: password123")
