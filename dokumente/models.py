from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.auth.models import User
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

    class Meta:
        verbose_name="Dokumententyp"
        verbose_name_plural="Dokumententypen"


class Person(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    funktion = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural="Personen"
        ordering = ['name']

class Thema(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    erklaerung = models.TextField(blank=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural="Themen"


class Dokument(models.Model):
    nummer = models.CharField(max_length=50, primary_key=True)
    dokumententyp = models.ForeignKey(Dokumententyp, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    autoren = models.ManyToManyField(Person, related_name='verfasste_dokumente')
    pruefende = models.ManyToManyField(Person, related_name='gepruefte_dokumente')
    gueltigkeit_von = models.DateField(null=True, blank=True)
    gueltigkeit_bis = models.DateField(null=True, blank=True)
    signatur_cso = models.CharField(max_length=255, blank=True)
    anhaenge = models.TextField(blank=True)
    aktiv = models.BooleanField(blank=True)

    def __str__(self):
        return f"{self.nummer} – {self.name}"

    @property
    def dates(self):
        """
        Returns an array of unique, chronologically sorted dates representing
        state-change dates from all Vorgaben in this document.
        
        These are dates where Vorgaben become active (gueltigkeit_von) or change state
        (the day after gueltigkeit_bis). Only includes the day after gueltigkeit_bis 
        for Vorgaben that have a defined end date (not infinite validity).
        """
        dates_set = set()
        
        # Get all vorgaben for this document
        for vorgabe in self.vorgaben.all():
            # Add gueltigkeit_von (when vorgabe becomes active)
            if vorgabe.gueltigkeit_von:
                dates_set.add(vorgabe.gueltigkeit_von)
            
            # Add the day after gueltigkeit_bis (when vorgabe expires/changes state)
            # Only if gueltigkeit_bis is defined (not None)
            if vorgabe.gueltigkeit_bis:
                dates_set.add(vorgabe.gueltigkeit_bis + datetime.timedelta(days=1))
        
        # Return sorted unique dates from oldest to newest
        return sorted(list(dates_set))

    class Meta:
        verbose_name_plural="Dokumente"
        verbose_name="Dokument"

class Vorgabe(models.Model):
    order = models.IntegerField()
    nummer = models.IntegerField()
    dokument = models.ForeignKey(Dokument, on_delete=models.CASCADE, related_name='vorgaben')
    thema = models.ForeignKey(Thema, on_delete=models.PROTECT, blank=False)
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

        if self.gueltigkeit_bis >= check_date:
            return "active"

        return "expired" if not verbose else "Ist seit dem "+self.gueltigkeit_bis.strftime('%d.%m.%Y')+" nicht mehr in Kraft."

    def __str__(self):
        return f"{self.Vorgabennummer()}: {self.titel}"

    @staticmethod
    def sanity_check_vorgaben():
        """
        Sanity check for Vorgaben:
        If there are two Vorgaben with the same number, Thema and Dokument,
        their valid_from and valid_to date ranges shouldn't intersect.
        
        Returns:
            list: List of dictionaries containing conflicts found
        """
        conflicts = []
        
        # Group Vorgaben by dokument, thema, and nummer
        from django.db.models import Count
        from itertools import combinations
        
        # Find Vorgaben with same dokument, thema, and nummer
        duplicate_groups = (
            Vorgabe.objects.values('dokument', 'thema', 'nummer')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        
        for group in duplicate_groups:
            # Get all Vorgaben in this group
            vorgaben = Vorgabe.objects.filter(
                dokument=group['dokument'],
                thema=group['thema'], 
                nummer=group['nummer']
            )
            
            # Check all pairs for date range intersections
            for vorgabe1, vorgabe2 in combinations(vorgaben, 2):
                if Vorgabe._date_ranges_intersect(
                    vorgabe1.gueltigkeit_von, vorgabe1.gueltigkeit_bis,
                    vorgabe2.gueltigkeit_von, vorgabe2.gueltigkeit_bis
                ):
                    conflicts.append({
                        'vorgabe1': vorgabe1,
                        'vorgabe2': vorgabe2,
                        'conflict_type': 'date_range_intersection',
                        'message': f"Vorgaben {vorgabe1.Vorgabennummer()} and {vorgabe2.Vorgabennummer()} "
                                  f"überschneiden sich in der Geltungsdauer"
                    })
        
        return conflicts

    def clean(self):
        """
        Validate the Vorgabe before saving.
        """
        from django.core.exceptions import ValidationError

        # Check for conflicts with existing Vorgaben
        conflicts = self.find_conflicts()
        if conflicts:
            conflict_messages = [c['message'] for c in conflicts]
            raise ValidationError({
                '__all__': conflict_messages
            })
    
    def find_conflicts(self):
        """
        Find conflicts with existing Vorgaben.
        
        Returns:
            list: List of conflict dictionaries
        """
        conflicts = []
        
        # Find Vorgaben with same dokument, thema, and nummer (excluding self)
        existing_vorgaben = Vorgabe.objects.filter(
            dokument=self.dokument,
            thema=self.thema,
            nummer=self.nummer
        ).exclude(pk=self.pk)
        
        for other_vorgabe in existing_vorgaben:
            if self._date_ranges_intersect(
                self.gueltigkeit_von, self.gueltigkeit_bis,
                other_vorgabe.gueltigkeit_von, other_vorgabe.gueltigkeit_bis
            ):
                conflicts.append({
                    'vorgabe1': self,
                    'vorgabe2': other_vorgabe,
                    'conflict_type': 'date_range_intersection',
                    'message': f"Vorgabe {self.Vorgabennummer()} in Konflikt mit "
                              f"bestehender {other_vorgabe.Vorgabennummer()} "
                              f" - Geltungsdauer übeschneidet sich"
                })
        
        return conflicts

    @staticmethod
    def _date_ranges_intersect(start1, end1, start2, end2):
        """
        Check if two date ranges intersect.
        None end date means open-ended range.
        
        Args:
            start1, start2: Start dates
            end1, end2: End dates (can be None for open-ended)
            
        Returns:
            bool: True if ranges intersect
        """
        # If either start date is None, treat it as invalid case
        if not start1 or not start2:
            return False
            
        # If end date is None, treat it as far future
        end1 = end1 or datetime.date.max
        end2 = end2 or datetime.date.max
        
        # Ranges intersect if start1 <= end2 and start2 <= end1
        return start1 <= end2 and start2 <= end1

    class Meta:
        verbose_name_plural="Vorgaben"
        ordering = ['order']

class VorgabeLangtext(Textabschnitt):
    abschnitt=models.ForeignKey(Vorgabe,on_delete=models.CASCADE)
    class Meta:
        verbose_name_plural="Langtext"
        verbose_name="Langtext-Abschnitt"

class VorgabeKurztext(Textabschnitt):
    abschnitt=models.ForeignKey(Vorgabe,on_delete=models.CASCADE)
    class Meta:
        verbose_name_plural="Kurztext"
        verbose_name="Kurztext-Abschnitt"

class Geltungsbereich(Textabschnitt):
    geltungsbereich=models.ForeignKey(Dokument,on_delete=models.CASCADE)
    class Meta:
        verbose_name_plural="Geltungsbereich"
        verbose_name="Geltungsbereichs-Abschnitt"

class Einleitung(Textabschnitt):
    einleitung=models.ForeignKey(Dokument,on_delete=models.CASCADE)
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
        verbose_name="Frage für Checkliste"

class VorgabenTable(Vorgabe):
    class Meta:
        proxy = True
        verbose_name = "Vorgabe (Tabellenansicht)"
        verbose_name_plural = "Vorgaben (Tabellenansicht)"

class Changelog(models.Model):
    dokument = models.ForeignKey(Dokument, on_delete=models.CASCADE, related_name='changelog')
    autoren = models.ManyToManyField(Person)
    datum = models.DateField()
    aenderung = models.TextField()

    def __str__(self):
        return f"{self.datum} – {self.dokument.nummer}"

    class Meta:
        verbose_name_plural="Changelog"
        verbose_name="Changelog-Eintrag"


class VorgabeComment(models.Model):
    vorgabe = models.ForeignKey(Vorgabe, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vorgabe-Kommentar"
        verbose_name_plural = "Vorgabe-Kommentare"
        ordering = ['-created_at']

    def __str__(self):
        return f"Kommentar von {self.user.username} zu {self.vorgabe.Vorgabennummer()}"
