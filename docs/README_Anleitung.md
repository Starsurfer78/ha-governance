Jarvis House Architecture – Room & Policy Model

Version 0.1

🧠 Zweck

Dieses Dokument beschreibt die strukturelle Architektur des Smart-Home-Systems.

Ziel:

Deterministische Sicherheitslogik

Klare Trennung zwischen Automationen und Policies

Raum-basierte Struktur

Skalierbarkeit für Jarvis-Orchestrator

Debugbarkeit und Wartbarkeit

🏗 System-Schichten
Automation Layer  → Trigger & Ablauf
Policy Layer      → Globale Zustandsregeln (HA Governance)
Home Assistant    → State Machine
Jarvis (optional) → Orchestrator / Intent / Goals


Wichtig:

Automationen lösen Aktionen aus.

Policies erzwingen globale Sicherheits- und Energiegrenzen.

Policies enthalten keine Trigger-Logik.

Automationen enthalten keine globalen Schutzbedingungen.

🏠 Raum-Modell

Jeder Raum wird als logische Einheit betrachtet.

Ein Raum besteht aus:

Komponente	Zweck
window_<raum>_any_open	Mindestens ein Fenster offen
presence_<raum>	Präsenz im Raum
climate.<raum>	Heizungs-Entity
light.<raum>_main	Hauptlicht-Gruppe
sensor.temperature_<raum>	Temperatur
sensor.co2_<raum> (optional)	Luftqualität
🪟 Fenster-Aggregation

Wenn ein Raum mehrere Fenster besitzt, werden diese über einen Template-Binary-Sensor zusammengefasst.

Beispiel:

template:
  - binary_sensor:
      - name: window_wohnzimmer_any_open
        state: >
          {{
            is_state('binary_sensor.window_wz_links', 'on')
            or
            is_state('binary_sensor.window_wz_rechts', 'on')
          }}


Warum?

Keine Wildcards in Policies

Klare 1:1 Beziehung zwischen Raum und Heizkreis

Debugbar im HA-State

Orchestrator-kompatibel

🔥 Heizungs-Schutzregel

Globale Sicherheitsregel:

- name: heating_window_protection_wohnzimmer
  priority: 95
  when:
    binary_sensor.window_wohnzimmer_any_open: "on"
    climate.wohnzimmer: "heat"
  enforce:
    service: climate.turn_off
    target: climate.wohnzimmer


Regel:

Wenn Fenster offen ist, darf Heizung nicht heizen.

Diese Logik gehört ausschließlich in die Policy Layer.

💡 Licht-Logik

Licht-Automationen enthalten nur:

Trigger (Bewegung, Lux, TV)

Ablauf

Globale Grenzen (z. B. Nachtmodus) gehören in Policies.

Adaptive Lighting bleibt Komfort-Engine und wird nicht dauerhaft überschrieben.

⚡ Media-Steckdose-Logik

Abschaltung erfolgt nur bei bestätigtem Idle-Zustand.

Automation erkennt Idle.

Policy erzwingt Abschaltung.

Trennung:

Automation = Zustandserkennung

Policy = physikalische Begrenzung

📛 Namenskonvention

Alle raumbasierten Entitäten folgen dem Schema:

window_<raum>_any_open
presence_<raum>
climate.<raum>
light.<raum>_main


Keine Wildcards in Policies.

Keine globalen Fenster-Aggregate.

🔐 Sicherheitsprinzipien

Safety hat höchste Priorität.

Energie kommt vor Komfort.

Policies enthalten keine Trigger.

Automationen enthalten keine globalen Schutzregeln.

LLMs (falls verwendet) sind niemals Entscheider.

🚦 Migration-Regel

Beim Refactoring von Automationen gilt:

Wenn eine Bedingung eine globale physikalische Grenze beschreibt,
wird sie in policies.yaml verschoben.

Automationen bleiben ansonsten unverändert.

🎯 Zielzustand

Das System soll:

Deterministisch sein

Skalierbar sein

Debugbar sein

Orchestrator-fähig sein

Nicht von impliziten Logik-Ketten abhängen

📌 Hinweis

Dieses Dokument beschreibt die Struktur.
Es ersetzt keine Automationen, sondern definiert deren Rahmen.
