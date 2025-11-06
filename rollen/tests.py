from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.models import Count
from .models import Rolle, RollenBeschreibung
from abschnitte.models import AbschnittTyp


class RolleModelTest(TestCase):
    """Test cases for Rolle model"""
    
    def setUp(self):
        """Set up test data"""
        self.rolle = Rolle.objects.create(
            name="Systemadministrator"
        )
    
    def test_rolle_creation(self):
        """Test that Rolle is created correctly"""
        self.assertEqual(self.rolle.name, "Systemadministrator")
    
    def test_rolle_str(self):
        """Test string representation of Rolle"""
        self.assertEqual(str(self.rolle), "Systemadministrator")
    
    def test_rolle_primary_key(self):
        """Test that name field is the primary key"""
        pk_field = Rolle._meta.pk
        self.assertEqual(pk_field.name, 'name')
        self.assertEqual(pk_field.max_length, 100)
    
    def test_rolle_verbose_name_plural(self):
        """Test verbose name plural"""
        self.assertEqual(
            Rolle._meta.verbose_name_plural,
            "Rollen"
        )
    
    def test_rolle_max_length(self):
        """Test max_length constraint"""
        max_length_rolle = "a" * 100
        rolle = Rolle.objects.create(name=max_length_rolle)
        self.assertEqual(rolle.name, max_length_rolle)
    
    def test_rolle_unique(self):
        """Test that name must be unique"""
        with self.assertRaises(Exception):
            Rolle.objects.create(name="Systemadministrator")
    
    def test_create_multiple_rollen(self):
        """Test creating multiple Rolle objects"""
        rollen = [
            "Datenschutzbeauftragter",
            "IT-Sicherheitsbeauftragter", 
            "Risikomanager",
            "Compliance-Officer"
        ]
        for rolle_name in rollen:
            Rolle.objects.create(name=rolle_name)
        
        self.assertEqual(Rolle.objects.count(), 5)  # Including setUp rolle
    
    def test_rolle_case_sensitivity(self):
        """Test that role name is case sensitive"""
        rolle_lower = Rolle.objects.create(name="systemadministrator")
        self.assertNotEqual(self.rolle.pk, rolle_lower.pk)
        self.assertEqual(Rolle.objects.count(), 2)
    
    def test_rolle_with_special_characters(self):
        """Test creating roles with special characters"""
        special_roles = [
            "IT-Administrator",
            "CISO (Chief Information Security Officer)",
            "Datenschutz-Beauftragter/-in",
            "Sicherheitsbeauftragter"
        ]
        
        for role_name in special_roles:
            rolle = Rolle.objects.create(name=role_name)
            self.assertEqual(rolle.name, role_name)
        
        self.assertEqual(Rolle.objects.count(), 5)  # Including setUp rolle


class RollenBeschreibungModelTest(TestCase):
    """Test cases for RollenBeschreibung model"""
    
    def setUp(self):
        """Set up test data"""
        self.rolle = Rolle.objects.create(
            name="Systemadministrator"
        )
        self.abschnitttyp = AbschnittTyp.objects.create(
            abschnitttyp="text"
        )
        self.beschreibung = RollenBeschreibung.objects.create(
            abschnitt=self.rolle,
            abschnitttyp=self.abschnitttyp,
            inhalt="Der Systemadministrator ist für die Verwaltung und Wartung der IT-Systeme verantwortlich.",
            order=1
        )
    
    def test_rollenbeschreibung_creation(self):
        """Test that RollenBeschreibung is created correctly"""
        self.assertEqual(self.beschreibung.abschnitt, self.rolle)
        self.assertEqual(self.beschreibung.abschnitttyp, self.abschnitttyp)
        self.assertEqual(self.beschreibung.inhalt, "Der Systemadministrator ist für die Verwaltung und Wartung der IT-Systeme verantwortlich.")
        self.assertEqual(self.beschreibung.order, 1)
    
    def test_rollenbeschreibung_foreign_key_relationship(self):
        """Test foreign key relationship to Rolle"""
        self.assertEqual(self.beschreibung.abschnitt.name, "Systemadministrator")
    
    def test_rollenbeschreibung_cascade_delete(self):
        """Test that deleting Rolle cascades to RollenBeschreibung"""
        rolle_count = Rolle.objects.count()
        beschreibung_count = RollenBeschreibung.objects.count()
        
        self.rolle.delete()
        
        self.assertEqual(Rolle.objects.count(), rolle_count - 1)
        self.assertEqual(RollenBeschreibung.objects.count(), beschreibung_count - 1)
    
    def test_rollenbeschreibung_verbose_names(self):
        """Test verbose names"""
        self.assertEqual(
            RollenBeschreibung._meta.verbose_name,
            "Rollenbeschreibungs-Abschnitt"
        )
        self.assertEqual(
            RollenBeschreibung._meta.verbose_name_plural,
            "Rollenbeschreibung"
        )
    
    def test_rollenbeschreibung_multiple_descriptions(self):
        """Test creating multiple descriptions for one Rolle"""
        abschnitttyp2 = AbschnittTyp.objects.create(abschnitttyp="liste ungeordnet")
        beschreibung2 = RollenBeschreibung.objects.create(
            abschnitt=self.rolle,
            abschnitttyp=abschnitttyp2,
            inhalt="Aufgaben:\n- Systemüberwachung\n- Backup-Management\n- Benutzeradministration",
            order=2
        )
        
        descriptions = RollenBeschreibung.objects.filter(abschnitt=self.rolle)
        self.assertEqual(descriptions.count(), 2)
        self.assertIn(self.beschreibung, descriptions)
        self.assertIn(beschreibung2, descriptions)
    
    def test_rollenbeschreibung_ordering(self):
        """Test that descriptions can be ordered"""
        beschreibung2 = RollenBeschreibung.objects.create(
            abschnitt=self.rolle,
            abschnitttyp=self.abschnitttyp,
            inhalt="Zweite Beschreibung",
            order=3
        )
        beschreibung3 = RollenBeschreibung.objects.create(
            abschnitt=self.rolle,
            abschnitttyp=self.abschnitttyp,
            inhalt="Erste Beschreibung",
            order=2
        )
        
        ordered = RollenBeschreibung.objects.filter(abschnitt=self.rolle).order_by('order')
        expected_order = [self.beschreibung, beschreibung3, beschreibung2]
        self.assertEqual(list(ordered), expected_order)
    
    def test_rollenbeschreibung_blank_fields(self):
        """Test that optional fields can be blank/null"""
        rolle2 = Rolle.objects.create(name="Testrolle")
        beschreibung_blank = RollenBeschreibung.objects.create(
            abschnitt=rolle2
        )
        
        self.assertIsNone(beschreibung_blank.abschnitttyp)
        self.assertIsNone(beschreibung_blank.inhalt)
        self.assertEqual(beschreibung_blank.order, 0)
    
    def test_rollenbeschreibung_inheritance(self):
        """Test that RollenBeschreibung inherits from Textabschnitt"""
        # Check that it has the expected fields from Textabschnitt
        self.assertTrue(hasattr(self.beschreibung, 'abschnitttyp'))
        self.assertTrue(hasattr(self.beschreibung, 'inhalt'))
        self.assertTrue(hasattr(self.beschreibung, 'order'))
        
        # Check that the fields work as expected
        self.assertIsInstance(self.beschreibung.abschnitttyp, AbschnittTyp)
        self.assertIsInstance(self.beschreibung.inhalt, str)
        self.assertIsInstance(self.beschreibung.order, int)
    
    def test_rollenbeschreibung_different_types(self):
        """Test creating descriptions with different section types"""
        # Create different section types
        typ_list = AbschnittTyp.objects.create(abschnitttyp="liste ungeordnet")
        typ_table = AbschnittTyp.objects.create(abschnitttyp="tabelle")
        
        # Create descriptions with different types
        beschreibung_text = RollenBeschreibung.objects.create(
            abschnitt=self.rolle,
            abschnitttyp=self.abschnitttyp,
            inhalt="Textbeschreibung der Rolle",
            order=1
        )
        
        beschreibung_list = RollenBeschreibung.objects.create(
            abschnitt=self.rolle,
            abschnitttyp=typ_list,
            inhalt="Aufgabe 1\nAufgabe 2\nAufgabe 3",
            order=2
        )
        
        beschreibung_table = RollenBeschreibung.objects.create(
            abschnitt=self.rolle,
            abschnitttyp=typ_table,
            inhalt="| Verantwortung | Priorität |\n|--------------|------------|\n| Systemwartung | Hoch |",
            order=3
        )
        
        # Verify all descriptions are created
        descriptions = RollenBeschreibung.objects.filter(abschnitt=self.rolle)
        self.assertEqual(descriptions.count(), 4)  # Including setUp beschreibung
        
        # Verify types are correct
        self.assertEqual(beschreibung_text.abschnitttyp, self.abschnitttyp)
        self.assertEqual(beschreibung_list.abschnitttyp, typ_list)
        self.assertEqual(beschreibung_table.abschnitttyp, typ_table)


class RolleIntegrationTest(TestCase):
    """Integration tests for Rolle app"""
    
    def setUp(self):
        """Set up test data"""
        self.rolle1 = Rolle.objects.create(name="IT-Sicherheitsbeauftragter")
        self.rolle2 = Rolle.objects.create(name="Datenschutzbeauftragter")
        
        self.abschnitttyp = AbschnittTyp.objects.create(abschnitttyp="text")
        
        self.beschreibung1 = RollenBeschreibung.objects.create(
            abschnitt=self.rolle1,
            abschnitttyp=self.abschnitttyp,
            inhalt="Beschreibung für IT-Sicherheitsbeauftragten",
            order=1
        )
        
        self.beschreibung2 = RollenBeschreibung.objects.create(
            abschnitt=self.rolle2,
            abschnitttyp=self.abschnitttyp,
            inhalt="Beschreibung für Datenschutzbeauftragten",
            order=1
        )
    
    def test_rolle_with_descriptions_query(self):
        """Test querying Rollen with their descriptions"""
        rollen_with_descriptions = Rolle.objects.filter(
            rollenbeschreibung__isnull=False
        ).distinct()
        
        self.assertEqual(rollen_with_descriptions.count(), 2)
        self.assertIn(self.rolle1, rollen_with_descriptions)
        self.assertIn(self.rolle2, rollen_with_descriptions)
    
    def test_rolle_without_descriptions(self):
        """Test finding Rollen without descriptions"""
        rolle3 = Rolle.objects.create(name="Compliance-Officer")
        
        rollen_without_descriptions = Rolle.objects.filter(
            rollenbeschreibung__isnull=True
        )
        
        self.assertEqual(rollen_without_descriptions.count(), 1)
        self.assertEqual(rollen_without_descriptions.first(), rolle3)
    
    def test_description_count_annotation(self):
        """Test annotating Rollen with description count"""
        from django.db.models import Count
        
        rollen_with_count = Rolle.objects.annotate(
            description_count=Count('rollenbeschreibung')
        )
        
        for rolle in rollen_with_count:
            if rolle.name in ["IT-Sicherheitsbeauftragter", "Datenschutzbeauftragter"]:
                self.assertEqual(rolle.description_count, 1)
            else:
                self.assertEqual(rolle.description_count, 0)
    
    def test_multiple_descriptions_per_rolle(self):
        """Test multiple descriptions for a single role"""
        # Add more descriptions to rolle1
        abschnitttyp2 = AbschnittTyp.objects.create(abschnitttyp="liste ungeordnet")
        
        beschreibung2 = RollenBeschreibung.objects.create(
            abschnitt=self.rolle1,
            abschnitttyp=abschnitttyp2,
            inhalt="Zusätzliche Aufgaben:\n- Überwachung\n- Berichterstattung",
            order=2
        )
        
        # Check that rolle1 now has 2 descriptions
        descriptions = RollenBeschreibung.objects.filter(abschnitt=self.rolle1)
        self.assertEqual(descriptions.count(), 2)
        
        # Check annotation
        rolle_with_count = Rolle.objects.annotate(
            description_count=Count('rollenbeschreibung')
        ).get(pk=self.rolle1.pk)
        self.assertEqual(rolle_with_count.description_count, 2)
    
    def test_role_descriptions_ordered(self):
        """Test that role descriptions are returned in correct order"""
        # Add more descriptions in random order
        beschreibung2 = RollenBeschreibung.objects.create(
            abschnitt=self.rolle1,
            abschnitttyp=self.abschnitttyp,
            inhalt="Dritte Beschreibung",
            order=3
        )
        
        beschreibung3 = RollenBeschreibung.objects.create(
            abschnitt=self.rolle1,
            abschnitttyp=self.abschnitttyp,
            inhalt="Zweite Beschreibung",
            order=2
        )
        
        # Get descriptions in order
        ordered_descriptions = RollenBeschreibung.objects.filter(
            abschnitt=self.rolle1
        ).order_by('order')
        
        expected_order = [self.beschreibung1, beschreibung3, beschreibung2]
        self.assertEqual(list(ordered_descriptions), expected_order)
    
    def test_role_search_by_name(self):
        """Test searching roles by name"""
        # Test exact match
        exact_match = Rolle.objects.filter(name="IT-Sicherheitsbeauftragter")
        self.assertEqual(exact_match.count(), 1)
        self.assertEqual(exact_match.first(), self.rolle1)
        
        # Test case-sensitive contains
        contains_match = Rolle.objects.filter(name__contains="Sicherheits")
        self.assertEqual(contains_match.count(), 1)
        self.assertEqual(contains_match.first(), self.rolle1)
        
        # Test case-insensitive contains
        icontains_match = Rolle.objects.filter(name__icontains="sicherheits")
        self.assertEqual(icontains_match.count(), 1)
        self.assertEqual(icontains_match.first(), self.rolle1)
    
    def test_role_with_long_descriptions(self):
        """Test roles with long description content"""
        long_content = "Dies ist eine sehr lange Beschreibung " * 50  # Repeat to make it long
        
        rolle_long = Rolle.objects.create(name="Rolle mit langer Beschreibung")
        beschreibung_long = RollenBeschreibung.objects.create(
            abschnitt=rolle_long,
            abschnitttyp=self.abschnitttyp,
            inhalt=long_content,
            order=1
        )
        
        # Verify the long content is stored correctly
        retrieved = RollenBeschreibung.objects.get(pk=beschreibung_long.pk)
        self.assertEqual(retrieved.inhalt, long_content)
        self.assertGreater(len(retrieved.inhalt), 1000)  # Should be quite long
