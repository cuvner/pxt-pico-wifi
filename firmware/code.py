# Pico W CircuitPython AT modem (UART) → WiFi + MQTT (Adafruit IO friendly)
# Use $circup install --auto  to install dependencies
# UART wiring: micro:bit P0 (TX) -> Pico GP1 (RX), optional Pico GP0 (TX) -> micro:bit P1 (RX), GND↔GND
# Baud: 115200

import time, json, microcontroller
import board, busio, digitalio
import wifi
import socketpool
import adafruit_minimqtt.adafruit_minimqtt as MQTT

# ---------------- UART + LED ----------------
uart = busio.UART(tx=board.GP0, rx=board.GP1, baudrate=115200, timeout=0.05)
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

def println(msg: str):
    # to UART (micro:bit) + USB REPL
    try:
        uart.write((msg + "\n").encode("utf-8"))
    except Exception:
        pass
    print(msg)

# ---------------- State / Config ----------------
CONFIG_FILE = "modem_config.json"
state = {
    "wifi": {"ssid": None, "pwd": None},
    "aio":  {"user": None, "key": None},
    "feeds": [],          # e.g. ["mb-temp","mb-light"]
    "mode": "CSV"         # CSV or RAW
}
client = None
pool = None

# Publish pacing (safety net; you can still throttle on the micro:bit)
last_pub = 0.0
min_interval = 1.5  # seconds; keep >=1s to be friendly to Adafruit IO

def load_config():
    global state
    try:
        with open(CONFIG_FILE, "r") as f:
            raw = json.loads(f.read())
        # normalize
        if "wifi" in raw and isinstance(raw["wifi"], dict):
            state["wifi"]["ssid"] = raw["wifi"].get("ssid")
            state["wifi"]["pwd"]  = raw["wifi"].get("pwd")
        if "aio" in raw and isinstance(raw["aio"], dict):
            state["aio"]["user"] = raw["aio"].get("user")
            state["aio"]["key"]  = raw["aio"].get("key")
        feeds = raw.get("feeds", [])
        state["feeds"] = feeds if isinstance(feeds, list) else ([feeds] if feeds else [])
        m = raw.get("mode", "CSV")
        state["mode"] = "CSV" if str(m).upper() == "CSV" else "RAW"
        println("OK:LOADED")
    except Exception as e:
        println(f"ERR:LOAD:{repr(e)}")

def save_config():
    try:
        with open(CONFIG_FILE, "w") as f:
            f.write(json.dumps(state))
        println("OK:SAVED")
    except Exception as e:
        println(f"ERR:SAVE:{repr(e)}")

# ---------------- WiFi / MQTT ----------------
def wifi_connect():
    ssid = state["wifi"]["ssid"]
    pwd  = state["wifi"]["pwd"]
    if not ssid or not pwd:
        println("WIFI:ERR:MISSING_CREDS")
        return False
    if not wifi.radio.connected:
        println(f"WIFI:CONNECTING:{ssid!r}")
        try:
            wifi.radio.connect(ssid, pwd)
        except Exception as e:
            println(f"WIFI:ERR:{repr(e)}")
            return False
    println(f"WIFI:OK:{wifi.radio.ipv4_address}")
    return True

def make_client():
    global pool
    if pool is None:
        pool = socketpool.SocketPool(wifi.radio)
    # Use non-SSL port 1883 for simplicity (AIO supports it)
    return MQTT.MQTT(
        broker="io.adafruit.com",
        username=state["aio"]["user"],
        password=state["aio"]["key"],
        socket_pool=pool,
        port=1883,
        is_ssl=False,
        client_id="pico-" + microcontroller.cpu.uid.hex()
    )

def mqtt_on_message(mq, topic, msg):
    println(f"RXMQTT:{topic}:{msg}")

def mqtt_connect():
    global client
    if not state["aio"]["user"] or not state["aio"]["key"]:
        println("MQTT:ERR:MISSING_AIO")
        return False
    if client is None:
        client = make_client()
        client.on_message = mqtt_on_message
    println("MQTT:CONNECTING")
    try:
        client.connect()
        println("MQTT:OK")
        return True
    except Exception as e:
        println(f"MQTT:ERR:{repr(e)}")
        return False

def mqtt_connected():
    if not client:
        return False
    try:
        return client.is_connected() if callable(client.is_connected) else bool(client.is_connected)
    except Exception:
        return False

def _rate_ok():
    global last_pub
    now = time.monotonic()
    if now - last_pub < min_interval:
        # Uncomment to visualize throttling:
        # println("SKIP:RATE")
        return False
    last_pub = now
    return True

def publish_idx(idx: int, val: str):
    if not (0 <= idx < len(state["feeds"])):
        println("ERR:SEND:IDX")
        return
    if not _rate_ok():
        return
    topic = f"{state['aio']['user']}/feeds/{state['feeds'][idx]}"
    try:
        client.publish(topic, val)
        println(f"ACK:{state['feeds'][idx]}:{val}")
    except Exception as e:
        println(f"ERR:SEND:{repr(e)}")

def publish_csv(csv_line: str):
    if not state["feeds"]:
        println("ERR:FEEDS:EMPTY")
        return
    if not _rate_ok():
        return
    parts = [p.strip() for p in csv_line.split(",") if p.strip() != ""]
    for i, val in enumerate(parts):
        if i >= len(state["feeds"]):
            break
        feed = state["feeds"][i]
        topic = f"{state['aio']['user']}/feeds/{feed}"
        try:
            client.publish(topic, val)
            println(f"ACK:{feed}:{val}")
        except Exception as e:
            println(f"ERR:PUB:{feed}:{repr(e)}")

# ---------------- AT parsing & handlers ----------------
def parse_args(body: str):
    # split on commas outside quotes
    args, cur, inq = [], "", False
    for c in body:
        if c == '"':
            inq = not inq
        elif c == "," and not inq:
            args.append(cur); cur = ""
        else:
            cur += c
    if cur:
        args.append(cur)
    return [a.strip().strip('"') for a in args]

def at_wifi(args):
    # AT+WIFI="SSID","PASS"
    a = parse_args(args)
    if len(a) < 2: println("ERR:AT:WIFI:ARGS"); return
    state["wifi"]["ssid"], state["wifi"]["pwd"] = a[0], a[1]
    println("OK:WIFI:SET")

def at_aio(args):
    # AT+AIO="user","key"
    a = parse_args(args)
    if len(a) < 2: println("ERR:AT:AIO:ARGS"); return
    state["aio"]["user"], state["aio"]["key"] = a[0], a[1]
    println("OK:AIO:SET")

def at_feeds(args):
    # AT+FEEDS="f1","f2",...
    state["feeds"] = parse_args(args)
    println("OK:FEEDS:SET")

def at_mode(args):
    # AT+MODE=CSV|RAW
    m = (args or "").strip().upper()
    if m in ("CSV","RAW"):
        state["mode"] = m
    println(f"OK:MODE:{state['mode']}")

def at_connect(_args=None):
    if wifi_connect():
        mqtt_connect()

def at_send(args):
    # AT+SEND=<index>,<value>  OR  AT+SEND=val1,val2,val3 (CSV shorthand)
    if not mqtt_connected(): println("ERR:SEND:NO_MQTT"); return
    a = parse_args(args)
    if len(a) == 0:
        println("ERR:SEND:ARGS"); return
    # If looks like CSV-of-values (no explicit index)
    if len(a) == 1 or all((x.replace('.','',1).lstrip('-').isdigit()) for x in a):
        publish_csv(",".join(a))
        println("OK:SEND")
        return
    # index,value mode
    try:
        idx = int(a[0])
        val = a[1]
        publish_idx(idx, val)
        println("OK:SEND")
    except Exception as e:
        println(f"ERR:SEND:{repr(e)}")

def at_pub(args):
    # AT+PUB="topic","payload"
    if not mqtt_connected(): println("ERR:PUB:NO_MQTT"); return
    a = parse_args(args)
    if len(a) < 2: println("ERR:PUB:ARGS"); return
    if not _rate_ok():
        return
    try:
        client.publish(a[0], a[1]); println("OK:PUB")
    except Exception as e:
        println(f"ERR:PUB:{repr(e)}")

def at_sub(args):
    # AT+SUB="topic"
    if not mqtt_connected(): println("ERR:SUB:NO_MQTT"); return
    a = parse_args(args)
    if len(a) < 1: println("ERR:SUB:ARGS"); return
    try:
        client.subscribe(a[0]); println("OK:SUB")
    except Exception as e:
        println(f"ERR:SUB:{repr(e)}")

def at_led(args):
    v = (args or "").strip().upper()
    if v == "ON": led.value = True; println("OK:LED:ON")
    elif v == "OFF": led.value = False; println("OK:LED:OFF")
    else: println("ERR:LED:ARG")

def at_status(_args=None):
    w = "YES" if wifi.radio.connected else "NO"
    ip = wifi.radio.ipv4_address if wifi.radio.connected else None
    println(f"STATUS:WIFI:{w}:{ip} MQTT:{'YES' if mqtt_connected() else 'NO'} MODE:{state['mode']} FEEDS:{state['feeds']}")

def at_save(_args=None): save_config()
def at_load(_args=None): load_config()
def at_reset(_args=None):
    println("OK:RESET"); time.sleep(0.25); microcontroller.reset()
def at_ready(_args=None): println("OK:READY")

AT = {
    "WIFI": at_wifi,
    "AIO": at_aio,
    "FEEDS": at_feeds,
    "MODE": at_mode,
    "CONNECT": at_connect,
    "SEND": at_send,
    "PUB": at_pub,
    "SUB": at_sub,
    "LED": at_led,
    "STATUS": at_status,
    "SAVE": at_save,
    "LOAD": at_load,
    "RESET": at_reset,
    "": at_ready,   # "AT" or "AT?"
    "?": at_status
}

# ---------------- Boot + Loop ----------------
println("MODEM:READY (AT? for status)")

buf = b""
while True:
    try:
        data = uart.read(64)
        if data:
            buf += data
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                line = raw.decode("utf-8","ignore")
                # tolerate CRLF and long bursts
                line = line.replace("\r", "").strip()
                if not line:
                    continue
                if len(line) > 256:
                    println("ERR:LINE:TOO_LONG")
                    continue

                # AT handling
                if line.upper().startswith("AT"):
                    body = line[2:]
                    if body.startswith("+"): body = body[1:]
                    cmd, args = "", ""
                    if "=" in body:
                        cmd, args = body.split("=", 1)
                    else:
                        cmd, args = body, ""
                    handler = AT.get(cmd.strip().upper())
                    if handler:
                        try:
                            handler(args)
                        except Exception as e:
                            println(f"ERR:AT:{repr(e)}")
                    else:
                        println(f"ERR:AT:UNKNOWN:{cmd.strip()}")
                else:
                    # Non-AT data line → publish according to mode
                    if mqtt_connected():
                        if state["mode"] == "CSV":
                            publish_csv(line)
                        else:
                            # RAW: "topic payload"
                            if " " in line:
                                t, p = line.split(" ", 1)
                                if _rate_ok():
                                    try: client.publish(t, p); println("OK:PUB")
                                    except Exception as e: println(f"ERR:PUB:{repr(e)}")
                            else:
                                println("ERR:RAWFMT")

        # Maintain MQTT (loop timeout must be >= socket timeout)
        if client:
            try:
                client.loop(timeout=2.00)
            except Exception as e:
                println(f"MQTT:LOOP_ERR:{repr(e)}")
                # gentle recovery
                try:
                    client.disconnect()
                except Exception:
                    pass
                client = None
                if wifi_connect():
                    mqtt_connect()

        time.sleep(0.01)

    except Exception as e:
        println(f"ERR:MAIN:{repr(e)}")
        # full recovery path
        try:
            if client: client.disconnect()
        except Exception:
            pass
        client = None
        try:
            if wifi.radio.connected: wifi.radio.disconnect()
        except Exception:
            pass
        time.sleep(0.5)

