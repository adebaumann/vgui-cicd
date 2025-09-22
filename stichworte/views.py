from django.shortcuts import render
from abschnitte.utils import render_textabschnitte
from .models import Stichwort, Stichworterklaerung
from itertools import groupby
from django.db.models.functions import Lower



# Create your views here.
def stichwort_list(request):
    qs = Stichwort.objects.order_by(Lower('stichwort'))
    stichworte = {k: [o.stichwort for o in g] for k,g in groupby (qs, key=lambda o: o.stichwort[0].upper())}
    return render(request, 'stichworte/stichwort_list.html', {'stichworte': stichworte})

def stichwort_detail(request, stichwort):
    stichwort = Stichwort.objects.get(stichwort=stichwort)
    stichwort.erklaerung = render_textabschnitte(stichwort.stichworterklaerung_set.order_by("order"))
    stichwort.vorgaben = stichwort.vorgabe_set.all()
    return render(request, "stichworte/stichwort_detail.html", {'stichwort': stichwort})
