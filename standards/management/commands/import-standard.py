# Standards/management/commands/import_standard.py
import re
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from standards.models import (
    Standard,
    Dokumententyp,
    Thema,
    Vorgabe,
    VorgabeKurztext,
    VorgabeLangtext,
    Geltungsbereich,
    Einleitung,           # <-- make sure this model exists as a Textabschnitt subclass
    Checklistenfrage,
)
from abschnitte.models import AbschnittTyp
from stichworte.models import Stichwort


class Command(BaseCommand):
    help = (
        "Import a security standard from a structured text file.\n"
        "Supports Einleitung, Geltungsbereich, Vorgaben (Kurztext/Langtext with AbschnittTyp), "
        "Stichworte (comma-separated), Checklistenfragen, dry-run, verbose, and purge."
    )

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str, help="Path to the plaintext file")
        parser.add_argument("--nummer", required=True, help="Standard number (e.g., STD-001)")
        parser.add_argument("--name", required=True, help='Standard name (e.g., "IT-Sicherheit Container")')
        parser.add_argument("--dokumententyp", required=True, help='Dokumententyp name (e.g., "IT-Sicherheit")')
        parser.add_argument("--gueltigkeit_von", default=None, help="Start date (YYYY-MM-DD)")
        parser.add_argument("--gueltigkeit_bis", default=None, help="End date (YYYY-MM-DD)")
        parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without saving to DB")
        parser.add_argument("--verbose", action="store_true", help="Verbose output for dry run")
        parser.add_argument("--purge", action="store_true", help="Delete existing Einleitung/Geltungsbereich/Vorgaben first")

    # normalize header: "liste-ungeordnet" -> "liste ungeordnet"
    @staticmethod
    def _norm_header(h: str) -> str:
        return h.lower().replace("-", " ").strip()

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        verbose = options["verbose"]
        purge = options["purge"]

        file_path = Path(options["file_path"])
        if not file_path.exists():
            raise CommandError(f"File {file_path} does not exist")

        nummer = options["nummer"]
        name = options["name"]
        dokumententyp_name = options["dokumententyp"]

        try:
            dokumententyp = Dokumententyp.objects.get(name=dokumententyp_name)
        except Dokumententyp.DoesNotExist:
            raise CommandError(f"Dokumententyp '{dokumententyp_name}' does not exist")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run: no database changes will be made."))

        # get or create Standard (we want a real instance even in purge to count existing rows)
        standard, created = Standard.objects.get_or_create(
            nummer=nummer,
            defaults={
                "dokumententyp": dokumententyp,
                "name": name,
                "gueltigkeit_von": options["gueltigkeit_von"],
                "gueltigkeit_bis": options["gueltigkeit_bis"],
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Standard {nummer} – {name}"))
        else:
            self.stdout.write(self.style.WARNING(f"Standard {nummer} already exists; content may be updated."))

        # purge (Einleitung + Geltungsbereich + Vorgaben cascade)
        if purge:
            qs_vorgaben = standard.vorgaben.all()
            qs_check = Checklistenfrage.objects.filter(vorgabe__in=qs_vorgaben)
            qs_kurz = VorgabeKurztext.objects.filter(abschnitt__in=qs_vorgaben)
            qs_lang = VorgabeLangtext.objects.filter(abschnitt__in=qs_vorgaben)
            qs_gb = Geltungsbereich.objects.filter(geltungsbereich=standard)
            qs_einl = Einleitung.objects.filter(einleitung=standard)

            c_vorgaben = qs_vorgaben.count()
            c_check = qs_check.count()
            c_kurz = qs_kurz.count()
            c_lang = qs_lang.count()
            c_gb = qs_gb.count()
            c_einl = qs_einl.count()

            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f"[DRY RUN] Would purge: {c_einl} Einleitung-Abschnitte, "
                    f"{c_gb} Geltungsbereich-Abschnitte, {c_vorgaben} Vorgaben "
                    f"({c_kurz} Kurztext, {c_lang} Langtext, {c_check} Checklistenfragen)."
                ))
            else:
                deleted_einl = qs_einl.delete()[0]
                deleted_gb = qs_gb.delete()[0]
                deleted_vorgaben = qs_vorgaben.delete()[0]
                self.stdout.write(self.style.SUCCESS(
                    f"Purged {deleted_einl} Einleitung, {deleted_gb} Geltungsbereich, "
                    f"{deleted_vorgaben} Vorgaben (incl. Kurz/Lang/Checklistenfragen)."
                ))

        # read and split file
        content = file_path.read_text(encoding="utf-8")
        blocks = re.split(r"^>>>", content, flags=re.MULTILINE)
        blocks = [b.strip() for b in blocks if b.strip()]

        # state
        abschnittstyp_names = {"text", "liste geordnet", "liste ungeordnet"}
        current_context = "geltungsbereich"  # default before first Vorgabe

        einleitung_sections = []       # list of {inhalt, typ: AbschnittTyp}
        geltungsbereich_sections = []  # list of {inhalt, typ: AbschnittTyp}

        current_vorgabe = None
        vorgaben_data = []  # each: {thema, titel, nummer, kurztext:[{inhalt,typ}], langtext:[{inhalt,typ}], stichworte:set(), checkliste:[str]}

        for block in blocks:
            lines = block.splitlines()
            header = lines[0].strip()
            text = "\n".join(lines[1:]).strip()
            header_norm = self._norm_header(header)

            # resolve AbschnittTyp if this is a section block
            abschnitt_typ = None
            if header_norm in abschnittstyp_names:
                try:
                    abschnitt_typ = AbschnittTyp.objects.get(abschnitttyp=header_norm)
                except AbschnittTyp.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"AbschnittTyp '{header_norm}' not found; defaulting to 'text'."
                    ))
                    abschnitt_typ = AbschnittTyp.objects.get(abschnitttyp="text")

            # contexts
            if header_norm == "einleitung":
                current_context = "einleitung"
                continue

            if header_norm == "geltungsbereich":
                current_context = "geltungsbereich"
                continue

            if header_norm.startswith("vorgabe"):
                # save previous
                if current_vorgabe:
                    vorgaben_data.append(current_vorgabe)

                parts = header.split(" ", 1)
                thema_name = parts[1].strip() if len(parts) > 1 else ""
                current_vorgabe = {
                    "thema": thema_name,
                    "titel": "",
                    "nummer": None,
                    "kurztext": [],
                    "langtext": [],
                    "stichworte": set(),
                    "checkliste": [],
                }
                current_context = "vorgabe_none"
                continue

            if header_norm.startswith("titel") and current_vorgabe:
                # inline title or next text block
                inline = header[len("Titel"):].strip() if header.startswith("Titel") else ""
                title_value = inline or text
                current_vorgabe["titel"] = title_value
                continue

            if header_norm.startswith("nummer") and current_vorgabe:
                m = re.search(r"\d+", header)
                if m:
                    current_vorgabe["nummer"] = int(m.group())
                current_context = "vorgabe_none"
                continue

            if header_norm == "kurztext":
                current_context = "vorgabe_kurztext"
                continue

            if header_norm == "langtext":
                current_context = "vorgabe_langtext"
                continue

            if header_norm.startswith("stichworte") and current_vorgabe:
                inline = header[len("Stichworte"):].strip() if header.startswith("Stichworte") else ""
                kw_str = inline or text
                if kw_str:
                    for k in kw_str.split(","):
                        k = k.strip()
                        if k:
                            current_vorgabe["stichworte"].add(k)
                else:
                    current_context = "vorgabe_stichworte"
                continue

            if header_norm == "checkliste" and current_vorgabe:
                if text:
                    current_vorgabe["checkliste"].extend([q.strip() for q in text.splitlines() if q.strip()])
                else:
                    current_context = "vorgabe_checkliste"
                continue

            # Abschnitt content blocks
            if header_norm in abschnittstyp_names:
                section = {"inhalt": text, "typ": abschnitt_typ}

                if current_context == "einleitung":
                    einleitung_sections.append(section)
                    if dry_run and verbose:
                        self.stdout.write(self.style.SUCCESS(
                            f"[DRY RUN] Einleitung Abschnitt ({section['typ']}): {text[:50]}..."
                        ))

                elif current_context == "geltungsbereich":
                    geltungsbereich_sections.append(section)
                    if dry_run and verbose:
                        self.stdout.write(self.style.SUCCESS(
                            f"[DRY RUN] Geltungsbereich Abschnitt ({section['typ']}): {text[:50]}..."
                        ))

                elif current_context == "vorgabe_kurztext" and current_vorgabe:
                    current_vorgabe["kurztext"].append(section)
                    if dry_run and verbose:
                        self.stdout.write(self.style.SUCCESS(
                            f"[DRY RUN] Vorgabe {current_vorgabe.get('nummer')} Kurztext ({section['typ']}): {text[:50]}..."
                        ))

                elif current_context == "vorgabe_langtext" and current_vorgabe:
                    current_vorgabe["langtext"].append(section)
                    if dry_run and verbose:
                        self.stdout.write(self.style.SUCCESS(
                            f"[DRY RUN] Vorgabe {current_vorgabe.get('nummer')} Langtext ({section['typ']}): {text[:50]}..."
                        ))

                elif current_context == "vorgabe_stichworte" and current_vorgabe:
                    for k in text.split(","):
                        k = k.strip()
                        if k:
                            current_vorgabe["stichworte"].add(k)
                    current_context = "vorgabe_none"

                elif current_context == "vorgabe_checkliste" and current_vorgabe:
                    current_vorgabe["checkliste"].extend([q.strip() for q in text.splitlines() if q.strip()])
                    current_context = "vorgabe_none"

        # append last vorgabe
        if current_vorgabe:
            vorgaben_data.append(current_vorgabe)

        # === SAVE: Einleitung ===
        for sektion in einleitung_sections:
            if dry_run:
                self.stdout.write(self.style.SUCCESS(
                    f"[DRY RUN] Would create Einleitung Abschnitt ({sektion['typ']}): {sektion['inhalt'][:50]}..."
                ))
            else:
                Einleitung.objects.create(
                    einleitung=standard,
                    abschnitttyp=sektion["typ"],
                    inhalt=sektion["inhalt"],
                )

        # === SAVE: Geltungsbereich ===
        for sektion in geltungsbereich_sections:
            if dry_run:
                self.stdout.write(self.style.SUCCESS(
                    f"[DRY RUN] Would create Geltungsbereich Abschnitt ({sektion['typ']}): {sektion['inhalt'][:50]}..."
                ))
            else:
                Geltungsbereich.objects.create(
                    geltungsbereich=standard,
                    abschnitttyp=sektion["typ"],
                    inhalt=sektion["inhalt"],
                )

        # === SAVE: Vorgaben and children ===
        for v in vorgaben_data:
            try:
                thema = Thema.objects.get(name=v["thema"])
            except Thema.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"Thema '{v['thema']}' not found, skipping Vorgabe {v['nummer']}"
                ))
                continue

            if dry_run:
                self.stdout.write(self.style.SUCCESS(
                    f"[DRY RUN] Would create Vorgabe {v['nummer']}: '{v['titel']}' (Thema: {v['thema']})"
                ))
                if v["stichworte"]:
                    self.stdout.write(self.style.SUCCESS(
                        f"[DRY RUN]   Stichworte: {', '.join(sorted(v['stichworte']))}"
                    ))
                if v["checkliste"]:
                    for frage in v["checkliste"]:
                        self.stdout.write(self.style.SUCCESS(f"[DRY RUN]   Checkliste: {frage}"))
                for s in v["kurztext"]:
                    self.stdout.write(self.style.SUCCESS(
                        f"[DRY RUN]   Kurztext ({s['typ']}): {s['inhalt'][:50]}..."
                    ))
                for s in v["langtext"]:
                    self.stdout.write(self.style.SUCCESS(
                        f"[DRY RUN]   Langtext ({s['typ']}): {s['inhalt'][:50]}..."
                    ))
            else:
                vorgabe = Vorgabe.objects.create(
                    nummer=v["nummer"],
                    dokument=standard,
                    thema=thema,
                    titel=v["titel"],
                    gueltigkeit_von=timezone.now().date(),
                )

                # Stichworte
                for kw in sorted(v["stichworte"]):
                    stw, _ = Stichwort.objects.get_or_create(stichwort=kw)
                    vorgabe.stichworte.add(stw)

                # Checklistenfragen
                for frage in v["checkliste"]:
                    Checklistenfrage.objects.create(vorgabe=vorgabe, frage=frage)

                # Kurztext sections
                for s in v["kurztext"]:
                    VorgabeKurztext.objects.create(
                        abschnitt=vorgabe,
                        abschnitttyp=s["typ"],
                        inhalt=s["inhalt"],
                    )

                # Langtext sections
                for s in v["langtext"]:
                    VorgabeLangtext.objects.create(
                        abschnitt=vorgabe,
                        abschnitttyp=s["typ"],
                        inhalt=s["inhalt"],
                    )

        self.stdout.write(self.style.SUCCESS(
            "Dry run complete" if dry_run else f"Imported standard {nummer} – {name} with {len(vorgaben_data)} Vorgaben"
        ))

