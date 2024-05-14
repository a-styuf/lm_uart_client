import crc16

class Modbus_RTU():
    def __init__(self):
        pass
    
    def request(self, ad=0x05, fc=0x03, ar=0x0001, lr=0x01, dr=0x00, dl=None):
        """
        :param ad: slave address Modbus-RTU
        :param fc: Function Code
        :param ar: Register Address
        :param lr: data length
        :param dr: single register used for FC = 6
        :param dl: byte values list for FC = 16
        :return: frame bytes
        """
        data_to_send = []
        if fc == 0x03:  # F3
            data_to_send = [ad, fc, (ar >> 8) & 0xFF, (ar >> 0) & 0xFF, 0x00, lr]
        elif fc == 0x06:  # F6
            data_to_send = [ad, fc, (ar >> 8) & 0xFF, (ar >> 0) & 0xFF, (dr >> 8) & 0xFF, (dr >> 0) & 0xFF]
        elif fc == 0x10:  # F16
            data_to_send = [ad, fc, (ar >> 8) & 0xFF, (ar >> 0) & 0xFF, 0x00, lr, (lr*2) & 0xFF]
            data_to_send.extend(dl)
        crc16_reg = crc16.calc_modbus_crc16_bytes(data_to_send)
        data_to_send.extend(crc16_reg)
        return bytes(data_to_send)
    
    def parcing(self, read_data):
        ret_str = ""
        if read_data:
            leng = 0
            bad_packet_flag = 0
            error_packet_flag = 0
            # print(bytes_array_to_str(read_data))
            if len(read_data) >= 5:
                ad = read_data[0]
                if read_data[1] & 0x80:
                    if len(read_data) >= 5:  # проверка на запрос
                        if crc16.calc_modbus_crc16_bytes(read_data[0:5]) == [0, 0]:
                            leng = 5
                            error_packet_flag = 1
                    if leng == 0 and (len(read_data) >= 5):  # проверка на ответ
                        if crc16.calc_modbus_crc16_bytes(read_data[0:5]) == [0, 0]:
                            leng = 5
                            error_packet_flag = 1
                        else:
                            bad_packet_flag = 1
                elif read_data[1] == 0x03:
                    if len(read_data) >= 8:  # проверка на запрос
                        if crc16.calc_modbus_crc16_bytes(read_data[0:8]) == [0, 0]:
                            leng = 8
                    if leng == 0 and (len(read_data) >= 5 + read_data[2]):  # проверка на ответ
                        if crc16.calc_modbus_crc16_bytes(read_data[0:5 + read_data[2]]) == [0, 0]:
                            leng = 5 + read_data[2]
                        else:
                            bad_packet_flag = 1
                elif read_data[1] == 0x06:
                    if len(read_data) >= 8:  # проверка на запрос
                        if crc16.calc_modbus_crc16_bytes(read_data[0:8]) == [0, 0]:
                            leng = 8
                        else:
                            bad_packet_flag = 1
                    if leng == 0 and len(read_data) >= 8 and read_data[4] == 0x00 and read_data[5] == 0x00:  # ответ
                        if crc16.calc_modbus_crc16_bytes(read_data[0:8]) == [0, 0]:
                            leng = 8
                        else:
                            bad_packet_flag = 1
                elif read_data[1] == 0x10:
                    if leng == 0 and len(read_data) >= 8:  # ответ
                        if crc16.calc_modbus_crc16_bytes(read_data[0:8]) == [0, 0]:
                            leng = 8
                        else:
                            bad_packet_flag = 1
                    if len(read_data) >= 9 + read_data[6]:
                        if crc16.calc_modbus_crc16_bytes(read_data[0:9 + read_data[6]]) == [0, 0]:
                            leng = 9 + read_data[6]
                        else:
                            bad_packet_flag = 1
                elif read_data[0] == 0xFF: # широковещательная команда
                    if len(read_data) >= 8:  # проверка на запрос
                        if crc16.calc_modbus_crc16_bytes(read_data[0:8]) == [0, 0]:
                            leng = 8
                        else:
                            bad_packet_flag = 1
                else:
                    bad_packet_flag = 1
            else:
                ret_str += f"Short frame"
            if leng:  # пакет разобрался
                work_data = read_data[0:leng]
                # buf = read_data[leng:]
                if bad_packet_flag:
                    ret_str += "CRC error"
                if error_packet_flag:
                    ret_str += "Exception frame"
                else:
                    ret_str += "OK"
                pass
            else:
                pass
        else:
            pass
        return ret_str
