# DSBmobile Vertretungsplan für Home Assistant

Eine benutzerdefinierte Home-Assistant-Integration, die Vertretungspläne aus DSBmobile als **Sensoren und Kalender** bereitstellt. Klassen lassen sich einzeln auswählen; zusätzliche Kalender können nach Vertretungsart gefiltert werden.

Diese Erweiterung basiert auf [Tenner/dsbmobile](https://github.com/Tenner/dsbmobile). Sie ergänzt unter anderem die Kalenderanbindung, die Verarbeitung klassengruppierter HTML-Pläne und die Behandlung fehlgeschlagener Abrufe.

**Dokumentierter Versionsstand: 2.5.2.** Es handelt sich um ein unabhängiges Community-Projekt, nicht um eine offizielle Integration des DSBmobile-Anbieters.

## Funktionen

- Einrichtung über die Home-Assistant-Oberfläche.
- Ein Sensor und ein Gesamtkalender pro konfigurierter Klasse.
- Mehrere Klassen über eine kommagetrennte Eingabe; ohne Filter werden alle erkannten Einträge angezeigt.
- Optionale Kalender für **Betreuung, Vertretung, Raum-Vtr., Entfall und Verlegung**.
- Automatischer gemeinsamer Datenabruf alle **30 Minuten**.
- Sensorattribute mit Datum, Art, Klasse, Stunde, Fach, Lehrkraft, Raum und weiteren Planfeldern.
- Ganztägige Kalendereinträge mit Stundenangabe im Titel und Details in der Beschreibung.
- Erneuter API-Versuch mit frischer Anmeldung bei fehlgeschlagenem API-Abruf.
- Erhalt des letzten erfolgreichen Datenstands bei Abruffehlern, ergänzt um Attribute zur Aktualität.
- Deutsche und englische Texte für die Einrichtung.

## Voraussetzungen und unterstützte Pläne

Benötigt werden eine Home-Assistant-Installation mit Zugriff auf das Konfigurationsverzeichnis, gültige DSBmobile-Zugangsdaten und eine Internetverbindung zu DSBmobile sowie zu den verlinkten Planseiten.

Der Parser verarbeitet **Untis-artige HTML-Tabellen mit der CSS-Klasse `mon_list`**. Unterstützt werden sowohl Tabellen mit eigener Klassenspalte als auch nach Klassen gruppierte Tabellen mit `inline_header`-Zeilen. Die Spalten werden anhand ihrer Überschriften zugeordnet. Für das Datum wird die vorangehende Überschrift mit der Klasse `mon_title` verwendet.

Nicht jedes von Schulen verwendete Exportformat ist damit kompatibel:

- PDF- und Bildpläne werden nicht als Vertretungseinträge ausgelesen. Erkannte Nicht-HTML-Pläne erscheinen als Verweise im Sensorattribut `other_plans`.
- Als HTML werden Planadressen erkannt, deren URL-Pfad auf `.htm` oder `.html` endet.
- Seiten, die den eigentlichen Plan nur per `iframe` einbetten, werden nicht automatisch weiterverfolgt.
- Abweichende Tabellenstrukturen oder Spaltenbezeichnungen können eine Anpassung des Parsers erfordern.

Eine verbindliche Home-Assistant-Mindestversion ist für diesen Stand nicht festgelegt. Die Integration verwendet aktuelle Config-Entry-, Coordinator- und Kalender-Schnittstellen; die Kompatibilität mit älteren Installationen ist nicht zugesichert.

## Installation

### Manuell installieren

1. Die Projektdateien herunterladen und entpacken.
2. Den Ordner `custom_components/dsbmobile` in das Home-Assistant-Konfigurationsverzeichnis kopieren.
3. Prüfen, dass beispielsweise diese Datei direkt vorhanden ist:
   `/config/custom_components/dsbmobile/manifest.json`.
4. Home Assistant vollständig neu starten.
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen** öffnen.
6. Nach **DSBmobile Vertretungsplan** suchen und die Integration einrichten.

`/config` bezeichnet das übliche Konfigurationsverzeichnis; bei anderen Installationsarten kann der Pfad abweichen. Es darf kein zusätzlicher verschachtelter Ordner wie `custom_components/dsbmobile/custom_components/dsbmobile` entstehen.

Eine YAML-Konfiguration der Integration ist nicht erforderlich. Die Python-Abhängigkeit `beautifulsoup4` ist im Manifest hinterlegt.

### Vorhandene Installation aktualisieren

1. Den bisherigen Ordner `custom_components/dsbmobile` sichern.
2. Die darin enthaltenen Integrationsdateien durch die neue Version ersetzen.
3. Home Assistant vollständig neu starten.

Die vorhandene Integration muss dafür **nicht gelöscht oder neu eingerichtet** werden. Bestehende eindeutige IDs der Sensoren und Gesamtkalender bleiben bei unverändertem Konfigurationseintrag und Klassenfilter erhalten.

Ein Update aus einem anderen Repository, beispielsweise über eine bestehende HACS-Verknüpfung zum Ursprungsprojekt, kann diese Erweiterungen überschreiben. Diese Anleitung beschreibt die manuelle Installation; eine HACS-Installation dieses Forks ist hier nicht als geprüft dokumentiert.

## Einrichtung

| Feld | Bedeutung | Beispiel |
| --- | --- | --- |
| Benutzername | DSBmobile-Benutzername bzw. Kennung | Zugang der Schule |
| Passwort | Zugehöriges DSBmobile-Passwort | Persönlich eingeben |
| Klassenfilter | Eine oder mehrere Klassen, durch Kommas getrennt | `08b, 09a` |

Ein leerer Klassenfilter liefert alle erkannten Einträge. Pro Benutzername lässt sich ein Konfigurationseintrag anlegen; mehrere Klassen werden innerhalb dieses Eintrags konfiguriert.

Der Klassenvergleich ignoriert Groß-/Kleinschreibung und führende Nullen: `8b` passt zu `08B`. Enthält eine Klassenangabe mehrere durch Komma, Semikolon oder Leerzeichen getrennte Klassen, werden diese einzeln verglichen. Ein Schrägstrich bleibt Bestandteil des Namens, beispielsweise bei `Q1/2`.

### Klassen und zusätzliche Kalender ändern

Unter **Einstellungen → Geräte & Dienste → DSBmobile → Konfigurieren** lassen sich der Klassenfilter und die **zusätzlichen Kalender nach Art** ändern.

| Auswahl | Berücksichtigter Wert im Feld `art` |
| --- | --- |
| Betreuung | `Betreuung` |
| Vertretung | `Vertretung` |
| Raum-Vtr. | `Raum-Vtr.` |
| Entfall | `Entfall` |
| Verlegung | `Verlegung` |

Standardmäßig sind keine zusätzlichen Kalender ausgewählt. Jede ausgewählte Art erzeugt pro Klasse einen weiteren Kalender – auch wenn aktuell keine passenden Einträge vorliegen. Ohne Klassenfilter gelten diese Kalender für alle Klassen.

Der Artfilter vergleicht den vollständigen Wert und ignoriert Groß-/Kleinschreibung sowie überflüssige Leerzeichen. Andere Bezeichnungen und Einträge ohne Art bleiben im Gesamtkalender sichtbar.

Beim Entfernen einer Klasse werden deren Sensor und Kalender aus dem Entitätsregister entfernt. Beim Abwählen einer Art werden die entsprechenden Zusatzkalender entfernt. Darauf verweisende Karten und Automationen müssen gegebenenfalls angepasst werden.

## Sensoren

Ein Sensor heißt beispielsweise `Vertretungsplan 08b`. Seine tatsächliche Entity-ID kann etwa `sensor.vertretungsplan_08b` lauten. Bitte die ID unter **Einstellungen → Geräte & Dienste → Entitäten** prüfen; Umbenennungen und bereits vorhandene Entitäten können sie verändern.

Der Sensorzustand ist die **Anzahl der erkannten Einträge für den Klassenfilter im zuletzt abgerufenen Plan**. Er ist nicht automatisch auf den heutigen Tag beschränkt.

| Attribut | Inhalt |
| --- | --- |
| `class_filter` | Konfigurierter Klassenfilter; leer für alle Klassen |
| `count` | Anzahl der Einträge |
| `entries` | Liste der Vertretungseinträge |
| `other_plans` | Nicht als HTML verarbeitete Pläne mit `title`, `date` und `url` |
| `data_stale` | `true`, wenn der letzte Abruf fehlgeschlagen ist und alte Daten angezeigt werden |
| `last_successful_update` | Zeitpunkt des letzten erfolgreichen Abrufs als ISO-Zeitstempel in UTC |
| `last_error` | Letzte Abruffehlermeldung oder `null` |

Jeder Eintrag in `entries` enthält diese Felder:

| Feld | Bedeutung |
| --- | --- |
| `day` | Datums-/Tagesüberschrift des Plans |
| `art` | Vertretungsart |
| `class` | Klasse bzw. Klassenangabe |
| `lesson` | Unterrichtsstunde oder Stundenbereich |
| `subject` | Fach |
| `teacher` | Lehrkraft, sofern eine passende Spalte vorhanden ist |
| `room` | Raum |
| `vertr_von` | Inhalt der Planspalte „Vertr. von“ |
| `nach` | Inhalt der Planspalte „Nach“ bzw. „Le. nach“ |
| `text` | Hinweis- oder Vertretungstext |

Nicht vorhandene Werte bleiben leer. In HTML durchgestrichene Werte werden in Sensorattributen als `~~bisheriger Wert~~` erhalten.

## Kalender

Pro Klasse wird ein nur lesbarer Gesamtkalender erzeugt. Zusätzliche Artkalender enthalten jeweils eine gefilterte Teilmenge desselben Plans.

- Eine erkannte Vertretungszeile ergibt einen **ganztägigen Termin** am angegebenen Datum.
- Der Titel enthält Klasse, Art, Stunde und gegebenenfalls Fach.
- Die Beschreibung enthält die verfügbaren Planfelder; der Raum wird außerdem als Ort gesetzt.
- Durchgestrichene Werte erscheinen als `(bisher: …)`.
- Identische Kalendereinträge werden innerhalb eines Kalenders zusammengefasst.
- Ein Datum muss als `TT.MM.JJJJ` erkennbar und gültig sein. Andernfalls wird für die betreffende Zeile kein Kalendertermin erzeugt.

Es werden **keine Unterrichtszeiten ergänzt**. Der Termin endet exklusiv am Folgetag. Startbasierte Kalenderautomationen beziehen sich daher auf Mitternacht, nicht auf den Unterrichtsbeginn. Änderungen, die erst später abgerufen werden, lösen einen bereits vergangenen Startzeitpunkt nicht rückwirkend aus.

Die Kalender bilden den zuletzt abgerufenen veröffentlichten Plan ab. Nicht mehr enthaltene Einträge verschwinden nach einem erfolgreichen Abruf. Es gibt keine dauerhafte Historie und keine eingebaute Synchronisation mit Google Kalender oder Outlook.

Wer Gesamtkalender und Artkalender gleichzeitig anzeigt, sieht die entsprechenden Termine mehrfach. Für eine nach Arten getrennte Darstellung nur die gewünschten Artkalender auswählen.

### Kalenderkarte im Dashboard

Entity-ID an die eigene Installation anpassen:

```yaml
type: calendar
initial_view: listWeek
entities:
  - calendar.vertretungsplan_08b
```

### Einträge in einer Markdown-Karte anzeigen

Dieses Beispiel zeigt alle Einträge des Sensors, einschließlich ihres Datums, und kennzeichnet zwischengespeicherte Daten:

```yaml
type: markdown
title: Vertretungsplan
content: >-
  {% set entity = 'sensor.vertretungsplan_08b' %}
  {% if states(entity) in ['unknown', 'unavailable'] %}
  Der Vertretungsplan ist derzeit nicht verfügbar.
  {% else %}
  {% if state_attr(entity, 'data_stale') %}
  **Hinweis: Der letzte Abruf ist fehlgeschlagen. Angezeigt wird der letzte bekannte Stand.**

  {% endif %}
  {% for e in state_attr(entity, 'entries') or [] %}
  **{{ e.day }} · {{ e.lesson }}. Std. · {{ e.art }}**

  {{ e.subject }}{% if e.room %} · Raum {{ e.room }}{% endif %}

  {{ e.text }}

  {% else %}
  Keine Einträge im zuletzt erkannten Plan.
  {% endfor %}
  {% endif %}
```

## Aktualisierung und Abruffehler

Sensoren und Kalender verwenden einen gemeinsamen Coordinator. Zusätzliche Kalender verursachen keine eigenen regelmäßigen Planabrufe. Das Intervall beträgt **1.800 Sekunden / 30 Minuten** und ist in `const.py` als `DEFAULT_SCAN_INTERVAL` definiert. Eine Option zur Änderung des Intervalls in der Oberfläche ist nicht implementiert.

### Manuell aktualisieren

Unter **Entwicklerwerkzeuge → Aktionen** kann eine vorhandene Sensor- oder Kalenderentität aktualisiert werden:

```yaml
action: homeassistant.update_entity
target:
  entity_id: sensor.vertretungsplan_08b
```

Dadurch wird der gemeinsame Datenabruf angefordert.

### Verhalten bei Fehlern

Bei einem fehlgeschlagenen Web-API-Aufruf wird die Sitzung verworfen und einmal mit erneuter Anmeldung wiederholt. Schlägt der Abruf weiterhin fehl oder kann eine HTML-Planseite wegen eines HTTP-/Netzwerkfehlers nicht geladen werden, bleibt ein bereits vorhandener vollständiger Datenstand im Arbeitsspeicher erhalten.

Sensoren und Kalender erhalten dann `data_stale: true`. `last_successful_update` bleibt auf dem Zeitpunkt des letzten erfolgreichen Abrufs; `last_error` beschreibt den Fehler. Nach einem erfolgreichen Abruf werden diese Fehlerkennzeichen zurückgesetzt.

**Der Zwischenspeicher überlebt keinen Neustart.** Scheitert bereits der erste Abruf, steht kein alter Datenstand zur Verfügung.

Ein erfolgreich geladener leerer Plan ersetzt den bisherigen Datenstand. Auch ein technisch erfolgreicher Abruf mit einem nicht unterstützten HTML-Layout kann keine Einträge ergeben: Der Parser unterscheidet solche Fälle nicht zuverlässig von einem leeren Plan. `data_stale: false` bestätigt deshalb den erfolgreichen Abruf, nicht die Vollständigkeit der inhaltlichen Erkennung.

## Fehlerbehebung

| Problem | Prüfung und Vorgehen |
| --- | --- |
| Integration erscheint nicht | Ordnerstruktur und `manifest.json` prüfen; Home Assistant vollständig neu starten; Protokolle auf Ladefehler prüfen. |
| `Login page missing form fields` | Die empfangene Loginseite enthält nicht die erwarteten Formularfelder. Zugang im DSBmobile-Webportal prüfen und Protokolle auswerten. Die Meldung allein beweist kein falsches Passwort. |
| `Web API returned no data, session may have expired` | Die Integration versucht automatisch eine erneute Anmeldung. Bei wiederholtem Fehler Verbindung, Zugang und Dienstverfügbarkeit prüfen; Aktualitätsattribute beachten. |
| Sensor zeigt `0`, obwohl Einträge erwartet werden | Klassenfilter, tatsächliche Klassenbezeichnung und unterstütztes HTML-Format prüfen. Ein PDF- oder Bildplan wird nicht als Eintragsliste ausgewertet. |
| Sensor enthält Einträge, Kalender bleibt leer | Prüfen, ob `day` ein gültiges Datum mit vierstelliger Jahreszahl enthält und der Kalender im betrachteten Zeitraum eingeblendet ist. |
| Kalenderentitäten fehlen | Prüfen, ob insbesondere `calendar.py`, `coordinator.py` und die aktuelle `__init__.py` installiert sind. Vollständigen Neustart durchführen; in der Entitätsliste Filter entfernen und deaktivierte Entitäten prüfen. |
| Ein Artkalender bleibt leer | Den tatsächlichen Wert von `entries[].art` mit der ausgewählten Art vergleichen. Ein leerer Kalender ist bei fehlenden passenden Einträgen normal. |
| Alte Einträge bleiben sichtbar | `data_stale`, `last_successful_update` und `last_error` prüfen. Bei Abruffehlern wird bewusst der letzte bekannte Stand weiterverwendet. |
| Termine erscheinen doppelt | Gesamtkalender und die entsprechenden Artkalender nicht gleichzeitig einblenden. |

### Debug-Protokollierung

Mit einem vorhandenen `logger`-Abschnitt in `configuration.yaml` zusammenführen und Home Assistant neu starten:

```yaml
logger:
  default: warning
  logs:
    custom_components.dsbmobile: debug
```

Anschließend unter **Einstellungen → System → Protokolle** nach `dsbmobile` suchen. Nach der Diagnose die zusätzliche Debug-Protokollierung wieder entfernen.

Für einen Fehlerbericht sind die Home-Assistant-Core-Version, Integrationsversion, erwartetes und tatsächliches Verhalten sowie ein bereinigter Fehlerauszug hilfreich. Bei Parserproblemen möglichst einen anonymisierten HTML-Ausschnitt mit Tabellenüberschrift und betroffener Zeile beifügen.

**Keine Passwörter, Sitzungsdaten oder unbereinigten Schulpläne in öffentliche Issues hochladen.** Debug-Protokolle können Planadressen und schulbezogene Angaben enthalten. Zugangsdaten werden als Teil des Home-Assistant-Konfigurationseintrags gespeichert; das Konfigurationsverzeichnis und dessen Sicherungen gehören nicht in ein öffentliches Repository.

## Projektstruktur

| Datei | Aufgabe |
| --- | --- |
| `custom_components/dsbmobile/__init__.py` | Einrichtung, Sitzung und Laden der Plattformen |
| `custom_components/dsbmobile/config_flow.py` | Anmeldung, Klassenfilter und Kalenderoptionen |
| `custom_components/dsbmobile/const.py` | Domain, Abrufintervall und Kalenderarten |
| `custom_components/dsbmobile/dsb_api.py` | Webanmeldung, API-Abruf und HTML-Parser |
| `custom_components/dsbmobile/coordinator.py` | Gemeinsame Aktualisierung und Fehler-/Aktualitätsstatus |
| `custom_components/dsbmobile/sensor.py` | Anzahl und Attribute der Vertretungseinträge |
| `custom_components/dsbmobile/calendar.py` | Gesamtkalender und Kalender nach Art |
| `custom_components/dsbmobile/manifest.json` | Version, Abhängigkeiten und Integrationsmetadaten |
| `custom_components/dsbmobile/strings.json` | Oberflächentexte |
| `custom_components/dsbmobile/translations/` | Übersetzungen für Deutsch und Englisch |
| `LICENSE` | Mitgelieferte MIT-Lizenz |

## Qualitätssicherung und Beiträge

Laut den mitgelieferten Entwicklungsnotizen wurden Parser-, Filter-, Kalender- und Fehlerbehandlungsfunktionen lokal mit Beispieldaten bzw. simulierten Home-Assistant-Abhängigkeiten geprüft. Das ist kein vollständiger Integrationstest in einer laufenden Home-Assistant-Installation. Das dokumentierte Paket enthält keine automatisierte Testsuite und legt keine verbindliche Kompatibilitätsmatrix fest.

Bei Änderungen sollten insbesondere Klassenfilter, unterschiedliche Tabellenlayouts, Datumsverarbeitung, Kalenderarten und das Verhalten bei Abruffehlern geprüft werden. Anonymisierte Beispiele zusätzlicher Schulformate helfen bei der Weiterentwicklung des Parsers.

## Herkunft und Lizenz

Grundlage ist das Projekt [Tenner/dsbmobile](https://github.com/Tenner/dsbmobile). Die mitgelieferte `LICENSE` enthält die **MIT-Lizenz** mit dem Copyright-Hinweis `Copyright (c) 2026 Tenner`. Diese Lizenzdatei und der bestehende Urheberrechtshinweis gehören zum veröffentlichten Projekt.

Die hier dokumentierten Erweiterungen umfassen insbesondere die Kalenderplattform, zusätzliche Kalender nach Art, Parser-/Klassenfilteranpassungen und die Weiterverwendung des letzten erfolgreichen Datenstands bei Abruffehlern.
