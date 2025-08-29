# Notes de Migration - Module Flight

## Mise à jour des modèles avec champs standards

### Changements apportés

Tous les modèles du module Flight ont été mis à jour pour inclure les champs standards suivants :

```python
# Champs standards ajoutés à tous les modèles
is_active = models.BooleanField(verbose_name="Actif?", default=True)
create = models.DateTimeField(verbose_name="Date de création", auto_now_add=True)
last_update = models.DateTimeField(verbose_name="Dernière mise à jour", auto_now=True)
create_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="..._createby", verbose_name="Créé par")
update_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="..._updateby", verbose_name="Mis à jour par")
```

### Modèles affectés

#### 1. TravelAgency
- **Supprimé :** `created_at`, `updated_at`
- **Ajouté :** `create`, `last_update`, `create_by`, `update_by`
- **Related names :** `travelagency_createby`, `travelagency_updateby`

#### 2. MerchantAgency
- **Conservé :** `assigned_at` (champ spécifique métier)
- **Ajouté :** `create`, `last_update`, `create_by`, `update_by`
- **Related names :** `merchantagency_createby`, `merchantagency_updateby`

#### 3. FlightBooking
- **Supprimé :** `created_at`, `updated_at`
- **Conservé :** `confirmed_at`, `paid_at` (champs spécifiques métier)
- **Ajouté :** `create`, `last_update`, `create_by`, `update_by`
- **Related names :** `flightbooking_createby`, `flightbooking_updateby`

### Métadonnées des modèles

Tous les modèles utilisent maintenant :
```python
class Meta:
    ordering = ['-create']  # Au lieu de ['-created_at']
```

### Méthodes mises à jour

Les méthodes suivantes ont été mises à jour pour accepter les paramètres `created_by` et `updated_by` :

#### TravelAgency
- `deactivate(updated_by=None)`

#### MerchantAgency
- `assign_merchant_to_agency(..., created_by=None)`
- `remove_assignment(updated_by=None)`

#### FlightBooking
- `create_booking(..., created_by=None)`
- `confirm_booking(..., updated_by=None)`
- `cancel_booking(updated_by=None)`
- `mark_paid(..., updated_by=None)`

### Interface d'administration

L'admin Django a été mis à jour pour :
- Afficher les nouveaux champs dans les listes
- Inclure les filtres par `create`, `create_by`
- Utiliser les nouveaux noms de champs dans les fieldsets
- Trier par `-create` au lieu de `-created_at`

### Serializers DRF

Tous les serializers incluent maintenant :
- `create`, `last_update`, `create_by`, `update_by` dans les champs
- `create`, `last_update` en read-only

### Vues et API

Les vues ont été mises à jour pour passer :
- `created_by=request.user` lors de la création
- `updated_by=request.user` lors des modifications

## Migration requise

Pour appliquer ces changements, exécuter :

```bash
python manage.py makemigrations ModuleFlight
python manage.py migrate ModuleFlight
```

## Compatibilité

- ✅ Rétrocompatible avec les données existantes
- ✅ Les anciens champs sont remplacés automatiquement
- ✅ Les nouvelles fonctionnalités sont optionnelles (nullable)
- ✅ Aucune perte de données

## Tests recommandés

Après migration, tester :
1. Création d'agences via admin
2. Affectation de marchands
3. Création de réservations
4. Paiements et annulations
5. Vérification des champs create_by/update_by

## Notes importantes

- Les `related_names` sont uniques pour éviter les conflits
- Le champ `is_active` est maintenant standard sur tous les modèles
- L'ordre par défaut est basé sur `create` (plus récent en premier)
- Les timestamps spécifiques métier (`confirmed_at`, `paid_at`) sont conservés
