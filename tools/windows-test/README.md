# Arnés de verificación en Windows

Scripts usados para verificar el visor en la máquina donde corre (DANIEL-WORK), sin
depender de que el escritorio esté renderizando. Todos se lanzan **en la sesión
interactiva** con una tarea programada (`-it` / `LogonType Interactive`), porque desde
una sesión SSH no hay escritorio.

| Script | Para qué |
| --- | --- |
| `inspect-toolbar.ps1` | Lee la barra de herramientas del visor entre procesos: cuenta botones, y para el botón de entrada remota (comando 217) da estado, índice de imagen, rectángulo y texto. Usa `VirtualAllocEx`/`WriteProcessMemory`/`ReadProcessMemory` para los mensajes que reciben un puntero — **nunca** hay que pasar un puntero propio a otro proceso. |
| `toggle-test.ps1` | Prueba de alternancia: hace clic en el botón (con la secuencia de mensajes de ratón que recibe la barra), comprueba estado/imagen/título y manda clics y teclas al escritorio remoto para contrastar con el registro del servidor de prueba. |
| `launch-in-session.ps1` | Lanza el visor instalado dentro de la sesión interactiva (usa los cmdlets `ScheduledTasks`, que citan bien la ruta con espacios). |
| `deploy.ps1` | Instala el binario compilado en `C:\Program Files\TightVNC`, respalda el anterior, crea el acceso directo y re-apunta la asociación `.vnc`. |
| `cleanup-tests.ps1` | Borra el servidor de prueba, las tareas programadas y los archivos temporales usados en la verificación. |

Combinado con `tools/fake-rfb-server.py` (servidor RFB mínimo que registra cada
mensaje del cliente) esto permite demostrar que en "solo ver" no sale ni un evento de
ratón/teclado y que al permitir la entrada sí salen.

Ejemplo completo:

```bat
:: 1. servidor de prueba (en la máquina del visor)
C:\Python314\python.exe tools\fake-rfb-server.py --port 5901 --log C:\temp\rfb-events.log

:: 2. visor contra el servidor de prueba, en la sesión interactiva
powershell -File tools\windows-test\launch-in-session.ps1

:: 3. prueba de alternancia
powershell -File tools\windows-test\toggle-test.ps1
```

Trampas conocidas (detalle en `Fork-Notes.md`): `-showcontrols` necesita `=yes`; una
ventana restaurada del registro puede venir minimizada (`-32000,-32000`), hay que
restaurarla antes de calcular clics; el ratón real no se enruta si la sesión está
desconectada; y los mensajes de barra que reciben un puntero tumban el visor si se
mandan entre procesos con un buffer propio.
