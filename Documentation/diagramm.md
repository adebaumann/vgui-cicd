# Diagramme in VorgabenUI

Diese Anleitung beschreibt, wie Diagramme in Textabschnitten verwendet werden können. VorgabenUI nutzt [Kroki](https://kroki.io/) zur Generierung von Diagrammen aus Textbeschreibungen.

## Übersicht

Der Abschnitttyp **"diagramm"** ermöglicht es, verschiedene Diagrammtypen direkt in Vorgaben, Einleitungen und Geltungsbereichen einzubinden. Die Diagramme werden aus Textbeschreibungen automatisch als SVG-Grafiken generiert und gecacht.

## Grundlegende Verwendung

### Format

```
[Diagrammtyp]
option: [HTML-Attribute] (optional)
[Diagramm-Code]
```

**Zeile 1:** Diagrammtyp (z.B. `plantuml`, `mermaid`, `graphviz`)
**Zeile 2 (optional):** `option:` gefolgt von HTML-Attributen für die Bildgrösse
**Zeile 3+:** Der eigentliche Diagramm-Quellcode

### Standard-Einstellungen

Wenn keine `option:`-Zeile angegeben wird, wird das Diagramm mit `width="100%"` dargestellt.

### Grösse anpassen

Um die Grösse des Diagramms anzupassen, verwenden Sie die `option:`-Zeile:

```
plantuml
option: width="50%"
@startuml
...
@enduml
```

Weitere Beispiele für Optionen:

```
option: width="800px"
option: width="60%" style="max-width: 600px;"
option: height="400px"
option: width="100%" class="img-fluid"
```

## Unterstützte Diagrammtypen

Kroki unterstützt über 20 verschiedene Diagrammtypen. Die wichtigsten sind:

| Typ | Beschreibung | Verwendung |
|-----|--------------|------------|
| `plantuml` | UML-Diagramme, Sequenzdiagramme, Aktivitätsdiagramme | Prozesse, Architekturen |
| `mermaid` | Flussdiagramme, Sequenzdiagramme, Gantt-Charts | Prozessabläufe, Zeitpläne |
| `graphviz` | Gerichtete/ungerichtete Graphen | Abhängigkeiten, Netzwerke |
| `blockdiag` | Block-Diagramme | Systemübersichten |
| `nwdiag` | Netzwerk-Diagramme | Netzwerktopologien |
| `seqdiag` | Sequenz-Diagramme | Kommunikationsabläufe |
| `c4plantuml` | C4-Modell Diagramme | Software-Architektur |
| `ditaa` | ASCII-Art zu Diagrammen | Einfache Skizzen |
| `excalidraw` | Hand-gezeichnete Diagramme | Präsentationen |
| `bpmn` | Business Process Model Notation | Geschäftsprozesse |

Vollständige Liste: https://kroki.io/

## Beispiele

### PlantUML: Sequenzdiagramm

```
plantuml
option: width="80%"
@startuml
Alice -> Bob: Authentifizierungsanfrage
Bob --> Alice: Authentifizierungsantwort

Alice -> Bob: Weitere Anfrage
Alice <-- Bob: Weitere Antwort
@enduml
```

**Verwendung:** Darstellung von Kommunikationsabläufen, API-Interaktionen

### PlantUML: Aktivitätsdiagramm

```
plantuml
@startuml
start
:Sicherheitsrichtlinie prüfen;
if (Richtlinie erfüllt?) then (ja)
  :Zugriff gewähren;
else (nein)
  :Zugriff verweigern;
  :Incident loggen;
endif
stop
@enduml
```

**Verwendung:** Prozesse, Entscheidungsabläufe, Workflows

### PlantUML: Komponentendiagramm

```
plantuml
option: width="70%"
@startuml
package "Web-Tier" {
  [Web-Server]
  [Load Balancer]
}

package "App-Tier" {
  [Application Server]
  [Cache]
}

package "Data-Tier" {
  [Datenbank]
}

[Load Balancer] --> [Web-Server]
[Web-Server] --> [Application Server]
[Application Server] --> [Cache]
[Application Server] --> [Datenbank]
@enduml
```

**Verwendung:** System-Architekturen, Komponenten-Übersicht

### Mermaid: Flussdiagramm

```
mermaid
option: width="75%"
flowchart TD
    Start[Log-Event empfangen] --> Check{Schweregrad?}
    Check -->|CRITICAL| Alert[Alert auslösen]
    Check -->|WARNING| Log[In Log-System speichern]
    Check -->|INFO| Archive[Archivieren]
    Alert --> SIEM[An SIEM weiterleiten]
    Log --> SIEM
    SIEM --> End[Fertig]
    Archive --> End
```

**Verwendung:** Prozessabläufe, Entscheidungsbäume

### Mermaid: Sequenzdiagramm

```
mermaid
sequenceDiagram
    participant Benutzer
    participant Firewall
    participant Server

    Benutzer->>Firewall: Verbindungsanfrage
    Firewall->>Firewall: Regel-Prüfung
    alt Regel erlaubt
        Firewall->>Server: Weiterleitung
        Server-->>Firewall: Antwort
        Firewall-->>Benutzer: Antwort
    else Regel blockiert
        Firewall-->>Benutzer: Verbindung abgelehnt
    end
```

**Verwendung:** Kommunikationsabläufe mit Bedingungen

### GraphViz: Abhängigkeitsgraph

```
graphviz
digraph G {
    rankdir=LR;
    node [shape=box, style=rounded];

    "R0066\nLogging" -> "R0009\nServersysteme";
    "R0066\nLogging" -> "R0126\nNetzwerksicherheit";
    "R0009\nServersysteme" -> "R0135\nInformationssicherheit";
    "R0126\nNetzwerksicherheit" -> "R0135\nInformationssicherheit";

    "R0135\nInformationssicherheit" [style="rounded,filled", fillcolor=lightblue];
}
```

**Verwendung:** Abhängigkeiten zwischen Dokumenten/Standards

### GraphViz: Netzwerk-Topologie

```
graphviz
option: width="100%"
graph G {
    layout=neato;

    Internet [shape=cloud];
    Firewall [shape=box, style=filled, fillcolor=red];
    DMZ [shape=box, style=filled, fillcolor=yellow];
    LAN [shape=box, style=filled, fillcolor=green];

    Internet -- Firewall [label="WAN"];
    Firewall -- DMZ [label="DMZ-Segment"];
    Firewall -- LAN [label="Internes Netz"];
}
```

**Verwendung:** Netzwerk-Segmentierung, Zonen-Modelle

### BlockDiag: System-Übersicht

```
blockdiag
blockdiag {
    orientation = portrait;

    Client -> "Load Balancer" -> "Web-Server 1", "Web-Server 2";
    "Web-Server 1", "Web-Server 2" -> "App-Server";
    "App-Server" -> "Datenbank Primary";
    "Datenbank Primary" -> "Datenbank Replica";

    "Load Balancer" [color = "lightblue"];
    "App-Server" [color = "lightgreen"];
    "Datenbank Primary" [color = "pink"];
}
```

**Verwendung:** Einfache System-Diagramme, Datenflüsse

### NwDiag: Netzwerk-Diagramm

```
nwdiag
nwdiag {
    network dmz {
        address = "192.168.1.0/24";

        web01 [address = "192.168.1.10"];
        web02 [address = "192.168.1.11"];
    }

    network internal {
        address = "10.0.0.0/8";

        web01 [address = "10.0.1.10"];
        web02 [address = "10.0.1.11"];
        app01 [address = "10.0.2.10"];
        db01 [address = "10.0.3.10"];
    }
}
```

**Verwendung:** Netzwerk-Topologien mit IP-Adressen

### SeqDiag: Authentifizierungsablauf

```
seqdiag
seqdiag {
    Benutzer -> System: Benutzername + Passwort;
    System -> LDAP: Authentifizierung prüfen;
    LDAP --> System: Erfolgreich;
    System -> 2FA: 2FA-Code anfordern;
    2FA --> Benutzer: Code per SMS;
    Benutzer -> System: 2FA-Code eingeben;
    System --> Benutzer: Zugriff gewährt;
}
```

**Verwendung:** Authentifizierungs- und Autorisierungsabläufe

### C4 PlantUML: System-Kontext

```
c4plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml

Person(admin, "Administrator", "BIT System-Administrator")
System(vorgaben, "VorgabenUI", "IT-Sicherheits-Vorgaben Portal")
System_Ext(ldap, "LDAP", "Authentifizierung")

Rel(admin, vorgaben, "Verwaltet Vorgaben")
Rel(vorgaben, ldap, "Authentifiziert über")
@enduml
```

**Verwendung:** Software-Architektur nach C4-Modell

## Best Practices

### 1. Diagramm-Grösse anpassen

Verwenden Sie die `option:`-Zeile, um die Grösse für bessere Lesbarkeit anzupassen:

```
plantuml
option: width="60%"
...
```

Für sehr detaillierte Diagramme:
```
plantuml
option: width="100%" style="max-width: 1200px;"
...
```

### 2. Einfachheit bevorzugen

Halten Sie Diagramme einfach und fokussiert. Zu komplexe Diagramme sind schwer zu lesen.

**Gut:**
```
mermaid
flowchart LR
    A[Start] --> B{Prüfung}
    B -->|OK| C[Weiter]
    B -->|Fehler| D[Abbruch]
```

**Zu komplex:** Vermeiden Sie Diagramme mit mehr als 15-20 Elementen.

### 3. Konsistente Stil-Wahl

Verwenden Sie für ähnliche Konzepte den gleichen Diagrammtyp:
- **Prozesse:** Mermaid Flowchart oder PlantUML Activity
- **Kommunikation:** Mermaid/PlantUML Sequence
- **Architektur:** PlantUML Component oder C4
- **Netzwerke:** NwDiag oder GraphViz

### 4. Beschriftungen auf Deutsch

Verwenden Sie deutsche Beschriftungen für bessere Verständlichkeit:

```
mermaid
flowchart TD
    Start[Anfrage empfangen] --> Prüfung{Berechtigung?}
    Prüfung -->|Ja| Zugriff[Zugriff gewähren]
    Prüfung -->|Nein| Ablehnung[Zugriff verweigern]
```

### 5. Farben sparsam einsetzen

Nutzen Sie Farben zur Hervorhebung wichtiger Elemente:

```
graphviz
digraph {
    node [shape=box];

    Kritisch [style=filled, fillcolor=red, fontcolor=white];
    Wichtig [style=filled, fillcolor=orange];
    Normal [style=filled, fillcolor=lightgreen];

    Kritisch -> Wichtig -> Normal;
}
```

### 6. Lesbarkeit testen

Nach dem Speichern prüfen, ob das Diagramm in der Webansicht gut lesbar ist. Bei Bedarf:
- Grösse anpassen (`option: width="..."`)
- Diagramm vereinfachen
- Anderen Diagrammtyp wählen

## Fehlerbehandlung

### Diagramm wird nicht angezeigt

**Mögliche Ursachen:**

1. **Syntaxfehler im Diagramm-Code**
   - Prüfen Sie die Syntax gemäss Dokumentation des Diagrammtyps
   - Testen Sie den Code auf https://kroki.io/

2. **Falscher Diagrammtyp**
   - Erste Zeile muss genau dem Kroki-Typ entsprechen
   - Beispiel: `plantuml` (nicht `PlantUML` oder `plant-uml`)

3. **Kroki-Server nicht erreichbar**
   - Bei Fehlermeldung "Error generating diagram" Server prüfen

### Fehlersuche

1. **Code auf kroki.io testen:**
   ```
   https://kroki.io/
   ```
   Geben Sie dort den Code ein und testen Sie die Generierung.

2. **Diagramm-Cache leeren:**
   ```bash
   python manage.py clear_diagram_cache
   ```

3. **Logs prüfen:**
   Fehler werden im Application-Log ausgegeben.

## Häufig verwendete Diagramm-Szenarien

### IT-Sicherheit: Bedrohungsmodell

```
mermaid
flowchart TB
    Asset[Schützenswertes Asset]
    Threat[Bedrohung]
    Vuln[Schwachstelle]
    Control[Sicherheitsmassnahme]

    Threat -->|nutzt aus| Vuln
    Vuln -->|betrifft| Asset
    Control -->|schliesst| Vuln
    Control -->|schützt| Asset
```

### Netzwerk-Segmentierung

```
nwdiag
nwdiag {
    network internet {
        address = "Internet";
        internet [shape = cloud];
    }
    network dmz {
        address = "DMZ (192.168.1.0/24)";
        fw [address = "192.168.1.1"];
        web [address = "192.168.1.10"];
    }
    network internal {
        address = "Intern (10.0.0.0/8)";
        fw [address = "10.0.0.1"];
        app [address = "10.0.1.10"];
        db [address = "10.0.2.10"];
    }

    internet -- fw;
}
```

### Patch-Management Prozess

```
plantuml
@startuml
start
:Patch-Benachrichtigung empfangen;
:Schweregrad bewerten;
if (Kritischer Patch?) then (ja)
  :Sofort in Test-Umgebung testen;
  if (Test erfolgreich?) then (ja)
    :Notfall-Change erstellen;
    :In Produktion ausrollen;
  else (nein)
    :Vendor kontaktieren;
  endif
else (nein)
  :In regulären Patch-Zyklus einplanen;
  :Testen im Change-Window;
  :Reguläres Rollout;
endif
:Dokumentation aktualisieren;
stop
@enduml
```

### Zugriffskontrolle

```
plantuml
@startuml
skinparam actorStyle awesome

actor Benutzer
actor Administrator
actor "Security Team" as ST

rectangle "VorgabenUI" {
    usecase "Vorgaben lesen" as UC1
    usecase "Vorgaben bearbeiten" as UC2
    usecase "Vorgaben publizieren" as UC3
    usecase "Sicherheitsreview" as UC4
}

Benutzer --> UC1
Administrator --> UC1
Administrator --> UC2
ST --> UC4
UC2 .> UC4 : <<extends>>
UC4 --> UC3
@enduml
```

## Weiterführende Ressourcen

- **Kroki Dokumentation:** https://kroki.io/
- **PlantUML Dokumentation:** https://plantuml.com/
- **Mermaid Dokumentation:** https://mermaid.js.org/
- **GraphViz Dokumentation:** https://graphviz.org/
- **Live-Editor zum Testen:** https://kroki.io/

## Tipps für spezifische Diagrammtypen

### PlantUML Tipps

```
@startuml
' Kommentare mit Apostroph
skinparam backgroundColor transparent
skinparam defaultFontName Arial
@enduml
```

### Mermaid Tipps

```
%%{ init: { 'theme': 'base' } }%%
flowchart LR
    %% Kommentare mit doppeltem Prozent
```

### GraphViz Tipps

```
digraph {
    // Kommentare mit doppeltem Slash
    rankdir=LR;  // Links nach Rechts
    // rankdir=TB;  // Top nach Bottom
}
```

## Support

Bei Fragen oder Problemen mit Diagrammen:
1. Code auf https://kroki.io/ testen
2. Syntax-Dokumentation des jeweiligen Diagrammtyps konsultieren
3. Diagramm-Cache leeren: `python manage.py clear_diagram_cache`
4. Bei technischen Problemen: Information Security Management BIT kontaktieren
