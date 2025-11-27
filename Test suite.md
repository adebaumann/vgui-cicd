# Test Suite Documentation

This document provides a comprehensive overview of all tests in the vgui-cicd Django project, describing what each test does and how it works.

## Table of Contents

- [abschnitte App Tests](#abschnitte-app-tests)
- [dokumente App Tests](#dokumente-app-tests)
- [pages App Tests](#pages-app-tests)
- [referenzen App Tests](#referenzen-app-tests)
- [rollen App Tests](#rollen-app-tests)
- [stichworte App Tests](#stichworte-app-tests)

---

## abschnitte App Tests

The abschnitte app contains 33 tests covering models, utility functions, diagram caching, management commands, and security.

### Model Tests

#### AbschnittTypModelTest
- **test_abschnitttyp_creation**: Verifies that AbschnittTyp objects are created correctly with the expected field values
- **test_abschnitttyp_primary_key**: Confirms that the `abschnitttyp` field serves as the primary key
- **test_abschnitttyp_str**: Tests the string representation returns the `abschnitttyp` value
- **test_abschnitttyp_verbose_name_plural**: Validates the verbose name plural is set correctly
- **test_create_multiple_abschnitttypen**: Ensures multiple AbschnittTyp objects can be created with different types

#### TextabschnittModelTest
- **test_textabschnitt_creation**: Tests that Textabschnitt can be instantiated through the concrete model
- **test_textabschnitt_default_order**: Verifies the `order` field defaults to 0
- **test_textabschnitt_ordering**: Tests that Textabschnitt objects can be ordered by the `order` field
- **test_textabschnitt_blank_fields**: Confirms that `abschnitttyp` and `inhalt` fields can be blank/null
- **test_textabschnitt_foreign_key_protection**: Tests that AbschnittTyp objects are protected from deletion when referenced by Textabschnitt

### Utility Function Tests

#### MdTableToHtmlTest
- **test_simple_table**: Converts a basic markdown table with headers and one row to HTML
- **test_table_with_multiple_rows**: Tests conversion of tables with multiple data rows
- **test_table_with_empty_cells**: Handles tables with empty cells in the data
- **test_table_with_spaces**: Processes tables with extra spaces in cells
- **test_table_empty_string**: Raises ValueError for empty input strings
- **test_table_only_whitespace**: Raises ValueError for strings containing only whitespace
- **test_table_insufficient_lines**: Raises ValueError when input has fewer than 2 lines

#### RenderTextabschnitteTest
- **test_render_empty_queryset**: Returns empty string for empty querysets
- **test_render_multiple_abschnitte**: Renders multiple Textabschnitte in correct order
- **test_render_text_markdown**: Converts plain text with markdown formatting
- **test_render_ordered_list**: Renders ordered lists correctly
- **test_render_unordered_list**: Renders unordered lists correctly
- **test_render_code_block**: Renders code blocks with proper syntax highlighting
- **test_render_table**: Converts markdown tables to HTML using md_table_to_html
- **test_render_diagram_success**: Tests diagram generation with successful caching
- **test_render_diagram_error**: Handles diagram generation errors gracefully
- **test_render_diagram_with_options**: Tests diagram rendering with custom options
- **test_render_text_with_footnotes**: Processes text containing footnotes
- **test_render_abschnitt_without_type**: Handles Textabschnitte without AbschnittTyp
- **test_render_abschnitt_with_empty_content**: Handles Textabschnitte with empty content
- **test_render_textabschnitte_xss_prevention**: Verifies that malicious HTML and script tags are sanitized from rendered content to prevent XSS attacks

### Diagram Caching Tests

#### DiagramCacheTest
- **test_compute_hash**: Generates consistent SHA256 hashes for the same input
- **test_get_cache_path**: Creates correct cache file paths based on hash and type
- **test_get_cached_diagram_hit**: Returns cached diagram when cache hit occurs
- **test_get_cached_diagram_miss**: Generates new diagram when cache miss occurs
- **test_get_cached_diagram_request_error**: Properly handles and raises request errors
- **test_clear_cache_specific_type**: Clears cache files for specific diagram types
- **test_clear_cache_all_types**: Clears all cache files when no type specified

### Management Command Tests

#### ClearDiagramCacheCommandTest
- **test_command_without_type**: Tests management command execution without specifying type
- **test_command_with_type**: Tests management command execution with specific diagram type

### Integration Tests

#### IntegrationTest
- **test_textabschnitt_inheritance**: Verifies VorgabeLangtext properly inherits Textabschnitt fields
- **test_render_vorgabe_langtext**: Tests rendering VorgabeLangtext through render_textabschnitte

---

## dokumente App Tests

The dokumente app contains 98 tests, making it the most comprehensive test suite, covering all models, views, URLs, and business logic.

### Model Tests

#### DokumententypModelTest
- **test_dokumententyp_creation**: Verifies Dokumententyp creation with correct field values
- **test_dokumententyp_str**: Tests string representation returns the `typ` field
- **test_dokumententyp_verbose_name**: Validates verbose name is set correctly

#### PersonModelTest
- **test_person_creation**: Tests Person object creation with name and optional title
- **test_person_str**: Verifies string representation includes title and name
- **test_person_verbose_name_plural**: Tests verbose name plural configuration

#### ThemaModelTest
- **test_thema_creation**: Tests Thema creation with name and optional explanation
- **test_thema_str**: Verifies string representation returns the theme name
- **test_thema_blank_erklaerung**: Confirms `erklaerung` field can be blank

#### DokumentModelTest
- **test_dokument_creation**: Tests Dokument creation with required and optional fields
- **test_dokument_str**: Verifies string representation returns the document title
- **test_dokument_optional_fields**: Tests that optional fields can be None or blank
- **test_dokument_many_to_many_relationships**: Verifies many-to-many relationships with Personen and Themen

#### VorgabeModelTest
- **test_vorgabe_creation**: Tests Vorgabe creation with all required fields
- **test_vorgabe_str**: Verifies string representation returns the Vorgabennummer
- **test_vorgabennummer**: Tests automatic generation of Vorgabennummer format
- **test_get_status_active**: Tests status determination for current active Vorgaben
- **test_get_status_expired**: Tests status determination for expired Vorgaben
- **test_get_status_future**: Tests status determination for future Vorgaben
- **test_get_status_with_custom_check_date**: Tests status with custom check date
- **test_get_status_verbose**: Tests verbose status output

#### ChangelogModelTest
- **test_changelog_creation**: Tests Changelog creation with version, date, and description
- **test_changelog_str**: Verifies string representation includes version and date

#### ChecklistenfrageModelTest
- **test_checklistenfrage_creation**: Tests Checklistenfrage creation with question and optional answer
- **test_checklistenfrage_str**: Verifies string representation truncates long questions
- **test_checklistenfrage_related_name**: Tests the reverse relationship from Vorgabe

### Text Abschnitt Tests

#### DokumentTextAbschnitteTest
- **test_einleitung_creation**: Tests Einleitung creation and inheritance from Textabschnitt
- **test_geltungsbereich_creation**: Tests Geltungsbereich creation and inheritance

#### VorgabeTextAbschnitteTest
- **test_vorgabe_kurztext_creation**: Tests VorgabeKurztext creation and inheritance
- **test_vorgabe_langtext_creation**: Tests VorgabeLangtext creation and inheritance

### Sanity Check Tests

#### VorgabeSanityCheckTest
- **test_date_ranges_intersect_no_overlap**: Tests date intersection with non-overlapping ranges
- **test_date_ranges_intersect_with_overlap**: Tests date intersection with overlapping ranges
- **test_date_ranges_intersect_identical_ranges**: Tests date intersection with identical ranges
- **test_date_ranges_intersect_with_none_end_date**: Tests intersection with open-ended ranges
- **test_date_ranges_intersect_both_none_end_dates**: Tests intersection with two open-ended ranges
- **test_check_vorgabe_conflicts_utility**: Tests the utility function for conflict detection
- **test_find_conflicts_no_conflicts**: Tests conflict detection on Vorgabe without conflicts
- **test_find_conflicts_with_conflicts**: Tests conflict detection with conflicting Vorgaben
- **test_format_conflict_report_no_conflicts**: Tests conflict report formatting with no conflicts
- **test_format_conflict_report_with_conflicts**: Tests conflict report formatting with conflicts
- **test_sanity_check_vorgaben_no_conflicts**: Tests full sanity check with no conflicts
- **test_sanity_check_vorgaben_with_conflicts**: Tests full sanity check with conflicts
- **test_sanity_check_vorgaben_multiple_conflicts**: Tests sanity check with multiple conflict groups
- **test_vorgabe_clean_no_conflicts**: Tests Vorgabe.clean() method without conflicts
- **test_vorgabe_clean_with_conflicts**: Tests Vorgabe.clean() raises ValidationError with conflicts

### Management Command Tests

#### SanityCheckManagementCommandTest
- **test_sanity_check_command_no_conflicts**: Tests management command output with no conflicts
- **test_sanity_check_command_with_conflicts**: Tests management command output with conflicts

### URL Pattern Tests

#### URLPatternsTest
- **test_standard_list_url_resolves**: Verifies standard_list URL resolves to correct view
- **test_standard_detail_url_resolves**: Verifies standard_detail URL resolves with pk parameter
- **test_standard_history_url_resolves**: Verifies standard_history URL resolves with check_date
- **test_standard_checkliste_url_resolves**: Verifies standard_checkliste URL resolves with pk

### View Tests

#### ViewsTestCase
- **test_standard_list_view**: Tests standard list view returns 200 and contains expected content
- **test_standard_detail_view**: Tests standard detail view with existing document
- **test_standard_detail_view_404**: Tests standard detail view returns 404 for non-existent document
- **test_standard_history_view**: Tests standard detail view with historical check_date parameter
- **test_standard_checkliste_view**: Tests checklist view functionality

### JSON Export Tests

#### JSONExportManagementCommandTest
- **test_export_json_command_to_file**: Tests export_json command outputs JSON to specified file
- **test_export_json_command_stdout**: Tests export_json command outputs JSON to stdout when no file specified
- **test_export_json_command_inactive_documents**: Tests export_json command filters out inactive documents
- **test_export_json_command_empty_database**: Tests export_json command handles empty database gracefully

#### StandardJSONViewTest
- **test_standard_json_view_success**: Tests standard_json view returns correct JSON for existing document
- **test_standard_json_view_not_found**: Tests standard_json view returns 404 for non-existent document
- **test_standard_json_view_json_formatting**: Tests standard_json view returns properly formatted JSON
- **test_standard_json_view_null_dates**: Tests standard_json view handles null date fields correctly
- **test_standard_json_view_empty_sections**: Tests standard_json view handles empty document sections

### Incomplete Vorgaben Tests

#### IncompleteVorgabenTest
- **test_incomplete_vorgaben_page_status**: Tests page loads successfully (200 status)
- **test_incomplete_vorgaben_staff_only**: Tests non-staff users are redirected to login
- **test_incomplete_vorgaben_page_content**: Tests page contains expected headings and structure
- **test_navigation_link**: Tests navigation includes link to incomplete Vorgaben page
- **test_no_references_list**: Tests Vorgaben without references are listed correctly
- **test_no_stichworte_list**: Tests Vorgaben without Stichworte are listed correctly
- **test_no_text_list**: Tests Vorgaben without Kurz- or Langtext are listed correctly
- **test_no_checklistenfragen_list**: Tests Vorgaben without Checklistenfragen are listed correctly
- **test_vorgabe_with_both_text_types**: Tests Vorgabe with both text types is considered complete
- **test_vorgabe_with_langtext_only**: Tests Vorgabe with only Langtext is still incomplete for text
- **test_empty_lists_message**: Tests appropriate messages when lists are empty
- **test_badge_counts**: Tests badge counts are calculated correctly
- **test_summary_section**: Tests summary section shows correct counts
- **test_vorgabe_links**: Tests Vorgaben link to correct admin pages
- **test_back_link**: Tests back link to standard list exists

---

## pages App Tests

The pages app contains 4 tests focusing on search functionality and validation.

### ViewsTestCase
- **test_search_view_get**: Tests GET request to search view returns 200 status
- **test_search_view_post_with_query**: Tests POST request with query returns results
- **test_search_view_post_empty_query**: Tests POST request with empty query shows validation error
- **test_search_view_post_no_query**: Tests POST request without query parameter shows validation error

---

## referenzen App Tests

The referenzen app contains 18 tests focusing on MPTT hierarchy functionality and model relationships.

### Model Tests

#### ReferenzModelTest
- **test_referenz_creation**: Tests Referenz creation with required fields
- **test_referenz_str**: Tests string representation returns the reference text
- **test_referenz_ordering**: Tests default ordering by `order` field
- **test_referenz_optional_fields**: Tests optional fields can be blank

#### ReferenzerklaerungModelTest
- **test_referenzerklaerung_creation**: Tests Referenzerklaerung creation with reference and explanation
- **test_referenzerklaerung_str**: Tests string representation includes reference and explanation preview
- **test_referenzerklaerung_ordering**: Tests default ordering by `order` field
- **test_referenzerklaerung_optional_explanation**: Tests explanation field can be blank

### Hierarchy Tests

#### ReferenzHierarchyTest
- **test_hierarchy_relationships**: Tests parent-child relationships in MPTT tree
- **test_get_root**: Tests getting the root node of a hierarchy
- **test_get_children**: Tests getting direct children of a node
- **test_get_descendants**: Tests getting all descendants of a node
- **test_get_ancestors**: Tests getting all ancestors of a node
- **test_get_ancestors_include_self**: Tests getting ancestors including the node itself
- **test_is_leaf_node**: Tests leaf node detection
- **test_is_root_node**: Tests root node detection
- **test_tree_ordering**: Tests tree ordering with multiple levels
- **test_move_node**: Tests moving nodes within the tree structure

---

## rollen App Tests

The rollen app contains 18 tests covering role models and their relationships with document sections.

### Model Tests

#### RolleModelTest
- **test_rolle_creation**: Tests Rolle creation with name and optional description
- **test_rolle_str**: Tests string representation returns the role name
- **test_rolle_ordering**: Tests default ordering by `order` field
- **test_rolle_unique_name**: Tests that role names must be unique
- **test_rolle_optional_beschreibung**: Tests description field can be blank

#### RollenBeschreibungModelTest
- **test_rollenbeschreibung_creation**: Tests RollenBeschreibung creation with role and section type
- **test_rollenbeschreibung_str**: Tests string representation includes role and section type
- **test_rollenbeschreibung_ordering**: Tests default ordering by `order` field
- **test_rollenbeschreibung_unique_combination**: Tests unique constraint on role and section type
- **test_rollenbeschreibung_optional_beschreibung**: Tests description field can be blank

### Relationship Tests

#### RelationshipTest
- **test_rolle_rollenbeschreibung_relationship**: Tests one-to-many relationship between Rolle and RollenBeschreibung
- **test_abschnitttyp_rollenbeschreibung_relationship**: Tests relationship between AbschnittTyp and RollenBeschreibung
- **test_cascade_delete**: Tests cascade delete behavior when role is deleted
- **test_protected_delete**: Tests protected delete behavior when section type is referenced
- **test_query_related_objects**: Tests querying related objects efficiently
- **test_string_representations**: Tests all string representations work correctly
- **test_ordering_consistency**: Tests ordering is consistent across queries

---

## stichworte App Tests

The stichworte app contains 18 tests covering keyword models and their ordering.

### Model Tests

#### StichwortModelTest
- **test_stichwort_creation**: Tests Stichwort creation with keyword text
- **test_stichwort_str**: Tests string representation returns the keyword text
- **test_stichwort_ordering**: Tests default ordering by `stichwort` field
- **test_stichwort_unique**: Tests that keywords must be unique
- **test_stichwort_case_insensitive**: Tests case-insensitive uniqueness

#### StichworterklaerungModelTest
- **test_stichworterklaerung_creation**: Tests Stichworterklaerung creation with keyword and explanation
- **test_stichworterklaerung_str**: Tests string representation includes keyword and explanation preview
- **test_stichworterklaerung_ordering**: Tests default ordering by `order` field
- **test_stichworterklaerung_optional_erklaerung**: Tests explanation field can be blank
- **test_stichworterklaerung_unique_stichwort**: Tests unique constraint on keyword

### Relationship Tests

#### RelationshipTest
- **test_stichwort_stichworterklaerung_relationship**: Tests one-to-one relationship between Stichwort and Stichworterklaerung
- **test_cascade_delete**: Tests cascade delete behavior when keyword is deleted
- **test_protected_delete**: Tests protected delete behavior when explanation is referenced
- **test_query_related_objects**: Tests querying related objects efficiently
- **test_string_representations**: Tests all string representations work correctly
- **test_ordering_consistency**: Tests ordering is consistent across queries
- **test_reverse_relationship**: Tests reverse relationship from explanation to keyword

---

## Test Statistics

- **Total Tests**: 207
- **abschnitte**: 33 tests (including XSS prevention)
- **dokumente**: 116 tests (98 in tests.py + 9 in test_json.py + 9 JSON tests in main tests.py)
- **pages**: 4 tests
- **referenzen**: 18 tests
- **rollen**: 18 tests
- **stichworte**: 18 tests

## Test Coverage Areas

1. **Model Validation**: Field validation, constraints, and relationships
2. **Business Logic**: Status determination, conflict detection, hierarchy management
3. **View Functionality**: HTTP responses, template rendering, URL resolution
4. **Utility Functions**: Text processing, caching, formatting
5. **Management Commands**: CLI interface and output handling
6. **Integration**: Cross-app functionality and data flow
7. **Security**: XSS prevention through HTML sanitization in content rendering

## Running the Tests

To run all tests:
```bash
python manage.py test
```

To run tests for a specific app:
```bash
python manage.py test app_name
```

To run with verbose output:
```bash
python manage.py test --verbosity=2
```

All tests are currently passing and provide comprehensive coverage of the application's functionality.