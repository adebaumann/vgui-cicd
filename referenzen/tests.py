from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Referenz, Referenzerklaerung
from abschnitte.models import AbschnittTyp


class ReferenzModelTest(TestCase):
    """Test cases for Referenz model"""
    
    def setUp(self):
        """Set up test data"""
        self.referenz = Referenz.objects.create(
            name_nummer="ISO-27001",
            name_text="Information Security Management",
            url="https://www.iso.org/isoiec-27001-information-security.html"
        )
    
    def test_referenz_creation(self):
        """Test that Referenz is created correctly"""
        self.assertEqual(self.referenz.name_nummer, "ISO-27001")
        self.assertEqual(self.referenz.name_text, "Information Security Management")
        self.assertEqual(self.referenz.url, "https://www.iso.org/isoiec-27001-information-security.html")
        self.assertIsNone(self.referenz.oberreferenz)
    
    def test_referenz_str(self):
        """Test string representation of Referenz"""
        self.assertEqual(str(self.referenz), "ISO-27001")
    
    def test_referenz_verbose_name_plural(self):
        """Test verbose name plural"""
        self.assertEqual(
            Referenz._meta.verbose_name_plural,
            "Referenzen"
        )
    
    def test_referenz_path_method(self):
        """Test Path method for root reference"""
        path = self.referenz.Path()
        self.assertEqual(path, "ISO-27001 (Information Security Management)")
    
    def test_referenz_path_without_name_text(self):
        """Test Path method when name_text is empty"""
        referenz_no_text = Referenz.objects.create(
            name_nummer="NIST-800-53"
        )
        path = referenz_no_text.Path()
        self.assertEqual(path, "NIST-800-53")
    
    def test_referenz_blank_fields(self):
        """Test that optional fields can be blank"""
        referenz_minimal = Referenz.objects.create(
            name_nummer="TEST-001"
        )
        self.assertEqual(referenz_minimal.name_text, "")
        self.assertEqual(referenz_minimal.url, "")
        self.assertIsNone(referenz_minimal.oberreferenz)
    
    def test_referenz_max_lengths(self):
        """Test max_length constraints"""
        max_name_nummer = "a" * 100
        max_name_text = "b" * 255
        
        referenz = Referenz.objects.create(
            name_nummer=max_name_nummer,
            name_text=max_name_text
        )
        
        self.assertEqual(referenz.name_nummer, max_name_nummer)
        self.assertEqual(referenz.name_text, max_name_text)
    
    def test_create_multiple_references(self):
        """Test creating multiple Referenz objects"""
        references = [
            ("ISO-9001", "Quality Management"),
            ("ISO-14001", "Environmental Management"),
            ("ISO-45001", "Occupational Health and Safety")
        ]
        
        for name_nummer, name_text in references:
            Referenz.objects.create(
                name_nummer=name_nummer,
                name_text=name_text
            )
        
        self.assertEqual(Referenz.objects.count(), 4)  # Including setUp referenz


class ReferenzHierarchyTest(TestCase):
    """Test cases for Referenz hierarchy using MPTT"""
    
    def setUp(self):
        """Set up hierarchical test data"""
        # Create root references
        self.iso_root = Referenz.objects.create(
            name_nummer="ISO",
            name_text="International Organization for Standardization"
        )
        
        self.iso_27000_series = Referenz.objects.create(
            name_nummer="ISO-27000",
            name_text="Information Security Management System Family",
            oberreferenz=self.iso_root
        )
        
        self.iso_27001 = Referenz.objects.create(
            name_nummer="ISO-27001",
            name_text="Information Security Management",
            oberreferenz=self.iso_27000_series
        )
        
        self.iso_27002 = Referenz.objects.create(
            name_nummer="ISO-27002",
            name_text="Code of Practice for Information Security Controls",
            oberreferenz=self.iso_27000_series
        )
    
    def test_hierarchy_relationships(self):
        """Test parent-child relationships"""
        self.assertEqual(self.iso_27000_series.oberreferenz, self.iso_root)
        self.assertEqual(self.iso_27001.oberreferenz, self.iso_27000_series)
        self.assertEqual(self.iso_27002.oberreferenz, self.iso_27000_series)
    
    def test_get_ancestors(self):
        """Test getting ancestors"""
        ancestors = self.iso_27001.get_ancestors()
        expected_ancestors = [self.iso_root, self.iso_27000_series]
        self.assertEqual(list(ancestors), expected_ancestors)
    
    def test_get_ancestors_include_self(self):
        """Test getting ancestors including self"""
        ancestors = self.iso_27001.get_ancestors(include_self=True)
        expected_ancestors = [self.iso_root, self.iso_27000_series, self.iso_27001]
        self.assertEqual(list(ancestors), expected_ancestors)
    
    def test_get_descendants(self):
        """Test getting descendants"""
        descendants = self.iso_27000_series.get_descendants()
        expected_descendants = [self.iso_27001, self.iso_27002]
        self.assertEqual(list(descendants), expected_descendants)
    
    def test_get_children(self):
        """Test getting direct children"""
        children = self.iso_27000_series.get_children()
        expected_children = [self.iso_27001, self.iso_27002]
        self.assertEqual(list(children), expected_children)
    
    def test_get_root(self):
        """Test getting root of hierarchy"""
        root = self.iso_27001.get_root()
        self.assertEqual(root, self.iso_root)
    
    def test_is_root(self):
        """Test is_root method"""
        self.assertTrue(self.iso_root.is_root_node())
        self.assertFalse(self.iso_27001.is_root_node())
    
    def test_is_leaf(self):
        """Test is_leaf method"""
        self.assertFalse(self.iso_root.is_leaf_node())
        self.assertFalse(self.iso_27000_series.is_leaf_node())
        self.assertTrue(self.iso_27001.is_leaf_node())
        self.assertTrue(self.iso_27002.is_leaf_node())
    
    def test_level_property(self):
        """Test level property"""
        self.assertEqual(self.iso_root.level, 0)
        self.assertEqual(self.iso_27000_series.level, 1)
        self.assertEqual(self.iso_27001.level, 2)
        self.assertEqual(self.iso_27002.level, 2)
    
    def test_path_method_with_hierarchy(self):
        """Test Path method with hierarchical references"""
        path = self.iso_27001.Path()
        expected_path = "ISO → ISO-27000 → ISO-27001 (Information Security Management)"
        self.assertEqual(path, expected_path)
    
    def test_path_method_without_name_text_in_hierarchy(self):
        """Test Path method when intermediate nodes have no name_text"""
        # Create reference without name_text
        ref_no_text = Referenz.objects.create(
            name_nummer="NO-TEXT",
            oberreferenz=self.iso_root
        )
        
        child_ref = Referenz.objects.create(
            name_nummer="CHILD",
            name_text="Child Reference",
            oberreferenz=ref_no_text
        )
        
        path = child_ref.Path()
        expected_path = "ISO → NO-TEXT → CHILD (Child Reference)"
        self.assertEqual(path, expected_path)
    
    def test_order_insertion_by(self):
        """Test that references are ordered by name_nummer"""
        # Create more children in different order
        ref_c = Referenz.objects.create(
            name_nummer="C-REF",
            oberreferenz=self.iso_root
        )
        ref_a = Referenz.objects.create(
            name_nummer="A-REF", 
            oberreferenz=self.iso_root
        )
        ref_b = Referenz.objects.create(
            name_nummer="B-REF",
            oberreferenz=self.iso_root
        )
        
        children = list(self.iso_root.get_children())
        # Should be ordered alphabetically by name_nummer
        expected_order = [ref_a, ref_b, ref_c, self.iso_27000_series]
        self.assertEqual(children, expected_order)


class ReferenzerklaerungModelTest(TestCase):
    """Test cases for Referenzerklaerung model"""
    
    def setUp(self):
        """Set up test data"""
        self.referenz = Referenz.objects.create(
            name_nummer="ISO-27001",
            name_text="Information Security Management"
        )
        self.abschnitttyp = AbschnittTyp.objects.create(
            abschnitttyp="text"
        )
        self.erklaerung = Referenzerklaerung.objects.create(
            erklaerung=self.referenz,
            abschnitttyp=self.abschnitttyp,
            inhalt="Dies ist eine Erklärung für ISO-27001.",
            order=1
        )
    
    def test_referenzerklaerung_creation(self):
        """Test that Referenzerklaerung is created correctly"""
        self.assertEqual(self.erklaerung.erklaerung, self.referenz)
        self.assertEqual(self.erklaerung.abschnitttyp, self.abschnitttyp)
        self.assertEqual(self.erklaerung.inhalt, "Dies ist eine Erklärung für ISO-27001.")
        self.assertEqual(self.erklaerung.order, 1)
    
    def test_referenzerklaerung_foreign_key_relationship(self):
        """Test foreign key relationship to Referenz"""
        self.assertEqual(self.erklaerung.erklaerung.name_nummer, "ISO-27001")
        self.assertEqual(self.erklaerung.erklaerung.name_text, "Information Security Management")
    
    def test_referenzerklaerung_cascade_delete(self):
        """Test that deleting Referenz cascades to Referenzerklaerung"""
        referenz_count = Referenz.objects.count()
        erklaerung_count = Referenzerklaerung.objects.count()
        
        self.referenz.delete()
        
        self.assertEqual(Referenz.objects.count(), referenz_count - 1)
        self.assertEqual(Referenzerklaerung.objects.count(), erklaerung_count - 1)
    
    def test_referenzerklaerung_verbose_name(self):
        """Test verbose name"""
        self.assertEqual(
            Referenzerklaerung._meta.verbose_name,
            "Erklärung"
        )
    
    def test_referenzerklaerung_multiple_explanations(self):
        """Test creating multiple explanations for one Referenz"""
        abschnitttyp2 = AbschnittTyp.objects.create(abschnitttyp="liste ungeordnet")
        erklaerung2 = Referenzerklaerung.objects.create(
            erklaerung=self.referenz,
            abschnitttyp=abschnitttyp2,
            inhalt="Zweite Erklärung für ISO-27001.",
            order=2
        )
        
        explanations = Referenzerklaerung.objects.filter(erklaerung=self.referenz)
        self.assertEqual(explanations.count(), 2)
        self.assertIn(self.erklaerung, explanations)
        self.assertIn(erklaerung2, explanations)
    
    def test_referenzerklaerung_ordering(self):
        """Test that explanations can be ordered"""
        erklaerung2 = Referenzerklaerung.objects.create(
            erklaerung=self.referenz,
            abschnitttyp=self.abschnitttyp,
            inhalt="Zweite Erklärung",
            order=3
        )
        erklaerung3 = Referenzerklaerung.objects.create(
            erklaerung=self.referenz,
            abschnitttyp=self.abschnitttyp,
            inhalt="Erste Erklärung",
            order=2
        )
        
        ordered = Referenzerklaerung.objects.filter(erklaerung=self.referenz).order_by('order')
        expected_order = [self.erklaerung, erklaerung3, erklaerung2]
        self.assertEqual(list(ordered), expected_order)
    
    def test_referenzerklaerung_blank_fields(self):
        """Test that optional fields can be blank/null"""
        referenz2 = Referenz.objects.create(name_nummer="TEST-001")
        erklaerung_blank = Referenzerklaerung.objects.create(
            erklaerung=referenz2
        )
        
        self.assertIsNone(erklaerung_blank.abschnitttyp)
        self.assertIsNone(erklaerung_blank.inhalt)
        self.assertEqual(erklaerung_blank.order, 0)
    
    def test_referenzerklaerung_inheritance(self):
        """Test that Referenzerklaerung inherits from Textabschnitt"""
        # Check that it has the expected fields from Textabschnitt
        self.assertTrue(hasattr(self.erklaerung, 'abschnitttyp'))
        self.assertTrue(hasattr(self.erklaerung, 'inhalt'))
        self.assertTrue(hasattr(self.erklaerung, 'order'))
        
        # Check that the fields work as expected
        self.assertIsInstance(self.erklaerung.abschnitttyp, AbschnittTyp)
        self.assertIsInstance(self.erklaerung.inhalt, str)
        self.assertIsInstance(self.erklaerung.order, int)


class ReferenzIntegrationTest(TestCase):
    """Integration tests for Referenz app"""
    
    def setUp(self):
        """Set up test data"""
        self.root_ref = Referenz.objects.create(
            name_nummer="ROOT",
            name_text="Root Reference"
        )
        
        self.child_ref = Referenz.objects.create(
            name_nummer="CHILD",
            name_text="Child Reference",
            oberreferenz=self.root_ref
        )
        
        self.abschnitttyp = AbschnittTyp.objects.create(abschnitttyp="text")
        
        self.erklaerung = Referenzerklaerung.objects.create(
            erklaerung=self.child_ref,
            abschnitttyp=self.abschnitttyp,
            inhalt="Explanation for child reference",
            order=1
        )
    
    def test_reference_with_explanations_query(self):
        """Test querying references with their explanations"""
        references_with_explanations = Referenz.objects.filter(
            referenzerklaerung__isnull=False
        ).distinct()
        
        self.assertEqual(references_with_explanations.count(), 1)
        self.assertIn(self.child_ref, references_with_explanations)
        self.assertNotIn(self.root_ref, references_with_explanations)
    
    def test_reference_without_explanations(self):
        """Test finding references without explanations"""
        references_without_explanations = Referenz.objects.filter(
            referenzerklaerung__isnull=True
        )
        
        self.assertEqual(references_without_explanations.count(), 1)
        self.assertEqual(references_without_explanations.first(), self.root_ref)
    
    def test_explanation_count_annotation(self):
        """Test annotating references with explanation count"""
        from django.db.models import Count
        
        references_with_count = Referenz.objects.annotate(
            explanation_count=Count('referenzerklaerung')
        )
        
        for reference in references_with_count:
            if reference == self.child_ref:
                self.assertEqual(reference.explanation_count, 1)
            else:
                self.assertEqual(reference.explanation_count, 0)
    
    def test_hierarchy_with_explanations(self):
        """Test that explanations work correctly with hierarchical references"""
        # Add explanation to root reference
        root_erklaerung = Referenzerklaerung.objects.create(
            erklaerung=self.root_ref,
            abschnitttyp=self.abschnitttyp,
            inhalt="Explanation for root reference",
            order=1
        )
        
        # Both references should now have explanations
        references_with_explanations = Referenz.objects.filter(
            referenzerklaerung__isnull=False
        ).distinct()
        
        self.assertEqual(references_with_explanations.count(), 2)
        self.assertIn(self.root_ref, references_with_explanations)
        self.assertIn(self.child_ref, references_with_explanations)
