from django.db import models
from abschnitte.models import Textabschnitt

class Stichwort(models.Model):
    stichwort = models.CharField(max_length=50, primary_key=True)

    def __str__(self):
        return self.stichwort

    class Meta:
        verbose_name_plural="Stichworte"

class Stichworterklaerung (Textabschnitt):
    erklaerung = models.ForeignKey(Stichwort,on_delete=models.CASCADE)

    class Meta:
        verbose_name="Erklärung"
