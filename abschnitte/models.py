from django.db import models

class AbschnittTyp(models.Model):
    abschnitttyp = models.CharField(max_length=100, primary_key=True)

    def __str__(self):
        return self.abschnitttyp

    class Meta:
        verbose_name_plural = "Abschnitttypen"


class Textabschnitt(models.Model):
    abschnitttyp = models.ForeignKey(
        AbschnittTyp, on_delete=models.PROTECT, blank=True, null=True
    )
    inhalt = models.TextField(blank=True, null=True)
    order=models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        verbose_name = "Abschnitt"
        verbose_name_plural = "Abschnitte"
