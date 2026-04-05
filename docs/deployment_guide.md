# Guía de Despliegue en Producción (Ubuntu / Mac)

Este documento contiene las instrucciones precisas para encender tu bot SaaS de forma resiliente, asegurando que se auto-recupere tras reinicios del servidor y pueda ejecutar navegadores invisibles.

## 0.1 Setup Inicial en macOS Limpia
Si acabas de formatear la Mac o es una MacBook Pro dedicada desde cero, ejecuta esto primero:

1. **Xcode Command Line Tools:** `xcode-select --install`
2. **Homebrew:** `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
3. **Dependencias Core:** `brew install python@3.11 tmux git`

---

## 0. Requisitos del Proyecto

En cualquier servidor que decidas usar (tu Mac de casa o la Lenovo con Ubuntu headless), asegúrate de clonar el repositorio, entrar a la carpeta y ejecutar:

```bash
# 1. Crear entorno y activar
python3 -m venv venv
source venv/bin/activate

# 2. Instalar el bot
pip install -r requirements.txt

# 3. Descargar los navegadores de Playwright
playwright install chromium
```

### Solo para Servidores Linux Headless (La Lenovo con Ubuntu)
Playwright necesita dependencias visuales de sistema y utilidades de entorno X11 virtual si está en un entorno donde no hay interfaz gráfica instalada:
```bash
sudo apt update && sudo apt install -y xvfb
playwright install-deps
```

---

## Estrategia 1: Despliegue Robusto (Systemd en Ubuntu) 🌟 Recomendada
Esta estrategia convierte tu bot en un ciudadano nativo de Linux. El bot arrancará automáticamente si se te corta la luz y vuelve, e imprimirá los logs hermosos.

### 1.1 Crear archivo de servicio
Desde tu terminal de Ubuntu:
```bash
sudo nano /etc/systemd/system/fifabot.service
```

Pega exactamente esto (ajusta `/home/usuario/Documents/bot` a donde realmente esté clonada tu carpeta):

```ini
[Unit]
Description=Fifa Ticket Bot Service con xvfb
After=network.target

[Service]
Type=simple
User=root
# Ajustar rutas según necesidad:
WorkingDirectory=/ruta/a/tu/proyecto/bot
# XVFB-run permiete correr Playwright simulando una pantalla de servidor
ExecStart=/usr/bin/xvfb-run -a /ruta/a/tu/proyecto/bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 1.2 Encender y Monitorear
```bash
sudo systemctl daemon-reload
sudo systemctl enable fifabot    # Arranca al reiniciar
sudo systemctl start fifabot     # Enender ahora mismito

# Ver los logs en vivo (verás si atrapa Captchas o funciona cool):
sudo journalctl -u fifabot -f
```

---

## Estrategia 2: Despliegue Semi-Manual (Tmux en MAC y Ubuntu)
Si solo quieres correrlo ocasionalmente en la Mac y que no muera al minimizar la terminal.

1. Instala Tmux (`brew install tmux` en Mac o `sudo apt install tmux` en Ubuntu).
2. Crea una sesión virtual:
   ```bash
   tmux new -s fifabot
   ```
3. Activa tu entorno y corre tu bot de fondo:
   ```bash
   source venv/bin/activate
   # Si usas mac:
   python main.py
   # Si usas linux (Lenovo):
   xvfb-run -a python main.py
   ```
4. Minimiza la instancia presionando `Ctrl + B`, suelta todo, y aprieta `D` (detach). 
5. Si pasado el mes quieres saber qué estubo haciendo el bot, simplemente tipea:
   ```bash
   tmux attach -t fifabot
   ```

---

## 🍏 Estrategia 3: MacBook Dedicada (Tapa Cerrada y Ahorro de Energía)
Si vas a utilizar la MacBook Pro 2019 i9 como servidor para tus familiares, el gran problema de macOS es que detendrá los procesos en segundo plano al cerrar la tapa. Para evitarlo sin sobrecalentar el equipo y usando los mínimos recursos, debes usar `caffeinate`.

### 3.1 Prevenir la suspensión al cerrar la tapa
**Opción A (Comando Nativo y Ligero - Recomendado):**
macOS incluye la utilidad de línea de comandos `caffeinate` que previene que la Mac se duerma.
Dentro de una sesión de `tmux`, puedes ejecutar el bot forzándolo a mantenerse activo:
```bash
tmux new -s fifabot
source venv/bin/activate
# -i evita suspensión del sistema (idle), -s evita suspensión por batería
caffeinate -is python main.py
```
*Nota:* Para que la Mac no se apague **con la tapa cerrada**, la laptop **DEBE** estar conectada a la corriente (cargador de batería activo) usando `caffeinate`.

**Opción B (App Amphetamine):**
Si quieres evitar problemas de Terminal y lidiar con la tapa de forma visual, puedes descargar la app gratuita "Amphetamine" de la Mac App Store, encenderla indefinidamente y destildar la opción de "Allow system to sleep when display is closed".

### 3.2 Optimizar Recursos de la Mac
Para consumir lo mínimo indispensable:
1. **Baja el Brillo a Cero:** Si no usas la pantalla.
2. **Usa `playwright` limpio:** El bot en `session_manager.py` ya está diseñado para ejecutarse en modo `headless=True`, esto asegura que el navegador virtual (Chromium) no genere renderizado gráfico real, reduciendo la carga de CPU y GPU a la mitad.
3. **Tmux de Fondo:** Nunca dejes la ventana de tu Mac Terminal maximizada de frente, dejalo adjuntado en `tmux` en el background y apaga la pantalla, así WindowServer de macOS no gasta procesador re-dibujando la consola con cada log `print`.

### 3.3 Auto-Arranque tras Cortes de Luz (Mac)
¡Sí! macOS también tiene un excelente manejo para auto-recuperarse como un servidor real, solo necesitas configurar dos cosas:

**Paso 1: Encender la Mac sola cuando vuelva la tensión**
Abre la terminal y ejecuta este comando para modificar la energía desde el hardware:
```bash
sudo pmset -a autorestart 1
```

**Paso 2: Auto-Logueo**
Ve a **Preferencias del Sistema (System Settings) > Usuarios y Grupos** y configura **"Iniciar sesión automáticamente como: [Tu Usuario]"**. Si la Mac se reinicia y se queda en la pantalla de contraseña, los programas de usuario no arrancan.

**Paso 3: Que arranque el bot solo (Automator o Launchd)**
La forma más sencilla y sin usar código para ejecutar tu `tmux` con el bot al arrancar es usar la app nativa **Automator**:
1. Abre Autómator y crea una nueva **"Aplicación"**.
2. Arrastra la acción **"Ejecutar script de la shell"** (Run Shell Script).
3. Pega este código (ajustando las rutas):
   ```bash
   # Carga las variables de entorno de tu usuario
   source ~/.zshrc
   cd /Users/martinnavarro/Documents/bot
   # Crea una sesion tmux detached e inicia el bot con caffeinate
   /usr/local/bin/tmux new-session -d -s fifabot 'source venv/bin/activate && /usr/bin/caffeinate -is python main.py'
   ```
4. Guarda como `FifaBot_Start.app`.
5. Ve a **Preferencias del Sistema > General > Ítems de inicio (Login Items)** y agrega tu nueva app `FifaBot_Start.app`.

Listo, si se corta la luz, la Mac se encenderá sola, pondrá tu usuario sola, y lanzará el bot de fondo.

---

## Notas adicionales sobre DataDome
Si el bot te alerta por Telegram: *"🚨 CRÍTICO: La Auto-Renovación topó con el Slider"*, solo necesitas ir a tu computadora, abrir Chrome manualmente, ir al portal de la fifa, copiar tus cookies frescas tal y cual hiciste al iniciar, y copiarlas en `cookies.json` o presionar `Ctrl+C` en el bot e inyectarlas en `test_scrape.py` para forzar su absorción.
