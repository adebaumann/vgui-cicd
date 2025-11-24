# Modelle (App: dokumente)

Kurzbeschreibungen der Modelle in dokumente/models.py. 

## Dokumententyp
- Zweck: Kategorisierung von Dokumenten (z. B. Richtlinie, Verfahren).
- Wichtige Felder: `name` (CharField, PK), `verantwortliche_ve` (CharField).
- Besonderheiten: `__str__()` gibt `name` zurück.
- Meta: `verbose_name` und `verbose_name_plural` gesetzt.

## Person
- Zweck: Repräsentiert Personen (Autoren, Prüfer).
- Wichtige Felder: `name` (CharField, PK), `funktion` (CharField).
- Beziehungen: Many-to-many mit Dokument über `autoren` und `pruefende`.
- Besonderheiten: `__str__()` gibt `name` zurück; `ordering = ['name']`.
- Meta: `verbose_name_plural = "Personen"`.

## Thema
- Zweck: Thematische Einordnung von Vorgaben.
- Wichtige Felder: `name` (CharField, PK), `erklaerung` (TextField, optional).
- Besonderheiten: `__str__()` gibt `name` zurück.

## Dokument
- Zweck: Hauptobjekt; ein einzelnes Dokument mit Metadaten.
- Wichtige Felder:
  - `nummer` (CharField, PK)
  - `dokumententyp` (FK → Dokumententyp, on_delete=PROTECT)
  - `name` (CharField)
  - `autoren`, `pruefende` (ManyToManyField → Person)
  - `gueltigkeit_von`, `gueltigkeit_bis` (DateField, optional)
  - `aktiv` (BooleanField)
  - `signatur_cso`, `anhaenge` (Metadaten)
- Besonderheiten: `__str__()` formatiert als "nummer – name".
- Meta: `verbose_name` / `verbose_name_plural`.

## Vorgabe
- Zweck: Einzelne Vorgabe / Anforderung innerhalb eines Dokuments.
- Wichtige Felder:
  - `order` (IntegerField) — Sortierreihenfolge
  - `nummer` (IntegerField) — Nummer innerhalb Thema/Dokument
  - `dokument` (FK → Dokument, CASCADE, related_name='vorgaben')
  - `thema` (FK → Thema, PROTECT)
  - `titel` (CharField)
  - `referenzen` (M2M → Referenz, optional)
  - `stichworte` (M2M → Stichwort, optional)
  - `relevanz` (M2M → Rolle, optional)
  - `gueltigkeit_von`, `gueltigkeit_bis` (Datum/Felder)
- Beziehungen: zu Dokument, Thema, Referenzen, Stichworte, Rollen.
- Wichtige Methoden:
  - `Vorgabennummer()` — generiert eine lesbare Kennung (z. B. "DOK. T. N").
  - `get_status(check_date, verbose)` — liefert "future", "active" oder "expired" oder eine deutsche Statusbeschreibung, abhängig von Gültigkeitsdaten.
  - `sanity_check_vorgaben()` (static) — findet Konflikte zwischen Vorgaben mit gleicher Nummer/Thema/Dokument, deren Zeiträume sich überschneiden.
  - `clean()` — ruft `find_conflicts()` auf und wirft ValidationError bei Konflikten.
  - `find_conflicts()` — prüft Konflikte mit bestehenden Vorgaben (ohne sich selbst).
  - `_date_ranges_intersect(...)` (static) — prüft, ob sich zwei Datumsbereiche überschneiden (None = offen).
- Besonderheiten: `__str__()` gibt "Vorgabennummer: titel" zurück.
- Meta: `ordering = ['order']`, `verbose_name_plural = "Vorgaben"`.

## VorgabeLangtext, VorgabeKurztext
- Zweck: Textabschnitts-Modelle, erben von `Textabschnitt` (aus abschnitte.models).
- Wichtige Felder: je ein FK `abschnitt` → Vorgabe.
- Besonderheit: konkrete Untertypen für Lang- und Kurztexte; Meta-`verbose_name` gesetzt.

## Geltungsbereich, Einleitung
- Zweck: Dokumentbezogene Textabschnitte (erben von `Textabschnitt`).
- Wichtige Felder: FK zum `Dokument` (`geltungsbereich` bzw. `einleitung`).
- Meta: `verbose_name`/`verbose_name_plural` gesetzt.

## Checklistenfrage
- Zweck: Einzelne Frage für Checklisten zu einer Vorgabe.
- Wichtige Felder: `vorgabe` (FK → Vorgabe, related_name="checklistenfragen"), `frage` (CharField).
- Besonderheiten: `__str__()` gibt `frage` zurück.

## VorgabenTable
- Zweck: Proxy-Modell für Vorgabe zur Darstellung (Tabellenansicht).
- Besonderheiten: kein eigenes Schema; nur Meta-Attribute (`proxy = True`, `verbose_name`).

## Changelog
- Zweck: Änderungsverzeichnis-Eintrag für ein Dokument.
- Wichtige Felder:
  - `dokument` (FK → Dokument, related_name='changelog')
  - `autoren` (M2M → Person)
  - `datum` (DateField)
  - `aenderung` (TextField)
- Besonderheiten: `__str__()` formatiert als "datum – dokumentnummer".
- Meta: `verbose_name` / `verbose_name_plural`.

Hinweise zur Pflege
- Wichtige Relationen nutzen häufig on_delete=PROTECT, um versehentliche Löschungen zu vermeiden.
- Viele Modelle haben CharField-Primärschlüssel (z. B. `nummer`, `name`).
- Validierungslogik für zeitliche Konflikte ist in Vorgabe implementiert (clean / find_conflicts).
- Textabschnitt-Modelle erben Verhalten aus `abschnitte.models.Textabschnitt` — dort sind Anzeige- und Inhaltsregeln definiert.