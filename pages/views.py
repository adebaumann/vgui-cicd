from django.shortcuts import render
from abschnitte.utils import render_textabschnitte
from standards.models import Standard, VorgabeLangtext, VorgabeKurztext, Geltungsbereich
from itertools import groupby
import datetime

def startseite(request):
    standards=list(Standard.objects.all())
    return render(request, 'startseite.html', {"standards":standards,})

def search(request):
    if request.method == "GET":
        return render(request, 'search.html')
    elif request.method == "POST":
        suchbegriff=request.POST.get("q")
        areas=request.POST.getlist("suchbereich[]")
        result= {}
        geltungsbereich=set()
        if "kurztext" in areas:
            qs = VorgabeKurztext.objects.filter(inhalt__contains=suchbegriff).exclude(abschnitt__gueltigkeit_bis__lt=datetime.date.today())
            result["kurztext"] = {k: [o.abschnitt for o in g] for k, g in groupby(qs, key=lambda o: o.abschnitt.dokument)}
        if "langtext" in areas:
            qs = VorgabeLangtext.objects.filter(inhalt__contains=suchbegriff).exclude(abschnitt__gueltigkeit_bis__lt=datetime.date.today())
            result['langtext']=  {k: [o.abschnitt for o in g] for k, g in groupby(qs, key=lambda o: o.abschnitt.dokument)}
        if "geltungsbereich" in areas:
            result["geltungsbereich"]={}
            geltungsbereich=set(list([x.geltungsbereich for x in Geltungsbereich.objects.filter(inhalt__contains=suchbegriff)]))
        for s in geltungsbereich:
            result["geltungsbereich"][s]=render_textabschnitte(s.geltungsbereich_set.order_by("order"))
        for r in result.keys():
            for s in result[r].keys():
                result[r][s]=set(result[r][s])
        return render(request,"results.html",{"suchbegriff":suchbegriff,"resultat":result})

