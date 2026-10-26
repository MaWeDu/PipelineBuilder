"""Portrait Studio: text-only configuration with explicit export approval."""
import os
import time
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from portrait_core import (QUESTIONS, GUARD, build_prompt, export_prompt, fingerprint,
                           validate, valid_hash, verify_password)

st.set_page_config(page_title='Portrait Studio', page_icon='📷', layout='centered')


def revoke():
    st.session_state.pop('approved_digest', None)
    st.session_state['export_consent'] = False


def config_changed():
    revoke()
    for key in ('prompt_editor', 'source_digest'):
        st.session_state.pop(key, None)


def clear_session():
    for key in list(st.session_state):
        del st.session_state[key]


def setting(name):
    try:
        return st.secrets.get(name, os.environ.get(name, ''))
    except StreamlitSecretNotFoundError:
        return os.environ.get(name, '')


def authenticate():
    encoded = setting('APP_PASSWORD_HASH')
    if not valid_hash(encoded):
        st.error('Der private Zugang ist noch nicht eingerichtet. Bitte APP_PASSWORD_HASH in den Server-Secrets konfigurieren. Anleitung: README.md.')
        st.stop()
    now = time.time()
    if st.session_state.get('auth_config') != fingerprint(encoded) or now - st.session_state.get('last_active', 0) > 1800:
        clear_session()
        st.session_state.update(auth_config=fingerprint(encoded), last_active=now)
    if st.session_state.get('authenticated'):
        st.session_state['last_active'] = now
        return
    st.title('📷 Portrait Studio')
    st.subheader('Privater Zugang')
    remaining = max(0, int(st.session_state.get('locked_until', 0) - now) + 1)
    if remaining:
        st.warning(f'Bitte warte {remaining} Sekunden und versuche es danach erneut.')
    with st.form('login'):
        password = st.text_input('Zugangspasswort', type='password', max_chars=256, key='password_entry')
        submitted = st.form_submit_button('Anmelden', disabled=bool(remaining))
    if submitted and not remaining:
        if verify_password(password, encoded):
            clear_session()
            st.session_state.update(authenticated=True, auth_config=fingerprint(encoded), last_active=now)
            st.rerun()
        else:
            failures = st.session_state.get('failures', 0) + 1
            st.session_state.update(auth_config=fingerprint(encoded), last_active=now, failures=failures)
            if failures >= 5:
                st.session_state['locked_until'] = now + 60
            st.session_state['clear_password'] = True
            st.rerun()
    if st.session_state.pop('clear_password', False):
        # Clear on the next run before widget instantiation (handled below).
        st.error('Anmeldung fehlgeschlagen.')
    st.stop()


if st.session_state.get('clear_password'):
    st.session_state.pop('password_entry', None)
authenticate()

st.title('📷 Portrait Studio')
st.write('Dein Bewerbungs- und LinkedIn-Porträt in 11 Fragen vorbereiten.')
st.info('Diese App erstellt ausschließlich Text. Sie erzeugt keine Bilder und hat keine Verbindung zu einem Bild-KI-Dienst.')
st.button('Sitzungsdaten löschen und abmelden', on_click=clear_session)
with st.expander('Datenschutz: Was passiert mit deinen Angaben?'):
    st.write('Deine Texte werden zur Verarbeitung an den Streamlit-Server übertragen und im Sitzungsspeicher gehalten. Diese App schreibt sie nicht in Dateien, Datenbanken oder eigene Protokolle. Ein Foto-Upload ist bewusst nicht enthalten. Namen, Kontaktdaten oder andere vertrauliche Angaben sind für den Prompt nicht nötig.')
    st.write('Die Schaltfläche zum Abmelden entfernt die von dieser App verwalteten Sitzungsdaten. Bereits heruntergeladene Dateien bleiben auf deinem Gerät. Eine sofortige vollständige Löschung aus Browser-, Infrastruktur- oder Serverspeicher wird nicht zugesichert. Bei Inaktivität wird die Anmeldung beim nächsten Zugriff nach 30 Minuten verworfen.')
    st.write('Referenzfotos erst später im von dir gewählten Bilddienst hochladen. Dessen Bedingungen und Datenschutzhinweise gelten dort gesondert. Nutze nur Fotos mit den erforderlichen Rechten und Einwilligungen. Betreiber- und Hosting-Angaben stehen unten, sofern konfiguriert.')
    st.caption('Der Passwortzugang ist ein geteilter Zugang ohne Benutzerkonten. Für öffentlich erreichbare Apps zusätzlich die Zugriffsverwaltung des Hosters nutzen.')

answers = {}
for key, label, options in QUESTIONS:
    st.subheader(label)
    if options:
        answers[key] = st.selectbox('Auswahl', options, key='q_' + key, on_change=config_changed)
        answers[key + '_detail'] = st.text_input('Details (bei eigener Vorgabe erforderlich)', key='q_' + key + '_detail', max_chars=400, on_change=config_changed)
    else:
        help_text = ('Zum Beispiel: Data Analyst im Gesundheitswesen; keine Arbeitgebernamen nötig.' if key == 'context'
                     else 'Zum Beispiel: Brille und Sommersprossen erhalten. Alter und Gesichtsmerkmale bleiben grundsätzlich erhalten.')
        answers[key] = st.text_input('Deine Angaben (optional)', help=help_text, key='q_' + key, max_chars=400, on_change=config_changed)
    if key == 'context':
        answers['market'] = st.text_input('Bewerbungsmarkt (optional)', key='q_market', max_chars=100, on_change=config_changed)
    if key == 'composition':
        answers['gaze'] = st.selectbox('Blickrichtung', ['Direkt in die Kamera', 'Leicht versetzt', 'Dezent seitlich'], key='q_gaze', on_change=config_changed)
    if key == 'variants':
        answers['formats'] = st.selectbox('Ausgabeformate', ['4:5 und 1:1', '4:5', '3:4', '1:1'], key='q_formats', on_change=config_changed)
answers['notes'] = st.text_area('Weitere Wünsche (optional)', key='q_notes', max_chars=1200, on_change=config_changed)

if st.button('Prompt-Vorschau erstellen', type='primary'):
    revoke()
    errors = validate(answers)
    if errors:
        for error in errors:
            st.error(error)
    else:
        st.session_state['prompt_editor'] = build_prompt(answers)
        st.session_state['source_digest'] = fingerprint(repr(answers))

if 'prompt_editor' in st.session_state:
    st.divider()
    st.subheader('Prompt prüfen und Export freigeben')
    st.caption('Änderungen an Antworten oder Prompt heben die Exportfreigabe auf. Neue Antworten erfordern eine neue Vorschau.')
    st.code(GUARD, language=None)
    body = st.text_area('Bearbeitbarer Prompt', key='prompt_editor', height=450, max_chars=16000, on_change=revoke)
    full_prompt = export_prompt(body)
    digest = fingerprint(full_prompt)
    st.checkbox('Ich habe diesen Text geprüft und gebe ausschließlich den TXT-Export frei. Eine Bilderzeugung erfordert später meine separate Zustimmung im Bild-KI-Chat.', key='export_consent', on_change=lambda: st.session_state.pop('approved_digest', None))
    if st.button('Diesen Prompt zum Export freigeben', disabled=not (st.session_state.get('export_consent') and body.strip())):
        st.session_state['approved_digest'] = digest
    approved = st.session_state.get('approved_digest') == digest and st.session_state.get('export_consent')
    if approved:
        st.success('Text zum Export freigegeben. Es wurden keine Bilder erzeugt.')
        st.download_button('Geprüften Prompt als TXT herunterladen', full_prompt.encode('utf-8'), file_name='portrait-studio-prompt.txt', mime='text/plain')
        st.caption('Zum Kopieren kannst du den vollständigen Exporttext aufklappen. Der feste Freigabehinweis wird immer mit exportiert.')
        with st.expander('Vollständigen Exporttext kopieren'):
            st.code(full_prompt, language=None)

st.divider()
st.caption('Portrait Studio · Textvorbereitung · Keine integrierte Bilderzeugung')
operator = setting('OPERATOR_NOTICE')
if operator:
    st.text(operator)
else:
    st.caption('Betreiber- und Datenschutzkontakt noch nicht hinterlegt. Vor Veröffentlichung ergänzen.')
