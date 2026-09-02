[app]

# (str) Título de tu aplicación
title = Software Educativo

# (str) Nombre del paquete (sin espacios ni caracteres especiales)
package.name = softwareeducativo

# (str) Dominio de la organización (en formato inverso)
package.domain = org.educativo

# (str) Directorio donde se encuentra el código fuente
source.dir = .

# (list) Extensiones de archivos que deben incluirse en la app
source.include_exts = py,png,jpg,kv,atlas,json,txt,mp3,wav

# (str) Versión de tu aplicación
version = 0.1

# (list) Dependencias de tu aplicación
requirements = python3,kivy

# (str) Orientación de la pantalla (portrait, landscape o all)
orientation = portrait

# (bool) Si la app debe mostrarse en pantalla completa
fullscreen = 0

# (list) Permisos de Android necesarios
android.permissions = INTERNET

# (int) API Objetivo de Android y API Mínima
android.api = 33
android.minapi = 21
android.sdk_build_tools_version = 33.0.2
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

# Configuración adicional necesaria para Buildozer
android.ndk_path = 
android.sdk_path =
