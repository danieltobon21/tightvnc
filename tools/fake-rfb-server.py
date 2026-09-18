#!/usr/bin/env python3
"""
Minimal RFB (VNC) server used to test TobonVNC Viewer's remote-input toggle.

It completes the RFB 3.8 handshake with "None" authentication, draws one solid
frame, and then logs every client-to-server message it receives. That makes it
possible to prove, without a real desktop, that the viewer sends no pointer or
keyboard event while remote input is blocked and sends them as soon as the user
allows it.

    python fake-rfb-server.py --port 5901 --log rfb-events.log

Log lines:
    CONNECTED / DISCONNECTED  client connection lifecycle
    POINTER mask=.. x=.. y=..  pointer event (mouse move / button / wheel)
    KEY down=.. keysym=..      key event
    FBREQUEST incremental=..   framebuffer update request (harmless)
"""
import argparse
import socket
import struct
import sys
import threading
import time

SCREEN_W = 640
SCREEN_H = 480

_log_lock = threading.Lock()
_log_path = None


def log(message):
    now = time.time()
    line = "%s.%03d  %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
                            int((now % 1) * 1000), message)
    with _log_lock:
        print(line, flush=True)
        if _log_path:
            with open(_log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")


def recv_exact(sock, count):
    data = b""
    while len(data) < count:
        chunk = sock.recv(count - len(data))
        if not chunk:
            raise ConnectionError("client closed the connection")
        data += chunk
    return data


PIXEL_FORMAT = struct.pack(">BBBBHHHBBBxxx",
                           32,   # bits per pixel
                           24,   # depth
                           0,    # big endian flag
                           1,    # true colour flag
                           255, 255, 255,   # max red / green / blue
                           16, 8, 0)        # shifts


def send_frame(conn):
    """Send one raw framebuffer update: a vertical grey gradient."""
    header = struct.pack(">BBH", 0, 0, 1)                  # FramebufferUpdate, 1 rect
    rect = struct.pack(">HHHHi", 0, 0, SCREEN_W, SCREEN_H, 0)  # x, y, w, h, encoding=raw
    row = bytearray()
    for x in range(SCREEN_W):
        value = int(40 + 180 * x / SCREEN_W)
        row += struct.pack("<BBBB", value, value, value, 0)
    conn.sendall(header + rect + bytes(row) * SCREEN_H)


def serve(conn, addr):
    try:
        conn.sendall(b"RFB 003.008\n")
        version = recv_exact(conn, 12)
        log("CONNECTED   %s:%d  (client %s)" % (addr[0], addr[1], version.strip().decode("ascii", "replace")))

        conn.sendall(bytes([1, 1]))            # one security type: None (1)
        recv_exact(conn, 1)                    # client picks the security type
        conn.sendall(struct.pack(">I", 0))     # SecurityResult: OK
        recv_exact(conn, 1)                    # ClientInit (shared flag)

        name = b"TobonVNC test server"
        conn.sendall(struct.pack(">HH", SCREEN_W, SCREEN_H) + PIXEL_FORMAT +
                     struct.pack(">I", len(name)) + name)

        frame_sent = False
        while True:
            msg_type = recv_exact(conn, 1)[0]

            if msg_type == 0:                                   # SetPixelFormat
                recv_exact(conn, 19)
                log("SETPIXELFMT")
            elif msg_type == 2:                                 # SetEncodings
                pad, count = struct.unpack(">BH", recv_exact(conn, 3))
                encodings = struct.unpack(">%di" % count, recv_exact(conn, 4 * count))
                log("SETENCODINGS count=%d %s" % (count, ",".join(str(e) for e in encodings)))
            elif msg_type == 3:                                 # FramebufferUpdateRequest
                incremental, x, y, w, h = struct.unpack(">BHHHH", recv_exact(conn, 9))
                log("FBREQUEST  incremental=%d %dx%d+%d+%d" % (incremental, w, h, x, y))
                if not incremental or not frame_sent:
                    send_frame(conn)
                    frame_sent = True
            elif msg_type == 4:                                 # KeyEvent
                down, pad, key = struct.unpack(">BBHI", recv_exact(conn, 7))
                log("KEY        down=%d keysym=0x%08x" % (down, key))
            elif msg_type == 5:                                 # PointerEvent
                mask, x, y = struct.unpack(">BHH", recv_exact(conn, 5))
                log("POINTER    mask=%d x=%d y=%d" % (mask, x, y))
            elif msg_type == 6:                                 # ClientCutText
                recv_exact(conn, 3)                             # padding
                length = struct.unpack(">I", recv_exact(conn, 4))[0]
                recv_exact(conn, length)
                log("CUTTEXT    length=%d" % length)
            else:
                log("UNKNOWN    message type %d - closing" % msg_type)
                break
    except (ConnectionError, OSError) as error:
        log("DISCONNECTED %s:%d (%s)" % (addr[0], addr[1], error))
    finally:
        try:
            conn.close()
        except OSError:
            pass


def main():
    global _log_path
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5901)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--log", default=None)
    args = parser.parse_args()

    _log_path = args.log
    if _log_path:
        with open(_log_path, "w", encoding="utf-8") as f:
            f.write("")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((args.bind, args.port))
    server.listen(4)
    log("LISTENING  %s:%d (screen %dx%d)" % (args.bind, args.port, SCREEN_W, SCREEN_H))

    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=serve, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        log("STOPPED")
    finally:
        server.close()


if __name__ == "__main__":
    sys.exit(main())
