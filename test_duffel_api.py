#!/usr/bin/env python3
"""
Script de test pour l'API Duffel
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'YXPLORE_NODE.settings')
django.setup()

from ModuleFlight.duffel_service import DuffelService

def test_get_offer_details():
    """Test de récupération des détails d'une offre"""
    try:
        duffel_service = DuffelService()
        
        # Test avec l'ID d'offre fourni
        offer_id = "off_0000AxePR1Bp3LJq0ToDYL"
        
        print(f"🔍 Test de récupération des détails de l'offre: {offer_id}")
        
        # Récupérer les détails
        offer_details = duffel_service.get_offer_details(offer_id)
        
        if offer_details:
            print("✅ Détails récupérés avec succès!")
            print(f"   Compagnie: {offer_details.get('owner', {}).get('name', 'N/A')}")
            print(f"   Prix: {offer_details.get('total_amount', 'N/A')} {offer_details.get('total_currency', 'N/A')}")
            print(f"   Emissions: {offer_details.get('total_emissions_kg', 'N/A')} kg CO₂")
            
            # Formater pour le frontend
            formatted_offer = duffel_service.format_offer_for_frontend(offer_details)
            
            if formatted_offer:
                print("✅ Formatage frontend réussi!")
                print(f"   Slices: {len(formatted_offer.get('slices', []))}")
                print(f"   Passagers: {len(formatted_offer.get('passengers', []))}")
            else:
                print("❌ Erreur lors du formatage frontend")
        else:
            print("❌ Impossible de récupérer les détails de l'offre")
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Test de l'API Duffel")
    print("=" * 50)
    
    test_get_offer_details()
    
    print("\n" + "=" * 50)
    print("🏁 Test terminé")
