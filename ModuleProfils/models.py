from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profil(models.Model):
    USERNAME_FIELD = 'username'

    nom = models.CharField(max_length=255, verbose_name="Nom", null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')

    create = models.DateTimeField(verbose_name="Date de création", auto_now_add=True)
    last_update = models.DateTimeField(verbose_name="Dernière mise à jour", auto_now=True)
    create_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="Profil_createby", verbose_name="Créé par")
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="Profil_updateby", verbose_name="Mis à jour par")
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "UTILISATEURS"
        ordering = ['-create']
