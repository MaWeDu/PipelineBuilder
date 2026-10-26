"""Run locally; paste only the resulting hash into Streamlit secrets."""
from getpass import getpass
from portrait_core import hash_password

if __name__ == '__main__':
    password = getpass('Neues Zugangspasswort (mindestens 16 Zeichen): ')
    if len(password) < 16:
        raise SystemExit('Bitte mindestens 16 Zeichen verwenden.')
    if password != getpass('Passwort wiederholen: '):
        raise SystemExit('Die Eingaben stimmen nicht überein.')
    print('APP_PASSWORD_HASH = "' + hash_password(password) + '"')
