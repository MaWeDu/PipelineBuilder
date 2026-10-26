# Prüfbericht · 26. Oktober 2026

## Untersuchte Quellen

- GitHub-Repository `MaWeDu/PortraitStudio`, Standardbranch `main`:
  `streamlit_app.py` enthielt bei der Prüfung nur die unveränderte Beispiel-App.
  `pyproject.toml` verlangte Python >=3.14 und Streamlit >=1.61.1.
- Der bereitgestellte Codespace war über die angemeldete Chrome-Sitzung erreichbar.
  Dort lagen zusätzliche, noch nicht ins Repository übernommene Dateien und
  Änderungen vor. Die eigentliche Portrait-App wurde aus dem Editor gelesen.
- Untersucht: `app.py`, `streamlit_app.py`, `requirements.txt`, `config.toml`;
  zusätzlich Repository-README und pyproject. Keine Secrets-Dateien ausgelesen.
- `https://portraitstudio.streamlit.app/` zeigte während dieser Prüfung in Chrome
  nur den Ladezustand. Ein erfolgreicher Start der bestehenden Cloud-App konnte
  nicht bestätigt werden. Der private weitergeleitete Codespace-Port konnte im
  Browser nicht zuverlässig geprüft werden.
- Die referenzierte Unterhaltung lieferte nur Verweise statt der früheren
  ausführlichen Assistentenantworten. Frühere ZIP-Inhalte waren nicht verfügbar;
  maßgeblich waren deshalb die tatsächlich sichtbaren Codespace-Dateien.

## Korrigierte Befunde

1. **Veraltete Vorschau:** Der alte Code aktualisierte `prompt`, aber der Editor
   besaß einen eigenen bestehenden Widget-Zustand unter `prompt_editor`.
   Neue Antworten konnten dadurch im sichtbaren Export fehlen. Neue Vorschauen
   ersetzen nun ausdrücklich den Editorzustand; Antwortänderungen entfernen die
   alte Vorschau und verlangen deren Neuerstellung.
2. **Freigabe nach Textänderung:** Die alte Checkbox blieb nach Editoränderungen
   gesetzt. Die neue Freigabe bindet sich an den Hash des vollständigen Exports.
   Jede Antwort- oder Textänderung widerruft sie. Checkbox plus eigener Button
   machen den Freigabeschritt eindeutig.
3. **Unklare Freigabebedeutung:** Der alte Checkboxtext sprach von Freigabe der
   Bilderzeugung, obwohl nur Text exportiert wurde. Jetzt wird ausschließlich der
   Text-Export freigegeben. Der feste Exportkopf verlangt die separate Zustimmung
   im späteren Bilddienst und kann im App-Editor nicht entfernt werden.
4. **Offener Zugang bei fehlenden Secrets:** Der alte Passwortschutz war optional
   und wurde auch bei einem Secrets-Fehler übersprungen. Jetzt bleibt die App ohne
   gültigen Passwort-Hash geschlossen. PBKDF2-SHA256 mit 600.000 Iterationen und
   zufälligem Salt ersetzt Klartextvergleich. Unicode-Passwörter funktionieren.
5. **Sitzungsverwaltung:** Abmeldung, 30-Minuten-Inaktivitätsprüfung und Widerruf
   alter Anmeldungen bei Hashwechsel ergänzt. Fehlversuche werden pro Sitzung
   begrenzt; dies ersetzt keinen globalen Login-/Rate-Limit-Dienst.
6. **Datensparsamkeit:** Der bisherige optionale Upload übertrug Fotos an den Host,
   obwohl die App sie für den Prompt nicht benötigte. Der Upload wurde entfernt.
   Hinweise unterscheiden App-Sitzung, Hosting und späteren Bilddienst. Löschung
   wird nur für den verwalteten Sitzungszustand zugesagt.
7. **11 Fragen:** Klare deutsche Fragen, konservative Voreinstellungen, direkte
   Blickrichtung, ausdrückliche Formatauswahl und Pflichtdetails für „Eigene
   Vorgabe“. Alter und persönliche Merkmale bleiben grundsätzlich erhalten.
   „Aktuelle Trends“ wird als Stilwahl formuliert, ohne eine Recherche vorzutäuschen.
8. **Deployment:** Gültige Konfiguration in `.streamlit/config.toml`; nur ein
   zentraler App-Code mit kompatiblem `app.py`-Einstiegspunkt; feste getestete
   Streamlit-Version; Python-3.12-Anleitung statt widersprüchlicher Vorlage.
   Alten Lockfile bei Übernahme neu erzeugen.
9. **Kopieren:** Der bisher behauptete Kopierknopf im Textfeld existierte so nicht.
   Jetzt gibt es nach Freigabe einen aufklappbaren vollständigen Codeblock mit dem
   von Streamlit unterstützten Kopieren sowie einen TXT-Download.

## Ausgeführte Tests

Umgebung: Windows, Python 3.12.14, Streamlit 1.66.0, pytest 9.1.1.

**8 automatisierte Tests bestanden (20,94 Sekunden).** Geprüft wurden:

- Passwortprüfung inklusive Umlauten, ungültigen Hashes und falschem Passwort.
- Geschlossener Zugang bei fehlender/ungültiger Hashkonfiguration.
- Fünf Fehlversuche, Wartezeit und anschließende erfolgreiche Anmeldung.
- Genau elf Fragen, keine Foto-Upload-Komponente, Vorschau ohne Downloadfreigabe.
- Freigabe per Checkbox und Button; Widerruf bei Änderungen am Prompt.
- Widerruf bei Antwortänderung und tatsächlich aktualisierte neue Vorschau.
- Validierung eigener Vorgaben und Übernahme in den Prompt.
- Abmeldung, Zeitablauf, Passwort-Hashwechsel, kompatibler `app.py`-Start sowie
  fester Exportkopf.

Zusätzlicher Funktionstest in **Chrome** gegen eine nur lokal erreichbare Instanz:
Anmeldung mit synthetischem Testpasswort, elf Fragen, Vorschau, Exportfreigabe und
echter TXT-Download erfolgreich. Der heruntergeladene UTF-8-Text wurde gelesen;
der feste Hinweis „Noch keine Bilder erzeugen“ ist enthalten.
Screenshot der erfolgreichen Freigabe liegt neben dem ZIP.

Keine echten Referenzfotos, keine Bild-API und keine Bilderzeugung verwendet.
Tests betreffen die ausgelieferten Dateien. Die produktive Cloud-App wurde nicht
aktualisiert; ihr späterer Start mit echten Betreiber-Secrets muss nach Deployment
separat geprüft werden. Ein rechtliches Datenschutz-Audit wurde nicht durchgeführt.

## Auslieferung

ZIP und entpackte Projektdateien sind lokale aktualisierte Lieferdateien.
Codespace und GitHub wurden bei dieser Prüfung nur gelesen. Die Schritte zur
Übernahme und zum Cloud-Deployment stehen in `README.md`. Für einen öffentlichen
Betrieb müssen Betreiberkontakt, konkrete Datenschutzhinweise und Hosting-Zugang
durch den Betreiber eingerichtet werden.
