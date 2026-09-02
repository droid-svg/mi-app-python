[app]

# (str) Título de tu aplicación
title = Software Educativo

# (str) Nombre del paquete
package.name = softwareeducativo

# (str) Dominio de la organización
package.domain = org.educativo

# (str) Directorio fuente
source.dir = .

# (list) Extensiones incluidas
source.include_exts = py,png,jpg,kv,atlas,json,txt,mp3,wav

# (str) Versión
version = 0.1

# (list) Dependencias explicitando versión estable de Python
requirements = python3==3.11.5,kivy

# Orientación y pantalla
orientation = portrait
fullscreen = 0

# Permisos
android.permissions = INTERNET

# Configuración de compilación Android
android.api = 33
android.minapi = 21
android.sdk_build_tools_version = 33.0.2
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

android.ndk_path = 
android.sdk_path =
