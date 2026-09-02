# -*- coding: utf-8 -*-
"""Almacenamiento local: progreso, configuración de aprendizaje y misiones."""
import json
import os
from datetime import datetime

from config import (
    PROGRESS_FILE, SETTINGS_FILE, MISSIONS_FILE, LEARNING_CATEGORIES
)


def _read(path, default):
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            return default
    return default


def _write(path, data):
    json.dump(data, open(path, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)


# ------------------- Configuración de aprendizaje (Módulo 5) -----------------
def get_settings(email):
    all_ = _read(SETTINGS_FILE, {})
    if email not in all_:
        all_[email] = {
            "categories": {k: True for k, _ in LEARNING_CATEGORIES},
            "session_size": 10,
        }
        _write(SETTINGS_FILE, all_)
    return all_[email]


def save_settings(email, settings):
    all_ = _read(SETTINGS_FILE, {})
    all_[email] = settings
    _write(SETTINGS_FILE, all_)


# ------------------- Misiones (Quest Mode, Módulo 5) --------------------------
def get_missions(email):
    all_ = _read(MISSIONS_FILE, {})
    return all_.get(email, [])


def save_missions(email, missions):
    all_ = _read(MISSIONS_FILE, {})
    all_[email] = missions
    _write(MISSIONS_FILE, all_)


def add_mission(email, title, target, category):
    m = get_missions(email)
    m.append({
        "id": len(m) + 1, "title": title, "target": int(target),
        "category": category, "progress": 0, "done": False,
        "created": datetime.now().isoformat(timespec="seconds"),
    })
    save_missions(email, m)


def bump_mission(email, category, amount=1):
    m = get_missions(email)
    changed = False
    for x in m:
        if not x["done"] and x["category"] == category:
            x["progress"] = min(x["target"], x["progress"] + amount)
            if x["progress"] >= x["target"]:
                x["done"] = True
            changed = True
    if changed:
        save_missions(email, m)


# ------------------- Progreso y sesiones (Módulo 6) --------------------------
def get_progress(email):
    all_ = _read(PROGRESS_FILE, {})
    return all_.get(email, {
        "points": 0, "sessions": [], "sensory_uses": 0,
        "totals": {k: {"ok": 0, "fail": 0} for k, _ in LEARNING_CATEGORIES},
    })


def save_progress(email, data):
    all_ = _read(PROGRESS_FILE, {})
    all_[email] = data
    _write(PROGRESS_FILE, all_)


def record_activity(email, category, correct):
    p = get_progress(email)
    p["totals"].setdefault(category, {"ok": 0, "fail": 0})
    if correct:
        p["totals"][category]["ok"] += 1
        p["points"] += 5
        bump_mission(email, category, 1)
    else:
        p["totals"][category]["fail"] += 1
    save_progress(email, p)


def record_session(email, total, correct, sensory_used=False):
    p = get_progress(email)
    p["sessions"].append({
        "date": datetime.now().isoformat(timespec="seconds"),
        "total": total, "correct": correct,
        "sensory_used": sensory_used,
    })
    if sensory_used:
        p["sensory_uses"] += 1
    save_progress(email, p)


def recommend_next(email):
    """Sugiere categorías con más fallos."""
    p = get_progress(email)
    ranking = []
    for k, label in LEARNING_CATEGORIES:
        t = p["totals"].get(k, {"ok": 0, "fail": 0})
        total = t["ok"] + t["fail"]
        if total == 0:
            score = 0.5
        else:
            score = t["fail"] / total
        ranking.append((score, label))
    ranking.sort(reverse=True)
    return [lbl for _, lbl in ranking[:3]]


def export_report(email):
    """Genera un reporte de texto simple exportable (Módulo 8)."""
    p = get_progress(email)
    lines = [
        f"Reporte OCUPAMOR — {email}",
        f"Generado: {datetime.now().isoformat(timespec='seconds')}",
        f"Puntos totales: {p['points']}",
        f"Usos de regulación sensorial: {p['sensory_uses']}",
        "",
        "Desempeño por categoría:",
    ]
    for k, label in LEARNING_CATEGORIES:
        t = p["totals"].get(k, {"ok": 0, "fail": 0})
        lines.append(f"  - {label}: {t['ok']} correctas / {t['fail']} a reforzar")
    lines += ["", "Últimas sesiones:"]
    for s in p["sessions"][-10:]:
        pct = int((s["correct"] / s["total"]) * 100) if s["total"] else 0
        lines.append(f"  {s['date']}  {s['correct']}/{s['total']} ({pct}%)"
                     f"{'  [sensorial]' if s.get('sensory_used') else ''}")
    lines += ["", "Recomendado para próxima sesión:"]
    for r in recommend_next(email):
        lines.append(f"  • {r}")
    path = os.path.join(os.path.dirname(PROGRESS_FILE),
                        f"reporte_{email.replace('@','_')}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path
