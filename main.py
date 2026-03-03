import sys
import json
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice

import ldap_auth

BASE        = Path(__file__).parent
CONFIG_PATH = BASE / "config.json"
LOGIN_UI    = BASE / "GraFix1.ui"
SUCCESS_UI  = BASE / "success.ui"

# ── Stílusok ──────────────────────────────────────────────────────────────────

STYLE_TITLE = "font-size: 18px; font-weight: bold; margin-bottom: 4px;"
STYLE_ERROR = "color: #cc0000; font-weight: bold;"
STYLE_SUCCESS_LABEL = "color: #00aa44; font-size: 22px; font-weight: bold;"
STYLE_USER_INFO = "color: #555555; font-size: 12px;"

STYLE_LOGIN_BTN = """
QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    padding: 8px 0px;
    border-radius: 4px;
    font-size: 13px;
}
QPushButton:hover    { background-color: #106ebe; }
QPushButton:pressed  { background-color: #005a9e; }
QPushButton:disabled { background-color: #888888; }
"""

STYLE_CLOSE_BTN = """
QPushButton {
    background-color: #e0e0e0;
    color: #222;
    border: none;
    padding: 7px 0px;
    border-radius: 4px;
    font-size: 13px;
}
QPushButton:hover   { background-color: #c8c8c8; }
QPushButton:pressed { background-color: #aaaaaa; }
"""

# ── Segédfüggvény ──────────────────────────────────────────────────────────────

def _load_ui(path: Path):
    loader = QUiLoader()
    f = QFile(str(path))
    f.open(QIODevice.ReadOnly)
    widget = loader.load(f)
    f.close()
    return widget


# ── Sikeres ablak ─────────────────────────────────────────────────────────────

def show_success(login_win, sam: str):
    win = _load_ui(SUCCESS_UI)
    win.successLabel.setStyleSheet(STYLE_SUCCESS_LABEL)
    win.userInfoLabel.setStyleSheet(STYLE_USER_INFO)
    win.userInfoLabel.setText(f"Üdvözöljük, {sam}!")
    win.closeButton.setStyleSheet(STYLE_CLOSE_BTN)
    win.closeButton.clicked.connect(win.close)

    # Ablak pozícionálása a login ablak fölé
    win.move(
        login_win.x() + (login_win.width()  - win.width())  // 2,
        login_win.y() + (login_win.height() - win.height()) // 2,
    )
    login_win.hide()
    win.show()

    # Ha bezárja a success ablakot, ismét megjelenik a login
    win.finished.connect(lambda _: login_win.show())
    return win  # referencia megőrzése


# ── Login ablak ───────────────────────────────────────────────────────────────

def make_login_window(config: dict):
    win = _load_ui(LOGIN_UI)

    # Cím stílus
    win.titleLabel.setStyleSheet(STYLE_TITLE)

    # Felhasználónév mező: domain előtöltése
    win.usernameEdit.setText(f"{config['domain']}\\")

    # Hiba label: kezdetben rejtett
    win.errorLabel.setStyleSheet(STYLE_ERROR)
    win.errorLabel.hide()

    # Gomb stílus
    win.loginButton.setStyleSheet(STYLE_LOGIN_BTN)

    # ── Bejelentkezés logika ──────────────────────────────────────────────────

    def on_login():
        username = win.usernameEdit.text().strip()
        password = win.passwordEdit.text()

        if not username or "\\" not in username or not password:
            win.errorLabel.setText("Kérjük adja meg a felhasználónevet (DOMAIN\\user) és a jelszót")
            win.errorLabel.show()
            return

        # UI letiltás a hívás idejére
        win.loginButton.setEnabled(False)
        win.loginButton.setText("Kérem várjon…")
        QApplication.processEvents()

        ok, msg = ldap_auth.authenticate(username, password, config)

        win.loginButton.setEnabled(True)
        win.loginButton.setText("Bejelentkezés")

        if ok:
            win.errorLabel.hide()
            win._success_win = show_success(win, msg)  # referencia
        else:
            win.errorLabel.setText(msg)
            win.errorLabel.show()
            win.passwordEdit.clear()
            win.passwordEdit.setFocus()

    win.loginButton.clicked.connect(on_login)
    win.passwordEdit.returnPressed.connect(on_login)

    return win


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)

    login = make_login_window(config)
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
