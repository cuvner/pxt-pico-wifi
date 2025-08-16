/**
 * Adafruit IO Extension
 */
//% weight=100 color=#00AACC icon="\uf1eb"
namespace aio {

    function at(cmd: string) {
        serial.writeLine(cmd)
        basic.pause(200)
    }

    /**
     * Setup serial on pins P0 (TX) and P1 (RX)
     */
    //% block="init modem on P0 TX, P1 RX"
    export function init() {
        serial.redirect(SerialPin.P0, SerialPin.P1, BaudRate.Baud9600)
    }

    /**
     * Connect WiFi
     * @param ssid SSID
     * @param pwd password
     */
    //% block="connect WiFi SSID %ssid pwd %pwd"
    export function wifi(ssid: string, pwd: string) {
        at(`AT+WIFI="${ssid}","${pwd}"`)
    }

    /**
     * Set Adafruit IO credentials
     */
    //% block="set AIO user %user key %key"
    export function aioCreds(user: string, key: string) {
        at(`AT+AIO="${user}","${key}"`)
    }

    /**
     * Set feed names (comma separated)
     */
    //% block="set feeds %feeds"
    export function feeds(feeds: string) {
        at(`AT+FEEDS=${feeds}`)
    }

    /**
     * Connect to MQTT
     */
    //% block="connect to AIO"
    export function connect() {
        at("AT+CONNECT")
    }

    /**
     * Send value to feed
     */
    //% block="send feed index %index value %value"
    export function send(index: number, value: number) {
        at(`AT+SEND=${index},${value}`)
    }
}
