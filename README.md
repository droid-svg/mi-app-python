# OCUPAMOR Mobile

Software educativo de soporte lingüístico y fonético con **disminución
sensorial** para niños de educación básica, adaptado a **teléfonos**
(Android / iOS / escritorio) con **Kivy** en Python.

## Módulos incluidos

1. **Login** (Supabase o modo local cifrado, elige tu rol).
2. **Menú principal** con dos modos:
   - **Modo Familiar**: colores suaves, ritmo tranquilo.
   - **Modo Escolar**: alto contraste, sin sonidos ambientales.
3. **Etapa Inicial**: vocales/fonemas, sílabas y vocabulario con audio TTS.
4. **Etapa Avanzada**: trabalenguas, ordenar oraciones, comprensión lectora,
   sinónimos/antónimos y retos cognitivos.
5. **Calma Sensorial**: respiración guiada con animación de círculo.
6. **Configuración de Aprendizaje (Módulo 5)**: el adulto activa/desactiva
   categorías y crea **misiones personalizadas** (Quest Mode).
7. **Evaluación y Progreso (Módulo 6)**: reporte por sesión con
   barra de progreso, actividades a reforzar y recomendaciones.
8. **Comunicación y Lenguaje de Señas (Módulo 7)**: 12 tarjetas de
   frases diarias con gesto, uso y audio, más guía para adultos.
9. **Panel del Adulto (Módulo 8)**: historial, uso sensorial,
   recomendaciones y **exportación de reporte** en TXT.

## Cómo ejecutar (escritorio)

```bash
pip install -r requirements.txt
python main.py
```

## Cómo empaquetar para Android

```bash
pip install buildozer
buildozer -v android debug
```

El APK se genera en `bin/`.

## Variables de entorno (opcional)

Copia `.env.example` a `.env` para conectar Supabase:

```
SUPABASE_URL=...
SUPABASE_KEY=...
```

Sin Supabase la app funciona 100 % local (usuarios, progreso, misiones y
configuración se guardan cifrados/serializados en `~/.ocupamor`).

## Diseño con calma

- Tipografía grande, botones amplios (≥44 dp).
- Paletas suaves, sin destellos.
- Sin puntajes competitivos: se usan estrellas y misiones.
- Modo escolar con alto contraste y sonidos desactivados.
