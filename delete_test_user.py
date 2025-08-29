import os
import django
from django.db import transaction

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'YXPLORE_NODE.settings')
django.setup()

from django.contrib.auth.models import User
from ModuleProfils.models import ClientProfile, MerchantProfile
from ModuleFlight.models import TravelAgency, MerchantAgency


def delete_test_users():
    with transaction.atomic():
        # Supprimer l'affectation marchand-agence
        merchant_user = User.objects.filter(username='testmerchant').first()
        agency = TravelAgency.objects.filter(name='Agence Congo Tours').first()
        if merchant_user and agency:
            merchant_profile = MerchantProfile.objects.filter(user=merchant_user).first()
            assignments = MerchantAgency.objects.filter(merchant=merchant_profile, agency=agency)
            count = assignments.count()
            assignments.delete()
            print(f"Affectations Marchand-Agence supprimées : {count}")
        # Supprimer l'agence de voyage
        if agency:
            agency.delete()
            print("Agence de voyage supprimée.")
        # Supprimer le profil et l'utilisateur marchand
        if merchant_user:
            MerchantProfile.objects.filter(user=merchant_user).delete()
            merchant_user.delete()
            print("Marchand supprimé.")
        # Supprimer le profil et l'utilisateur client
        client_user = User.objects.filter(username='testclient').first()
        if client_user:
            ClientProfile.objects.filter(user=client_user).delete()
            client_user.delete()
            print("Client supprimé.")
        print("Suppression terminée.")

if __name__ == "__main__":
    delete_test_users()

