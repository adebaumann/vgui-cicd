from django.shortcuts import render
from abschnitte.utils import render_textabschnitte
from dokumente.models import Dokument, VorgabeLangtext, VorgabeKurztext, Geltungsbereich
from itertools import groupby
import datetime
import pprint

def startseite(request):
    standards=list(Dokument.objects.all())
    return render(request, 'startseite.html', {"dokumente":standards,})

def search(request):
    if request.method == "GET":
        return render(request, 'search.html')
    elif request.method == "POST":
        suchbegriff=request.POST.get("q")
        result= {"all": {}}
        qs = VorgabeKurztext.objects.filter(inhalt__contains=suchbegriff).exclude(abschnitt__gueltigkeit_bis__lt=datetime.date.today())
        result["kurztext"] = {k: [o.abschnitt for o in g] for k, g in groupby(qs, key=lambda o: o.abschnitt.dokument)}
        qs = VorgabeLangtext.objects.filter(inhalt__contains=suchbegriff).exclude(abschnitt__gueltigkeit_bis__lt=datetime.date.today())
        result['langtext']=  {k: [o.abschnitt for o in g] for k, g in groupby(qs, key=lambda o: o.abschnitt.dokument)}
        for r in result.keys():
            for s in result[r].keys():
                result["all"][s] = set(result[r][s])
        result["geltungsbereich"]={}
        geltungsbereich=set(list([x.geltungsbereich for x in Geltungsbereich.objects.filter(inhalt__contains=suchbegriff)]))
        for s in geltungsbereich:
            result["geltungsbereich"][s]=render_textabschnitte(s.geltungsbereich_set.order_by("order"))
        pprint.pp (result)
        return render(request,"results.html",{"suchbegriff":suchbegriff,"resultat":result})

