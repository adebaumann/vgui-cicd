# Dokumenten-Import: Anleitung

Diese Anleitung beschreibt, wie Dokumente und Vorgaben mittels des `import-document` Management Commands in die VorgabenUI importiert werden können.

## Übersicht

Der `import-document` Command ermöglicht es, strukturierte Textdateien zu importieren, die Dokumente mit Einleitung, Geltungsbereich und Vorgaben enthalten. Das Format ist speziell für die einfache Erfassung und Pflege von IT-Sicherheitsstandards konzipiert.

## Grundlegende Verwendung

### Minimaler Aufruf

```bash
python manage.py import-document <dateipfad> \
  --nummer <dokumentnummer> \
  --name "<dokumentname>" \
  --dokumententyp "<typ>"
```

### Beispiel

```bash
python manage.py import-document Documentation/import\ formats/r009.txt \
  --nummer "R0009" \
  --name "Serversysteme" \
  --dokumententyp "Standard IT-Sicherheit"
```

## Parameter

### Pflichtparameter

| Parameter | Beschreibung | Beispiel |
|-----------|--------------|----------|
| `file_path` | Pfad zur Importdatei | `Documentation/import formats/r009.txt` |
| `--nummer` | Dokumentnummer (eindeutig) | `R0009`, `R0066` |
| `--name` | Dokumentname | `"Logging"`, `"Serversysteme"` |
| `--dokumententyp` | Dokumententyp (muss bereits existieren) | `"Standard IT-Sicherheit"` |

### Optionale Parameter

| Parameter | Beschreibung | Verwendung |
|-----------|--------------|------------|
| `--gueltigkeit_von` | Startdatum der Gültigkeit | `--gueltigkeit_von 2024-01-01` |
| `--gueltigkeit_bis` | Enddatum der Gültigkeit | `--gueltigkeit_bis 2025-12-31` |
| `--dry-run` | Testlauf ohne Datenbankänderungen | `--dry-run` |
| `--verbose` | Ausführliche Ausgabe (mit `--dry-run`) | `--dry-run --verbose` |
| `--purge` | Löscht bestehende Einleitung/Geltungsbereich/Vorgaben vor Import | `--purge` |

### Dry-Run Modus

Der Dry-Run Modus ist besonders nützlich zum Testen:

```bash
python manage.py import-document r009.txt \
  --nummer "R0009" \
  --name "Serversysteme" \
  --dokumententyp "Standard IT-Sicherheit" \
  --dry-run --verbose
```

Dies zeigt an, was importiert würde, ohne die Datenbank zu ändern.

### Purge Modus

**Achtung:** Der Purge-Modus löscht alle bestehenden Vorgaben des Dokuments!

```bash
python manage.py import-document r009.txt \
  --nummer "R0009" \
  --name "Serversysteme" \
  --dokumententyp "Standard IT-Sicherheit" \
  --purge
```

Nutzen Sie `--dry-run --purge` zuerst, um zu sehen, was gelöscht würde.

## Dateiformat

### Grundstruktur

Die Importdatei ist eine Textdatei (UTF-8 kodiert) mit speziellen Trennzeichen `>>>` am Zeilenanfang.

### Aufbau

```
>>>Einleitung
>>>text
[Einleitungstext]

>>>Geltungsbereich
>>>text
[Geltungsbereichstext]

>>>Vorgabe [Thema]
>>>Nummer [nummer]
>>>Titel
[Titel der Vorgabe]
>>>Kurztext
>>>Text
[Kurztext-Inhalt]
>>>Langtext
>>>Text
[Langtext-Inhalt]
>>>Stichworte
[Stichwort1, Stichwort2, ...]
>>>Checkliste
[Frage 1]
[Frage 2]
```

### Abschnitt-Trenner

Jeder Abschnitt beginnt mit `>>>` gefolgt vom Abschnittstyp:

- `>>>Einleitung` - Startet den Einleitungsbereich
- `>>>Geltungsbereich` - Startet den Geltungsbereichsbereich
- `>>>Vorgabe [Thema]` - Startet eine neue Vorgabe mit angegebenem Thema

### Abschnitttypen für Textinhalte

Nach `>>>Einleitung`, `>>>Geltungsbereich`, `>>>Kurztext` oder `>>>Langtext` folgt ein Abschnitttyp:

| Typ | Verwendung | Beispiel |
|-----|------------|----------|
| `>>>text` oder `>>>Text` | Normaler Fliesstext | `>>>text` |
| `>>>liste geordnet` oder `>>>Liste geordnet` | Nummerierte Liste | `>>>Liste geordnet` |
| `>>>liste ungeordnet` oder `>>>Liste ungeordnet` | Aufzählungsliste | `>>>liste ungeordnet` |

**Hinweis:** Gross-/Kleinschreibung und Bindestriche (`liste-ungeordnet`) werden normalisiert.

## Beispiele

### Beispiel 1: Einfaches Dokument mit einer Vorgabe

```
>>>Einleitung
>>>text
Dieser Standard definiert Anforderungen für XYZ.

>>>Geltungsbereich
>>>text
Dieser Standard gilt für alle Systeme im BIT.

>>>Vorgabe Technik
>>>Nummer 1
>>>Titel
Verschlüsselung verwenden
>>>Kurztext
>>>Text
Alle Verbindungen müssen verschlüsselt sein.
>>>Langtext
>>>Text
Die Verschlüsselung muss mindestens TLS 1.2 verwenden.
Es sind folgende Cipher Suites erlaubt:
>>>Liste ungeordnet
TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
>>>Stichworte
Verschlüsselung, TLS, Kryptographie
>>>Checkliste
TLS 1.2 oder höher ist konfiguriert
Schwache Cipher Suites sind deaktiviert
```

### Beispiel 2: Mehrere Vorgaben mit gleichem Thema

```
>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel
CMDB-Erfassung
>>>Kurztext
>>>Text
Alle Assets müssen in der CMDB erfasst sein.
>>>Langtext
>>>Text
Jedes Asset muss dokumentiert werden...

>>>Vorgabe Organisation
>>>Nummer 2
>>>Titel
Verantwortlichkeiten
>>>Kurztext
>>>Text
Verantwortlichkeiten müssen definiert sein.
>>>Langtext
>>>Text
Für jedes System muss ein Verantwortlicher...
```

### Beispiel 3: Verschiedene Themen

```
>>>Vorgabe Technik
>>>Nummer 1
>>>Titel
Firewall-Konfiguration
>>>Kurztext
>>>Text
Lokale Firewall muss aktiviert sein.
>>>Langtext
>>>Text
Details zur Firewall-Konfiguration...

>>>Vorgabe Organisation
>>>Nummer 1
>>>Titel
Dokumentation
>>>Kurztext
>>>Text
Konfiguration muss dokumentiert sein.
>>>Langtext
>>>Text
Die Firewall-Regeln müssen...

>>>Vorgabe Informationen
>>>Nummer 1
>>>Titel
Datenklassifizierung
>>>Kurztext
>>>Text
Daten müssen klassifiziert werden.
>>>Langtext
>>>Text
Klassifizierungsstufen sind...
```

### Beispiel 4: Mehrere Textabschnitte

```
>>>Vorgabe Technik
>>>Nummer 1
>>>Titel
Komplexe Anforderung
>>>Kurztext
>>>Text
Erste Zusammenfassung.
>>>Langtext
>>>Text
Erster Absatz mit Details.
>>>Text
Zweiter Absatz mit weiteren Informationen.
>>>Liste ungeordnet
Punkt 1
Punkt 2
Punkt 3
>>>Text
Abschliessender Text nach der Liste.
```

## Vorgaben-Struktur

### Vorgabe-Header

```
>>>Vorgabe [Thema]
```

Das Thema muss in der Datenbank bereits als `Thema`-Objekt existieren. Übliche Themen:
- Organisation
- Technik
- Informationen
- Systeme
- Anwendungen
- Zonen

### Vorgabe-Felder

#### Nummer (Pflicht)

```
>>>Nummer 1
```

oder inline:

```
>>>Nummer: 1
```

Die Nummer wird als Integer gespeichert. Sie ist eindeutig innerhalb eines Dokuments und Themas.

#### Titel (Pflicht)

```
>>>Titel
Titel der Vorgabe
```

oder inline:

```
>>>Titel: Titel der Vorgabe
```

#### Kurztext (Optional)

```
>>>Kurztext
>>>Text
Kurze Zusammenfassung der Vorgabe.
```

#### Langtext (Optional)

```
>>>Langtext
>>>Text
Ausführliche Beschreibung der Vorgabe.
>>>Liste ungeordnet
Punkt 1
Punkt 2
```

#### Stichworte (Optional)

Komma-getrennte Liste:

```
>>>Stichworte
Firewall, Netzwerk, Sicherheit
```

oder als Block:

```
>>>Stichworte
>>>Text
Firewall, Netzwerk, Sicherheit
```

**Hinweis:** Stichworte werden automatisch in der Datenbank angelegt, falls sie noch nicht existieren.

#### Checkliste (Optional)

```
>>>Checkliste
Ist die Firewall aktiviert?
Sind alle unnötigen Ports geschlossen?
Wurde die Konfiguration dokumentiert?
```

Jede Zeile wird als separate Checklistenfrage gespeichert.

## Tipps und Best Practices

### 1. Dry-Run vor Import

Führen Sie immer zuerst einen Dry-Run durch:

```bash
python manage.py import-document datei.txt \
  --nummer "R0XXX" \
  --name "Test" \
  --dokumententyp "Standard IT-Sicherheit" \
  --dry-run --verbose
```

### 2. Themen vorab erstellen

Stellen Sie sicher, dass alle verwendeten Themen in der Datenbank existieren:

```python
python manage.py shell
>>> from dokumente.models import Thema
>>> Thema.objects.get_or_create(name="Organisation")
>>> Thema.objects.get_or_create(name="Technik")
>>> Thema.objects.get_or_create(name="Informationen")
```

### 3. Dokumententyp vorab erstellen

Der Dokumententyp muss existieren:

```python
python manage.py shell
>>> from dokumente.models import Dokumententyp
>>> Dokumententyp.objects.get_or_create(
...     name="Standard IT-Sicherheit",
...     defaults={"verantwortliche_ve": "SR-SUR-SEC"}
... )
```

### 4. Abschnitttypen prüfen

Folgende Abschnitttypen müssen in der Datenbank existieren:
- `text`
- `liste geordnet`
- `liste ungeordnet`
- `code`
- `diagramm`

Prüfen Sie diese in der Autorenumgebung unter "Abschnitttypen".

### 5. UTF-8 Kodierung

Stellen Sie sicher, dass Ihre Importdatei UTF-8 kodiert ist, besonders bei Umlauten (ä, ö, ü) und Sonderzeichen.

### 6. Versionierung mit Purge

Beim Re-Import mit `--purge`:

```bash
# 1. Backup erstellen
python manage.py dumpdata dokumente.Dokument dokumente.Vorgabe > backup.json

# 2. Import mit Purge
python manage.py import-document datei.txt \
  --nummer "R0009" \
  --name "Serversysteme" \
  --dokumententyp "Standard IT-Sicherheit" \
  --purge
```

### 7. Mehrzeilige Inhalte

Mehrzeiliger Text wird automatisch erkannt:

```
>>>Langtext
>>>Text
Dies ist Zeile 1.
Dies ist Zeile 2.

Dies ist ein neuer Absatz.
```

### 8. Leerzeilen

Leerzeilen innerhalb eines Abschnitts werden beibehalten. Eine Leerzeile nach einem `>>>`-Trenner wird ignoriert.

## Fehlerbehebung

### "Dokumententyp does not exist"

Der angegebene Dokumententyp existiert nicht in der Datenbank.

**Lösung:** Erstellen Sie den Dokumententyp in der Autorenumgebung oder per Shell.

### "Thema not found, skipping Vorgabe"

Das in der Vorgabe verwendete Thema existiert nicht.

**Lösung:** Erstellen Sie das Thema in der Autorenumgebung oder passen Sie die Importdatei an.

### "AbschnittTyp not found"

Ein verwendeter Abschnitttyp existiert nicht.

**Lösung:**
- Prüfen Sie die Schreibweise (Gross-/Kleinschreibung wird normalisiert)
- Erstellen Sie den Abschnitttyp in der Autorenumgebung
- Standardtypen: `text`, `liste geordnet`, `liste ungeordnet`

### Vorgabe wird nicht importiert

Prüfen Sie:
- Ist `>>>Nummer` gesetzt?
- Ist `>>>Titel` gesetzt?
- Existiert das Thema?

Verwenden Sie `--dry-run --verbose` für detaillierte Informationen.

## Weitere Informationen

### Beispieldateien

Beispieldateien finden Sie in:
- `Documentation/import formats/r009.txt`
- `Documentation/import formats/r0126.txt`

### Export-Format

Der Export verwendet JSON statt Textformat. Für JSON-Export siehe:

```bash
python manage.py export_json --output dokumente.json
```

Oder über die Web-Oberfläche: `/dokumente/R0066/?format=json`

### Verwandte Commands

- `export_json` - Exportiert Dokumente als JSON
- `sanity_check_vorgaben` - Prüft Vorgaben auf Konflikte
- `clear_diagram_cache` - Löscht Diagramm-Cache

## Kontakt

Bei Fragen oder Problemen wenden Sie sich an das Information Security Management BIT.
