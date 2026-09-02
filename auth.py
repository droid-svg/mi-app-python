# -*- coding: utf-8 -*-
"""Autenticación (Supabase opcional, respaldo local cifrado)."""
import json
import os
import hashlib

from config import SUPABASE_URL, SUPABASE_KEY, LOCAL_USERS_FILE

_supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print("Aviso: Supabase no disponible, modo local.", e)
        _supabase = None


def _hash(p): return hashlib.sha256(p.encode("utf-8")).hexdigest()


def _load():
    if os.path.exists(LOCAL_USERS_FILE):
        try:
            return json.load(open(LOCAL_USERS_FILE, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(d):
    json.dump(d, open(LOCAL_USERS_FILE, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)


def is_supabase_enabled(): return _supabase is not None


def register(email, password, name="", role="representante"):
    email = email.strip().lower()
    if not email or not password:
        return False, "Ingresa correo y contraseña."
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    if _supabase:
        try:
            res = _supabase.auth.sign_up({
                "email": email, "password": password,
                "options": {"data": {"name": name, "role": role}},
            })
            if res and res.user:
                return True, "Cuenta creada."
            return False, "No se pudo crear la cuenta."
        except Exception as e:
            return False, f"Error: {e}"
    users = _load()
    if email in users:
        return False, "Correo ya registrado."
    users[email] = {"password": _hash(password), "name": name, "role": role}
    _save(users)
    return True, "Cuenta creada (modo local)."


def login(email, password):
    email = email.strip().lower()
    if not email or not password:
        return False, "Ingresa correo y contraseña.", None
    if _supabase:
        try:
            res = _supabase.auth.sign_in_with_password(
                {"email": email, "password": password})
            if res and res.user:
                meta = res.user.user_metadata or {}
                return True, "Bienvenido.", {
                    "email": email,
                    "name": meta.get("name", email.split("@")[0]),
                    "role": meta.get("role", "representante"),
                }
            return False, "Credenciales incorrectas.", None
        except Exception as e:
            return False, f"Error: {e}", None
    users = _load()
    u = users.get(email)
    if u and u["password"] == _hash(password):
        return True, "Bienvenido.", {
            "email": email,
            "name": u.get("name", email.split("@")[0]),
            "role": u.get("role", "representante"),
        }
    return False, "Credenciales incorrectas.", None
