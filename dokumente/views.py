from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Dokument, Vorgabe, VorgabeKurztext, VorgabeLangtext, Checklistenfrage, VorgabeComment
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
        
        # Add comment count
        if request.user.is_authenticated:
            if request.user.is_staff:
                vorgabe.comment_count = vorgabe.comments.count()
            else:
                vorgabe.comment_count = vorgabe.comments.filter(user=request.user).count()
        else:
            vorgabe.comment_count = 0

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


def standard_json(request, nummer):
    """
    Export a single Dokument as JSON
    """
    # Get the document with all related data
    dokument = get_object_or_404(
        Dokument.objects.prefetch_related(
            'autoren', 'pruefende', 'vorgaben__thema', 
            'vorgaben__referenzen', 'vorgaben__stichworte',
            'vorgaben__checklistenfragen', 'vorgaben__vorgabekurztext_set',
            'vorgaben__vorgabelangtext_set', 'geltungsbereich_set',
            'einleitung_set', 'changelog__autoren'
        ),
        nummer=nummer
    )

    # Build document structure (reusing logic from export_json command)
    doc_data = {
        "Typ": dokument.dokumententyp.name if dokument.dokumententyp else "",
        "Nummer": dokument.nummer,
        "Name": dokument.name,
        "Autoren": [autor.name for autor in dokument.autoren.all()],
        "Pruefende": [pruefender.name for pruefender in dokument.pruefende.all()],
        "Gueltigkeit": {
            "Von": dokument.gueltigkeit_von.strftime("%Y-%m-%d") if dokument.gueltigkeit_von else "",
            "Bis": dokument.gueltigkeit_bis.strftime("%Y-%m-%d") if dokument.gueltigkeit_bis else None
        },
        "SignaturCSO": dokument.signatur_cso,
        "Geltungsbereich": {},
        "Einleitung": {},
        "Ziel": "",
        "Grundlagen": "",
        "Changelog": [],
        "Anhänge": dokument.anhaenge,
        "Verantwortlich": "Information Security Management BIT",
        "Klassifizierung": None,
        "Glossar": {},
        "Vorgaben": []
    }

    # Process Geltungsbereich sections
    geltungsbereich_sections = []
    for gb in dokument.geltungsbereich_set.all().order_by('order'):
        geltungsbereich_sections.append({
            "typ": gb.abschnitttyp.abschnitttyp if gb.abschnitttyp else "text",
            "inhalt": gb.inhalt
        })
    
    if geltungsbereich_sections:
        doc_data["Geltungsbereich"] = {
            "Abschnitt": geltungsbereich_sections
        }

    # Process Einleitung sections
    einleitung_sections = []
    for ei in dokument.einleitung_set.all().order_by('order'):
        einleitung_sections.append({
            "typ": ei.abschnitttyp.abschnitttyp if ei.abschnitttyp else "text",
            "inhalt": ei.inhalt
        })
    
    if einleitung_sections:
        doc_data["Einleitung"] = {
            "Abschnitt": einleitung_sections
        }

    # Process Changelog entries
    changelog_entries = []
    for cl in dokument.changelog.all().order_by('-datum'):
        changelog_entries.append({
            "Datum": cl.datum.strftime("%Y-%m-%d"),
            "Autoren": [autor.name for autor in cl.autoren.all()],
            "Aenderung": cl.aenderung
        })
    
    doc_data["Changelog"] = changelog_entries

    # Process Vorgaben for this document
    vorgaben = dokument.vorgaben.all().order_by('order')
    
    for vorgabe in vorgaben:
        # Get Kurztext and Langtext sections
        kurztext_sections = []
        for kt in vorgabe.vorgabekurztext_set.all().order_by('order'):
            kurztext_sections.append({
                "typ": kt.abschnitttyp.abschnitttyp if kt.abschnitttyp else "text",
                "inhalt": kt.inhalt
            })
        
        langtext_sections = []
        for lt in vorgabe.vorgabelangtext_set.all().order_by('order'):
            langtext_sections.append({
                "typ": lt.abschnitttyp.abschnitttyp if lt.abschnitttyp else "text", 
                "inhalt": lt.inhalt
            })

        # Build text structures following Langtext pattern
        kurztext = {
            "Abschnitt": kurztext_sections if kurztext_sections else []
        } if kurztext_sections else {}
        langtext = {
            "Abschnitt": langtext_sections if langtext_sections else []
        } if langtext_sections else {}

        # Get references and keywords
        referenzen = [f"{ref.name_nummer}: {ref.name_text}" if ref.name_text else ref.name_nummer for ref in vorgabe.referenzen.all()]
        stichworte = [stw.stichwort for stw in vorgabe.stichworte.all()]
        
        # Get checklist questions
        checklistenfragen = [cf.frage for cf in vorgabe.checklistenfragen.all()]

        vorgabe_data = {
            "Nummer": str(vorgabe.nummer),
            "Titel": vorgabe.titel,
            "Thema": vorgabe.thema.name if vorgabe.thema else "",
            "Kurztext": kurztext,
            "Langtext": langtext,
            "Referenz": referenzen,
            "Gueltigkeit": {
                "Von": vorgabe.gueltigkeit_von.strftime("%Y-%m-%d") if vorgabe.gueltigkeit_von else "",
                "Bis": vorgabe.gueltigkeit_bis.strftime("%Y-%m-%d") if vorgabe.gueltigkeit_bis else None
            },
            "Checklistenfragen": checklistenfragen,
            "Stichworte": stichworte
        }
        
        doc_data["Vorgaben"].append(vorgabe_data)

    # Return JSON response
    return JsonResponse(doc_data, json_dumps_params={'indent': 2, 'ensure_ascii': False}, encoder=DjangoJSONEncoder)


@login_required
def get_vorgabe_comments(request, vorgabe_id):
    """Get comments for a specific Vorgabe"""
    vorgabe = get_object_or_404(Vorgabe, id=vorgabe_id)
    
    if request.user.is_staff:
        # Staff can see all comments
        comments = vorgabe.comments.all().select_related('user')
    else:
        # Regular users can only see their own comments
        comments = vorgabe.comments.filter(user=request.user).select_related('user')
    
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'text': comment.text,
            'user': comment.user.username,
            'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M'),
            'updated_at': comment.updated_at.strftime('%d.%m.%Y %H:%M'),
            'is_own': comment.user == request.user
        })
    
    return JsonResponse({'comments': comments_data})


@require_POST
@login_required
def add_vorgabe_comment(request, vorgabe_id):
    """Add a new comment to a Vorgabe"""
    vorgabe = get_object_or_404(Vorgabe, id=vorgabe_id)
    
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        
        if not text:
            return JsonResponse({'error': 'Kommentar darf nicht leer sein'}, status=400)
        
        comment = VorgabeComment.objects.create(
            vorgabe=vorgabe,
            user=request.user,
            text=text
        )
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'text': comment.text,
                'user': comment.user.username,
                'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M'),
                'updated_at': comment.updated_at.strftime('%d.%m.%Y %H:%M'),
                'is_own': True
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Ungültige Daten'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@login_required
def delete_vorgabe_comment(request, comment_id):
    """Delete a comment (only own comments or staff can delete)"""
    comment = get_object_or_404(VorgabeComment, id=comment_id)
    
    # Check if user can delete this comment
    if comment.user != request.user and not request.user.is_staff:
        return JsonResponse({'error': 'Keine Berechtigung zum Löschen dieses Kommentars'}, status=403)
    
    try:
        comment.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
