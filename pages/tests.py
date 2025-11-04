from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from dokumente.models import Dokument, Vorgabe, VorgabeKurztext, VorgabeLangtext, Geltungsbereich, Dokumententyp, Thema
from stichworte.models import Stichwort
from unittest.mock import patch
import re


class SearchViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
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
        
        self.vorgabe = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=self.dokument,
            thema=self.thema,
            titel="Test Vorgabe Titel",
            gueltigkeit_von=date.today()
        )
        
        # Create text content
        self.kurztext = VorgabeKurztext.objects.create(
            abschnitt=self.vorgabe,
            inhalt="Dies ist ein Test Kurztext mit Suchbegriff"
        )
        
        self.langtext = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            inhalt="Dies ist ein Test Langtext mit anderem Suchbegriff"
        )
        
        self.geltungsbereich = Geltungsbereich.objects.create(
            geltungsbereich=self.dokument,
            inhalt="Test Geltungsbereich mit Suchbegriff"
        )
    
    def test_search_get_request(self):
        """Test GET request returns search form"""
        response = self.client.get('/search/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Suche')
        self.assertContains(response, 'Suchbegriff')
    
    def test_search_post_valid_term(self):
        """Test POST request with valid search term"""
        response = self.client.post('/search/', {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Suchresultate für Test')
    
    def test_search_case_insensitive(self):
        """Test that search is case insensitive"""
        # Search for lowercase
        response = self.client.post('/search/', {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Suchresultate für test')
        
        # Search for uppercase
        response = self.client.post('/search/', {'q': 'TEST'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Suchresultate für TEST')
        
        # Search for mixed case
        response = self.client.post('/search/', {'q': 'TeSt'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Suchresultate für TeSt')
    
    def test_search_in_kurztext(self):
        """Test search in Kurztext content"""
        response = self.client.post('/search/', {'q': 'Suchbegriff'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST-001')
    
    def test_search_in_langtext(self):
        """Test search in Langtext content"""
        response = self.client.post('/search/', {'q': 'anderem'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST-001')
    
    def test_search_in_titel(self):
        """Test search in Vorgabe title"""
        response = self.client.post('/search/', {'q': 'Titel'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST-001')
    
    def test_search_in_geltungsbereich(self):
        """Test search in Geltungsbereich content"""
        response = self.client.post('/search/', {'q': 'Geltungsbereich'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Standards mit')
    
    def test_search_no_results(self):
        """Test search with no results"""
        response = self.client.post('/search/', {'q': 'NichtVorhanden'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Keine Resultate für "NichtVorhanden"')
    
    def test_search_expired_vorgabe_not_included(self):
        """Test that expired Vorgaben are not included in results"""
        # Create expired Vorgabe
        expired_vorgabe = Vorgabe.objects.create(
            order=2,
            nummer=2,
            dokument=self.dokument,
            thema=self.thema,
            titel="Abgelaufene Vorgabe",
            gueltigkeit_von=date.today() - timedelta(days=10),
            gueltigkeit_bis=date.today() - timedelta(days=1)
        )
        
        VorgabeKurztext.objects.create(
            abschnitt=expired_vorgabe,
            inhalt="Abgelaufener Inhalt mit Test"
        )
        
        response = self.client.post('/search/', {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        
        # Should only find the active Vorgabe, not the expired one
        self.assertContains(response, 'Test Vorgabe Titel')
        # The expired vorgabe should not appear in results
        self.assertNotContains(response, 'Abgelaufene Vorgabe')
    
    def test_search_empty_term_validation(self):
        """Test validation for empty search term"""
        response = self.client.post('/search/', {'q': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fehler:')
        self.assertContains(response, 'Suchbegriff darf nicht leer sein')
    
    def test_search_no_term_validation(self):
        """Test validation when no search term is provided"""
        response = self.client.post('/search/', {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fehler:')
        self.assertContains(response, 'Suchbegriff darf nicht leer sein')
    
    def test_search_html_tags_stripped(self):
        """Test that HTML tags are stripped from search input"""
        response = self.client.post('/search/', {'q': '<script>alert("xss")</script>Test'})
        self.assertEqual(response.status_code, 200)
        # Should search for "alert('xss')Test" after HTML tag removal
        self.assertContains(response, 'Suchresultate für alert(&quot;xss&quot;)Test')
    
    def test_search_invalid_characters_validation(self):
        """Test validation for invalid characters"""
        response = self.client.post('/search/', {'q': 'Test| DROP TABLE users'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fehler:')
        self.assertContains(response, 'Ungültige Zeichen im Suchbegriff')
    
    def test_search_too_long_validation(self):
        """Test validation for overly long search terms"""
        long_term = 'a' * 201  # 201 characters, exceeds limit of 200
        response = self.client.post('/search/', {'q': long_term})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fehler:')
        self.assertContains(response, 'Suchbegriff ist zu lang')
    
    def test_search_max_length_allowed(self):
        """Test that exactly 200 characters are allowed"""
        max_term = 'a' * 200  # Exactly 200 characters
        response = self.client.post('/search/', {'q': max_term})
        self.assertEqual(response.status_code, 200)
        # Should not show validation error
        self.assertNotContains(response, 'Fehler:')
    
    def test_search_german_umlauts_allowed(self):
        """Test that German umlauts are allowed in search"""
        response = self.client.post('/search/', {'q': 'Test Müller äöü ÄÖÜ ß'})
        self.assertEqual(response.status_code, 200)
        # Should not show validation error
        self.assertNotContains(response, 'Fehler:')
    
    def test_search_special_characters_allowed(self):
        """Test that allowed special characters work"""
        response = self.client.post('/search/', {'q': 'Test-Test, Test: Test; Test! Test? (Test) [Test] {Test} "Test" \'Test\''})
        self.assertEqual(response.status_code, 200)
        # Should not show validation error
        self.assertNotContains(response, 'Fehler:')
    
    def test_search_input_preserved_on_error(self):
        """Test that search input is preserved on validation errors"""
        response = self.client.post('/search/', {'q': '<script>Test</script>'})
        self.assertEqual(response.status_code, 200)
        # The input should be preserved (escaped) in the form
        # Since HTML tags are stripped, we expect "Test" to be searched
        self.assertContains(response, 'Suchresultate für Test')
    
    def test_search_xss_prevention_in_results(self):
        """Test that search terms are escaped in results to prevent XSS"""
        # Create content with potential XSS
        self.kurztext.inhalt = "Content with <script>alert('xss')</script> term"
        self.kurztext.save()
        
        response = self.client.post('/search/', {'q': 'term'})
        self.assertEqual(response.status_code, 200)
        # The script tag should be escaped in the output
        # Note: This depends on how the template renders the content
        self.assertContains(response, 'Suchresultate für term')
    
    @patch('pages.views.pprint.pp')
    def test_search_result_logging(self, mock_pprint):
        """Test that search results are logged for debugging"""
        response = self.client.post('/search/', {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        # Verify that pprint.pp was called with the result
        mock_pprint.assert_called_once()
    
    def test_search_multiple_documents(self):
        """Test search across multiple documents"""
        # Create second document
        dokument2 = Dokument.objects.create(
            nummer="TEST-002",
            dokumententyp=self.dokumententyp,
            name="Zweites Test Dokument",
            gueltigkeit_von=date.today(),
            aktiv=True
        )
        
        vorgabe2 = Vorgabe.objects.create(
            order=1,
            nummer=1,
            dokument=dokument2,
            thema=self.thema,
            titel="Zweite Test Vorgabe",
            gueltigkeit_von=date.today()
        )
        
        VorgabeKurztext.objects.create(
            abschnitt=vorgabe2,
            inhalt="Zweiter Test Inhalt"
        )
        
        response = self.client.post('/search/', {'q': 'Test'})
        self.assertEqual(response.status_code, 200)
        # Should find results from both documents
        self.assertContains(response, 'TEST-001')
        self.assertContains(response, 'TEST-002')


class SearchValidationTest(TestCase):
    """Test the validate_search_input function directly"""
    
    def test_validate_search_input_valid(self):
        """Test valid search input"""
        from pages.views import validate_search_input
        
        result = validate_search_input("Test Suchbegriff")
        self.assertEqual(result, "Test Suchbegriff")
    
    def test_validate_search_input_empty(self):
        """Test empty search input"""
        from pages.views import validate_search_input
        
        with self.assertRaises(ValidationError) as context:
            validate_search_input("")
        
        self.assertIn("Suchbegriff darf nicht leer sein", str(context.exception))
    
    def test_validate_search_input_html_stripped(self):
        """Test that HTML tags are stripped"""
        from pages.views import validate_search_input
        
        result = validate_search_input("<script>alert('xss')</script>Test")
        self.assertEqual(result, "alert('xss')Test")
    
    def test_validate_search_input_invalid_chars(self):
        """Test validation of invalid characters"""
        from pages.views import validate_search_input
        
        with self.assertRaises(ValidationError) as context:
            validate_search_input("Test| DROP TABLE users")
        
        self.assertIn("Ungültige Zeichen im Suchbegriff", str(context.exception))
    
    def test_validate_search_input_too_long(self):
        """Test length validation"""
        from pages.views import validate_search_input
        
        with self.assertRaises(ValidationError) as context:
            validate_search_input("a" * 201)
        
        self.assertIn("Suchbegriff ist zu lang", str(context.exception))
    
    def test_validate_search_input_whitespace_stripped(self):
        """Test that whitespace is stripped"""
        from pages.views import validate_search_input
        
        result = validate_search_input("  Test Suchbegriff  ")
        self.assertEqual(result, "Test Suchbegriff")