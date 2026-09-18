# Notas de mantenimiento — TobonVNC Viewer

Diario técnico del fork: qué se tocó, qué se rompió por el camino, cómo se verificó y
qué queda pendiente. Pensado para la próxima sesión (o para mí mismo dentro de seis
meses).

## 1. Punto de partida

* Fork: `danieltobon21/tightvnc`, partiendo de `chenall/tightvnc` (TightVNC 2.8.81 con
  soporte de `tvnserver.ini` y localización china).
* Lo instalado en DANIEL-WORK era **solo el visor** `tvnviewer.exe` **2.8.88.0** en
  `C:\Program Files\TightVNC`.
* Uso real: ver la pantalla virtual de la laptop (Xvfb `:99` + `x11vnc` en 5900, túnel
  SSH `-L 5900:127.0.0.1:5900` hacia el VPS) donde corre Chrome con
  `--remote-debugging-port=9222`.

## 2. Cambios de la característica

Archivos tocados (todos con nota "TobonVNC fork"):

| Archivo | Cambio |
| --- | --- |
| `tvnviewer/ViewerWindow.{h,cpp}` | Botón de la barra con dos imágenes, handler `commandRemoteInput()`, `updateRemoteInputState()`, `updateRemoteInputUI()`, tooltip según estado, sufijo de estado en el título. |
| `tvnviewer/ViewerMenu.cpp` | Ítem de menú `IDS_TB_REMOTEINPUT`. |
| `tvnviewer/ViewerInstance.cpp` | `prepareStartConfig()`: fuerza `viewOnly` al crear cada conexión. |
| `client-config-lib/ViewerConfig.{h,cpp}` | Opción `StartViewOnly` (por defecto activa). |
| `tvnviewer/ConfigurationDialog.{h,cpp}` | Casilla "Start connections in view-only mode". |
| `tvnviewer/resource.h`, `resource_chs.h` | IDs nuevos: `IDS_TB_REMOTEINPUT` (217), tooltips (218/219), `IDB_TOOLBAR_INPUT` (232), `IDC_CSTARTVIEWONLY` (1091), `ID_CONN_REMOTE_INPUT` (40009). |
| `tvnviewer/tvnviewer.rc`, `tvnviewer_chs.rc` | Cadenas nuevas, bitmap nuevo, atajo `Ctrl+Alt+Shift+K`, casilla en el diálogo de configuración, rebranding, versión 2.8.81.1. |
| `tvnviewer/res/toolbar_input.bmp` | Dos iconos 16x16 (candado cerrado con ojo rojo / abierto con ojo verde), 4bpp con la misma paleta y color de fondo que `toolbar.bmp`. Generado por `tools/make-toolbar-input-bmp.py`. |
| `tvnviewer/tvnviewer.vcxproj` | `TargetName` = `TobonVNCViewer`, retarget a `v143`. |
| Todos los `.vcxproj` | `v140_xp` → `v143` (373 configuraciones). |
| `tvnviewer/NamingDefs.cpp` | Producto a TobonVNC; **se mantiene** `Software\TightVNC\Viewer` como ruta de registro. |

Utilidades añadidas: `tools/patch-resources.py` (edición de los `.rc` en UTF-16 con
aserciones por reemplazo), `tools/make-toolbar-input-bmp.py`,
`tools/clean-stale-project-entries.py`, `tools/fake-rfb-server.py`,
`tools/windows-test/` (arnés de verificación en Windows).

## 3. Hallazgos y trampas (lo que costó tiempo)

### Compilación

* **Toolset**: el árbol venía en `v140_xp`; VS2022 Build Tools no lo trae. Retarget a
  `v143` (no hizo falta instalar nada).
* **C1083 por archivos inexistentes**: `viewer-core` referenciaba
  `ExtendedDesktopSizeDecoder.cpp` (y otros 13 casos) que no existen en esta copia.
  Nada los usa: se quitaron las entradas (`tools/clean-stale-project-entries.py`).
* **RC2135 "file not found"**: en el `.rc` la ruta debe llevar **doble barra**
  (`"res\\toolbar_input.bmp"`). Con una sola barra, el compilador de recursos
  interpreta `\t` como tabulador y no encuentra el archivo.
* **RC4206 "title string too long"**: el texto de un control de diálogo se trunca a
  **256 caracteres**. El párrafo del *About* se recortó por eso.
* Aviso inofensivo pendiente: `tvnviewer.vcxproj` referencia
  `..\tcp-dispatcher\tcp-dispatcher.vcxproj`, que no existe (`MSB9008`).
* Para regenerar el ejecutable hay que **cerrar el visor**: si está en marcha, el
  enlazador falla con `LNK1104: cannot open file ...TobonVNCViewer.exe`.

### El botón de la barra (y sus dos bugs reales)

1. **Reentrancia**: el comando llega desde un botón `TBSTYLE_CHECK`, es decir, *dentro*
   del procesamiento del clic de la propia barra. Actualizar la toolbar en ese momento
   (cambiar la imagen, el estado) desde el handler **corrompe el estado interno** y el
   proceso muere. Solución: el handler solo cambia la bandera y hace
   `PostMessage(WM_USER_REMOTE_INPUT)`; la parte de UI corre después.
2. **Excepción que escapa → `abort()`**: `viewerCoreSettings()` habla con el servidor y
   **puede lanzar** (`Failed to send data to socket.` cuando la conexión se rompe). Al
   ejecutarse desde un mensaje posteado queda fuera del manejo de excepciones del hilo
   RFB, así que la excepción llegaba al runtime de C++ y el proceso terminaba con
   `0xC0000409` (fallo rápido de `abort`, que además **no pasa por SEH**: no lo captura
   ni `SetUnhandledExceptionFilter` ni el manejador de parámetros inválidos del CRT).
   Solución: `try/catch (Exception &e)` registrando el error.

   Para localizarlo se generó mapa de enlazado (`GenerateMapFile`) y se resolvió la
   dirección del fallo: caía en la ruta de `abort` del CRT, no en `/GS`. El rastro
   temporal a archivo confirmó que el camino completo terminaba bien y que el que
   fallaba era `viewerCoreSettings()`.

### Verificación (sin depender del escritorio)

* La sesión de DANIEL-WORK puede estar **desconectada**: entonces `CopyFromScreen`
  devuelve un escritorio viejo (las capturas no muestran la ventana) y **el ratón real
  no se enruta** a las ventanas. El teclado sí llega (atajos), y los mensajes
  sintéticos sí se procesan.
* **Nunca** mandar mensajes de barra de herramientas que reciban un puntero
  (`TB_GETBUTTON`, `TB_GETITEMRECT`) desde otro proceso: el manejador escribe en la
  dirección *de tu* proceso, que no existe en el suyo → `AccessViolation` dentro de
  `comctl32`/`msvcrt` y **muerte del visor**. La forma correcta de leer la barra entre
  procesos es reservar memoria *en* el proceso destino (`VirtualAllocEx` +
  `WriteProcessMemory` + `SendMessage` + `ReadProcessMemory`), o usar mensajes sin
  punteros (`TB_BUTTONCOUNT`, `TB_GETSTATE`, `TB_GETBITMAP`).
* El botón nuevo queda como **último ítem** de la barra y, medido con buffer remoto, en
  el cliente de la barra ocupa `x=412..435, y=0..22` (la barra tiene 632x26 y deja un
  tramo vacío a la derecha: los clics "a la derecha del todo" no tocan ningún botón).
* `-showcontrols` **exige valor**: sin `=yes` interpreta "no" y **oculta** la barra.
* Una ventana restaurada desde el registro puede venir **minimizada** (rect
  `-32000,-32000`): hay que hacer `ShowWindow(SW_RESTORE)` y volver a leer la geometría
  antes de calcular clics.
* Para conceder foco real a la ventana hija del escritorio remoto (y poder probar
  teclado real) hay que usar `AttachThreadInput` + `SetFocus`; `WM_SETFOCUS` sintético
  no basta.
* Toda esta mecánica (probar en la sesión interactiva por tareas programadas
  `-it`, leer geometría, sondead la barra) está en `tools/windows-test/`.

### Verificación final (DANIEL-WORK, 2026-09-18)

Con el binario final, contra `tools/fake-rfb-server.py`:

* Arranque en solo ver: estado del botón `0x4`, imagen 21, título
  `[VIEW ONLY - remote input blocked]`. Sin eventos en el servidor.
* Cuatro clics seguidos en el botón: solo ver ↔ permitido, con la imagen cambiando
  21 ↔ 22 y el título actualizándose; el proceso sobrevive.
* Clics/teclas en el escritorio remoto: **cero** eventos mientras está bloqueado; tres
  eventos `POINTER` (mover, pulsar, soltar) cuando está permitido.
* Prueba de despliegue: el `.vnc` guardado abre `TobonVNCViewer.exe` (asociación
  re-apuntada) y el visor instalado arranca en solo ver.

## 4. Pendientes / observaciones

* `HKLM\...\Run` tiene `tvncontrol = "C:\Program Files\TightVNC\tvnserver.exe" -controlservice -slave`
  apuntando a un ejecutable que **no existe** (residuo anterior a este trabajo: la
  instalación era solo visor). No se tocó; si molesta en el arranque, borrar el valor.
* El servidor del fork (`tvnserver`) no se rebrandeó ni se compiló: en DANIEL-WORK no
  se usa. Si algún día se quiere, el cambio es análogo (`NamingDefs` del servidor +
  `.rc`/`.vcxproj`).
* El visor sigue ofreciendo "Commercial Licensing" de GlavSoft en el diálogo *About*
  como crédito al proyecto original; el botón "Source Code (Fork)" abre este repo.
* Base 2.8.81 (el visor que estaba instalado era 2.8.88): si se quiere equiparar con
  versiones nuevas de TightVNC, hay que traer los cambios de upstream a mano (este
  fork sale de la copia de `chenall`).
