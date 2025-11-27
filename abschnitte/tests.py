from django.test import TestCase, TransactionTestCase
from django.core.management import call_command
from django.conf import settings
from django.core.files.storage import default_storage
from unittest.mock import patch, Mock, MagicMock
from io import StringIO
import os
import hashlib
import tempfile
import shutil

from .models import AbschnittTyp, Textabschnitt
from .utils import render_textabschnitte, md_table_to_html
from diagramm_proxy.diagram_cache import (
    get_cached_diagram, compute_hash, get_cache_path, clear_cache
)


class AbschnittTypModelTest(TestCase):
    """Test cases for AbschnittTyp model"""

    def setUp(self):
        """Set up test data"""
        self.abschnitttyp = AbschnittTyp.objects.create(
            abschnitttyp="text"
        )

    def test_abschnitttyp_creation(self):
        """Test that AbschnittTyp is created correctly"""
        self.assertEqual(self.abschnitttyp.abschnitttyp, "text")

    def test_abschnitttyp_str(self):
        """Test string representation of AbschnittTyp"""
        self.assertEqual(str(self.abschnitttyp), "text")

    def test_abschnitttyp_verbose_name_plural(self):
        """Test verbose name plural"""
        self.assertEqual(
            AbschnittTyp._meta.verbose_name_plural,
            "Abschnitttypen"
        )

    def test_abschnitttyp_primary_key(self):
        """Test that abschnitttyp field is the primary key"""
        pk_field = AbschnittTyp._meta.pk
        self.assertEqual(pk_field.name, 'abschnitttyp')

    def test_create_multiple_abschnitttypen(self):
        """Test creating multiple AbschnittTyp objects"""
        types = ['liste ungeordnet', 'liste geordnet', 'tabelle', 'diagramm', 'code']
        for typ in types:
            AbschnittTyp.objects.create(abschnitttyp=typ)

        self.assertEqual(AbschnittTyp.objects.count(), 6)  # Including setUp type


class TextabschnittModelTest(TestCase):
    """Test cases for Textabschnitt abstract model using VorgabeLangtext"""

    def setUp(self):
        """Set up test data"""
        from dokumente.models import Dokumententyp, Dokument, Vorgabe, VorgabeLangtext, Thema
        from datetime import date

        self.typ_text = AbschnittTyp.objects.create(abschnitttyp="text")
        self.typ_code = AbschnittTyp.objects.create(abschnitttyp="code")

        # Create required dokumente objects
        self.dokumententyp = Dokumententyp.objects.create(
            name="Test Type", verantwortliche_ve="TEST"
        )
        self.dokument = Dokument.objects.create(
            nummer="TEST-001",
            name="Test Doc",
            dokumententyp=self.dokumententyp,
            aktiv=True
        )
        self.thema = Thema.objects.create(name="Test Thema")
        self.vorgabe = Vorgabe.objects.create(
            dokument=self.dokument,
            nummer=1,
            order=1,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date.today()
        )

    def test_textabschnitt_creation(self):
        """Test that Textabschnitt can be instantiated via concrete model"""
        from dokumente.models import VorgabeLangtext

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_text,
            inhalt="Test content",
            order=1
        )
        self.assertEqual(abschnitt.abschnitttyp, self.typ_text)
        self.assertEqual(abschnitt.inhalt, "Test content")
        self.assertEqual(abschnitt.order, 1)

    def test_textabschnitt_default_order(self):
        """Test that order defaults to 0"""
        from dokumente.models import VorgabeLangtext

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_text,
            inhalt="Test"
        )
        self.assertEqual(abschnitt.order, 0)

    def test_textabschnitt_blank_fields(self):
        """Test that abschnitttyp and inhalt can be blank/null"""
        from dokumente.models import VorgabeLangtext

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe
        )
        self.assertIsNone(abschnitt.abschnitttyp)
        self.assertIsNone(abschnitt.inhalt)

    def test_textabschnitt_ordering(self):
        """Test that Textabschnitte can be ordered"""
        from dokumente.models import VorgabeLangtext

        abschnitt1 = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_text,
            inhalt="First",
            order=2
        )
        abschnitt2 = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_text,
            inhalt="Second",
            order=1
        )
        abschnitt3 = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_text,
            inhalt="Third",
            order=3
        )

        ordered = VorgabeLangtext.objects.filter(abschnitt=self.vorgabe).order_by('order')
        self.assertEqual(list(ordered), [abschnitt2, abschnitt1, abschnitt3])

    def test_textabschnitt_foreign_key_protection(self):
        """Test that AbschnittTyp is protected from deletion"""
        from dokumente.models import VorgabeLangtext
        from django.db.models import ProtectedError

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_text,
            inhalt="Test"
        )

        # Try to delete the AbschnittTyp
        with self.assertRaises(ProtectedError):
            self.typ_text.delete()


class RenderTextabschnitteTest(TestCase):
    """Test cases for render_textabschnitte function"""

    def setUp(self):
        """Set up test data"""
        from dokumente.models import Dokumententyp, Dokument, Vorgabe, VorgabeLangtext, Thema
        from datetime import date

        self.typ_text = AbschnittTyp.objects.create(abschnitttyp="text")
        self.typ_unordered = AbschnittTyp.objects.create(abschnitttyp="liste ungeordnet")
        self.typ_ordered = AbschnittTyp.objects.create(abschnitttyp="liste geordnet")
        self.typ_table = AbschnittTyp.objects.create(abschnitttyp="tabelle")
        self.typ_code = AbschnittTyp.objects.create(abschnitttyp="code")
        self.typ_diagram = AbschnittTyp.objects.create(abschnitttyp="diagramm")

        # Create required dokumente objects
        self.dokumententyp = Dokumententyp.objects.create(
            name="Test Type", verantwortliche_ve="TEST"
        )
        self.dokument = Dokument.objects.create(
            nummer="TEST-001",
            name="Test Doc",
            dokumententyp=self.dokumententyp,
            aktiv=True
        )
        self.thema = Thema.objects.create(name="Test Thema")
        self.vorgabe = Vorgabe.objects.create(
            dokument=self.dokument,
            nummer=1,
            order=1,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date.today()
        )

    def test_render_empty_queryset(self):
        """Test rendering an empty queryset"""
        from dokumente.models import VorgabeLangtext

        result = render_textabschnitte(VorgabeLangtext.objects.none())
        self.assertEqual(result, [])

    def test_render_text_markdown(self):
        """Test rendering plain text with markdown"""
        from dokumente.models import VorgabeLangtext

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_text,
            inhalt="# Heading\n\nThis is **bold** text.",
            order=1
        )

        result = render_textabschnitte(VorgabeLangtext.objects.filter(abschnitt=self.vorgabe))
        self.assertEqual(len(result), 1)
        typ, html = result[0]
        self.assertEqual(typ, "text")
        self.assertIn("<h1>Heading</h1>", html)
        self.assertIn("<strong>bold</strong>", html)

    def test_render_text_with_footnotes(self):
        """Test rendering text with footnotes"""
        from dokumente.models import VorgabeLangtext

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_text,
            inhalt="This is text[^1].\n\n[^1]: This is a footnote.",
            order=1
        )

        result = render_textabschnitte(VorgabeLangtext.objects.filter(abschnitt=self.vorgabe))
        typ, html = result[0]
        self.assertIn("footnote", html.lower())

    def test_render_unordered_list(self):
        """Test rendering unordered list"""
        from dokumente.models import VorgabeLangtext

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_unordered,
            inhalt="Item 1\nItem 2\nItem 3",
            order=1
        )

        result = render_textabschnitte(VorgabeLangtext.objects.filter(abschnitt=self.vorgabe))
        typ, html = result[0]
        self.assertEqual(typ, "liste ungeordnet")
        self.assertIn("<ul>", html)
        self.assertIn("<li>Item 1</li>", html)
        self.assertIn("<li>Item 2</li>", html)
        self.assertIn("<li>Item 3</li>", html)

    def test_render_ordered_list(self):
        """Test rendering ordered list"""
        from dokumente.models import VorgabeLangtext

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_ordered,
            inhalt="First item\nSecond item\nThird item",
            order=1
        )

        result = render_textabschnitte(VorgabeLangtext.objects.filter(abschnitt=self.vorgabe))
        typ, html = result[0]
        self.assertEqual(typ, "liste geordnet")
        self.assertIn("<ol>", html)
        self.assertIn("<li>First item</li>", html)
        self.assertIn("<li>Second item</li>", html)
        self.assertIn("<li>Third item</li>", html)

    def test_render_table(self):
        """Test rendering table"""
        from dokumente.models import VorgabeLangtext

        table_content = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |"""

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_table,
            inhalt=table_content,
            order=1
        )

        result = render_textabschnitte(VorgabeLangtext.objects.filter(abschnitt=self.vorgabe))
        typ, html = result[0]
        self.assertEqual(typ, "tabelle")
        self.assertIn('<table class="table table-bordered table-hover">', html)
        self.assertIn("<thead>", html)
        self.assertIn("<th>Header 1</th>", html)
        self.assertIn("<th>Header 2</th>", html)
        self.assertIn("<tbody>", html)
        self.assertIn("<td>Cell 1</td>", html)
        self.assertIn("<td>Cell 2</td>", html)

    def test_render_code_block(self):
        """Test rendering code block"""
        from dokumente.models import VorgabeLangtext

        code_content = "def hello():\n    print('Hello, World!')"

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_code,
            inhalt=code_content,
            order=1
        )

        result = render_textabschnitte(VorgabeLangtext.objects.filter(abschnitt=self.vorgabe))
        typ, html = result[0]
        self.assertEqual(typ, "code")
        self.assertIn("<pre><code>", html)
        self.assertIn("</code></pre>", html)
        self.assertIn("hello", html)

    @patch('abschnitte.utils.get_cached_diagram')
    def test_render_diagram_success(self, mock_get_cached):
        """Test rendering diagram with successful caching"""
        from dokumente.models import VorgabeLangtext

        mock_get_cached.return_value = "diagram_cache/plantuml/abc123.svg"

        diagram_content = """plantuml
@startuml
Alice -> Bob: Hello
@enduml"""

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_diagram,
            inhalt=diagram_content,
            order=1
        )

        result = render_textabschnitte(VorgabeLangtext.objects.filter(abschnitt=self.vorgabe))
        typ, html = result[0]
        self.assertEqual(typ, "diagramm")
        self.assertIn('<img', html)
        self.assertIn('width="100%"', html)
        self.assertIn('diagram_cache/plantuml/abc123.svg', html)

        # Verify get_cached_diagram was called correctly
        mock_get_cached.assert_called_once()
        args = mock_get_cached.call_args[0]
        self.assertEqual(args[0], "plantuml")
        self.assertIn("Alice -> Bob", args[1])

    @patch('abschnitte.utils.get_cached_diagram')
    def test_render_diagram_with_options(self, mock_get_cached):
        """Test rendering diagram with custom options"""
        from dokumente.models import VorgabeLangtext

        mock_get_cached.return_value = "diagram_cache/mermaid/xyz789.svg"

        diagram_content = """mermaid
option: width="50%" height="300px"
graph TD
    A-->B"""

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_diagram,
            inhalt=diagram_content,
            order=1
        )

        result = render_textabschnitte(VorgabeLangtext.objects.filter(abschnitt=self.vorgabe))
        typ, html = result[0]
        self.assertIn('width="50%"', html)
        self.assertIn('height="300px"', html)

    @patch('abschnitte.utils.get_cached_diagram')
    def test_render_diagram_error(self, mock_get_cached):
        """Test rendering diagram when caching fails"""
        from dokumente.models import VorgabeLangtext

        mock_get_cached.side_effect = Exception("Connection error")

        diagram_content = """plantuml
@startuml
A -> B
@enduml"""

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_diagram,
            inhalt=diagram_content,
            order=1
        )

        result = render_textabschnitte(VorgabeLangtext.objects.filter(abschnitt=self.vorgabe))
        typ, html = result[0]
        self.assertIn("Error generating diagram", html)
        self.assertIn("Connection error", html)
        self.assertIn('class="text-danger"', html)

    def test_render_multiple_abschnitte(self):
        """Test rendering multiple Textabschnitte in order"""
        from dokumente.models import VorgabeLangtext

        abschnitt1 = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_text,
            inhalt="First section",
            order=1
        )
        abschnitt2 = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_unordered,
            inhalt="Item 1\nItem 2",
            order=2
        )
        abschnitt3 = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_code,
            inhalt="print('hello')",
            order=3
        )

        result = render_textabschnitte(
            VorgabeLangtext.objects.filter(abschnitt=self.vorgabe).order_by('order')
        )

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][0], "text")
        self.assertEqual(result[1][0], "liste ungeordnet")
        self.assertEqual(result[2][0], "code")

    def test_render_abschnitt_without_type(self):
        """Test rendering Textabschnitt without AbschnittTyp"""
        from dokumente.models import VorgabeLangtext

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=None,
            inhalt="Content without type",
            order=1
        )

        result = render_textabschnitte(VorgabeLangtext.objects.filter(abschnitt=self.vorgabe))
        typ, html = result[0]
        self.assertEqual(typ, '')
        self.assertIn("Content without type", html)

    def test_render_abschnitt_with_empty_content(self):
        """Test rendering Textabschnitt with empty content"""
        from dokumente.models import VorgabeLangtext

        abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_text,
            inhalt=None,
            order=1
        )

        result = render_textabschnitte(VorgabeLangtext.objects.filter(abschnitt=self.vorgabe))
        self.assertEqual(len(result), 1)
        typ, html = result[0]
        self.assertEqual(typ, "text")

    def test_render_textabschnitte_xss_prevention(self):
        """Test that malicious HTML is sanitized in rendered content"""
        from dokumente.models import VorgabeLangtext

        # Create content with malicious HTML
        malicious_abschnitt = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_text,
            inhalt='<script>alert("xss")</script><img src=x onerror=alert(1)>Normal text',
            order=1
        )

        result = render_textabschnitte(VorgabeLangtext.objects.filter(pk=malicious_abschnitt.pk))

        self.assertEqual(len(result), 1)
        typ, html = result[0]
        self.assertEqual(typ, "text")

        # Dangerous tags and attributes should be removed or sanitized
        self.assertNotIn('<script>', html)  # Script tags should not be present unescaped
        self.assertNotIn('onerror', html)   # Dangerous attributes removed
        # Note: 'alert' may still be present in escaped script tags, which is safe

        # Safe content should remain
        self.assertIn('Normal text', html)


class MdTableToHtmlTest(TestCase):
    """Test cases for md_table_to_html function"""

    def test_simple_table(self):
        """Test converting a simple markdown table to HTML"""
        md = """| Name | Age |
|------|-----|
| John | 30  |
| Jane | 25  |"""

        html = md_table_to_html(md)

        self.assertIn('<table class="table table-bordered table-hover">', html)
        self.assertIn("<thead>", html)
        self.assertIn("<th>Name</th>", html)
        self.assertIn("<th>Age</th>", html)
        self.assertIn("<tbody>", html)
        self.assertIn("<td>John</td>", html)
        self.assertIn("<td>30</td>", html)
        self.assertIn("<td>Jane</td>", html)
        self.assertIn("<td>25</td>", html)

    def test_table_with_multiple_rows(self):
        """Test table with multiple rows"""
        md = """| A | B | C |
|---|---|---|
| 1 | 2 | 3 |
| 4 | 5 | 6 |
| 7 | 8 | 9 |"""

        html = md_table_to_html(md)

        self.assertEqual(html.count("<tr>"), 4)  # 1 header + 3 body rows
        self.assertEqual(html.count("<td>"), 9)  # 3x3 cells
        self.assertEqual(html.count("<th>"), 3)  # 3 headers

    def test_table_with_spaces(self):
        """Test table with extra spaces"""
        md = """  |  Header 1  |  Header 2  |
  | --------- | ---------- |
  |  Value 1  |  Value 2   |  """

        html = md_table_to_html(md)

        self.assertIn("<th>Header 1</th>", html)
        self.assertIn("<th>Header 2</th>", html)
        self.assertIn("<td>Value 1</td>", html)
        self.assertIn("<td>Value 2</td>", html)

    def test_table_with_empty_cells(self):
        """Test table with empty cells"""
        md = """| Col1 | Col2 | Col3 |
|------|------|------|
| A    |      | C    |
|      | B    |      |"""

        html = md_table_to_html(md)

        self.assertIn("<td>A</td>", html)
        self.assertIn("<td></td>", html)
        self.assertIn("<td>C</td>", html)
        self.assertIn("<td>B</td>", html)

    def test_table_insufficient_lines(self):
        """Test that ValueError is raised for insufficient lines"""
        md = """| Header |"""

        with self.assertRaises(ValueError) as context:
            md_table_to_html(md)

        self.assertIn("at least header + separator", str(context.exception))

    def test_table_empty_string(self):
        """Test that ValueError is raised for empty string"""
        with self.assertRaises(ValueError):
            md_table_to_html("")

    def test_table_only_whitespace(self):
        """Test that ValueError is raised for only whitespace"""
        with self.assertRaises(ValueError):
            md_table_to_html("   \n   \n   ")


class DiagramCacheTest(TestCase):
    """Test cases for diagram caching functionality"""

    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for testing
        self.test_media_root = tempfile.mkdtemp()
        self.original_media_root = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = self.test_media_root

    def tearDown(self):
        """Clean up test environment"""
        # Restore original settings
        settings.MEDIA_ROOT = self.original_media_root
        # Remove test directory
        if os.path.exists(self.test_media_root):
            shutil.rmtree(self.test_media_root)

    def test_compute_hash(self):
        """Test that compute_hash generates consistent SHA256 hashes"""
        content1 = "test content"
        content2 = "test content"
        content3 = "different content"

        hash1 = compute_hash(content1)
        hash2 = compute_hash(content2)
        hash3 = compute_hash(content3)

        # Same content should produce same hash
        self.assertEqual(hash1, hash2)
        # Different content should produce different hash
        self.assertNotEqual(hash1, hash3)
        # Hash should be 64 characters (SHA256 hex)
        self.assertEqual(len(hash1), 64)

    def test_get_cache_path(self):
        """Test that get_cache_path generates correct paths"""
        diagram_type = "plantuml"
        content_hash = "abc123"

        path = get_cache_path(diagram_type, content_hash)

        self.assertIn("diagram_cache", path)
        self.assertIn("plantuml", path)
        self.assertIn("abc123.svg", path)

    @patch('diagramm_proxy.diagram_cache.requests.post')
    @patch('diagramm_proxy.diagram_cache.default_storage')
    def test_get_cached_diagram_miss(self, mock_storage, mock_post):
        """Test diagram generation on cache miss"""
        # Setup mocks
        mock_storage.exists.return_value = False
        mock_storage.path.return_value = os.path.join(
            self.test_media_root, 'diagram_cache/plantuml/test.svg'
        )
        mock_response = Mock()
        mock_response.content = b'<svg>test</svg>'
        mock_post.return_value = mock_response

        diagram_content = "@startuml\nA -> B\n@enduml"

        # Call function
        result = get_cached_diagram("plantuml", diagram_content)

        # Verify POST request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        # Check URL in positional args (first argument)
        self.assertIn("plantuml/svg", call_args[0][0])

        # Verify storage.save was called
        mock_storage.save.assert_called_once()

    @patch('diagramm_proxy.diagram_cache.default_storage')
    def test_get_cached_diagram_hit(self, mock_storage):
        """Test diagram retrieval on cache hit"""
        # Setup mock - diagram exists in cache
        mock_storage.exists.return_value = True

        diagram_content = "@startuml\nA -> B\n@enduml"

        # Call function
        result = get_cached_diagram("plantuml", diagram_content)

        # Verify no save was attempted (cache hit)
        mock_storage.save.assert_not_called()

        # Verify result contains expected path elements
        self.assertIn("diagram_cache", result)
        self.assertIn("plantuml", result)
        self.assertIn(".svg", result)

    @patch('diagramm_proxy.diagram_cache.requests.post')
    @patch('diagramm_proxy.diagram_cache.default_storage')
    def test_get_cached_diagram_request_error(self, mock_storage, mock_post):
        """Test that request errors are properly raised"""
        import requests

        mock_storage.exists.return_value = False
        mock_storage.path.return_value = os.path.join(
            self.test_media_root, 'diagram_cache/plantuml/test.svg'
        )
        mock_post.side_effect = requests.RequestException("Connection error")

        with self.assertRaises(requests.RequestException):
            get_cached_diagram("plantuml", "@startuml\nA -> B\n@enduml")

    @patch('diagramm_proxy.diagram_cache.default_storage')
    def test_clear_cache_specific_type(self, mock_storage):
        """Test clearing cache for specific diagram type"""
        # Create real test cache structure for this test
        cache_dir = os.path.join(self.test_media_root, 'diagram_cache', 'plantuml')
        os.makedirs(cache_dir, exist_ok=True)

        # Create test files
        test_file1 = os.path.join(cache_dir, 'test1.svg')
        test_file2 = os.path.join(cache_dir, 'test2.svg')
        open(test_file1, 'w').close()
        open(test_file2, 'w').close()

        # Mock storage methods
        mock_storage.exists.return_value = True
        mock_storage.path.return_value = cache_dir

        # Clear cache
        clear_cache('plantuml')

        # Verify files are deleted
        self.assertFalse(os.path.exists(test_file1))
        self.assertFalse(os.path.exists(test_file2))

    @patch('diagramm_proxy.diagram_cache.default_storage')
    def test_clear_cache_all_types(self, mock_storage):
        """Test clearing cache for all diagram types"""
        # Create real test cache structure with multiple types
        cache_root = os.path.join(self.test_media_root, 'diagram_cache')
        for diagram_type in ['plantuml', 'mermaid', 'graphviz']:
            cache_dir = os.path.join(cache_root, diagram_type)
            os.makedirs(cache_dir, exist_ok=True)
            test_file = os.path.join(cache_dir, 'test.svg')
            open(test_file, 'w').close()

        # Mock storage methods
        mock_storage.exists.return_value = True
        mock_storage.path.return_value = cache_root

        # Clear all cache
        clear_cache()

        # Verify all files are deleted
        for diagram_type in ['plantuml', 'mermaid', 'graphviz']:
            test_file = os.path.join(cache_root, diagram_type, 'test.svg')
            self.assertFalse(os.path.exists(test_file))


class ClearDiagramCacheCommandTest(TestCase):
    """Test cases for clear_diagram_cache management command"""

    def setUp(self):
        """Set up test environment"""
        self.test_media_root = tempfile.mkdtemp()
        self.original_media_root = settings.MEDIA_ROOT
        settings.MEDIA_ROOT = self.test_media_root

    def tearDown(self):
        """Clean up test environment"""
        settings.MEDIA_ROOT = self.original_media_root
        if os.path.exists(self.test_media_root):
            shutil.rmtree(self.test_media_root)

    def test_command_without_type(self):
        """Test running command without specifying type"""
        # Create test cache
        cache_dir = os.path.join(self.test_media_root, 'diagram_cache', 'plantuml')
        os.makedirs(cache_dir, exist_ok=True)
        test_file = os.path.join(cache_dir, 'test.svg')
        open(test_file, 'w').close()

        # Run command
        out = StringIO()
        call_command('clear_diagram_cache', stdout=out)

        # Check output
        self.assertIn('Clearing all diagram caches', out.getvalue())
        self.assertIn('Cache cleared successfully', out.getvalue())

    def test_command_with_type(self):
        """Test running command with specific diagram type"""
        # Create test cache
        cache_dir = os.path.join(self.test_media_root, 'diagram_cache', 'mermaid')
        os.makedirs(cache_dir, exist_ok=True)
        test_file = os.path.join(cache_dir, 'test.svg')
        open(test_file, 'w').close()

        # Run command
        out = StringIO()
        call_command('clear_diagram_cache', type='mermaid', stdout=out)

        # Check output
        self.assertIn('Clearing cache for mermaid', out.getvalue())
        self.assertIn('Cache cleared successfully', out.getvalue())


class IntegrationTest(TestCase):
    """Integration tests with actual dokumente models"""

    def setUp(self):
        """Set up test data using dokumente models"""
        from dokumente.models import (
            Dokumententyp, Dokument, Vorgabe, VorgabeLangtext, Thema
        )
        from datetime import date

        # Create required objects
        self.dokumententyp = Dokumententyp.objects.create(
            name="Test Policy",
            verantwortliche_ve="TEST"
        )

        self.dokument = Dokument.objects.create(
            nummer="TEST-001",
            name="Test Document",
            dokumententyp=self.dokumententyp,
            aktiv=True
        )

        self.thema = Thema.objects.create(name="Test Thema")
        self.vorgabe = Vorgabe.objects.create(
            dokument=self.dokument,
            nummer=1,
            order=1,
            thema=self.thema,
            titel="Test Vorgabe",
            gueltigkeit_von=date.today()
        )

        # Create AbschnittTypen
        self.typ_text = AbschnittTyp.objects.create(abschnitttyp="text")

        # Create VorgabeLangtext (which inherits from Textabschnitt)
        self.langtext = VorgabeLangtext.objects.create(
            abschnitt=self.vorgabe,
            abschnitttyp=self.typ_text,
            inhalt="# Test\n\nThis is a **test** vorgabe.",
            order=1
        )

    def test_render_vorgabe_langtext(self):
        """Test rendering VorgabeLangtext through render_textabschnitte"""
        from dokumente.models import VorgabeLangtext

        result = render_textabschnitte(
            VorgabeLangtext.objects.filter(abschnitt=self.vorgabe).order_by('order')
        )

        self.assertEqual(len(result), 1)
        typ, html = result[0]
        self.assertEqual(typ, "text")
        self.assertIn("<h1>Test</h1>", html)
        self.assertIn("<strong>test</strong>", html)
        self.assertIn("vorgabe", html)

    def test_textabschnitt_inheritance(self):
        """Test that VorgabeLangtext properly inherits Textabschnitt fields"""
        self.assertEqual(self.langtext.abschnitttyp, self.typ_text)
        self.assertIn("test", self.langtext.inhalt)
        self.assertEqual(self.langtext.order, 1)
