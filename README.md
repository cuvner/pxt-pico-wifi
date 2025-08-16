# Pico MQTT Extension

This MakeCode extension lets a **micro:bit** talk to a **Raspberry Pi Pico W** running custom CircuitPython firmware via **UART (serial pins)**.  
The Pico connects to WiFi and Adafruit IO using MQTT, while the micro:bit sends commands and reads responses.       
You will need an adafruit account [ADAFRUIT.io](https://io.adafruit.com)

---

## 🔌 Hardware Setup

### 1. Flash the Pico W
1. Hold down the **BOOTSEL** button on the Pico and plug it into your computer with USB.  
2. A drive called **RPI-RP2** will appear.  
3. Copy the CircuitPython `.uf2` firmware to the drive.  
4. Once rebooted, a new drive called **CIRCUITPY** will appear.  
5. Copy `code.py` from this repo onto the **CIRCUITPY** drive.

---

### 2. Wiring micro:bit → Pico W
Connect the **micro:bit edge connector** pins to the Pico W:

| micro:bit | Pico W | Notes                   |
|-----------|--------|-------------------------|
| `P0` (TX) | `GP1`  | Connects to Pico RX     |
| `P1` (RX) | `GP0`  | Connects to Pico TX     |
| `GND`     | `GND`  | Common ground required  |

⚠️ Remember: **cross the wires** – TX → RX and RX → TX.  

Power both boards via USB.

---

## 📦 Using the Extension

1. Open your project in [MakeCode](https://makecode.microbit.org/).  
2. Click **Extensions** → search for this GitHub repo.  
3. Add the blocks under the **Pico MQTT** category.  

## 🔧 Firmware

The Raspberry Pi Pico must be flashed with the [**pico-modem firmware**](firmware/code.py) that listens for AT-style commands over UART.  
- Copy the provided `.uf2` firmware to the Pico via drag-and-drop (bootloader mode).  
- Once flashed, the Pico will respond to AT commands from the micro:bit.

---

## 🚀 Blocks

- **Init modem**: Select micro:bit pins for TX/RX and baud rate.  
- **Wi-Fi**: Set SSID and password.  
- **Adafruit IO**: Set username and key.  
- **Feeds**: Add and send feed list to the modem.  
- **Connect**: Connect to Wi-Fi and MQTT.  
- **Send numbers**: Send up to 3 values to Adafruit IO feeds.

---

## 🖥️ Example Program

```blocks
serial.redirect(
    SerialPin.P0,  // TX pin
    SerialPin.P1,  // RX pin
    BaudRate.BaudRate115200
)
basic.pause(1000)

// Send WiFi setup
PicoMQTT.sendData("WIFI:SET:SSID,PASSWORD")

// Send Adafruit IO setup
PicoMQTT.sendData("AIO:SET:USERNAME,KEY")

// Publish a message
PicoMQTT.sendData("SEND:hello from microbit")

// Read response back
basic.showString(PicoMQTT.readData())
