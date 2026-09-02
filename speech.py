# -*- coding: utf-8 -*-
"""TTS multiplataforma (voz) para OCUPAMOR.

Estrategia por plataforma, con varios respaldos para que SIEMPRE suene:

- Android: TextToSpeech nativo (jnius).
- Windows: 1) SAPI por PowerShell (no necesita instalar nada)
           2) SAPI por COM (comtypes/win32com)
           3) pyttsx3 en proceso aparte
- macOS:   comando `say`
- Linux:   espeak-ng / espeak / spd-say / festival
- Ultimo respaldo: pyttsx3 y, si nada existe, se imprime el texto.

Todo se ejecuta en un hilo aparte para no congelar la interfaz de Kivy.
"""
import os
import sys
import shutil
import subprocess
import tempfile
import threading
import time

try:
    from kivy.utils import platform
except Exception:
    platform = "unknown"

_android_tts = None
_lock = threading.Lock()
_busy = threading.Event()      # hay voz sonando ahora mismo
_last_text = ""                # ultimo texto dicho (anti-repeticion)
_last_time = 0.0


# ------------------------------------------------------------------ Android
if platform == "android":
    try:
        from jnius import autoclass
        Locale = autoclass("java.util.Locale")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        TextToSpeech = autoclass("android.speech.tts.TextToSpeech")
        _android_tts = TextToSpeech(PythonActivity.mActivity, None)
        try:
            _android_tts.setLanguage(Locale("es", "ES"))
        except Exception:
            pass
        try:
            _android_tts.setSpeechRate(0.80)
            _android_tts.setPitch(1.0)
        except Exception:
            pass
    except Exception as e:
        print("[TTS] Android TTS no disponible:", e)
        _android_tts = None


def _no_window_kwargs():
    """Evita la ventana negra de consola en Windows."""
    kw = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            kw["startupinfo"] = si
            kw["creationflags"] = subprocess.CREATE_NO_WINDOW
        except Exception:
            pass
    return kw


# ------------------------------------------------------------------ Windows
def _ps_escape(text):
    return text.replace("'", "''")


def _win_powershell(text):
    """Voz con System.Speech (SAPI). Disponible en cualquier Windows."""
    exe = shutil.which("powershell") or shutil.which("pwsh")
    if not exe:
        return False
    script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Rate = -2; $s.Volume = 100; "
        "try { $v = $s.GetInstalledVoices() | "
        "Where-Object { $_.VoiceInfo.Culture.Name -like 'es*' } | "
        "Select-Object -First 1; "
        "if ($v) { $s.SelectVoice($v.VoiceInfo.Name) } } catch {}; "
        "$s.Speak('%s');" % _ps_escape(text)
    )
    try:
        r = subprocess.run(
            [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            timeout=60, **_no_window_kwargs()
        )
        return r.returncode == 0
    except Exception as e:
        print("[TTS] PowerShell no pudo hablar:", e)
        return False


def _win_com(text):
    """Voz con SAPI.SpVoice por COM."""
    try:
        try:
            import win32com.client as w32  # type: ignore
            voice = w32.Dispatch("SAPI.SpVoice")
        except Exception:
            import comtypes.client as cc  # type: ignore
            voice = cc.CreateObject("SAPI.SpVoice")
        try:
            voice.Rate = -2
            voice.Volume = 100
        except Exception:
            pass
        voice.Speak(text)
        return True
    except Exception as e:
        print("[TTS] SAPI COM no disponible:", e)
        return False


# ------------------------------------------------------------------ pyttsx3
_PYTTSX3_SCRIPT = '''# -*- coding: utf-8 -*-
import sys
import pyttsx3
text = sys.argv[1]
engine = pyttsx3.init()
try:
    engine.setProperty("rate", 130)
    engine.setProperty("volume", 1.0)
except Exception:
    pass
try:
    for v in engine.getProperty("voices"):
        name = (getattr(v, "name", "") or "").lower()
        vid = (getattr(v, "id", "") or "").lower()
        if "spanish" in name or "espa" in name or "es-" in vid or "es_" in vid:
            engine.setProperty("voice", v.id)
            break
except Exception:
    pass
engine.say(text)
engine.runAndWait()
'''


def _pyttsx3_subprocess(text):
    """pyttsx3 en un proceso separado (no bloquea ni se queda pegado)."""
    script_path = None
    try:
        fd, script_path = tempfile.mkstemp(suffix=".py")
        os.close(fd)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(_PYTTSX3_SCRIPT)
        r = subprocess.run(
            [sys.executable, script_path, text], timeout=60, **_no_window_kwargs()
        )
        return r.returncode == 0
    except Exception as e:
        print("[TTS] pyttsx3 subproceso fallo:", e)
        return False
    finally:
        if script_path:
            try:
                os.remove(script_path)
            except Exception:
                pass


def _pyttsx3_inline(text):
    """Ultimo recurso: pyttsx3 en este mismo proceso (dentro del hilo)."""
    try:
        import pyttsx3  # type: ignore
        engine = pyttsx3.init()
        try:
            engine.setProperty("rate", 130)
            engine.setProperty("volume", 1.0)
        except Exception:
            pass
        engine.say(text)
        engine.runAndWait()
        try:
            engine.stop()
        except Exception:
            pass
        return True
    except Exception as e:
        print("[TTS] pyttsx3 directo fallo:", e)
        return False


# ------------------------------------------------------------------ Unix
def _mac_say(text):
    exe = shutil.which("say")
    if not exe:
        return False
    try:
        r = subprocess.run([exe, "-r", "150", text], timeout=60,
                           **_no_window_kwargs())
        return r.returncode == 0
    except Exception:
        return False


def _linux_say(text):
    for cmd in (["espeak-ng", "-v", "es", "-s", "140"],
                ["espeak", "-v", "es", "-s", "140"],
                ["spd-say", "-l", "es", "-r", "-20"],
                ["festival", "--tts"]):
        exe = shutil.which(cmd[0])
        if not exe:
            continue
        try:
            if cmd[0] == "festival":
                p = subprocess.Popen([exe, "--tts"], stdin=subprocess.PIPE,
                                     **_no_window_kwargs())
                p.communicate(text.encode("utf-8"), timeout=60)
                return p.returncode == 0
            r = subprocess.run([exe] + cmd[1:] + [text], timeout=60,
                               **_no_window_kwargs())
            if r.returncode == 0:
                return True
        except Exception:
            continue
    return False


# ------------------------------------------------------------------ API
def _speak_blocking(text):
    if os.name == "nt":
        backends = (_win_powershell, _win_com, _pyttsx3_subprocess,
                    _pyttsx3_inline)
    elif sys.platform == "darwin":
        backends = (_mac_say, _pyttsx3_subprocess, _pyttsx3_inline)
    else:
        backends = (_linux_say, _pyttsx3_subprocess, _pyttsx3_inline)

    for backend in backends:
        try:
            if backend(text):
                return True
        except Exception as e:
            print("[TTS] Error en", backend.__name__, ":", e)
    print("[TTS] Sin voz disponible. Texto:", text)
    return False


def is_speaking():
    """Indica si en este momento hay una voz sonando."""
    return _busy.is_set()


def say(text):
    """Dice el texto en voz alta sin bloquear la interfaz.

    Protecciones para que la voz NUNCA se quede pegada ni se repita:
    - Si ya hay una voz sonando, la peticion nueva se ignora.
    - Si se repite el mismo texto en menos de 1.5 s, se ignora.
    """
    text = str(text).strip()
    if not text:
        return

    global _last_text, _last_time
    now = time.time()
    if text == _last_text and (now - _last_time) < 1.5:
        return
    if _busy.is_set():
        return
    _last_text, _last_time = text, now
    print("[TTS] Diciendo:", text)

    # Android: TTS nativo (ya es asincrono)
    if _android_tts is not None:
        try:
            try:
                _android_tts.stop()
            except Exception:
                pass
            _android_tts.speak(text, 0, None)
            return
        except Exception as e:
            print("[TTS] Error Android:", e)

    _busy.set()

    def worker():
        # Un solo audio a la vez: evita voces encimadas
        try:
            with _lock:
                _speak_blocking(text)
        finally:
            _busy.clear()

    threading.Thread(target=worker, daemon=True).start()



def stop():
    """Detiene la voz en Android (en escritorio termina sola)."""
    if _android_tts is not None:
        try:
            _android_tts.stop()
        except Exception:
            pass
