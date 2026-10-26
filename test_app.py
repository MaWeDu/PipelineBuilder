import sys
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from streamlit.testing.v1 import AppTest
from portrait_core import QUESTIONS, GUARD, hash_password, verify_password, valid_hash

PASSWORD = 'Testpasswort mit Umlaut ä 123!'
HASH = hash_password(PASSWORD)


def app(login=True, entry='streamlit_app.py'):
    at = AppTest.from_file(str(ROOT / entry))
    at.secrets['APP_PASSWORD_HASH'] = HASH
    at.run()
    if login:
        at.text_input(key='password_entry').set_value(PASSWORD)
        at.button[0].click().run()
    assert not at.exception
    return at


def button(at, label):
    return next(b for b in at.button if b.label == label)


def preview(at):
    button(at, 'Prompt-Vorschau erstellen').click().run()
    assert not at.exception


def approve(at):
    at.checkbox(key='export_consent').check().run()
    button(at, 'Diesen Prompt zum Export freigeben').click().run()
    assert not at.exception


def test_password_hash_unicode_and_invalid():
    assert verify_password(PASSWORD, HASH)
    assert not verify_password('falsch', HASH)
    for bad in ['', None, 'pbkdf2_sha256$1$ab$cd', HASH + '$bad']:
        assert not valid_hash(bad)
        assert not verify_password(PASSWORD, bad)


def test_missing_or_invalid_secret_closed():
    for secret in ['', 'wrong']:
        at = AppTest.from_file(str(ROOT / 'streamlit_app.py'))
        at.secrets['APP_PASSWORD_HASH'] = secret
        at.run()
        assert len(at.error) == 1
        assert not at.selectbox
        assert not at.exception


def test_login_and_throttle():
    at = app(login=False)
    for _ in range(5):
        at.text_input(key='password_entry').set_value('falsch')
        at.button[0].click().run()
        assert not at.exception
        assert at.text_input(key='password_entry').value == ''
    assert at.button[0].disabled
    assert not at.selectbox
    at.session_state['locked_until'] = time.time() - 1
    at.run()
    at.text_input(key='password_entry').set_value(PASSWORD)
    at.button[0].click().run()
    assert at.selectbox


def test_eleven_questions_preview_approval_and_prompt_change():
    at = app()
    assert len(QUESTIONS) == 11
    assert len([h for h in at.subheader if h.value[:2].isdigit()]) == 11
    assert not at.get('file_uploader')
    preview(at)
    assert not at.get('download_button')
    assert button(at, 'Diesen Prompt zum Export freigeben').disabled
    approve(at)
    assert len(at.get('download_button')) == 1
    old = at.text_area(key='prompt_editor').value
    at.text_area(key='prompt_editor').set_value(old + '\nNeue Anweisung').run()
    assert not at.get('download_button')
    assert not at.checkbox(key='export_consent').value
    approve(at)
    assert at.get('download_button')


def test_answers_invalidate_and_new_preview_is_fresh():
    at = app()
    preview(at)
    approve(at)
    at.text_input(key='q_context').set_value('Data Analyst').run()
    assert not at.get('download_button')
    assert 'prompt_editor' not in at.session_state
    preview(at)
    assert 'Data Analyst' in at.text_area(key='prompt_editor').value
    assert not at.checkbox(key='export_consent').value


def test_custom_choice_requires_details():
    at = app()
    at.selectbox(key='q_outfit').select('Eigene Vorgabe').run()
    preview(at)
    assert at.error
    assert 'prompt_editor' not in at.session_state
    at.text_input(key='q_outfit_detail').set_value('Dunkelblaues Hemd').run()
    preview(at)
    assert 'Dunkelblaues Hemd' in at.text_area(key='prompt_editor').value


def test_logout_timeout_and_password_rotation():
    at = app()
    preview(at)
    button(at, 'Sitzungsdaten löschen und abmelden').click().run()
    assert not at.selectbox
    assert 'prompt_editor' not in at.session_state
    at = app()
    at.session_state['last_active'] = time.time() - 1801
    at.run()
    assert not at.selectbox
    at = app()
    at.secrets['APP_PASSWORD_HASH'] = hash_password('another valid password')
    at.run()
    assert not at.selectbox


def test_compatibility_entrypoint_and_guard():
    at = app(entry='app.py')
    preview(at)
    assert at.code[0].value == GUARD.strip()
    approve(at)
    assert at.code[1].value.startswith(GUARD)
