# Project Context

## Purpose
This is a Django-based document management system for regulatory documents (Dokumente) and their provisions (Vorgaben). It manages validity periods, conflicts between overlapping provisions, references, keywords, and roles. The system supports importing documents, checking for compliance, and maintaining changelogs.

## Tech Stack
- Python 3.x
- Django 5.2.5
- SQLite (development), PostgreSQL (production)
- Django MPTT for tree structures
- Django Nested Admin for inline editing
- Kubernetes for deployment
- ArgoCD for continuous deployment
- Traefik for ingress
- Gunicorn for WSGI server

## Project Conventions

### Code Style
- Language: German for user-facing strings and model names, English for code comments and internal naming
- Imports: Standard library first, then Django, then third-party, then local apps
- Model naming: German nouns (Dokument, Vorgabe, Person)
- Field naming: German for field names, English Django conventions
- Class naming: PascalCase for models, snake_case for functions/variables
- All models have __str__ methods returning meaningful German strings
- Use verbose_name and verbose_name_plural in Meta classes (German)

### Architecture Patterns
- Django apps: abschnitte, dokumente, referenzen, rollen, stichworte, pages
- MPTT for hierarchical text sections
- Foreign keys with on_delete=models.PROTECT for important relationships
- Many-to-many with descriptive related_name
- Proxy models for different views (e.g., VorgabenTable)
- Management commands for data operations

### Testing Strategy
- Django test framework
- Test class names in English, methods in English
- Comprehensive model tests
- Test both success and error cases
- Run with `python manage.py test`

### Git Workflow
- Standard Git workflow
- Commits in English
- Use Gitea workflows for CI/CD

## Domain Context
The system manages regulatory documents with numbered provisions that have validity dates. Provisions can conflict if they have overlapping date ranges for the same document, theme, and number. The system includes sanity checks for conflicts, diagram caching for visualization, and JSON export functionality.

## Important Constraints
- German language for all user interfaces and data
- Strict validation of date ranges to prevent overlapping provisions
- Documents have types, authors, reviewers, and validity periods
- Provisions linked to themes, references, keywords, and relevant roles
- Active/inactive status for documents

## External Dependencies
- Django ecosystem: MPTT, nested-admin, revproxy
- Kubernetes cluster for deployment
- ArgoCD for GitOps
- Traefik for load balancing
- External diagram services (diagramm_proxy)
