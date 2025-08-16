# Module Profils - YXPLORE

## Vue d'ensemble

Le module des profils gère les différents types d'utilisateurs dans la plateforme YXPLORE avec un système de gestion des rôles basé sur des modèles séparés.

## Structure des Modèles

### 1. ClientProfile
- **Type** : Profil pour les clients finaux
- **Fonctionnalités** :
  - Informations personnelles (nom, prénom, téléphone, adresse)
  - Système KYC avec statuts et documents
  - Préférences linguistiques
  - Métadonnées de création/modification

### 2. MerchantProfile
- **Type** : Profil pour les marchands/partenaires commerciaux
- **Fonctionnalités** :
  - Informations entreprise (nom, enregistrement, TVA)
  - Contact principal et adresse commerciale
  - Système KYC avec documents légaux
  - Type d'entreprise et taux de commission
  - Statut de vérification

### 3. AdminProfile
- **Type** : Profil pour les administrateurs de la plateforme
- **Fonctionnalités** :
  - Niveau d'administration (Super, Système, KYC, Financier, Support)
  - Permissions granulaires par fonction
  - Département et informations de contact
  - Métadonnées de gestion

### 4. KYCValidation
- **Type** : Historique des validations KYC
- **Fonctionnalités** :
  - Suivi des validations KYC1 et KYC2
  - Statuts (En attente, Approuvé, Rejeté)
  - Notes et historique des validations
  - Traçabilité des actions

## Constantes et Choix

### Statuts KYC
- `0` - En attente
- `1` - KYC1 Approuvé
- `2` - KYC2 Approuvé
- `3` - Rejeté

### Types de profil
- `0` - Client
- `1` - Marchand
- `2` - Administrateur

### Langues
- `0` - Français
- `1` - English
- `2` - العربية

### Types d'entreprise
- `0` - Agence de voyage
- `1` - Hôtel
- `2` - Compagnie aérienne
- `3` - Location de voiture
- `4` - Tour opérateur
- `5` - Autre

### Niveaux d'administration
- `0` - Super Administrateur
- `1` - Administrateur Système
- `2` - Administrateur KYC
- `3` - Administrateur Financier
- `4` - Administrateur Support

## Interface d'Administration

L'interface d'administration Django est personnalisée avec :

- **Inline profiles** : Affichage des profils directement dans l'interface User
- **Filtres avancés** : Par statut KYC, type de profil, etc.
- **Recherche** : Par nom, email, entreprise
- **Groupement des champs** : Organisation logique des informations
- **Permissions** : Gestion des droits d'accès

## URLs

- **Page principale** : `/profils/`
- **Admin Django** : `/admin/ModuleProfils/`

## Prochaines Étapes

1. **Créer les migrations** : `python manage.py makemigrations ModuleProfils`
2. **Appliquer les migrations** : `python manage.py migrate`
3. **Créer un super utilisateur** : `python manage.py createsuperuser`
4. **Tester l'interface d'administration**
5. **Implémenter les workflows KYC** (Phase 1 - J3-4)

## Architecture

```
ModuleProfils/
├── models.py          # Modèles de données
├── admin.py          # Interface d'administration
├── views.py          # Vues simples
├── urls.py           # Routes
└── migrations/       # Base de données
```

## Notes Techniques

- **Relations** : OneToOne avec le modèle User Django
- **Choix** : Utilisation de constantes entières pour les performances
- **Métadonnées** : Traçabilité complète des créations/modifications
- **Validation** : Gestion des documents avec types de fichiers autorisés
- **Extensibilité** : Structure prête pour l'ajout de nouveaux types de profils
