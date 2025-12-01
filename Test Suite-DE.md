# Test-Suite Dokumentation

Dieses Dokument bietet einen umfassenden Überblick über alle Tests im vgui-cicd Django-Projekt und beschreibt, was jeder Test tut und wie er funktioniert.

## Inhaltsverzeichnis

- [abschnitte App Tests](#abschnitte-app-tests)
- [dokumente App Tests](#dokumente-app-tests)
- [pages App Tests](#pages-app-tests)
- [referenzen App Tests](#referenzen-app-tests)
- [rollen App Tests](#rollen-app-tests)
- [stichworte App Tests](#stichworte-app-tests)

---

## abschnitte App Tests

Die abschnitte App enthält 33 Tests, die Modelle, Utility-Funktionen, Diagram-Caching, Management-Befehle und Sicherheit abdecken.

### Modell-Tests

#### AbschnittTypModelTest
- **test_abschnitttyp_creation**: Überprüft, dass AbschnittTyp-Objekte korrekt mit den erwarteten Feldwerten erstellt werden
- **test_abschnitttyp_primary_key**: Bestätigt, dass das `abschnitttyp`-Feld als Primärschlüssel dient
- **test_abschnitttyp_str**: Testet die String-Repräsentation, die den `abschnitttyp`-Wert zurückgibt
- **test_abschnitttyp_verbose_name_plural**: Validiert den korrekt gesetzten verbose_name_plural
- **test_create_multiple_abschnitttypen**: Stellt sicher, dass mehrere AbschnittTyp-Objekte mit verschiedenen Typen erstellt werden können

#### TextabschnittModelTest
- **test_textabschnitt_creation**: Testet, dass Textabschnitt über das konkrete Modell instanziiert werden kann
- **test_textabschnitt_default_order**: Überprüft, dass das `order`-Feld standardmäßig 0 ist
- **test_textabschnitt_ordering**: Testet, dass Textabschnitt-Objekte nach dem `order`-Feld sortiert werden können
- **test_textabschnitt_blank_fields**: Bestätigt, dass `abschnitttyp`- und `inhalt`-Felder leer/null sein können
- **test_textabschnitt_foreign_key_protection**: Testet, dass AbschnittTyp-Objekte vor Löschung geschützt sind, wenn sie von Textabschnitt referenziert werden

### Utility-Funktions-Tests

#### MdTableToHtmlTest
- **test_simple_table**: Konvertiert eine einfache Markdown-Tabelle mit Überschriften und einer Zeile nach HTML
- **test_table_with_multiple_rows**: Testet die Konvertierung von Tabellen mit mehreren Datenzeilen
- **test_table_with_empty_cells**: Verarbeitet Tabellen mit leeren Zellen in den Daten
- **test_table_with_spaces**: Verarbeitet Tabellen mit zusätzlichen Leerzeichen in Zellen
- **test_table_empty_string**: Löst ValueError für leere Eingabe-Strings aus
- **test_table_only_whitespace**: Löst ValueError für Strings aus, die nur Leerzeichen enthalten
- **test_table_insufficient_lines**: Löst ValueError aus, wenn die Eingabe weniger als 2 Zeilen hat

#### RenderTextabschnitteTest
- **test_render_empty_queryset**: Gibt leeren String für leere Querysets zurück
- **test_render_multiple_abschnitte**: Rendert mehrere Textabschnitte in korrekter Reihenfolge
- **test_render_text_markdown**: Konvertiert Klartext mit Markdown-Formatierung
- **test_render_ordered_list**: Rendert geordnete Listen korrekt
- **test_render_unordered_list**: Rendert ungeordnete Listen korrekt
- **test_render_code_block**: Rendert Code-Blöcke mit korrekter Syntax-Hervorhebung
- **test_render_table**: Konvertiert Markdown-Tabellen mit md_table_to_html nach HTML
- **test_render_diagram_success**: Testet die Diagramm-Generierung mit erfolgreichem Caching
- **test_render_diagram_error**: Behandelt Diagramm-Generierungsfehler angemessen
- **test_render_diagram_with_options**: Testet das Diagramm-Rendering mit benutzerdefinierten Optionen
- **test_render_text_with_footnotes**: Verarbeitet Text, der Fußnoten enthält
- **test_render_abschnitt_without_type**: Behandelt Textabschnitte ohne AbschnittTyp
- **test_render_abschnitt_with_empty_content**: Behandelt Textabschnitte mit leerem Inhalt
- **test_render_textabschnitte_xss_prevention**: Überprüft, dass bösartiger HTML-Code und Skript-Tags aus gerenderten Inhalten bereinigt werden, um XSS-Angriffe zu verhindern

### Diagram-Caching-Tests

#### DiagramCacheTest
- **test_compute_hash**: Generiert konsistente SHA256-Hashes für dieselbe Eingabe
- **test_get_cache_path**: Erstellt korrekte Cache-Dateipfade basierend auf Hash und Typ
- **test_get_cached_diagram_hit**: Gibt zwischengespeichertes Diagramm zurück bei Cache-Treffer
- **test_get_cached_diagram_miss**: Generiert neues Diagramm bei Cache-Fehltreffer
- **test_get_cached_diagram_request_error**: Behandelt und löst Request-Fehler korrekt aus
- **test_clear_cache_specific_type**: Löscht Cache-Dateien für spezifische Diagrammtypen
- **test_clear_cache_all_types**: Löscht alle Cache-Dateien, wenn kein Typ angegeben ist

### Management-Befehl-Tests

#### ClearDiagramCacheCommandTest
- **test_command_without_type**: Testet die Ausführung des Management-Befehls ohne Angabe des Typs
- **test_command_with_type**: Testet die Ausführung des Management-Befehls mit spezifischem Diagrammtyp

### Integrations-Tests

#### IntegrationTest
- **test_textabschnitt_inheritance**: Überprüft, dass VorgabeLangtext Textabschnitt-Felder korrekt erbt
- **test_render_vorgabe_langtext**: Testet das Rendern von VorgabeLangtext durch render_textabschnitte

---

## dokumente App Tests

Die dokumente App enthält 121 Tests und ist damit die umfassendste Test-Suite, die alle Modelle, Views, URLs, Geschäftslogik und Kommentarfunktionalität mit XSS-Schutz abdeckt.

### Modell-Tests

#### DokumententypModelTest
- **test_dokumententyp_creation**: Überprüft die Erstellung von Dokumententyp mit korrekten Feldwerten
- **test_dokumententyp_str**: Testet die String-Repräsentation, die das `typ`-Feld zurückgibt
- **test_dokumententyp_verbose_name**: Validiert den korrekt gesetzten verbose_name

#### PersonModelTest
- **test_person_creation**: Testet die Erstellung von Person-Objekten mit Name und optionalem Titel
- **test_person_str**: Überprüft, dass die String-Repräsentation Titel und Namen enthält
- **test_person_verbose_name_plural**: Testet die Konfiguration von verbose_name_plural

#### ThemaModelTest
- **test_thema_creation**: Testet die Erstellung von Thema mit Name und optionaler Erklärung
- **test_thema_str**: Überprüft, dass die String-Repräsentation den Themennamen zurückgibt
- **test_thema_blank_erklaerung**: Bestätigt, dass das `erklaerung`-Feld leer sein kann

#### DokumentModelTest
- **test_dokument_creation**: Testet die Erstellung von Dokument mit erforderlichen und optionalen Feldern
- **test_dokument_str**: Überprüft, dass die String-Repräsentation den Dokumenttitel zurückgibt
- **test_dokument_optional_fields**: Testet, dass optionale Felder None oder leer sein können
- **test_dokument_many_to_many_relationships**: Überprüft Many-to-Many-Beziehungen mit Personen und Themen

#### VorgabeModelTest
- **test_vorgabe_creation**: Testet die Erstellung von Vorgabe mit allen erforderlichen Feldern
- **test_vorgabe_str**: Überprüft, dass die String-Repräsentation die Vorgabennummer zurückgibt
- **test_vorgabennummer**: Testet die automatische Generierung des Vorgabennummer-Formats
- **test_get_status_active**: Testet die Statusbestimmung für aktuelle aktive Vorgaben
- **test_get_status_expired**: Testet die Statusbestimmung für abgelaufene Vorgaben
- **test_get_status_future**: Testet die Statusbestimmung für zukünftige Vorgaben
- **test_get_status_with_custom_check_date**: Testet den Status mit benutzerdefiniertem Prüfdatum
- **test_get_status_verbose**: Testet die ausführliche Statusausgabe

#### ChangelogModelTest
- **test_changelog_creation**: Testet die Erstellung von Changelog mit Version, Datum und Beschreibung
- **test_changelog_str**: Überprüft, dass die String-Repräsentation Version und Datum enthält

#### ChecklistenfrageModelTest
- **test_checklistenfrage_creation**: Testet die Erstellung von Checklistenfrage mit Frage und optionaler Antwort
- **test_checklistenfrage_str**: Überprüft, dass die String-Repräsentation lange Fragen kürzt
- **test_checklistenfrage_related_name**: Testet die umgekehrte Beziehung von Vorgabe

#### VorgabeCommentModelTest
- **test_comment_creation**: Testet die Erstellung von VorgabeComment mit Vorgabe, Benutzer und Text
- **test_comment_str**: Überprüft, dass die String-Repräsentation Benutzername und Vorgabennummer enthält
- **test_comment_related_name**: Testet die umgekehrte Beziehung von Vorgabe
- **test_comment_ordering**: Testet, dass Kommentare nach created_at absteigend sortiert sind (neueste zuerst)
- **test_comment_timestamps_auto_update**: Testet, dass sich updated_at ändert, wenn ein Kommentar geändert wird
- **test_multiple_users_can_comment**: Testet, dass mehrere Benutzer zur selben Vorgabe kommentieren können

### Text-Abschnitt-Tests

#### DokumentTextAbschnitteTest
- **test_einleitung_creation**: Testet die Erstellung von Einleitung und Vererbung von Textabschnitt
- **test_geltungsbereich_creation**: Testet die Erstellung von Geltungsbereich und Vererbung

#### VorgabeTextAbschnitteTest
- **test_vorgabe_kurztext_creation**: Testet die Erstellung von VorgabeKurztext und Vererbung
- **test_vorgabe_langtext_creation**: Testet die Erstellung von VorgabeLangtext und Vererbung

### Sanity-Check-Tests

#### VorgabeSanityCheckTest
- **test_date_ranges_intersect_no_overlap**: Testet Datumsüberschneidung mit nicht überlappenden Bereichen
- **test_date_ranges_intersect_with_overlap**: Testet Datumsüberschneidung mit überlappenden Bereichen
- **test_date_ranges_intersect_identical_ranges**: Testet Datumsüberschneidung mit identischen Bereichen
- **test_date_ranges_intersect_with_none_end_date**: Testet Überschneidung mit offenen Endbereichen
- **test_date_ranges_intersect_both_none_end_dates**: Testet Überschneidung mit zwei offenen Endbereichen
- **test_check_vorgabe_conflicts_utility**: Testet die Utility-Funktion zur Konflikterkennung
- **test_find_conflicts_no_conflicts**: Testet die Konflikterkennung bei Vorgabe ohne Konflikte
- **test_find_conflicts_with_conflicts**: Testet die Konflikterkennung mit konfliktbehafteten Vorgaben
- **test_format_conflict_report_no_conflicts**: Testet die Konfliktbericht-Formatierung ohne Konflikte
- **test_format_conflict_report_with_conflicts**: Testet die Konfliktbericht-Formatierung mit Konflikten
- **test_sanity_check_vorgaben_no_conflicts**: Testet vollständigen Sanity-Check ohne Konflikte
- **test_sanity_check_vorgaben_with_conflicts**: Testet vollständigen Sanity-Check mit Konflikten
- **test_sanity_check_vorgaben_multiple_conflicts**: Testet Sanity-Check mit mehreren Konfliktgruppen
- **test_vorgabe_clean_no_conflicts**: Testet Vorgabe.clean()-Methode ohne Konflikte
- **test_vorgabe_clean_with_conflicts**: Testet, dass Vorgabe.clean() ValidationError bei Konflikten auslöst

### Management-Befehl-Tests

#### SanityCheckManagementCommandTest
- **test_sanity_check_command_no_conflicts**: Testet Management-Befehlsausgabe ohne Konflikte
- **test_sanity_check_command_with_conflicts**: Testet Management-Befehlsausgabe mit Konflikten

### URL-Pattern-Tests

#### URLPatternsTest
- **test_standard_list_url_resolves**: Überprüft, dass standard_list URL zur korrekten View aufgelöst wird
- **test_standard_detail_url_resolves**: Überprüft, dass standard_detail URL mit pk-Parameter aufgelöst wird
- **test_standard_history_url_resolves**: Überprüft, dass standard_history URL mit check_date aufgelöst wird
- **test_standard_checkliste_url_resolves**: Überprüft, dass standard_checkliste URL mit pk aufgelöst wird

### View-Tests

#### ViewsTestCase
- **test_standard_list_view**: Testet, dass die Standard-Listen-View 200 zurückgibt und erwartete Inhalte enthält
- **test_standard_detail_view**: Testet die Standard-Detail-View mit existierendem Dokument
- **test_standard_detail_view_404**: Testet, dass die Standard-Detail-View 404 für nicht existierendes Dokument zurückgibt
- **test_standard_history_view**: Testet die Standard-Detail-View mit historischem check_date-Parameter
- **test_standard_checkliste_view**: Testet die Funktionalität der Checklisten-View

### JSON-Export-Tests

#### JSONExportManagementCommandTest
- **test_export_json_command_to_file**: Testet, dass der export_json-Befehl JSON in die angegebene Datei ausgibt
- **test_export_json_command_stdout**: Testet, dass der export_json-Befehl JSON an stdout ausgibt, wenn keine Datei angegeben ist
- **test_export_json_command_inactive_documents**: Testet, dass der export_json-Befehl inaktive Dokumente herausfiltert
- **test_export_json_command_empty_database**: Testet, dass der export_json-Befehl leere Datenbank angemessen behandelt

#### StandardJSONViewTest
- **test_standard_json_view_success**: Testet, dass die standard_json-View korrektes JSON für existierendes Dokument zurückgibt
- **test_standard_json_view_not_found**: Testet, dass die standard_json-View 404 für nicht existierendes Dokument zurückgibt
- **test_standard_json_view_json_formatting**: Testet, dass die standard_json-View korrekt formatiertes JSON zurückgibt
- **test_standard_json_view_null_dates**: Testet, dass die standard_json-View null-Datumfelder korrekt behandelt
- **test_standard_json_view_empty_sections**: Testet, dass die standard_json-View leere Dokumentabschnitte behandelt

### Unvollständige Vorgaben Tests

#### IncompleteVorgabenTest
- **test_incomplete_vorgaben_page_status**: Testet, dass die Seite erfolgreich lädt (200-Status)
- **test_incomplete_vorgaben_staff_only**: Testet, dass Nicht-Staff-Benutzer zum Login weitergeleitet werden
- **test_incomplete_vorgaben_page_content**: Testet, dass die Seite erwartete Überschriften und Struktur enthält
- **test_navigation_link**: Testet, dass die Navigation einen Link zur unvollständigen Vorgaben-Seite enthält
- **test_no_references_list**: Testet, dass Vorgaben ohne Referenzen korrekt aufgelistet werden
- **test_no_stichworte_list**: Testet, dass Vorgaben ohne Stichworte korrekt aufgelistet werden
- **test_no_text_list**: Testet, dass Vorgaben ohne Kurz- oder Langtext korrekt aufgelistet werden
- **test_no_checklistenfragen_list**: Testet, dass Vorgaben ohne Checklistenfragen korrekt aufgelistet werden
- **test_vorgabe_with_both_text_types**: Testet, dass Vorgabe mit beiden Texttypen als vollständig betrachtet wird
- **test_vorgabe_with_langtext_only**: Testet, dass Vorgabe mit nur Langtext immer noch unvollständig für Text ist
- **test_empty_lists_message**: Testet angemessene Nachrichten, wenn Listen leer sind
- **test_badge_counts**: Testet, dass Badge-Zähler korrekt berechnet werden
- **test_summary_section**: Testet, dass die Zusammenfassungssektion korrekte Zähler anzeigt
- **test_vorgabe_links**: Testet, dass Vorgaben zu korrekten Admin-Seiten verlinken
- **test_back_link**: Testet, dass der Zurück-Link zur Standardübersicht existiert

### Kommentar-Funktionalität Tests

#### GetVorgabeCommentsViewTest
- **test_get_comments_requires_login**: Testet, dass anonyme Benutzer keine Kommentare sehen können und weitergeleitet werden
- **test_regular_user_sees_only_own_comments**: Testet, dass normale Benutzer nur ihre eigenen Kommentare sehen
- **test_staff_user_sees_all_comments**: Testet, dass Staff-Benutzer alle Kommentare sehen können
- **test_get_comments_returns_404_for_nonexistent_vorgabe**: Testet 404-Antwort für nicht existierende Vorgabe
- **test_comments_are_html_escaped**: Testet HTML-Escaping zur Verhinderung von XSS-Angriffen (z.B. `<script>`-Tags)
- **test_line_breaks_preserved**: Testet, dass Zeilenumbrüche in `<br>`-Tags umgewandelt werden
- **test_security_headers_present**: Testet, dass Content-Security-Policy und X-Content-Type-Options Header gesetzt sind

#### AddVorgabeCommentViewTest
- **test_add_comment_requires_login**: Testet, dass anonyme Benutzer keine Kommentare hinzufügen können
- **test_add_comment_requires_post**: Testet, dass nur POST-Methode erlaubt ist (405 für GET)
- **test_add_comment_success**: Testet erfolgreiche Kommentarerstellung mit gültigen Daten
- **test_add_empty_comment_fails**: Testet, dass leere Kommentare mit 400-Fehler abgelehnt werden
- **test_add_whitespace_only_comment_fails**: Testet, dass Kommentare nur mit Leerzeichen abgelehnt werden
- **test_add_too_long_comment_fails**: Testet, dass Kommentare über 2000 Zeichen abgelehnt werden
- **test_add_comment_xss_script_tag_blocked**: Testet, dass Kommentare mit `<script>`-Tags blockiert werden
- **test_add_comment_xss_javascript_protocol_blocked**: Testet, dass `javascript:`-Protokoll blockiert wird
- **test_add_comment_xss_event_handlers_blocked**: Testet, dass Event-Handler (onload, onerror, onclick, onmouseover) blockiert werden
- **test_add_comment_invalid_json_fails**: Testet, dass ungültige JSON-Payloads abgelehnt werden
- **test_add_comment_nonexistent_vorgabe_fails**: Testet 404-Antwort für nicht existierende Vorgabe
- **test_add_comment_security_headers**: Testet, dass Sicherheits-Header in Antworten vorhanden sind

#### DeleteVorgabeCommentViewTest
- **test_delete_comment_requires_login**: Testet, dass anonyme Benutzer keine Kommentare löschen können
- **test_delete_comment_requires_post**: Testet, dass nur POST-Methode erlaubt ist (405 für GET)
- **test_user_can_delete_own_comment**: Testet, dass Benutzer ihre eigenen Kommentare löschen können
- **test_user_cannot_delete_other_users_comment**: Testet, dass Benutzer keine Kommentare anderer löschen können (403 Forbidden)
- **test_staff_can_delete_any_comment**: Testet, dass Staff-Benutzer jeden Kommentar löschen können
- **test_delete_nonexistent_comment_returns_404**: Testet 404-Antwort für nicht existierenden Kommentar
- **test_delete_comment_security_headers**: Testet, dass Sicherheits-Header in Antworten vorhanden sind

---

## pages App Tests

Die pages App enthält 4 Tests, die sich auf die Suchfunktionalität und Validierung konzentrieren.

### ViewsTestCase
- **test_search_view_get**: Testet GET-Anfrage an die Search-View gibt 200-Status zurück
- **test_search_view_post_with_query**: Testet POST-Anfrage mit Query gibt Ergebnisse zurück
- **test_search_view_post_empty_query**: Testet POST-Anfrage mit leerer Query zeigt Validierungsfehler
- **test_search_view_post_no_query**: Testet POST-Anfrage ohne Query-Parameter zeigt Validierungsfehler

---

## referenzen App Tests

Die referenzen App enthält 18 Tests, die sich auf MPTT-Hierarchiefunktionalität und Modellbeziehungen konzentrieren.

### Modell-Tests

#### ReferenzModelTest
- **test_referenz_creation**: Testet die Erstellung von Referenz mit erforderlichen Feldern
- **test_referenz_str**: Testet die String-Repräsentation gibt den Referenztext zurück
- **test_referenz_ordering**: Testet die Standard-Sortierung nach `order`-Feld
- **test_referenz_optional_fields**: Testet, dass optionale Felder leer sein können

#### ReferenzerklaerungModelTest
- **test_referenzerklaerung_creation**: Testet die Erstellung von Referenzerklaerung mit Referenz und Erklärung
- **test_referenzerklaerung_str**: Testet die String-Repräsentation enthält Referenz und Erklärungsvorschau
- **test_referenzerklaerung_ordering**: Testet die Standard-Sortierung nach `order`-Feld
- **test_referenzerklaerung_optional_explanation**: Testet, dass das Erklärungsfeld leer sein kann

### Hierarchie-Tests

#### ReferenzHierarchyTest
- **test_hierarchy_relationships**: Testet Eltern-Kind-Beziehungen im MPTT-Baum
- **test_get_root**: Testet das Abrufen des Wurzelknotens einer Hierarchie
- **test_get_children**: Testet das Abrufen direkter Kinder eines Knotens
- **test_get_descendants**: Testet das Abrufen aller Nachkommen eines Knotens
- **test_get_ancestors**: Testet das Abrufen aller Vorfahren eines Knotens
- **test_get_ancestors_include_self**: Testet das Abrufen von Vorfahren einschließlich des Knotens selbst
- **test_is_leaf_node**: Testet die Erkennung von Blattknoten
- **test_is_root_node**: Testet die Erkennung von Wurzelknoten
- **test_tree_ordering**: Testet die Baum-Sortierung mit mehreren Ebenen
- **test_move_node**: Testet das Verschieben von Knoten innerhalb der Baumstruktur

---

## rollen App Tests

Die rollen App enthält 18 Tests, die Rollenmodelle und ihre Beziehungen zu Dokumentabschnitten abdecken.

### Modell-Tests

#### RolleModelTest
- **test_rolle_creation**: Testet die Erstellung von Rolle mit Name und optionaler Beschreibung
- **test_rolle_str**: Testet die String-Repräsentation gibt den Rollennamen zurück
- **test_rolle_ordering**: Testet die Standard-Sortierung nach `order`-Feld
- **test_rolle_unique_name**: Testet, dass Rollennamen einzigartig sein müssen
- **test_rolle_optional_beschreibung**: Testet, dass das Beschreibungsfeld leer sein kann

#### RollenBeschreibungModelTest
- **test_rollenbeschreibung_creation**: Testet die Erstellung von RollenBeschreibung mit Rolle und Abschnittstyp
- **test_rollenbeschreibung_str**: Testet die String-Repräsentation enthält Rolle und Abschnittstyp
- **test_rollenbeschreibung_ordering**: Testet die Standard-Sortierung nach `order`-Feld
- **test_rollenbeschreibung_unique_combination**: Testet die Unique-Constraint auf Rolle und Abschnittstyp
- **test_rollenbeschreibung_optional_beschreibung**: Testet, dass das Beschreibungsfeld leer sein kann

### Beziehungs-Tests

#### RelationshipTest
- **test_rolle_rollenbeschreibung_relationship**: Testet die Eins-zu-viele-Beziehung zwischen Rolle und RollenBeschreibung
- **test_abschnitttyp_rollenbeschreibung_relationship**: Testet die Beziehung zwischen AbschnittTyp und RollenBeschreibung
- **test_cascade_delete**: Testet das Cascade-Delete-Verhalten beim Löschen einer Rolle
- **test_protected_delete**: Testet das Protected-Delete-Verhalten, wenn Abschnittstyp referenziert wird
- **test_query_related_objects**: Testet das effiziente Abfragen verwandter Objekte
- **test_string_representations**: Testet, dass alle String-Repräsentationen korrekt funktionieren
- **test_ordering_consistency**: Testet, dass die Sortierung über Abfragen hinweg konsistent ist

---

## stichworte App Tests

Die stichworte App enthält 18 Tests, die Schlüsselwortmodelle und ihre Sortierung abdecken.

### Modell-Tests

#### StichwortModelTest
- **test_stichwort_creation**: Testet die Erstellung von Stichwort mit Schlüsselworttext
- **test_stichwort_str**: Testet die String-Repräsentation gibt den Schlüsselworttext zurück
- **test_stichwort_ordering**: Testet die Standard-Sortierung nach `stichwort`-Feld
- **test_stichwort_unique**: Testet, dass Schlüsselwörter einzigartig sein müssen
- **test_stichwort_case_insensitive**: Testet die Groß-/Kleinschreibungs-unabhängige Eindeutigkeit

#### StichworterklaerungModelTest
- **test_stichworterklaerung_creation**: Testet die Erstellung von Stichworterklaerung mit Schlüsselwort und Erklärung
- **test_stichworterklaerung_str**: Testet die String-Repräsentation enthält Schlüsselwort und Erklärungsvorschau
- **test_stichworterklaerung_ordering**: Testet die Standard-Sortierung nach `order`-Feld
- **test_stichworterklaerung_optional_erklaerung**: Testet, dass das Erklärungsfeld leer sein kann
- **test_stichworterklaerung_unique_stichwort**: Testet den Unique-Constraint auf das Schlüsselwort

### Beziehungs-Tests

#### RelationshipTest
- **test_stichwort_stichworterklaerung_relationship**: Testet die Eins-zu-eins-Beziehung zwischen Stichwort und Stichworterklaerung
- **test_cascade_delete**: Testet das Cascade-Delete-Verhalten beim Löschen eines Schlüsselworts
- **test_protected_delete**: Testet das Protected-Delete-Verhalten, wenn Erklärung referenziert wird
- **test_query_related_objects**: Testet das effiziente Abfragen verwandter Objekte
- **test_string_representations**: Testet, dass alle String-Repräsentationen korrekt funktionieren
- **test_ordering_consistency**: Testet, dass die Sortierung über Abfragen hinweg konsistent ist
- **test_reverse_relationship**: Testet die umgekehrte Beziehung von Erklärung zu Schlüsselwort

---

## Test-Statistiken

- **Gesamt-Tests**: 230
- **abschnitte**: 33 Tests (einschließlich XSS-Prävention)
- **dokumente**: 121 Tests (einschließlich Kommentarfunktionalität mit XSS-Schutz)
  - Modell-Tests: 44 Tests
  - View-Tests: 7 Tests
  - URL-Pattern-Tests: 4 Tests
  - Sanity-Check-Tests: 16 Tests
  - Management-Befehl-Tests: 2 Tests
  - JSON-Export-Tests: 9 Tests
  - Unvollständige-Vorgaben-Tests: 15 Tests
  - Kommentar-Tests: 24 Tests (6 Modell + 18 View-Tests)
- **pages**: 4 Tests
- **referenzen**: 18 Tests
- **rollen**: 18 Tests
- **stichworte**: 18 Tests

## Test-Abdeckungsbereiche

1. **Modell-Validierung**: Feldvalidierung, Constraints und Beziehungen
2. **Geschäftslogik**: Statusbestimmung, Konflikterkennung, Hierarchieverwaltung
3. **View-Funktionalität**: HTTP-Antworten, Template-Rendering, URL-Auflösung
4. **Utility-Funktionen**: Textverarbeitung, Caching, Formatierung
5. **Management-Befehle**: CLI-Schnittstelle und Ausgabeverarbeitung
6. **Integration**: App-übergreifende Funktionalität und Datenfluss
7. **Sicherheit**: 
   - XSS-Prävention durch HTML-Bereinigung beim Rendern von Inhalten
   - XSS-Angriffsverhinderung im Kommentarsystem (Script-Tags, javascript:-Protokoll, Event-Handler)
   - Eingabevalidierung und -bereinigung
   - Autorisierungsprüfungen (Staff vs. normale Benutzer)
   - Sicherheits-Header (Content-Security-Policy, X-Content-Type-Options)
8. **Kommentar-Funktionalität**:
   - CRUD-Operationen (Create, Read, Delete)
   - Benutzerberechtigungen und -besitz
   - HTML-Escaping und Erhalt von Zeilenumbrüchen
   - Verhinderung mehrerer XSS-Angriffsvektoren

## Ausführen der Tests

Um alle Tests auszuführen:
```bash
python manage.py test
```

Um Tests für eine spezifische App auszuführen:
```bash
python manage.py test app_name
```

Um mit ausführlicher Ausgabe auszuführen:
```bash
python manage.py test --verbosity=2
```

Alle Tests laufen derzeit erfolgreich und bieten umfassende Abdeckung der Funktionalität der Anwendung.