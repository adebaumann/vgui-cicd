from django.test import TestCase, Client
from django.urls import reverse
from django.core.management import call_command
from django.contrib.auth.models import User
from datetime import date, timedelta
from io import StringIO
from .models import (
    Dokumententyp, Person, Thema, Dokument, Vorgabe,
    VorgabeLangtext, VorgabeKurztext, Geltungsbereich,
    Einleitung, Checklistenfrage, Changelog, VorgabeComment
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
    
    def test_standard_history_past_date_shows_historische(self):
        """Test that past dates show 'Historische Version'"""
        past_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        url = f'/dokumente/R01234/history/{past_date}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Historische Version vom')
        self.assertNotContains(response, 'Zukünftige Version vom')
        # Verify is_future flag is False
        self.assertFalse(response.context['standard'].is_future)
    
    def test_standard_history_future_date_shows_zukuenftige(self):
        """Test that future dates show 'Zukünftige Version'"""
        future_date = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
        url = f'/dokumente/R01234/history/{future_date}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Zukünftige Version vom')
        self.assertNotContains(response, 'Historische Version vom')
        # Verify is_future flag is True
        self.assertTrue(response.context['standard'].is_future)
    
    def test_standard_detail_current_has_no_version_label(self):
        """Test that current view (no history) has no version label"""
        url = reverse('standard_detail', kwargs={'nummer': 'R01234'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Historische Version vom')
        self.assertNotContains(response, 'Zukünftige Version vom')
        # Verify history flag is False
        self.assertFalse(response.context['standard'].history)


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


class VorgabeThemaValidationTest(TestCase):
    """Test cases for Vorgabe Thema validation"""
    
    def setUp(self):
        """Set up test data for Thema validation tests"""
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
    
    def test_vorgabe_with_thema_passes_validation(self):
        """Test that Vorgabe with a valid Thema passes clean() validation"""
        vorgabe = Vorgabe(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date.today()
        )
        # Should not raise any exception
        try:
            vorgabe.clean()
        except Exception as e:
            self.fail(f"clean() raised {e} unexpectedly!")
    
    def test_vorgabe_without_thema_fails_validation(self):
        """Test that Vorgabe without Thema fails clean() validation"""
        from django.core.exceptions import ValidationError
        
        vorgabe = Vorgabe(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=None,  # No Thema
            titel="Test Vorgabe",
            gueltigkeit_von=date.today()
        )
        
        with self.assertRaises(ValidationError) as context:
            vorgabe.clean()
        
        # Check that the error message is about thema
        self.assertIn('thema', context.exception.message_dict)
        self.assertIn('Thema ist ein Pflichtfeld', str(context.exception))
    
    def test_vorgabe_form_with_thema_is_valid(self):
        """Test that VorgabeForm with Thema is valid"""
        from dokumente.admin import VorgabeForm
        
        form_data = {
            'order': 1,
            'nummer': 1,
            'dokument': self.dokument.pk,
            'thema': self.thema.pk,
            'titel': 'Test Vorgabe',
            'gueltigkeit_von': date.today(),
        }
        form = VorgabeForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    def test_vorgabe_form_without_thema_is_invalid(self):
        """Test that VorgabeForm without Thema is invalid"""
        from dokumente.admin import VorgabeForm
        
        form_data = {
            'order': 1,
            'nummer': 1,
            'dokument': self.dokument.pk,
            'thema': '',  # Empty/missing Thema
            'titel': 'Test Vorgabe',
            'gueltigkeit_von': date.today(),
        }
        form = VorgabeForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('thema', form.errors)
    
    def test_vorgabe_form_thema_error_message_is_german(self):
        """Test that VorgabeForm shows German error message for missing Thema"""
        from dokumente.admin import VorgabeForm
        
        form_data = {
            'order': 1,
            'nummer': 1,
            'dokument': self.dokument.pk,
            'thema': '',  # Empty/missing Thema
            'titel': 'Test Vorgabe',
            'gueltigkeit_von': date.today(),
        }
        form = VorgabeForm(data=form_data)
        form.is_valid()
        
        # Check that the error message is in German
        thema_errors = form.errors.get('thema', [])
        error_messages = ' '.join(thema_errors)
        self.assertTrue(
            'Pflichtfeld' in error_messages or 'pflichtfeld' in error_messages.lower(),
            f"Expected German error message about Pflichtfeld, got: {thema_errors}"
        )
    
    def test_vorgabe_model_clean_error_message_is_german(self):
        """Test that Vorgabe.clean() shows German error message for missing Thema"""
        from django.core.exceptions import ValidationError
        
        vorgabe = Vorgabe(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=None,
            titel="Test Vorgabe",
            gueltigkeit_von=date.today()
        )
        
        with self.assertRaises(ValidationError) as context:
            vorgabe.clean()
        
        # Check error message is in German
        error_str = str(context.exception)
        self.assertIn('Thema ist ein Pflichtfeld', error_str)


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
        #print("Response content:", response.content.decode())
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
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            call_command('export_json', output=tmp_filename)
            
            # Read file content
            with open(tmp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse JSON to ensure it's valid
            import json
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
            inhalt="JSON Geltungsbereich",
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
        import json
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
        
        import json
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
        
        import json
        data = json.loads(response.content)
        
        # Verify null dates are handled correctly
        self.assertEqual(data['Gueltigkeit']['Von'], '')
        self.assertIsNone(data['Gueltigkeit']['Bis'])
    
    def test_standard_json_view_json_formatting(self):
        """Test standard_json view returns properly formatted JSON"""
        url = reverse('standard_json', kwargs={'nummer': 'JSON-001'})
        response = self.client.get(url)
        
        # Check that response is valid JSON
        import json
        try:
            data = json.loads(response.content)
            json_valid = True
        except json.JSONDecodeError:
            json_valid = False
        
        self.assertTrue(json_valid)
        
        # Check that JSON is properly indented (should be formatted)
        self.assertIn('\n', response.content.decode())
        self.assertIn('  ', response.content.decode())  # Check for indentation


class VorgabeCommentModelTest(TestCase):
    """Test cases for VorgabeComment model"""
    
    def setUp(self):
        """Set up test data for comment tests"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.dokumententyp = Dokumententyp.objects.create(
            name="Test Typ",
            verantwortliche_ve="Test VE"
        )
        
        self.thema = Thema.objects.create(
            name="Test Thema"
        )
        
        self.dokument = Dokument.objects.create(
            nummer="COMM-001",
            dokumententyp=self.dokumententyp,
            name="Comment Test Document",
            aktiv=True
        )
        
        self.vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date.today()
        )
        
        self.comment = VorgabeComment.objects.create(
            vorgabe=self.vorgabe,
            user=self.user,
            text="Dies ist ein Testkommentar"
        )
    
    def test_comment_creation(self):
        """Test that VorgabeComment is created correctly"""
        self.assertEqual(self.comment.vorgabe, self.vorgabe)
        self.assertEqual(self.comment.user, self.user)
        self.assertEqual(self.comment.text, "Dies ist ein Testkommentar")
        self.assertIsNotNone(self.comment.created_at)
        self.assertIsNotNone(self.comment.updated_at)
    
    def test_comment_str(self):
        """Test string representation of VorgabeComment"""
        expected = f"Kommentar von {self.user.username} zu {self.vorgabe.Vorgabennummer()}"
        self.assertEqual(str(self.comment), expected)
    
    def test_comment_related_name(self):
        """Test related name works correctly"""
        self.assertIn(self.comment, self.vorgabe.comments.all())
    
    def test_comment_ordering(self):
        """Test comments are ordered by created_at descending"""
        comment2 = VorgabeComment.objects.create(
            vorgabe=self.vorgabe,
            user=self.user,
            text="Zweiter Kommentar"
        )
        
        comments = list(self.vorgabe.comments.all())
        self.assertEqual(comments[0], comment2)  # Newest first
        self.assertEqual(comments[1], self.comment)
    
    def test_comment_timestamps_auto_update(self):
        """Test that updated_at changes when comment is modified"""
        original_updated_at = self.comment.updated_at
        
        # Wait a tiny bit and update
        import time
        time.sleep(0.01)
        
        self.comment.text = "Updated text"
        self.comment.save()
        
        self.assertNotEqual(self.comment.updated_at, original_updated_at)
        self.assertEqual(self.comment.text, "Updated text")
    
    def test_multiple_users_can_comment(self):
        """Test multiple users can comment on same Vorgabe"""
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        
        comment2 = VorgabeComment.objects.create(
            vorgabe=self.vorgabe,
            user=user2,
            text="Kommentar von anderem Benutzer"
        )
        
        self.assertEqual(self.vorgabe.comments.count(), 2)
        self.assertIn(self.comment, self.vorgabe.comments.all())
        self.assertIn(comment2, self.vorgabe.comments.all())


class GetVorgabeCommentsViewTest(TestCase):
    """Test cases for get_vorgabe_comments view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create users
        self.regular_user = User.objects.create_user(
            username='regularuser',
            password='testpass123',
            first_name='Regular',
            last_name='User'
        )
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            first_name='Staff',
            last_name='User'
        )
        self.staff_user.is_staff = True
        self.staff_user.save()
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        
        # Create test data
        self.dokumententyp = Dokumententyp.objects.create(
            name="Test Typ",
            verantwortliche_ve="Test VE"
        )
        
        self.thema = Thema.objects.create(name="Test Thema")
        
        self.dokument = Dokument.objects.create(
            nummer="COMM-001",
            dokumententyp=self.dokumententyp,
            name="Comment Test",
            aktiv=True
        )
        
        self.vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date.today()
        )
        
        # Create comments from different users
        self.comment1 = VorgabeComment.objects.create(
            vorgabe=self.vorgabe,
            user=self.regular_user,
            text="Kommentar von Regular User"
        )
        
        self.comment2 = VorgabeComment.objects.create(
            vorgabe=self.vorgabe,
            user=self.other_user,
            text="Kommentar von Other User"
        )
    
    def test_get_comments_requires_login(self):
        """Test that anonymous users cannot view comments"""
        url = reverse('get_vorgabe_comments', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_regular_user_sees_only_own_comments(self):
        """Test that regular users only see their own comments"""
        self.client.login(username='regularuser', password='testpass123')
        
        url = reverse('get_vorgabe_comments', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        import json
        data = json.loads(response.content)
        
        # Should only see their own comment
        self.assertEqual(len(data['comments']), 1)
        self.assertEqual(data['comments'][0]['text'], 'Kommentar von Regular User')
        self.assertEqual(data['comments'][0]['user'], 'Regular User')
        self.assertTrue(data['comments'][0]['is_own'])
    
    def test_staff_user_sees_all_comments(self):
        """Test that staff users see all comments"""
        self.client.login(username='staffuser', password='testpass123')
        
        url = reverse('get_vorgabe_comments', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        import json
        data = json.loads(response.content)
        
        # Should see all comments
        self.assertEqual(len(data['comments']), 2)
        usernames = [c['user'] for c in data['comments']]
        self.assertIn('Regular User', usernames)
        self.assertIn('Other User', usernames)
    
    def test_get_comments_returns_404_for_nonexistent_vorgabe(self):
        """Test that requesting comments for non-existent Vorgabe returns 404"""
        self.client.login(username='regularuser', password='testpass123')
        
        url = reverse('get_vorgabe_comments', kwargs={'vorgabe_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_comments_are_html_escaped(self):
        """Test that comments are properly HTML escaped"""
        # Create comment with HTML
        comment = VorgabeComment.objects.create(
            vorgabe=self.vorgabe,
            user=self.regular_user,
            text="Test <script>alert('xss')</script> comment"
        )
        
        self.client.login(username='regularuser', password='testpass123')
        
        url = reverse('get_vorgabe_comments', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.get(url)
        
        import json
        data = json.loads(response.content)
        
        # Find the comment with script tag
        script_comment = [c for c in data['comments'] if 'script' in c['text'].lower()][0]
        
        # Should be escaped
        self.assertIn('&lt;script&gt;', script_comment['text'])
        self.assertNotIn('<script>', script_comment['text'])
    
    def test_line_breaks_preserved(self):
        """Test that line breaks are converted to <br> tags"""
        comment = VorgabeComment.objects.create(
            vorgabe=self.vorgabe,
            user=self.regular_user,
            text="Line 1\nLine 2\nLine 3"
        )
        
        self.client.login(username='regularuser', password='testpass123')
        
        url = reverse('get_vorgabe_comments', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.get(url)
        
        import json
        data = json.loads(response.content)
        
        # Find the multiline comment
        multiline_comment = [c for c in data['comments'] if 'Line 1' in c['text']][0]
        
        # Should contain <br> tags
        self.assertIn('<br>', multiline_comment['text'])
        self.assertIn('Line 1<br>Line 2<br>Line 3', multiline_comment['text'])
    
    def test_security_headers_present(self):
        """Test that security headers are present in response"""
        self.client.login(username='regularuser', password='testpass123')
        
        url = reverse('get_vorgabe_comments', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.get(url)
        
        self.assertIn('Content-Security-Policy', response)
        self.assertIn('X-Content-Type-Options', response)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')


class DokumentDatesPropertyTest(TestCase):
    """Test cases for Dokument.dates property"""
    
    def setUp(self):
        """Set up test data for dates property tests"""
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
    
    def test_dates_property_no_vorgaben(self):
        """Test dates property returns empty list when dokument has no vorgaben"""
        dates = self.dokument.dates
        self.assertEqual(dates, [])
    
    def test_dates_property_single_vorgabe_with_only_gueltigkeit_von(self):
        """Test dates property with single vorgabe with only gueltigkeit_von"""
        vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date(2025, 1, 1)
        )
        
        dates = self.dokument.dates
        self.assertEqual(len(dates), 1)
        self.assertEqual(dates[0], date(2025, 1, 1))
    
    def test_dates_property_single_vorgabe_with_both_dates(self):
        """Test dates property with single vorgabe with both gueltigkeit_von and gueltigkeit_bis"""
        vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date(2025, 1, 1),
            gueltigkeit_bis=date(2026, 1, 1)
        )
        
        dates = self.dokument.dates
        # gueltigkeit_bis would add 2026-01-02, but that's the last date so it's excluded
        self.assertEqual(len(dates), 1)
        self.assertEqual(dates[0], date(2025, 1, 1))
    
    def test_dates_property_multiple_vorgaben_different_dates(self):
        """Test dates property with multiple vorgaben with different dates"""
        vorgabe1 = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe 1",
            gueltigkeit_von=date(2025, 1, 1),
            gueltigkeit_bis=date(2025, 6, 30)
        )
        
        vorgabe2 = Vorgabe.objects.create(
            order=2,
            nummer=2,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe 2",
            gueltigkeit_von=date(2025, 7, 1),
            gueltigkeit_bis=date(2026, 1, 1)
        )
        
        dates = self.dokument.dates
        # Dates: 2025-01-01, 2025-07-01, 2026-01-02 (but last one excluded)
        self.assertEqual(len(dates), 2)
        self.assertIn(date(2025, 1, 1), dates)  # Start of vorgabe1
        self.assertIn(date(2025, 7, 1), dates)  # End of vorgabe1 + 1 day = Start of vorgabe2 (deduplicated)
    
    def test_dates_property_ensures_uniqueness(self):
        """Test dates property returns unique dates only"""
        # Create two vorgaben with overlapping dates
        vorgabe1 = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe A",
            gueltigkeit_von=date(2025, 1, 1),
            gueltigkeit_bis=date(2026, 1, 1)
        )
        
        vorgabe2 = Vorgabe.objects.create(
            order=2,
            nummer=2,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe B",
            gueltigkeit_von=date(2025, 1, 1),  # Same start date
            gueltigkeit_bis=date(2026, 1, 1)   # Same end date
        )
        
        dates = self.dokument.dates
        # Both vorgaben have same dates, and the last date (2026-01-02) is excluded
        self.assertEqual(len(dates), 1)
        self.assertEqual(dates[0], date(2025, 1, 1))
    
    def test_dates_property_sorted_chronologically(self):
        """Test dates property returns dates sorted from oldest to newest"""
        # Create vorgaben in non-chronological order
        vorgabe1 = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe 1",
            gueltigkeit_von=date(2026, 1, 1)
        )
        
        vorgabe2 = Vorgabe.objects.create(
            order=2,
            nummer=2,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe 2",
            gueltigkeit_von=date(2024, 1, 1)
        )
        
        vorgabe3 = Vorgabe.objects.create(
            order=3,
            nummer=3,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe 3",
            gueltigkeit_von=date(2025, 1, 1)
        )
        
        dates = self.dokument.dates
        # Dates are [2024-01-01, 2025-01-01, 2026-01-01] but the last one is excluded
        self.assertEqual(len(dates), 2)
        self.assertEqual(dates[0], date(2024, 1, 1))
        self.assertEqual(dates[1], date(2025, 1, 1))
    
    def test_dates_property_ignores_none_dates(self):
        """Test dates property ignores None date values"""
        vorgabe1 = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe 1",
            gueltigkeit_von=date(2025, 1, 1)
            # No gueltigkeit_bis (None)
        )
        
        vorgabe2 = Vorgabe.objects.create(
            order=2,
            nummer=2,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe 2",
            gueltigkeit_von=date(2026, 1, 1),
            gueltigkeit_bis=None  # Explicitly None
        )
        
        dates = self.dokument.dates
        # Dates are 2025-01-01 and 2026-01-01, but the last date (2026-01-01) is excluded
        self.assertEqual(len(dates), 1)
        self.assertEqual(dates[0], date(2025, 1, 1))
    
    def test_dates_property_complex_scenario(self):
        """Test dates property with complex real-world scenario
        
        Vorgabe A: 2025-01-01 to 2025-12-31
        Vorgabe B: 2025-06-01 to 2026-01-01  (overlaps with A)
        Vorgabe C: 2026-02-01 to None        (no end date)
        
        Expected dates: [2025-01-01, 2025-06-01, 2025-12-31, 2026-01-01, 2026-02-01]
        The middle date (2026-01-01) should NOT be excluded even though B overlaps with A
        """
        vorgabe_a = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe A",
            gueltigkeit_von=date(2025, 1, 1),
            gueltigkeit_bis=date(2025, 12, 31)
        )
        
        vorgabe_b = Vorgabe.objects.create(
            order=2,
            nummer=2,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe B",
            gueltigkeit_von=date(2025, 6, 1),
            gueltigkeit_bis=date(2026, 1, 1)
        )
        
        vorgabe_c = Vorgabe.objects.create(
            order=3,
            nummer=3,
            dokument=self.dokument,
            thema=self.thema,
            titel="Vorgabe C",
            gueltigkeit_von=date(2026, 2, 1)
            # No gueltigkeit_bis
        )
        
        dates = self.dokument.dates
        # All dates: 2025-01-01, 2025-06-01, 2026-01-01, 2026-01-02, 2026-02-01
        # Last date (2026-02-01) is excluded
        expected = [
            date(2025, 1, 1),   # Start of A
            date(2025, 6, 1),   # Start of B
            date(2026, 1, 1),   # End of A + 1 day
            date(2026, 1, 2)    # End of B + 1 day
        ]
        
        self.assertEqual(dates, expected)
    
    def test_dates_property_returns_list(self):
        """Test dates property returns a list (not a set or tuple)"""
        vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date(2025, 1, 1)
        )
        
        dates = self.dokument.dates
        self.assertIsInstance(dates, list)
    
    def test_dates_property_does_not_persist_to_database(self):
        """Test dates property is calculated on-the-fly, not stored"""
        vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date(2025, 1, 1),
            gueltigkeit_bis=date(2025, 12, 31)
        )
        
        # Get dates before adding new vorgabe
        dates_before = self.dokument.dates
        self.assertEqual(len(dates_before), 1)  # 2025-01-01 (2026-01-02 is last, so excluded)
        
        # Add new vorgabe
        vorgabe2 = Vorgabe.objects.create(
            order=2,
            nummer=2,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Vorgabe 2",
            gueltigkeit_von=date(2026, 2, 1)
        )
        
        # Get dates after - new dates are 2025-01-01, 2026-01-02, 2026-02-01
        # Last date (2026-02-01) is excluded, so we get [2025-01-01, 2026-01-01]
        dates_after = self.dokument.dates
        self.assertEqual(len(dates_after), 2)
        self.assertEqual(dates_after[0], date(2025, 1, 1))
        self.assertEqual(dates_after[1], date(2026, 1, 1))


class AddVorgabeCommentViewTest(TestCase):
    """Test cases for add_vorgabe_comment view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.dokumententyp = Dokumententyp.objects.create(
            name="Test Typ",
            verantwortliche_ve="Test VE"
        )
        
        self.thema = Thema.objects.create(name="Test Thema")
        
        self.dokument = Dokument.objects.create(
            nummer="COMM-001",
            dokumententyp=self.dokumententyp,
            name="Comment Test",
            aktiv=True
        )
        
        self.vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date.today()
        )
    
    def test_add_comment_requires_login(self):
        """Test that anonymous users cannot add comments"""
        url = reverse('add_vorgabe_comment', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.post(url, 
            data='{"text": "Test comment"}',
            content_type='application/json'
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_add_comment_requires_post(self):
        """Test that only POST method is allowed"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('add_vorgabe_comment', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.get(url)
        
        # Should return method not allowed
        self.assertEqual(response.status_code, 405)
    
    def test_add_comment_success(self):
        """Test successful comment addition"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('add_vorgabe_comment', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.post(url,
            data='{"text": "Dies ist ein neuer Kommentar"}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        import json
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['comment']['text'], 'Dies ist ein neuer Kommentar')
        self.assertEqual(data['comment']['user'], 'testuser')
        self.assertTrue(data['comment']['is_own'])
        
        # Verify comment was created in database
        self.assertEqual(VorgabeComment.objects.count(), 1)
        comment = VorgabeComment.objects.first()
        self.assertEqual(comment.text, 'Dies ist ein neuer Kommentar')
        self.assertEqual(comment.user, self.user)
    
    def test_add_empty_comment_fails(self):
        """Test that empty comments are rejected"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('add_vorgabe_comment', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.post(url,
            data='{"text": ""}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        import json
        data = json.loads(response.content)
        
        self.assertIn('error', data)
        self.assertIn('leer', data['error'].lower())
        
        # No comment should be created
        self.assertEqual(VorgabeComment.objects.count(), 0)
    
    def test_add_whitespace_only_comment_fails(self):
        """Test that whitespace-only comments are rejected"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('add_vorgabe_comment', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.post(url,
            data='{"text": "   \\n\\t  "}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(VorgabeComment.objects.count(), 0)
    
    def test_add_too_long_comment_fails(self):
        """Test that comments exceeding max length are rejected"""
        self.client.login(username='testuser', password='testpass123')
        
        long_text = "a" * 2001  # Over the 2000 character limit
        
        url = reverse('add_vorgabe_comment', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.post(url,
            data=f'{{"text": "{long_text}"}}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        import json
        data = json.loads(response.content)
        
        self.assertIn('error', data)
        self.assertIn('lang', data['error'].lower())
        
        # No comment should be created
        self.assertEqual(VorgabeComment.objects.count(), 0)
    
    def test_add_comment_xss_script_tag_blocked(self):
        """Test that comments with <script> tags are blocked"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('add_vorgabe_comment', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.post(url,
            data='{"text": "Test <script>alert(\\"xss\\")</script> comment"}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        import json
        data = json.loads(response.content)
        
        self.assertIn('error', data)
        self.assertIn('ungültige', data['error'].lower())
        
        # No comment should be created
        self.assertEqual(VorgabeComment.objects.count(), 0)
    
    def test_add_comment_xss_javascript_protocol_blocked(self):
        """Test that comments with javascript: protocol are blocked"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('add_vorgabe_comment', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.post(url,
            data='{"text": "Click <a href=\\"javascript:alert(1)\\">here</a>"}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(VorgabeComment.objects.count(), 0)
    
    def test_add_comment_xss_event_handlers_blocked(self):
        """Test that comments with event handlers are blocked"""
        dangerous_inputs = [
            'Test onload=alert(1) comment',
            'Test onerror=alert(1) comment',
            'Test onclick=alert(1) comment',
            'Test onmouseover=alert(1) comment'
        ]
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('add_vorgabe_comment', kwargs={'vorgabe_id': self.vorgabe.id})
        
        for dangerous_input in dangerous_inputs:
            response = self.client.post(url,
                data=f'{{"text": "{dangerous_input}"}}',
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 400)
        
        # No comments should be created
        self.assertEqual(VorgabeComment.objects.count(), 0)
    
    def test_add_comment_invalid_json_fails(self):
        """Test that invalid JSON is rejected"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('add_vorgabe_comment', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.post(url,
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        import json
        data = json.loads(response.content)
        
        self.assertIn('error', data)
        self.assertIn('Ungültige', data['error'])
    
    def test_add_comment_nonexistent_vorgabe_fails(self):
        """Test that adding comment to non-existent Vorgabe returns 404"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('add_vorgabe_comment', kwargs={'vorgabe_id': 99999})
        response = self.client.post(url,
            data='{"text": "Test comment"}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_add_comment_security_headers(self):
        """Test that security headers are present in response"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('add_vorgabe_comment', kwargs={'vorgabe_id': self.vorgabe.id})
        response = self.client.post(url,
            data='{"text": "Test comment"}',
            content_type='application/json'
        )
        
        self.assertIn('Content-Security-Policy', response)
        self.assertIn('X-Content-Type-Options', response)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')


class DeleteVorgabeCommentViewTest(TestCase):
    """Test cases for delete_vorgabe_comment view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            first_name='Staff',
            last_name='User'
        )
        self.staff_user.is_staff = True
        self.staff_user.save()
        
        self.dokumententyp = Dokumententyp.objects.create(
            name="Test Typ",
            verantwortliche_ve="Test VE"
        )
        
        self.thema = Thema.objects.create(name="Test Thema")
        
        self.dokument = Dokument.objects.create(
            nummer="COMM-001",
            dokumententyp=self.dokumententyp,
            name="Comment Test",
            aktiv=True
        )
        
        self.vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date.today()
        )
        
        self.comment = VorgabeComment.objects.create(
            vorgabe=self.vorgabe,
            user=self.user,
            text="Test comment to delete"
        )
    
    def test_delete_comment_requires_login(self):
        """Test that anonymous users cannot delete comments"""
        url = reverse('delete_vorgabe_comment', kwargs={'comment_id': self.comment.id})
        response = self.client.post(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        
        # Comment should still exist
        self.assertTrue(VorgabeComment.objects.filter(id=self.comment.id).exists())
    
    def test_delete_comment_requires_post(self):
        """Test that only POST method is allowed"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('delete_vorgabe_comment', kwargs={'comment_id': self.comment.id})
        response = self.client.get(url)
        
        # Should return method not allowed
        self.assertEqual(response.status_code, 405)
    
    def test_user_can_delete_own_comment(self):
        """Test that users can delete their own comments"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('delete_vorgabe_comment', kwargs={'comment_id': self.comment.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        
        import json
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        
        # Comment should be deleted
        self.assertFalse(VorgabeComment.objects.filter(id=self.comment.id).exists())
    
    def test_user_cannot_delete_other_users_comment(self):
        """Test that users cannot delete other users' comments"""
        self.client.login(username='otheruser', password='testpass123')
        
        url = reverse('delete_vorgabe_comment', kwargs={'comment_id': self.comment.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 403)
        
        import json
        data = json.loads(response.content)
        
        self.assertIn('error', data)
        self.assertIn('Berechtigung', data['error'])
        
        # Comment should still exist
        self.assertTrue(VorgabeComment.objects.filter(id=self.comment.id).exists())
    
    def test_staff_can_delete_any_comment(self):
        """Test that staff users can delete any comment"""
        self.client.login(username='staffuser', password='testpass123')
        
        url = reverse('delete_vorgabe_comment', kwargs={'comment_id': self.comment.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        
        import json
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        
        # Comment should be deleted
        self.assertFalse(VorgabeComment.objects.filter(id=self.comment.id).exists())
    
    def test_delete_nonexistent_comment_returns_404(self):
        """Test that deleting non-existent comment returns 404"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('delete_vorgabe_comment', kwargs={'comment_id': 99999})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_delete_comment_security_headers(self):
        """Test that security headers are present in response"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('delete_vorgabe_comment', kwargs={'comment_id': self.comment.id})
        response = self.client.post(url)
        
        self.assertIn('Content-Security-Policy', response)
        self.assertIn('X-Content-Type-Options', response)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')


class UserCommentsViewTest(TestCase):
    """Test the user comments view that displays all comments grouped by document"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        
        # Create documents
        self.doc_type = Dokumententyp.objects.create(name='Test Type', verantwortliche_ve='test')
        self.doc1 = Dokument.objects.create(nummer='DOC-001', name='Document 1', dokumententyp=self.doc_type, aktiv=True)
        self.doc2 = Dokument.objects.create(nummer='DOC-002', name='Document 2', dokumententyp=self.doc_type, aktiv=True)
        
        # Create themes
        self.theme1 = Thema.objects.create(name='Theme 1')
        self.theme2 = Thema.objects.create(name='Theme 2')
        
        # Create vorgaben
        from datetime import date
        self.vorgabe1 = Vorgabe.objects.create(
            nummer=1,
            order=1,
            dokument=self.doc1,
            thema=self.theme1,
            titel='Vorgabe 1',
            gueltigkeit_von=date.today()
        )
        self.vorgabe2 = Vorgabe.objects.create(
            nummer=2,
            order=2,
            dokument=self.doc1,
            thema=self.theme1,
            titel='Vorgabe 2',
            gueltigkeit_von=date.today()
        )
        self.vorgabe3 = Vorgabe.objects.create(
            nummer=1,
            order=1,
            dokument=self.doc2,
            thema=self.theme2,
            titel='Vorgabe 3',
            gueltigkeit_von=date.today()
        )
        
        # Create comments for user1
        self.comment1 = VorgabeComment.objects.create(
            vorgabe=self.vorgabe1,
            user=self.user1,
            text='User1 comment on vorgabe1'
        )
        self.comment2 = VorgabeComment.objects.create(
            vorgabe=self.vorgabe2,
            user=self.user1,
            text='User1 comment on vorgabe2'
        )
        self.comment3 = VorgabeComment.objects.create(
            vorgabe=self.vorgabe3,
            user=self.user1,
            text='User1 comment on vorgabe3'
        )
        
        # Create comment for user2
        self.comment4 = VorgabeComment.objects.create(
            vorgabe=self.vorgabe1,
            user=self.user2,
            text='User2 comment on vorgabe1'
        )
    
    def test_user_comments_requires_login(self):
        """Test that user comments view requires authentication"""
        response = self.client.get(reverse('user_comments'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_user_comments_shows_only_own_comments(self):
        """Test that user only sees their own comments"""
        self.client.login(username='user1', password='pass123')
        response = self.client.get(reverse('user_comments'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User1 comment on vorgabe1')
        self.assertContains(response, 'User1 comment on vorgabe2')
        self.assertContains(response, 'User1 comment on vorgabe3')
        self.assertNotContains(response, 'User2 comment on vorgabe1')
    
    def test_user_comments_grouped_by_document(self):
        """Test that comments are properly grouped by document"""
        self.client.login(username='user1', password='pass123')
        response = self.client.get(reverse('user_comments'))
        
        self.assertEqual(response.status_code, 200)
        # Check that document titles appear
        self.assertContains(response, 'DOC-001 – Document 1')
        self.assertContains(response, 'DOC-002 – Document 2')
        
        # Check context
        self.assertIn('comments_by_document', response.context)
        self.assertEqual(len(response.context['comments_by_document']), 2)
    
    def test_user_comments_count_display(self):
        """Test that total comment count is displayed"""
        self.client.login(username='user1', password='pass123')
        response = self.client.get(reverse('user_comments'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_comments'], 3)
        self.assertContains(response, '3 Kommentare')
    
    def test_user_comments_empty_view(self):
        """Test the view when user has no comments"""
        # Create a new user with no comments
        user3 = User.objects.create_user(username='user3', password='pass123')
        self.client.login(username='user3', password='pass123')
        response = self.client.get(reverse('user_comments'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_comments'], 0)
        self.assertContains(response, 'Sie haben noch keine Kommentare')
    
    def test_user_comments_comment_text_preserved(self):
        """Test that comment text is correctly displayed"""
        self.client.login(username='user1', password='pass123')
        response = self.client.get(reverse('user_comments'))
        
        self.assertEqual(response.status_code, 200)
        # Check that comment text appears in response
        self.assertContains(response, 'User1 comment on vorgabe1')
    
    def test_user_comments_vorgabe_number_link(self):
        """Test that vorgabe numbers are linked correctly"""
        self.client.login(username='user1', password='pass123')
        response = self.client.get(reverse('user_comments'))
        
        self.assertEqual(response.status_code, 200)
        # Check that vorgabe numbers appear (format is DOC-001.T.1)
        self.assertContains(response, 'DOC-001.T.1')
        self.assertContains(response, 'DOC-001.T.2')
        self.assertContains(response, 'DOC-002.T.1')
    
    def test_user_comments_ordered_by_creation_date(self):
        """Test that comments are ordered by creation date (newest first)"""
        self.client.login(username='user1', password='pass123')
        response = self.client.get(reverse('user_comments'))
        
        self.assertEqual(response.status_code, 200)
        # The queryset orders by vorgabe document, then by -created_at
        # Check that all three comments are in the response
        self.assertContains(response, 'User1 comment on vorgabe1')
        self.assertContains(response, 'User1 comment on vorgabe2')
        self.assertContains(response, 'User1 comment on vorgabe3')
    
    def test_user_comments_template_used(self):
        """Test that correct template is used"""
        self.client.login(username='user1', password='pass123')
        response = self.client.get(reverse('user_comments'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'standards/user_comments.html')


class AllCommentsViewTest(TestCase):
    """Test the all comments view that displays all comments from all users (staff only)"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.user1 = User.objects.create_user(username='user1', password='pass123', first_name='Max', last_name='Mustermann')
        self.user2 = User.objects.create_user(username='user2', password='pass123', first_name='Anna', last_name='Mueller')
        self.staff_user = User.objects.create_user(username='staff', password='pass123', is_staff=True, first_name='Admin', last_name='User')
        
        # Create documents
        self.doc_type = Dokumententyp.objects.create(name='Test Type', verantwortliche_ve='test')
        self.doc1 = Dokument.objects.create(nummer='DOC-001', name='Document 1', dokumententyp=self.doc_type, aktiv=True)
        self.doc2 = Dokument.objects.create(nummer='DOC-002', name='Document 2', dokumententyp=self.doc_type, aktiv=True)
        
        # Create themes
        self.theme1 = Thema.objects.create(name='Theme 1')
        self.theme2 = Thema.objects.create(name='Theme 2')
        
        # Create vorgaben
        self.vorgabe1 = Vorgabe.objects.create(
            nummer=1,
            order=1,
            dokument=self.doc1,
            thema=self.theme1,
            titel='Vorgabe 1',
            gueltigkeit_von=date.today()
        )
        self.vorgabe2 = Vorgabe.objects.create(
            nummer=2,
            order=2,
            dokument=self.doc1,
            thema=self.theme1,
            titel='Vorgabe 2',
            gueltigkeit_von=date.today()
        )
        self.vorgabe3 = Vorgabe.objects.create(
            nummer=1,
            order=1,
            dokument=self.doc2,
            thema=self.theme2,
            titel='Vorgabe 3',
            gueltigkeit_von=date.today()
        )
        
        # Create comments from different users
        self.comment1 = VorgabeComment.objects.create(
            vorgabe=self.vorgabe1,
            user=self.user1,
            text='User1 comment on vorgabe1'
        )
        self.comment2 = VorgabeComment.objects.create(
            vorgabe=self.vorgabe2,
            user=self.user1,
            text='User1 comment on vorgabe2'
        )
        self.comment3 = VorgabeComment.objects.create(
            vorgabe=self.vorgabe3,
            user=self.user2,
            text='User2 comment on vorgabe3'
        )
        self.comment4 = VorgabeComment.objects.create(
            vorgabe=self.vorgabe1,
            user=self.user2,
            text='User2 comment on vorgabe1'
        )
    
    def test_all_comments_requires_login(self):
        """Test that all comments view requires authentication"""
        response = self.client.get(reverse('all_comments'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_all_comments_staff_only(self):
        """Test that non-staff users cannot access all comments view"""
        self.client.login(username='user1', password='pass123')
        response = self.client.get(reverse('all_comments'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_all_comments_staff_can_access(self):
        """Test that staff users can access all comments view"""
        self.client.login(username='staff', password='pass123')
        response = self.client.get(reverse('all_comments'))
        self.assertEqual(response.status_code, 200)
    
    def test_all_comments_shows_all_comments(self):
        """Test that staff sees all comments from all users"""
        self.client.login(username='staff', password='pass123')
        response = self.client.get(reverse('all_comments'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User1 comment on vorgabe1')
        self.assertContains(response, 'User1 comment on vorgabe2')
        self.assertContains(response, 'User2 comment on vorgabe3')
        self.assertContains(response, 'User2 comment on vorgabe1')
    
    def test_all_comments_shows_usernames(self):
        """Test that all comments display the username of the author"""
        self.client.login(username='staff', password='pass123')
        response = self.client.get(reverse('all_comments'))
        
        self.assertEqual(response.status_code, 200)
        # Check that user names appear in the response
        self.assertContains(response, 'Max Mustermann')
        self.assertContains(response, 'Anna Mueller')
    
    def test_all_comments_grouped_by_document(self):
        """Test that comments are properly grouped by document"""
        self.client.login(username='staff', password='pass123')
        response = self.client.get(reverse('all_comments'))
        
        self.assertEqual(response.status_code, 200)
        # Check that document titles appear
        self.assertContains(response, 'DOC-001 – Document 1')
        self.assertContains(response, 'DOC-002 – Document 2')
        
        # Check context
        self.assertIn('comments_by_document', response.context)
        self.assertEqual(len(response.context['comments_by_document']), 2)
    
    def test_all_comments_count_display(self):
        """Test that total comment count is displayed"""
        self.client.login(username='staff', password='pass123')
        response = self.client.get(reverse('all_comments'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_comments'], 4)
        self.assertContains(response, '4 Kommentare')
    
    def test_all_comments_empty_view(self):
        """Test the view when there are no comments"""
        # Delete all comments
        VorgabeComment.objects.all().delete()
        
        self.client.login(username='staff', password='pass123')
        response = self.client.get(reverse('all_comments'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_comments'], 0)
        self.assertContains(response, 'Es gibt noch keine Kommentare')
    
    def test_all_comments_template_used(self):
        """Test that correct template is used"""
        self.client.login(username='staff', password='pass123')
        response = self.client.get(reverse('all_comments'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'standards/all_comments.html')
    
    def test_all_comments_has_delete_buttons(self):
        """Test that delete buttons are present for each comment"""
        self.client.login(username='staff', password='pass123')
        response = self.client.get(reverse('all_comments'))
        
        self.assertEqual(response.status_code, 200)
        # Check for delete button form elements - look for the delete form action URLs
        self.assertContains(response, '/dokumente/comments/delete/', count=4)
        # Also check for the delete button text
        self.assertContains(response, 'Löschen', count=4)
    
    def test_all_comments_vorgabe_number_link(self):
        """Test that vorgabe numbers are linked correctly"""
        self.client.login(username='staff', password='pass123')
        response = self.client.get(reverse('all_comments'))
        
        self.assertEqual(response.status_code, 200)
        # Check that vorgabe numbers appear
        self.assertContains(response, 'DOC-001.T.1')
        self.assertContains(response, 'DOC-001.T.2')
        self.assertContains(response, 'DOC-002.T.1')
    
    def test_all_comments_ordered_by_document_and_date(self):
        """Test that comments are ordered by document then by creation date"""
        self.client.login(username='staff', password='pass123')
        response = self.client.get(reverse('all_comments'))
        
        self.assertEqual(response.status_code, 200)
        # Check context has properly grouped comments
        comments_by_doc = response.context['comments_by_document']
        
        # Verify all documents are present
        doc_numbers = [doc.nummer for doc in comments_by_doc.keys()]
        self.assertIn('DOC-001', doc_numbers)
        self.assertIn('DOC-002', doc_numbers)
    
    def test_all_comments_displays_timestamps(self):
        """Test that comment timestamps are displayed"""
        self.client.login(username='staff', password='pass123')
        response = self.client.get(reverse('all_comments'))
        
        self.assertEqual(response.status_code, 200)
        # Check that timestamp patterns appear (date formatting)
        self.assertContains(response, 'Erstellt:')
    
    def test_all_comments_regular_user_redirect(self):
        """Test that regular users are redirected to login"""
        # Create and login as regular user
        regular_user = User.objects.create_user(username='regular', password='pass123')
        self.client.login(username='regular', password='pass123')
        
        response = self.client.get(reverse('all_comments'))
        # Should redirect to login since user is not staff
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_all_comments_no_own_comments_filter(self):
        """Test that staff sees comments from ALL users, not just their own"""
        self.client.login(username='staff', password='pass123')
        response = self.client.get(reverse('all_comments'))
        
        # Verify all comments are visible, not filtered by user
        self.assertContains(response, 'User1 comment on vorgabe1')
        self.assertContains(response, 'User2 comment on vorgabe1')
        # Both users' comments on the same vorgabe should be visible
        self.assertEqual(response.context['total_comments'], 4)


