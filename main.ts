/**
 * Adafruit IO Extension
 */
//% weight=100 color=#00AACC icon="\uf1eb"
namespace aio {

    /**
     * Internal helper: send AT command over serial
     */
    function at(cmd: string) {
        serial.writeLine(cmd)
        basic.pause(200)
    }

    /**
     * Setup serial on pins
     * @param tx the TX pin
     * @param rx the RX pin
     */
    //% block="init modem TX %tx RX %rx"
    //% tx.defl=SerialPin.P0 rx.defl=SerialPin.P1
    export function init(tx: SerialPin, rx: SerialPin): void {
        serial.redirect(tx, rx, BaudRate.Baud9600)
        basic.pause(100)
    }

    /**
     * Connect to WiFi
     * @param ssid SSID
     * @param pwd password
     */
    //% block="connect WiFi SSID %ssid password %pwd"
    export function wifi(ssid: string, pwd: string): void {
        at("AT+WIFI=\"" + ssid + "\",\"" + pwd + "\"")
    }

    /**
     * Set Adafruit IO credentials
     * @param user AIO username
     * @param key AIO key
     */
    //% block="set AIO user %user key %key"
    export function aioCreds(user: string, key: string): void {
        at("AT+AIO=\"" + user + "\",\"" + key + "\"")
    }

    /**
     * Set feed names (comma separated)
     * @param feeds list of feed names
     */
    //% block="set feeds %feeds"
    export function feeds(feeds: string): void {
        at("AT+FEEDS=" + feeds)
    }

    /**
     * Connect to Adafruit IO
     */
    //% block="connect to AIO"
    export function connect(): void {
        at("AT+CONNECT")
    }

    /**
     * Send value to feed
     * @param index feed index (0 = first feed)
     * @param value number to send
     */
    //% block="send to feed index %index value %value"
    export function send(index: number, value: number): void {
        at("AT+SEND=" + index + "," + value)
    }
}
