import time
import copy
from ctypes import c_int8, c_int16
import threading
import configparser
import os
import usb_can_bridge
import norby_data


class LMData:
    def __init__(self, **kw):
        # настройки LM
        self.fabrication_number = 0
        self.address = 1
        self.baudrate = 9600
        self.serial_numbers = []
        self.debug = True
        self.crc_check = True
        for key in sorted(kw):
            if key == "serial_numbers":
                self.serial_numbers = kw.pop(key)
            elif key == "baudrate":
                self.baudrate = kw.pop(key)
            elif key == "address":
                self.address = kw.pop(key)
            elif key == "timeout":
                self.timeout = kw.pop(key)
            elif key == "port":
                self.port = kw.pop(key)
            elif key == "debug":
                self.debug = kw.pop(key)
            elif key == "crc":
                self.crc_check = kw.pop(key)
            else:
                pass
        # интерфейс работы с ITB - VCP-CAN
        self.usb_can = usb_can_bridge.MyUSBCANDevice(baudrate=self.baudrate,
                                                     serial_numbers=self.serial_numbers,
                                                     debug=self.debug,
                                                     crc=self.crc_check,
                                                     )
        # заготовка для хранения данных прибора
        self.general_data = []
        self.load_parameters_data = {}
        self.tmi_dict = {}
        self.graph_interval = 3600
        self.transaction_busy = False
        # заготовка для хранения и отображения параметров работы прибора
        # заготовка для хранения результата циклограммы
        self.cycl_result_offset = 1280
        self.cycl_128B_part_num = 33
        self.cyclogram_result_data = [[] for i in range(self.cycl_128B_part_num)]
        # хранение общих данных
        self.com_registers = []
        self.instamessage_data = [0 for i in range(128)]
        #
        self.uart_rx_ctrl = [0 for i in range(8)]
        self.uart_rx_data = [0 for i in range(1024)]
        self.uart_tx_data = [0 for i in range(1024)]
        #
        self.flash_data = {"rd": [0xfe for i in range(0x80000)], "ctrl_reg": []}
        #
        self.mem_num = 9  # 0 - all mem, 1 - pl sol
        self.mem_data = [[] for i in range(self.mem_num)]
        # заготовка для хранения переменных общения с ПН
        # empty
        #
        self._close_event = threading.Event()
        self.parc_thread = threading.Thread(target=self.parc_data, args=(), daemon=True)
        self.data_lock = threading.Lock()
        # инициализация
        self.parc_thread.start()
        pass

    def reconnect(self):
        self.usb_can.close_id()
        time.sleep(0.1)
        #
        self.usb_can = usb_can_bridge.MyUSBCANDevice(baudrate=self.baudrate,
                                                     serial_numbers=self.serial_numbers,
                                                     debug=self.debug,
                                                     crc=self.crc_check,
                                                     )
        return self.usb_can.open_id()

    def send_cmd(self, mode="dbg_led_test", action="start"):
        req_param_dict =   {"can_num": 0,
                            "dev_id": self.address,
                            "mode": "write",
                            "var_id": 2,
                            "offset": 16,
                            "d_len": 1,
                            "data": [0x01]}
        if action == "start":
            req_param_dict["data"] = [0x01]
        elif action == "stop":
            req_param_dict["data"] = [0xFF]
        if mode in "dbg_led_test":
            req_param_dict["offset"] = 16
        elif mode in "lm_init":
            req_param_dict["offset"] = 0
        else:
            raise ValueError("Incorrect method parameter <mode>")
        self._print("send com <%s> <%s>" % (mode, action))
        self.usb_can.request(**req_param_dict)

    def busy(self):
        return not self.usb_can.ready_to_transaction

    def wait_busy(self, timeout=0.1):
        """
        Ожидание занятости приемо-передатчика
        :param timeout: секунды, таймаут ожидания
        :return: время ожидания секунды
        """
        start = time.perf_counter_ns()
        while (time.perf_counter_ns() - start) < timeout*10E9:
            time.sleep(0.001)
            if not self.busy():
                break
        stop = time.perf_counter_ns()
        return (stop - start)/10E9

    def read_cmd_status(self, mode="dbg_led_test"):
        req_param_dict =   {"can_num": 0,
                            "dev_id": self.address,
                            "mode": "read",
                            "var_id": 3,
                            "offset": 16,
                            "d_len": 1,
                            "data": [0x01]}
        if mode in "dbg_led_test":
            req_param_dict["offset"] = 16
        elif mode in "lm_init":
            req_param_dict["offset"] = 0
        else:
            raise ValueError("Incorrect method parameter <mode>")
        self._print("read com_status <%s>" % (mode))
        self.usb_can.request(**req_param_dict)

    def send_cmd_reg(self, mode="dbg_led_test", data=None):
        if data is not None:
            req_param_dict =   {"can_num": 0,
                                "dev_id": self.address,
                                "mode": "write",
                                "var_id": 4,
                                "offset": 16,
                                "d_len": len(data),
                                "data": data}
            if mode in "dbg_led_test":
                req_param_dict["offset"] = 0x40
            elif mode in "synch_time":
                req_param_dict["offset"] = 0x00
            elif mode in "const_mode":
                req_param_dict["offset"] = 0x04
            elif mode in "mem_init":
                req_param_dict["offset"] = 0x05
            elif mode in "mem_rd_ptr":
                req_param_dict["offset"] = 0x07
            elif mode in "write_ft_to_mem":
                req_param_dict["offset"] = 0x0C
            elif mode in "read_ft_from_mem":
                req_param_dict["offset"] = 0x0D
            elif mode in "read_ft_from_regs":
                req_param_dict["offset"] = 0x0E
            elif mode in "run_ft":
                req_param_dict["offset"] = 0x0F
            elif mode in "lm_mode":
                req_param_dict["offset"] = 0x10
            elif mode in "lm_pn_pwr_switch":
                req_param_dict["offset"] = 0x11
            elif mode in "lm_pn_pwr_switch_on":
                req_param_dict["offset"] = 0x12
            elif mode in "lm_pn_pwr_switch_off":
                req_param_dict["offset"] = 0x13
            elif mode in "lm_ft_default":
                req_param_dict["offset"] = 0x14
            elif mode in "stop_ft":
                req_param_dict["offset"] = 0x16
            #
            elif mode in "pl_kkd_get_tmi":
                req_param_dict["offset"] = 0x20
            elif mode in "pl_kkd_get_data":
                req_param_dict["offset"] = 0x21
            elif mode in "pl_kkd_set_interval":
                req_param_dict["offset"] = 0x22
            elif mode in "pl_kkd_set_rd_ptr":
                req_param_dict["offset"] = 0x24
            elif mode in "pl_kkd_synch_time":
                req_param_dict["offset"] = 0x28
            #
            elif mode in "pl_aznv_get_tmi":
                req_param_dict["offset"] = 0x51
            elif mode in "pl_aznv_get_single_frame_data":
                req_param_dict["offset"] = 0x53
            #
            elif mode in "lm_soft_reset":
                req_param_dict["offset"] = 0x30
            else:
                raise ValueError("Incorrect method parameter <mode>")
            self._print("send com_reg <%s>: " % mode, data)
            self.usb_can.request(**req_param_dict)

    def read_cmd_reg(self, mode="dbg_led_test", leng=1):
        if leng >= 1:
            req_param_dict = {"can_num": 0,
                              "dev_id": self.address,
                              "mode": "read",
                              "var_id": 4,
                              "offset": 16,
                              "d_len": leng,
                              "data": []}
            if mode in "dbg_led_test":
                req_param_dict["offset"] = 0x40
            elif mode in "synch_time":
                req_param_dict["offset"] = 0x00
            elif mode in "const_mode":
                req_param_dict["offset"] = 0x04
            elif mode in "mem_init":
                req_param_dict["offset"] = 0x05
            elif mode in "mem_rd_ptr":
                req_param_dict["offset"] = 0x07
            elif mode in "write_ft_to_mem":
                req_param_dict["offset"] = 0x0C
            elif mode in "read_ft_from_mem":
                req_param_dict["offset"] = 0x0D
            elif mode in "read_ft_from_regs":
                req_param_dict["offset"] = 0x0E
            elif mode in "run_ft":
                req_param_dict["offset"] = 0x0F
            elif mode in "lm_mode":
                req_param_dict["offset"] = 0x10
            elif mode in "lm_pn_pwr_switch":
                req_param_dict["offset"] = 0x11
            elif mode in "lm_pn_pwr_switch_on":
                req_param_dict["offset"] = 0x12
            elif mode in "lm_pn_pwr_switch_off":
                req_param_dict["offset"] = 0x13
            #
            elif mode in "pl_kkd_get_tmi":
                req_param_dict["offset"] = 0x20
            elif mode in "pl_kkd_get_data":
                req_param_dict["offset"] = 0x21
            elif mode in "pl_kkd_set_interval":
                req_param_dict["offset"] = 0x22
            elif mode in "pl_kkd_set_rd_ptr":
                req_param_dict["offset"] = 0x24
            elif mode in "pl_kkd_synch_time":
                req_param_dict["offset"] = 0x28
            #
            elif mode in "pl_aznv_get_tmi":
                req_param_dict["offset"] = 0x51
            elif mode in "pl_aznv_get_single_frame_data":
                req_param_dict["offset"] = 0x53
            #
            elif mode in "lm_soft_reset":
                req_param_dict["offset"] = 0x30
            else:
                raise ValueError("Incorrect method parameter <mode>")
            self._print("read com_reg <%s>" % mode)
            self.usb_can.request(**req_param_dict)

    def write_ft_regs(self, num=0, step=0, step_data=None):
        if step_data is not None:
            if len(step_data) == 64:
                req_param_dict = {"can_num": 0,
                                  "dev_id": self.address,
                                  "mode": "write",
                                  "var_id": 8,
                                  "offset": 0,
                                  "d_len": 64,
                                  "data": step_data}
                if num < 5:
                    for ft_num in range(5):
                        req_param_dict["offset"] = num*2048+64*step
                else:
                    raise ValueError("Incorrect method parameter <mode>")
                self._print(f"write step {step} to ft_{num}_regs")
                self.usb_can.request(**req_param_dict)
            else:
                raise ValueError(f"Incorect data len <{len(step_data)}>")

    def read_tmi(self, mode="beacon"):
        req_param_dict = {"can_num": 0,
                          "dev_id": self.address,
                          "mode": "read",
                          "var_id": 5,
                          "offset": 0,
                          "d_len": 128,
                          "data": []}
        if mode in "lm_beacon":
            req_param_dict["offset"] = 0
        elif mode in "lm_tmi":
            req_param_dict["offset"] = 128
        elif mode in "lm_full_tmi":
            req_param_dict["offset"] = 256
        elif mode in "lm_load_param":
            req_param_dict["offset"] = 384
        elif mode in "pl_sol_tmi":
            req_param_dict["offset"] = 512
        elif mode in "pl_brk_tmi":
            req_param_dict["offset"] = 640
        elif mode in "loaded_cfg":
            req_param_dict["offset"] = 768
        elif mode in "cfg_to_save":
            req_param_dict["offset"] = 896
        else:
            raise ValueError("Incorrect method parameter <mode>")
        self._print("read tmi <%s>" % mode)
        self.usb_can.request(**req_param_dict)

    def read_cyclogram_result(self, part_num=0):
        req_param_dict = {"can_num": 0,
                          "dev_id": self.address,
                          "mode": "read",
                          "var_id": 5,
                          "offset": 0,
                          "d_len": 128,
                          "data": []}
        part_num = 32 if part_num > self.cycl_128B_part_num else part_num
        req_param_dict["offset"] = self.cycl_result_offset + part_num * 128
        self._print("read cyclogram result <offset %d>" % req_param_dict["offset"])
        self.usb_can.request(**req_param_dict)

    def read_mem(self, mode="mem_all", part=-1):
        req_param_dict = {"can_num": 0,
                          "dev_id": self.address,
                          "mode": "read",
                          "var_id": 7,
                          "offset": 0,
                          "d_len": 128,
                          "data": []}
        if part == -1:
            if mode in "part_all":
                req_param_dict["offset"] = 0*128
            elif mode in "part_general":
                req_param_dict["offset"] = 1*128
            elif mode in "part_ekkd":
                req_param_dict["offset"] = 2*128
            elif mode in "part_aznv":
                req_param_dict["offset"] = 3*128
            elif mode in "part_gfo":
                req_param_dict["offset"] = 4*128
            elif mode in "part_ft0":
                req_param_dict["offset"] = 5*128
            elif mode in "part_ft1":
                req_param_dict["offset"] = 6*128
            elif mode in "part_ft2":
                req_param_dict["offset"] = 7*128
            elif mode in "part_ft3":
                req_param_dict["offset"] = 8*128
            elif mode in "part_ft4":
                req_param_dict["offset"] = 9*128
            elif mode in "part_ft5":
                req_param_dict["offset"] = 10*128
            elif mode in "part_ft6":
                req_param_dict["offset"] = 11*128
            else:
                raise ValueError("Incorrect method parameter <mode>")
            self._print("read <%s>" % mode)
            self.usb_can.request(**req_param_dict)
        elif part >= 0:
            req_param_dict["offset"] = (part+1)*128
            self._print("read part <%d>" % part)
            self.usb_can.request(**req_param_dict)

    def write_flash_sw(self, offset=0, data=None):
        if data is not None:
            if offset + len(data) < 0x80000:
                req_param_dict = {  "can_num": 0, "dev_id": self.address, "mode": "write", "var_id": 14, "offset": offset,
                                    "d_len": len(data), "data": data}
            else:
                raise ValueError(f"Out of bound flash mem^ max is 0x80000, 0x{offset + len(data):05X}")
        else:
            raise ValueError("Data is empty")
        self._print("write flash data <%s>: " % data)
        self.usb_can.request(**req_param_dict)

    def read_flash_sw(self, offset=0, leng=128):
        if offset + leng < 0x80000:
            req_param_dict = {  "can_num": 0, "dev_id": self.address, "mode": "read", "var_id": 14, "offset": offset,
                                "d_len": leng, "data": [0]}
        else:
            raise ValueError(f"Out of bound flash mem: max is 0x80000, 0x{offset + leng:05X}")
        self.usb_can.request(**req_param_dict)

    def reset_flash_sw_data(self):
        self.flash_data["rd"] = [0xfe for i in range(0x80000)]

    def write_flash_ctrl(self, data=None):
        if data is not None:
            if len(data) <= 8:
                req_param_dict = {  "can_num": 0, "dev_id": self.address,
                                    "mode": "write",
                                    "var_id": 14,
                                    "offset": 0x80000,
                                    "d_len": len(data), "data": data}
            else:
                raise ValueError(f"Incorrect data len: must be 8 now - {len(data)}")
        else:
            raise ValueError("Data is empty")
        self._print("write flash ctrl reg<%s>: " % data)
        self.usb_can.request(**req_param_dict)

    def read_flash_ctrl(self):
        self.flash_data["ctrl_reg"] = []
        req_param_dict = {"can_num": 0, "dev_id": self.address,
                          "mode": "read",
                          "var_id": 14,
                          "offset": 0x80000,
                          "d_len": 8, "data": []}
        self.usb_can.request(**req_param_dict)

    def parc_data(self):
        while True:
            time.sleep(0.01)
            if self.usb_can:
                id_var_row, data = self.usb_can.get_data()
                if data is not None:
                    res1, rtr, res2, offset, var_id, dev_id = self.usb_can.process_id_var(id_var_row)
                    with self.data_lock:
                        if var_id == 5:  # переменная телеметрии
                            report_data = " ".join([("%02X" % var) for var in data])
                            self._print("process tmi <var_id = %d, offset %d>" % (var_id, offset), report_data)
                            parced_data = norby_data.frame_parcer(data)
                            parced_data_report = "\n".join([f"{data}" for data in parced_data])
                            self._print(parced_data_report)
                            if offset == 256:
                                self.manage_general_data(parced_data)
                            elif offset == 384:
                                self.manage_load_parameters_data(parced_data)
                            pass
                        elif var_id == 7:  # переменная памяти
                            self._print("process mem <var_id = %d, offset %d>" % (var_id, offset))
                            self.manage_mem_data(offset, data)
                            pass
                        elif var_id == 3:  # статусы функций
                            self._print("process cmd_status <var_id = %d, offset %d>:" % (var_id, offset), data)
                            pass
                        elif var_id == 4:  # статусные регистры
                            self._print("process cmd_regs <var_id = %d, offset %d>:" % (var_id, offset), data)
                            self.com_registers = copy.deepcopy(data)
                            pass
                        elif var_id == 9:  # отправка данных по UART
                            self._print("uart tx data <var_id = %d, offset %d>:" % (var_id, offset), list_to_str(data))
                            self.uart_tx_data = copy.deepcopy(data)
                            pass
                        elif var_id == 10:  # прием данных UART
                            self._print("uart rx data <var_id = %d, offset %d>:" % (var_id, offset), list_to_str(data))
                            if (offset % 1024 == 0):
                                self.uart_rx_ctrl = copy.deepcopy(data)
                            else:
                                self.uart_rx_data = copy.deepcopy(data)
                            pass
                        elif var_id == 14:  # работа с переменной загрузки Flush
                            self._print("process flash <var_id = %d, offset %d>:" % (var_id, offset), list_to_str(data))
                            self.parc_flash_data(offset, data)
                            self.instamessage_data = copy.deepcopy(data)
                            pass
                else:
                    self.transaction_busy = False
            if self._close_event.is_set() is True:
                self._close_event.clear()
                return
        pass

    def parc_flash_data(self, offset, data):
        if offset == 0x80000:
            self.flash_data["ctrl_reg"] = data
        elif 0 <= offset < 0x80000:
            self.flash_data["rd"][offset: offset+len(data)] = data
        pass

    def manage_general_data(self, frame_data):
        if len(frame_data) >= 4:
            name_list = ["Time, s"]
            data_list = [int(time.perf_counter())]
            str_data_list = ["%d" % int(time.perf_counter())]
            name_list.extend([var[0] for var in frame_data])
            data_list.extend([(self._get_number_from_str(var[1])) for var in frame_data])
            str_data_list.extend([(var[1]) for var in frame_data])
            #
            try:
                if len(self.general_data) == 0:
                    for num in range(len(name_list)):
                        self.general_data.append([name_list[num], [data_list[num]], [str_data_list[num]]])
                        self.tmi_dict[name_list[num]] = data_list[num]
                else:
                    for num in range(min(len(data_list), len(self.general_data))):
                        self.general_data[num][1].append(data_list[num])
                        self.general_data[num][2].append(str_data_list[num])
                # self.cut_general_data(self.graph_interval)
            #
            except Exception as error:
                self._print("m: manage_general_data <%s>" % error)
            try:
                self.cut_general_data(self.graph_interval)
            except Exception as error:
                self._print("m: manage_general_data <%s>" % error)
        else:
            self._print("m: manage_general_data frame_data_error")

    def manage_load_parameters_data(self, frame_data):
        if len(frame_data) >= 4:
            self.load_parameters_data = {pair[0]: pair[1] for pair in frame_data}
        else:
            self._print("m: manage_general_data frame_data_error")

    def reset_general_data(self):
        self.general_data = []

    def _get_number_from_str(self, str_var):
        try:
            try:
                number = float(str_var)
            except ValueError:
                number = int(str_var, 16)
            return number
        except Exception as error:
            self._print(error)
        return 0

    def cut_general_data(self, interval_s):
        if len(self.general_data) > 1:
            while (self.general_data[0][1][-1] - self.general_data[0][1][0]) >= interval_s:
                for var in self.general_data:
                    var[1].pop(0)
                    var[2].pop(0)
        pass

    def get_cyclogram_result_str(self):
        report_str = "Row cyclogram result data:\n\n"
        with self.data_lock:
            for part in self.cyclogram_result_data:
                report_str += list_to_str(part) + '\n'
        return report_str

    def get_parc_cyclogram_result(self):
        report_str = "\nParced cyclogram result data:\n\n"
        cycl_result = []
        with self.data_lock:
            cycl_result = copy.deepcopy(self.cyclogram_result_data)
        # вычленение сырах данных
        report_str += "\nCyclogram result PL data:\n\n"
        bytes_num = 0
        for body in cycl_result[1:]:
            try:
                if body[0] == 0xF1 and body[1] == 0x0F:
                    report_str += list_to_str(body[8:126]) + "\n"
            except IndexError:
                pass
        report_str += "\n"
        # вычленение сырых данных
        report_str += "\nCyclogram result PL data (reverse byte order in u32-words, special for PL1.1):\n\n"
        bytes_num = 0
        try:
            for body in cycl_result[1:]:
                if body[0] == 0xF1 and body[1] == 0x0F:
                    for j in range(len(body[8:126])//4):
                        word_to_print = "%02X%02X %02X%02X " % (body[8 + 4 * j + 3],
                                                                body[8 + 4 * j + 2],
                                                                body[8 + 4 * j + 1],
                                                                body[8 + 4 * j + 0])
                        report_str += word_to_print
        except IndexError:
            pass
        report_str += "\n"
        # вычленение сырах данных
        report_str += "\n Cyclogram result PL data (reverse byte order in u16-words, special for PL2.0):\n\n"
        bytes_num = 0
        try:
            for body in cycl_result[1:]:
                if body[0] == 0xF1 and body[1] == 0x0F:
                    for j in range(len(body[8:126]) // 4):
                        word_to_print = "%02X%02X %02X%02X " % (body[8 + 4 * j + 1],
                                                                body[8 + 4 * j + 0],
                                                                body[8 + 4 * j + 3],
                                                                body[8 + 4 * j + 2])
                        report_str += word_to_print
        except IndexError:
            pass
        report_str += "\n"
        # разбор заголовка
        report_str += "\nCyclogram result header:\n\n"
        parced_data = norby_data.frame_parcer(cycl_result[0])
        for data in parced_data:
            report_str += "{:<30}".format(data[0]) + "\t{:}".format(data[1]) + "\n"
        return report_str

    # mem data #
    def manage_mem_data(self, offset, data):
        mem_num = offset // 128
        if data:
            self._print("manage_mem_data: offset: %d, data: " % offset, list_to_str(data, u16_rev=True))
            if mem_num == 0:  # all mem
                self.mem_data[mem_num] = copy.deepcopy(data)
                pass
            elif mem_num < self.mem_num:
                self.mem_data[mem_num] = copy.deepcopy(data)
                pass
            else:
                self._print("manage_mem_data: offset error")
            pass
        else:
            self._print("manage_mem_data: data error")

    def get_mem_data(self, num):
        try:
            if self.mem_data[num]:
                ret_str = list_to_str(self.mem_data[num], u16_rev=True)
                self.mem_data[num] = []
                return ret_str
            return " "
        except IndexError:
            return " "

    # LOG data #
    def get_log_file_title(self):
        name_str = ""
        if len(self.general_data):
            for var in self.general_data:
                name_str += var[0] + ';'
            return name_str + '\n'
        else:
            return None

    def get_log_file_data(self):
        data_str = ""
        if len(self.general_data):
            for var in self.general_data:
                data_str += var[2][-1] + ';'
            return data_str + '\n'
        else:
            return None

    def _print(self, *args):
        if self.debug:
            print_str = "lmd: " + self.get_time()
            for arg in args:
                print_str += " " + str(arg)
            print(print_str)

    @staticmethod
    def get_time():
        return time.strftime("%H-%M-%S", time.localtime()) + "." + ("%.3f:" % time.perf_counter()).split(".")[1]


def value_from_bound(val, val_min, val_max):
    return max(val_min, min(val_max, val))


def list_to_str(input_list, u16_rev=False):
    return_str = ""
    if input_list:
        for i in range(len(input_list)):
            if u16_rev:
                num = i - 1 if i % 2 else i + 1
            else:
                num = i
            try:
                return_str += "%02X" % input_list[num]
            except IndexError:
                return_str += "XX"
            if i % 2 == 1:
                return_str += " "
        return return_str
    return " "


if __name__ == "__main__":
    lm = LMData(address=6, debug=True, serial_numbers=["205135995748"])
    lm.usb_can.open_id()
    #
    print("тест отправки команд")
    lm.send_cmd(mode="dbg_led_test", action="start")
    for i in range(10):
        time.sleep(1)
        lm.read_cmd_status(mode="dbg_led_test")
    lm.send_cmd(mode="dbg_led_test", action="stop")
    for i in range(2):
        time.sleep(1)
        lm.read_cmd_status(mode="dbg_led_test")
    time.sleep(1)
    #
    print("тест записи командного регистра")
    lm.send_cmd_reg(mode="dbg_led_test", data=[0xEE])
    lm.read_cmd_reg(mode="dbg_led_test", leng=1)
    time.sleep(2)
    lm.send_cmd_reg(mode="dbg_led_test", data=[0x1E])
    lm.read_cmd_reg(mode="dbg_led_test", leng=1)
    time.sleep(2)
    #
    print("тест чтения телеметрии")
    lm.read_tmi(mode="lm_beacon")
    time.sleep(1)
    #
    print("тест чтения памяти")
    lm.read_mem(mode="mem_all")
    time.sleep(1)
    #
    pass
