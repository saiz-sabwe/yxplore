# 🚀 Guide d'intégration JavaScript ModuleFlight

## 📋 **Améliorations apportées**

### ✅ **1. Structure AJAX avec opérations (op)**
- **Avant** : Appels directs à des URLs spécifiques
- **Après** : Système d'opérations unifié comme dans ModuleProfils
- **Format** : `formData.append('op', 'operation_name')`

### ✅ **2. Utilisation du module de notifications global**
- **Import** : Le module `static/YXPLORE_NODE/js/module_notification.js` est utilisé directement
- **Fonctions** : `showSuccessFeedback()`, `showErrorFeedback()`, `showAlertFeedback()`, `showPopup()`
- **Plus de SweetAlert2 en dur** dans les fichiers JavaScript

### ✅ **3. Séparation HTML/JavaScript**
- **Avant** : HTML complexe généré dans le JavaScript
- **Après** : HTML minimal ou utilisation de templates existants
- **Approche** : Le JavaScript se concentre sur la logique, le HTML reste dans les templates

### ✅ **4. jQuery et structure cohérente**
- **Format uniforme** : Tous les appels AJAX suivent le même pattern
- **Gestion d'erreurs** : Centralisée et cohérente
- **CSRF** : Gestion automatique via les data attributes

---

## 🛠️ **Fichiers mis à jour**

### **1. static/ModuleFlight/js/flight-search.js**
```javascript
// Nouveau format d'appel AJAX avec opération
const formData = new FormData();
formData.append('op', 'search_flights');
// ... autres données
```

**Opérations supportées :**
- `search_flights` : Recherche de vols avec redirection
- Validation côté client renforcée
- Utilisation des notifications globales

### **2. static/ModuleFlight/js/flight-booking.js**
```javascript
// Nouveau format pour les réservations
const formData = new FormData();
formData.append('op', 'create_booking');
formData.append('offer_id', offerId);
formData.append('agency_id', agencyId);
formData.append('passenger_data', JSON.stringify(passengerData));
```

**Opérations supportées :**
- `get_agencies` : Récupération des agences disponibles
- `create_booking` : Création d'une réservation
- `pay_booking` : Paiement d'une réservation
- `cancel_booking` : Annulation d'une réservation
- `get_booking_details` : Détails d'une réservation

### **3. ModuleFlight/views.py**
Nouvelles méthodes AJAX ajoutées :
- `ajax_search_flights()`
- `ajax_get_agencies()`
- `ajax_create_booking()`
- `ajax_pay_booking()`
- `ajax_cancel_booking()`
- `ajax_get_booking_details()`

---

## 🎯 **Intégration dans les templates HTML**

### **1. Éléments requis dans les templates**

#### **Dans `base.html` ou `skeleton.html` :**
```html
<!-- Module de notifications global (obligatoire) -->
<script src="{% static 'YXPLORE_NODE/js/module_notification.js' %}"></script>

<!-- CSRF Token -->
<div id="csrf" data-csrf="{{ csrf_token }}" hidden></div>

<!-- URLs pour AJAX -->
<div id="flight-search-url" data-url="{% url 'flight:flight_search' %}" hidden></div>
<div id="booking-url" data-url="{% url 'flight:flight_book' %}" hidden></div>
<div id="payment-url" data-url="/flights/pay/" hidden></div>
<div id="cancel-url" data-url="{% url 'flight:flight_cancel' %}" hidden></div>
<div id="bookings-url" data-url="/flights/api/bookings/my_bookings/" hidden></div>
<div id="login-url" data-url="{% url 'profils:login' %}" hidden></div>

<!-- Statut utilisateur -->
<div id="user-status" data-authenticated="{% if user.is_authenticated %}true{% else %}false{% endif %}" hidden></div>
```

#### **Dans les templates de vols :**
```html
<!-- Formulaire de recherche -->
<form id="flight-search-form">
    {% csrf_token %}
    <input type="text" id="origin" name="origin" placeholder="Origine (ex: CDG)" required>
    <input type="text" id="destination" name="destination" placeholder="Destination (ex: JFK)" required>
    <input type="date" id="departure_date" name="departure_date" required>
    <input type="date" id="return_date" name="return_date">
    <select id="passengers" name="passengers">
        <option value="1">1 passager</option>
        <option value="2">2 passagers</option>
        <!-- ... -->
    </select>
    <button type="submit">Rechercher</button>
</form>

<!-- Boutons d'action pour les réservations -->
<button class="book-flight-btn" 
        data-offer-id="OFFER123" 
        data-price="499.99" 
        data-currency="EUR">
    Réserver
</button>

<button class="pay-booking-btn" 
        data-booking-id="{{ booking.uuid }}" 
        data-amount="{{ booking.price }}" 
        data-currency="{{ booking.currency }}">
    Payer
</button>

<button class="cancel-booking-btn" 
        data-booking-id="{{ booking.uuid }}" 
        data-booking-ref="{{ booking.booking_reference }}">
    Annuler
</button>

<button class="view-booking-details" 
        data-booking-id="{{ booking.uuid }}">
    Voir détails
</button>
```

### **2. Classes CSS pour l'état utilisateur**
```html
<body class="{% if user.is_authenticated %}authenticated{% endif %}">
```

### **3. Chargement des scripts**
```html
<!-- En fin de page -->
<script src="{% static 'ModuleFlight/js/flight-search.js' %}"></script>
<script src="{% static 'ModuleFlight/js/flight-booking.js' %}"></script>
```

---

## 🔄 **Format des réponses AJAX**

### **Format standard utilisé :**
```javascript
// Réponse de succès
{
    "resultat": "SUCCESS",
    "message": "Opération réussie",
    "data": { ... },  // Optionnel
    "redirect_url": "/path/"  // Optionnel
}

// Réponse d'erreur
{
    "resultat": "FAIL",
    "message": "Description de l'erreur"
}
```

### **Exemples de réponses :**

#### **Recherche de vols :**
```javascript
{
    "resultat": "SUCCESS",
    "message": "Recherche en cours...",
    "redirect_url": "/flights/results/?origin=CDG&destination=JFK&departure_date=2024-12-01"
}
```

#### **Récupération des agences :**
```javascript
{
    "resultat": "SUCCESS",
    "message": "Agences chargées",
    "agencies": [
        {
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "id": 1,
            "name": "Air France Travel",
            "city": "Paris",
            "country": "France"
        }
    ]
}
```

#### **Création de réservation :**
```javascript
{
    "resultat": "SUCCESS",
    "message": "Réservation créée avec succès",
    "data": {
        "booking_id": "550e8400-e29b-41d4-a716-446655440000",
        "booking_reference": "YX123456",
        "status": "En attente",
        "price": "499.99",
        "currency": "EUR"
    }
}
```

---

## 🎨 **Notifications utilisées**

### **Types disponibles :**
- `showSuccessFeedback(message)` : Notification de succès (toast vert)
- `showErrorFeedback(message)` : Notification d'erreur (toast rouge)
- `showAlertFeedback(message)` : Information (toast bleu)
- `showPopup(icon, title, text, options)` : Popup personnalisée

### **Exemples d'usage :**
```javascript
// Toast simple
showSuccessFeedback('Réservation créée avec succès');

// Popup avec choix
showPopup('question', 'Confirmer ?', 'Voulez-vous continuer ?', {
    showCancelButton: true,
    confirmButtonText: 'Oui',
    cancelButtonText: 'Non'
}).then((result) => {
    if (result.isConfirmed) {
        // Action confirmée
    }
});
```

---

## 🚀 **Avantages de cette approche**

### ✅ **1. Consistance**
- Même format d'appel AJAX dans tout le projet
- Même système de notifications
- Même gestion d'erreurs

### ✅ **2. Maintenabilité**
- Code JavaScript plus propre et organisé
- Séparation claire HTML/JS
- Réutilisation du code

### ✅ **3. Évolutivité**
- Facile d'ajouter de nouvelles opérations
- Templates HTML indépendants du JavaScript
- Système modulaire

### ✅ **4. UX améliorée**
- Notifications cohérentes
- Gestion d'erreurs centralisée
- Interface reactive

---

## 📝 **Instructions finales**

### **1. Import obligatoire :**
```html
<script src="{% static 'YXPLORE_NODE/js/module_notification.js' %}"></script>
```

### **2. Data attributes requis :**
- `data-csrf` : Token CSRF
- `data-authenticated` : Statut de connexion
- URLs des endpoints AJAX

### **3. Classes CSS :**
- `authenticated` sur `<body>` si connecté
- Classes pour les boutons d'action

### **4. Structure des boutons :**
- Utiliser les `data-*` attributes pour passer les paramètres
- Classes CSS spécifiques pour les event listeners

**L'intégration est maintenant prête et conforme aux standards du projet !** 🎉
