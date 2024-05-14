import lm_data
import time
import crc16
import copy
import random

class UART_Channel:
    def __init__(self, **kw):
        self.num = kw.get("num", 0)
        self.lm = kw.get("lm", None)
        self.debug = kw.get("debug", True)
    
    def send(self, data=b""):
        len_data = len(data) + 8
        can_data = len(data).to_bytes(2, byteorder = 'little', signed = False)
        can_data += bytes.fromhex("00 00 00 00 00 00")
        can_data += data
        # запись данных
        req_param_dict = {  "can_num": 0,
                            "dev_id": self.lm.address,
                            "mode": "write", 
                            "var_id": 9, 
                            "offset": (self.num*1024) + 8, 
                            "d_len": len_data - 8, 
                            "data": can_data[8:]}
        id_var = self.lm.usb_can.request(**req_param_dict)
        self.lm.wait_busy(timeout=0.5)
        if self.debug:
            print("\tTX data: ", self.lm.usb_can.can_log_str(id_var, req_param_dict["data"], len(data)))
        # запись команды на запись
        req_param_dict = {  "can_num": 0,
                            "dev_id": self.lm.address,
                            "mode": "write", 
                            "var_id": 9, 
                            "offset": (self.num*1024), 
                            "d_len": 8, 
                            "data": can_data[:8]}
        id_var = self.lm.usb_can.request(**req_param_dict)
        self.lm.wait_busy(timeout=0.5)
        if self.debug:
            print("\tTX ctrl: ", self.lm.usb_can.can_log_str(id_var, req_param_dict["data"], len(data)))
        time.sleep(0.1)
        #
        pass
    
    def read(self, timeout=0.1):
        # чтение статуса
        req_param_dict = {  "can_num": 0, 
                            "dev_id": self.lm.address, 
                            "mode": "read", 
                            "var_id": 10, 
                            "offset": self.num*1024, 
                            "d_len": 8, 
                            "data": []}
        id_var = self.lm.usb_can.request(**req_param_dict)
        self.lm.wait_busy(timeout=0.5)
        time.sleep(0.05)
        if self.debug:
            print("\tRX ctrl: ", self.lm.usb_can.can_log_str(id_var, self.lm.uart_rx_ctrl, 8))
        #
        rx_len = int.from_bytes(self.lm.uart_rx_ctrl[0:2], byteorder="little")
        rx_flag = int.from_bytes(self.lm.uart_rx_ctrl[2:4], byteorder="little")
        #
        if (rx_len != 0) and ((rx_flag & 0x01) == 1):
            req_param_dict = {  "can_num": 0, 
                                "dev_id": self.lm.address, 
                                "mode": "read", 
                                "var_id": 10, 
                                "offset": self.num*1024 + 8, 
                                "d_len": rx_len, 
                                "data": []}
            id_var = self.lm.usb_can.request(**req_param_dict)
            self.lm.wait_busy(timeout=0.5)
            time.sleep(0.05)
            if self.debug:
                print("\tRX data: ", self.lm.usb_can.can_log_str(id_var, self.lm.uart_rx_data[:rx_len], rx_len))
            return bytes(self.lm.uart_rx_data[:rx_len])
        return b""
    
    def pwr_ctrl(self, ena=0):
        pwr_ch_preset = [1, 2, 3, 4, 5]
        self.lm.read_cmd_reg(mode="lm_pn_pwr_switch", leng=1)
        time.sleep(0.1)
        state = 0
        if self.lm.com_registers:
            state = self.lm.com_registers[0]
        if ena:
            state |= 1 << (pwr_ch_preset[self.num])
        else:
            state &= ~(1 << (pwr_ch_preset[self.num]))
        self.lm.send_cmd_reg(mode="lm_pn_pwr_switch", data=[state])
        time.sleep(0.1)
        
    
    
if __name__=="__main__":
    lm = lm_data.LMData(serial_numbers=["206E359D5748"], address=6, debug=True)
    lm.reconnect()
    #
    uart_ch0 = UART_Channel(num=0, debug=False, lm = lm)
    uart_ch1 = UART_Channel(num=1, debug=False, lm = lm)
    uart_ch2 = UART_Channel(num=2, debug=False, lm = lm)
    lm.debug = False
    lm.usb_can.debug = False
    #
    time.sleep(0.1)
    uart_ch0.pwr_ctrl(ena=1)
    time.sleep(0.1)
    uart_ch1.pwr_ctrl(ena=1)
    time.sleep(0.1)
    uart_ch2.pwr_ctrl(ena=1)
    time.sleep(1.0)
    #
    uart_ch0.send(b"uart_ch0")
    print(f"TX data ch_{0}:",  b"uart_ch0".hex(" ").upper())
    print(f"RX data ch_{0}:", uart_ch0.read().hex(" ").upper())
    time.sleep(1.0)    
    uart_ch2.send(b"uart_ch2")
    print(f"TX data ch_{2}:",  b"uart_ch2".hex(" ").upper())
    while 1:
        time.sleep(1.0)    
        uart_ch2.send(b"uart_ch2")
        print(f"TX data ch_{2}:",  b"uart_ch2".hex(" ").upper())
        time.sleep(1.0)    
        print_str = uart_ch2.read().hex(" ").upper()
        if print_str:
            print(f"RX data ch_{2}:",  print_str)
        time.sleep(0.1)    
