# Alle Modelle der vgui-cicd Django-Anwendung

Dieses Dokument beschreibt alle Datenmodelle in der vgui-cicd Anwendung mit ihren Eigenschaften, Beziehungen und Verwendungszwecken.

---

## App: dokumente

Die Hauptmodelle für die Verwaltung von Dokumenten, Vorgaben und deren Metadaten.

### Dokumententyp

**Zweck**: Kategorisierung von Dokumenten (z. B. Richtlinie, Standard).

**Wichtige Felder**:
- `name` (CharField, max_length=100, **PRIMARY KEY**)
- `verantwortliche_ve` (CharField, max_length=255): Die verantwortliche Verwaltungseinheit

**Besonderheiten**:
- `__str__()` gibt den Namen zurück
- Dient als Klassifizierungskategorie für Dokumente

**Meta**:
- `verbose_name = "Dokumententyp"`
- `verbose_name_plural = "Dokumententypen"`

---

### Person

**Zweck**: Repräsentiert Personen, die als Autoren, Prüfer oder in anderen Rollen tätig sind.

**Wichtige Felder**:
- `name` (CharField, max_length=100, **PRIMARY KEY**)
- `funktion` (CharField, max_length=255): Funktionsbezeichnung der Person

**Beziehungen**:
- Many-to-Many mit `Dokument` über `verfasste_dokumente` (Autoren)
- Many-to-Many mit `Dokument` über `gepruefte_dokumente` (Prüfer)

**Besonderheiten**:
- `__str__()` gibt den Namen zurück
- `ordering = ['name']`: Alphabetische Sortierung

**Meta**:
- `verbose_name_plural = "Personen"`

---

### Thema

**Zweck**: Thematische Einordnung und Kategorisierung von Vorgaben innerhalb von Dokumenten.

**Wichtige Felder**:
- `name` (CharField, max_length=100, **PRIMARY KEY**)
- `erklaerung` (TextField, blank=True): Optionale Erklärung des Themas

**Besonderheiten**:
- `__str__()` gibt den Namen zurück
- Der erste Buchstabe des Themas wird in Vorgabennummern verwendet

**Meta**:
- `verbose_name_plural = "Themen"`

---

### Dokument

**Zweck**: Hauptmodell für ein einzelnes Dokument mit allen zugehörigen Metadaten und Inhalten.

**Wichtige Felder**:
- `nummer` (CharField, max_length=50, **PRIMARY KEY**): Eindeutige Dokumentennummer
- `dokumententyp` (ForeignKey → Dokumententyp, on_delete=PROTECT): Klassifizierung
- `name` (CharField, max_length=255): Dokumenttitel
- `autoren` (ManyToManyField → Person, related_name='verfasste_dokumente')
- `pruefende` (ManyToManyField → Person, related_name='gepruefte_dokumente')
- `gueltigkeit_von` (DateField, null=True, blank=True): Gültig ab Datum
- `gueltigkeit_bis` (DateField, null=True, blank=True): Gültig bis Datum
- `signatur_cso` (CharField, max_length=255, blank=True): CSO-Signatur
- `anhaenge` (TextField, blank=True): Beschreibung von Anhängen
- `aktiv` (BooleanField, blank=True): Aktivierungsstatus

**Beziehungen**:
- 1-to-Many mit `Vorgabe` (über related_name='vorgaben')
- 1-to-Many mit `Geltungsbereich`
- 1-to-Many mit `Einleitung`
- 1-to-Many mit `Changelog`

**Besonderheiten**:
- `__str__()` formatiert als "nummer – name"

**Meta**:
- `verbose_name = "Dokument"`
- `verbose_name_plural = "Dokumente"`

---

### Vorgabe

**Zweck**: Repräsentiert eine einzelne Vorgabe oder Anforderung innerhalb eines Dokuments.

**Wichtige Felder**:
- `order` (IntegerField): Sortierreihenfolge für die Darstellung
- `nummer` (IntegerField): Nummer innerhalb eines Themas/Dokuments. Muss nicht eindeutig sein (z.B. für geänderte Vorgaben)
- `dokument` (ForeignKey → Dokument, on_delete=CASCADE, related_name='vorgaben')
- `thema` (ForeignKey → Thema, on_delete=PROTECT): Thematische Einordnung
- `titel` (CharField, max_length=255): Titel der Vorgabe
- `referenzen` (ManyToManyField → Referenz, blank=True): Verweise auf externe Referenzen
- `gueltigkeit_von` (DateField): Gültig ab Datum
- `gueltigkeit_bis` (DateField, blank=True, null=True): Gültig bis Datum (offen = unbegrenzt)
- `stichworte` (ManyToManyField → Stichwort, blank=True): Tags zur Kategorisierung
- `relevanz` (ManyToManyField → Rolle, blank=True): Relevante Rollen

**Beziehungen**:
- Foreign Key zu `Dokument` und `Thema`
- Many-to-Many zu `Referenz`, `Stichwort`, `Rolle`
- 1-to-Many zu `VorgabeLangtext`, `VorgabeKurztext`
- 1-to-Many zu `Checklistenfrage`

**Wichtige Methoden**:

- `Vorgabennummer()` → str
  - Generiert eine eindeutige, lesbare Kennummer
  - Format: "{dokument.nummer}.{thema.name[0]}.{nummer}"
  - Beispiel: "R0066.A.1"

- `get_status(check_date=None, verbose=False)` → str
  - Bestimmt den Status einer Vorgabe zu einem gegebenen Datum
  - Parameter: `check_date` (Default: heute), `verbose` (Deutsche Beschreibung ja/nein)
  - Rückgabewerte:
    - "future": Vorgabe ist noch nicht gültig
    - "active": Vorgabe ist aktuell gültig
    - "expired": Vorgabe ist nicht mehr gültig
  - Verbose-Ausgaben enthalten Datumsangaben

- `sanity_check_vorgaben()` (statisch) → list
  - Findet zeitliche Konflikte zwischen Vorgaben mit gleicher Nummer/Thema/Dokument
  - Überprüft, ob sich Geltungszeiträume überschneiden
  - Gibt Liste mit Konflikt-Dictionaries zurück

- `clean()`
  - Validiert die Vorgabe vor dem Speichern
  - Ruft `find_conflicts()` auf
  - Wirft `ValidationError` bei erkannten Konflikten

- `find_conflicts()` → list
  - Findet Konflikte mit bestehenden Vorgaben (ausgenommen self)
  - Überprüft auf zeitliche Überschneidungen
  - Gibt Liste mit Konflikt-Details zurück

- `_date_ranges_intersect(start1, end1, start2, end2)` (statisch) → bool
  - Prüft, ob zwei Datumsbereiche sich überschneiden
  - `None` als Enddatum = unbegrenzter Bereich
  - Gibt `True` bei Überschneidung zurück

**Besonderheiten**:
- `__str__()` gibt "Vorgabennummer: titel" zurück
- Validierung von Gültigkeitszeiträumen ist implementiert
- Sehr wichtiges Modell im Geschäftslogik-Kontext

**Meta**:
- `ordering = ['order']`
- `verbose_name_plural = "Vorgaben"`

---

### VorgabeLangtext

**Zweck**: Speichert ausführliche Textinhalte (Langtext) einer Vorgabe.

**Wichtige Felder**:
- `abschnitt` (ForeignKey → Vorgabe, on_delete=CASCADE): Referenz zur Vorgabe
- Erbt von `Textabschnitt` (siehe App: abschnitte):
  - `abschnitttyp` (ForeignKey → AbschnittTyp, optional)
  - `inhalt` (TextField, blank=True, null=True)
  - `order` (PositiveIntegerField, default=0)

**Meta**:
- `verbose_name = "Langtext-Abschnitt"`
- `verbose_name_plural = "Langtext"`

---

### VorgabeKurztext

**Zweck**: Speichert kurze Textinhalte (Kurztext) einer Vorgabe.

**Wichtige Felder**:
- `abschnitt` (ForeignKey → Vorgabe, on_delete=CASCADE): Referenz zur Vorgabe
- Erbt von `Textabschnitt` (siehe App: abschnitte):
  - `abschnitttyp` (ForeignKey → AbschnittTyp, optional)
  - `inhalt` (TextField, blank=True, null=True)
  - `order` (PositiveIntegerField, default=0)

**Meta**:
- `verbose_name = "Kurztext-Abschnitt"`
- `verbose_name_plural = "Kurztext"`

---

### Geltungsbereich

**Zweck**: Speichert den Geltungsbereich-Abschnitt eines Dokuments.

**Wichtige Felder**:
- `geltungsbereich` (ForeignKey → Dokument, on_delete=CASCADE): Referenz zum Dokument
- Erbt von `Textabschnitt` (siehe App: abschnitte):
  - `abschnitttyp` (ForeignKey → AbschnittTyp, optional)
  - `inhalt` (TextField, blank=True, null=True)
  - `order` (PositiveIntegerField, default=0)

**Meta**:
- `verbose_name = "Geltungsbereichs-Abschnitt"`
- `verbose_name_plural = "Geltungsbereich"`

---

### Einleitung

**Zweck**: Speichert die Einleitungs-Abschnitte eines Dokuments.

**Wichtige Felder**:
- `einleitung` (ForeignKey → Dokument, on_delete=CASCADE): Referenz zum Dokument
- Erbt von `Textabschnitt` (siehe App: abschnitte):
  - `abschnitttyp` (ForeignKey → AbschnittTyp, optional)
  - `inhalt` (TextField, blank=True, null=True)
  - `order` (PositiveIntegerField, default=0)

**Meta**:
- `verbose_name = "Einleitungs-Abschnitt"`
- `verbose_name_plural = "Einleitung"`

---

### Checklistenfrage

**Zweck**: Repräsentiert eine Frage für die Checkliste zu einer Vorgabe.

**Wichtige Felder**:
- `vorgabe` (ForeignKey → Vorgabe, on_delete=CASCADE, related_name='checklistenfragen')
- `frage` (CharField, max_length=255): Text der Checklistenfrage

**Besonderheiten**:
- `__str__()` gibt den Fragetext zurück

**Meta**:
- `verbose_name = "Frage für Checkliste"`
- `verbose_name_plural = "Fragen für Checkliste"`

---

### VorgabenTable

**Zweck**: Proxy-Modell für `Vorgabe` für die Darstellung von Vorgaben in Tabellenform.

**Besonderheiten**:
- Proxy-Modell (kein eigenes Datenbankschema)
- Ermöglicht alternative Django-Admin-Ansicht
- Erbt alle Felder und Methoden von `Vorgabe`

**Meta**:
- `proxy = True`
- `verbose_name = "Vorgabe (Tabellenansicht)"`
- `verbose_name_plural = "Vorgaben (Tabellenansicht)"`

---

### Changelog

**Zweck**: Dokumentiert Änderungen und Versionshistorie für Dokumente.

**Wichtige Felder**:
- `dokument` (ForeignKey → Dokument, on_delete=CASCADE, related_name='changelog'): Referenz zum Dokument
- `autoren` (ManyToManyField → Person): Personen, die die Änderung vorgenommen haben
- `datum` (DateField): Datum der Änderung
- `aenderung` (TextField): Beschreibung der Änderung

**Beziehungen**:
- Foreign Key zu `Dokument`
- Many-to-Many zu `Person`

**Besonderheiten**:
- `__str__()` formatiert als "datum – dokumentnummer"

**Meta**:
- `verbose_name = "Changelog-Eintrag"`
- `verbose_name_plural = "Changelog"`

---

## App: abschnitte

Modelle für die Verwaltung von Textabschnitten, die von mehreren Modellen geerbt werden.

### AbschnittTyp

**Zweck**: Klassifizierung von Textabschnitten (z. B. "Beschreibung", "Erklärung", "Anleitung").

**Wichtige Felder**:
- `abschnitttyp` (CharField, max_length=100, **PRIMARY KEY**): Name des Abschnitttyps

**Besonderheiten**:
- `__str__()` gibt den Namen zurück

**Meta**:
- `verbose_name_plural = "Abschnitttypen"`

---

### Textabschnitt (abstrakt)

**Zweck**: Abstrakte Basisklasse für Textinhalte, die mit anderen Modellen verknüpft sind.

**Wichtige Felder**:
- `abschnitttyp` (ForeignKey → AbschnittTyp, on_delete=PROTECT, optional)
- `inhalt` (TextField, blank=True, null=True): Der Textinhalt
- `order` (PositiveIntegerField, default=0): Sortierreihenfolge

**Besonderheiten**:
- Abstrakte Klasse (wird nicht direkt in der Datenbank gespeichert)
- Wird von anderen Modellen geerbt: `VorgabeLangtext`, `VorgabeKurztext`, `Geltungsbereich`, `Einleitung`, `Referenzerklaerung`, `Stichworterklaerung`, `RollenBeschreibung`

**Meta**:
- `abstract = True`
- `verbose_name = "Abschnitt"`
- `verbose_name_plural = "Abschnitte"`

---

## App: referenzen

Modelle für die Verwaltung von Referenzen und Verweisen auf externe Standards.

### Referenz (MPTT-Tree)

**Zweck**: Hierarchische Verwaltung von Referenzen und externen Normen (z. B. ISO-Standards, Gesetze, übergeordnete Vorgaben).

**Wichtige Felder**:
- `id` (AutoField, **PRIMARY KEY**)
- `name_nummer` (CharField, max_length=100): Nummer/Kennung der Referenz (z. B. "ISO 27001")
- `name_text` (CharField, max_length=255, blank=True): Ausführlicher Name/Beschreibung
- `oberreferenz` (TreeForeignKey zu self, optional): Parent-Referenz für Hierarchien
- `url` (URLField, blank=True): Link zur Referenz

**Beziehungen**:
- Many-to-Many mit `Vorgabe`
- MPTT Tree-Struktur für hierarchische Referenzen

**Wichtige Methoden**:

- `Path()` → str
  - Gibt die vollständige Pfad-Hierarchie als String zurück
  - Format: "Referenz → Subreferenz → Unterreferenz (Beschreibung)"
  - Beispiel: "ISO → 27000 → 27001 (Information Security Management)"

**Besonderheiten**:
- Verwendet MPPT (Modified Preorder Tree Traversal) für Baumoperationen
- `get_ancestors(include_self=True)`: Gibt alle Vorfahren zurück
- `unterreferenzen`: Related_name für Kindreferenzen
- Sortierung: Nach `name_nummer`

**Meta**:
- `verbose_name_plural = "Referenzen"`
- **MPTTMeta**:
  - `parent_attr = 'oberreferenz'`
  - `order_insertion_by = ['name_nummer']`

---

### Referenzerklaerung

**Zweck**: Speichert Erklärungen und zusätzliche Informationen zu einer Referenz.

**Wichtige Felder**:
- `erklaerung` (ForeignKey → Referenz, on_delete=CASCADE): Referenz zur Referenz
- Erbt von `Textabschnitt`:
  - `abschnitttyp` (ForeignKey → AbschnittTyp, optional)
  - `inhalt` (TextField, blank=True, null=True)
  - `order` (PositiveIntegerField, default=0)

**Meta**:
- `verbose_name = "Erklärung"`
- `verbose_name_plural = "Erklärungen"`

---

## App: stichworte

Modelle für die Verwaltung von Stichworte und Tags.

### Stichwort

**Zweck**: Einfache Tag/Keyword-Modell zur Kategorisierung von Vorgaben.

**Wichtige Felder**:
- `stichwort` (CharField, max_length=50, **PRIMARY KEY**): Das Stichwort

**Beziehungen**:
- Many-to-Many mit `Vorgabe`

**Besonderheiten**:
- `__str__()` gibt das Stichwort zurück

**Meta**:
- `verbose_name_plural = "Stichworte"`

---

### Stichworterklaerung

**Zweck**: Speichert Erklärungen zu Stichworten.

**Wichtige Felder**:
- `erklaerung` (ForeignKey → Stichwort, on_delete=CASCADE): Referenz zum Stichwort
- Erbt von `Textabschnitt`:
  - `abschnitttyp` (ForeignKey → AbschnittTyp, optional)
  - `inhalt` (TextField, blank=True, null=True)
  - `order` (PositiveIntegerField, default=0)

**Meta**:
- `verbose_name = "Erklärung"`
- `verbose_name_plural = "Erklärungen"`

---

## App: rollen

Modelle für die Verwaltung von Rollen und deren Beschreibungen.

### Rolle

**Zweck**: Definiert Rollen/Positionen im Unternehmen (z. B. "Geschäftsleiter", "IT-Sicherheit", "Datenschutzbeauftragter").

**Wichtige Felder**:
- `name` (CharField, max_length=100, **PRIMARY KEY**): Name der Rolle

**Beziehungen**:
- Many-to-Many mit `Vorgabe` (über `relevanz`)

**Besonderheiten**:
- `__str__()` gibt den Namen zurück
- Wird verwendet, um Rollen zu markieren, die von einer Vorgabe betroffen sind

**Meta**:
- `verbose_name_plural = "Rollen"`

---

### RollenBeschreibung

**Zweck**: Speichert detaillierte Beschreibungen und Informationen zu einer Rolle.

**Wichtige Felder**:
- `abschnitt` (ForeignKey → Rolle, on_delete=CASCADE): Referenz zur Rolle
- Erbt von `Textabschnitt`:
  - `abschnitttyp` (ForeignKey → AbschnittTyp, optional)
  - `inhalt` (TextField, blank=True, null=True)
  - `order` (PositiveIntegerField, default=0)

**Meta**:
- `verbose_name = "Rollenbeschreibungs-Abschnitt"`
- `verbose_name_plural = "Rollenbeschreibung"`

---

## Allgemeine Hinweise zur Modellverwaltung

### Primärschlüssel-Strategie
- Viele Modelle verwenden CharField-basierte Primärschlüssel (`name`, `nummer`, `stichwort`)
- Dies ermöglicht direkte Verwendung von Strings als Identifikatoren
- Vorteil: Lesbarkeit; Nachteil: Umbenennungen sind kritisch

### On-Delete-Strategien
- **PROTECT**: Verwendet für wichtige Beziehungen (z. B. Dokumententyp, Thema, AbschnittTyp)
  - Verhindert versehentliches Löschen von Daten, auf die verwiesen wird
- **CASCADE**: Verwendet für Unterkomponenten (z. B. Vorgabe → Dokument)
  - Löscht abhängige Datensätze automatisch
- **SET_NULL**: Nur bei optionalen Referenzen (z. B. Oberreferenz in Referenz-Tree)

### Validierungsmechanismen
- **Vorgabe.clean()**: Validiert Gültigkeitszeiträume
- **Vorgabe.find_conflicts()**: Prüft zeitliche Überschneidungen
- Wird von Django-Admin automatisch aufgerufen vor dem Speichern

### MPTT (Modified Preorder Tree Traversal)
- Verwendet in `Referenz` für hierarchische Strukturen
- Ermöglicht effiziente Abfragen von Vorfahren und Nachkommen
- Zusätzliche Datenbank-Felder für Tree-Management (automatisch verwaltet)

### Textabschnitt-Vererbung
- Mehrere Modelle erben von `Textabschnitt`
- Wird verwendet für Lang-/Kurztexte, Erklärungen, Beschreibungen
- `order`-Feld ermöglicht Sortierung mehrerer Abschnitte

### Datumsverwaltung
- `gueltigkeit_von`: Immer erforderlich für Vorgaben
- `gueltigkeit_bis`: Optional; `None` bedeutet unbegrenzte Gültigkeit
- `_date_ranges_intersect()` prüft korrekt auf Überschneidungen mit None-Werten

### Many-to-Many-Beziehungen
- Vielfach verwendet für flexible Zuordnungen (Autoren, Stichworte, Rollen, Referenzen)
- `related_name`-Attribute ermöglichen rückwärts Zugriff
- Beispiel: `dokument.vorgaben.all()`, `person.verfasste_dokumente.all()`

---

## Zusammenfassung der Beziehungen

```
Dokumententyp ← Dokument
Person ← Dokument (Autoren/Prüfer)
Dokument → Vorgabe (1-to-Many)
Dokument → Geltungsbereich (1-to-Many)
Dokument → Einleitung (1-to-Many)
Dokument → Changelog (1-to-Many)

Thema ← Vorgabe
Vorgabe → VorgabeLangtext (1-to-Many)
Vorgabe → VorgabeKurztext (1-to-Many)
Vorgabe → Checklistenfrage (1-to-Many)
Vorgabe ← Referenz (Many-to-Many)
Vorgabe ← Stichwort (Many-to-Many)
Vorgabe ← Rolle (Many-to-Many)

Referenz → Referenz (Hierarchie via MPPT)
Referenz → Referenzerklaerung (1-to-Many)

Stichwort → Stichworterklaerung (1-to-Many)

Rolle → RollenBeschreibung (1-to-Many)

AbschnittTyp ← Textabschnitt (von verschiedenen Modellen geerbt)
```

---

## Entwicklungsrichtlinien

- Alle Modelle sollten aussagekräftige `__str__()`-Methoden haben
- `verbose_name` und `verbose_name_plural` sollten auf Deutsch sein (für Django-Admin)
- Validierungslogik (z. B. `clean()`) sollte implementiert werden für komplexe Business-Logic
- Related-Names sollten aussagekräftig und konsistent sein
- Textinhalte sollten die `Textabschnitt`-Basisklasse erben
- Datumsverwaltung: Immer auf None-Werte bei `gueltigkeit_bis` achten, wenn Vorgaben noch aktiv sind.
