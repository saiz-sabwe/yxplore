#!/usr/bin/env python
"""
Script pour créer un utilisateur de test pour les connexions
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'YXPLORE_NODE.settings')
django.setup()

from django.contrib.auth.models import User
from ModuleProfils.models import ClientProfile, MerchantProfile
from ModuleFlight.models import TravelAgency, MerchantAgency

def create_rdc_users_and_profiles():
    password = '12345678@'
    # --- Création du client ---
    client_username = 'rdcclient'
    client_email = 'rdcclient@rdc.cd'
    client_first_name = 'Jean-Pierre'
    client_last_name = 'Kabasele'
    User.objects.filter(username=client_username).delete()
    client_user = User.objects.create_user(
        username=client_username,
        email=client_email,
        password=password,
        first_name=client_first_name,
        last_name=client_last_name
    )
    print(f"✅ Utilisateur client créé : {client_username} / {client_email}")
    ClientProfile.objects.filter(user=client_user).delete()
    client_profile = ClientProfile.objects.create(
        user=client_user,
        nom=client_last_name,
        prenom=client_first_name,
        phone='+243810000001',
        address='10, Avenue du Fleuve, Gombe, Kinshasa',
        birth_date='1992-05-15',
        nationality='Congolaise',
    )
    print(f"✅ Profil client RDC créé pour {client_username}")

    # --- Création du marchand ---
    merchant_username = 'rdcmerchant'
    merchant_email = 'rdcmerchant@rdc.cd'
    merchant_first_name = 'Chantal'
    merchant_last_name = 'Mwamba'
    User.objects.filter(username=merchant_username).delete()
    merchant_user = User.objects.create_user(
        username=merchant_username,
        email=merchant_email,
        password=password,
        first_name=merchant_first_name,
        last_name=merchant_last_name
    )
    print(f"✅ Utilisateur marchand créé : {merchant_username} / {merchant_email}")
    MerchantProfile.objects.filter(user=merchant_user).delete()
    merchant_profile = MerchantProfile.objects.create(
        user=merchant_user,
        company_name='RDC Travel SARL',
        company_registration='RCCM/CD/KIN/123.456',
        tax_id='CD123456789',
        contact_person=f'{merchant_first_name} {merchant_last_name}',
        contact_phone='+243820000002',
        contact_email=merchant_email,
        company_address='15, Boulevard du 30 Juin, Gombe, Kinshasa',
        company_city='Kinshasa',
        company_country='RDC',
        company_postal_code='',
        business_type=MerchantProfile.BUSINESS_TRAVEL_AGENCY,
        is_verified=True,
        commission_rate=7.5,
    )
    print(f"✅ Profil marchand RDC créé pour {merchant_username}")

    # --- Création d'un établissement (agence de voyage) RDC ---
    agency_name = "Etablissement RDC Voyage"
    TravelAgency.objects.filter(name=agency_name).delete()
    agency = TravelAgency.objects.create(
        name=agency_name,
        country='RDC',
        city='Kinshasa',
        address='25, Avenue Lumumba, Kinshasa',
        iata_code='KIN',
        phone='+243990000003',
        email='contact@rdcvoyage.cd',
        is_active=True,
        create_by=merchant_user
    )
    print(f"✅ Etablissement (agence) RDC créé : {agency_name}")

    # --- Affectation du marchand à l'établissement ---
    MerchantAgency.objects.filter(merchant=merchant_profile, agency=agency).delete()
    assignment = MerchantAgency.assign_merchant_to_agency(
        merchant=merchant_profile,
        agency=agency,
        role=MerchantAgency.ROLE_MANAGER,
        is_responsible=True,
        created_by=merchant_user
    )
    print(f"✅ Affectation du marchand à l'établissement : {assignment}")

    print("\n🎉 Tous les objets RDC ont été créés avec succès !")
    print(f"\nIdentifiants de connexion client :\n  Utilisateur : {client_username}\n  Email : {client_email}\n  Mot de passe : {password}")
    print(f"\nIdentifiants de connexion marchand :\n  Utilisateur : {merchant_username}\n  Email : {merchant_email}\n  Mot de passe : {password}")

if __name__ == "__main__":
    print("Création d'un client, d'un marchand et d'un établissement RDC...")
    create_rdc_users_and_profiles()
    print("Terminé.")
