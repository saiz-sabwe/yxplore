# 🔍 Debug de la recherche de vol - ModuleFlight

## ✅ **Problèmes identifiés et corrigés**

### **1. Formulaire HTML manquant**
- ❌ **Avant** : Pas d'`id="flight-search-form"` sur le `<form>`
- ✅ **Après** : `<form id="flight-search-form" class="...">`

### **2. Champs sans ID**
- ❌ **Avant** : Les `<select>` et `<input>` n'avaient pas d'`id`
- ✅ **Après** : Tous les champs ont maintenant des `id` et `name`

### **3. Bouton de soumission incorrect**
- ❌ **Avant** : `<a href="#" class="btn...">` (lien sans action)
- ✅ **Après** : `<button type="submit" class="btn...">` (bouton de soumission)

### **4. Valeurs des options manquantes**
- ❌ **Avant** : `<option>CDG</option>` (sans `value`)
- ✅ **Après** : `<option value="CDG">Paris Charles de Gaulle (CDG)</option>`

---

## 🎯 **Champs maintenant fonctionnels**

### **✅ Formulaire principal**
```html
<form id="flight-search-form" class="...">
  <!-- Type de vol -->
  <input type="radio" name="trip_type" value="one_way" checked>
  <input type="radio" name="trip_type" value="round_trip">
  
  <!-- Classe de cabine -->
  <select id="cabin_class" name="cabin_class">
    <option value="economy">Économique</option>
    <option value="business">Affaires</option>
    <!-- etc. -->
  </select>
  
  <!-- Nombre de passagers -->
  <select id="passengers" name="passengers">
    <option value="1">1</option>
    <option value="2">2</option>
    <!-- etc. jusqu'à 9 -->
  </select>
</form>
```

### **✅ Onglet Aller simple**
```html
<!-- Origine -->
<select id="origin" name="origin">
  <option value="CDG">Paris Charles de Gaulle (CDG)</option>
  <option value="JFK">New York JFK (JFK)</option>
  <!-- etc. -->
</select>

<!-- Destination -->
<select id="destination" name="destination">
  <option value="JFK">New York JFK (JFK)</option>
  <option value="CDG">Paris Charles de Gaulle (CDG)</option>
  <!-- etc. -->
</select>

<!-- Date de départ -->
<input type="text" id="departure_date" name="departure_date" required>

<!-- Bouton de recherche -->
<button type="submit">Rechercher un billet</button>
```

### **✅ Onglet Aller-retour**
```html
<!-- Mêmes champs + date de retour -->
<input type="text" id="return_date" name="return_date">
```

---

## 🚀 **Comment tester maintenant**

### **1. Recharger la page**
```
http://127.0.0.1:8000/flights/Flight/
```

### **2. Vérifier la console JavaScript**
- Ouvrir DevTools (F12)
- Aller dans l'onglet Console
- Vérifier : "Flight Search JS loaded"

### **3. Remplir le formulaire**
```
Origine: CDG (Paris Charles de Gaulle)
Destination: JFK (New York JFK)
Date départ: 15/12/2024
Passagers: 2
Classe: Affaires
```

### **4. Cliquer sur "Rechercher un billet"**
- Le formulaire doit se soumettre via AJAX
- Vérifier dans l'onglet Network des DevTools
- POST vers `/flights/search/` avec `op=search_flights`

---

## 🔧 **Fonctionnalités disponibles**

### **✅ Échange origine/destination**
- Bouton avec icône ↔️
- Échange automatique des valeurs

### **✅ Validation des aéroports**
- Codes IATA valides (CDG, JFK, LHR, etc.)
- Validation côté client et serveur

### **✅ Gestion des dates**
- Sélecteur de date avec Flatpickr
- Validation des dates (pas de dates passées)
- Gestion aller simple vs aller-retour

### **✅ Types de vol**
- Radio buttons cachés dans les onglets
- JavaScript détecte le changement d'onglet

---

## 📱 **URLs de test**

### **✅ Page de recherche**
```
http://127.0.0.1:8000/flights/
http://127.0.0.1:8000/flights/search/
http://127.0.0.1:8000/flights/Flight/
```

### **✅ Page de résultats (après recherche)**
```
http://127.0.0.1:8000/flights/results/?origin=CDG&destination=JFK&departure_date=2024-12-15&passengers=2&cabin_class=business
```

---

## 🎉 **Résultat attendu**

Après avoir cliqué sur "Rechercher un billet" :

1. **AJAX POST** vers `/flights/search/` avec `op=search_flights`
2. **Validation** côté serveur dans `FlightView.ajax_search_flights()`
3. **Redirection** vers `/flights/results/` avec les paramètres
4. **Affichage** des résultats via `FlightView.flight_results()`
5. **Appel API Duffel** pour récupérer les vrais vols

**La recherche de vol devrait maintenant fonctionner parfaitement ! 🚀**
