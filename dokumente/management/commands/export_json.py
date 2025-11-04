from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
import json
from datetime import datetime
from dokumente.models import Dokument, Vorgabe, VorgabeKurztext, VorgabeLangtext, Checklistenfrage


class Command(BaseCommand):
    help = 'Export all dokumente as JSON using R0066.json format as reference'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: stdout)',
        )

    def handle(self, *args, **options):
        # Get all active documents
        dokumente = Dokument.objects.filter(aktiv=True).prefetch_related(
            'autoren', 'pruefende', 'vorgaben__thema', 
            'vorgaben__referenzen', 'vorgaben__stichworte',
            'vorgaben__checklistenfragen', 'vorgaben__vorgabekurztext_set',
            'vorgaben__vorgabelangtext_set', 'geltungsbereich_set',
            'einleitung_set', 'changelog__autoren'
        ).order_by('nummer')

        result = {
            "Vorgabendokument": {
                "Typ": "Standard IT-Sicherheit",
                "Nummer": "",  # Will be set per document
                "Name": "",  # Will be set per document  
                "Autoren": [],  # Will be set per document
                "Pruefende": [],  # Will be set per document
                "Geltungsbereich": {
                    "Abschnitt": []
                },
                "Ziel": "",
                "Grundlagen": "",
                "Changelog": [],
                "Anhänge": [],
                "Verantwortlich": "Information Security Management BIT",
                "Klassifizierung": None,
                "Glossar": {},
                "Vorgaben": []
            }
        }

        output_data = []

        for dokument in dokumente:
            # Build document structure
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
                # Get Kurztext and Langtext
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

            output_data.append(doc_data)

        # Output the data
        json_output = json.dumps(output_data, cls=DjangoJSONEncoder, indent=2, ensure_ascii=False)
        
        if options['output']:
            with open(options['output'], 'w', encoding='utf-8') as f:
                f.write(json_output)
            self.stdout.write(self.style.SUCCESS(f'JSON exported to {options["output"]}'))
        else:
            self.stdout.write(json_output)