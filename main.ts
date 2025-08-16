//% color=#0f9d58 icon="\uf1eb" block="Pico Modem"
namespace picoModem {
    function at(line: string) {
        serial.writeLine(line)
        basic.pause(50)
    }

    //% block="init modem TX %tx RX %rx at %baud"
    //% tx.defl=SerialPin.P0 rx.defl=SerialPin.P1 baud.defl=BaudRate.BaudRate115200
    export function init(tx: SerialPin, rx: SerialPin, baud: BaudRate) {
        serial.redirect(tx, rx, baud)
        basic.pause(100)
        at("AT?")
    }

    //% block="set Wi-Fi SSID %ssid password %password"
    export function wifi(ssid: string, password: string) {
        at(`AT+WIFI="${ssid}","${password}"`)
    }

    //% block="use Adafruit IO user %user key %key"
    export function aio(user: string, key: string) {
        at(`AT+AIO="${user}","${key}"`)
    }

    let _feeds: string[] = []

    //% block="clear feed list"
    export function clearFeeds() {
        _feeds = []
    }

    //% block="add feed %name"
    export function addFeed(name: string) {
        _feeds.push(name)
    }

    //% block="send feed list to modem"
    export function sendFeeds() {
        if (_feeds.length == 0) return
        const q = _feeds.map(f => `"${f}"`).join(",")
        at(`AT+FEEDS=${q}`)
    }

    //% block="connect modem"
    export function connect() {
        at("AT+CONNECT")
    }

    //% block="send up to 3 numbers %v1 %v2 %v3"
    //% v2.defl=0 v3.defl=0
    export function sendNumbers(v1: number, v2?: number, v3?: number) {
        const arr = [v1, v2, v3].filter(v => v !== undefined).map(v => `${v}`)
        serial.writeLine(arr.join(","))
    }
}
