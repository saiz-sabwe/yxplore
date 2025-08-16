# 📝 Valeurs pour la Création de Compte

## 🎯 **Formulaire Actuel (sign-up.html)**

Le formulaire simple contient uniquement :
- `account_type` : "client" ou "merchant"
- `email` : Email de l'utilisateur
- `password` : Mot de passe
- `password_confirm` : Confirmation du mot de passe
- `terms` : Acceptation des conditions

## 🔧 **Valeurs Utilisées dans la Vue**

### **👤 Pour les Clients (`account_type = "client"`):**

```python
ClientProfile.create_from_user_data(
    user=user,
    first_name='',      # ✅ Vide - À compléter lors du KYC
    last_name='',       # ✅ Vide - À compléter lors du KYC  
    phone=None          # ✅ None - À compléter lors du KYC
)
```

**📋 Valeurs par défaut du modèle :**
- `kyc_status` = `KYC_PENDING` (0)
- `preferred_language` = `LANG_FR` (0)
- `is_active` = `True`
- `address` = `None`
- `birth_date` = `None`
- `nationality` = `None`
- `id_document` = `None`

### **🏢 Pour les Marchands (`account_type = "merchant"`):**

```python
temp_company_name = f"Entreprise de {email.split('@')[0]}"
MerchantProfile.create_from_registration_data(
    user=user,
    company_name=temp_company_name,                        # ✅ "Entreprise de john" (depuis john@example.com)
    business_type=MerchantProfile.BUSINESS_TRAVEL_AGENCY,  # ✅ 0 (Agence de voyage par défaut)
    contact_phone=None                                     # ✅ None - À compléter lors du KYC
)
```

**📋 Valeurs par défaut du modèle :**
- `contact_person` = `user.username` (car first_name et last_name sont vides)
- `contact_email` = `user.email`
- `kyc_status` = `KYC_PENDING` (0)
- `is_verified` = `False`
- `commission_rate` = `0.00`
- `is_active` = `True`
- `company_registration` = `None`
- `tax_id` = `None`
- `company_address` = `""`
- `company_city` = `""`
- `company_country` = `""`
- `company_postal_code` = `""`
- `business_license` = `None`
- `tax_certificate` = `None`
- `company_registration_doc` = `None`

## 🎯 **Pourquoi ces Valeurs ?**

### **✅ Logique de Progression :**

1. **Inscription Simple** : Seuls email + mot de passe + type requis
2. **Profil de Base** : Créé avec valeurs minimales
3. **Completion KYC** : L'utilisateur complète les informations manquantes

### **📈 Étapes du Workflow :**

```
📧 Inscription → 👤 Profil Minimal → 📋 Completion KYC → ✅ Validation Admin
```

### **🔄 Avantages :**

1. **🚀 Inscription Rapide** : Moins de friction à l'inscription
2. **📝 Progressive** : Informations complétées progressivement
3. **🎯 Flexibilité** : Adaptation selon le type d'utilisateur
4. **🔒 Sécurité** : KYC obligatoire avant utilisation complète

## 💡 **Exemples Concrets**

### **Client : john@example.com**
```python
User:
- username: "john"  # Auto-généré depuis email
- email: "john@example.com"
- first_name: ""
- last_name: ""

ClientProfile:
- nom: ""           # À compléter
- prenom: ""        # À compléter  
- phone: None       # À compléter
- kyc_status: 0     # En attente
```

### **Marchand : travel@agence.com**
```python
User:
- username: "travel"  # Auto-généré depuis email
- email: "travel@agence.com"
- first_name: ""
- last_name: ""

MerchantProfile:
- company_name: "Entreprise de travel"  # Auto-généré
- contact_person: "travel"              # username car first/last vides
- contact_email: "travel@agence.com"    # email utilisateur
- business_type: 0                      # Agence de voyage par défaut
- kyc_status: 0                         # En attente
```

## 🎯 **Prochaines Étapes**

1. **Dashboard** : Redirection vers completion du profil
2. **KYC Form** : Formulaires pour compléter les informations
3. **Validation** : Process de validation par les admins
4. **Activation** : Compte pleinement fonctionnel

Cette approche garantit une **inscription fluide** avec **completion progressive** ! 🎉
