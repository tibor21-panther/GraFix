# Claude Code Szabályok – GraFix

**MUNKAKÖNYVTÁR:** `C:\GitHub\tibor21-panther\GraFix` (symlink: `C:\GraFix`)

**Git remote:** https://github.com/tibor21-panther/GraFix

## Projekt Célja

GraFix: grafikus telepítő (installer) fejlesztése Qt Designer + PySide6 alapon, Windows platformra.

## Alapszabályok

1. **Magyar nyelv** – minden kommunikáció magyarul
2. **Pontos feladatvégzés** – sem többet, sem kevesebbet mint amit kértek
3. **Nincs időbecslés** – nem adunk időbecslést
4. **Nincs halogatás** – ha van feladat, elvégezzük
5. **Merge conflict** – SOHA ne oldd fel automatikusan, kérdezd meg a felhasználót

## Git Workflow

- **Branch:** `main` (közvetlen push megengedett – saját repo)
- **Commit üzenet** – angol, rövid, tömör
- **Co-Authored-By footer kötelező:**
  ```
  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
  ```

## Push Módszer

KeePass PAT tokenes push (DPAPI titkosítás):
```powershell
# Megtalálható: C:\github\tibor21-panther\MachineForge\helpers\gh-login.ps1
# Vagy manuálisan: temp script a PAT-tal, push, temp script törlés
```

## Fájlstruktúra

```
C:\GitHub\tibor21-panther\GraFix\   # Git repo
├── .claude/
│   ├── CLAUDE.md                   # Ez a fájl
│   └── settings.json               # Claude Code permissions
└── ...                             # Projekt fájlok
```

## Technológiai Stack

- **GUI:** PySide6 + Qt Designer (`pyside6-designer`)
- **Packaging:** PyInstaller (Windows exe)
- **Python:** 3.x
- **Platform:** Windows 11
