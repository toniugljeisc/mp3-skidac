# MP3 Skidač

Windows program: zalijepiš link pjesme ili playliste → vidiš pregled (sličice, hover = mali YouTube player) → skida redom u MP3 i svaku pjesmu nivelira na istu glasnoću (−14 LUFS).

Treba Windows 10/11 s Microsoft Edge WebView2 (već ugrađen u Windows 11 i ažurirani Windows 10).

## Kako dobiti MP3-Skidac-Setup.exe (GitHub ga napravi besplatno)

1. Napravi besplatan račun na https://github.com i klikni **New repository** (ime npr. `mp3-skidac`, može Private).
2. Na stranici repozitorija klikni **uploading an existing file** i povuci SVE iz ovog foldera
   (`app`, `installer`, `.github`, `README.md`, `.gitignore`). Klikni **Commit changes**.
   - Folder `.github` je skriven u Windowsu: u Exploreru uključi **Prikaz → Skrivene stavke**.
3. Otvori karticu **Actions**. Build traje ~5 minuta (zelena kvačica = gotovo).
4. Desno na glavnoj stranici repozitorija → **Releases** → skini **MP3-Skidac-Setup.exe**.

## Instalacija

- Dvoklik na `MP3-Skidac-Setup.exe` → Next → Install. Ne treba administrator ni Python.
- Ako Windows pokaže "Windows je zaštitio računar": **Više informacija → Ipak pokreni**
  (program nije digitalno potpisan).
- Deinstalacija: Postavke → Aplikacije → MP3 Skidač → Deinstaliraj.

## Što je unutra

- `app/mp3_skidac.py` — program (Python + pywebview)
- `app/ui/index.html` — sučelje
- `installer/setup.iss` — Inno Setup instalacija
- `.github/workflows/build.yml` — automatski build (PyInstaller + yt-dlp.exe + ffmpeg.exe + Inno Setup)

yt-dlp se sam ažurira pri svakom pokretanju programa.
