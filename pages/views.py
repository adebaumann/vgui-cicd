from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.utils.html import escape
import re
from abschnitte.utils import render_textabschnitte
from dokumente.models import Dokument, VorgabeLangtext, VorgabeKurztext, Geltungsbereich, Vorgabe
from itertools import groupby
import datetime


def startseite(request):
    standards=list(Dokument.objects.filter(aktiv=True))
    return render(request, 'startseite.html', {"dokumente":standards,})

def validate_search_input(search_term):
    """
    Validate search input to prevent SQL injection and XSS
    """
    if not search_term:
        raise ValidationError("Suchbegriff darf nicht leer sein")
    
    # Remove any HTML tags to prevent XSS
    search_term = re.sub(r'<[^>]*>', '', search_term)
    
    # Allow only alphanumeric characters, spaces, and basic punctuation
    # This prevents SQL injection and other malicious input while allowing useful characters
    if not re.match(r'^[a-zA-Z0-9äöüÄÖÜß\s\-\.\,\:\;\!\?\(\)\[\]\{\}\"\']+$', search_term):
        raise ValidationError("Ungültige Zeichen im Suchbegriff")
    
    # Limit length to prevent DoS attacks
    if len(search_term) > 200:
        raise ValidationError("Suchbegriff ist zu lang")
    
    return search_term.strip()

def search(request):
    if request.method == "GET":
        return render(request, 'search.html')
    elif request.method == "POST":
        raw_search_term = request.POST.get("q", "")
        
        try:
            suchbegriff = validate_search_input(raw_search_term)
        except ValidationError as e:
            return render(request, 'search.html', {
                'error_message': str(e),
                'search_term': escape(raw_search_term)
            })
        
        # Escape the search term for display in templates
        safe_search_term = escape(suchbegriff)
        result= {"all": {}}
        qs = VorgabeKurztext.objects.filter(inhalt__icontains=suchbegriff).exclude(abschnitt__gueltigkeit_bis__lt=datetime.date.today())
        result["kurztext"] = {k: [o.abschnitt for o in g] for k, g in groupby(qs, key=lambda o: o.abschnitt.dokument)}
        qs = VorgabeLangtext.objects.filter(inhalt__icontains=suchbegriff).exclude(abschnitt__gueltigkeit_bis__lt=datetime.date.today())
        result['langtext']=  {k: [o.abschnitt for o in g] for k, g in groupby(qs, key=lambda o: o.abschnitt.dokument)}
        qs = Vorgabe.objects.filter(titel__icontains=suchbegriff).exclude(gueltigkeit_bis__lt=datetime.date.today())
        result['titel']= {k: list(g) for k, g in groupby(qs, key=lambda o: o.dokument)}
        for r in result.keys():
            for s in result[r].keys():
                if r == 'titel':
                    result["all"][s] = set(result["all"].get(s, set()) | set(result[r][s]))
                else:
                    result["all"][s] = set(result["all"].get(s, set()) | set(result[r][s]))
        result["geltungsbereich"]={}
        geltungsbereich=set(list([x.geltungsbereich for x in Geltungsbereich.objects.filter(inhalt__icontains=suchbegriff)]))
        for s in geltungsbereich:
            result["geltungsbereich"][s]=render_textabschnitte(s.geltungsbereich_set.order_by("order"))

        return render(request,"results.html",{"suchbegriff":safe_search_term,"resultat":result})

