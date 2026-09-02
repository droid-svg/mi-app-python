# -*- coding: utf-8 -*-
"""
OCUPAMOR Mobile — Kivy (MEJORADO)
=================================
Software educativo de soporte lingüístico y fonético con disminución
sensorial, adaptado para teléfonos (Android / iOS / escritorio).

MEJORAS:
- Misiones ahora tienen panel de juego interactivo
- Botones de audio usan imagen de corneta en vez de texto
- Etapa Inicial separada en sub-paneles con imágenes
- Calma Sensorial con imágenes de niño respirando/exhalando
"""
import random
import os

from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.graphics import (Color, Ellipse, Rectangle, RoundedRectangle, Line,
                           Triangle)
from kivy.animation import Animation

import auth
import speech
import data_store as ds
from config import THEMES, APP_TITLE, LEARNING_CATEGORIES
import content as C
import abecedario_data as ABC

# Ventana estilo teléfono en escritorio (en móvil se respeta la pantalla)
try:
    if Window is not None and "Android" not in Window.__class__.__name__:
        Window.size = (400, 720)
        Window.minimum_width, Window.minimum_height = 360, 600
except Exception as _e:
    print("[UI] No se pudo ajustar la ventana:", _e)

STATE = {
    "mode": "escolar",   # unico tema disponible
    "user": None,
    "sensory_used": False,
    "session": {"total": 0, "correct": 0},
}

# Directorio de imágenes (relativo al proyecto)
IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "images")
os.makedirs(IMG_DIR, exist_ok=True)


def theme():
    return THEMES["escolar"]


# ---------------------------------------------------------------- widgets utils
class RoundedBox(BoxLayout):
    """Tarjeta con esquinas redondeadas (nada de cuadrados duros)."""

    def __init__(self, bg=(1, 1, 1, 1), radius=22, border=None, **kw):
        super().__init__(**kw)
        self.bg = bg
        self.border = border
        rad = list(radius) if isinstance(radius, (list, tuple)) else [radius] * 4
        self.radius = rad
        with self.canvas.before:
            self._c = Color(*bg)
            self._r = RoundedRectangle(pos=self.pos, size=self.size, radius=rad)
            self._bc = Color(*(border or (0, 0, 0, 0)))
            self._bl = Line(width=1.2,
                            rounded_rectangle=(0, 0, 1, 1, max(rad)))
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._r.pos = self.pos
        self._r.size = self.size
        self._bl.rounded_rectangle = (self.x, self.y, self.width,
                                      self.height, max(self.radius))

    def set_bg(self, bg):
        self.bg = bg
        self._c.rgba = bg


class RoundedButton(Button):
    """Boton redondeado con respuesta tactil suave (sin destellos)."""

    def __init__(self, bg=(0.1, 0.4, 0.75, 1), radius=20, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_down", "")
        super().__init__(**kw)
        self.background_color = (0, 0, 0, 0)
        self._bg = list(bg)
        self.radius = radius
        with self.canvas.before:
            self._c = Color(*self._bg)
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                       radius=[radius] * 4)
        self.bind(pos=self._sync, size=self._sync, state=self._on_state)

    def _sync(self, *_):
        self._r.pos = self.pos
        self._r.size = self.size

    def _on_state(self, _w, state):
        if state == "down":
            self._c.rgba = [max(0.0, v * 0.88) for v in self._bg[:3]] + [self._bg[3]]
        else:
            self._c.rgba = self._bg

    def set_bg(self, bg):
        self._bg = list(bg)
        self._c.rgba = self._bg


def fade_in(widget, delay=0.0):
    """Animacion de entrada suave: nada brusco ni parpadeante."""
    widget.opacity = 0
    anim = Animation(opacity=1, duration=0.28, t="out_quad")
    Clock.schedule_once(lambda *_: anim.start(widget), max(0.0, delay))
    return widget


def stagger_in(widgets, step=0.045, start=0.02):
    for i, w in enumerate(widgets):
        fade_in(w, start + i * step)


def soft_pulse(widget):
    """Latido muy leve para confirmar una accion (calmado)."""
    try:
        Animation.cancel_all(widget, "opacity")
    except Exception:
        pass
    (Animation(opacity=0.6, duration=0.16, t="out_quad") +
     Animation(opacity=1.0, duration=0.22, t="out_quad")).start(widget)


class SpeakerIcon(Widget):
    """Bocina dibujada con vectores (no depende de fuentes ni emojis)."""

    def __init__(self, color=(1, 1, 1, 1), **kw):
        super().__init__(**kw)
        self.icon_color = color
        with self.canvas:
            self._c = Color(*color)
            self._body = Rectangle()
            self._cone = Triangle(points=[0, 0, 0, 0, 0, 0])
            self._w1 = Line(width=1.6)
            self._w2 = Line(width=1.6)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        s = min(self.width, self.height)
        cx = self.center_x - s * 0.10
        cy = self.center_y
        self._body.pos = (cx - s * 0.34, cy - s * 0.14)
        self._body.size = (s * 0.20, s * 0.28)
        self._cone.points = [
            cx - s * 0.16, cy - s * 0.30,
            cx - s * 0.16, cy + s * 0.30,
            cx + s * 0.06, cy,
        ]
        self._w1.circle = (cx + s * 0.02, cy, s * 0.24, 30, 150)
        self._w2.circle = (cx + s * 0.02, cy, s * 0.38, 35, 145)


class GlyphBadge(AnchorLayout):
    """Circulo con iniciales (reemplaza emojis que no existen en Windows)."""

    def __init__(self, text="", fg=(1, 1, 1, 1), diameter="52dp", **kw):
        kw.setdefault("size_hint_y", None)
        super().__init__(**kw)
        self.height = diameter
        circle = RoundedBox(bg=(*fg[:3], 0.22), radius=999,
                            size_hint=(None, None),
                            size=(diameter, diameter))
        lbl = Label(text=text, color=fg, bold=True, font_size="17sp",
                    halign="center", valign="middle")
        lbl.bind(size=lambda i, s: setattr(i, "text_size", s))
        circle.add_widget(lbl)
        self.add_widget(circle)



def AudioButton(source, on_press_callback, size=(64, 64), color=None,
                label="Escuchar"):
    """Boton de audio en forma de pastilla, con corneta y texto.

    Se dibuja la bocina con vectores (siempre se ve bien, aunque falte la
    imagen) y si existe `source` se usa esa imagen como icono.
    """
    t = theme()
    btn = RoundedButton(
        bg=color or t["primary"],
        radius=26,
        text="",
        size_hint=(None, None),
        size=("164dp", "52dp"),
    )

    row = BoxLayout(orientation="horizontal", spacing=8,
                    padding=[14, 8, 16, 8],
                    size_hint=(None, None), size=btn.size)

    has_img = bool(source) and os.path.exists(source)
    if has_img:
        icon = Image(source=source, size_hint=(None, 1), width="26dp",
                     allow_stretch=True, keep_ratio=True)
    else:
        icon = SpeakerIcon(color=t["white"], size_hint=(None, 1),
                           width="26dp")
    row.add_widget(icon)

    txt = Label(text=label, color=t["white"], bold=True, font_size="15sp",
                halign="left", valign="middle")
    txt.bind(size=lambda i, s: setattr(i, "text_size", s))
    row.add_widget(txt)
    btn.add_widget(row)

    def _sync_row(b, *_):
        row.size = b.size
        row.pos = b.pos
    btn.bind(pos=_sync_row, size=_sync_row)

    if on_press_callback:
        btn.bind(on_release=lambda *_: on_press_callback())
    return btn



def PrimaryButton(text, on_press=None, color=None, fg=None, big=False):
    t = theme()
    b = RoundedButton(
        bg=color or t["primary"],
        radius=22,
        text=text,
        color=fg or t["white"],
        font_size="18sp" if big else "15sp",
        bold=True,
        size_hint_y=None,
        height="58dp" if big else "48dp",
    )
    if on_press:
        b.bind(on_release=lambda *_: on_press())
    return b


def SoftLabel(text, size="15sp", bold=False, color=None, halign="left"):
    t = theme()
    lbl = Label(
        text=text, font_size=size, bold=bold,
        color=color or t["text"],
        halign=halign, valign="middle",
        size_hint_y=None,
    )
    lbl.bind(width=lambda i, w: setattr(i, "text_size", (w, None)))
    lbl.bind(texture_size=lambda i, s: setattr(i, "height", s[1] + 6))
    return lbl


def apply_bg(screen):
    """Pinta el fondo del screen con el color del tema actual."""
    t = theme()
    if not hasattr(screen, '_bg_initialized'):
        with screen.canvas.before:
            screen._bg_color_inst = Color(*t["bg"])
            screen._bg_rect_inst = Rectangle(pos=screen.pos, size=screen.size)
        screen.bind(pos=lambda *_: setattr(screen._bg_rect_inst, "pos", screen.pos),
                    size=lambda *_: setattr(screen._bg_rect_inst, "size", screen.size))
        screen._bg_initialized = True
    else:
        screen._bg_color_inst.rgba = t["bg"]
        screen._bg_rect_inst.pos = screen.pos
        screen._bg_rect_inst.size = screen.size


def show_toast(msg, title="OCUPAMOR"):
    lbl = Label(text=msg, font_size="15sp")
    p = Popup(title=title, content=lbl,
              size_hint=(0.85, 0.35))
    p.open()
    Clock.schedule_once(lambda *_: p.dismiss(), 1.8)


# ---------------------------------------------------------------- base screen
class BaseScreen(Screen):
    """Pantalla con encabezado y botón volver."""
    title_text = "OCUPAMOR"
    subtitle_text = ""
    show_back = True

    def on_pre_enter(self, *_):
        self.clear_widgets()
        apply_bg(self)
        root = BoxLayout(orientation="vertical")
        root.add_widget(self._header())
        body = BoxLayout(orientation="vertical", padding=[16, 12, 16, 16],
                         spacing=10)
        root.add_widget(body)
        self.add_widget(root)
        self.body = body
        self.build()
        stagger_in(list(body.children)[::-1])

    def _header(self):
        t = theme()
        bar = RoundedBox(bg=t["primary"], radius=[0, 0, 26, 26],
                         orientation="horizontal",
                         size_hint_y=None, height="78dp",
                         padding=[14, 10, 14, 14], spacing=10)
        if self.show_back:
            back = RoundedButton(bg=t["primary_dark"], radius=18,
                                 text="<", color=t["white"], bold=True,
                                 font_size="18sp",
                                 size_hint=(None, None), size=("44dp", "44dp"),
                                 pos_hint={"center_y": 0.5})
            back.bind(on_release=lambda *_: self.go_back())
            bar.add_widget(back)
        tx = BoxLayout(orientation="vertical")
        title = Label(text=self.title_text, color=t["white"], bold=True,
                      font_size="18sp", halign="left", valign="middle")
        title.bind(size=lambda i, s: setattr(i, "text_size", s))
        tx.add_widget(title)
        if self.subtitle_text:
            st = Label(text=self.subtitle_text, color=t["white"],
                       font_size="12sp", halign="left", valign="middle")
            st.bind(size=lambda i, s: setattr(i, "text_size", s))
            tx.add_widget(st)
        bar.add_widget(tx)
        return bar

    def go_back(self):
        sm = App.get_running_app().sm
        sm.transition = SlideTransition(direction="right")
        sm.current = "menu"

    def build(self):
        pass


# ---------------------------------------------------------------- login
class LoginScreen(Screen):
    def on_pre_enter(self, *_):
        self.clear_widgets()
        apply_bg(self)
        t = theme()

        outer = BoxLayout(orientation="vertical")

        # Encabezado curvo con la marca
        head = RoundedBox(bg=t["primary"], radius=[0, 0, 34, 34],
                          orientation="vertical", size_hint_y=None,
                          height="150dp", padding=[24, 26, 24, 20], spacing=2)
        brand = Label(text="OCUPAMOR", color=t["white"], bold=True,
                      font_size="32sp", halign="left", valign="middle",
                      size_hint_y=None, height="46dp")
        brand.bind(size=lambda i, s: setattr(i, "text_size", s))
        head.add_widget(brand)
        claim = Label(text="Aprendiendo con calma", color=(1, 1, 1, 0.9),
                      font_size="14sp", halign="left", valign="top",
                      size_hint_y=None, height="24dp")
        claim.bind(size=lambda i, s: setattr(i, "text_size", s))
        head.add_widget(claim)
        outer.add_widget(head)

        scroll = ScrollView(bar_width=4)
        wrap = BoxLayout(orientation="vertical", padding=[20, 18, 20, 20],
                         spacing=14, size_hint_y=None)
        wrap.bind(minimum_height=wrap.setter("height"))

        card = RoundedBox(bg=t["card"], radius=26, orientation="vertical",
                          padding=[18, 18, 18, 18], spacing=10,
                          size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))
        card.add_widget(SoftLabel("Entra o crea tu cuenta", bold=True,
                                  size="17sp"))
        card.add_widget(SoftLabel(
            "El nombre y el rol solo se necesitan al registrarte.",
            size="12sp", color=t["text_soft"]))

        def field(label, widget):
            card.add_widget(SoftLabel(label, bold=True, size="13sp"))
            holder = RoundedBox(bg=t["white"], radius=16, border=t["line"],
                                padding=[10, 4, 10, 4], size_hint_y=None,
                                height="52dp")
            holder.add_widget(widget)
            card.add_widget(holder)

        _in = dict(multiline=False, background_normal="", background_active="",
                   background_color=(0, 0, 0, 0), foreground_color=t["text"],
                   cursor_color=t["primary"], font_size="15sp",
                   padding=[6, 12, 6, 6])
        self.email = TextInput(hint_text="correo@ejemplo.com", **_in)
        self.pwd = TextInput(hint_text="Mínimo 6 caracteres",
                             password=True, **_in)
        self.name_input = TextInput(hint_text="¿Cómo te llamas?", **_in)
        self.role = Spinner(text="representante",
                            values=("representante", "docente",
                                    "terapeuta", "tutor"),
                            size_hint_y=None, height="46dp",
                            background_normal="", background_down="",
                            background_color=t["soft"], color=t["text"],
                            font_size="15sp")

        field("Correo", self.email)
        field("Contraseña", self.pwd)
        field("Nombre", self.name_input)
        card.add_widget(SoftLabel("Rol", bold=True, size="13sp"))
        card.add_widget(self.role)

        card.add_widget(Widget(size_hint_y=None, height="6dp"))
        card.add_widget(PrimaryButton("Iniciar sesión", self.do_login,
                                      big=True))
        card.add_widget(PrimaryButton("Crear cuenta nueva", self.do_register,
                                      color=t["secondary"]))
        wrap.add_widget(card)

        backend = "Cuenta en línea conectada" if auth.is_supabase_enabled() \
            else "Modo local (funciona sin internet)"
        note = RoundedBox(bg=t["soft"], radius=18, padding=[12, 10, 12, 10],
                          size_hint_y=None, height="42dp")
        note.add_widget(SoftLabel(backend, size="12sp",
                                  color=t["text_soft"], halign="center"))
        wrap.add_widget(note)

        scroll.add_widget(wrap)
        outer.add_widget(scroll)
        self.add_widget(outer)
        stagger_in([head, card, note])


    def do_login(self):
        ok, msg, user = auth.login(self.email.text, self.pwd.text)
        show_toast(msg)
        if ok:
            STATE["user"] = user
            app = App.get_running_app()
            app.sm.transition = SlideTransition(direction="left")
            app.sm.current = "menu"

    def do_register(self):
        ok, msg = auth.register(self.email.text, self.pwd.text,
                                self.name_input.text, self.role.text)
        show_toast(msg)


# ---------------------------------------------------------------- menu
class MenuScreen(BaseScreen):
    title_text = "OCUPAMOR"
    show_back = False

    def build(self):
        t = theme()
        u = STATE["user"] or {"name": "amig@", "role": "representante"}
        self.subtitle_text = f"Bienvenido, {u['name']}"
        self.body.add_widget(SoftLabel("Elige una actividad",
                                       size="18sp", bold=True))

        scroll = ScrollView(bar_width=4)
        grid = GridLayout(cols=2, spacing=14, padding=[0, 6],
                          size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        items = [
            ("Etapa Inicial", "Letras, colores y primeras palabras",
             "inicial_hub", t["secondary"], "01_etapa_inicial.png"),
            ("Abecedario", "De la A a la Z con dibujos",
             "abecedario", t["primary"], "02_abecedario.png"),
            ("Matemáticas", "Números, sumas y figuras",
             "matematicas", t["primary_dark"], "03_matematicas.png"),
            ("Etapa Avanzada", "Lectura y ejercicios más largos",
             "avanzada", t["accent"], "04_etapa_avanzada.png"),
            ("Calma Sensorial", "Respirar y bajar revoluciones",
             "calma", t["calm"], "05_calma_sensorial.png"),
            ("Señas y Comunicación", "Aprender a pedir y responder",
             "senas", t["primary"], "06_senas_comunicacion.png"),
            ("Emociones", "Reconocer cómo me siento",
             "emociones", t["secondary"], "07_emociones.png"),
            ("Misiones", "Retos cortos del día",
             "misiones", t["accent"], "08_misiones.png"),
            ("Mi Progreso", "Lo que ya lograste",
             "progress", t["primary"], "09_mi_progreso.png"),
            ("Configuración", "Ajustes de la aplicación",
             "settings", t["calm"], "10_configuracion.png"),
        ]
        if u.get("role") in ("representante", "docente", "terapeuta", "tutor"):
            items.append(("Panel del Adulto", "Seguimiento y reportes",
                          "dashboard", t["primary_dark"], "11_panel_adulto.png"))

        cards = []
        for txt, desc, target, col, icon in items:
            fg = t["text"] if col == t["accent"] else t["white"]
            card = RoundedBox(bg=col, radius=24, orientation="vertical",
                              size_hint_y=None, height="188dp",
                              padding=[12, 14, 12, 12], spacing=2)

            # Icono ilustrado de la actividad
            icon_path = os.path.join(IMG_DIR, "menu", icon)
            if os.path.exists(icon_path):
                holder = AnchorLayout(size_hint_y=None, height="86dp")
                holder.add_widget(Image(source=icon_path, size_hint=(None, 1),
                                        width="86dp", allow_stretch=True,
                                        keep_ratio=True))
                card.add_widget(holder)
            else:
                card.add_widget(GlyphBadge(txt[:3], fg=fg, diameter="52dp"))



            card.add_widget(Label(text=txt, color=fg, bold=True,
                                  font_size="15sp", halign="center",
                                  valign="middle",
                                  size_hint_y=None, height="38dp",
                                  text_size=(None, None)))
            sub = Label(text=desc, color=(*fg[:3], 0.85), font_size="11sp",
                        halign="center", valign="top")
            sub.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            card.add_widget(sub)

            def on_touch(instance, touch, tg=target):
                if instance.collide_point(*touch.pos):
                    soft_pulse(instance)
                    Clock.schedule_once(lambda *_: self.go(tg), 0.12)
                    return True
            card.bind(on_touch_down=on_touch)
            cards.append(card)
            grid.add_widget(card)

        scroll.add_widget(grid)
        self.body.add_widget(scroll)
        stagger_in(cards, step=0.04)

        logout = PrimaryButton("Cerrar sesión", lambda: self.logout(),
                               color=t["card"], fg=t["text"])
        self.body.add_widget(logout)

    def go(self, name):
        sm = App.get_running_app().sm
        sm.transition = SlideTransition(direction="left")
        sm.current = name

    def logout(self):
        STATE["user"] = None
        sm = App.get_running_app().sm
        sm.transition = SlideTransition(direction="right")
        sm.current = "login"


# =============================================================================
# NUEVO: HUB DE ETAPA INICIAL (sub-paneles)
# =============================================================================
class InicialHubScreen(BaseScreen):
    title_text = "Etapa Inicial"
    subtitle_text = "Elige un área de aprendizaje"

    def build(self):
        t = theme()
        self.body.add_widget(SoftLabel("¿Qué quieres aprender hoy?",
                                       size="16sp", bold=True))

        scroll = ScrollView()
        col = BoxLayout(orientation="vertical", spacing=14,
                        size_hint_y=None, padding=[0, 4])
        col.bind(minimum_height=col.setter("height"))

        # Panel 1: Abecedario con imágenes
        card1 = RoundedBox(bg=t["card"], orientation="vertical",
                           padding=[16, 14, 16, 14], size_hint_y=None, spacing=8)
        card1.bind(minimum_height=card1.setter("height"))
        card1.add_widget(SoftLabel("Abecedario", bold=True, size="17sp"))
        card1.add_widget(SoftLabel("Letras del alfabeto con dibujos para identificar",
                                   size="13sp", color=t["text_soft"]))
        # Preview de letras
        preview = BoxLayout(orientation="horizontal", spacing=6, size_hint_y=None, height="60dp")
        for letter, emoji in [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]:
            cell = RoundedBox(bg=t["primary"], size_hint_x=None, width="56dp",
                              orientation="vertical", padding=[4, 4, 4, 4])
            cell.add_widget(Label(text=emoji, font_size="22sp"))
            cell.add_widget(Label(text=letter, color=t["white"], bold=True, font_size="14sp"))
            preview.add_widget(cell)
        card1.add_widget(preview)
        btn1 = PrimaryButton("Ir al Abecedario", lambda: self.go("abecedario"),
                             color=t["secondary"], big=True)
        card1.add_widget(btn1)
        col.add_widget(card1)

        # Panel 2: Monosílabas con imágenes
        card2 = RoundedBox(bg=t["card"], orientation="vertical",
                           padding=[16, 14, 16, 14], size_hint_y=None, spacing=8)
        card2.bind(minimum_height=card2.setter("height"))
        card2.add_widget(SoftLabel("Monosílabas", bold=True, size="17sp"))
        card2.add_widget(SoftLabel("ma, me, mi, mo, mu... con imágenes",
                                   size="13sp", color=t["text_soft"]))
        preview2 = BoxLayout(orientation="horizontal", spacing=6, size_hint_y=None, height="60dp")
        for syl, emoji in [("ma", "ma"), ("me", "me"), ("mi", "mi"), ("mo", "mo")]:
            cell = RoundedBox(bg=t["secondary"], size_hint_x=None, width="56dp",
                              orientation="vertical", padding=[4, 4, 4, 4])
            cell.add_widget(Label(text=emoji, font_size="22sp"))
            cell.add_widget(Label(text=syl, color=t["text"], bold=True, font_size="13sp"))
            preview2.add_widget(cell)
        card2.add_widget(preview2)
        btn2 = PrimaryButton("Ir a Monosílabas", lambda: self.go("monosilabas"),
                             color=t["accent"], fg=t["text"], big=True)
        card2.add_widget(btn2)
        col.add_widget(card2)

        # Panel 3: Sílabas
        card3 = RoundedBox(bg=t["card"], orientation="vertical",
                           padding=[16, 14, 16, 14], size_hint_y=None, spacing=8)
        card3.bind(minimum_height=card3.setter("height"))
        card3.add_widget(SoftLabel("Sílabas", bold=True, size="17sp"))
        card3.add_widget(SoftLabel("Todas las sílabas para practicar",
                                   size="13sp", color=t["text_soft"]))
        preview3 = BoxLayout(orientation="horizontal", spacing=6, size_hint_y=None, height="50dp")
        for s in ["sa", "se", "si", "so", "su"]:
            lbl = Label(text=s, font_size="18sp", bold=True, color=t["primary"],
                        size_hint_x=None, width="50dp")
            preview3.add_widget(lbl)
        card3.add_widget(preview3)
        btn3 = PrimaryButton("Ir a Sílabas", lambda: self.go("silabas"),
                             color=t["primary"], big=True)
        card3.add_widget(btn3)
        col.add_widget(card3)

        # Panel 4: Vocabulario con imágenes
        card4 = RoundedBox(bg=t["card"], orientation="vertical",
                           padding=[16, 14, 16, 14], size_hint_y=None, spacing=8)
        card4.bind(minimum_height=card4.setter("height"))
        card4.add_widget(SoftLabel("Vocabulario", bold=True, size="17sp"))
        card4.add_widget(SoftLabel("Palabras con dibujos para identificar",
                                   size="13sp", color=t["text_soft"]))
        preview4 = BoxLayout(orientation="horizontal", spacing=6, size_hint_y=None, height="60dp")
        for emo, pal in [("G", "gato"), ("C", "casa"), ("S", "sol"), ("L", "luna")]:
            cell = RoundedBox(bg=t["accent"], size_hint_x=None, width="56dp",
                              orientation="vertical", padding=[4, 4, 4, 4])
            cell.add_widget(Label(text=emo, font_size="22sp"))
            cell.add_widget(Label(text=pal, color=t["text"], bold=True, font_size="11sp"))
            preview4.add_widget(cell)
        card4.add_widget(preview4)
        btn4 = PrimaryButton("Ir a Vocabulario", lambda: self.go("vocabulario"),
                             color=t["calm"], big=True)
        card4.add_widget(btn4)
        col.add_widget(card4)

        scroll.add_widget(col)
        self.body.add_widget(scroll)

    def go(self, name):
        sm = App.get_running_app().sm
        sm.transition = SlideTransition(direction="left")
        sm.current = name


# =============================================================================
# ABECEDARIO ILUSTRADO (A - Z, dos colecciones con imagenes reales)
# =============================================================================
ABC_DIR = os.path.join(IMG_DIR, "abecedario")


class AbecedarioScreen(BaseScreen):
    title_text = "Abecedario"
    subtitle_text = "De la A a la Z con dibujos"

    current_set = "comida"

    def build(self):
        t = theme()
        self.body.add_widget(SoftLabel(
            "Toca una tarjeta para escuchar la letra y su palabra.",
            size="13sp", color=t["text_soft"]))

        chooser = BoxLayout(orientation="horizontal", spacing=10,
                            size_hint_y=None, height="46dp")
        self._chips = {}
        for s in ABC.SETS:
            activo = s["key"] == self.current_set
            chip = RoundedButton(
                bg=t["primary"] if activo else t["soft"],
                radius=23, text=s["titulo"],
                color=t["white"] if activo else t["text"],
                bold=True, font_size="13sp")
            chip.bind(on_release=lambda _b, k=s["key"]: self.switch_set(k))
            self._chips[s["key"]] = chip
            chooser.add_widget(chip)
        self.body.add_widget(chooser)

        self.grid_holder = BoxLayout(orientation="vertical")
        self.body.add_widget(self.grid_holder)
        self._render_grid()

    def switch_set(self, key):
        if key == self.current_set:
            return
        self.current_set = key
        t = theme()
        for k, chip in self._chips.items():
            activo = (k == key)
            chip.set_bg(t["primary"] if activo else t["soft"])
            chip.color = t["white"] if activo else t["text"]
        self._render_grid()

    def _render_grid(self):
        t = theme()
        self.grid_holder.clear_widgets()
        data = ABC.get_set(self.current_set)

        scroll = ScrollView(bar_width=4)
        grid = GridLayout(cols=2, spacing=14, padding=[6, 10, 6, 10],
                          size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        tints = [t["soft"], t["soft_2"], t["soft_3"]]
        cards = []
        for i, (letra, palabra, img) in enumerate(data["items"]):
            card = RoundedBox(bg=tints[i % 3], radius=20, border=t["line"],
                              orientation="vertical", size_hint_y=None,
                              height="286dp", padding=[10, 10, 10, 10],
                              spacing=6)
            path = os.path.join(ABC_DIR, img.replace("/", os.sep))
            if os.path.exists(path):
                card.add_widget(Image(source=path, allow_stretch=True,
                                      keep_ratio=True, size_hint_y=None,
                                      height="196dp"))
            else:
                card.add_widget(Label(text=letra, font_size="72sp",
                                      color=t["primary"],
                                      size_hint_y=None, height="196dp"))
            card.add_widget(Label(text=letra, color=t["primary"], bold=True,
                                  font_size="26sp",
                                  size_hint_y=None, height="34dp"))
            card.add_widget(Label(text=palabra, color=t["text_soft"],
                                  font_size="15sp",
                                  size_hint_y=None, height="26dp"))

            def on_touch(instance, touch, l=letra, p=palabra, ip=path):
                if instance.collide_point(*touch.pos):
                    soft_pulse(instance)
                    speech.say(f"{l}, de {p}")
                    self._record("vocales")
                    self.open_detail(l, p, ip)
                    return True
            card.bind(on_touch_down=on_touch)
            cards.append(card)
            grid.add_widget(card)

        scroll.add_widget(grid)
        self.grid_holder.add_widget(scroll)
        stagger_in(cards, step=0.02)

    def open_detail(self, letra, palabra, img_path):
        """Ficha grande de la letra, tranquila y sin ruido visual."""
        t = theme()
        box = RoundedBox(bg=t["card"], radius=24, orientation="vertical",
                         padding=[16, 16, 16, 16], spacing=10)
        if os.path.exists(img_path):
            box.add_widget(Image(source=img_path, allow_stretch=True,
                                 keep_ratio=True))
        box.add_widget(Label(text=f"{letra} {letra.lower()}",
                             color=t["primary"], bold=True, font_size="34sp",
                             size_hint_y=None, height="46dp"))
        box.add_widget(Label(text=palabra, color=t["text"], bold=True,
                             font_size="20sp", size_hint_y=None, height="30dp"))

        row = BoxLayout(orientation="horizontal", spacing=10,
                        size_hint_y=None, height="52dp")
        row.add_widget(PrimaryButton("Oir la letra",
                                     lambda: speech.say(letra),
                                     color=t["secondary"]))
        row.add_widget(PrimaryButton("Oir la palabra",
                                     lambda: speech.say(palabra),
                                     color=t["calm"]))
        box.add_widget(row)

        popup = Popup(title="", separator_height=0, content=box,
                      background_color=(0, 0, 0, 0.35),
                      size_hint=(0.9, 0.8), auto_dismiss=True)
        box.add_widget(PrimaryButton("Cerrar", lambda: popup.dismiss(),
                                     color=t["primary"]))
        popup.open()
        fade_in(box, 0.0)

    def _record(self, cat):
        u = STATE["user"]
        if u:
            ds.record_activity(u["email"], cat, True)
        STATE["session"]["total"] += 1
        STATE["session"]["correct"] += 1


# =============================================================================
# NUEVO: MONOSÍLABAS CON IMÁGENES
# =============================================================================
class MonosilabasScreen(BaseScreen):
    title_text = "Monosílabas"
    subtitle_text = "Sílabas simples con dibujos"

    # Monosílabas con emojis representativos
    MONOSILABAS = [
        ("ma", "MA", "mama"), ("me", "ME", "miel"), ("mi", "MI", "raton"),
        ("mo", "MO", "manzana"), ("mu", "MU", "vaca"),
        ("pa", "PA", "papa"), ("pe", "PE", "pie"), ("pi", "PI", "pastel"),
        ("po", "PO", "pollo"), ("pu", "PU", "puno"),
        ("sa", "SA", "sal"), ("se", "SE", "silla"), ("si", "SI", "si"),
        ("so", "SO", "sueno"), ("su", "SU", "calcetin"),
        ("la", "LA", "leche"), ("le", "LE", "leon"), ("li", "LI", "libro"),
        ("lo", "LO", "lobo"), ("lu", "LU", "luna"),
    ]

    def build(self):
        t = theme()
        self.body.add_widget(SoftLabel(
            "Toca una sílaba para escucharla. Toca el dibujo para la palabra.",
            size="13sp", color=t["text_soft"]))

        scroll = ScrollView()
        grid = GridLayout(cols=3, spacing=10, padding=[4, 4],
                          size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for syl, emoji, palabra in self.MONOSILABAS:
            card = RoundedBox(bg=t["card"], orientation="vertical",
                              size_hint_y=None, height="140dp",
                              padding=[8, 8, 8, 8], spacing=4)

            card.add_widget(Label(text=emoji, font_size="40sp",
                                  size_hint_y=None, height="56dp"))
            card.add_widget(Label(text=syl, color=t["secondary"],
                                  bold=True, font_size="22sp",
                                  size_hint_y=None, height="32dp"))
            card.add_widget(Label(text=palabra, color=t["text_soft"],
                                  font_size="12sp",
                                  size_hint_y=None, height="20dp"))

            audio_btn = self._make_audio_btn(syl)
            card.add_widget(audio_btn)

            def on_touch(instance, touch, s=syl, p=palabra):
                if instance.collide_point(*touch.pos):
                    speech.say(f"{s} como en {p}")
                    self._record("silabas")
            card.bind(on_touch_down=on_touch)
            grid.add_widget(card)

        scroll.add_widget(grid)
        self.body.add_widget(scroll)

    def _make_audio_btn(self, text_to_say):
        t = theme()
        corneta_path = os.path.join(IMG_DIR, "corneta.png")
        def on_play():
            speech.say(text_to_say)
            self._record("silabas")
        return AudioButton(corneta_path, on_play, size=(64, 64), color=t["secondary"])

    def _record(self, cat):
        u = STATE["user"]
        if u:
            ds.record_activity(u["email"], cat, True)
        STATE["session"]["total"] += 1
        STATE["session"]["correct"] += 1


# =============================================================================
# NUEVO: PANTALLA DE SÍLABAS (todas)
# =============================================================================
class SilabasScreen(BaseScreen):
    title_text = "Sílabas"
    subtitle_text = "Todas las sílabas"

    def build(self):
        t = theme()
        self.body.add_widget(SoftLabel(
            "Toca una sílaba para escucharla", size="14sp"))

        scroll = ScrollView()
        grid = GridLayout(cols=5, spacing=8, padding=[4, 4],
                          size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for s in C.SILABAS:
            card = RoundedBox(bg=t["secondary"], orientation="vertical",
                              size_hint_y=None, height="80dp",
                              padding=[6, 6, 6, 6])
            lbl = Label(text=s, color=t["text"], bold=True, font_size="20sp")
            card.add_widget(lbl)

            def on_touch(instance, touch, x=s):
                if instance.collide_point(*touch.pos):
                    speech.say(x)
                    self._record("silabas")
            card.bind(on_touch_down=on_touch)
            grid.add_widget(card)

        scroll.add_widget(grid)
        self.body.add_widget(scroll)

    def _record(self, cat):
        u = STATE["user"]
        if u:
            ds.record_activity(u["email"], cat, True)
        STATE["session"]["total"] += 1
        STATE["session"]["correct"] += 1


# =============================================================================
# NUEVO: PANTALLA DE VOCABULARIO (con imágenes)
# =============================================================================
class VocabularioScreen(BaseScreen):
    title_text = "Vocabulario"
    subtitle_text = "Palabras con dibujos"

    def build(self):
        t = theme()
        self.body.add_widget(SoftLabel(
            "Toca una palabra para escucharla", size="14sp"))

        scroll = ScrollView()
        grid = GridLayout(cols=2, spacing=10, padding=[4, 4],
                          size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for emo, pal in C.PALABRAS:
            card = RoundedBox(bg=t["card"], orientation="vertical",
                              size_hint_y=None, height="160dp",
                              padding=[10, 10, 10, 10], spacing=6)

            card.add_widget(Label(text=emo, font_size="50sp",
                                  size_hint_y=None, height="70dp"))
            card.add_widget(Label(text=pal, color=t["text"], bold=True,
                                  font_size="16sp",
                                  size_hint_y=None, height="28dp"))

            audio_btn = self._make_audio_btn(pal)
            card.add_widget(audio_btn)

            def on_touch(instance, touch, p=pal):
                if instance.collide_point(*touch.pos):
                    speech.say(p)
                    self._record("vocabulario")
            card.bind(on_touch_down=on_touch)
            grid.add_widget(card)

        scroll.add_widget(grid)
        self.body.add_widget(scroll)

    def _make_audio_btn(self, text_to_say):
        t = theme()
        corneta_path = os.path.join(IMG_DIR, "corneta.png")
        def on_play():
            speech.say(text_to_say)
            self._record("vocabulario")
        return AudioButton(corneta_path, on_play, size=(64, 64), color=t["accent"])

    def _record(self, cat):
        u = STATE["user"]
        if u:
            ds.record_activity(u["email"], cat, True)
        STATE["session"]["total"] += 1
        STATE["session"]["correct"] += 1


# ---------------------------------------------------------------- inicial (legacy - redirige al hub)
class InicialScreen(BaseScreen):
    title_text = "Etapa Inicial"
    subtitle_text = "Fonemas, sílabas y palabras"

    def on_pre_enter(self, *_):
        # Redirigir al nuevo hub
        sm = App.get_running_app().sm
        sm.current = "inicial_hub"

    def build(self):
        pass


# ---------------------------------------------------------------- avanzada
class AvanzadaScreen(BaseScreen):
    title_text = "Etapa Avanzada"
    subtitle_text = "Trabalenguas, oraciones, comprensión"

    def _cat_enabled(self, key):
        u = STATE["user"]
        if not u:
            return True
        return ds.get_settings(u["email"])["categories"].get(key, True)

    def build(self):
        t = theme()
        scroll = ScrollView()
        col = BoxLayout(orientation="vertical", spacing=14,
                        size_hint_y=None, padding=[0, 4])
        col.bind(minimum_height=col.setter("height"))

        if self._cat_enabled("trabalenguas"):
            col.add_widget(SoftLabel("Trabalenguas", bold=True, size="16sp"))
            tl = random.choice(C.TRABALENGUAS)
            card = RoundedBox(bg=t["card"], orientation="vertical",
                              padding=[14, 12, 14, 12], size_hint_y=None)
            card.bind(minimum_height=card.setter("height"))
            card.add_widget(SoftLabel(tl, size="15sp"))
            btn = self._make_audio_btn(tl, lambda: self._record("trabalenguas", True))
            card.add_widget(btn)
            col.add_widget(card)

        if self._cat_enabled("oraciones"):
            col.add_widget(SoftLabel("Ordena la oración",
                                     bold=True, size="16sp"))
            self._build_ordering(col)

        if self._cat_enabled("comprension"):
            col.add_widget(SoftLabel("Comprensión lectora",
                                     bold=True, size="16sp"))
            self._build_quiz(col, random.choice(C.COMPRENSION),
                             cat="comprension")

        if self._cat_enabled("sinonimos"):
            col.add_widget(SoftLabel("Sinónimos", bold=True, size="16sp"))
            w, opts, ok = random.choice(C.SINONIMOS)
            self._build_choice(col, f"Sinónimo de: {w}", opts, ok, "sinonimos")
            col.add_widget(SoftLabel("Antónimos", bold=True, size="16sp"))
            w, opts, ok = random.choice(C.ANTONIMOS)
            self._build_choice(col, f"Antónimo de: {w}", opts, ok, "sinonimos")

        if self._cat_enabled("cognitivo"):
            col.add_widget(SoftLabel("Retos cognitivos",
                                     bold=True, size="16sp"))
            q = random.choice(C.RETOS_COGNITIVOS)
            self._build_choice(col, q["pregunta"], q["opciones"],
                               q["correcta"], "cognitivo")

        col.add_widget(PrimaryButton("Terminar sesión", self._end_session,
                                     color=t["primary_dark"], big=True))
        scroll.add_widget(col)
        self.body.add_widget(scroll)

    def _make_audio_btn(self, text_to_say, callback=None):
        """Botón de audio con corneta."""
        t = theme()
        corneta_path = os.path.join(IMG_DIR, "corneta.png")
        def on_play():
            speech.say(text_to_say)
            if callback:
                callback()
        return AudioButton(corneta_path, on_play, size=(64, 64), color=t["primary"])

    def _record(self, cat, ok):
        u = STATE["user"]
        if u:
            ds.record_activity(u["email"], cat, ok)
        STATE["session"]["total"] += 1
        if ok:
            STATE["session"]["correct"] += 1

    def _build_ordering(self, col):
        t = theme()
        target = random.choice(C.ORACIONES)
        pool = target[:]
        random.shuffle(pool)
        chosen = []
        card = RoundedBox(bg=t["card"], orientation="vertical",
                          padding=[12, 10, 12, 10], size_hint_y=None,
                          spacing=8)
        card.bind(minimum_height=card.setter("height"))
        preview = SoftLabel("_____", size="16sp", bold=True)
        card.add_widget(preview)
        btn_row = GridLayout(cols=3, spacing=6, size_hint_y=None)
        btn_row.bind(minimum_height=btn_row.setter("height"))

        buttons = []

        def refresh():
            preview.text = " ".join(chosen) if chosen else "_____"

        def pick(word, btn):
            if btn.disabled:
                return
            chosen.append(word)
            btn.disabled = True
            refresh()
            if len(chosen) == len(target):
                if chosen == target:
                    show_toast("¡Muy bien! Frase correcta.")
                    speech.say(" ".join(target))
                    self._record("oraciones", True)
                else:
                    show_toast("Casi, inténtalo de nuevo.")
                    self._record("oraciones", False)
                    Clock.schedule_once(lambda dt: reset(), 1.5)

        for w in pool:
            b = Button(text=w, background_normal="",
                       background_color=t["accent"], color=t["text"],
                       bold=True, size_hint_y=None, height="42dp")
            b.bind(on_release=lambda _b, x=w:
                   pick(x, _b))
            buttons.append(b)
            btn_row.add_widget(b)
        card.add_widget(btn_row)

        def reset(*_):
            chosen.clear()
            refresh()
            for b in buttons:
                b.disabled = False
        card.add_widget(PrimaryButton("Reiniciar", reset,
                                      color=t["secondary"], fg=t["text"]))
        col.add_widget(card)

    def _build_quiz(self, col, q, cat):
        t = theme()
        card = RoundedBox(bg=t["card"], orientation="vertical",
                          padding=[12, 10, 12, 10], size_hint_y=None, spacing=8)
        card.bind(minimum_height=card.setter("height"))
        card.add_widget(SoftLabel(q["texto"]))
        card.add_widget(SoftLabel(q["pregunta"], bold=True))
        for i, opt in enumerate(q["opciones"]):
            b = Button(text=opt, background_normal="",
                       background_color=t["secondary"], color=t["text"],
                       size_hint_y=None, height="42dp")
            b.bind(on_release=lambda _b, idx=i:
                   self._answer(idx == q["correcta"], cat))
            card.add_widget(b)
        col.add_widget(card)

    def _build_choice(self, col, prompt, opts, correct, cat):
        t = theme()
        card = RoundedBox(bg=t["card"], orientation="vertical",
                          padding=[12, 10, 12, 10], size_hint_y=None, spacing=8)
        card.bind(minimum_height=card.setter("height"))
        card.add_widget(SoftLabel(prompt, bold=True, size="15sp"))
        for i, o in enumerate(opts):
            b = Button(text=o, background_normal="",
                       background_color=t["accent"], color=t["text"],
                       size_hint_y=None, height="42dp")
            b.bind(on_release=lambda _b, idx=i:
                   self._answer(idx == correct, cat))
            card.add_widget(b)
        col.add_widget(card)

    def _answer(self, ok, cat):
        show_toast("¡Correcto!" if ok else "Sigue intentando ")
        self._record(cat, ok)

    def _end_session(self):
        u = STATE["user"]
        s = STATE["session"]
        if u and s["total"] > 0:
            ds.record_session(u["email"], s["total"], s["correct"],
                              STATE["sensory_used"])
            show_toast(f"Sesión: {s['correct']}/{s['total']} completadas")
        STATE["session"] = {"total": 0, "correct": 0}
        STATE["sensory_used"] = False
        self.go_back()


# ---------------------------------------------------------------- calma (MEJORADO con imágenes)
class CalmaScreen(BaseScreen):
    title_text = "Calma Sensorial"
    subtitle_text = "Respira y relájate"

    def build(self):
        t = theme()
        STATE["sensory_used"] = True
        self.body.add_widget(SoftLabel(
            "Sigue al niño con tu respiración.",
            size="14sp"))

        self.state_lbl = Label(text="Inhala...", color=t["calm"],
                               font_size="22sp", bold=True,
                               size_hint_y=None, height="40dp")
        self.body.add_widget(self.state_lbl)

        # Área de animación con imagen de niño
        self.breath_area = BoxLayout(orientation="vertical",
                                      size_hint_y=None, height="320dp")
        self.body.add_widget(self.breath_area)

        # Imagen de niño respirando (cambia entre inhalar/exhalar)
        self.breath_img = Image(source="", allow_stretch=True,
                                 keep_ratio=True, size_hint=(1, 0.7))
        self.breath_area.add_widget(self.breath_img)

        # Círculo animado debajo
        area = Widget(size_hint_y=None, height="100dp")
        self.breath_area.add_widget(area)

        with area.canvas:
            self.color = Color(*t["calm"])
            self.circle = Ellipse(pos=(0, 0), size=(80, 80))

        self._st = {"r": 60, "dir": 1}

        # Rutas de imágenes
        self.inhale_img = os.path.join(IMG_DIR, "inhalar.png")
        self.exhale_img = os.path.join(IMG_DIR, "exhalar.png")

        def draw(*_):
            cx = area.x + area.width / 2
            cy = area.y + area.height / 2
            r = self._st["r"]
            self.circle.pos = (cx - r, cy - r)
            self.circle.size = (r * 2, r * 2)

        def tick(_dt):
            self._st["r"] += self._st["dir"] * 2
            if self._st["r"] >= 140:
                self._st["dir"] = -1
                self.state_lbl.text = "Exhala..."
                # Cambiar imagen a exhalar
                if os.path.exists(self.exhale_img):
                    self.breath_img.source = self.exhale_img
            elif self._st["r"] <= 60:
                self._st["dir"] = 1
                self.state_lbl.text = "Inhala..."
                # Cambiar imagen a inhalar
                if os.path.exists(self.inhale_img):
                    self.breath_img.source = self.inhale_img
            draw()

        area.bind(pos=lambda *_: draw(), size=lambda *_: draw())
        self._ev = Clock.schedule_interval(tick, 1 / 20)
        Clock.schedule_once(lambda *_: draw(), 0)

        # Inicializar imagen
        if os.path.exists(self.inhale_img):
            self.breath_img.source = self.inhale_img
        else:
            # Fallback: mostrar emoji grande
            self.breath_area.remove_widget(self.breath_img)
            self.fallback_lbl = Label(text="RESPIRA", font_size="100sp",
                                       size_hint=(1, 0.7))
            self.breath_area.add_widget(self.fallback_lbl, index=0)

        self.body.add_widget(SoftLabel(
            "Consejo: apoya los pies en el suelo y suelta los hombros.",
            size="13sp"))

    def on_leave(self, *_):
        try:
            self._ev.cancel()
        except Exception:
            pass


# ---------------------------------------------------------------- señas (M7) - con botón corneta
class SeñasScreen(BaseScreen):
    title_text = "Comunicación y Lenguaje de Señas"
    subtitle_text = "Frases para casa y escuela"

    def build(self):
        t = theme()
        self.body.add_widget(SoftLabel(
            "Lee el gesto y toca el botón Escuchar para oír la frase.",
            size="13sp"))
        scroll = ScrollView()
        col = BoxLayout(orientation="vertical", spacing=10,
                        size_hint_y=None)
        col.bind(minimum_height=col.setter("height"))
        for item in C.SEÑAS:
            card = RoundedBox(bg=t["card"], orientation="vertical",
                              padding=[12, 10, 12, 12], size_hint_y=None,
                              spacing=4)
            card.bind(minimum_height=card.setter("height"))
            _img = C.SEÑAS_IMG.get(item["frase"])
            _p = os.path.join(IMG_DIR, "senas", _img) if _img else ""
            if _p and os.path.exists(_p):
                card.add_widget(Image(source=_p, allow_stretch=True,
                                      keep_ratio=True, size_hint_y=None,
                                      height="380dp"))
            else:
                card.add_widget(Label(
                    text=item["emoji"] or (item["frase"][0].upper() if item["frase"] else "S"),
                    font_size="90sp", size_hint_y=None, height="200dp"))
            _title = Label(text=item["frase"], color=t["text"],
                           bold=True, font_size="20sp",
                           halign="center", valign="middle",
                           size_hint_y=None, height="34dp")
            _title.bind(size=lambda i, v: setattr(i, "text_size", v))
            card.add_widget(_title)
            card.add_widget(SoftLabel(f"Gesto: {item['gesto']}", size="13sp"))
            card.add_widget(SoftLabel(f"Cuándo usar: {item['uso']}",
                                      size="12sp", color=t["text_soft"]))

            # Botón de audio con corneta
            play = self._make_audio_btn(item["frase"])
            card.add_widget(play)
            col.add_widget(card)

        # Guía para adultos
        guide = RoundedBox(bg=t["accent"], orientation="vertical",
                           padding=[12, 12, 12, 12], size_hint_y=None,
                           spacing=6)
        guide.bind(minimum_height=guide.setter("height"))
        guide.add_widget(SoftLabel("Guía para adultos", bold=True, size="15sp"))
        guide.add_widget(SoftLabel(
            "• Modela el gesto antes de pedirlo. "
            "• Refuerza cada intento con una sonrisa o palabra amable. "
            "• Úsalos en rutinas: comida, baño, transiciones. "
            "• Reducen la frustración cuando hablar cuesta.",
            size="13sp"))
        col.add_widget(guide)

        scroll.add_widget(col)
        self.body.add_widget(scroll)

    def _make_audio_btn(self, text_to_say):
        t = theme()
        corneta_path = os.path.join(IMG_DIR, "corneta.png")
        def on_play():
            speech.say(text_to_say)
            self._record()
        return AudioButton(corneta_path, on_play, size=(64, 64), color=t["secondary"])

    def _record(self):
        u = STATE["user"]
        if u:
            ds.record_activity(u["email"], "senas", True)
        STATE["session"]["total"] += 1
        STATE["session"]["correct"] += 1


# ---------------------------------------------------------------- emociones
class EmocionesScreen(BaseScreen):
    title_text = "Vocabulario emocional"

    def build(self):
        t = theme()
        self.body.add_widget(SoftLabel(
            "¿Cómo te sientes hoy? Toca el botón Escuchar de la emoción.",
            size="14sp"))
        scroll = ScrollView(bar_width=4)
        grid = GridLayout(cols=2, spacing=12, size_hint_y=None,
                          padding=[0, 4])
        grid.bind(minimum_height=grid.setter("height"))
        for emo, name in C.EMOCIONES:
            cell = RoundedBox(bg=t["card"], radius=22, orientation="vertical",
                              size_hint_y=None, height="286dp",
                              padding=[10, 10, 10, 12], spacing=6)
            _img = C.EMOCIONES_IMG.get(name)
            _p = os.path.join(IMG_DIR, "emociones", _img) if _img else ""
            if _p and os.path.exists(_p):
                cell.add_widget(Image(source=_p, allow_stretch=True,
                                      keep_ratio=True, size_hint_y=None,
                                      height="180dp"))
            else:
                cell.add_widget(Label(text=name[0].upper(), color=t["primary"],
                                      bold=True, font_size="70sp",
                                      size_hint_y=None, height="180dp"))
            title = Label(text=name, color=t["text"], bold=True,
                          font_size="17sp", halign="center", valign="middle",
                          size_hint_y=None, height="30dp")
            title.bind(size=lambda i, s: setattr(i, "text_size", s))
            cell.add_widget(title)

            # La voz SOLO suena con el boton (nunca al pasar el cursor)
            holder = AnchorLayout(size_hint_y=None, height="56dp")
            holder.add_widget(self._make_audio_btn(name))
            cell.add_widget(holder)
            grid.add_widget(cell)
        scroll.add_widget(grid)
        self.body.add_widget(scroll)

    def _make_audio_btn(self, name):
        t = theme()
        corneta_path = os.path.join(IMG_DIR, "corneta.png")

        def on_play():
            speech.say(f"Me siento {name}")
            u = STATE["user"]
            if u:
                ds.record_activity(u["email"], "emociones", True)
        return AudioButton(corneta_path, on_play, color=t["secondary"])



# ---------------------------------------------------------------- settings (M5)
class SettingsScreen(BaseScreen):
    title_text = "Configuración de Aprendizaje"
    subtitle_text = "Activa lo que el niño debe practicar"

    def build(self):
        t = theme()
        u = STATE["user"]
        if not u:
            self.body.add_widget(SoftLabel("Inicia sesión primero."))
            return
        s = ds.get_settings(u["email"])

        scroll = ScrollView()
        col = BoxLayout(orientation="vertical", spacing=8,
                        size_hint_y=None)
        col.bind(minimum_height=col.setter("height"))

        col.add_widget(SoftLabel("Categorías", bold=True, size="15sp"))
        checks = {}
        for key, label in LEARNING_CATEGORIES:
            row = BoxLayout(orientation="horizontal", size_hint_y=None,
                            height="36dp", spacing=8)
            cb = CheckBox(active=s["categories"].get(key, True),
                          size_hint_x=None, width="40dp")
            row.add_widget(cb)
            row.add_widget(Label(text=label, color=t["text"],
                                 halign="left", valign="middle"))
            checks[key] = cb
            col.add_widget(row)

        col.add_widget(SoftLabel("Actividades por sesión", bold=True,
                                 size="15sp"))
        size_input = TextInput(text=str(s.get("session_size", 10)),
                               input_filter="int", multiline=False,
                               size_hint_y=None, height="44dp")
        col.add_widget(size_input)

        def save(*_):
            s["categories"] = {k: bool(cb.active) for k, cb in checks.items()}
            try:
                s["session_size"] = max(1, int(size_input.text or "10"))
            except Exception:
                s["session_size"] = 10
            ds.save_settings(u["email"], s)
            show_toast("Configuración guardada.")

        col.add_widget(PrimaryButton("Guardar", save, big=True))

        # Misiones
        col.add_widget(SoftLabel("Misión personalizada (Quest)",
                                 bold=True, size="15sp"))
        title_in = TextInput(hint_text="Ej: Completar 5 ejercicios de fonemas",
                             multiline=False, size_hint_y=None, height="44dp")
        target_in = TextInput(hint_text="Meta (número)", input_filter="int",
                              multiline=False, size_hint_y=None, height="44dp")
        cat_in = Spinner(text=LEARNING_CATEGORIES[0][0],
                         values=tuple(k for k, _ in LEARNING_CATEGORIES),
                         size_hint_y=None, height="44dp")
        col.add_widget(title_in)
        col.add_widget(target_in)
        col.add_widget(cat_in)

        def add_m(*_):
            if not title_in.text or not target_in.text:
                show_toast("Escribe título y meta.")
                return
            ds.add_mission(u["email"], title_in.text,
                           int(target_in.text), cat_in.text)
            title_in.text = ""
            target_in.text = ""
            show_toast("Misión creada.")

        col.add_widget(PrimaryButton("Crear misión", add_m,
                                     color=t["secondary"], fg=t["text"]))
        scroll.add_widget(col)
        self.body.add_widget(scroll)


# =============================================================================
# MEJORADO: MISIONES CON PANEL DE JUEGO INTERACTIVO
# =============================================================================
class MisionesScreen(BaseScreen):
    title_text = "Misiones"
    subtitle_text = "Progreso sin estrés"

    def build(self):
        t = theme()
        u = STATE["user"]
        if not u:
            self.body.add_widget(SoftLabel("Inicia sesión primero."))
            return
        missions = ds.get_missions(u["email"])
        if not missions:
            self.body.add_widget(SoftLabel(
                "Aún no hay misiones. Créalas en Configuración."))
            return

        self.body.add_widget(SoftLabel(
            "Toca una misión para jugarla directamente", size="13sp", color=t["text_soft"]))

        scroll = ScrollView()
        col = BoxLayout(orientation="vertical", spacing=10,
                        size_hint_y=None)
        col.bind(minimum_height=col.setter("height"))

        for m in missions:
            card = RoundedBox(bg=t["card"], orientation="vertical",
                              padding=[12, 10, 12, 10], size_hint_y=None,
                              spacing=6)
            card.bind(minimum_height=card.setter("height"))

            # Header con estado
            status = "OK " if m["done"] else " "
            card.add_widget(SoftLabel(
                status + m["title"],
                bold=True, size="15sp"))

            pb = ProgressBar(max=m["target"], value=m["progress"],
                             size_hint_y=None, height="14dp")
            card.add_widget(pb)
            card.add_widget(SoftLabel(
                f"{m['progress']}/{m['target']} — {m['category']}",
                size="12sp", color=t["text_soft"]))

            # Botón para jugar la misión (solo si no está completada)
            if not m["done"]:
                play_btn = PrimaryButton(
                    "> Jugar misión",
                    lambda mid=m["id"]: self._play_mission(mid),
                    color=t["accent"], fg=t["text"])
                card.add_widget(play_btn)

            col.add_widget(card)

        scroll.add_widget(col)
        self.body.add_widget(scroll)

    def _play_mission(self, mission_id):
        """Abre el panel de juego para una misión específica."""
        u = STATE["user"]
        if not u:
            return
        missions = ds.get_missions(u["email"])
        mission = next((m for m in missions if m["id"] == mission_id), None)
        if not mission:
            show_toast("Misión no encontrada.")
            return

        # Guardar misión activa y navegar
        STATE["active_mission"] = mission
        sm = App.get_running_app().sm
        sm.transition = SlideTransition(direction="left")
        sm.current = "mission_play"


# =============================================================================
# NUEVO: PANTALLA DE JUEGO DE MISIÓN
# =============================================================================
class MissionPlayScreen(BaseScreen):
    title_text = "Jugando Misión"
    subtitle_text = ""

    def build(self):
        t = theme()
        u = STATE["user"]
        mission = STATE.get("active_mission")

        if not u or not mission:
            self.body.add_widget(SoftLabel("No hay misión activa."))
            self.body.add_widget(PrimaryButton("Volver", self.go_back))
            return

        self.subtitle_text = f"{mission['title']} ({mission['progress']}/{mission['target']})"

        self.body.add_widget(SoftLabel(
            f"Categoría: {mission['category']}", size="14sp", color=t["text_soft"]))

        # Barra de progreso
        pb = ProgressBar(max=mission["target"], value=mission["progress"],
                         size_hint_y=None, height="20dp")
        self.body.add_widget(pb)

        # Contenido según categoría de la misión
        self._build_mission_content(mission)

        # Botón para terminar
        self.body.add_widget(PrimaryButton("Terminar y volver", self.go_back,
                                            color=t["primary_dark"], big=True))

    def _build_mission_content(self, mission):
        t = theme()
        cat = mission["category"]

        scroll = ScrollView()
        col = BoxLayout(orientation="vertical", spacing=10,
                        size_hint_y=None, padding=[0, 4])
        col.bind(minimum_height=col.setter("height"))

        if cat == "vocales":
            col.add_widget(SoftLabel("Toca las vocales para practicar", bold=True))
            grid = GridLayout(cols=5, spacing=8, size_hint_y=None)
            grid.bind(minimum_height=grid.setter("height"))
            for ch in C.VOCALES:
                b = Button(text=ch, background_normal="",
                           background_color=t["primary"], color=t["white"],
                           bold=True, font_size="22sp",
                           size_hint_y=None, height="60dp")
                b.bind(on_release=lambda _b, c=ch: self._do_activity("vocales", c))
                grid.add_widget(b)
            col.add_widget(grid)

        elif cat == "silabas":
            col.add_widget(SoftLabel("Toca las sílabas para practicar", bold=True))
            grid = GridLayout(cols=5, spacing=8, size_hint_y=None)
            grid.bind(minimum_height=grid.setter("height"))
            for s in C.SILABAS:
                b = Button(text=s, background_normal="",
                           background_color=t["secondary"], color=t["text"],
                           bold=True, font_size="18sp",
                           size_hint_y=None, height="52dp")
                b.bind(on_release=lambda _b, x=s: self._do_activity("silabas", x))
                grid.add_widget(b)
            col.add_widget(grid)

        elif cat == "vocabulario":
            col.add_widget(SoftLabel("Toca las palabras para practicar", bold=True))
            grid = GridLayout(cols=3, spacing=8, size_hint_y=None)
            grid.bind(minimum_height=grid.setter("height"))
            for emo, pal in C.PALABRAS:
                cell = RoundedBox(bg=t["card"], orientation="vertical",
                                  size_hint_y=None, height="100dp",
                                  padding=[6, 6, 6, 6])
                cell.add_widget(Label(text=emo, font_size="30sp",
                                      size_hint_y=None, height="46dp"))
                cell.add_widget(Label(text=pal, color=t["text"], bold=True,
                                      font_size="13sp"))
                def on_touch(instance, touch, p=pal):
                    if instance.collide_point(*touch.pos):
                        self._do_activity("vocabulario", p)
                cell.bind(on_touch_down=on_touch)
                grid.add_widget(cell)
            col.add_widget(grid)

        elif cat == "trabalenguas":
            col.add_widget(SoftLabel("Practica este trabalenguas", bold=True))
            tl = random.choice(C.TRABALENGUAS)
            card = RoundedBox(bg=t["card"], orientation="vertical",
                              padding=[14, 12, 14, 12], size_hint_y=None)
            card.bind(minimum_height=card.setter("height"))
            card.add_widget(SoftLabel(tl, size="15sp"))
            btn = self._make_audio_btn(tl, lambda: self._do_activity("trabalenguas", tl))
            card.add_widget(btn)
            col.add_widget(card)

        elif cat == "comprension":
            col.add_widget(SoftLabel("Lee y responde", bold=True))
            q = random.choice(C.COMPRENSION)
            card = RoundedBox(bg=t["card"], orientation="vertical",
                              padding=[12, 10, 12, 10], size_hint_y=None, spacing=8)
            card.bind(minimum_height=card.setter("height"))
            card.add_widget(SoftLabel(q["texto"]))
            card.add_widget(SoftLabel(q["pregunta"], bold=True))
            for i, opt in enumerate(q["opciones"]):
                b = Button(text=opt, background_normal="",
                           background_color=t["secondary"], color=t["text"],
                           size_hint_y=None, height="42dp")
                b.bind(on_release=lambda _b, idx=i, correct=q["correcta"]:
                       self._do_activity("comprension", idx == correct))
                card.add_widget(b)
            col.add_widget(card)

        elif cat == "sinonimos":
            col.add_widget(SoftLabel("Encuentra el sinónimo", bold=True))
            w, opts, ok = random.choice(C.SINONIMOS)
            self._build_choice_mission(col, f"Sinónimo de: {w}", opts, ok, "sinonimos")

        elif cat == "cognitivo":
            col.add_widget(SoftLabel("Resuelve el reto", bold=True))
            q = random.choice(C.RETOS_COGNITIVOS)
            self._build_choice_mission(col, q["pregunta"], q["opciones"],
                                       q["correcta"], "cognitivo")

        elif cat == "senas":
            col.add_widget(SoftLabel("Practica señas", bold=True))
            item = random.choice(C.SEÑAS)
            card = RoundedBox(bg=t["card"], orientation="vertical",
                              padding=[12, 10, 12, 10], size_hint_y=None, spacing=6)
            card.bind(minimum_height=card.setter("height"))
            card.add_widget(Label(text=item["frase"][0].upper() if item["frase"] else "S", font_size="40sp",
                                  size_hint_y=None, height="50dp"))
            card.add_widget(SoftLabel(item["frase"], bold=True, size="16sp"))
            card.add_widget(SoftLabel(f"Gesto: {item['gesto']}", size="13sp"))
            btn = self._make_audio_btn(item["frase"],
                                        lambda: self._do_activity("senas", item["frase"]))
            card.add_widget(btn)
            col.add_widget(card)

        elif cat == "emociones":
            col.add_widget(SoftLabel("¿Cómo te sientes?", bold=True))
            grid = GridLayout(cols=2, spacing=12, size_hint_y=None)
            grid.bind(minimum_height=grid.setter("height"))
            for emo, name in C.EMOCIONES:
                cell = RoundedBox(bg=t["card"], radius=20,
                                  orientation="vertical",
                                  size_hint_y=None, height="250dp",
                                  padding=[8, 8, 8, 10], spacing=6)
                _img = C.EMOCIONES_IMG.get(name)
                _p = os.path.join(IMG_DIR, "emociones", _img) if _img else ""
                if _p and os.path.exists(_p):
                    cell.add_widget(Image(source=_p, allow_stretch=True,
                                          keep_ratio=True, size_hint_y=None,
                                          height="150dp"))
                else:
                    cell.add_widget(Label(text=name[0].upper(),
                                          color=t["primary"], bold=True,
                                          font_size="60sp",
                                          size_hint_y=None, height="150dp"))
                lbl = Label(text=name, color=t["text"], bold=True,
                            font_size="16sp", halign="center",
                            valign="middle", size_hint_y=None, height="28dp")
                lbl.bind(size=lambda i, s: setattr(i, "text_size", s))
                cell.add_widget(lbl)
                holder = AnchorLayout(size_hint_y=None, height="56dp")
                holder.add_widget(self._make_audio_btn(
                    f"Me siento {name}",
                    lambda n=name: self._do_activity("emociones", n)))
                cell.add_widget(holder)
                grid.add_widget(cell)
            col.add_widget(grid)


        elif cat == "oraciones":
            col.add_widget(SoftLabel("Ordena la oración", bold=True))
            self._build_ordering_mission(col)

        else:
            col.add_widget(SoftLabel("Actividad no disponible para esta categoría."))

        scroll.add_widget(col)
        self.body.add_widget(scroll)

    def _make_audio_btn(self, text_to_say, callback=None):
        t = theme()
        corneta_path = os.path.join(IMG_DIR, "corneta.png")
        def on_play():
            speech.say(text_to_say)
            if callback:
                callback()
        return AudioButton(corneta_path, on_play, size=(64, 64), color=t["primary"])

    def _do_activity(self, cat, result):
        """Registra una actividad completada en la misión activa."""
        u = STATE["user"]
        mission = STATE.get("active_mission")
        if not u or not mission:
            return

        # Registrar en progreso general
        if isinstance(result, bool):
            ds.record_activity(u["email"], cat, result)
            if result:
                show_toast("¡Bien hecho!")
            else:
                show_toast("Sigue intentando ")
        else:
            ds.record_activity(u["email"], cat, True)
            speech.say(str(result))
            show_toast("¡Excelente!")

        # Actualizar misión
        ds.bump_mission(u["email"], cat, 1)

        # Recargar misión
        missions = ds.get_missions(u["email"])
        updated = next((m for m in missions if m["id"] == mission["id"]), None)
        if updated:
            STATE["active_mission"] = updated
            if updated["done"]:
                show_toast("FELICIDADES ¡Misión completada!")
                Clock.schedule_once(lambda *_: self.go_back(), 1.5)
            else:
                # Recargar pantalla
                self.on_pre_enter()

    def _build_choice_mission(self, col, prompt, opts, correct, cat):
        t = theme()
        card = RoundedBox(bg=t["card"], orientation="vertical",
                          padding=[12, 10, 12, 10], size_hint_y=None, spacing=8)
        card.bind(minimum_height=card.setter("height"))
        card.add_widget(SoftLabel(prompt, bold=True, size="15sp"))
        for i, o in enumerate(opts):
            b = Button(text=o, background_normal="",
                       background_color=t["accent"], color=t["text"],
                       size_hint_y=None, height="42dp")
            b.bind(on_release=lambda _b, idx=i:
                   self._do_activity(cat, idx == correct))
            card.add_widget(b)
        col.add_widget(card)

    def _build_ordering_mission(self, col):
        t = theme()
        target = random.choice(C.ORACIONES)
        pool = target[:]
        random.shuffle(pool)
        chosen = []
        card = RoundedBox(bg=t["card"], orientation="vertical",
                          padding=[12, 10, 12, 10], size_hint_y=None,
                          spacing=8)
        card.bind(minimum_height=card.setter("height"))
        preview = SoftLabel("_____", size="16sp", bold=True)
        card.add_widget(preview)
        btn_row = GridLayout(cols=3, spacing=6, size_hint_y=None)
        btn_row.bind(minimum_height=btn_row.setter("height"))

        buttons = []

        def refresh():
            preview.text = " ".join(chosen) if chosen else "_____"

        def pick(word, btn):
            if btn.disabled:
                return
            chosen.append(word)
            btn.disabled = True
            refresh()
            if len(chosen) == len(target):
                if chosen == target:
                    show_toast("¡Muy bien! Frase correcta.")
                    speech.say(" ".join(target))
                    self._do_activity("oraciones", True)
                else:
                    show_toast("Casi, inténtalo de nuevo.")
                    self._do_activity("oraciones", False)
                    Clock.schedule_once(lambda dt: reset(), 1.5)

        for w in pool:
            b = Button(text=w, background_normal="",
                       background_color=t["accent"], color=t["text"],
                       bold=True, size_hint_y=None, height="42dp")
            b.bind(on_release=lambda _b, x=w:
                   pick(x, _b))
            buttons.append(b)
            btn_row.add_widget(b)
        card.add_widget(btn_row)

        def reset(*_):
            chosen.clear()
            refresh()
            for b in buttons:
                b.disabled = False
        card.add_widget(PrimaryButton("Reiniciar", reset,
                                      color=t["secondary"], fg=t["text"]))
        col.add_widget(card)


# ---------------------------------------------------------------- progress (M6)
class ProgressScreen(BaseScreen):
    title_text = "Mi Progreso"
    subtitle_text = "Reporte amigable"

    def build(self):
        t = theme()
        u = STATE["user"]
        if not u:
            self.body.add_widget(SoftLabel("Inicia sesión primero."))
            return
        p = ds.get_progress(u["email"])
        s = ds.get_settings(u["email"])
        target = s.get("session_size", 10)
        last = p["sessions"][-1] if p["sessions"] else None

        totals = p.get("totals", {})
        tot_ok = sum(v.get("ok", 0) for v in totals.values())
        tot_fail = sum(v.get("fail", 0) for v in totals.values())
        tot_all = tot_ok + tot_fail
        acierto = int((tot_ok / tot_all) * 100) if tot_all else 0

        scroll = ScrollView(bar_width=4)
        col = BoxLayout(orientation="vertical", spacing=14, size_hint_y=None,
                        padding=[0, 4, 0, 8])
        col.bind(minimum_height=col.setter("height"))

        # ---- Resumen destacado -------------------------------------------
        hero = RoundedBox(bg=t["primary"], radius=26, orientation="vertical",
                          padding=[16, 14, 16, 16], spacing=8,
                          size_hint_y=None, height="150dp")
        hero.add_widget(SoftLabel("Puntos acumulados", bold=True, size="13sp",
                                  color=(1, 1, 1, 0.9)))
        big = Label(text=str(p["points"]), color=t["white"], bold=True,
                    font_size="40sp", halign="left", valign="middle",
                    size_hint_y=None, height="48dp")
        big.bind(size=lambda i, v: setattr(i, "text_size", v))
        hero.add_widget(big)

        stats = BoxLayout(orientation="horizontal", spacing=10,
                          size_hint_y=None, height="52dp")
        for value, caption in (
            (f"{tot_ok}", "Aciertos"),
            (f"{acierto}%", "Precisión"),
            (f"{len(p['sessions'])}", "Sesiones"),
        ):
            box = RoundedBox(bg=(1, 1, 1, 0.18), radius=16,
                             orientation="vertical", padding=[8, 6, 8, 6])
            v = Label(text=value, color=t["white"], bold=True,
                      font_size="17sp")
            c = Label(text=caption, color=(1, 1, 1, 0.85), font_size="11sp")
            box.add_widget(v)
            box.add_widget(c)
            stats.add_widget(box)
        hero.add_widget(stats)
        col.add_widget(hero)

        # ---- Última sesión ------------------------------------------------
        card = RoundedBox(bg=t["card"], radius=22, orientation="vertical",
                          padding=[16, 14, 16, 16], spacing=8,
                          size_hint_y=None)
        card.bind(minimum_height=card.setter("height"))
        card.add_widget(SoftLabel("Última sesión", bold=True, size="16sp"))
        if last:
            pct = int((last["correct"] / last["total"]) * 100) \
                if last["total"] else 0
            card.add_widget(SoftLabel(
                f"{last['correct']} de {last['total']} actividades logradas",
                size="14sp", color=t["text_soft"]))
            card.add_widget(self._bar(pct, t["primary"]))
            card.add_widget(SoftLabel(f"{pct}% completado", size="13sp",
                                      bold=True))
            if last.get("sensory_used"):
                card.add_widget(SoftLabel(
                    "Se usaron herramientas de regulación sensorial.",
                    size="12sp", color=t["text_soft"]))
        else:
            card.add_widget(SoftLabel(
                "Todavía no hay sesiones. Empieza una actividad y aquí verás "
                "tu avance.", size="13sp", color=t["text_soft"]))
        col.add_widget(card)

        # ---- Desempeño por categoría --------------------------------------
        totals_card = RoundedBox(bg=t["card"], radius=22,
                                 orientation="vertical",
                                 padding=[16, 14, 16, 16], spacing=10,
                                 size_hint_y=None)
        totals_card.bind(minimum_height=totals_card.setter("height"))
        totals_card.add_widget(SoftLabel("Desempeño por categoría",
                                         bold=True, size="16sp"))
        for k, label in LEARNING_CATEGORIES:
            tt = totals.get(k, {"ok": 0, "fail": 0})
            tot = tt["ok"] + tt["fail"]
            pct = int((tt["ok"] / tot) * 100) if tot else 0
            row = BoxLayout(orientation="vertical", spacing=4,
                            size_hint_y=None, height="52dp")
            head = BoxLayout(orientation="horizontal", size_hint_y=None,
                             height="24dp")
            name = Label(text=label, color=t["text"], font_size="13sp",
                         bold=True, halign="left", valign="middle")
            name.bind(size=lambda i, v: setattr(i, "text_size", v))
            val = Label(text=(f"{tt['ok']} / {tot}" if tot else "sin practicar"),
                        color=t["text_soft"], font_size="12sp",
                        halign="right", valign="middle",
                        size_hint_x=None, width="110dp")
            val.bind(size=lambda i, v: setattr(i, "text_size", v))
            head.add_widget(name)
            head.add_widget(val)
            row.add_widget(head)
            color = t["success"] if pct >= 70 else (
                t["accent"] if pct > 0 else t["line"])
            row.add_widget(self._bar(pct, color, height="10dp"))
            totals_card.add_widget(row)
        col.add_widget(totals_card)

        # ---- Recomendaciones ----------------------------------------------
        rec_card = RoundedBox(bg=t["soft_3"], radius=22,
                              orientation="vertical",
                              padding=[16, 14, 16, 16], spacing=6,
                              size_hint_y=None)
        rec_card.bind(minimum_height=rec_card.setter("height"))
        rec_card.add_widget(SoftLabel("Sugerido para la próxima sesión",
                                      bold=True, size="16sp"))
        for r in ds.recommend_next(u["email"]):
            chip = RoundedBox(bg=t["white"], radius=16, border=t["line"],
                              padding=[12, 8, 12, 8], size_hint_y=None,
                              height="40dp")
            chip.add_widget(SoftLabel(r, size="13sp"))
            rec_card.add_widget(chip)
        rec_card.add_widget(SoftLabel(
            f"Meta configurada por sesión: {target} actividades.",
            size="12sp", color=t["text_soft"]))
        col.add_widget(rec_card)

        scroll.add_widget(col)
        self.body.add_widget(scroll)

    def _bar(self, pct, color, height="14dp"):
        """Barra de progreso redondeada y limpia."""
        t = theme()
        from kivy.metrics import dp
        h = height if isinstance(height, (int, float)) else dp(
            float(str(height).replace("dp", "")))

        rad = h / 2.0
        track = RoundedBox(bg=t["line"], radius=rad, size_hint_y=None,
                           height=h)
        fill = RoundedBox(bg=color, radius=rad, size_hint=(None, 1))

        def _sync(*_):
            fill.width = max(0, track.width) * max(0.0, min(1.0, pct / 100.0))
        track.add_widget(fill)
        track.bind(pos=_sync, size=_sync)
        return track




# ---------------------------------------------------------------- dashboard (M8)
class DashboardScreen(BaseScreen):
    title_text = "Panel del Adulto"
    subtitle_text = "Monitoreo y seguimiento"

    def build(self):
        t = theme()
        u = STATE["user"]
        if not u:
            self.body.add_widget(SoftLabel("Inicia sesión primero."))
            return
        p = ds.get_progress(u["email"])

        scroll = ScrollView()
        col = BoxLayout(orientation="vertical", spacing=10,
                        size_hint_y=None)
        col.bind(minimum_height=col.setter("height"))

        # Resumen
        summary = RoundedBox(bg=t["card"], orientation="vertical",
                             padding=[14, 12, 14, 12], size_hint_y=None,
                             spacing=6)
        summary.bind(minimum_height=summary.setter("height"))
        summary.add_widget(SoftLabel("Resumen", bold=True, size="16sp"))
        summary.add_widget(SoftLabel(f"Sesiones registradas: {len(p['sessions'])}"))
        summary.add_widget(SoftLabel(f"Puntos totales: {p['points']} *"))
        summary.add_widget(SoftLabel(
            f"Usos de regulación sensorial: {p['sensory_uses']} "))
        col.add_widget(summary)

        # Historial
        hist = RoundedBox(bg=t["card"], orientation="vertical",
                          padding=[14, 12, 14, 12], size_hint_y=None,
                          spacing=4)
        hist.bind(minimum_height=hist.setter("height"))
        hist.add_widget(SoftLabel("Historial de sesiones",
                                  bold=True, size="15sp"))
        for s in p["sessions"][-8:][::-1]:
            pct = int((s["correct"] / s["total"]) * 100) if s["total"] else 0
            extra = "  " if s.get("sensory_used") else ""
            hist.add_widget(SoftLabel(
                f"{s['date']} · {s['correct']}/{s['total']} ({pct}%){extra}",
                size="12sp"))
        if not p["sessions"]:
            hist.add_widget(SoftLabel("Sin sesiones aún.", size="12sp"))
        col.add_widget(hist)

        # Recomendaciones
        rec = RoundedBox(bg=t["accent"], orientation="vertical",
                         padding=[14, 12, 14, 12], size_hint_y=None,
                         spacing=4)
        rec.bind(minimum_height=rec.setter("height"))
        rec.add_widget(SoftLabel("Recomendaciones automáticas",
                                 bold=True, size="15sp"))
        for r in ds.recommend_next(u["email"]):
            rec.add_widget(SoftLabel(f"• Reforzar: {r}", size="13sp"))
        col.add_widget(rec)

        # Accesos rápidos
        col.add_widget(PrimaryButton(" Configurar aprendizaje",
                                     lambda: self._go("settings"), big=True))
        col.add_widget(PrimaryButton(" Ver misiones",
                                     lambda: self._go("misiones"),
                                     color=t["secondary"], fg=t["text"]))

        # Exportar reporte
        def export(*_):
            path = ds.export_report(u["email"])
            show_toast(f"Reporte guardado en:\n{path}", title="Exportar")

        col.add_widget(PrimaryButton(" Exportar reporte",
                                     export, color=t["primary_dark"]))

        scroll.add_widget(col)
        self.body.add_widget(scroll)

    def _go(self, name):
        sm = App.get_running_app().sm
        sm.transition = SlideTransition(direction="left")
        sm.current = name


# =============================================================================
# NUEVO BLOQUE: MATEMATICAS (numeros, sumas, restas, figuras y series)
# =============================================================================
NUMEROS = [
    (0, "cero"), (1, "uno"), (2, "dos"), (3, "tres"), (4, "cuatro"),
    (5, "cinco"), (6, "seis"), (7, "siete"), (8, "ocho"), (9, "nueve"),
    (10, "diez"), (11, "once"), (12, "doce"), (13, "trece"), (14, "catorce"),
    (15, "quince"), (16, "dieciseis"), (17, "diecisiete"), (18, "dieciocho"),
    (19, "diecinueve"), (20, "veinte"),
]

FIGURAS = [
    ("Circulo", "Redondo como el sol", "circulo.png"),
    ("Cuadrado", "Cuatro lados iguales", "cuadrado.png"),
    ("Triangulo", "Tres lados", "triangulo.png"),
    ("Rectangulo", "Dos lados largos", "rectangulo.png"),
    ("Estrella", "Brilla en el cielo", "estrella.png"),
    ("Corazon", "El del carino", "corazon.png"),
]

FIG_DIR = os.path.join(IMG_DIR, "figuras")


class MatematicasHubScreen(BaseScreen):
    title_text = "Matemáticas"
    subtitle_text = "Números, sumas y figuras"

    def build(self):
        t = theme()
        self.body.add_widget(SoftLabel("Elige un ejercicio, con calma",
                                       size="16sp", bold=True))
        scroll = ScrollView(bar_width=4)
        col = BoxLayout(orientation="vertical", spacing=12,
                        size_hint_y=None, padding=[0, 6])
        col.bind(minimum_height=col.setter("height"))

        bloques = [
            ("Números del 0 al 20", "Escucha y cuenta con puntos",
             "num_numeros", t["secondary"]),
            ("Sumas fáciles", "Ejercicios cortos, sin prisa",
             "num_sumas", t["primary"]),
            ("Restas fáciles", "Quitar poquito a poco",
             "num_restas", t["calm"]),
            ("Figuras y formas", "Reconocer figuras basicas",
             "num_figuras", t["accent"]),
            ("Contar en series", "De 2 en 2, de 5 en 5",
             "num_series", t["primary_dark"]),
        ]
        cards = []
        for titulo, desc, target, color in bloques:
            card = RoundedBox(bg=t["card"], radius=22, border=t["line"],
                              orientation="vertical", size_hint_y=None,
                              padding=[16, 14, 16, 14], spacing=8)
            card.bind(minimum_height=card.setter("height"))
            card.add_widget(SoftLabel(titulo, bold=True, size="17sp"))
            card.add_widget(SoftLabel(desc, size="13sp", color=t["text_soft"]))
            card.add_widget(PrimaryButton(
                "Comenzar", lambda tg=target: self.go(tg), color=color,
                fg=t["text"] if color == t["accent"] else t["white"], big=True))
            cards.append(card)
            col.add_widget(card)

        scroll.add_widget(col)
        self.body.add_widget(scroll)
        stagger_in(cards, step=0.05)

    def go(self, name):
        sm = App.get_running_app().sm
        sm.transition = SlideTransition(direction="left")
        sm.current = name


class MathBaseScreen(BaseScreen):
    def go_back(self):
        sm = App.get_running_app().sm
        sm.transition = SlideTransition(direction="right")
        sm.current = "matematicas"

    def _record(self, ok=True):
        u = STATE["user"]
        if u:
            ds.record_activity(u["email"], "matematicas", ok)
        STATE["session"]["total"] += 1
        if ok:
            STATE["session"]["correct"] += 1


class NumerosScreen(MathBaseScreen):
    title_text = "Números"
    subtitle_text = "Del 0 al 20"

    def build(self):
        t = theme()
        self.body.add_widget(SoftLabel(
            "Toca un numero para escucharlo y ver cuantos son.",
            size="13sp", color=t["text_soft"]))
        scroll = ScrollView(bar_width=4)
        grid = GridLayout(cols=3, spacing=12, padding=[4, 8, 4, 8],
                          size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        tints = [t["soft"], t["soft_2"], t["soft_3"]]
        cards = []
        for i, (n, nombre) in enumerate(NUMEROS):
            card = RoundedBox(bg=tints[i % 3], radius=20, border=t["line"],
                              orientation="vertical", size_hint_y=None,
                              height="120dp", padding=[8, 8, 8, 8], spacing=2)
            card.add_widget(Label(text=str(n), color=t["primary"], bold=True,
                                  font_size="34sp",
                                  size_hint_y=None, height="46dp"))
            puntos = ("o " * n).strip() if n <= 10 else f"{n} unidades"
            card.add_widget(Label(text=puntos or "vacio",
                                  color=t["text_soft"], font_size="12sp",
                                  size_hint_y=None, height="24dp"))
            card.add_widget(Label(text=nombre, color=t["text"], bold=True,
                                  font_size="13sp",
                                  size_hint_y=None, height="20dp"))

            def on_touch(instance, touch, num=n, nom=nombre):
                if instance.collide_point(*touch.pos):
                    soft_pulse(instance)
                    speech.say(f"{num}, {nom}")
                    self._record(True)
                    return True
            card.bind(on_touch_down=on_touch)
            cards.append(card)
            grid.add_widget(card)
        scroll.add_widget(grid)
        self.body.add_widget(scroll)
        stagger_in(cards, step=0.02)


class OperacionesScreen(MathBaseScreen):
    """Sumas o restas segun self.op."""
    op = "+"
    title_text = "Sumas"
    subtitle_text = "Un ejercicio a la vez"

    def build(self):
        t = theme()
        self.a, self.b, self.res = 1, 1, 2
        self.card = RoundedBox(bg=t["card"], radius=24, border=t["line"],
                               orientation="vertical", size_hint_y=None,
                               height="250dp", padding=[18, 18, 18, 18],
                               spacing=10)
        self.pregunta = Label(text="", color=t["text"], bold=True,
                              font_size="38sp", size_hint_y=None, height="70dp")
        self.pista = Label(text="Toma tu tiempo", color=t["text_soft"],
                           font_size="13sp", size_hint_y=None, height="22dp")
        self.card.add_widget(self.pregunta)
        self.card.add_widget(self.pista)
        self.opciones = GridLayout(cols=3, spacing=10, size_hint_y=None,
                                   height="110dp")
        self.card.add_widget(self.opciones)
        self.body.add_widget(self.card)

        self.feedback = SoftLabel("", size="15sp", bold=True, halign="center")
        self.body.add_widget(self.feedback)
        self.body.add_widget(PrimaryButton("Escuchar el ejercicio",
                                           lambda: speech.say(self._frase()),
                                           color=t["secondary"]))
        self.body.add_widget(PrimaryButton("Otro ejercicio",
                                           lambda: self.nueva(),
                                           color=t["calm"]))
        self.body.add_widget(Widget())
        self.nueva()

    def _frase(self):
        palabra = "mas" if self.op == "+" else "menos"
        return f"{self.a} {palabra} {self.b}. Cuanto es?"

    def nueva(self):
        t = theme()
        if self.op == "+":
            self.a = random.randint(1, 9)
            self.b = random.randint(1, 9)
            self.res = self.a + self.b
        else:
            self.a = random.randint(3, 12)
            self.b = random.randint(1, self.a)
            self.res = self.a - self.b
        self.pregunta.text = f"{self.a} {self.op} {self.b} = ?"
        self.feedback.text = ""
        fade_in(self.pregunta, 0.0)

        opciones = {self.res}
        while len(opciones) < 3:
            v = self.res + random.choice([-3, -2, -1, 1, 2, 3])
            if v >= 0:
                opciones.add(v)
        ops = list(opciones)
        random.shuffle(ops)

        self.opciones.clear_widgets()
        botones = []
        for v in ops:
            b = RoundedButton(bg=t["soft"], radius=20, text=str(v),
                              color=t["text"], bold=True, font_size="24sp")
            b.bind(on_release=lambda _b, val=v: self.responder(val, _b))
            botones.append(b)
            self.opciones.add_widget(b)
        stagger_in(botones, step=0.05)

    def responder(self, val, boton):
        t = theme()
        if val == self.res:
            boton.set_bg(t["soft_2"])
            self.feedback.text = "Muy bien"
            self.feedback.color = t["success"]
            speech.say("Muy bien")
            self._record(True)
            soft_pulse(self.card)
            Clock.schedule_once(lambda *_: self.nueva(), 1.6)
        else:
            boton.set_bg(t["soft_3"])
            self.feedback.text = "Casi, intenta otra vez"
            self.feedback.color = t["text_soft"]
            speech.say("Casi, intenta otra vez")
            self._record(False)


class SumasScreen(OperacionesScreen):
    op = "+"
    title_text = "Sumas"
    subtitle_text = "Sumar con calma"


class RestasScreen(OperacionesScreen):
    op = "-"
    title_text = "Restas"
    subtitle_text = "Restar con calma"


class FigurasScreen(MathBaseScreen):
    title_text = "Figuras"
    subtitle_text = "Formas basicas"

    def build(self):
        t = theme()
        self.body.add_widget(SoftLabel("Toca una figura para escucharla",
                                       size="14sp"))
        scroll = ScrollView(bar_width=4)
        grid = GridLayout(cols=2, spacing=12, padding=[4, 8, 4, 8],
                          size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        tints = [t["soft"], t["soft_2"], t["soft_3"]]
        cards = []
        for i, (nombre, desc, img) in enumerate(FIGURAS):
            card = RoundedBox(bg=tints[i % 3], radius=20, border=t["line"],
                              orientation="vertical", size_hint_y=None,
                              height="300dp", padding=[12, 12, 12, 12],
                              spacing=6)
            path = os.path.join(FIG_DIR, img)
            if os.path.exists(path):
                card.add_widget(Image(source=path, allow_stretch=True,
                                      keep_ratio=True, size_hint_y=None,
                                      height="190dp"))
            card.add_widget(Label(text=nombre, color=t["primary"], bold=True,
                                  font_size="20sp",
                                  size_hint_y=None, height="30dp"))
            card.add_widget(SoftLabel(desc, size="12sp", color=t["text_soft"],
                                      halign="center"))

            def on_touch(instance, touch, n=nombre, d=desc):
                if instance.collide_point(*touch.pos):
                    soft_pulse(instance)
                    speech.say(f"{n}. {d}")
                    self._record(True)
                    return True
            card.bind(on_touch_down=on_touch)
            cards.append(card)
            grid.add_widget(card)
        scroll.add_widget(grid)
        self.body.add_widget(scroll)
        stagger_in(cards, step=0.04)


class SeriesScreen(MathBaseScreen):
    title_text = "Series"
    subtitle_text = "Contar en orden"

    def build(self):
        t = theme()
        self.visible, self.res = [0, 2, 4], 6
        self.body.add_widget(SoftLabel(
            "Escucha la serie y elige el numero que sigue.", size="13sp",
            color=t["text_soft"]))
        self.card = RoundedBox(bg=t["card"], radius=24, border=t["line"],
                               orientation="vertical", size_hint_y=None,
                               height="220dp", padding=[18, 18, 18, 18],
                               spacing=10)
        self.serie_lbl = Label(text="", color=t["text"], bold=True,
                               font_size="26sp", size_hint_y=None, height="60dp")
        self.card.add_widget(self.serie_lbl)
        self.opciones = GridLayout(cols=3, spacing=10, size_hint_y=None,
                                   height="100dp")
        self.card.add_widget(self.opciones)
        self.body.add_widget(self.card)
        self.feedback = SoftLabel("", size="15sp", bold=True, halign="center")
        self.body.add_widget(self.feedback)
        self.body.add_widget(PrimaryButton("Escuchar la serie",
                                           lambda: speech.say(self._frase()),
                                           color=t["secondary"]))
        self.body.add_widget(PrimaryButton("Otra serie", lambda: self.nueva(),
                                           color=t["calm"]))
        self.body.add_widget(Widget())
        self.nueva()

    def _frase(self):
        return ", ".join(str(x) for x in self.visible) + ". Que sigue?"

    def nueva(self):
        t = theme()
        paso = random.choice([2, 2, 5, 10])
        inicio = random.choice([0, 2, 4, 5, 10])
        self.visible = [inicio + paso * i for i in range(3)]
        self.res = inicio + paso * 3
        self.serie_lbl.text = "  ".join(str(x) for x in self.visible) + "  ?"
        self.feedback.text = ""
        fade_in(self.serie_lbl, 0.0)

        opciones = {self.res, self.res + paso, max(0, self.res - paso)}
        while len(opciones) < 3:
            opciones.add(self.res + random.randint(1, 4))
        ops = list(opciones)
        random.shuffle(ops)
        self.opciones.clear_widgets()
        botones = []
        for v in ops:
            b = RoundedButton(bg=t["soft"], radius=20, text=str(v),
                              color=t["text"], bold=True, font_size="22sp")
            b.bind(on_release=lambda _b, val=v: self.responder(val, _b))
            botones.append(b)
            self.opciones.add_widget(b)
        stagger_in(botones, step=0.05)

    def responder(self, val, boton):
        t = theme()
        if val == self.res:
            boton.set_bg(t["soft_2"])
            self.feedback.text = "Excelente"
            self.feedback.color = t["success"]
            speech.say("Excelente")
            self._record(True)
            soft_pulse(self.card)
            Clock.schedule_once(lambda *_: self.nueva(), 1.6)
        else:
            boton.set_bg(t["soft_3"])
            self.feedback.text = "Cuenta otra vez, sin prisa"
            self.feedback.color = t["text_soft"]
            speech.say("Cuenta otra vez, sin prisa")
            self._record(False)


# ---------------------------------------------------------------- app
class OcupamorApp(App):
    title = APP_TITLE

    def build(self):
        self.sm = ScreenManager(transition=SlideTransition(duration=0.2))
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(MenuScreen(name="menu"))
        self.sm.add_widget(InicialScreen(name="inicial"))
        self.sm.add_widget(InicialHubScreen(name="inicial_hub"))
        self.sm.add_widget(AbecedarioScreen(name="abecedario"))
        self.sm.add_widget(MonosilabasScreen(name="monosilabas"))
        self.sm.add_widget(SilabasScreen(name="silabas"))
        self.sm.add_widget(VocabularioScreen(name="vocabulario"))
        self.sm.add_widget(MatematicasHubScreen(name="matematicas"))
        self.sm.add_widget(NumerosScreen(name="num_numeros"))
        self.sm.add_widget(SumasScreen(name="num_sumas"))
        self.sm.add_widget(RestasScreen(name="num_restas"))
        self.sm.add_widget(FigurasScreen(name="num_figuras"))
        self.sm.add_widget(SeriesScreen(name="num_series"))
        self.sm.add_widget(AvanzadaScreen(name="avanzada"))
        self.sm.add_widget(CalmaScreen(name="calma"))
        self.sm.add_widget(SeñasScreen(name="senas"))
        self.sm.add_widget(EmocionesScreen(name="emociones"))
        self.sm.add_widget(SettingsScreen(name="settings"))
        self.sm.add_widget(MisionesScreen(name="misiones"))
        self.sm.add_widget(MissionPlayScreen(name="mission_play"))
        self.sm.add_widget(ProgressScreen(name="progress"))
        self.sm.add_widget(DashboardScreen(name="dashboard"))
        return self.sm


if __name__ == "__main__":
    OcupamorApp().run()
