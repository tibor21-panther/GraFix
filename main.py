import sys
import json
import logging
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice

import ldap_auth

# ── Útvonalak ─────────────────────────────────────────────────────────────────

def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def _get_config_path() -> Path:
    external = _base_dir() / "config" / "config.json"
    if external.exists():
        return external
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "config" / "config.json"
    return Path(__file__).parent / "config" / "config.json"


def _ui_path(name: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / name
    return Path(__file__).parent / name


# ── Logging beállítás ──────────────────────────────────────────────────────────

def _setup_logging():
    log_dir = _base_dir() / "log"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "log.txt"

    fmt = "%(asctime)s  %(levelname)-8s  %(name)s — %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=logging.DEBUG,
        format=fmt,
        datefmt=datefmt,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    log = logging.getLogger("grafix.main")
    log.info("──────────────────────────────────────────")
    log.info("GraFix indítás  [%s]", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log.info("Config: %s", _get_config_path())
    return log


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
    return win


# ── Login ablak ────────────────────────────────────────────────────────────────

def make_login_window(config: dict):
    log = logging.getLogger("grafix.main")
    win = _load_ui("GraFix1.ui")

    if config.get("app_title"):
        win.setWindowTitle(config["app_title"])

    win.usernameEdit.setText(f"{config['domain']}\\")
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
            log.info("UI: sikeres bejelentkezés — %s", username)
            win.errorLabel.hide()
            win._success_win = show_success(win, msg)
        else:
            log.warning("UI: sikertelen bejelentkezés — %s | %s", username, msg)
            win.errorLabel.setText(msg)
            win.errorLabel.show()
            win.passwordEdit.clear()
            win.passwordEdit.setFocus()

    win.loginButton.clicked.connect(on_login)
    win.passwordEdit.returnPressed.connect(on_login)
    return win


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    log = _setup_logging()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    try:
        config_path = _get_config_path()
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
        log.info("Config betöltve: %s", config_path)
        log.debug("Config tartalom: %s", {k: v if k != "ldap_bind_password" else "***" for k, v in config.items()})
    except Exception as e:
        log.exception("Config betöltési hiba: %s", e)
        raise

    login = make_login_window(config)
    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
