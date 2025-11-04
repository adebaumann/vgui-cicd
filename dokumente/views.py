from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Dokument, Vorgabe, VorgabeKurztext, VorgabeLangtext, Checklistenfrage
from abschnitte.utils import render_textabschnitte

from datetime import date
import parsedatetime

calendar=parsedatetime.Calendar()


def standard_list(request):
    dokumente = Dokument.objects.all()
    return render(request, 'standards/standard_list.html',
                  {'dokumente': dokumente}
                  )


def standard_detail(request, nummer,check_date=""):
    standard = get_object_or_404(Dokument, nummer=nummer)

    if check_date:
        check_date = calendar.parseDT(check_date)[0].date()
        standard.history = True
    else:
        check_date = date.today()
        standard.history = False
    standard.check_date=check_date
    vorgaben = list(standard.vorgaben.order_by("thema","nummer").select_related("thema","dokument"))  # convert queryset to list so we can attach attributes

    standard.geltungsbereich_html = render_textabschnitte(standard.geltungsbereich_set.order_by("order").select_related("abschnitttyp"))
    standard.einleitung_html=render_textabschnitte(standard.einleitung_set.order_by("order"))
    for vorgabe in vorgaben:
        # Prepare Kurztext HTML
        vorgabe.kurztext_html = render_textabschnitte(vorgabe.vorgabekurztext_set.order_by("order").select_related("abschnitttyp","abschnitt"))
        vorgabe.langtext_html = render_textabschnitte(vorgabe.vorgabelangtext_set.order_by("order").select_related("abschnitttyp","abschnitt"))
        vorgabe.long_status=vorgabe.get_status(check_date,verbose=True)
        vorgabe.relevanzset=list(vorgabe.relevanz.all())

        referenz_items = []
        for r in vorgabe.referenzen.all():
            referenz_items.append(r.Path())
        vorgabe.referenzpfade = referenz_items

    return render(request, 'standards/standard_detail.html', {
        'standard': standard,
        'vorgaben': vorgaben,
    })


def standard_checkliste(request, nummer):
    standard = get_object_or_404(Dokument, nummer=nummer)
    vorgaben = list(standard.vorgaben.all())
    return render(request, 'standards/standard_checkliste.html', {
        'standard': standard,
        'vorgaben': vorgaben,
    })


def is_staff_user(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff_user)
def incomplete_vorgaben(request):
    """
    Show table of all Vorgaben with completeness status:
    - References (✓ or ✗)
    - Stichworte (✓ or ✗)
    - Text (✓ or ✗)
    - Checklistenfragen (✓ or ✗)
    """
    # Get all active Vorgaben
    all_vorgaben = Vorgabe.objects.all().select_related('dokument', 'thema').prefetch_related(
        'referenzen', 'stichworte', 'checklistenfragen', 'vorgabekurztext_set', 'vorgabelangtext_set'
    )
    
    # Build table data
    vorgaben_data = []
    for vorgabe in all_vorgaben:
        has_references = vorgabe.referenzen.exists()
        has_stichworte = vorgabe.stichworte.exists()
        has_kurztext = vorgabe.vorgabekurztext_set.exists()
        has_langtext = vorgabe.vorgabelangtext_set.exists()
        has_text = has_kurztext or has_langtext
        has_checklistenfragen = vorgabe.checklistenfragen.exists()
        
        # Only include Vorgaben that are incomplete in at least one way
        if not (has_references and has_stichworte and has_text and has_checklistenfragen):
            vorgaben_data.append({
                'vorgabe': vorgabe,
                'has_references': has_references,
                'has_stichworte': has_stichworte,
                'has_text': has_text,
                'has_checklistenfragen': has_checklistenfragen,
                'is_complete': has_references and has_stichworte and has_text and has_checklistenfragen
            })
    
    # Sort by document number and Vorgabe number
    vorgaben_data.sort(key=lambda x: (x['vorgabe'].dokument.nummer, x['vorgabe'].Vorgabennummer()))
    
    return render(request, 'standards/incomplete_vorgaben.html', {
        'vorgaben_data': vorgaben_data,
    })
