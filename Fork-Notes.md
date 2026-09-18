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
| `tvnviewer/resource.h`, `resource_chs.h` | IDs nuevos: `IDS_TB_REMOTEINPUT` (217), tooltips (218/219), `IDC_CSTARTVIEWONLY` (1091), `ID_CONN_REMOTE_INPUT` (40009). |
| `tvnviewer/tvnviewer.rc`, `tvnviewer_chs.rc` | Cadenas nuevas, bitmap nuevo, atajo `Ctrl+Alt+Shift+K`, casilla en el diálogo de configuración, rebranding, versión 2.8.81.1. |
| `tvnviewer/res/toolbar.bmp` | Tira de 18 imágenes de 24x24 en 32bpp **con alfa**: las 16 de comando (0..15) más los dos estados del candado (16 cerrado, 17 abierto). Generada por `tools/make-toolbar-icons.py`. |
| `gui/ToolBar.{h,cpp}` | La tira se carga en un `ImageList` `ILC_COLOR32` (`TB_SETIMAGELIST`) para conservar el alfa, y `setBitmapButtons()` desacopla "imágenes de la tira" de "botones automáticos". |
| `gui/CommonControlsEx.cpp`, `tvnviewer/main.cpp` | `ICC_STANDARD_CLASSES` + manifest de comctl32 v6: los controles de los diálogos usan el tema moderno de Windows 11. |
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
  (`"res\\toolbar.bmp"`). Con una sola barra, el compilador de recursos
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

### Icono de la aplicación

El `.ico` original traía **solo 16 y 32 px** (1078 bytes): en el menú Inicio, Alt+Tab y el
Explorador (que piden 48/256) Windows lo escalaba y se veía borroso. Se sustituyó por uno
propio con los 7 tamaños y la paleta de la familia Tobon, tomada de los iconos ya existentes
(`tobonframes.ico` y `tobonmouse.ico`, idénticos entre sí):

| Uso | Color |
| --- | --- |
| Fondo (squircle, radio ~23 %) | `#181A1F` |
| Trazo claro (gris pantalla) | `#ECEEF2` |
| Acento (candado) | `#FF5A1F` |

El motivo (monitor con el candado naranja dentro) dice lo que hace este visor: pantalla con
la entrada remota bloqueada. Se descartaron dos variantes (candado en insignia en la esquina
y candado grande delante) por desequilibradas, y el dibujo de 16 px es **específico** (sin
peana, trazo más grueso, candado más grande), porque a ese tamaño el monitor con detalles se
convierte en una mancha. Todo se regenera con `tools/make-appicon.py`.

Verificación de que el icono quedó dentro del binario, sin depender de la vista previa del
Explorador: **buscar los bytes de cada imagen del `.ico` dentro del exe** (las entradas se
guardan tal cual en `RT_ICON`). Con las 7 presentes y 0 del icono antiguo, es concluyente.
Ojo: `ExtractAssociatedIcon` **no** sirve para esto — devuelve el icono pequeño del sistema
reescalado desde otro tamaño, y parece un diseño distinto.

### La barra de herramientas: mapa implícito y frágil

Los comandos de la barra **no** vienen de una tabla: `Gui/ToolBar::attachToolBar()` los
calcula como `IDS_TB_NEWCONNECTION + i` (200..215), asigna `iBitmap = i` y marca los
separadores por **índice fijo** (`ViewerWindow::onCreate` llama a
`setViewAutoButtons(4, 6, 10, 11, 15, TB_Style_sep)`). Consecuencias que hay que respetar:

* Los `IDS_TB_*` tienen que ser consecutivos en el orden de la barra (200..215).
* Insertar un ítem en el **menú** no mueve la barra (son listas independientes): el ítem
  nuevo simplemente se añade como botón extra con su propio id (217) **después** de
  `attachToolBar()`.
* Cada separador produce **dos** entradas (un separador y un botón extra que hereda la
  imagen del índice), así que la barra acaba con 22 ranuras: 16 botones + 5 separadores +
  el candado. Verificado leyendo la barra con `TB_GETBUTTON`/`TB_GETITEMRECT` entre
  procesos (`tools/windows-test/inspect-toolbar.ps1`): comandos 200..215 con imágenes 0..15
  y el 217 con las imágenes 16/17.

### Interfaz: manifest v6 y tira de iconos con alfa

* El visor **no tenía manifest**, así que los 9 diálogos se dibujaban con el aspecto clásico
  y la barra nunca se tematizaba. Se añadió la dependencia de `Microsoft.Windows.Common-Controls`
  6.0.0.0 (pragma del enlazador en `main.cpp`) y `CommonControlsEx::init()` en la entrada del
  visor (antes solo lo hacía `tvncontrol`) con `ICC_STANDARD_CLASSES`.
  **Ojo al verificar**: el `comctl32` v6 se carga desde `WinSxS\...common-controls_6595b64144ccf1df_6.0.*`
  aunque su `FileVersion` interno diga «5.82»; la ruta es la prueba, no la versión.
* Iconos de la barra: tira de 24 px en 32bpp con alfa dibujada en el lenguaje de la familia
  (tinta `#2F3339`, acento `#FF5A1F`). `CreateToolbarEx`/`TB_ADDBITMAP` solo hacen máscara por
  color y dejan un cerco oscuro alrededor del glifo, así que la tira se carga con
  `LoadImage(..., LR_CREATEDIBSECTION)` en un `ImageList` `ILC_COLOR32` y se aplica con
  `TB_SETIMAGELIST` (+ `TB_SETBITMAPSIZE`/`TB_SETBUTTONSIZE` de 24).
* Windows 11 redondea solo las ventanas con título (`DWMWCP_DEFAULT`), así que las esquinas
  redondeadas **no** necesitan código; la barra de título oscura sí, y queda para cuando el
  cliente sea oscuro (el cliente es claro, como en TobonFrames/TobonMouse).

### MSBuild no ve las imágenes del `.rc` (un cambio de icono puede no llegar al exe)

El `.rc` referencia los bitmaps con la sintaxis del compilador de recursos
(`IDB_X BITMAP "res\\x.bmp"`), **no** con `#include`: MSBuild no registra esa dependencia, así
que al cambiar solo un `.bmp`/`.ico` el `.res` sigue siendo «más nuevo» que el `.rc`, el
compilador de recursos no vuelve a correr y el enlazador tampoco → **el exe sale idéntico al
anterior**. Pasó con la tira de la barra (se publicó una Release con el binario previo).

Regla: antes de compilar hay que **tocar el `.rc`** (`(Get-Item tvnviewer.rc).LastWriteTime = Get-Date`)
y, sobre todo, **verificar que el exe es nuevo**: comparar su `LastWriteTime` con el instante en
que arrancó el build (`$t0`) y comprobar que los bytes del recurso están dentro del binario.
Un `Select-String ': error'` sobre un log que no existe devuelve **0 errores** y da por buena una
compilación que nunca ocurrió: comprobar siempre que el log existe.

### Trampas de los scripts de prueba (segunda ronda)

* Los scripts de sondeo **deben** lanzarse en la sesión interactiva (tarea programada): desde
  SSH corren en la sesión 0 y `EnumWindows` no ve ninguna ventana del visor (parece que no
  hay barra cuando el problema es la sesión).
* En PowerShell, `$estructura.campo = valor` sobre una estructura traída de .NET **no se
  aplica**: hay que leer con `[BitConverter]::ToInt32($buf, offset)`. Con asignaciones de
  campo los informes salían con las columnas vacías.
* Las coordenadas del botón del candado **no** pueden estar fijas: al pasar los iconos a 24 px
  la barra creció y el clic de la prueba caía en «zoom −». Ahora el test localiza el botón por
  id de comando (`ButtonCenter(tb, pid, 217)`).

### La asociación `.vnc` necesita el switch (bug real de despliegue)

El visor **solo** lee un archivo de configuración con `-optionsfile=<ruta>`. La asociación
original era:

```
"C:\Program Files\TightVNC\tvnviewer.exe" -optionsfile="%1"
```

Al re-apuntarla al ejecutable nuevo sin el switch (`"<exe>" "%1"`), la ruta del `.vnc` se
interpreta como parámetro de conexión, no se parsea ningún host y el visor muestra
**"Connection parameters (host, port, socket, gates) is empty"** al abrir el archivo.
Corregido: `-optionsfile="%1"` (más `DefaultIcon`) en `HKCU` y `HKLM`
(`tools/windows-test/deploy.ps1` ya lo hace bien).

Comprobación: abrir el `.vnc` y ver el título → `fedora:99 - TobonVNC Viewer  [VIEW ONLY - remote input blocked]`.

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
