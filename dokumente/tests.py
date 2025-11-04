from django.test import TestCase, Client
from django.urls import reverse
from django.core.management import call_command
from django.contrib.auth.models import User
from datetime import date, timedelta
from io import StringIO
from .models import (
    Dokumententyp, Person, Thema, Dokument, Vorgabe,
    VorgabeLangtext, VorgabeKurztext, Geltungsbereich,
    Einleitung, Checklistenfrage, Changelog
)
from .utils import check_vorgabe_conflicts, date_ranges_intersect, format_conflict_report
from abschnitte.models import AbschnittTyp
from referenzen.models import Referenz
from stichworte.models import Stichwort
from rollen.models import Rolle


class DokumententypModelTest(TestCase):
    """Test cases for Dokumententyp model"""
    
    def setUp(self):
        self.dokumententyp = Dokumententyp.objects.create(
            name="Standard IT-Sicherheit",
            verantwortliche_ve="SR-SUR-SEC"
        )
    
    def test_dokumententyp_creation(self):
        """Test that Dokumententyp is created correctly"""
        self.assertEqual(self.dokumententyp.name, "Standard IT-Sicherheit")
        self.assertEqual(self.dokumententyp.verantwortliche_ve, "SR-SUR-SEC")
    
    def test_dokumententyp_str(self):
        """Test string representation of Dokumententyp"""
        self.assertEqual(str(self.dokumententyp), "Standard IT-Sicherheit")
    
    def test_dokumententyp_verbose_name(self):
        """Test verbose name"""
        self.assertEqual(
            Dokumententyp._meta.verbose_name,
            "Dokumententyp"
        )
        self.assertEqual(
            Dokumententyp._meta.verbose_name_plural,
            "Dokumententypen"
        )


class PersonModelTest(TestCase):
    """Test cases for Person model"""
    
    def setUp(self):
        self.person = Person.objects.create(
            name="Max Mustermann",
            funktion="Manager"
        )
    
    def test_person_creation(self):
        """Test that Person is created correctly"""
        self.assertEqual(self.person.name, "Max Mustermann")
        self.assertEqual(self.person.funktion, "Manager")
    
    def test_person_str(self):
        """Test string representation of Person"""
        self.assertEqual(str(self.person), "Max Mustermann")
    
    def test_person_verbose_name_plural(self):
        """Test verbose name plural"""
        self.assertEqual(
            Person._meta.verbose_name_plural,
            "Personen"
        )


class ThemaModelTest(TestCase):
    """Test cases for Thema model"""
    
    def setUp(self):
        self.thema = Thema.objects.create(
            name="Security",
            erklaerung="Security related topics"
        )
    
    def test_thema_creation(self):
        """Test that Thema is created correctly"""
        self.assertEqual(self.thema.name, "Security")
        self.assertEqual(self.thema.erklaerung, "Security related topics")
    
    def test_thema_str(self):
        """Test string representation of Thema"""
        self.assertEqual(str(self.thema), "Security")
    
    def test_thema_blank_erklaerung(self):
        """Test that erklaerung can be blank"""
        thema = Thema.objects.create(name="Testing")
        self.assertEqual(thema.erklaerung, "")


class DokumentModelTest(TestCase):
    """Test cases for Dokument model"""
    
    def setUp(self):
        self.dokumententyp = Dokumententyp.objects.create(
            name="Policy",
            verantwortliche_ve="Legal"
        )
        self.autor = Person.objects.create(
            name="John Doe",
            funktion="Author"
        )
        self.pruefer = Person.objects.create(
            name="Jane Smith",
            funktion="Reviewer"
        )
        self.dokument = Dokument.objects.create(
            nummer="DOC-001",
            dokumententyp=self.dokumententyp,
            name="Security Policy",
            gueltigkeit_von=date.today(),
            signatur_cso="CSO-123",
            anhaenge="Appendix A, B",
            aktiv=True
        )
        self.dokument.autoren.add(self.autor)
        self.dokument.pruefende.add(self.pruefer)
    
    def test_dokument_creation(self):
        """Test that Dokument is created correctly"""
        self.assertEqual(self.dokument.nummer, "DOC-001")
        self.assertEqual(self.dokument.name, "Security Policy")
        self.assertEqual(self.dokument.dokumententyp, self.dokumententyp)
        self.assertEqual(self.dokument.aktiv, True)
    
    def test_dokument_str(self):
        """Test string representation of Dokument"""
        self.assertEqual(str(self.dokument), "DOC-001 – Security Policy")
    
    def test_dokument_many_to_many_relationships(self):
        """Test many-to-many relationships"""
        self.assertIn(self.autor, self.dokument.autoren.all())
        self.assertIn(self.pruefer, self.dokument.pruefende.all())
    
    def test_dokument_optional_fields(self):
        """Test optional fields can be None or blank"""
        dokument = Dokument.objects.create(
            nummer="DOC-002",
            dokumententyp=self.dokumententyp,
            name="Test Document",
            aktiv=True
        )
        self.assertIsNone(dokument.gueltigkeit_von)
        self.assertIsNone(dokument.gueltigkeit_bis)
        self.assertEqual(dokument.signatur_cso, "")
        self.assertEqual(dokument.anhaenge, "")


class VorgabeModelTest(TestCase):
    """Test cases for Vorgabe model"""
    
    def setUp(self):
        self.dokumententyp = Dokumententyp.objects.create(
            name="Standard IT-Sicherheit",
            verantwortliche_ve="SR-SUR-SEC"
        )
        self.dokument = Dokument.objects.create(
            nummer="R01234",
            dokumententyp=self.dokumententyp,
            name="IT Standard",
            aktiv=True
        )
        self.thema = Thema.objects.create(name="Security")
        self.vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Password Requirements",
            gueltigkeit_von=date.today() - timedelta(days=30)
        )
    
    def test_vorgabe_creation(self):
        """Test that Vorgabe is created correctly"""
        self.assertEqual(self.vorgabe.order, 1)
        self.assertEqual(self.vorgabe.nummer, 1)
        self.assertEqual(self.vorgabe.dokument, self.dokument)
        self.assertEqual(self.vorgabe.thema, self.thema)
    
    def test_vorgabennummer(self):
        """Test Vorgabennummer generation"""
        expected = "R01234.S.1"
        self.assertEqual(self.vorgabe.Vorgabennummer(), expected)
    
    def test_vorgabe_str(self):
        """Test string representation of Vorgabe"""
        expected = "R01234.S.1: Password Requirements"
        self.assertEqual(str(self.vorgabe), expected)
    
    def test_get_status_active(self):
        """Test get_status returns 'active' for current vorgabe"""
        status = self.vorgabe.get_status()
        self.assertEqual(status, "active")
    
    def test_get_status_future(self):
        """Test get_status returns 'future' for future vorgabe"""
        future_vorgabe = Vorgabe.objects.create(
            order=2,
            nummer=2,
            dokument=self.dokument,
            thema=self.thema,
            titel="Future Requirement",
            gueltigkeit_von=date.today() + timedelta(days=30)
        )
        status = future_vorgabe.get_status()
        self.assertEqual(status, "future")
    
    def test_get_status_expired(self):
        """Test get_status returns 'expired' for expired vorgabe"""
        expired_vorgabe = Vorgabe.objects.create(
            order=3,
            nummer=3,
            dokument=self.dokument,
            thema=self.thema,
            titel="Old Requirement",
            gueltigkeit_von=date.today() - timedelta(days=60),
            gueltigkeit_bis=date.today() - timedelta(days=10)
        )
        status = expired_vorgabe.get_status()
        self.assertEqual(status, "expired")
    
    def test_get_status_verbose(self):
        """Test get_status with verbose=True"""
        future_vorgabe = Vorgabe.objects.create(
            order=4,
            nummer=4,
            dokument=self.dokument,
            thema=self.thema,
            titel="Future Test",
            gueltigkeit_von=date.today() + timedelta(days=10)
        )
        status = future_vorgabe.get_status(verbose=True)
        self.assertIn("Ist erst ab dem", status)
        self.assertIn("in Kraft", status)
    
    def test_get_status_with_custom_check_date(self):
        """Test get_status with custom check_date"""
        vorgabe = Vorgabe.objects.create(
            order=5,
            nummer=5,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Requirement",
            gueltigkeit_von=date.today() - timedelta(days=60),
            gueltigkeit_bis=date.today() - timedelta(days=10)
        )
        check_date = date.today() - timedelta(days=30)
        status = vorgabe.get_status(check_date=check_date)
        self.assertEqual(status, "active")


class VorgabeTextAbschnitteTest(TestCase):
    """Test cases for VorgabeLangtext and VorgabeKurztext"""
    
    def setUp(self):
        self.dokumententyp = Dokumententyp.objects.create(
            name="Standard IT-Sicherheit",
            verantwortliche_ve="SR-SUR-SEC"
        )
        self.dokument = Dokument.objects.create(
            nummer="R01234",
            dokumententyp=self.dokumententyp,
            name="Test Standard",
            aktiv=True
        )
        self.thema = Thema.objects.create(name="Testing")
        self.vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date.today()
        )
        self.abschnitttyp = AbschnittTyp.objects.create(
            abschnitttyp="Paragraph"
        )
    
    def test_vorgabe_langtext_creation(self):
        """Test VorgabeLangtext creation"""
        langtext = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.abschnitttyp,
            inhalt="This is a long text description",
            order=1
        )
        self.assertEqual(langtext.abschnitt, self.vorgabe)
        self.assertEqual(langtext.inhalt, "This is a long text description")
    
    def test_vorgabe_kurztext_creation(self):
        """Test VorgabeKurztext creation"""
        kurztext = VorgabeKurztext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.abschnitttyp,
            inhalt="Short summary",
            order=1
        )
        self.assertEqual(kurztext.abschnitt, self.vorgabe)
        self.assertEqual(kurztext.inhalt, "Short summary")


class DokumentTextAbschnitteTest(TestCase):
    """Test cases for Geltungsbereich and Einleitung"""
    
    def setUp(self):
        self.dokumententyp = Dokumententyp.objects.create(
            name="Policy",
            verantwortliche_ve="Legal"
        )
        self.dokument = Dokument.objects.create(
            nummer="POL-001",
            dokumententyp=self.dokumententyp,
            name="Test Policy",
            aktiv=True
        )
        self.abschnitttyp = AbschnittTyp.objects.create(
            abschnitttyp="Paragraph"
        )
    
    def test_geltungsbereich_creation(self):
        """Test Geltungsbereich creation"""
        geltungsbereich = Geltungsbereich.objects.create(
            geltungsbereich=self.dokument,
            abschnitttyp=self.abschnitttyp,
            inhalt="Applies to all employees",
            order=1
        )
        self.assertEqual(geltungsbereich.geltungsbereich, self.dokument)
        self.assertEqual(geltungsbereich.inhalt, "Applies to all employees")
    
    def test_einleitung_creation(self):
        """Test Einleitung creation"""
        einleitung = Einleitung.objects.create(
            einleitung=self.dokument,
            abschnitttyp=self.abschnitttyp,
            inhalt="This document defines...",
            order=1
        )
        self.assertEqual(einleitung.einleitung, self.dokument)
        self.assertEqual(einleitung.inhalt, "This document defines...")


class ChecklistenfrageModelTest(TestCase):
    """Test cases for Checklistenfrage model"""
    
    def setUp(self):
        self.dokumententyp = Dokumententyp.objects.create(
            name="Standard IT-Sicherheit",
            verantwortliche_ve="QA"
        )
        self.dokument = Dokument.objects.create(
            nummer="QA-001",
            dokumententyp=self.dokumententyp,
            name="QA Standard",
            aktiv=True
        )
        self.thema = Thema.objects.create(name="Quality")
        self.vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Quality Check",
            gueltigkeit_von=date.today()
        )
        self.frage = Checklistenfrage.objects.create(
            vorgabe=self.vorgabe,
            frage="Have all tests passed?"
        )
    
    def test_checklistenfrage_creation(self):
        """Test Checklistenfrage creation"""
        self.assertEqual(self.frage.vorgabe, self.vorgabe)
        self.assertEqual(self.frage.frage, "Have all tests passed?")
    
    def test_checklistenfrage_str(self):
        """Test string representation"""
        self.assertEqual(str(self.frage), "Have all tests passed?")
    
    def test_checklistenfrage_related_name(self):
        """Test related name works correctly"""
        self.assertIn(self.frage, self.vorgabe.checklistenfragen.all())


class ChangelogModelTest(TestCase):
    """Test cases for Changelog model"""
    
    def setUp(self):
        self.dokumententyp = Dokumententyp.objects.create(
            name="Standard IT-Sicherheit",
            verantwortliche_ve="SR-SUR-SEC"
        )
        self.dokument = Dokument.objects.create(
            nummer="R01234",
            dokumententyp=self.dokumententyp,
            name="IT Standard",
            aktiv=True
        )
        self.autor = Person.objects.create(
            name="John Doe",
            funktion="Developer"
        )
        self.changelog = Changelog.objects.create(
            dokument=self.dokument,
            datum=date.today(),
            aenderung="Initial version"
        )
        self.changelog.autoren.add(self.autor)
    
    def test_changelog_creation(self):
        """Test Changelog creation"""
        self.assertEqual(self.changelog.dokument, self.dokument)
        self.assertEqual(self.changelog.aenderung, "Initial version")
        self.assertIn(self.autor, self.changelog.autoren.all())
    
    def test_changelog_str(self):
        """Test string representation"""
        expected = f"{date.today()} – R01234"
        self.assertEqual(str(self.changelog), expected)


class ViewsTestCase(TestCase):
    """Test cases for views"""
    
    def setUp(self):
        self.client = Client()
        self.dokumententyp = Dokumententyp.objects.create(
            name="Standard IT-Sicherheit",
            verantwortliche_ve="SR-SUR-SEC"
        )
        self.dokument = Dokument.objects.create(
            nummer="R01234",
            dokumententyp=self.dokumententyp,
            name="Test Standard",
            aktiv=True
        )
        self.thema = Thema.objects.create(name="Testing")
        self.vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Requirement",
            gueltigkeit_von=date.today()
        )
        self.abschnitttyp = AbschnittTyp.objects.create(
            abschnitttyp="Paragraph"
        )
    
    def test_standard_list_view(self):
        """Test standard_list view"""
        response = self.client.get(reverse('standard_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "R01234")
        self.assertIn('dokumente', response.context)
    
    def test_standard_detail_view(self):
        """Test standard_detail view"""
        response = self.client.get(
            reverse('standard_detail', kwargs={'nummer': 'R01234'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('standard', response.context)
        self.assertIn('vorgaben', response.context)
        self.assertEqual(response.context['standard'], self.dokument)
    
    def test_standard_detail_view_404(self):
        """Test standard_detail view returns 404 for non-existent document"""
        response = self.client.get(
            reverse('standard_detail', kwargs={'nummer': 'NONEXISTENT'})
        )
        self.assertEqual(response.status_code, 404)
    
    def test_standard_checkliste_view(self):
        """Test standard_checkliste view"""
        response = self.client.get(
            reverse('standard_checkliste', kwargs={'nummer': 'R01234'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('standard', response.context)
        self.assertIn('vorgaben', response.context)
    
    def test_standard_history_view(self):
        """Test standard_detail with history (check_date)"""
        url = reverse('standard_history', kwargs={'nummer': 'R01234'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class URLPatternsTest(TestCase):
    """Test URL patterns"""
    
    def test_standard_list_url_resolves(self):
        """Test that standard_list URL resolves correctly"""
        url = reverse('standard_list')
        self.assertEqual(url, '/dokumente/')
    
    def test_standard_detail_url_resolves(self):
        """Test that standard_detail URL resolves correctly"""
        url = reverse('standard_detail', kwargs={'nummer': 'TEST-001'})
        self.assertEqual(url, '/dokumente/TEST-001/')
    
    def test_standard_checkliste_url_resolves(self):
        """Test that standard_checkliste URL resolves correctly"""
        url = reverse('standard_checkliste', kwargs={'nummer': 'TEST-001'})
        self.assertEqual(url, '/dokumente/TEST-001/checkliste/')
    
    def test_standard_history_url_resolves(self):
        """Test that standard_history URL resolves correctly"""
        url = reverse('standard_history', kwargs={'nummer': 'TEST-001'})
        self.assertEqual(url, '/dokumente/TEST-001/history/')


class VorgabeSanityCheckTest(TestCase):
    """Test cases for Vorgabe sanity check functionality"""
    
    def setUp(self):
        """Set up test data for sanity check tests"""
        self.dokumententyp = Dokumententyp.objects.create(
            name="Standard IT-Sicherheit",
            verantwortliche_ve="SR-SUR-SEC"
        )
        self.dokument = Dokument.objects.create(
            nummer="R0066",
            dokumententyp=self.dokumententyp,
            name="IT Security Standard",
            aktiv=True
        )
        self.thema = Thema.objects.create(name="Organisation")
        self.base_date = date(2023, 1, 1)
        
        # Create non-conflicting Vorgaben
        self.vorgabe1 = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="First Vorgabe",
            gueltigkeit_von=self.base_date,
            gueltigkeit_bis=date(2023, 12, 31)
        )
        
        self.vorgabe2 = Vorgabe.objects.create(
            order=2,
            nummer=2,
            dokument=self.dokument,
            thema=self.thema,
            titel="Second Vorgabe",
            gueltigkeit_von=self.base_date,
            gueltigkeit_bis=date(2023, 12, 31)
        )
    
    def test_date_ranges_intersect_no_overlap(self):
        """Test date_ranges_intersect with non-overlapping ranges"""
        # Range 1: 2023-01-01 to 2023-06-30
        # Range 2: 2023-07-01 to 2023-12-31
        result = date_ranges_intersect(
            date(2023, 1, 1), date(2023, 6, 30),
            date(2023, 7, 1), date(2023, 12, 31)
        )
        self.assertFalse(result)
    
    def test_date_ranges_intersect_with_overlap(self):
        """Test date_ranges_intersect with overlapping ranges"""
        # Range 1: 2023-01-01 to 2023-06-30
        # Range 2: 2023-06-01 to 2023-12-31 (overlaps in June)
        result = date_ranges_intersect(
            date(2023, 1, 1), date(2023, 6, 30),
            date(2023, 6, 1), date(2023, 12, 31)
        )
        self.assertTrue(result)
    
    def test_date_ranges_intersect_with_none_end_date(self):
        """Test date_ranges_intersect with None end date (open-ended)"""
        # Range 1: 2023-01-01 to None (open-ended)
        # Range 2: 2023-06-01 to 2023-12-31
        result = date_ranges_intersect(
            date(2023, 1, 1), None,
            date(2023, 6, 1), date(2023, 12, 31)
        )
        self.assertTrue(result)
    
    def test_date_ranges_intersect_both_none_end_dates(self):
        """Test date_ranges_intersect with both None end dates"""
        # Both ranges are open-ended
        result = date_ranges_intersect(
            date(2023, 1, 1), None,
            date(2023, 6, 1), None
        )
        self.assertTrue(result)
    
    def test_date_ranges_intersect_identical_ranges(self):
        """Test date_ranges_intersect with identical ranges"""
        result = date_ranges_intersect(
            date(2023, 1, 1), date(2023, 12, 31),
            date(2023, 1, 1), date(2023, 12, 31)
        )
        self.assertTrue(result)
    
    def test_sanity_check_vorgaben_no_conflicts(self):
        """Test sanity_check_vorgaben with no conflicts"""
        conflicts = Vorgabe.sanity_check_vorgaben()
        self.assertEqual(len(conflicts), 0)
    
    def test_sanity_check_vorgaben_with_conflicts(self):
        """Test sanity_check_vorgaben with conflicting Vorgaben"""
        # Create a conflicting Vorgabe (same nummer, thema, dokument with overlapping dates)
        conflicting_vorgabe = Vorgabe.objects.create(
            order=3,
            nummer=1,  # Same as vorgabe1
            dokument=self.dokument,
            thema=self.thema,
            titel="Conflicting Vorgabe",
            gueltigkeit_von=date(2023, 6, 1),  # Overlaps with vorgabe1
            gueltigkeit_bis=date(2023, 8, 31)
        )
        
        conflicts = Vorgabe.sanity_check_vorgaben()
        self.assertEqual(len(conflicts), 1)
        
        conflict = conflicts[0]
        self.assertEqual(conflict['conflict_type'], 'date_range_intersection')
        self.assertIn('R0066.O.1', conflict['message'])
        self.assertIn('überschneiden sich in der Geltungsdauer', conflict['message'])
        self.assertEqual(conflict['vorgabe1'], self.vorgabe1)
        self.assertEqual(conflict['vorgabe2'], conflicting_vorgabe)
    
    def test_sanity_check_vorgaben_multiple_conflicts(self):
        """Test sanity_check_vorgaben with multiple conflict groups"""
        # Create first conflict group
        conflicting_vorgabe1 = Vorgabe.objects.create(
            order=3,
            nummer=1,  # Same as vorgabe1
            dokument=self.dokument,
            thema=self.thema,
            titel="Conflicting Vorgabe 1",
            gueltigkeit_von=date(2023, 6, 1),
            gueltigkeit_bis=date(2023, 8, 31)
        )
        
        # Create second conflict group with different nummer
        conflicting_vorgabe2 = Vorgabe.objects.create(
            order=4,
            nummer=2,  # Same as vorgabe2
            dokument=self.dokument,
            thema=self.thema,
            titel="Conflicting Vorgabe 2",
            gueltigkeit_von=date(2023, 6, 1),
            gueltigkeit_bis=date(2023, 8, 31)
        )
        
        conflicts = Vorgabe.sanity_check_vorgaben()
        self.assertEqual(len(conflicts), 2)
        
        # Check that we have conflicts for both nummer 1 and nummer 2
        conflict_messages = [c['message'] for c in conflicts]
        self.assertTrue(any('R0066.O.1' in msg for msg in conflict_messages))
        self.assertTrue(any('R0066.O.2' in msg for msg in conflict_messages))
    
    def test_find_conflicts_no_conflicts(self):
        """Test find_conflicts method on Vorgabe with no conflicts"""
        conflicts = self.vorgabe1.find_conflicts()
        self.assertEqual(len(conflicts), 0)
    
    def test_find_conflicts_with_conflicts(self):
        """Test find_conflicts method on Vorgabe with conflicts"""
        # Create a conflicting Vorgabe
        conflicting_vorgabe = Vorgabe.objects.create(
            order=3,
            nummer=1,  # Same as vorgabe1
            dokument=self.dokument,
            thema=self.thema,
            titel="Conflicting Vorgabe",
            gueltigkeit_von=date(2023, 6, 1),  # Overlaps
            gueltigkeit_bis=date(2023, 8, 31)
        )
        
        conflicts = self.vorgabe1.find_conflicts()
        self.assertEqual(len(conflicts), 1)
        conflict = conflicts[0]
        self.assertEqual(conflict['vorgabe1'], self.vorgabe1)
        self.assertEqual(conflict['vorgabe2'], conflicting_vorgabe)
    
    def test_vorgabe_clean_no_conflicts(self):
        """Test Vorgabe.clean() with no conflicts"""
        try:
            self.vorgabe1.clean()
        except Exception as e:
            self.fail(f"clean() raised {e} unexpectedly!")
    
    def test_vorgabe_clean_with_conflicts(self):
        """Test Vorgabe.clean() with conflicts raises ValidationError"""
        # Create a conflicting Vorgabe
        conflicting_vorgabe = Vorgabe(
            order=3,
            nummer=1,  # Same as vorgabe1
            dokument=self.dokument,
            thema=self.thema,
            titel="Conflicting Vorgabe",
            gueltigkeit_von=date(2023, 6, 1),  # Overlaps
            gueltigkeit_bis=date(2023, 8, 31)
        )
        
        with self.assertRaises(Exception) as context:
            conflicting_vorgabe.clean()
        
        self.assertIn('Konflikt mit bestehender', str(context.exception))
        self.assertIn('Geltungsdauer übeschneidet sich', str(context.exception))
    
    def test_check_vorgabe_conflicts_utility(self):
        """Test check_vorgabe_conflicts utility function"""
        # Initially no conflicts
        conflicts = check_vorgabe_conflicts()
        self.assertEqual(len(conflicts), 0)
        
        # Create a conflicting Vorgabe
        conflicting_vorgabe = Vorgabe.objects.create(
            order=3,
            nummer=1,  # Same as vorgabe1
            dokument=self.dokument,
            thema=self.thema,
            titel="Conflicting Vorgabe",
            gueltigkeit_von=date(2023, 6, 1),  # Overlaps
            gueltigkeit_bis=date(2023, 8, 31)
        )
        
        conflicts = check_vorgabe_conflicts()
        self.assertEqual(len(conflicts), 1)
    
    def test_format_conflict_report_no_conflicts(self):
        """Test format_conflict_report with no conflicts"""
        report = format_conflict_report([])
        self.assertEqual(report, "✓ No conflicts found in Vorgaben")
    
    def test_format_conflict_report_with_conflicts(self):
        """Test format_conflict_report with conflicts"""
        # Create a conflicting Vorgabe
        conflicting_vorgabe = Vorgabe.objects.create(
            order=3,
            nummer=1,  # Same as vorgabe1
            dokument=self.dokument,
            thema=self.thema,
            titel="Conflicting Vorgabe",
            gueltigkeit_von=date(2023, 6, 1),  # Overlaps
            gueltigkeit_bis=date(2023, 8, 31)
        )
        
        conflicts = check_vorgabe_conflicts()
        report = format_conflict_report(conflicts)
        
        self.assertIn("Found 1 conflicts:", report)
        self.assertIn("R0066.O.1", report)
        self.assertIn("intersecting validity periods", report)


class SanityCheckManagementCommandTest(TestCase):
    """Test cases for sanity_check_vorgaben management command"""
    
    def setUp(self):
        """Set up test data for management command tests"""
        self.dokumententyp = Dokumententyp.objects.create(
            name="Standard IT-Sicherheit",
            verantwortliche_ve="SR-SUR-SEC"
        )
        self.dokument = Dokument.objects.create(
            nummer="R0066",
            dokumententyp=self.dokumententyp,
            name="IT Security Standard",
            aktiv=True
        )
        self.thema = Thema.objects.create(name="Organisation")
    
    def test_sanity_check_command_no_conflicts(self):
        """Test management command with no conflicts"""
        out = StringIO()
        call_command('sanity_check_vorgaben', stdout=out)
        
        output = out.getvalue()
        self.assertIn("Starting Vorgaben sanity check...", output)
        self.assertIn("✓ No conflicts found in Vorgaben", output)
    
    def test_sanity_check_command_with_conflicts(self):
        """Test management command with conflicts"""
        # Create conflicting Vorgaben
        Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="First Vorgabe",
            gueltigkeit_von=date(2023, 1, 1),
            gueltigkeit_bis=date(2023, 12, 31)
        )
        
        Vorgabe.objects.create(
            order=2,
            nummer=1,  # Same nummer, thema, dokument
            dokument=self.dokument,
            thema=self.thema,
            titel="Conflicting Vorgabe",
            gueltigkeit_von=date(2023, 6, 1),  # Overlaps
            gueltigkeit_bis=date(2023, 8, 31)
        )
        
        out = StringIO()
        call_command('sanity_check_vorgaben', stdout=out)
        
        output = out.getvalue()
        self.assertIn("Starting Vorgaben sanity check...", output)
        self.assertIn("Found 1 conflicts:", output)
        self.assertIn("R0066.O.1", output)
        self.assertIn("überschneiden sich in der Geltungsdauer", output)


class IncompleteVorgabenTest(TestCase):
    """Test cases for incomplete Vorgaben functionality"""
    
    def setUp(self):
        self.client = Client()
        
        # Create and login a staff user
        self.staff_user = User.objects.create_user(
            username='teststaff',
            password='testpass123'
        )
        self.staff_user.is_staff = True
        self.staff_user.save()
        self.client.login(username='teststaff', password='testpass123')
        
        # Create test data
        self.dokumententyp = Dokumententyp.objects.create(
            name="Test Typ",
            verantwortliche_ve="Test VE"
        )
        
        self.thema = Thema.objects.create(
            name="Test Thema",
            erklaerung="Test Erklärung"
        )
        
        self.dokument = Dokument.objects.create(
            nummer="TEST-001",
            dokumententyp=self.dokumententyp,
            name="Test Dokument",
            gueltigkeit_von=date.today(),
            aktiv=True
        )
        
        # Create complete Vorgabe (should not appear in any list)
        self.complete_vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vollständige Vorgabe",
            gueltigkeit_von=date.today()
        )
        
        # Add all required components to make it complete
        self.stichwort = Stichwort.objects.create(
            stichwort="Test Stichwort"
        )
        self.complete_vorgabe.stichworte.add(self.stichwort)
        
        self.referenz = Referenz.objects.create(
            name_nummer="Test Referenz",
            url="/test/path"
        )
        self.complete_vorgabe.referenzen.add(self.referenz)
        
        VorgabeKurztext.objects.create(
            abschnitt=self.complete_vorgabe,
            inhalt="Test Kurztext"
        )
        
        Checklistenfrage.objects.create(
            vorgabe=self.complete_vorgabe,
            frage="Test Frage"
        )
        
        # Create incomplete Vorgaben
        # 1. Vorgabe without references
        self.no_refs_vorgabe = Vorgabe.objects.create(
            order=2,
            nummer=2,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe ohne Referenzen",
            gueltigkeit_von=date.today()
        )
        self.no_refs_vorgabe.stichworte.add(self.stichwort)
        VorgabeKurztext.objects.create(
            abschnitt=self.no_refs_vorgabe,
            inhalt="Test Kurztext"
        )
        Checklistenfrage.objects.create(
            vorgabe=self.no_refs_vorgabe,
            frage="Test Frage"
        )
        
        # 2. Vorgabe without Stichworte
        self.no_stichworte_vorgabe = Vorgabe.objects.create(
            order=3,
            nummer=3,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe ohne Stichworte",
            gueltigkeit_von=date.today()
        )
        self.no_stichworte_vorgabe.referenzen.add(self.referenz)
        VorgabeKurztext.objects.create(
            abschnitt=self.no_stichworte_vorgabe,
            inhalt="Test Kurztext"
        )
        Checklistenfrage.objects.create(
            vorgabe=self.no_stichworte_vorgabe,
            frage="Test Frage"
        )
        
        # 3. Vorgabe without text
        self.no_text_vorgabe = Vorgabe.objects.create(
            order=4,
            nummer=4,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe ohne Text",
            gueltigkeit_von=date.today()
        )
        self.no_text_vorgabe.stichworte.add(self.stichwort)
        self.no_text_vorgabe.referenzen.add(self.referenz)
        Checklistenfrage.objects.create(
            vorgabe=self.no_text_vorgabe,
            frage="Test Frage"
        )
        
        # 4. Vorgabe without Checklistenfragen
        self.no_checklisten_vorgabe = Vorgabe.objects.create(
            order=5,
            nummer=5,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe ohne Checklistenfragen",
            gueltigkeit_von=date.today()
        )
        self.no_checklisten_vorgabe.stichworte.add(self.stichwort)
        self.no_checklisten_vorgabe.referenzen.add(self.referenz)
        VorgabeKurztext.objects.create(
            abschnitt=self.no_checklisten_vorgabe,
            inhalt="Test Kurztext"
        )
    
    def test_incomplete_vorgaben_page_status(self):
        """Test that the incomplete Vorgaben page loads successfully"""
        response = self.client.get(reverse('incomplete_vorgaben'))
        self.assertEqual(response.status_code, 200)
    
    def test_incomplete_vorgaben_page_content(self):
        """Test that the page contains expected content"""
        response = self.client.get(reverse('incomplete_vorgaben'))
        self.assertContains(response, 'Unvollständige Vorgaben')
        self.assertContains(response, 'Referenzen')
        self.assertContains(response, 'Stichworte')
        self.assertContains(response, 'Text')
        self.assertContains(response, 'Checklistenfragen')
        # Check for table structure
        self.assertContains(response, '<table class="table table-striped table-hover">')
        self.assertContains(response, '<th class="text-center">Referenzen</th>')
    
    def test_no_references_list(self):
        """Test that Vorgaben without references are listed"""
        response = self.client.get(reverse('incomplete_vorgaben'))
        self.assertContains(response, 'Vorgabe ohne Referenzen')
        self.assertNotContains(response, 'Vollständige Vorgabe')  # Should not appear
    
    def test_no_stichworte_list(self):
        """Test that Vorgaben without Stichworte are listed"""
        response = self.client.get(reverse('incomplete_vorgaben'))
        self.assertContains(response, 'Vorgabe ohne Stichworte')
        self.assertNotContains(response, 'Vollständige Vorgabe')  # Should not appear
    
    def test_no_text_list(self):
        """Test that Vorgaben without Kurz- or Langtext are listed"""
        response = self.client.get(reverse('incomplete_vorgaben'))
        self.assertContains(response, 'Vorgabe ohne Text')
        self.assertNotContains(response, 'Vollständige Vorgabe')  # Should not appear
    
    def test_no_checklistenfragen_list(self):
        """Test that Vorgaben without Checklistenfragen are listed"""
        response = self.client.get(reverse('incomplete_vorgaben'))
        self.assertContains(response, 'Vorgabe ohne Checklistenfragen')
        self.assertNotContains(response, 'Vollständige Vorgabe')  # Should not appear
    
    def test_vorgabe_links(self):
        """Test that Vorgaben link to their admin pages"""
        response = self.client.get(reverse('incomplete_vorgaben'))
        # Should contain links to Vorgabe admin pages
        self.assertContains(response, 'href="/autorenumgebung/dokumente/vorgabe/2/change/"')
        self.assertContains(response, 'href="/autorenumgebung/dokumente/vorgabe/3/change/"')
        self.assertContains(response, 'href="/autorenumgebung/dokumente/vorgabe/4/change/"')
        self.assertContains(response, 'href="/autorenumgebung/dokumente/vorgabe/5/change/"')
    
    def test_badge_counts(self):
        """Test that badge counts are correct"""
        response = self.client.get(reverse('incomplete_vorgaben'))
        # Check that JavaScript updates the counts correctly
        self.assertContains(response, 'id="no-references-count"')
        self.assertContains(response, 'id="no-stichworte-count"')
        self.assertContains(response, 'id="no-text-count"')
        self.assertContains(response, 'id="no-checklistenfragen-count"')
        # Check total count
        self.assertContains(response, 'Gesamt: 4 unvollständige Vorgaben')
    
    def test_summary_section(self):
        """Test that summary section shows correct counts"""
        response = self.client.get(reverse('incomplete_vorgaben'))
        self.assertContains(response, 'Zusammenfassung')
        self.assertContains(response, 'Ohne Referenzen')
        self.assertContains(response, 'Ohne Stichworte')
        self.assertContains(response, 'Ohne Text')
        self.assertContains(response, 'Ohne Checklistenfragen')
        self.assertContains(response, 'Gesamt: 4 unvollständige Vorgaben')
    
    def test_empty_lists_message(self):
        """Test that appropriate messages are shown when lists are empty"""
        # Delete all incomplete Vorgaben
        Vorgabe.objects.exclude(pk=self.complete_vorgabe.pk).delete()
        
        response = self.client.get(reverse('incomplete_vorgaben'))
        self.assertContains(response, 'Alle Vorgaben sind vollständig!')
        self.assertContains(response, 'Alle Vorgaben haben Referenzen, Stichworte, Text und Checklistenfragen.')
    
    def test_back_link(self):
        """Test that back link to standard list exists"""
        response = self.client.get(reverse('incomplete_vorgaben'))
        self.assertContains(response, 'href="/dokumente/"')
        self.assertContains(response, 'Zurück zur Übersicht')
    
    def test_navigation_link(self):
        """Test that navigation includes link to incomplete Vorgaben"""
        response = self.client.get('/dokumente/')
        self.assertContains(response, 'href="/dokumente/unvollstaendig/"')
        self.assertContains(response, 'Unvollständig')
    
    def test_vorgabe_with_langtext_only(self):
        """Test that Vorgabe with only Langtext is still considered incomplete for text"""
        vorgabe_langtext_only = Vorgabe.objects.create(
            order=6,
            nummer=6,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe nur mit Langtext",
            gueltigkeit_von=date.today()
        )
        vorgabe_langtext_only.stichworte.add(self.stichwort)
        vorgabe_langtext_only.referenzen.add(self.referenz)
        
        # Add only Langtext, no Kurztext
        VorgabeLangtext.objects.create(
            abschnitt=vorgabe_langtext_only,
            inhalt="Test Langtext"
        )
        # Add Checklistenfragen to make it complete in that aspect
        Checklistenfrage.objects.create(
            vorgabe=vorgabe_langtext_only,
            frage="Test Frage"
        )
        
        response = self.client.get(reverse('incomplete_vorgaben'))
        # Debug: print response content to see where it appears
        print("Response content:", response.content.decode())
        # Should NOT appear in "no text" list because it has Langtext
        self.assertNotContains(response, 'Vorgabe nur mit Langtext')
    
    def test_vorgabe_with_both_text_types(self):
        """Test that Vorgabe with both Kurztext and Langtext is complete"""
        vorgabe_both_text = Vorgabe.objects.create(
            order=7,
            nummer=7,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe mit beiden Texten",
            gueltigkeit_von=date.today()
        )
        vorgabe_both_text.stichworte.add(self.stichwort)
        vorgabe_both_text.referenzen.add(self.referenz)
        
        # Add both Kurztext and Langtext
        VorgabeKurztext.objects.create(
            abschnitt=vorgabe_both_text,
            inhalt="Test Kurztext"
        )
        VorgabeLangtext.objects.create(
            abschnitt=vorgabe_both_text,
            inhalt="Test Langtext"
        )
        # Add Checklistenfragen to make it complete in that aspect
        Checklistenfrage.objects.create(
            vorgabe=vorgabe_both_text,
            frage="Test Frage"
        )
        
        response = self.client.get(reverse('incomplete_vorgaben'))
        # Should NOT appear in "no text" list because it has both text types
        self.assertNotContains(response, 'Vorgabe mit beiden Texten')
    
    def test_incomplete_vorgaben_staff_only(self):
        """Test that non-staff users are redirected to login"""
        # Logout the staff user
        self.client.logout()
        
        # Try to access the page as anonymous user
        response = self.client.get(reverse('incomplete_vorgaben'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Create a regular (non-staff) user
        regular_user = User.objects.create_user(
            username='regularuser',
            password='testpass123'
        )
        self.client.login(username='regularuser', password='testpass123')
        
        # Try to access the page as regular user
        response = self.client.get(reverse('incomplete_vorgaben'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Login as staff user again - should work
        self.client.login(username='teststaff', password='testpass123')
        response = self.client.get(reverse('incomplete_vorgaben'))
        self.assertEqual(response.status_code, 200)  # Success
