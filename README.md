# Portrait Studio 2.0

Private Streamlit-App zur Vorbereitung von Bewerbungs- und LinkedIn-Porträts.
11 Fragen → bearbeitbare Vorschau → ausdrückliche TXT-Exportfreigabe.
Diese App hat **keine Bilderzeugung und keine KI-API-Anbindung**. Die Freigabe gilt
nur für den Export. Im späteren Bild-KI-Chat sind Referenzfotos und eine eigene
ausdrückliche Zustimmung erforderlich.

## Dateien übernehmen

1. Vorher den aktuellen Codespace sichern, insbesondere ungespeicherte Änderungen.
2. ZIP lokal entpacken. Den **Inhalt** des Ordners `PortraitStudio` in den
   Projektstamm `/workspaces/PortraitStudio` übernehmen. Versteckte Ordner wie
   `.streamlit` mit übernehmen. Die vorhandene `LICENSE` unverändert behalten.
3. Die alten `app.py`, `streamlit_app.py`, `requirements.txt`, `pyproject.toml`,
   `.python-version` und README durch die neuen Versionen ersetzen.
4. Die alte `config.toml` im Projektstamm wird nicht mehr verwendet. Die gültige
   Konfiguration liegt jetzt in `.streamlit/config.toml`.
5. Die alte `uv.lock` stammt aus der Vorlage und passt nicht zu den neuen
   Abhängigkeiten. Bei Nutzung von `uv` mit `uv lock` neu erzeugen und prüfen.
   Der unten beschriebene pip-Weg verwendet ausschließlich `requirements.txt`.
   Die bestehende `.devcontainer` kann für Codespaces erhalten bleiben.

## Lokal oder im Codespace starten

Python 3.12 verwenden (damit wurde dieses Paket geprüft).
Im Projektterminal:

```sh
python -m venv .venv
# Codespaces/Linux:
source .venv/bin/activate
# Windows PowerShell alternativ: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python make_password_hash.py
```

Das Hilfsprogramm fragt das Passwort verdeckt zweimal ab. Ein langes einzigartiges
Passwort verwenden; keine echten Passwörter in Chats, Code oder Git speichern.
Die ausgegebene Zeile `APP_PASSWORD_HASH = "..."` lokal in
`.streamlit/secrets.toml` eintragen. `secrets.toml.example` ist nur eine Vorlage
und wird nicht automatisch eingelesen. Die reale `secrets.toml` bleibt durch
`.gitignore` ausgeschlossen. Auch der Hash ist vertraulich zu behandeln, weil
er Offline-Passwortversuche ermöglicht.

Zusätzlich in den Secrets den Betreiberhinweis ausfüllen:

```toml
OPERATOR_NOTICE = "Betreiber: … | Datenschutzkontakt: … | Hosting und Datenschutzhinweise: …"
```

Dann:

```sh
python -m streamlit run streamlit_app.py --server.address 0.0.0.0
```

In Codespaces den angebotenen Port 8501 im Browser öffnen. Den Port **privat**
lassen. `app.py` bleibt als kompatibler zweiter Startpunkt erhalten, enthält aber
keine kopierte App-Logik mehr. Bei fehlendem/ungültigem Hash bleibt die App gesperrt.

## Bestehende Streamlit-Cloud-App aktualisieren

1. Neue Dateien einschließlich `.streamlit/config.toml` in `MaWeDu/PortraitStudio`
   committen und auf den tatsächlich deployten Branch pushen. Änderungen nur im
   Codespace aktualisieren die Cloud-App noch nicht.
2. In der Verwaltung von `portraitstudio.streamlit.app` Repository, Branch und
   Einstiegspunkt kontrollieren: `MaWeDu/PortraitStudio`, `main`, `streamlit_app.py`.
3. In den erweiterten Deployment-Einstellungen Python **3.12** wählen. Falls die
   bestehende App keinen Versionswechsel anbietet, mit denselben Einstellungen
   neu bereitstellen; vorher Secrets separat sichern.
4. In den App-Einstellungen unter **Secrets** die erzeugte Hash-Zeile und den
   ausgefüllten `OPERATOR_NOTICE` eintragen und speichern. Kein `APP_PASSWORD`
   mehr verwenden; dieser alte Klartext-Schlüssel wird nicht unterstützt.
5. App neu starten bzw. neu bereitstellen und die Cloud-Protokolle prüfen.
6. In einem privaten Browserfenster testen: ohne Anmeldung keine Fragen; falsches
   Passwort abgewiesen; richtiges Passwort zeigt elf Fragen; Vorschau und Export
   funktionieren; Änderung am Prompt entzieht Freigabe; Abmelden löscht die
   App-Sitzung. Keine Fotos und keine echte Bildgenerierung für diesen Test nötig.

Die App wird aus dem GitHub-Repository bereitgestellt, nicht durch Hochladen
einer ZIP-Datei in Streamlit. Das ZIP ist für die Dateiübernahme ins Repository.
Secrets müssen separat beim Hoster hinterlegt werden.

Offizielle Anleitungen:
- [App bereitstellen](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app)
- [Secrets verwalten](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest)

## Datenschutz und Grenzen

- Kein Foto-Upload, keine Datenbank, keine eigenen Datei- oder Inhaltsprotokolle.
- Antworttexte werden trotzdem an den Streamlit-Host übertragen und in dessen
  Sitzungsspeicher verarbeitet. Hosting-Protokolle, Infrastruktur und ein später
  genutzter Bilddienst liegen außerhalb dieser App.
- Abmelden entfernt von der App verwalteten Zustand; Downloads auf dem Endgerät
  werden nicht gelöscht. Keine Zusage sofortiger physischer Speicherlöschung.
- 30 Minuten Inaktivität führen beim nächsten Zugriff zum Abmelden, nicht zu einem
  serverseitigen Löschjob nach exakt 30 Minuten.
- Fünf fehlgeschlagene Anmeldungen sperren **diese Sitzung** für 60 Sekunden.
  Neue Sitzungen können das umgehen: kein globaler Schutz gegen Brute Force.
  Für größere Nutzung Authentifizierung und Rate-Limits des Hosters vorschalten.
- Passwortwechsel/Hashwechsel beendet alte Anmeldungen beim nächsten Zugriff.
- Kein Mehrbenutzer-Rechtesystem und keine Zusage rechtlicher Konformität.
  Betreiber muss die tatsächlichen Hosting-, Kontakt- und Datenschutzhinweise
  passend zur konkreten Bereitstellung ergänzen.
- Der feste Exporthinweis wird immer vorangestellt. Frei editierte Inhalte können
  ihm widersprechen; deshalb den gesamten Text vor Weitergabe prüfen. Eine
  Textvorlage kann Verhalten eines anderen KI-Dienstes technisch nicht erzwingen.

## Tests

```sh
python -m pip install pytest
python -m pytest tests -q
```

Die Tests verwenden ausschließlich synthetische Texte und ein Testpasswort.
Sie prüfen Anmeldung, Sperre, Unicode-Passwörter, Vorschau, eigene Vorgaben,
Freigabewiderruf nach Änderungen, Abmeldung, Zeitablauf und Hashwechsel.
Weitere Befunde und der konkrete Teststatus: `PRUEFBERICHT.md`.
