# 🛫 Module Flight - YXPLORE

## Vue d'ensemble

Le **Module Flight** est un système complet de gestion des vols pour la plateforme YXPLORE. Il permet la recherche, la réservation et la gestion des vols via l'intégration de l'API Duffel.

## 🚀 Fonctionnalités principales

### ✈️ Recherche de vols
- Recherche via l'API Duffel en temps réel
- Support des vols aller simple et aller-retour
- Filtres par classe de cabine et nombre de passagers
- Affichage des résultats avec détails complets

### 🏢 Gestion des agences
- Création et gestion des agences de voyage
- Affectation des marchands aux agences
- Gestion des rôles et responsabilités

### 📋 Réservations
- Création de réservations avec données passagers
- Gestion des statuts (En attente, Confirmé, Annulé)
- Calcul automatique des commissions
- Paiement factice intégré

### 💰 Système de paiement
- Simulation de paiement pour tests
- Gestion des statuts de paiement
- Calcul des commissions par agence

### 🔗 API REST
- API complète avec Django REST Framework
- Endpoints pour toutes les fonctionnalités
- Documentation automatique

## 📊 Architecture

### Modèles de données

#### TravelAgency
```python
- id: UUID (Primary Key)
- name: Nom de l'agence
- country: Pays
- city: Ville
- address: Adresse complète
- iata_code: Code IATA (optionnel)
- phone: Téléphone
- email: Email
- is_active: Statut actif
```

#### MerchantAgency
```python
- id: UUID (Primary Key)
- merchant: ForeignKey vers MerchantProfile
- agency: ForeignKey vers TravelAgency
- role: Rôle (MANAGER, AGENT, SUPERVISOR)
- is_responsible: Responsable principal
- is_active: Statut actif
```

#### FlightBooking
```python
- id: UUID (Primary Key)
- booking_reference: Référence unique
- client: ForeignKey vers ClientProfile
- agency: ForeignKey vers TravelAgency
- merchant: ForeignKey vers MerchantProfile
- duffel_offer_id: ID de l'offre Duffel
- duffel_booking_id: ID de réservation Duffel
- origin/destination: Codes aéroports
- departure_date/return_date: Dates de voyage
- passenger_count: Nombre de passagers
- price: Prix total
- currency: Devise
- commission_rate: Taux de commission
- status: Statut de la réservation
- payment_status: Statut du paiement
- passenger_data: Données JSON des passagers
- flight_data: Cache des données de vol
```

## 🔧 Installation et configuration

### 1. Dépendances
```bash
pip install -r requirements.txt
```

Nouvelles dépendances ajoutées :
- `duffel-api>=1.0.0` (SDK optionnel)
- `requests>=2.25.0` (pour HTTP)
- `python-dateutil>=2.8.0` (manipulation dates)

### 2. Configuration des settings

```python
# Configuration API Duffel
DUFFEL_API_KEY = 'duffel_test_...'  # Votre clé API Duffel
DUFFEL_BASE_URL = 'https://api.duffel.com/air'

# Configuration du module Flight
FLIGHT_CONFIG = {
    'DEFAULT_COMMISSION_RATE': 5.0,
    'MAX_PASSENGERS_PER_BOOKING': 9,
    'BOOKING_EXPIRY_HOURS': 24,
    'CURRENCY_DEFAULT': 'EUR',
    'SEARCH_RESULTS_LIMIT': 50,
}
```

### 3. Migrations
```bash
python manage.py makemigrations ModuleFlight
python manage.py migrate
```

### 4. Création d'un superutilisateur
```bash
python manage.py createsuperuser
```

## 🔀 URLs et Navigation

### URLs principales
- `/flights/` - Page de recherche (homepage)
- `/flights/search/` - Formulaire de recherche
- `/flights/results/` - Résultats de recherche
- `/flights/detail/<offer_id>/` - Détails d'une offre
- `/flights/book/` - Réservation (AJAX)
- `/flights/pay/<booking_id>/` - Paiement (AJAX)

### API REST
- `/flights/api/agencies/` - Gestion des agences
- `/flights/api/bookings/` - Gestion des réservations
- `/flights/api/merchant-agencies/` - Affectations marchand-agence
- `/flights/api/search/` - Recherche de vols

## 🎨 Interface utilisateur

### Templates
- `affiche.html` - Page de recherche de vols
- `flight-list.html` - Liste des résultats
- `flight-detail.html` - Détails et réservation

### JavaScript
- `flight-search.js` - Gestion de la recherche
- `flight-booking.js` - Gestion des réservations

### Fonctionnalités AJAX
- Validation en temps réel
- Notifications SweetAlert2
- Gestion des erreurs
- Interface responsive

## 👥 Gestion des utilisateurs

### Types d'utilisateurs

#### Clients
- Recherche et réservation de vols
- Gestion de leurs réservations
- Paiement des réservations

#### Marchands
- Accès aux réservations de leurs agences
- Gestion des commissions
- Validation des réservations

#### Administrateurs
- Gestion complète via Django Admin
- Configuration des agences
- Supervision des réservations

## 🔐 Sécurité et permissions

### Authentification
- Connexion requise pour les réservations
- Vérification des permissions par type d'utilisateur
- Protection CSRF sur tous les formulaires

### Validation des données
- Validation côté client (JavaScript)
- Validation côté serveur (Django + DRF)
- Validation des données Duffel

## 📱 API REST - Documentation

### Endpoints principaux

#### Recherche de vols
```http
POST /flights/api/search/
Content-Type: application/json

{
    "origin": "CDG",
    "destination": "JFK",
    "departure_date": "2024-03-15",
    "return_date": "2024-03-22",
    "passengers": 2,
    "cabin_class": "economy"
}
```

#### Création de réservation
```http
POST /flights/api/bookings/
Content-Type: application/json

{
    "duffel_offer_id": "off_123456789",
    "agency_id": "uuid-agency-id",
    "passenger_data": [
        {
            "title": "Mr",
            "given_name": "John",
            "family_name": "Doe",
            "born_on": "1985-06-15",
            "gender": "male"
        }
    ]
}
```

#### Paiement d'une réservation
```http
POST /flights/api/bookings/{booking_id}/pay/
```

#### Annulation d'une réservation
```http
POST /flights/api/bookings/{booking_id}/cancel/
```

### Réponses API
Toutes les réponses suivent le format :
```json
{
    "success": true|false,
    "message": "Message descriptif",
    "data": { ... }
}
```

## 🔄 Workflow de réservation

### 1. Recherche
```
Utilisateur → Formulaire recherche → API Duffel → Résultats
```

### 2. Sélection et réservation
```
Sélection offre → Formulaire passagers → Création réservation locale → Statut PENDING
```

### 3. Paiement
```
Demande paiement → Simulation paiement → Statut CONFIRMED + PAID
```

### 4. Gestion
```
Suivi réservation → Modifications possibles → Annulation si autorisée
```

## 🛠 Service Duffel

### Méthodes principales
- `search_flights()` - Recherche de vols
- `get_offer()` - Détails d'une offre
- `create_booking()` - Création réservation Duffel
- `confirm_booking()` - Confirmation réservation
- `cancel_booking()` - Annulation réservation

### Gestion d'erreurs
- `DuffelAPIError` - Exception personnalisée
- Logs détaillés des appels API
- Fallback en cas d'indisponibilité

## 📈 Administration Django

### Interface d'administration
- **TravelAgencyAdmin** - Gestion des agences
- **MerchantAgencyAdmin** - Affectations marchand-agence
- **FlightBookingAdmin** - Suivi des réservations

### Actions disponibles
- Activation/désactivation en masse
- Confirmation de réservations
- Marquage comme payé
- Annulation de réservations

### Statistiques
- Nombre de réservations par agence
- Commissions générées
- Taux de conversion

## 🧪 Tests et développement

### Variables d'environnement de test
```bash
DUFFEL_API_KEY=duffel_test_...
DEBUG=True
```

### Données de test
```python
# Codes d'aéroports pour tests
AIRPORTS = ['CDG', 'ORY', 'LHR', 'JFK', 'LAX', 'DXB']

# Agences de test
AGENCIES = [
    {'name': 'Voyages Paris', 'city': 'Paris', 'country': 'France'},
    {'name': 'Travel London', 'city': 'London', 'country': 'UK'},
]
```

## 🚨 Troubleshooting

### Erreurs courantes

#### Erreur API Duffel
```
Vérifier DUFFEL_API_KEY dans settings
Vérifier connectivité internet
Vérifier logs dans /logs/flight.log
```

#### Erreur de réservation
```
Vérifier permissions utilisateur
Vérifier données passagers
Vérifier disponibilité de l'offre
```

#### Erreur de paiement
```
Vérifier statut de la réservation
Vérifier que la réservation n'est pas déjà payée
```

### Logs
Les logs sont sauvegardés dans :
- `logs/flight.log` - Logs du module Flight
- Console Django en mode DEBUG

## 🔄 Mise à jour et maintenance

### Vérifications régulières
- Validité des clés API Duffel
- Nettoyage des réservations expirées
- Archivage des données anciennes

### Monitoring
- Surveillance des appels API Duffel
- Monitoring des performances
- Alertes en cas d'erreur

## 📞 Support

### Documentation API Duffel
- [Documentation officielle Duffel](https://duffel.com/docs)
- [Guide d'intégration](https://duffel.com/docs/guides)

### Contact
- Développeur : Équipe YXPLORE
- Email support : support@yxplore.com

## 📄 Licence

Ce module fait partie de la plateforme YXPLORE et est soumis aux mêmes conditions de licence.

---

**Version :** 1.0.0  
**Dernière mise à jour :** Décembre 2024  
**Compatibilité :** Django 5.2+, Python 3.8+
