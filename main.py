import sys
import json
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice

import ldap_auth

# ── Útvonalak ─────────────────────────────────────────────────────────────────

def _base_dir() -> Path:
    """Az exe melletti könyvtár (frozen) vagy a script mappája (dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def _get_config_path() -> Path:
    """
    Először az exe melletti config/config.json-t keresi (külső, szerkeszthető).
    Ha nem létezik, visszaesik a beágyazott verzióra.
    """
    external = _base_dir() / "config" / "config.json"
    if external.exists():
        return external
    # Fallback: PyInstaller _MEIPASS vagy script mappa
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "config" / "config.json"
    return Path(__file__).parent / "config" / "config.json"


def _ui_path(name: str) -> Path:
    """UI fájl keresése: dev módban script mappa, frozen módban _MEIPASS."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / name
    return Path(__file__).parent / name


# ── UI betöltő ─────────────────────────────────────────────────────────────────

def _load_ui(name: str):
    path = _ui_path(name)
    loader = QUiLoader()
    f = QFile(str(path))
    f.open(QIODevice.ReadOnly)
    widget = loader.load(f)
    f.close()
    return widget


# ── Sikeres ablak ──────────────────────────────────────────────────────────────

def show_success(login_win, sam: str):
    win = _load_ui("success.ui")
    win.userInfoLabel.setText(f"Üdvözöljük, {sam}!")
    win.closeButton.clicked.connect(win.close)

    win.move(
        login_win.x() + (login_win.width()  - win.width())  // 2,
        login_win.y() + (login_win.height() - win.height()) // 2,
    )
    login_win.hide()
    win.show()
    win.finished.connect(lambda _: login_win.show())
    return win  # referencia megőrzése a GC ellen


# ── Login ablak ────────────────────────────────────────────────────────────────

def make_login_window(config: dict):
    win = _load_ui("GraFix1.ui")

    # Domain előtöltése a config-ból
    win.usernameEdit.setText(f"{config['domain']}\\")

    # Hiba label: kezdetben rejtett (tervezőben látszik, futáskor elrejtjük)
    win.errorLabel.hide()

    def on_login():
        username = win.usernameEdit.text().strip()
        password = win.passwordEdit.text()

        if not username or "\\" not in username or not password:
            win.errorLabel.setText("Kérjük adja meg a felhasználónevet és a jelszót")
            win.errorLabel.show()
            return

        win.loginButton.setEnabled(False)
        win.loginButton.setText("Kérem várjon…")
        QApplication.processEvents()

        ok, msg = ldap_auth.authenticate(username, password, config)

        win.loginButton.setEnabled(True)
        win.loginButton.setText("Bejelentkezés")

        if ok:
            win.errorLabel.hide()
            win._success_win = show_success(win, msg)
        else:
            win.errorLabel.setText(msg)
            win.errorLabel.show()
            win.passwordEdit.clear()
            win.passwordEdit.setFocus()

    win.loginButton.clicked.connect(on_login)
    win.passwordEdit.returnPressed.connect(on_login)
    return win


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    config_path = _get_config_path()
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    login = make_login_window(config)
    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
