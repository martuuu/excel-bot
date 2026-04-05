# Contexto y Roadmap Estructurado: FIFA World Cup 2026 Ticket Bot (Python Edition)

Este documento sirve como "System Prompt" y guía maestra para asistentes de IA (Claude Code, OPUS, Sonnet, Gemini). Contiene todo el contexto, decisiones arquitectónicas, requerimientos técnicos y el roadmap paso a paso para crear un Bot de Telegram SaaS desde cero, dedicado a compras de tickets de FIFA.

---

## 🤖 1. Project Brief: Contexto General

**Rol Asignado al Agente:** Actúa como un Arquitecto de Software Senior y Desarrollador Fullstack Python experto en Web Scraping Evasivo y Bots de Telegram (aiogram). Ten en cuenta que el administrador (Martín) es un Senior Fullstack Developer (Next.js, Node.js, Tailwind, ecosistema frontend/backend amplio), por lo tanto, asume un nivel técnico avanzado, genera código limpio, arquitecturas escalables y explicaciones al grano evitando trivialidades.

**Objetivo del Proyecto:** 
Desarrollar un Bot de Telegram robusto y anti-bloqueos en Python que monitoree el portal de *hospitality* de la FIFA buscando entradas del Mundial 2026 y notifique a usuarios (con un sistema de suscripción básico). 

**Restricciones y Scope:**
- **Cero WebApps:** Toda la interacción del usuario (y administración) ocurre en Telegram.
- **Uso Mixto (Familiar / Comercial):** El bot empezará siendo usado por el administrador y familiares para pruebas, pero debe tener la capacidad de operar como un **"SaaS en Telegram"** permitiendo suscripción por uso a terceros.
- **Lenguaje:** 100% Python.

---

## 🛠 2. Decisiones Tecnológicas y Arquitectura

1. **Lenguaje: Python 3.11+ con `aiogram`**
   - **Justificación:** Python es el rey indiscutido para evadir protecciones (Cloudflare, DataDome). Escribir un bot de Telegram con `aiogram` es asíncrono, súper rápido y la sintaxis es extremadamente legible. Para alguien que viene de TypeScript, la transición usando IA tomará días y el código será un 40% más corto.

2. **Base de Datos: SQLite Local (vía SQLAlchemy / Pydantic o similar)**
   - **Justificación:** Al descartarse temporalmente la WebApp y el panel SaaS externo, una base SQLite corriendo localmente es lo óptimo. Es inmediata, no sufre latencia, y al interactuar mediante un ORM, si en el futuro decides transicionar a Supabase/PostgreSQL, bastará con cambiar el *connection string*.
   - **Requisito de Auditoría:** Obligatoriamente crear una tabla `audit_log` en el backend para trackear de forma permanente cada alerta que efectivamente haya sido enviada a un usuario (guardando producto, usuario, timestamp y variables de carrito).

3. **Infraestructura: Local (MacBook Pro i9 2019 / Servidor Headless Ubuntu Lenovo)**
   - **Hardware:** Tienes a disposición equipo pesado (MacBook Pro i9, 16GB) lo cual hace que límites de cómputo sean inexistentes, o en su defecto tu Lenovo con Ubuntu Headless. Cualquiera dominará el script asíncrono sin despeinarse.
   - **Ventaja Táctica (IP Residencial):** Usar tus máquinas locales esquiva automáticamente el 80% de los bloqueos corporativos de Datacenters de AWS o GCP.

4. **Motor de Scraping (Stealth / Anti-Bot):**
   - No usar `requests` estándar. 
   - Usar **`curl_cffi`** (que suplanta la huella TLS haciendo creer a FIFA que eres Google Chrome de Windows/Mac). En caso complejo, implementar **`undetected-chromedriver`**.

5. **Seguridad (Terceros y Familiares):**
   - **Concepto:** Telegram cifra todo nativamente de cliente a cliente. La "seguridad" correña por cuenta de Telegram.
   - **Control de Acceso:** Nadie puede usar el bot a menos que tenga su `telegram_chat_id` registrado en tu tabla `users` de Supabase con `status = 'active'`. Así puedes pasarle el link del bot a tu familia, aprobarlos manualmente (mediante un comando tuyo de ADMIN o desde el panel de Supabase) y listos.

---

## 🔍 3. Endpoints de FIFA y La "Magia" (Fifa Fetcher)

- **API Monitoreo Partidos (GET):** `/next-api/matches` y `/next-api/lounges`
- **API Add to Cart (POST):** `https://fifaworldcup26.hospitality.fifa.com/next-api/orders`
- **Payload a Emular en Compra:** 
  ```json
  {
    "ProductType": 2,
    "ProductCode": "ARG", 
    "OrderId": 0,
    "SelectedQuantity": 1,
    "PartnerId": "",
    "ServiceSelectionData": {
      "AudienceSubCategoryId": 10229206883477,
      "SeatCategoryCode": "FMT_P"
    }
  }
  ```
- **Cookies y Sesiones:** Requiere extraer e inyectar cookies como `QueueITAccepted` y potencialmente la cookie anti-bot (DataDome). El agente deberá dejar el código preparado para inyectar cookies dinámicamente vía un comando de administrador (ej: `/setcookie [cookie_string]`).

---

## 🗺️ 4. Roadmap Extendido de Construcción (Para Agente AI)

### Fase 1: Core de Telegram y Base de Datos (Día 1)
1. **Setup de Proyecto:** Crear `requirements.txt` (aiogram, sqlalchemy, aiosqlite, curl_cffi, pydantic, python-dotenv).
2. **Schema SQLite:** Crear tabla `users` (chat_id, username, is_admin, subscription_active, created_at), tabla `alerts` (ticket_code, user_id, active), y tabla `audit_log` (alert_id, user_id, timestamp, info_ticket).
3. **Bot Scaffold:** Configuración asíncrona de `aiogram`. Implementar middleware que intercepte todos los mensajes y varifique si el `chat_id` está en la DB local y tiene permisos vivos.
4. **Comandos Base:** `/start`, `/status`, `/alert [codigo]`, y bloqueador para no-administradores.

### Fase 2: Módulo "FIFA Evasivo" (Día 2)
1. **Stealth Client:** Crear una clase `FifaClient` que use `curl_cffi` con impersonación de Chrome.
2. **Mocking Headers:** Copiar headers reales (User-Agent, Accept-Language, Sec-Fetch, etc.).
3. **Parseo de Estado:** Mapear la respuesta de `/next-api/matches` hacia modelos de Pydantic. Detectar códigos `ARG`, `COL`, o los que pidan las alertas.

### Fase 3: Loop del Worker (Día 3)
1. **Scheduler Asíncrono:** Usar `asyncio` o librerías como `APScheduler` para ejecutar la revisión cada 45-60 segundos.
2. **Trigger y Notificación:** Al detectar stock, hacer un JOIN de la base de datos con los usuarios que piden ese código.
3. **Broadcasting:** Iterar sobre esos `chat_id`s y enviar mensaje de alerta.
4. **Link Mágico:** Incluir link de redirección o payload configurado para facilitar el checkout manual de terceros.

### Fase 4: Modo "SaaS Administrativo" (Fase Comercial Futura)
1. Permiso a desconocidos para usar el bot pero con `subscription_active = False` hasta la verificación.
2. Comando para el Admin (tú): `/approve [chat_id]` para activar suscripciones.
3. Notificaciones de expiración de suscripción limitadas a X meses.

---

## 🛠 5. Manual del Servidor Linux Headless (Para el Admin: Martín)

Esto te ayudará a controlar la notebook Lenovo desde tu computadora principal por SSH o directamente en su terminal negra.

**Conexión Básica (Si accedes por red Wi-Fi):**
\`\`\`bash
# Averiguar IP en la Lenovo:
ip a
# Conectar desde tu otra Mac/PC:
ssh usuario@<IP_LENOVO>
\`\`\`

**Instalación Rápida de Entorno y Git:**
\`\`\`bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git tmux tmux -y
\`\`\`

**Controlar el Bot Corriendo en Segundo Plano (USANDO TMUX o SYSTEMD):**
En servidores sin pantalla, si cierras el SSH o la laptop entra en reposo, el programa muere. Para evitarlo:

*Opción A (La más rápida con TMUX):*
\`\`\`bash
1. Crear sesión: tmux new -s fifabot
2. Correr el bot: python3 main.py
3. Para salir sin matarlo: Presiona CTRL + B, suelta, y luego presiona D (de detach).
4. Para volver a ver tu bot otro día: tmux attach -t fifabot
\`\`\`

*Opción B (La profesional con Systemd - PM2 para python):*
El asistente de IA debe proveerte un archivo `fifabot.service` para colocar en `/etc/systemd/system/`.
Comandos base:
\`\`\`bash
sudo systemctl start fifabot   # Inicia el bot
sudo systemctl enable fifabot  # Lo hace arrancar automatico si se reinicia la Lenovo
sudo journalctl -u fifabot -f  # Ver los logs en vivo
\`\`\`
