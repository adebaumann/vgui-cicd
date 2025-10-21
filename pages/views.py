from django.shortcuts import render
from abschnitte.utils import render_textabschnitte
from standards.models import Dokument, VorgabeLangtext, VorgabeKurztext, Geltungsbereich
from itertools import groupby
import datetime

def startseite(request):
    standards=list(Dokument.objects.all())
    return render(request, 'startseite.html', {"standards":standards,})

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
        print (result)
        return render(request,"results.html",{"suchbegriff":suchbegriff,"resultat":result})

