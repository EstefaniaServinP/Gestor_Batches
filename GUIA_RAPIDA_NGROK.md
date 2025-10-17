# 🚀 Guía Rápida: Exponer Dashboard con ngrok

## ✅ ngrok ya está instalado

Versión: **ngrok 3.30.0**
Ubicación: `./ngrok`

---

## 📋 Pasos para usar ngrok

### 1️⃣ Configurar authtoken (SOLO LA PRIMERA VEZ)

```bash
# Obtén tu token en: https://dashboard.ngrok.com/get-started/your-authtoken
./ngrok config add-authtoken TU_TOKEN_AQUI
```

### 2️⃣ Iniciar Dashboard con ngrok

**Opción A - Script automático (Recomendado):**
```bash
./start_with_ngrok.sh
```

**Opción B - Manual:**
```bash
# 1. Asegúrate que Gunicorn esté corriendo
ps aux | grep gunicorn

# 2. Si no está corriendo:
source venv/bin/activate
gunicorn -c gunicorn_config.py app:app &

# 3. Iniciar ngrok
./ngrok http 5000
```

### 3️⃣ Obtener tu URL pública

Cuando ngrok inicie, verás algo como:

```
Session Status                online
Forwarding                    https://xxxx-xx-xx-xx-xx.ngrok-free.app -> http://localhost:5000
```

**Copia esa URL** y compártela con quien necesites.

---

## 🛑 Detener servicios

```bash
# Detener ngrok
pkill ngrok

# Detener Gunicorn
pkill -f gunicorn
```

---

## ⚠️ IMPORTANTE

- ✅ Tu Dashboard YA está corriendo (puerto 5000)
- ✅ ngrok solo crea un túnel público a tu servidor local
- ⚠️ La URL gratis cambia cada vez que reinicias ngrok
- ⚠️ Cualquiera con la URL puede acceder al dashboard

---

## 🔐 Seguridad (Opcional)

Para agregar autenticación básica:

```bash
./ngrok http 5000 --basic-auth="usuario:contraseña"
```

---

## 📚 Documentación Completa

Ver `INSTALAR_NGROK.md` para más detalles.
