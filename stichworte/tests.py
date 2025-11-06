from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import models
from .models import Stichwort, Stichworterklaerung
from abschnitte.models import AbschnittTyp


class StichwortModelTest(TestCase):
    """Test cases for Stichwort model"""
    
    def setUp(self):
        """Set up test data"""
        self.stichwort = Stichwort.objects.create(
            stichwort="Sicherheit"
        )
    
    def test_stichwort_creation(self):
        """Test that Stichwort is created correctly"""
        self.assertEqual(self.stichwort.stichwort, "Sicherheit")
    
    def test_stichwort_str(self):
        """Test string representation of Stichwort"""
        self.assertEqual(str(self.stichwort), "Sicherheit")
    
    def test_stichwort_primary_key(self):
        """Test that stichwort field is the primary key"""
        pk_field = Stichwort._meta.pk
        self.assertEqual(pk_field.name, 'stichwort')
        self.assertEqual(pk_field.max_length, 50)
    
    def test_stichwort_verbose_name_plural(self):
        """Test verbose name plural"""
        self.assertEqual(
            Stichwort._meta.verbose_name_plural,
            "Stichworte"
        )
    
    def test_stichwort_max_length(self):
        """Test max_length constraint"""
        max_length_stichwort = "a" * 50
        stichwort = Stichwort.objects.create(stichwort=max_length_stichwort)
        self.assertEqual(stichwort.stichwort, max_length_stichwort)
    
    def test_stichwort_unique(self):
        """Test that stichwort must be unique"""
        with self.assertRaises(Exception):
            Stichwort.objects.create(stichwort="Sicherheit")
    
    def test_create_multiple_stichworte(self):
        """Test creating multiple Stichwort objects"""
        stichworte = ['Datenschutz', 'Netzwerk', 'Backup', 'Verschlüsselung']
        for stichwort in stichworte:
            Stichwort.objects.create(stichwort=stichwort)
        
        self.assertEqual(Stichwort.objects.count(), 5)  # Including setUp stichwort
    
    def test_stichwort_case_sensitivity(self):
        """Test that stichwort is case sensitive"""
        stichwort_lower = Stichwort.objects.create(stichwort="sicherheit")
        self.assertNotEqual(self.stichwort.pk, stichwort_lower.pk)
        self.assertEqual(Stichwort.objects.count(), 2)


class StichworterklaerungModelTest(TestCase):
    """Test cases for Stichworterklaerung model"""
    
    def setUp(self):
        """Set up test data"""
        self.stichwort = Stichwort.objects.create(
            stichwort="Sicherheit"
        )
        self.abschnitttyp = AbschnittTyp.objects.create(
            abschnitttyp="text"
        )
        self.erklaerung = Stichworterklaerung.objects.create(
            erklaerung=self.stichwort,
            abschnitttyp=self.abschnitttyp,
            inhalt="Dies ist eine Erklärung für Sicherheit.",
            order=1
        )
    
    def test_stichworterklaerung_creation(self):
        """Test that Stichworterklaerung is created correctly"""
        self.assertEqual(self.erklaerung.erklaerung, self.stichwort)
        self.assertEqual(self.erklaerung.abschnitttyp, self.abschnitttyp)
        self.assertEqual(self.erklaerung.inhalt, "Dies ist eine Erklärung für Sicherheit.")
        self.assertEqual(self.erklaerung.order, 1)
    
    def test_stichworterklaerung_foreign_key_relationship(self):
        """Test foreign key relationship to Stichwort"""
        self.assertEqual(self.erklaerung.erklaerung.stichwort, "Sicherheit")
    
    def test_stichworterklaerung_cascade_delete(self):
        """Test that deleting Stichwort cascades to Stichworterklaerung"""
        stichwort_count = Stichwort.objects.count()
        erklaerung_count = Stichworterklaerung.objects.count()
        
        self.stichwort.delete()
        
        self.assertEqual(Stichwort.objects.count(), stichwort_count - 1)
        self.assertEqual(Stichworterklaerung.objects.count(), erklaerung_count - 1)
    
    def test_stichworterklaerung_verbose_name(self):
        """Test verbose name"""
        self.assertEqual(
            Stichworterklaerung._meta.verbose_name,
            "Erklärung"
        )
    
    def test_stichworterklaerung_multiple_explanations(self):
        """Test creating multiple explanations for one Stichwort"""
        abschnitttyp2 = AbschnittTyp.objects.create(abschnitttyp="liste ungeordnet")
        erklaerung2 = Stichworterklaerung.objects.create(
            erklaerung=self.stichwort,
            abschnitttyp=abschnitttyp2,
            inhalt="Zweite Erklärung für Sicherheit.",
            order=2
        )
        
        explanations = Stichworterklaerung.objects.filter(erklaerung=self.stichwort)
        self.assertEqual(explanations.count(), 2)
        self.assertIn(self.erklaerung, explanations)
        self.assertIn(erklaerung2, explanations)
    
    def test_stichworterklaerung_ordering(self):
        """Test that explanations can be ordered"""
        erklaerung2 = Stichworterklaerung.objects.create(
            erklaerung=self.stichwort,
            abschnitttyp=self.abschnitttyp,
            inhalt="Zweite Erklärung",
            order=3
        )
        erklaerung3 = Stichworterklaerung.objects.create(
            erklaerung=self.stichwort,
            abschnitttyp=self.abschnitttyp,
            inhalt="Erste Erklärung",
            order=2
        )
        
        ordered = Stichworterklaerung.objects.filter(erklaerung=self.stichwort).order_by('order')
        expected_order = [self.erklaerung, erklaerung3, erklaerung2]
        self.assertEqual(list(ordered), expected_order)
    
    def test_stichworterklaerung_blank_fields(self):
        """Test that optional fields can be blank/null"""
        stichwort2 = Stichwort.objects.create(stichwort="Test")
        erklaerung_blank = Stichworterklaerung.objects.create(
            erklaerung=stichwort2
        )
        
        self.assertIsNone(erklaerung_blank.abschnitttyp)
        self.assertIsNone(erklaerung_blank.inhalt)
        self.assertEqual(erklaerung_blank.order, 0)
    
    def test_stichworterklaerung_inheritance(self):
        """Test that Stichworterklaerung inherits from Textabschnitt"""
        # Check that it has the expected fields from Textabschnitt
        self.assertTrue(hasattr(self.erklaerung, 'abschnitttyp'))
        self.assertTrue(hasattr(self.erklaerung, 'inhalt'))
        self.assertTrue(hasattr(self.erklaerung, 'order'))
        
        # Check that the fields work as expected
        self.assertIsInstance(self.erklaerung.abschnitttyp, AbschnittTyp)
        self.assertIsInstance(self.erklaerung.inhalt, str)
        self.assertIsInstance(self.erklaerung.order, int)


class StichwortIntegrationTest(TestCase):
    """Integration tests for Stichwort app"""
    
    def setUp(self):
        """Set up test data"""
        self.stichwort1 = Stichwort.objects.create(stichwort="IT-Sicherheit")
        self.stichwort2 = Stichwort.objects.create(stichwort="Datenschutz")
        
        self.abschnitttyp = AbschnittTyp.objects.create(abschnitttyp="text")
        
        self.erklaerung1 = Stichworterklaerung.objects.create(
            erklaerung=self.stichwort1,
            abschnitttyp=self.abschnitttyp,
            inhalt="Erklärung für IT-Sicherheit",
            order=1
        )
        
        self.erklaerung2 = Stichworterklaerung.objects.create(
            erklaerung=self.stichwort2,
            abschnitttyp=self.abschnitttyp,
            inhalt="Erklärung für Datenschutz",
            order=1
        )
    
    def test_stichwort_with_explanations_query(self):
        """Test querying Stichworte with their explanations"""
        stichworte_with_explanations = Stichwort.objects.filter(
            stichworterklaerung__isnull=False
        ).distinct()
        
        self.assertEqual(stichworte_with_explanations.count(), 2)
        self.assertIn(self.stichwort1, stichworte_with_explanations)
        self.assertIn(self.stichwort2, stichworte_with_explanations)
    
    def test_stichwort_without_explanations(self):
        """Test finding Stichworte without explanations"""
        stichwort3 = Stichwort.objects.create(stichwort="Backup")
        
        stichworte_without_explanations = Stichwort.objects.filter(
            stichworterklaerung__isnull=True
        )
        
        self.assertEqual(stichworte_without_explanations.count(), 1)
        self.assertEqual(stichworte_without_explanations.first(), stichwort3)
    
    def test_explanation_count_annotation(self):
        """Test annotating Stichworte with explanation count"""
        from django.db.models import Count
        
        stichworte_with_count = Stichwort.objects.annotate(
            explanation_count=Count('stichworterklaerung')
        )
        
        for stichwort in stichworte_with_count:
            if stichwort.stichwort in ["IT-Sicherheit", "Datenschutz"]:
                self.assertEqual(stichwort.explanation_count, 1)
            else:
                self.assertEqual(stichwort.explanation_count, 0)
