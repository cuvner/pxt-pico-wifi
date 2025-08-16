/**
 * Adafruit IO Extension (test minimal)
 */
//% color=#00AACC icon="\uf1eb"
namespace aio {

    /**
     * Init modem on TX RX
     */
    //% block="init modem TX %tx RX %rx"
    //% tx.defl=SerialPin.P0 rx.defl=SerialPin.P1
    export function init(tx: SerialPin, rx: SerialPin): void {
        serial.redirect(tx, rx, BaudRate.Baud9600)
        basic.pause(100)
    }
}
