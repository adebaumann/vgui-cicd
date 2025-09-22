from django.db import models
from abschnitte.models import Textabschnitt

# Create your models here.
class Rolle(models.Model):
    name = models.CharField(max_length=100, primary_key=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural="Rollen"

class RollenBeschreibung(Textabschnitt):
    abschnitt=models.ForeignKey(Rolle,on_delete=models.CASCADE)
    class Meta:
        verbose_name_plural="Rollenbeschreibung"
        verbose_name="Rollenbeschreibungs-Abschnitt"