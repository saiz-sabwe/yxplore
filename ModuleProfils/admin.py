from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from ModuleProfils.models import Profil

# Register your models here.

@admin.register(Profil)
class ProfilAdmin(ImportExportModelAdmin):
    list_display = (
        "nom",
        "user",
        "create",
        "create_by",
        "last_update",
    )
    search_fields = ("nom", "user__username", "user__email")
    list_filter = ("create", "last_update", "create_by")
    readonly_fields = ["create_by", "update_by", "create", "last_update"]
    autocomplete_fields = ['user']

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.create_by = request.user
        obj.update_by = request.user
        super().save_model(request, obj, form, change)

