from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from abschnitte.models import Textabschnitt

# Create your models here.
class Referenz(MPTTModel):
    id = models.AutoField(primary_key=True)
    name_nummer = models.CharField(max_length=100)
    name_text=models.CharField(max_length=255, blank=True)
    oberreferenz = TreeForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='unterreferenzen'
    )
    url = models.URLField(blank=True)

    def Path(self):
        Temp = " → ".join([str(x) for x in self.get_ancestors(include_self=True)])+(" (%s)"%self.name_text if self.name_text else "")
        return Temp

    class MPTTMeta:
        parent_attr = 'oberreferenz'  # optional, but safe
        order_insertion_by = ['name_nummer']

    def __str__(self):
        return self.name_nummer

    class Meta:
        verbose_name_plural="Referenzen"

class Referenzerklaerung (Textabschnitt):
    erklaerung = models.ForeignKey(Referenz,on_delete=models.CASCADE)

    class Meta:
        verbose_name="Erklärung"
