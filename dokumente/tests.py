from django.test import TestCase
from myapp.models import Dokument

# Create your tests here.

class DokumentTestCase (TestCase):
    def setUp(self):
        Document.objects.create(name)