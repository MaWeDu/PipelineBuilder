"""Pure prompt and password helpers; no network, storage or generation calls."""
import hashlib
import hmac
import secrets


QUESTIONS = [
    ('purpose', '01 · Wofür brauchst du das Porträt?', ['Bewerbung und LinkedIn', 'Bewerbungsfoto', 'LinkedIn', 'Business-Porträt']),
    ('context', '02 · Welche Position und Branche möchtest du ansprechen?', None),
    ('outfit', '03 · Welche Kleidung passt zu dir und deinem Arbeitsumfeld?', ['Business Casual', 'Klassisch formell', 'Modern Business', 'Smart Casual', 'Wie auf den Referenzfotos', 'Eigene Vorgabe']),
    ('background', '04 · Welcher Hintergrund soll zu sehen sein?', ['Neutrales Fotostudio', 'Dezentes modernes Büro', 'Helle Architektur', 'Warmer dezenter Hintergrund', 'Eigene Vorgabe']),
    ('expression', '05 · Wie möchtest du wirken?', ['Freundlich und natürlich', 'Ruhig und souverän', 'Leicht lächelnd', 'Seriös und konzentriert', 'Eigene Vorgabe']),
    ('composition', '06 · Welche Haltung und welchen Ausschnitt möchtest du?', ['Kopf und Schultern, leicht gedreht', 'Kopf und Schultern, frontal', 'Bis zur Brustmitte, leicht gedreht', 'Weiteres Halbporträt', 'Eigene Vorgabe']),
    ('retouch', '07 · Wie viel natürliche Retusche möchtest du?', ['Minimal; Hautstruktur erhalten', 'Leicht; nur vorübergehende Hautunreinheiten', 'Keine Retusche', 'Eigene Vorgabe']),
    ('identity', '08 · Welche persönlichen Merkmale müssen besonders erhalten bleiben?', None),
    ('styling', '09 · Soll sich dein Styling verändern?', ['Unverändert wie auf den Referenzfotos', 'Haare und Kleidung leicht ordnen', 'Eigene Vorgabe']),
    ('variants', '10 · Wie viele Varianten und welche Ausgabeformate brauchst du?', ['1', '3', '5']),
    ('style', '11 · Welche Bildsprache bevorzugst du?', ['Zeitlos und klassisch', 'Dezent modern', 'Eigene Vorgabe']),
]

GUARD = '''PROMPT-VORLAGE — KEIN STARTAUFTRAG
Noch keine Bilder erzeugen. Prüfe zuerst diese Vorlage mit der Person.
Erst wenn geeignete eigene Referenzfotos im Bild-KI-Chat verfügbar sind und
die Person dort ausdrücklich die Bilderzeugung freigegeben hat, darf sie beginnen.
Eine Exportfreigabe aus Portrait Studio ersetzt diese Zustimmung nicht.
Fehlen Fotos oder ist etwas unklar, zuerst nachfragen. Keine Ersatzperson erfinden.
'''


def fingerprint(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def validate(answers):
    errors = []
    for key, label, options in QUESTIONS:
        if options and answers.get(key) not in options:
            errors.append(f'{label}: Bitte eine gültige Auswahl treffen.')
        if answers.get(key) == 'Eigene Vorgabe' and not answers.get(key + '_detail', '').strip():
            errors.append(f'{label}: Bitte die eigene Vorgabe ergänzen.')
    return errors


def build_prompt(answers):
    lines = []
    for key, label, _ in QUESTIONS:
        value = answers.get(key, '').strip() or 'Keine zusätzliche Vorgabe'
        detail = answers.get(key + '_detail', '').strip()
        lines.append(f'{label}\n{value}' + (f' — {detail}' if detail else ''))
    return '\n\n'.join(lines) + f'''

ERGÄNZUNGEN
Bewerbungsmarkt: {answers.get('market', '').strip() or 'Nicht festgelegt'}
Blickrichtung: {answers.get('gaze', 'Direkt in die Kamera')}
Formate: {answers.get('formats', '4:5 und 1:1')}
Weitere Wünsche: {answers.get('notes', '').strip() or 'Keine'}

IDENTITÄT UND REFERENZEN
Nach separater Freigabe fotorealistische professionelle Porträts derselben Person
anhand der realen Referenzbilder erstellen. Gesichtsform, Augenfarbe, Augenabstand,
Nase, Mund, Ohren, Haaransatz, natürliche Asymmetrien und Alter erhalten.
Keine automatische Verjüngung oder Veränderung persönlicher Merkmale.
Keine stereotype Anpassung aufgrund von Beruf oder Branche.
Identitätstreue hat Vorrang; exakte Wiedererkennbarkeit kann nicht garantiert werden.

FOTOGRAFIE UND AUSGABE
Weiches natürliches Licht, echte Haut-, Haar- und Stoffstruktur, Kamera auf Augenhöhe.
Keine künstliche Symmetrie, überglättete Haut, Halos oder Anatomiefehler.
Für 1:1 genügend Rand für den kreisförmigen Profilzuschnitt lassen.
Gewünschte Varianten nach Möglichkeit als separate Dateien ausgeben.
Keine Garantie für Auflösung, transparente Hintergründe oder technische Formate;
bei Einschränkungen des Bilddienstes zuerst nachfragen.
Bildsprache ist eine Stilpräferenz; keine Recherche aktueller Trends behaupten.
'''


def export_prompt(body):
    return GUARD + '\nKONFIGURATION ZUR PRÜFUNG\n\n' + body


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    rounds = 600_000
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), rounds)
    return f'pbkdf2_sha256${rounds}${salt}${digest.hex()}'


def valid_hash(encoded):
    try:
        algorithm, rounds, salt, digest = encoded.split('$')
        return (algorithm == 'pbkdf2_sha256' and 600_000 <= int(rounds) <= 2_000_000
                and len(bytes.fromhex(salt)) == 16 and len(bytes.fromhex(digest)) == 32)
    except (ValueError, AttributeError, TypeError):
        return False


def verify_password(password, encoded):
    if not valid_hash(encoded):
        return False
    _, rounds, salt, expected = encoded.split('$')
    actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), int(rounds))
    return hmac.compare_digest(actual, bytes.fromhex(expected))
