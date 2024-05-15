import lm_data
import time
import crc16
import copy
import random
import lm_uart_ch as ch
from loguru import logger
import modbus_rtu

if __name__ == "__main__":
    #
    logger.add("logs/file_{time}.log")
    # класс для управления модулем сопряжения (lm - linking module)
    lm = lm_data.LMData(serial_numbers=["206E359D5748", "365638633038", "0000ACF0", "386C324C3233"], address=6, debug=True)
    if lm.reconnect():
        logger.info(f"Reconnect is OK: {(lm.usb_can)}")
    else:
        logger.warning(f"Reconnect Error: {(lm.usb_can)}")
    mb_rtu = modbus_rtu.Modbus_RTU()

    # класс для управления каналами общения
    uart_ch0 = ch.UART_Channel(num=0, debug=False, lm = lm)
    lm.debug = False
    lm.usb_can.debug = False

    time.sleep(0.1)
    uart_ch0.pwr_ctrl(ena=1)
    time.sleep(1.0)  # ожидание переходных процессов
    while True:    
        time.sleep(2.0)
        # отправка и прием данных канала 0
        tx_data = mb_rtu.request(ad=0x0A, fc=0x03, ar=0x00, lr=2)
        uart_ch0.send(tx_data)
        logger.info(f"TX data ch_{0}: raw <{(tx_data.hex(' ').upper())}>, mb <{mb_rtu.parcing(tx_data)}>")
        time.sleep(0.1)
        rx_data = uart_ch0.read()
        logger.info(f"RX data ch_{0}: raw <{(rx_data.hex(' ').upper())}>, mb <{mb_rtu.parcing(rx_data)}>")

