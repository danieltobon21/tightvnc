# TobonVNC Viewer

Visor VNC propio, derivado del **TightVNC Viewer** (GlavSoft LLC, GNU GPL v2), con una
característica central: **las sesiones entran en "solo ver" y la entrada remota
(mouse y teclado) solo se habilita cuando tú lo decides**, con un botón en la barra
de herramientas.

Este fork sirve para mirar —sin riesgo de tocar nada sin querer— la pantalla virtual
donde corre Chrome/Playwright (Xvfb + `x11vnc` en la laptop), que es la pantalla que
usa el agente para "navegación real". Por defecto puedes ver; para tomar el control,
pulsas el candado.

---

## La característica: candado de entrada remota

| Elemento | Comportamiento |
| --- | --- |
| **Estado inicial** | Toda conexión nueva arranca en **solo ver** (`[VIEW ONLY - remote input blocked]` en la barra de título). |
| **Botón de la barra** | Candado al final de la barra: **cerrado con ojo rojo** = entrada bloqueada; **abierto con ojo verde** = entrada permitida. Es un botón con estado (se queda "hundido" cuando permite entrada). |
| **Menú** | `Allow remote input (mouse && keyboard)` en el menú de la ventana, con marca de verificación cuando está activo. |
| **Atajo** | `Ctrl+Alt+Shift+K`. |
| **Tooltip** | Describe el estado actual: "Remote input is BLOCKED (view only) - click to allow mouse and keyboard" / "Remote input is ENABLED - click to switch back to view only". |
| **Título de la ventana** | Termina en `[VIEW ONLY - remote input blocked]` o `[remote input ENABLED]`, para que el estado se vea incluso sin la barra de herramientas. |
| **Alcance** | El cambio afecta **solo la sesión actual**: al reconectar vuelve a arrancar en solo ver (no se guarda en el `.vnc`). |
| **Qué bloquea** | En solo ver el visor no envía eventos de ratón ni de teclado. Además deshabilita los botones/atajos que envían teclas (Ctrl, Alt, Ctrl+Esc, Ctrl+Alt+Del) y la transferencia de archivos. |

### Opciones

* **Configuration → "Start connections in view-only mode"** (activa por defecto): si
  la desmarcas, las conexiones nuevas empiezan con la entrada remota permitida. Se
  guarda en el registro como `StartViewOnly`.
* **Connection options → "View only (inputs ignored)"**: sigue existiendo y controla
  la sesión actual; el botón de la barra refleja el mismo estado.

---

## Compilar

Requisitos: **Visual Studio 2022 (Build Tools sirve)** con el toolset **v143** y el
Windows SDK 10.

```bat
msbuild tightvnc2019.sln /t:tvnviewer /p:Configuration=Release /p:Platform=x64 /m
```

El binario sale como `Release\x64\TobonVNCViewer.exe`.

Notas del proyecto:

* Los 35 `.vcxproj` estaban en `v140_xp` (VS2015 XP) y se **retargetearon a `v143`**
  para compilar con VS2022 sin instalar toolchains antiguos.
* Se eliminaron entradas obsoletas que apuntaban a archivos inexistentes
  (`ExtendedDesktopSizeDecoder.*`, `SetDesktopSize.*`, `KeyMap.h`, …): rompían la
  compilación con `C1083`. Ver `tools/clean-stale-project-entries.py`.

## Instalar / actualizar

1. Detener el visor y copiar `TobonVNCViewer.exe` a `C:\Program Files\TightVNC\`.
2. Actualizar el acceso directo y la asociación de `.vnc` al nuevo ejecutable:
   `tools/windows-test/deploy.ps1` hace las dos cosas y respalda el visor anterior
   en `C:\working-files\_backups\tightvnc-viewer-original`.

El **registro de configuración se mantiene a propósito** en
`HKCU\Software\TightVNC\Viewer` (`...\Settings` para las opciones, `...\History`
para el historial y los ajustes por host): así el visor conserva ajustes, historial
y contraseñas guardadas de la instalación anterior.

## Verificar

`tools/fake-rfb-server.py` es un servidor RFB mínimo que registra cada mensaje que
recibe del cliente. Con él se comprueba, sin depender de una pantalla real, que en
solo ver **no** llega ningún evento de ratón/teclado y que al permitir la entrada sí
llegan:

```bat
python tools\fake-rfb-server.py --port 5901 --log rfb-events.log
TobonVNCViewer.exe 127.0.0.1::5901 -showcontrols=yes
```

`tools/windows-test/` contiene el arnés completo (sondeo de la barra por mensajes,
prueba de alternancia del botón y lanzamiento en la sesión interactiva).

## Ramas

| Rama | Contenido |
| --- | --- |
| `main` | Build personal (esta versión). |
| `feature/tobonvnc-viewer` | Rama de trabajo de la característica, integrada en `main`. |
| `upstream` (pendiente de añadir) | Fuente original: `https://github.com/chenall/tightvnc` y, por encima, el TightVNC oficial de GlavSoft. |

## Licencia y créditos

* Base: **TightVNC 2.8.81** — Copyright (C) 2023 GlavSoft LLC. GNU GPL v2
  (`LICENSE.txt`).
* Modificaciones de este fork: © 2026 Daniel Tobon. Cada archivo tocado lleva una
  nota con el cambio.
* El aviso de copyright, la licencia y los enlaces a TightVNC se conservan en el
  visor y en el diálogo *About*.
