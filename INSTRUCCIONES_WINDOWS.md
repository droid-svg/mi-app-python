# OCUPAMOR Mobile - Instrucciones de Instalación (Windows)

## Paso 1: Descomprimir el archivo
1. Crea una carpeta nueva en tu computadora, por ejemplo: `C:\Users\Lenovo\ocupamor`
2. Copia el archivo `ocupamor_fixed.zip` dentro de esa carpeta
3. Haz clic derecho sobre el ZIP → "Extraer todo..." → "Extraer"

## Paso 2: Abrir la terminal en la carpeta correcta
**Método 1 (Recomendado):**
1. Abre Visual Studio Code
2. Ve a `Archivo` → `Abrir carpeta...` → selecciona la carpeta donde descomprimiste
3. Ve a `Terminal` → `Nuevo terminal`
4. Asegúrate de que la ruta en la terminal sea la carpeta del proyecto:
   ```
   PS C:\Users\Lenovo\ocupamor>
   ```

**Método 2:**
1. Abre el Explorador de archivos
2. Navega a la carpeta donde descomprimiste
3. Haz clic en la barra de direcciones arriba
4. Escribe `cmd` y presiona Enter
5. Se abrirá una terminal en esa ubicación

## Paso 3: Instalar dependencias
En la terminal (asegúrate de estar en la carpeta del proyecto):
```bash
pip install -r requirements.txt
```

## Paso 4: Ejecutar la aplicación
```bash
python main.py
```

---

## ⚠️ Errores comunes y soluciones

### Error: "No such file or directory: requirements.txt"
**Causa:** Estás ejecutando el comando desde el directorio equivocado.
**Solución:** Asegúrate de que la terminal muestre la ruta de la carpeta del proyecto.

### Error: "can't open file main.py"
**Causa:** Python no encuentra main.py porque no estás en la carpeta correcta.
**Solución:** Navega a la carpeta del proyecto antes de ejecutar.

### Error: "ModuleNotFoundError: No module named 'kivy'"
**Causa:** Las dependencias no están instaladas.
**Solución:** Ejecuta `pip install -r requirements.txt` primero.

---

## Archivos incluidos
- `main.py` - Aplicación principal (corregida)
- `auth.py` - Autenticación
- `config.py` - Configuración
- `content.py` - Contenido educativo
- `data_store.py` - Almacenamiento de datos
- `speech.py` - Texto a voz
- `requirements.txt` - Dependencias
- `README.md` - Este archivo
