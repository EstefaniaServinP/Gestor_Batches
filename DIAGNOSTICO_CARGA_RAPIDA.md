# Diagnóstico: Error en Carga Rápida de Batches

## 🐛 Error Reportado

```
❌ Error en carga rápida:
{readyState: 4, getResponseHeader: ƒ, getAllResponseHeaders: ƒ, ...}
```

Este error indica que la petición AJAX **está fallando antes de llegar al backend**.

---

## 🔍 Causas Posibles

### 1. Servidor Flask NO está corriendo ⚠️
**Síntoma:** `readyState: 4` con error

**Solución:**
```bash
# Verificar si Flask está corriendo
ps aux | grep python | grep app.py

# Si no está corriendo, iniciarlo
python app.py
```

**Verificar en terminal:**
```bash
# Deberías ver algo como:
 * Running on http://0.0.0.0:5000
 * Running on http://192.168.1.93:5000
```

---

### 2. Puerto Incorrecto ⚠️
**Síntoma:** Error de conexión

**Verificación:**
1. Abre la consola del navegador (F12)
2. Ve a la pestaña "Network"
3. Intenta crear batches
4. Mira la URL que se está llamando

**Debería ser:**
```
POST http://192.168.1.93:5000/api/batches/quick-create
```

**Si es diferente**, verifica en `app.py` la línea donde se inicia Flask:
```python
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

---

### 3. CORS o Firewall ⚠️
**Síntoma:** `xhr.status = 0` o error de CORS

**Solución:**
Verificar que Flask tenga CORS habilitado. En `app.py` debería existir:
```python
from flask_cors import CORS
CORS(app)
```

---

### 4. Error en el Request JSON ⚠️
**Síntoma:** `xhr.status = 400` (Bad Request)

**Solución:**
Verificar que el textarea tenga contenido válido.

---

## 🧪 Pasos de Diagnóstico

### Paso 1: Verificar que Flask esté corriendo

```bash
# En terminal del servidor
ps aux | grep app.py
```

**Esperado:**
```
faservin  12345  0.5  2.1  ... python app.py
```

Si **NO aparece nada**, Flask NO está corriendo. Inícialo:
```bash
cd /home/faservin/proyectos/segmentacion-dashboard
python app.py
```

---

### Paso 2: Verificar logs de Flask

Cuando intentes crear batches, deberías ver en la terminal de Flask:

```
📝 Procesando lista de batches desde texto...
📋 3 batch IDs detectados: ['batch_TEST001', 'batch_TEST002', 'batch_TEST003']
✅ Batch batch_TEST001 creado
✅ Batch batch_TEST002 creado
✅ Batch batch_TEST003 creado
✅ Creados: 3, Ya existían: 0
```

Si **NO ves estos logs**, significa que la petición **no está llegando** al backend.

---

### Paso 3: Verificar en el navegador (mejorado)

1. Abre la consola del navegador (F12)
2. Ve a `/assign`
3. Pega esto en el textarea:
   ```
   batch_TEST001
   batch_TEST002
   ```
4. Clic en "Crear Batches"
5. Mira la consola

**Ahora deberías ver logs MÁS DETALLADOS:**
```
❌ Error en carga rápida:
  - Status: error
  - Error: [descripción del error]
  - Response Status: 0 (o 400, 500, etc.)
  - Response Text: [texto del error]
```

---

## 🔧 Soluciones según el Error

### Si `Response Status: 0`
**Causa:** El servidor NO está respondiendo (Flask apagado o puerto incorrecto)

**Solución:**
1. Iniciar Flask: `python app.py`
2. Verificar que escuche en el puerto correcto

---

### Si `Response Status: 404`
**Causa:** El endpoint no existe o la URL está mal

**Solución:**
1. Verificar que el endpoint existe en `app.py` (línea 2039)
2. Verificar la URL en el código JavaScript

---

### Si `Response Status: 400`
**Causa:** Datos inválidos en el request

**Solución:**
1. Verificar que el textarea tenga contenido
2. Verificar logs de Flask para ver el error específico

---

### Si `Response Status: 500`
**Causa:** Error interno del servidor

**Solución:**
1. Mirar logs de Flask en la terminal
2. Verificar que MongoDB esté conectado
3. Verificar que `batches_col` no sea `None`

---

### Si `Response Status: 503`
**Causa:** Base de datos no conectada

**Solución:**
Verificar en logs de Flask al iniciar:
```
✅ Conectado a MongoDB en 192.168.1.93:27017
✅ Base de datos: segmentacion_db
✅ Colección: batches
```

Si no está conectado:
```bash
# Verificar que MongoDB esté corriendo
sudo systemctl status mongod

# Si no está corriendo
sudo systemctl start mongod
```

---

## 🎯 Prueba Manual del Endpoint

Para verificar que el endpoint funciona, prueba con `curl`:

```bash
curl -X POST http://192.168.1.93:5000/api/batches/quick-create \
  -H "Content-Type: application/json" \
  -d '{"batch_list": "batch_TEST001\nbatch_TEST002\nbatch_TEST003"}'
```

**Respuesta esperada:**
```json
{
  "success": true,
  "message": "Creados: 3, Ya existían: 0",
  "created": ["batch_TEST001", "batch_TEST002", "batch_TEST003"],
  "skipped": [],
  "total_processed": 3
}
```

Si esto **funciona**, el problema está en el frontend/AJAX.
Si esto **falla**, el problema está en el backend/MongoDB.

---

## 📋 Checklist de Verificación

Marca lo que ya verificaste:

- [ ] Flask está corriendo (`ps aux | grep app.py`)
- [ ] Flask escucha en el puerto correcto (mira logs al iniciar)
- [ ] MongoDB está corriendo (`sudo systemctl status mongod`)
- [ ] La conexión a MongoDB fue exitosa (mira logs de Flask)
- [ ] El endpoint existe en `app.py` línea 2039
- [ ] Los logs detallados aparecen en la consola del navegador
- [ ] El `curl` manual funciona

---

## 🚀 Solución Rápida (Si todo lo demás falla)

1. **Reiniciar Flask:**
   ```bash
   # Detener Flask (Ctrl+C en la terminal donde corre)
   # Luego reiniciar:
   python app.py
   ```

2. **Verificar conexión a MongoDB:**
   ```bash
   mongo --host 192.168.1.93 --port 27017
   ```

3. **Limpiar caché del navegador:**
   - Presiona `Ctrl + Shift + R` para recargar sin caché
   - O ve a DevTools → Application → Clear Storage → Clear site data

4. **Reintentar la carga rápida**

---

## 📞 Próximos Pasos

Después de aplicar el fix del manejo de errores mejorado, **intenta nuevamente** y copia los logs COMPLETOS de la consola aquí:

```
❌ Error en carga rápida:
  - Status: [COPIAR AQUÍ]
  - Error: [COPIAR AQUÍ]
  - Response Status: [COPIAR AQUÍ]
  - Response Text: [COPIAR AQUÍ]
```

Con esa información podré darte una solución más específica.

---

**Documento creado:** 15 de Octubre de 2025
**Última actualización:** 15 de Octubre de 2025
