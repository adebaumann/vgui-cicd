from django.shortcuts import render, get_object_or_404
from .models import Standard
from abschnitte.utils import render_textabschnitte

from datetime import date
import parsedatetime

calendar=parsedatetime.Calendar()


def standard_list(request):
    standards = Standard.objects.all()
    return render(request, 'standards/standard_list.html',
                  {'standards': standards}
                  )


def standard_detail(request, nummer,check_date=""):
    standard = get_object_or_404(Standard, nummer=nummer)

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
    standard = get_object_or_404(Standard, nummer=nummer)
    vorgaben = list(standard.vorgaben.all())
    return render(request, 'standards/standard_checkliste.html', {
        'standard': standard,
        'vorgaben': vorgaben,
    })


