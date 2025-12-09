"""
Tests for the import-document management command.

This test suite covers:
- Basic import functionality
- Dry-run mode
- Purge functionality
- Error handling (missing file, dokumententyp, thema, abschnitttyp)
- Context switching (einleitung → geltungsbereich → vorgabe)
- Header normalization
- Vorgaben with Kurztext, Langtext, Stichworte, Checklistenfragen
- Edge cases and malformed input
"""

import os
import tempfile
from io import StringIO
from pathlib import Path
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from dokumente.models import (
    Dokumententyp,
    Dokument,
    Thema,
    Vorgabe,
    VorgabeKurztext,
    VorgabeLangtext,
    Geltungsbereich,
    Einleitung,
    Checklistenfrage,
)
from abschnitte.models import AbschnittTyp
from stichworte.models import Stichwort


class ImportDocumentCommandTestCase(TestCase):
    """Test cases for the import-document management command"""

    def setUp(self):
        """Set up test fixtures"""
        # Create required Dokumententyp
        self.dokumententyp = Dokumententyp.objects.create(
            name="IT-Sicherheit",
            verantwortliche_ve="TEST-VE"
        )

        # Create required AbschnittTyp instances
        self.text_typ = AbschnittTyp.objects.create(abschnitttyp="text")
        self.liste_geordnet_typ = AbschnittTyp.objects.create(
            abschnitttyp="liste geordnet"
        )
        self.liste_ungeordnet_typ = AbschnittTyp.objects.create(
            abschnitttyp="liste ungeordnet"
        )

        # Create test Themen
        self.thema_organisation = Thema.objects.create(
            name="Organisation",
            erklaerung="Organisatorische Anforderungen"
        )
        self.thema_technik = Thema.objects.create(
            name="Technik",
            erklaerung="Technische Anforderungen"
        )
        # Additional Themen for r009.txt example
        self.thema_informationen = Thema.objects.create(
            name="Informationen",
            erklaerung="Informationssicherheit"
        )
        self.thema_systeme = Thema.objects.create(
            name="Systeme",
            erklaerung="Systemanforderungen"
        )
        self.thema_anwendungen = Thema.objects.create(
            name="Anwendungen",
            erklaerung="Anwendungsanforderungen"
        )
        self.thema_zonen = Thema.objects.create(
            name="Zonen",
            erklaerung="Zonenanforderungen"
        )

    def create_test_file(self, content):
        """Helper to create a temporary test file with given content"""
        fd, path = tempfile.mkstemp(suffix=".txt", text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def test_basic_import_creates_document(self):
        """Test that basic import creates a document"""
        test_content = """>>>Einleitung
>>>text
This is the introduction.

>>>geltungsbereich
>>>text
This is the scope.

>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel
Test Requirement
>>>Kurztext
>>>Text
Short description.
>>>Langtext
>>>Text
Long description.
"""
        test_file = self.create_test_file(test_content)

        try:
            out = StringIO()
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-001',
                '--name', 'Test Document',
                '--dokumententyp', 'IT-Sicherheit',
                stdout=out
            )

            # Check document was created
            dokument = Dokument.objects.get(nummer='TEST-001')
            self.assertEqual(dokument.name, 'Test Document')
            self.assertEqual(dokument.dokumententyp, self.dokumententyp)

            # Check output message
            output = out.getvalue()
            self.assertIn('Created Document TEST-001', output)
            self.assertIn('Imported document TEST-001', output)

        finally:
            os.unlink(test_file)

    def test_import_creates_einleitung(self):
        """Test that Einleitung sections are created"""
        test_content = """>>>Einleitung
>>>text
This is the introduction text.

>>>geltungsbereich
>>>text
Scope text.
"""
        test_file = self.create_test_file(test_content)

        try:
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-002',
                '--name', 'Test Document 2',
                '--dokumententyp', 'IT-Sicherheit'
            )

            dokument = Dokument.objects.get(nummer='TEST-002')
            einleitung = Einleitung.objects.filter(einleitung=dokument)
            self.assertEqual(einleitung.count(), 1)
            self.assertEqual(einleitung.first().inhalt, 'This is the introduction text.')
            self.assertEqual(einleitung.first().abschnitttyp, self.text_typ)

        finally:
            os.unlink(test_file)

    def test_import_creates_geltungsbereich(self):
        """Test that Geltungsbereich sections are created"""
        test_content = """>>>geltungsbereich
>>>text
This standard applies to all servers.
"""
        test_file = self.create_test_file(test_content)

        try:
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-003',
                '--name', 'Test Document 3',
                '--dokumententyp', 'IT-Sicherheit'
            )

            dokument = Dokument.objects.get(nummer='TEST-003')
            geltungsbereich = Geltungsbereich.objects.filter(geltungsbereich=dokument)
            self.assertEqual(geltungsbereich.count(), 1)
            self.assertEqual(
                geltungsbereich.first().inhalt,
                'This standard applies to all servers.'
            )
            self.assertEqual(geltungsbereich.first().abschnitttyp, self.text_typ)

        finally:
            os.unlink(test_file)

    def test_import_creates_vorgabe_with_all_fields(self):
        """Test creating a Vorgabe with all fields"""
        test_content = """>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel
Complete Requirement
>>>Kurztext
>>>Text
Short text here.
>>>Langtext
>>>Text
Long text here.
>>>Stichworte
Testing, Management, Security
>>>Checkliste
Is the requirement met?
Has documentation been provided?
"""
        test_file = self.create_test_file(test_content)

        try:
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-004',
                '--name', 'Test Document 4',
                '--dokumententyp', 'IT-Sicherheit'
            )

            dokument = Dokument.objects.get(nummer='TEST-004')
            vorgabe = Vorgabe.objects.get(dokument=dokument, nummer=1)

            # Check basic fields
            self.assertEqual(vorgabe.titel, 'Complete Requirement')
            self.assertEqual(vorgabe.thema, self.thema_organisation)

            # Check Kurztext
            kurztext = VorgabeKurztext.objects.filter(abschnitt=vorgabe)
            self.assertEqual(kurztext.count(), 1)
            self.assertEqual(kurztext.first().inhalt, 'Short text here.')

            # Check Langtext
            langtext = VorgabeLangtext.objects.filter(abschnitt=vorgabe)
            self.assertEqual(langtext.count(), 1)
            self.assertEqual(langtext.first().inhalt, 'Long text here.')

            # Check Stichworte
            stichworte = vorgabe.stichworte.all()
            self.assertEqual(stichworte.count(), 3)
            stichwort_names = {s.stichwort for s in stichworte}
            self.assertEqual(stichwort_names, {'Testing', 'Management', 'Security'})

            # Check Checklistenfragen
            fragen = Checklistenfrage.objects.filter(vorgabe=vorgabe)
            self.assertEqual(fragen.count(), 2)
            frage_texts = {f.frage for f in fragen}
            self.assertEqual(frage_texts, {
                'Is the requirement met?',
                'Has documentation been provided?'
            })

        finally:
            os.unlink(test_file)

    def test_import_multiple_vorgaben(self):
        """Test importing multiple Vorgaben"""
        test_content = """>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel
First Requirement
>>>Kurztext
>>>Text
First requirement text.

>>>Vorgabe Technik
>>>Nummer 2
>>>Titel
Second Requirement
>>>Kurztext
>>>Text
Second requirement text.

>>>Vorgabe Organisation
>>>Nummer 3
>>>Titel
Third Requirement
>>>Kurztext
>>>Text
Third requirement text.
"""
        test_file = self.create_test_file(test_content)

        try:
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-005',
                '--name', 'Test Document 5',
                '--dokumententyp', 'IT-Sicherheit'
            )

            dokument = Dokument.objects.get(nummer='TEST-005')
            vorgaben = Vorgabe.objects.filter(dokument=dokument).order_by('nummer')

            self.assertEqual(vorgaben.count(), 3)
            self.assertEqual(vorgaben[0].nummer, 1)
            self.assertEqual(vorgaben[0].thema, self.thema_organisation)
            self.assertEqual(vorgaben[1].nummer, 2)
            self.assertEqual(vorgaben[1].thema, self.thema_technik)
            self.assertEqual(vorgaben[2].nummer, 3)
            self.assertEqual(vorgaben[2].thema, self.thema_organisation)

        finally:
            os.unlink(test_file)

    def test_dry_run_creates_no_data(self):
        """Test that dry-run mode creates no database records"""
        test_content = """>>>Einleitung
>>>text
Introduction text.

>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel
Test Requirement
>>>Kurztext
>>>Text
Short text.
"""
        test_file = self.create_test_file(test_content)

        try:
            out = StringIO()
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-DRY',
                '--name', 'Dry Run Test',
                '--dokumententyp', 'IT-Sicherheit',
                '--dry-run',
                stdout=out
            )

            # Document is created (for counting purposes) but not saved
            output = out.getvalue()
            self.assertIn('Dry run: no database changes will be made', output)
            self.assertIn('Dry run complete', output)

            # Check that Einleitung and Vorgabe were NOT created
            dokument = Dokument.objects.get(nummer='TEST-DRY')
            self.assertEqual(Einleitung.objects.filter(einleitung=dokument).count(), 0)
            self.assertEqual(Vorgabe.objects.filter(dokument=dokument).count(), 0)

        finally:
            os.unlink(test_file)

    def test_dry_run_verbose_shows_details(self):
        """Test that dry-run with verbose shows detailed output"""
        test_content = """>>>Einleitung
>>>text
Introduction.

>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel
Test
>>>Kurztext
>>>Text
Short.
>>>Langtext
>>>Text
Long.
>>>Stichworte
Keyword1, Keyword2
>>>Checkliste
Question 1?
Question 2?
"""
        test_file = self.create_test_file(test_content)

        try:
            out = StringIO()
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-VERBOSE',
                '--name', 'Verbose Test',
                '--dokumententyp', 'IT-Sicherheit',
                '--dry-run',
                '--verbose',
                stdout=out
            )

            output = out.getvalue()
            self.assertIn('[DRY RUN] Einleitung Abschnitt', output)
            self.assertIn('[DRY RUN] Would create Vorgabe 1', output)
            self.assertIn('Stichworte: Keyword1, Keyword2', output)
            self.assertIn('Checkliste: Question 1?', output)
            self.assertIn('Checkliste: Question 2?', output)
            self.assertIn('Kurztext', output)
            self.assertIn('Langtext', output)

        finally:
            os.unlink(test_file)

    def test_purge_deletes_existing_content(self):
        """Test that --purge deletes existing content before import"""
        test_content = """>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel
New Requirement
>>>Kurztext
>>>Text
New text.
"""
        test_file = self.create_test_file(test_content)

        try:
            # First import
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-PURGE',
                '--name', 'Purge Test',
                '--dokumententyp', 'IT-Sicherheit'
            )

            dokument = Dokument.objects.get(nummer='TEST-PURGE')
            self.assertEqual(Vorgabe.objects.filter(dokument=dokument).count(), 1)

            # Second import with different content and --purge
            test_content_2 = """>>>Vorgabe Technik
>>>Nummer 2
>>>Titel
Replacement Requirement
>>>Kurztext
>>>Text
Replacement text.
"""
            test_file_2 = self.create_test_file(test_content_2)

            try:
                out = StringIO()
                call_command(
                    'import-document',
                    test_file_2,
                    '--nummer', 'TEST-PURGE',
                    '--name', 'Purge Test',
                    '--dokumententyp', 'IT-Sicherheit',
                    '--purge',
                    stdout=out
                )

                # Old Vorgabe should be deleted, only new one exists
                vorgaben = Vorgabe.objects.filter(dokument=dokument)
                self.assertEqual(vorgaben.count(), 1)
                self.assertEqual(vorgaben.first().nummer, 2)
                self.assertEqual(vorgaben.first().thema, self.thema_technik)

                output = out.getvalue()
                self.assertIn('Purged', output)

            finally:
                os.unlink(test_file_2)

        finally:
            os.unlink(test_file)

    def test_purge_dry_run_shows_what_would_be_deleted(self):
        """Test that --purge with --dry-run shows deletion counts"""
        test_content = """>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel
Original
>>>Kurztext
>>>Text
Text.
"""
        test_file = self.create_test_file(test_content)

        try:
            # First import to create data
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-PURGE-DRY',
                '--name', 'Purge Dry Test',
                '--dokumententyp', 'IT-Sicherheit'
            )

            # Dry run with purge
            out = StringIO()
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-PURGE-DRY',
                '--name', 'Purge Dry Test',
                '--dokumententyp', 'IT-Sicherheit',
                '--purge',
                '--dry-run',
                stdout=out
            )

            output = out.getvalue()
            self.assertIn('[DRY RUN] Would purge:', output)
            self.assertIn('1 Vorgaben', output)

        finally:
            os.unlink(test_file)

    def test_header_normalization(self):
        """Test that headers with hyphens are normalized correctly"""
        test_content = """>>>geltungsbereich
>>>Liste-ungeordnet
Item 1
Item 2
Item 3
"""
        test_file = self.create_test_file(test_content)

        try:
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-NORM',
                '--name', 'Normalization Test',
                '--dokumententyp', 'IT-Sicherheit'
            )

            dokument = Dokument.objects.get(nummer='TEST-NORM')
            geltungsbereich = Geltungsbereich.objects.get(geltungsbereich=dokument)

            # Should have normalized "Liste-ungeordnet" to "liste ungeordnet"
            self.assertEqual(geltungsbereich.abschnitttyp, self.liste_ungeordnet_typ)

        finally:
            os.unlink(test_file)

    def test_missing_file_raises_error(self):
        """Test that missing file raises CommandError"""
        with self.assertRaises(CommandError) as cm:
            call_command(
                'import-document',
                '/nonexistent/file.txt',
                '--nummer', 'TEST-ERR',
                '--name', 'Error Test',
                '--dokumententyp', 'IT-Sicherheit'
            )
        self.assertIn('does not exist', str(cm.exception))

    def test_missing_dokumententyp_raises_error(self):
        """Test that missing Dokumententyp raises CommandError"""
        test_content = """>>>geltungsbereich
>>>text
Text.
"""
        test_file = self.create_test_file(test_content)

        try:
            with self.assertRaises(CommandError) as cm:
                call_command(
                    'import-document',
                    test_file,
                    '--nummer', 'TEST-ERR',
                    '--name', 'Error Test',
                    '--dokumententyp', 'NonExistentType'
                )
            self.assertIn('does not exist', str(cm.exception))

        finally:
            os.unlink(test_file)

    def test_missing_thema_skips_vorgabe(self):
        """Test that missing Thema causes Vorgabe to be skipped with warning"""
        test_content = """>>>Vorgabe NonExistentThema
>>>Nummer 1
>>>Titel
Test
>>>Kurztext
>>>Text
Text.
"""
        test_file = self.create_test_file(test_content)

        try:
            out = StringIO()
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-SKIP',
                '--name', 'Skip Test',
                '--dokumententyp', 'IT-Sicherheit',
                stdout=out
            )

            dokument = Dokument.objects.get(nummer='TEST-SKIP')
            # Vorgabe should NOT be created
            self.assertEqual(Vorgabe.objects.filter(dokument=dokument).count(), 0)

            output = out.getvalue()
            self.assertIn('not found, skipping Vorgabe', output)

        finally:
            os.unlink(test_file)

    def test_missing_abschnitttyp_defaults_to_text(self):
        """Test that missing AbschnittTyp defaults to 'text' with warning"""
        # Delete all but text type
        AbschnittTyp.objects.exclude(abschnitttyp='text').delete()

        test_content = """>>>geltungsbereich
>>>liste geordnet
Item 1
"""
        test_file = self.create_test_file(test_content)

        try:
            out = StringIO()
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-DEFAULT',
                '--name', 'Default Test',
                '--dokumententyp', 'IT-Sicherheit',
                stdout=out
            )

            dokument = Dokument.objects.get(nummer='TEST-DEFAULT')
            geltungsbereich = Geltungsbereich.objects.get(geltungsbereich=dokument)

            # Should default to 'text' type
            self.assertEqual(geltungsbereich.abschnitttyp.abschnitttyp, 'text')

            output = out.getvalue()
            self.assertIn("not found; defaulting to 'text'", output)

        finally:
            os.unlink(test_file)

    def test_inline_titel(self):
        """Test that inline title (on same line as header) is parsed"""
        test_content = """>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel Inline Title Here
>>>Kurztext
>>>Text
Text.
"""
        test_file = self.create_test_file(test_content)

        try:
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-INLINE',
                '--name', 'Inline Test',
                '--dokumententyp', 'IT-Sicherheit'
            )

            dokument = Dokument.objects.get(nummer='TEST-INLINE')
            vorgabe = Vorgabe.objects.get(dokument=dokument)
            self.assertEqual(vorgabe.titel, 'Inline Title Here')

        finally:
            os.unlink(test_file)

    def test_inline_stichworte(self):
        """Test that inline Stichworte (on same line as header) are parsed"""
        test_content = """>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel Test
>>>Stichworte Security, Testing, Compliance
>>>Kurztext
>>>Text
Text.
"""
        test_file = self.create_test_file(test_content)

        try:
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-INLINE-STW',
                '--name', 'Inline Stichwort Test',
                '--dokumententyp', 'IT-Sicherheit'
            )

            dokument = Dokument.objects.get(nummer='TEST-INLINE-STW')
            vorgabe = Vorgabe.objects.get(dokument=dokument)
            stichworte = {s.stichwort for s in vorgabe.stichworte.all()}
            self.assertEqual(stichworte, {'Security', 'Testing', 'Compliance'})

        finally:
            os.unlink(test_file)

    def test_gueltigkeit_dates(self):
        """Test that validity dates are set correctly"""
        test_content = """>>>geltungsbereich
>>>text
Scope.
"""
        test_file = self.create_test_file(test_content)

        try:
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-DATES',
                '--name', 'Date Test',
                '--dokumententyp', 'IT-Sicherheit',
                '--gueltigkeit_von', '2024-01-01',
                '--gueltigkeit_bis', '2024-12-31'
            )

            dokument = Dokument.objects.get(nummer='TEST-DATES')
            self.assertEqual(str(dokument.gueltigkeit_von), '2024-01-01')
            self.assertEqual(str(dokument.gueltigkeit_bis), '2024-12-31')

        finally:
            os.unlink(test_file)

    def test_existing_document_updates(self):
        """Test that importing to existing document number shows warning"""
        test_content = """>>>geltungsbereich
>>>text
First version.
"""
        test_file = self.create_test_file(test_content)

        try:
            # First import
            out = StringIO()
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-EXISTS',
                '--name', 'Existing Test',
                '--dokumententyp', 'IT-Sicherheit',
                stdout=out
            )

            output1 = out.getvalue()
            self.assertIn('Created Document TEST-EXISTS', output1)

            # Second import with same number
            out2 = StringIO()
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-EXISTS',
                '--name', 'Existing Test',
                '--dokumententyp', 'IT-Sicherheit',
                stdout=out2
            )

            output2 = out2.getvalue()
            self.assertIn('already exists', output2)

        finally:
            os.unlink(test_file)

    def test_multiple_kurztext_sections(self):
        """Test Vorgabe with multiple Kurztext sections"""
        test_content = """>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel Multiple Sections
>>>Kurztext
>>>Text
First kurztext section.
>>>Liste ungeordnet
Item A
Item B
>>>Langtext
>>>Text
Langtext.
"""
        test_file = self.create_test_file(test_content)

        try:
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-MULTI',
                '--name', 'Multi Section Test',
                '--dokumententyp', 'IT-Sicherheit'
            )

            dokument = Dokument.objects.get(nummer='TEST-MULTI')
            vorgabe = Vorgabe.objects.get(dokument=dokument)
            kurztext_sections = VorgabeKurztext.objects.filter(abschnitt=vorgabe).order_by('id')

            self.assertEqual(kurztext_sections.count(), 2)
            self.assertEqual(kurztext_sections[0].abschnitttyp.abschnitttyp, 'text')
            self.assertEqual(kurztext_sections[1].abschnitttyp.abschnitttyp, 'liste ungeordnet')

        finally:
            os.unlink(test_file)

    def test_empty_file(self):
        """Test importing an empty file"""
        test_content = ""
        test_file = self.create_test_file(test_content)

        try:
            out = StringIO()
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-EMPTY',
                '--name', 'Empty Test',
                '--dokumententyp', 'IT-Sicherheit',
                stdout=out
            )

            dokument = Dokument.objects.get(nummer='TEST-EMPTY')
            # Document created but no content
            self.assertEqual(Einleitung.objects.filter(einleitung=dokument).count(), 0)
            self.assertEqual(Geltungsbereich.objects.filter(geltungsbereich=dokument).count(), 0)
            self.assertEqual(Vorgabe.objects.filter(dokument=dokument).count(), 0)

            output = out.getvalue()
            self.assertIn('with 0 Vorgaben', output)

        finally:
            os.unlink(test_file)

    def test_unicode_content(self):
        """Test that Unicode characters (German umlauts, etc.) are handled correctly"""
        test_content = """>>>Einleitung
>>>text
Übersicht über die Sicherheitsanforderungen für IT-Systeme.

>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel
Überprüfung der Systemkonfiguration
>>>Kurztext
>>>Text
Die Konfiguration muss regelmäßig überprüft werden.
>>>Stichworte
Überprüfung, Sicherheit, Qualität
"""
        test_file = self.create_test_file(test_content)

        try:
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-UNICODE',
                '--name', 'Unicode Test',
                '--dokumententyp', 'IT-Sicherheit'
            )

            dokument = Dokument.objects.get(nummer='TEST-UNICODE')

            # Check Einleitung
            einleitung = Einleitung.objects.get(einleitung=dokument)
            self.assertIn('Übersicht', einleitung.inhalt)

            # Check Vorgabe
            vorgabe = Vorgabe.objects.get(dokument=dokument)
            self.assertEqual(vorgabe.titel, 'Überprüfung der Systemkonfiguration')

            # Check Kurztext
            kurztext = VorgabeKurztext.objects.get(abschnitt=vorgabe)
            self.assertIn('regelmäßig', kurztext.inhalt)

            # Check Stichworte
            stichworte = {s.stichwort for s in vorgabe.stichworte.all()}
            self.assertIn('Überprüfung', stichworte)

        finally:
            os.unlink(test_file)

    def test_context_switching(self):
        """Test that context switches correctly between sections"""
        test_content = """>>>Einleitung
>>>text
Intro text 1.
>>>text
Intro text 2.

>>>geltungsbereich
>>>text
Scope text 1.
>>>text
Scope text 2.

>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel Test
>>>Kurztext
>>>text
Kurztext 1.
>>>text
Kurztext 2.
>>>Langtext
>>>text
Langtext 1.
"""
        test_file = self.create_test_file(test_content)

        try:
            call_command(
                'import-document',
                test_file,
                '--nummer', 'TEST-CONTEXT',
                '--name', 'Context Test',
                '--dokumententyp', 'IT-Sicherheit'
            )

            dokument = Dokument.objects.get(nummer='TEST-CONTEXT')

            # Check Einleitung has 2 sections
            einleitung = Einleitung.objects.filter(einleitung=dokument)
            self.assertEqual(einleitung.count(), 2)

            # Check Geltungsbereich has 2 sections
            geltungsbereich = Geltungsbereich.objects.filter(geltungsbereich=dokument)
            self.assertEqual(geltungsbereich.count(), 2)

            # Check Vorgabe has correct Kurztext and Langtext counts
            vorgabe = Vorgabe.objects.get(dokument=dokument)
            kurztext = VorgabeKurztext.objects.filter(abschnitt=vorgabe)
            langtext = VorgabeLangtext.objects.filter(abschnitt=vorgabe)
            self.assertEqual(kurztext.count(), 2)
            self.assertEqual(langtext.count(), 1)

        finally:
            os.unlink(test_file)

    def test_real_world_example(self):
        """Test importing the real r009.txt example document"""
        # Use the actual example file
        example_file = Path(__file__).parent.parent / 'Documentation' / 'import formats' / 'r009.txt'

        if not example_file.exists():
            self.skipTest("r009.txt example file not found")

        out = StringIO()
        call_command(
            'import-document',
            str(example_file),
            '--nummer', 'R009',
            '--name', 'IT-Sicherheit Serversysteme',
            '--dokumententyp', 'IT-Sicherheit',
            stdout=out
        )

        dokument = Dokument.objects.get(nummer='R009')

        # Check that Einleitung was created
        self.assertGreater(Einleitung.objects.filter(einleitung=dokument).count(), 0)

        # Check that Geltungsbereich was created
        self.assertGreater(Geltungsbereich.objects.filter(geltungsbereich=dokument).count(), 0)

        # Check that multiple Vorgaben were created (r009.txt has 23 Vorgaben)
        vorgaben = Vorgabe.objects.filter(dokument=dokument)
        self.assertGreaterEqual(vorgaben.count(), 20)

        # Verify output message
        output = out.getvalue()
        self.assertIn('Imported document R009', output)
