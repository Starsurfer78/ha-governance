HA Governance – Deterministic Policy Layer

Version 0.1

🧠 Zweck

HA Governance ist die deterministische Sicherheits- und Validierungsschicht des Hauses.

Sie ist:

Kein Orchestrator

Kein Intent-System

Kein Planner

Kein Komfort-Manager

Sie ist:

Eine globale Zustands- und Sicherheits-Instanz.

🏗 Architekturrolle

System-Schichtung:

Automation Layer      → Trigger & Ablauf
Jarvis Orchestrator   → Entscheidung & Planung (optional)
HA Governance         → Globale Zustandsregeln
Home Assistant Core   → State Machine


Governance läuft parallel zu Automationen und überschreibt bei Bedarf Aktionen.

🔐 Designprinzipien

Deterministisch – keine probabilistische Logik

Keine Trigger – nur Zustandsregeln

Keine Ablaufketten

Keine Komfort-Optimierung

Explizite Entity-Zuordnung

Prioritätsbasiertes Enforcement

📊 Prioritätssystem
Priority	Kategorie
100	Kritische Sicherheit
90–95	Schutzmechanismen
70–85	Energie
40–65	Komfort-Grenzen
<40	Nicht verwenden

Regel:

Safety > Energy > Comfort

🏠 Raum-basierte Policies

Jede Policy muss einem klaren Raum zugeordnet sein.

Beispiel:

- name: heating_window_protection_wohnzimmer


Nicht erlaubt:

Wildcards wie climate.*

Globale Fenster-Regeln

Implizite Raumlogik

🪟 Fenster-Aggregation

Bei mehreren Fenstern pro Raum wird ein Template-Binary-Sensor verwendet:

binary_sensor.window_<raum>_any_open


Policies referenzieren nur diesen Sammelsensor.

Warum:

Eindeutige Zuordnung

Debugbarkeit

Skalierbarkeit

Orchestrator-Kompatibilität

🔥 Heizungs-Schutzregel (Beispiel)
- name: heating_window_protection_wohnzimmer
  priority: 95
  when:
    binary_sensor.window_wohnzimmer_any_open: "on"
    climate.wohnzimmer: "heat"
  enforce:
    service: climate.turn_off
    target: climate.wohnzimmer


Diese Regel darf nicht in Automationen dupliziert werden.

⚡ Energie-Regeln

Energie-Policies dürfen:

Standby vermeiden

Extreme Verbrauchssituationen korrigieren

Idle-Zustände abschalten

Energie-Policies dürfen nicht:

Komfort aktiv optimieren

Zeitpläne implementieren

Benutzerintention interpretieren

💡 Komfort-Grenzen

Governance darf Komfort begrenzen, aber nicht gestalten.

Erlaubt:

Maximaltemperatur

Nacht-Helligkeitsgrenze

Mindesttemperatur

Nicht erlaubt:

Szenen aktivieren

Adaptive Lighting steuern (außer Schutzfall)

Bewegungslogik implementieren

🛑 Was Policies niemals enthalten dürfen

Trigger

Delays (außer explizit unterstützt)

Sequenzen

Mehrstufige Workflows

Intent-Interpretation

Benutzerlogik

Policies sind Zustandsregeln, keine Programme.

🧪 Test- und Validierungsprozess

Beim Hinzufügen einer neuen Policy:

Entity-Mapping prüfen

Konflikte mit bestehenden Policies prüfen

Priorität korrekt setzen

Test-Szenario manuell ausführen

Logs prüfen

Erst danach produktiv verwenden

🧠 Debugging

Bei unerwartetem Verhalten:

HA Governance Logs prüfen

Policy-Name identifizieren

Priorität vergleichen

Triggernde Zustände prüfen

Automation vs. Policy unterscheiden

Merksatz:

Wenn etwas unerwartet abgeschaltet wird, war es wahrscheinlich Governance.

🔄 Änderungsregeln

Neue Policy nur hinzufügen, wenn:

Regel global gilt

Mehrfach in Automationen vorkommt

Physikalische Grenze beschreibt

Sicherheits- oder Energieschutz ist

Keine Policy für:

Einmalige Sonderfälle

Komfort-Features

Experimentelle Logik

🎯 Zielzustand

Governance soll:

Unsichtbar im Normalbetrieb sein

Nur bei Grenzverletzungen eingreifen

Klar loggen

Deterministisch bleiben

Jarvis-Orchestrator absichern

📌 Zukunft

Governance ist kompatibel mit:

Goal-Based Optimization

Multi-Room Orchestrator

LLM-gestützter Planung

Energy-Scoring

Governance bleibt jedoch immer:

Deterministische Realitätsschicht.
