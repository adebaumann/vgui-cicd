from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from abschnitte.models import Textabschnitt
from stichworte.models import Stichwort
from referenzen.models import Referenz
from rollen.models import Rolle
import datetime

class Dokumententyp(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    verantwortliche_ve = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Person(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    funktion = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural="Personen"

class Thema(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    erklaerung = models.TextField(blank=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural="Themen"


class Standard(models.Model):
    nummer = models.CharField(max_length=50, primary_key=True)
    dokumententyp = models.ForeignKey(Dokumententyp, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    autoren = models.ManyToManyField(Person, related_name='verfasste_dokumente')
    pruefende = models.ManyToManyField(Person, related_name='gepruefte_dokumente')
    gueltigkeit_von = models.DateField(null=True, blank=True)
    gueltigkeit_bis = models.DateField(null=True, blank=True)
    signatur_cso = models.CharField(max_length=255, blank=True)
    anhaenge = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nummer} – {self.name}"

    class Meta:
        verbose_name_plural="Standards"
        verbose_name="Standard"

class Vorgabe(models.Model):
    nummer = models.IntegerField()
    dokument = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='vorgaben')
    thema = models.ForeignKey(Thema, on_delete=models.PROTECT)
    titel = models.CharField(max_length=255)
    referenzen = models.ManyToManyField(Referenz, blank=True)
    gueltigkeit_von = models.DateField()
    gueltigkeit_bis = models.DateField(blank=True,null=True)
    stichworte = models.ManyToManyField(Stichwort, blank=True)
    relevanz = models.ManyToManyField(Rolle,blank=True)

    def Vorgabennummer(self):
        return str(self.dokument.nummer)+"."+self.thema.name[0]+"."+str(self.nummer)

    def get_status(self, check_date: datetime.date = datetime.date.today(), verbose: bool = False) -> str:
        if self.gueltigkeit_von > check_date:
            return "future" if not verbose else "Ist erst ab dem "+self.gueltigkeit_von.strftime('%d.%m.%Y')+" in Kraft."

        if not self.gueltigkeit_bis:
            return "active"

        if self.gueltigkeit_bis > check_date:
            return "active"

        return "expired" if not verbose else "Ist seit dem "+self.gueltigkeit_bis.strftime('%d.%m.%Y')+" nicht mehr in Kraft."


    class Meta:
        verbose_name_plural="Vorgaben"

    def __str__(self):
        return f"{self.Vorgabennummer()}: {self.titel}"

class VorgabeLangtext(Textabschnitt):
    abschnitt=models.ForeignKey(Vorgabe,on_delete=models.CASCADE)
    class Meta:
        verbose_name_plural="Langtext-Abschnitte"
        verbose_name="Langtext-Abschnitt"

class VorgabeKurztext(Textabschnitt):
    abschnitt=models.ForeignKey(Vorgabe,on_delete=models.CASCADE)
    class Meta:
        verbose_name_plural="Kurztext"
        verbose_name="Kurztext-Abschnitt"

class Geltungsbereich(Textabschnitt):
    geltungsbereich=models.ForeignKey(Standard,on_delete=models.CASCADE)
    class Meta:
        verbose_name_plural="Geltungsbereich"
        verbose_name="Geltungsbereichs-Abschnitt"

class Einleitung(Textabschnitt):
    einleitung=models.ForeignKey(Standard,on_delete=models.CASCADE)
    class Meta:
        verbose_name_plural="Einleitung"
        verbose_name="Einleitungs-Abschnitt"

class Checklistenfrage(models.Model):
    vorgabe=models.ForeignKey(Vorgabe, on_delete=models.CASCADE, related_name="checklistenfragen")
    frage = models.CharField(max_length=255)

    def __str__(self):
        return self.frage

    class Meta:
        verbose_name_plural="Fragen für Checkliste"

class Changelog(models.Model):
    dokument = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='changelog')
    autoren = models.ManyToManyField(Person)
    datum = models.DateField()
    aenderung = models.TextField()

    def __str__(self):
        return f"{self.datum} – {self.dokument.nummer}"
