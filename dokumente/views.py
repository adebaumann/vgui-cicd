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
    Show lists of incomplete Vorgaben:
    1. Ones with no references
    2. Ones with no Stichworte
    3. Ones without Kurz- or Langtext
    4. Ones without Checklistenfragen
    """
    # Get all active Vorgaben
    all_vorgaben = Vorgabe.objects.all().select_related('dokument', 'thema')
    
    # 1. Vorgaben with no references
    no_references = [v for v in all_vorgaben if not v.referenzen.exists()]
    
    # 2. Vorgaben with no Stichworte
    no_stichworte = [v for v in all_vorgaben if not v.stichworte.exists()]
    
    # 3. Vorgaben without Kurz- or Langtext
    no_text = []
    for vorgabe in all_vorgaben:
        has_kurztext = VorgabeKurztext.objects.filter(abschnitt=vorgabe).exists()
        has_langtext = VorgabeLangtext.objects.filter(abschnitt=vorgabe).exists()

        if not has_kurztext and not has_langtext:
            no_text.append(vorgabe)
    
    # 4. Vorgaben without Checklistenfragen
    no_checklistenfragen = [v for v in all_vorgaben if not v.checklistenfragen.exists()]
    
    return render(request, 'standards/incomplete_vorgaben.html', {
        'no_references': no_references,
        'no_stichworte': no_stichworte,
        'no_text': no_text,
        'no_checklistenfragen': no_checklistenfragen,
    })
