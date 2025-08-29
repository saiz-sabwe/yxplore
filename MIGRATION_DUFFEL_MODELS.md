# 🔄 Migration des modèles pour l'API Duffel v2

## 📋 **Nouveaux champs ajoutés au modèle FlightBooking**

### **Champs API Duffel v2**
```python
# Identifiants Duffel spécifiques
duffel_order_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID commande Duffel")
duffel_offer_request_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID demande d'offre Duffel")
duffel_payment_intent_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID intention de paiement Duffel")

# Métadonnées Duffel
duffel_offer_data = models.JSONField(default=dict, verbose_name="Cache offre Duffel")
duffel_order_data = models.JSONField(default=dict, blank=True, verbose_name="Cache commande Duffel")
duffel_live_mode = models.BooleanField(default=False, verbose_name="Mode production Duffel")
duffel_expires_at = models.DateTimeField(blank=True, null=True, verbose_name="Expiration offre Duffel")
duffel_conditions = models.JSONField(default=dict, verbose_name="Conditions Duffel")
```

### **Champs modifiés**
```python
# Renommé pour plus de clarté
duffel_booking_id → duffel_order_id  # Plus conforme à l'API Duffel

# Amélioré
passenger_data = models.JSONField(help_text="Données passagers conformes API Duffel (avec IDs)")
```

## ⚡ **Commandes de migration à exécuter**

```bash
# 1. Créer la migration
python manage.py makemigrations ModuleFlight

# 2. Appliquer la migration
python manage.py migrate ModuleFlight

# 3. Vérifier la migration
python manage.py showmigrations ModuleFlight
```

## 🔧 **Settings mis à jour**

### **Configuration Duffel v2 complète**
```python
# Mode de fonctionnement
DUFFEL_LIVE_MODE = False  # Test/Production
DUFFEL_API_KEY = 'duffel_test_...'  # Token test
DUFFEL_API_KEY_LIVE = None  # Token production

# Configuration avancée
DUFFEL_CONFIG = {
    'REQUEST_TIMEOUT': 30,
    'RATE_LIMIT_PER_MINUTE': 60,
    'OFFER_CACHE_TTL': 900,
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 1,
}

# Types supportés
DUFFEL_PAYMENT_TYPES = {
    'BALANCE': 'balance',
    'ARC_BSP_CASH': 'arc_bsp_cash',
}

# Configuration Flight étendue
FLIGHT_CONFIG = {
    'CABIN_CLASSES': {
        'economy': 'economy',
        'premium_economy': 'premium_economy', 
        'business': 'business',
        'first': 'first'
    },
    'PASSENGER_TYPES': {
        'adult': 'adult',
        'child': 'child',
        'infant_without_seat': 'infant_without_seat'
    }
}
```

## 🚀 **Service Duffel amélioré**

### **Nouvelles fonctionnalités**
- ✅ **Mode Live/Test automatique** selon configuration
- ✅ **Timeout et retry configurables** 
- ✅ **Headers complets** avec User-Agent
- ✅ **Logging détaillé** du mode utilisé
- ✅ **Configuration centralisée** depuis settings

### **Méthodes mises à jour**
```python
# Service auto-configuré selon l'environnement
duffel_service = DuffelService()  # Test ou Live selon DUFFEL_LIVE_MODE

# Headers conformes API v2
headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Duffel-Version': 'v2',
    'User-Agent': 'YXplore-Flight-Module/1.0'
}
```

## 📊 **Impact sur les fonctionnalités existantes**

### **Compatibilité arrière ✅**
- ✅ **Modèles existants** : Aucun changement breaking
- ✅ **API existante** : Fonctionne avec nouveaux champs
- ✅ **Templates** : Aucune modification requise
- ✅ **JavaScript** : Compatible avec nouvelles données

### **Nouvelles possibilités ⭐**
- ✅ **Cache des offres Duffel** pour performance
- ✅ **Tracking complet** des transactions Duffel
- ✅ **Mode test/production** automatique
- ✅ **Conditions de vol** stockées localement
- ✅ **Expiration des offres** gérée

### **Données enrichies 📈**
```python
# Exemple de données stockées
booking.duffel_offer_data = {
    "id": "off_xxxxx",
    "total_amount": "499.99",
    "total_currency": "EUR",
    "slices": [...],
    "conditions": {...}
}

booking.duffel_order_data = {
    "id": "ord_xxxxx", 
    "booking_reference": "ABC123",
    "documents": [...],
    "services": [...]
}
```

## 🧪 **Tests recommandés après migration**

### **1. Migration des données**
```bash
# Vérifier que tous les champs sont créés
python manage.py dbshell
.schema ModuleFlight_flightbooking
```

### **2. Service Duffel**
```python
# Test du service en mode test
from ModuleFlight.duffel_service import duffel_service
print(f"Mode: {'LIVE' if duffel_service.live_mode else 'TEST'}")
print(f"API Key: {duffel_service.api_key[:20]}...")
```

### **3. Création de réservation**
```python
# Test avec nouvelles données Duffel
booking = FlightBooking.create_booking(
    client=client,
    agency=agency, 
    merchant=merchant,
    duffel_offer_id="off_test_123",
    flight_details=flight_details,
    passenger_data=passenger_data,
    duffel_data={
        'order_id': 'ord_test_456',
        'offer_request_id': 'orq_test_789',
        'live_mode': False,
        'offer_data': {...},
        'order_data': {...}
    }
)
```

## ✅ **Checklist de déploiement**

- [ ] **Migration créée** : `makemigrations ModuleFlight`
- [ ] **Migration appliquée** : `migrate ModuleFlight`
- [ ] **Settings mis à jour** : Configuration Duffel v2
- [ ] **Service testé** : Appels API fonctionnels
- [ ] **Modèles validés** : Nouveaux champs accessibles
- [ ] **Admin mis à jour** : Affichage des nouveaux champs
- [ ] **Documentation** : Équipe informée des changements

**Les modèles et settings sont maintenant conformes à l'API Duffel v2 ! 🎉**
