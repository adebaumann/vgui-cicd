from django.test import TestCase, Client
from django.urls import reverse
from django.core.management import call_command
from datetime import date
from io import StringIO
import tempfile
import os
import json

from dokumente.models import (
    Dokumententyp, Person, Thema, Dokument, Vorgabe,
    VorgabeLangtext, VorgabeKurztext, Geltungsbereich,
    Einleitung, Checklistenfrage, Changelog
)
from abschnitte.models import AbschnittTyp


class JSONExportManagementCommandTest(TestCase):
    """Test cases for export_json management command"""
    
    def setUp(self):
        """Set up test data for JSON export"""
        # Create test data
        self.dokumententyp = Dokumententyp.objects.create(
            name="Standard IT-Sicherheit",
            verantwortliche_ve="SR-SUR-SEC"
        )
        
        self.autor1 = Person.objects.create(
            name="Max Mustermann",
            funktion="Security Analyst"
        )
        self.autor2 = Person.objects.create(
            name="Erika Mustermann", 
            funktion="Security Manager"
        )
        
        self.thema = Thema.objects.create(
            name="Access Control",
            erklaerung="Zugangskontrolle"
        )
        
        self.dokument = Dokument.objects.create(
            nummer="TEST-001",
            dokumententyp=self.dokumententyp,
            name="Test Standard",
            gueltigkeit_von=date(2023, 1, 1),
            gueltigkeit_bis=date(2025, 12, 31),
            signatur_cso="CSO-123",
            anhaenge="Anhang1.pdf, Anhang2.pdf",
            aktiv=True
        )
        self.dokument.autoren.add(self.autor1, self.autor2)
        
        self.vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date(2023, 1, 1),
            gueltigkeit_bis=date(2025, 12, 31)
        )
        
        # Create text sections
        self.abschnitttyp_text = AbschnittTyp.objects.create(abschnitttyp="text")
        self.abschnitttyp_table = AbschnittTyp.objects.create(abschnitttyp="table")
        
        self.geltungsbereich = Geltungsbereich.objects.create(
            geltungsbereich=self.dokument,
            abschnitttyp=self.abschnitttyp_text,
            inhalt="Dies ist der Geltungsbereich",
            order=1
        )
        
        self.einleitung = Einleitung.objects.create(
            einleitung=self.dokument,
            abschnitttyp=self.abschnitttyp_text,
            inhalt="Dies ist die Einleitung",
            order=1
        )
        
        self.kurztext = VorgabeKurztext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.abschnitttyp_text,
            inhalt="Dies ist der Kurztext",
            order=1
        )
        
        self.langtext = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.abschnitttyp_table,
            inhalt="Spalte1|Spalte2\nWert1|Wert2",
            order=1
        )
        
        self.checklistenfrage = Checklistenfrage.objects.create(
            vorgabe=self.vorgabe,
            frage="Ist die Zugriffskontrolle implementiert?"
        )
        
        self.changelog = Changelog.objects.create(
            dokument=self.dokument,
            datum=date(2023, 6, 1),
            aenderung="Erste Version erstellt"
        )
        self.changelog.autoren.add(self.autor1)
    
    def test_export_json_command_stdout(self):
        """Test export_json command output to stdout"""
        out = StringIO()
        call_command('export_json', stdout=out)
        
        output = out.getvalue()
        
        # Check that output contains expected JSON structure
        self.assertIn('"Typ": "Standard IT-Sicherheit"', output)
        self.assertIn('"Nummer": "TEST-001"', output)
        self.assertIn('"Name": "Test Standard"', output)
        self.assertIn('"Max Mustermann"', output)
        self.assertIn('"Erika Mustermann"', output)
        self.assertIn('"Von": "2023-01-01"', output)
        self.assertIn('"Bis": "2025-12-31"', output)
        self.assertIn('"SignaturCSO": "CSO-123"', output)
        self.assertIn('"Dies ist der Geltungsbereich"', output)
        self.assertIn('"Dies ist die Einleitung"', output)
        self.assertIn('"Dies ist der Kurztext"', output)
        self.assertIn('"Ist die Zugriffskontrolle implementiert?"', output)
        self.assertIn('"Erste Version erstellt"', output)
    
    def test_export_json_command_to_file(self):
        """Test export_json command output to file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            call_command('export_json', output=tmp_filename)
            
            # Read file content
            with open(tmp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse JSON to ensure it's valid
            data = json.loads(content)
            
            # Verify structure
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1)
            
            doc_data = data[0]
            self.assertEqual(doc_data['Nummer'], 'TEST-001')
            self.assertEqual(doc_data['Name'], 'Test Standard')
            self.assertEqual(doc_data['Typ'], 'Standard IT-Sicherheit')
            self.assertEqual(len(doc_data['Autoren']), 2)
            self.assertIn('Max Mustermann', doc_data['Autoren'])
            self.assertIn('Erika Mustermann', doc_data['Autoren'])
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
    
    def test_export_json_command_empty_database(self):
        """Test export_json command with no documents"""
        # Delete all documents
        Dokument.objects.all().delete()
        
        out = StringIO()
        call_command('export_json', stdout=out)
        
        output = out.getvalue()
        
        # Should output empty array
        self.assertEqual(output.strip(), '[]')
    
    def test_export_json_command_inactive_documents(self):
        """Test export_json command filters inactive documents"""
        # Create inactive document
        inactive_doc = Dokument.objects.create(
            nummer="INACTIVE-001",
            dokumententyp=self.dokumententyp,
            name="Inactive Document",
            aktiv=False
        )
        
        out = StringIO()
        call_command('export_json', stdout=out)
        
        output = out.getvalue()
        
        # Should not contain inactive document
        self.assertNotIn('"INACTIVE-001"', output)
        self.assertNotIn('"Inactive Document"', output)
        
        # Should still contain active document
        self.assertIn('"TEST-001"', output)
        self.assertIn('"Test Standard"', output)


class StandardJSONViewTest(TestCase):
    """Test cases for standard_json view"""
    
    def setUp(self):
        """Set up test data for JSON view"""
        self.client = Client()
        
        # Create test data
        self.dokumententyp = Dokumententyp.objects.create(
            name="Standard IT-Sicherheit",
            verantwortliche_ve="SR-SUR-SEC"
        )
        
        self.autor = Person.objects.create(
            name="Test Autor",
            funktion="Security Analyst"
        )
        
        self.pruefender = Person.objects.create(
            name="Test Pruefender",
            funktion="Security Manager"
        )
        
        self.thema = Thema.objects.create(
            name="Access Control",
            erklaerung="Zugangskontrolle"
        )
        
        self.dokument = Dokument.objects.create(
            nummer="JSON-001",
            dokumententyp=self.dokumententyp,
            name="JSON Test Standard",
            gueltigkeit_von=date(2023, 1, 1),
            gueltigkeit_bis=date(2025, 12, 31),
            signatur_cso="CSO-456",
            anhaenge="test.pdf",
            aktiv=True
        )
        self.dokument.autoren.add(self.autor)
        self.dokument.pruefende.add(self.pruefender)
        
        self.vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="JSON Test Vorgabe",
            gueltigkeit_von=date(2023, 1, 1),
            gueltigkeit_bis=date(2025, 12, 31)
        )
        
        # Create text sections
        self.abschnitttyp_text = AbschnittTyp.objects.create(abschnitttyp="text")
        
        self.geltungsbereich = Geltungsbereich.objects.create(
            geltungsbereich=self.dokument,
            abschnitttyp=self.abschnitttyp_text,
            inhalt="Dies ist der Geltungsbereich",
            order=1
        )
        
        self.einleitung = Einleitung.objects.create(
            einleitung=self.dokument,
            abschnitttyp=self.abschnitttyp_text,
            inhalt="Dies ist die Einleitung",
            order=1
        )
        
        self.kurztext = VorgabeKurztext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.abschnitttyp_text,
            inhalt="JSON Kurztext",
            order=1
        )
        
        self.langtext = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.abschnitttyp_text,
            inhalt="JSON Langtext",
            order=1
        )
        
        self.checklistenfrage = Checklistenfrage.objects.create(
            vorgabe=self.vorgabe,
            frage="JSON Checklistenfrage?"
        )
        
        self.changelog = Changelog.objects.create(
            dokument=self.dokument,
            datum=date(2023, 6, 1),
            aenderung="JSON Changelog Eintrag"
        )
        self.changelog.autoren.add(self.autor)
    
    def test_standard_json_view_success(self):
        """Test standard_json view returns correct JSON"""
        url = reverse('standard_json', kwargs={'nummer': 'JSON-001'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Parse JSON response
        data = json.loads(response.content)
        
        # Verify document structure
        self.assertEqual(data['Nummer'], 'JSON-001')
        self.assertEqual(data['Name'], 'JSON Test Standard')
        self.assertEqual(data['Typ'], 'Standard IT-Sicherheit')
        self.assertEqual(len(data['Autoren']), 1)
        self.assertEqual(data['Autoren'][0], 'Test Autor')
        self.assertEqual(len(data['Pruefende']), 1)
        self.assertEqual(data['Pruefende'][0], 'Test Pruefender')
        self.assertEqual(data['Gueltigkeit']['Von'], '2023-01-01')
        self.assertEqual(data['Gueltigkeit']['Bis'], '2025-12-31')
        self.assertEqual(data['SignaturCSO'], 'CSO-456')
        self.assertEqual(data['Anhänge'], 'test.pdf')
        self.assertEqual(data['Verantwortlich'], 'Information Security Management BIT')
        self.assertIsNone(data['Klassifizierung'])
    
    def test_standard_json_view_not_found(self):
        """Test standard_json view returns 404 for non-existent document"""
        url = reverse('standard_json', kwargs={'nummer': 'NONEXISTENT'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_standard_json_view_empty_sections(self):
        """Test standard_json view handles empty sections correctly"""
        # Create document without sections
        empty_doc = Dokument.objects.create(
            nummer="EMPTY-001",
            dokumententyp=self.dokumententyp,
            name="Empty Document",
            aktiv=True
        )
        
        url = reverse('standard_json', kwargs={'nummer': 'EMPTY-001'})
        response = self.client.get(url)
        
        data = json.loads(response.content)
        
        # Verify empty sections are handled correctly
        self.assertEqual(data['Geltungsbereich'], {})
        self.assertEqual(data['Einleitung'], {})
        self.assertEqual(data['Vorgaben'], [])
        self.assertEqual(data['Changelog'], [])
    
    def test_standard_json_view_null_dates(self):
        """Test standard_json view handles null dates correctly"""
        # Create document with null dates
        null_doc = Dokument.objects.create(
            nummer="NULL-001",
            dokumententyp=self.dokumententyp,
            name="Null Dates Document",
            gueltigkeit_von=None,
            gueltigkeit_bis=None,
            aktiv=True
        )
        
        url = reverse('standard_json', kwargs={'nummer': 'NULL-001'})
        response = self.client.get(url)
        
        data = json.loads(response.content)
        
        # Verify null dates are handled correctly
        self.assertEqual(data['Gueltigkeit']['Von'], '')
        self.assertIsNone(data['Gueltigkeit']['Bis'])
    
    def test_standard_json_view_json_formatting(self):
        """Test standard_json view returns properly formatted JSON"""
        url = reverse('standard_json', kwargs={'nummer': 'JSON-001'})
        response = self.client.get(url)
        
        # Check that response is valid JSON
        try:
            data = json.loads(response.content)
            json_valid = True
        except json.JSONDecodeError:
            json_valid = False
        
        self.assertTrue(json_valid)
        
        # Check that JSON is properly indented (should be formatted)
        self.assertIn('\n', response.content.decode())
        self.assertIn('  ', response.content.decode())  # Check for indentation