# 🏥 Dashboard de Segmentación de Imágenes Médicas

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Status](https://img.shields.io/badge/status-stable-green.svg)
![Python](https://img.shields.io/badge/python-3.x-blue.svg)

Sistema web para gestionar la asignación y seguimiento de batches de segmentación de imágenes médicas.

## 🎯 Características Principales

- **👥 Vista de Equipo**: Página principal con tarjetas visuales de cada miembro
- **📊 Dashboard Interactivo**: Gestión completa de batches con filtros
- **⚡ Edición Inline**: Cambio directo de estados y fechas límite
- **🗄️ Base de Datos MongoDB**: Persistencia de datos
- **📱 Responsive Design**: Funciona en cualquier dispositivo

## 🚀 Tecnologías Utilizadas

- **Backend**: Python Flask
- **Base de Datos**: MongoDB
- **Frontend**: Bootstrap 5, jQuery, DataTables
- **Iconos**: Font Awesome

## 📁 Estructura del Proyecto

```
segmentacion-dashboard/
├── app.py                 # Aplicación Flask principal
├── requirements.txt       # Dependencias Python
├── batches,json          # Datos iniciales de batches
├── templates/            # Plantillas HTML
│   ├── team.html         # Página principal del equipo
│   ├── dashboard.html    # Dashboard de gestión
│   └── masks.html        # Vista de máscaras MongoDB
├── test_api.py           # Script de pruebas de API
└── README.md             # Este archivo
```

## 🛠️ Instalación y Configuración

### Prerrequisitos
- Python 3.x
- MongoDB en ejecución
- Conexión a internet (para CDNs de Bootstrap y jQuery)

### Instalación de Dependencias

```bash
# Instalar dependencias del sistema (Ubuntu/Debian)
sudo apt update
sudo apt install python3-flask python3-pymongo -y

# O usando pip (si está disponible)
pip install -r requirements.txt
```

### Configuración de MongoDB

1. Asegúrate de que MongoDB esté ejecutándose
2. Actualiza la cadena de conexión en `app.py`:
   ```python
   MONGO_URI = "mongodb://admin:password@host:port/?authSource=admin"
   ```

### Ejecución

```bash
python3 app.py
```

La aplicación estará disponible en: `http://localhost:5001`

## 🎮 Uso del Sistema

### 1. Página Principal - Vista del Equipo
- Muestra tarjetas de cada miembro del equipo
- Estadísticas en tiempo real de batches asignados
- **Doble clic** en cualquier miembro para ver sus batches

### 2. Dashboard de Gestión
- **Edición Inline**: Cambia estados y fechas directamente en la tabla
- **Filtros**: Por responsable, estado, etc.
- **Gestión Completa**: Crear, editar, eliminar batches

### 3. Estados de Batch
- 🟡 **Pendiente**: Sin comenzar
- 🔵 **En Progreso**: En proceso de segmentación
- 🟢 **Completado**: Segmentación finalizada

## 🗂️ Concepto de "Carpeta"

Cada batch representa una **carpeta física** con imágenes médicas:

- **Ejemplo**: `/imagenes/tomografias/lote_9`
- **Contenido**: 150 imágenes de tomografías de tórax
- **Proceso**: Segmentación manual por especialista

## 📊 API Endpoints

- `GET /api/batches` - Obtener todos los batches
- `POST /api/batches` - Crear nuevo batch
- `PUT /api/batches/<id>` - Actualizar batch
- `DELETE /api/batches/<id>` - Eliminar batch
- `POST /api/reset-batches` - Recargar datos desde JSON

## 🧪 Pruebas

Ejecuta el script de pruebas para verificar la API:

```bash
python3 test_api.py
```

## 👥 Equipo de Desarrollo

- **Responsables de Segmentación**: Mauricio, Maggie, Ceci, Flor, Ignacio
- **Tipo de Imágenes**: Tomografías, Resonancias, Ultrasonidos, Rayos X

## 📄 Licencia

Este proyecto es para uso interno del equipo de segmentación de imágenes médicas.

---

**Última actualización**: Julio 23, 2025
