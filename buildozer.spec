[app]

# (str) Title of your application
title = Software Educativo

# (str) Package name
package.name = softwareeducativo

# (str) Package domain (needed for android/ios packaging)
package.domain = org.educativo

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,txt,mp3,wav

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# Fuerza a pythonforandroid a usar la versión estable Python 3.11 en lugar de 3.14
requirements = python3==3.11.0,kivy

# (str) Custom source folders for requirements
# Sets custom source for any requirement with recipes or site-packages
# requirement.source.kivy = ../kivy

# (list) Garden requirements
#garden_requirements =

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
#services = my service:./service.py

#
# OSX Specific
#

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for android toolchain)
#android.presplash_color = white

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk_build_tools_version = 33.0.2

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
#android.private_storage = True

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
android.ndk_path = 

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
android.sdk_path = 

# (bool) Accept SDK license automatically if needed
android.accept_sdk_license = True

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (list) Android architecture to build for
android.archs = arm64-v8a

# (bool) Enable AndroidX support. Required when targeting API 28+
android.enable_androidx = True

# (str) python-for-android branch to use
p4a.branch = master

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = ignore, 1 = warn, 2 = error)
warn_on_root = 1
