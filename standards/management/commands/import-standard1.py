# Standards/management/commands/import_standard.py
import re
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from standards.models import (
    Standard,
    Vorgabe,
    VorgabeKurztext,
    VorgabeLangtext,
    Geltungsbereich,
    Dokumententyp,
    Thema,
)
from abschnitte.models import AbschnittTyp


class Command(BaseCommand):
    help = "Import a security standard from a structured text file"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str, help="Path to the plaintext file")
        parser.add_argument("--nummer", required=True, help="Standard number (e.g., STD-001)")
        parser.add_argument("--name", required=True, help="Standard name (e.g., IT-Sicherheit Container)")
        parser.add_argument("--dokumententyp", required=True, help="Dokumententyp name")
        parser.add_argument("--gueltigkeit_von", default=None, help="Start date (YYYY-MM-DD)")
        parser.add_argument("--gueltigkeit_bis", default=None, help="End date (YYYY-MM-DD)")
        parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without saving to the database")
        parser.add_argument("--verbose", action="store_true", help="Verbose output for dry run")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        verbose = options["verbose"]
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
            self.stdout.write(self.style.WARNING("Dry run: no database changes will be made"))

        # Create or get the Standard
        if dry_run:
            standard = {"nummer": nummer, "name": name, "dokumententyp": dokumententyp}
        else:
            standard, created = Standard.objects.get_or_create(
                nummer=nummer,
                defaults={
                    "dokumententyp": dokumententyp,
                    "name": name,
                    "gueltigkeit_von": options["gueltigkeit_von"],
                    "gueltigkeit_bis": options["gueltigkeit_bis"],
                },
            )
            if not created:
                self.stdout.write(self.style.WARNING(f"Standard {nummer} already exists, updating content"))

        # Read and parse the file
        content = file_path.read_text(encoding="utf-8")
        blocks = re.split(r"^>>>", content, flags=re.MULTILINE)
        blocks = [b.strip() for b in blocks if b.strip()]

        geltungsbereich_sections = []
        current_vorgabe = None
        vorgaben_data = []
        current_context = "geltungsbereich"
        abschnittstyp_headers = ["text", "liste geordnet", "liste ungeordnet"]

        for block in blocks:
            lines = block.splitlines()
            header = lines[0].strip()
            text = "\n".join(lines[1:]).strip()
            header_lower = header.lower()

            # Determine AbschnittTyp if applicable
            abschnitt_typ = None
            if header_lower in abschnittstyp_headers:
                try:
                    abschnitt_typ = AbschnittTyp.objects.get(abschnitttyp=header_lower)
                except AbschnittTyp.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"AbschnittTyp '{header_lower}' not found, defaulting to 'text'"))
                    abschnitt_typ = AbschnittTyp.objects.get(abschnitttyp="text")

            if header_lower == "geltungsbereich":
                current_context = "geltungsbereich"

            elif header_lower.startswith("vorgabe"):
                if current_vorgabe:
                    vorgaben_data.append(current_vorgabe)
                thema_name = header.split(" ", 1)[1].strip()
                current_vorgabe = {"thema": thema_name, "titel": "", "nummer": None, "kurztext": [], "langtext": []}
                current_context = "vorgabe_none"

            elif header_lower.startswith("titel") and current_vorgabe:
                current_vorgabe["titel"] = text

            elif header_lower.startswith("nummer") and current_vorgabe:
                nummer_match = re.search(r"\d+", header)
                if nummer_match:
                    current_vorgabe["nummer"] = int(nummer_match.group())
                current_context = "vorgabe_none"

            elif header_lower == "kurztext":
                current_context = "vorgabe_kurztext"

            elif header_lower == "langtext":
                current_context = "vorgabe_langtext"

            elif header_lower in abschnittstyp_headers:
                abschnitt = {"inhalt": text, "typ": abschnitt_typ}
                if current_context == "geltungsbereich":
                    geltungsbereich_sections.append(abschnitt)
                    if dry_run and verbose:
                        self.stdout.write(self.style.SUCCESS(f"[DRY RUN] Geltungsbereich Abschnitt (Abschnittstyp: {abschnitt_typ}): {text[:50]}..."))
                elif current_context == "vorgabe_kurztext" and current_vorgabe:
                    current_vorgabe["kurztext"].append(abschnitt)
                    if dry_run and verbose:
                        self.stdout.write(self.style.SUCCESS(f"[DRY RUN] Vorgabe {current_vorgabe['nummer']} Kurztext Abschnitt (Abschnittstyp: {abschnitt_typ}): {text[:50]}..."))
                elif current_context == "vorgabe_langtext" and current_vorgabe:
                    current_vorgabe["langtext"].append(abschnitt)
                    if dry_run and verbose:
                        self.stdout.write(self.style.SUCCESS(f"[DRY RUN] Vorgabe {current_vorgabe['nummer']} Langtext Abschnitt (Abschnittstyp: {abschnitt_typ}): {text[:50]}..."))

        if current_vorgabe:
            vorgaben_data.append(current_vorgabe)

        # Save Geltungsbereich
        for sektion in geltungsbereich_sections:
            if dry_run:
                self.stdout.write(self.style.SUCCESS(f"[DRY RUN] Would create Geltungsbereich Abschnitt (Abschnittstyp: {sektion['typ']}): {sektion['inhalt'][:50]}..."))
            else:
                Geltungsbereich.objects.create(
                    geltungsbereich=standard,
                    abschnitttyp=sektion["typ"],
                    inhalt=sektion["inhalt"],
                )

        # Save Vorgaben
        for v in vorgaben_data:
            try:
                thema = Thema.objects.get(name=v["thema"])
            except Thema.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Thema '{v['thema']}' not found, skipping Vorgabe {v['nummer']}"))
                continue

            if dry_run:
                self.stdout.write(self.style.SUCCESS(f"[DRY RUN] Would create Vorgabe {v['nummer']}: '{v['titel']}' (Thema: {v['thema']})"))
                for sektion in v["kurztext"]:
                    self.stdout.write(self.style.SUCCESS(f"[DRY RUN]   Kurztext Abschnitt (Abschnittstyp: {sektion['typ']}): {sektion['inhalt'][:50]}..."))
                for sektion in v["langtext"]:
                    self.stdout.write(self.style.SUCCESS(f"[DRY RUN]   Langtext Abschnitt (Abschnittstyp: {sektion['typ']}): {sektion['inhalt'][:50]}..."))
            else:
                vorgabe = Vorgabe.objects.create(
                    nummer=v["nummer"],
                    dokument=standard,
                    thema=thema,
                    titel=v["titel"],
                    gueltigkeit_von=timezone.now().date(),
                )
                for sektion in v["kurztext"]:
                    VorgabeKurztext.objects.create(abschnitt=vorgabe, abschnitttyp=sektion["typ"], inhalt=sektion["inhalt"])
                for sektion in v["langtext"]:
                    VorgabeLangtext.objects.create(abschnitt=vorgabe, abschnitttyp=sektion["typ"], inhalt=sektion["inhalt"])

        self.stdout.write(self.style.SUCCESS(
            f"{'Dry run complete' if dry_run else f'Imported standard {standard} with {len(vorgaben_data)} Vorgaben'}"
        ))

