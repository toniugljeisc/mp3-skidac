"""
MP3 Skidač
- Zalijepi link pjesme ili playliste (pregled s YouTube playerom)
- Skida redom, pretvara u MP3
- Svaku pjesmu nivelira na istu glasnoću (FFmpeg loudnorm, 2 prolaza)

Sučelje: ui/index.html u prozoru (pywebview + Edge WebView2).
Alati: yt-dlp.exe i ffmpeg.exe pored programa (instalacija ih donosi).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading

APP_NAME = "MP3 Skidač"
APP_VERSION = "1.1"

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
    RES_DIR = getattr(sys, "_MEIPASS", APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RES_DIR = APP_DIR

IS_WIN = os.name == "nt"
NO_WINDOW = 0x08000000 if IS_WIN else 0
EXE = ".exe" if IS_WIN else ""

CONFIG_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "MP3 Skidac")
CONFIG_FILE = os.path.join(CONFIG_DIR, "postavke.json")
DEFAULTS = {
    "out_dir": os.path.join(os.path.expanduser("~"), "Music", "MP3 Skidac"),
    "lufs": "-14", "bitrate": "320k", "numbering": True, "subfolder": True, "skip": True,
}


# ------------------------------------------------------------------ Alati ---

def find_tool(name):
    for c in (os.path.join(APP_DIR, name + EXE),
              os.path.join(APP_DIR, "bin", name + EXE),
              os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Links", name + EXE)):
        if os.path.isfile(c):
            return c
    return shutil.which(name)


def run(cmd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", creationflags=NO_WINDOW, env=env)


def measure_loudness(ffmpeg, src, target_i, target_tp, target_lra):
    """1. prolaz: izmjeri glasnoću."""
    af = f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:print_format=json"
    r = run([ffmpeg, "-hide_banner", "-nostats", "-i", src, "-af", af, "-f", "null", "-"])
    m = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        raise RuntimeError("Mjerenje glasnoće nije uspjelo:\n" + r.stderr[-600:])
    return json.loads(m[-1])


def normalize_to_mp3(ffmpeg, src, dst, meta, target_i, target_tp, target_lra, bitrate):
    """2. prolaz: linearna normalizacija + MP3."""
    st = measure_loudness(ffmpeg, src, target_i, target_tp, target_lra)
    af = (f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}"
          f":measured_I={st['input_i']}:measured_TP={st['input_tp']}"
          f":measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}"
          f":offset={st['target_offset']}:linear=true:print_format=summary")
    cmd = [ffmpeg, "-hide_banner", "-nostats", "-y", "-i", src, "-vn",
           "-af", af, "-ar", "44100", "-c:a", "libmp3lame", "-b:a", bitrate,
           "-id3v2_version", "3"]
    for k, v in meta.items():
        if v:
            cmd += ["-metadata", f"{k}={v}"]
    cmd.append(dst)
    r = run(cmd)
    if r.returncode != 0 or not os.path.isfile(dst):
        raise RuntimeError("Konverzija nije uspjela:\n" + r.stderr[-600:])
    return float(st["input_i"])


def last_json(text):
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return None


YT_ID = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})")


def video_id(url):
    m = YT_ID.search(url or "")
    return m.group(1) if m else ""


def ytdlp_list(ytdlp, url):
    """Vrati (naslov_playliste ili None, [{id, url, title}...]) redom."""
    r = run([ytdlp, "-J", "--flat-playlist", "--no-warnings", "--encoding", "utf-8", url])
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-400:] or "Nepoznata greška")
    info = json.loads(r.stdout)
    if info.get("_type") == "playlist" or info.get("entries") is not None:
        out = []
        for e in info.get("entries") or []:
            if not e:
                continue
            u = e.get("url") or e.get("webpage_url") or ""
            vid = e.get("id") or video_id(u)
            if not u.startswith("http"):
                u = f"https://www.youtube.com/watch?v={vid or u}"
            out.append({"id": vid, "url": u, "title": e.get("title") or ""})
        return info.get("title") or "Playlista", out
    u = info.get("webpage_url") or url
    return None, [{"id": info.get("id") or video_id(u), "url": u, "title": info.get("title") or ""}]


def ytdlp_download(ytdlp, ffmpeg, url, tmp):
    fields = "%(.{filepath,title,track,artist,uploader,album,id})j"
    r = run([ytdlp, "-f", "bestaudio/best", "--no-playlist", "--no-progress",
             "--no-warnings", "--encoding", "utf-8", "--retries", "5",
             "--ffmpeg-location", ffmpeg,
             "-o", os.path.join(tmp, "%(id)s.%(ext)s"),
             "--no-simulate", "-O", "after_move:" + fields, url])
    info = last_json(r.stdout)
    if r.returncode != 0 or not info or not os.path.isfile(info.get("filepath") or ""):
        raise RuntimeError(r.stderr.strip()[-400:] or "Skidanje nije uspjelo")
    return info


def nice_error(e):
    msg = str(e).strip().splitlines()[-1] if str(e).strip() else "Greška"
    msg = re.sub(r"^ERROR:\s*(\[[^\]]+\]\s*[\w-]+:\s*)?", "", msg)
    low = msg.lower()
    for k, v in (("private video", "Privatni video"), ("video unavailable", "Video nije dostupan"),
                 ("sign in to confirm your age", "Video je dobno ograničen"),
                 ("not available in your country", "Nije dostupno u tvojoj zemlji"),
                 ("unable to download", "Skidanje nije uspjelo — provjeri internet")):
        if k in low:
            return v
    return msg[:120]


def safe_name(s, maxlen=150):
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", s or "").strip().rstrip(".")
    s = re.sub(r"\s+", " ", s)
    return s[:maxlen].strip() or "pjesma"


def load_config():
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def read_clipboard():
    if not IS_WIN:
        return ""
    import ctypes
    from ctypes import wintypes
    u32, k32 = ctypes.windll.user32, ctypes.windll.kernel32
    u32.GetClipboardData.restype = wintypes.HANDLE
    k32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    k32.GlobalLock.restype = wintypes.LPVOID
    k32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    if not u32.OpenClipboard(None):
        return ""
    try:
        h = u32.GetClipboardData(13)  # CF_UNICODETEXT
        if not h:
            return ""
        p = k32.GlobalLock(h)
        try:
            return ctypes.wstring_at(p) if p else ""
        finally:
            k32.GlobalUnlock(h)
    finally:
        u32.CloseClipboard()


def split_urls(text):
    return [u.strip() for u in (text or "").splitlines() if u.strip()]


# -------------------------------------------------------- Most prema UI-ju ---

class Api:
    """Metode koje sučelje (JavaScript) poziva preko window.pywebview.api."""

    def __init__(self):
        self._window = None
        self._ytdlp = find_tool("yt-dlp")
        self._ffmpeg = find_tool("ffmpeg")
        self._stop_flag = threading.Event()
        self._running = False
        self._cache = {}           # url -> (pl_title, items)
        self._lock = threading.Lock()

    # ---- slanje događaja u UI
    def _emit(self, kind, **data):
        if not self._window:
            return
        data["kind"] = kind
        try:
            self._window.evaluate_js(f"window.onEvent({json.dumps(data, ensure_ascii=False)})")
        except Exception:
            pass

    # ---- pozivi iz UI-ja
    def init(self):
        missing = [n for n, p in (("yt-dlp", self._ytdlp), ("ffmpeg", self._ffmpeg)) if not p]
        threading.Thread(target=self._self_update, daemon=True).start()
        return {"config": load_config(), "missing": missing, "version": APP_VERSION}

    def save(self, cfg):
        c = load_config()
        c.update({k: cfg[k] for k in DEFAULTS if k in cfg})
        save_config(c)
        return True

    def paste(self):
        try:
            return read_clipboard()
        except Exception:
            return ""

    def pick_dir(self, current=""):
        import webview
        try:
            res = self._window.create_file_dialog(webview.FOLDER_DIALOG, directory=current or "")
        except Exception:
            return ""
        if not res:
            return ""
        return os.path.normpath(res[0] if isinstance(res, (list, tuple)) else res)

    def open_dir(self, path):
        try:
            os.makedirs(path, exist_ok=True)
            if IS_WIN:
                os.startfile(path)
        except OSError:
            pass
        return True

    def _list(self, url):
        with self._lock:
            if url in self._cache:
                return self._cache[url]
        res = ytdlp_list(self._ytdlp, url)
        with self._lock:
            self._cache[url] = res
        return res

    def preview(self, text):
        """Pročitaj linkove (bez skidanja): naslovi + ID-jevi za sličice."""
        if not self._ytdlp:
            return {"items": [], "errors": ["Nedostaje yt-dlp"]}
        items, errors, playlists = [], [], []
        for u in split_urls(text):
            try:
                pl, entries = self._list(u)
            except Exception as e:
                errors.append(f"{u}: {str(e).strip().splitlines()[-1] if str(e).strip() else 'greška'}")
                continue
            if pl is not None:
                playlists.append({"title": pl, "count": len(entries)})
            for e in entries:
                items.append({"id": e["id"], "title": e["title"]})
        return {"items": items, "playlists": playlists, "errors": errors}

    def start(self, cfg):
        if self._running:
            return False
        if not self._ytdlp or not self._ffmpeg:
            return False
        self.save(cfg)
        self._stop_flag.clear()
        self._running = True
        threading.Thread(target=self._work, args=(cfg,), daemon=True).start()
        return True

    def stop(self):
        self._stop_flag.set()
        return True

    # ---- pozadina
    def _self_update(self):
        """yt-dlp se sam ažurira pri svakom pokretanju (YouTube se često mijenja)."""
        if not self._ytdlp or not os.path.dirname(self._ytdlp).startswith(APP_DIR):
            return
        r = run([self._ytdlp, "-U"])
        if "updated yt-dlp to" in (r.stdout + r.stderr).lower():
            self._emit("info", text="yt-dlp je ažuriran na najnoviju verziju.")

    def _work(self, cfg):
        emit = self._emit
        ok = fail = skipped = 0
        tmp = tempfile.mkdtemp(prefix="mp3skidac_")
        try:
            try:
                lufs = float(str(cfg.get("lufs", "-14")).replace(",", ".").replace("−", "-"))
            except ValueError:
                lufs = -14.0
            bitrate = cfg.get("bitrate", "320k")
            out = cfg.get("out_dir") or DEFAULTS["out_dir"]
            numbering, subfolder, skip = cfg.get("numbering", True), cfg.get("subfolder", True), cfg.get("skip", True)

            jobs = []
            emit("status", text="Čitam linkove…")
            for u in split_urls(cfg.get("text", "")):
                try:
                    pl_title, items = self._list(u)
                except Exception as e:
                    emit("status", text=f"Ne mogu pročitati link: {u}", color="red")
                    continue
                if pl_title is not None:
                    folder = os.path.join(out, safe_name(pl_title)) if subfolder else out
                    for i, e in enumerate(items, 1):
                        jobs.append(dict(e, folder=folder, idx=i, pl_len=len(items), pl=pl_title))
                else:
                    jobs.append(dict(items[0], folder=out, idx=None, pl_len=None, pl=None))

            total = len(jobs)
            if not total:
                emit("status", text="Nema ništa za skinuti.", color="red")
                return

            def label(j, title):
                name = safe_name(title) if title else "Učitavam naziv…"
                if numbering and j["idx"]:
                    name = f"{str(j['idx']).zfill(max(2, len(str(j['pl_len']))))} - {name}"
                return name

            emit("jobs", items=[{"id": j["id"], "title": label(j, j["title"])} for j in jobs])
            pls = {j["pl"] for j in jobs if j["pl"]}
            if len(pls) == 1:
                emit("status", text=f"Playlista: {pls.pop()} · {total} pjesama")

            for n, j in enumerate(jobs, 1):
                if self._stop_flag.is_set():
                    emit("status", text=f"Zaustavljeno — skinuto: {ok}, preskočeno: {skipped}, greške: {fail}", color="accent")
                    return
                i = n - 1
                emit("progress", cur=n, done=i, total=total)
                emit("row", i=i, state="active", sub="Skidam…")
                emit("status", text=f"Skidam: {label(j, j['title'])}")
                src = None
                try:
                    info = ytdlp_download(self._ytdlp, self._ffmpeg, j["url"], tmp)
                    src = info["filepath"]
                    title = info.get("track") or info.get("title") or info.get("id")
                    artist = re.sub(r"\s*-\s*Topic$", "", info.get("artist") or info.get("uploader") or "")
                    name = label(j, title)
                    os.makedirs(j["folder"], exist_ok=True)
                    dst = os.path.join(j["folder"], name + ".mp3")

                    if skip and os.path.isfile(dst):
                        skipped += 1
                        emit("row", i=i, state="skip", title=name, sub="Već postoji · preskočeno")
                        continue

                    emit("row", i=i, state="active", title=name, sub="Niveliram glasnoću…")
                    emit("status", text=f"Niveliram: {name}")
                    meta = {"title": title, "artist": artist,
                            "album": info.get("album") or j["pl"] or "",
                            "track": str(j["idx"]) if j["idx"] else ""}
                    before = normalize_to_mp3(self._ffmpeg, src, dst, meta, lufs, -1.0, 11, bitrate)
                    ok += 1
                    b = f"{before:.1f}".replace(".", ",").replace("-", "−")
                    t = f"{lufs:.0f}".replace("-", "−")
                    emit("row", i=i, state="done", title=name, sub=f"{b} → {t} LUFS · {bitrate[:-1]} kbps")
                except Exception as e:
                    fail += 1
                    emit("row", i=i, state="error", sub=nice_error(e))
                finally:
                    if src and os.path.isfile(src):
                        try:
                            os.remove(src)
                        except OSError:
                            pass
            emit("progress", cur=total, done=total, total=total)
            emit("status", text=f"Gotovo — skinuto: {ok}, preskočeno: {skipped}, greške: {fail}",
                 color="green" if not fail else "accent")
        except Exception as e:
            emit("status", text=f"Neočekivana greška: {e}", color="red")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            self._running = False
            emit("done")


def main():
    import webview
    api = Api()
    win = webview.create_window(
        f"{APP_NAME} {APP_VERSION}", url=os.path.join(RES_DIR, "ui", "index.html"),
        js_api=api, width=1140, height=800, min_size=(1000, 720),
        background_color="#0E1014", text_select=True)
    api._window = win
    webview.start(http_server=True, private_mode=False,
                  storage_path=os.path.join(CONFIG_DIR, "webview"))


if __name__ == "__main__":
    main()
