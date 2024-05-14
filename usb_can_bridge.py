"""
Библиотека для общения через устройтво USB-CAN bridge (за авторством А.А. Дорошика):
 -описание typeIdxMask
    uint32_t res1 : 1;
    uint32_t RTR : 1;
    uint32_t res2 : 1;
    uint32_t Offset : 21;
    uint32_t VarId : 4;
    uint32_t DevId : 4;
 -описаиние пасылки в CAN-USB:
    uint8_t ncan;
    uint8_t res1;
    typeIdxMask id;
    uint16_t leng;
    uint8_t data[8];
}typePacket;
"""
import serial
import serial.tools.list_ports
import threading
import time
import crc16
import copy


class MyUSBCANDevice(serial.Serial):
    def __init__(self, **kw):
        serial.Serial.__init__(self)
        self.serial_numbers = []  # это лист возможных серийников!!! (не строка)
        self.baudrate = 115200
        self.timeout = 0.005
        self.port = "COM0"
        self.row_data = b""
        self.read_timeout = 0.2
        self.request_num = 0
        self.debug = True
        self.crc_check = True
        for key in sorted(kw):
            if key == "serial_numbers":
                self.serial_numbers = kw.pop(key)
            elif key == "baudrate":
                self.baudrate = kw.pop(key)
            elif key == "timeout":
                self.timeout = kw.pop(key)
            elif key == "port":
                self.port = kw.pop(key)
            elif key == "debug":
                self.debug = kw.pop(key)
            else:
                pass
        # общие переменные
        self.com_queue = []  # очередь отправки
        self.request_num = 0
        self.nansw = 0  # неответы
        self.answer_data = []
        self.req_number = 0
        self.last_answer_data = None
        self.answer_data_buffer = []
        self.read_data = b""
        self.read_flag = 0
        self.state_string = {
            -3: "Связь потеряна",
            -2: "Устройство не отвечает",
            -1: "Не удалось установить связь",
            +0: "Подключите устройство",
            +1: "Связь в норме",
        }
        self.state = 0
        self.ready_to_transaction = True
        self.serial_log_buffer = []
        self.can_log_buffer = []
        # для работы с потоками
        self.read_write_thread = None
        self._close_event = threading.Event()
        self.read_write_thread = threading.Thread(target=self.thread_function, args=(), daemon=True)

        self.log_lock = threading.Lock()
        self.com_send_lock = threading.Lock()
        self.ans_data_lock = threading.Lock()

    def open_id(self):  # функция для установки связи с КПА
        com_list = serial.tools.list_ports.comports()
        for com in com_list:
            self._print("Find:", str(com), com.serial_number)
            for serial_number in self.serial_numbers:
                self._print("ID comparison:", com.serial_number, serial_number)
                if com.serial_number and len(serial_number) >= 8:
                    if com.serial_number.find(serial_number) >= 0:
                        self._print("Connection to:", com.device)
                        self.port = com.device
                        try:
                            self.open()
                            self._print("Success connection!")
                            try:
                                self._close_event.clear()
                                self.read_write_thread.start()
                            except Exception:
                                pass
                            self.state = 1
                            self.nansw = 0
                            return True
                        except serial.serialutil.SerialException as error:
                            self._print("Fail connection")
                            self._print(error)
        self.state = -1
        return False

    def _print(self, *args):
        if self.debug:
            print_str = "ucb: " + get_time()
            for arg in args:
                print_str += " " + str(arg)
            print(print_str)

    def close_id(self):
        self._print("Try to close COM-port <0x%s>:" % self.port)
        self._close_event.set()
        self.close()
        self.state = 0
        pass

    def reconnect(self):
        self.close_id()
        print(f"Try to close: is_open is <{self.is_open}>")
        time.sleep(0.1)
        self.open_id()
        print(f"Try to open: is_open is <{self.is_open}>")
        print(self)

    def request(self, can_num=0, dev_id=0, mode="read", var_id=0, offset=0, d_len=0, data=None):
        rtr = 0 if mode == "write" else 1

        if data is None:
            data = []
        real_len = min(d_len, len(data)) if mode == "write" else d_len
        part_offset = 0
        packets_list = []
        while real_len > 0:
            part_len = 8 if real_len >= 8 else real_len
            real_len -= 8
            finish = 1 if real_len <= 0 else 0
            id_var = ((dev_id & 0x0F) << 28) | ((var_id & 0x0F) << 24) | (((part_offset+offset) & 0x1FFFFF) << 3) | \
                     ((0x00 & 0x01) << 2) | ((rtr & 0x01) << 1) | ((0x00 & 0x01) << 0)
            packet_list = [can_num & 0x01, 0x00,
                           (id_var >> 0) & 0xFF, (id_var >> 8) & 0xFF,
                           (id_var >> 16) & 0xFF, (id_var >> 24) & 0xFF,
                           (part_len >> 0) & 0xFF, (part_len >> 8) & 0xFF]
            packet_list.extend(data[0+part_offset:part_len+part_offset])
            part_offset += 8
            packets_list.append([packet_list, rtr, finish])
        with self.com_send_lock:
            self.com_queue.extend(packets_list)
            self.ready_to_transaction = False
        with self.log_lock:
            id_var = ((dev_id & 0x0F) << 28) | ((var_id & 0x0F) << 24) | ((offset & 0x1FFFFF) << 3) | \
                     ((0x00 & 0x01) << 2) | ((rtr & 0x01) << 1) | ((0x00 & 0x01) << 0)
            self.can_log_buffer.append(self.can_log_str(id_var, data[0:real_len], real_len))
        self._print("Try to send command <0x%08X> (%s):" % (id_var, self._id_var_to_str(id_var)))
        return id_var

    @staticmethod
    def process_id_var(id_var):
        """
        process id_var_value
        :param id_var: id_var according to title
        :return: егзду of id_var fields
        """
        dev_id = (id_var >> 28) & 0x0F
        var_id = (id_var >> 24) & 0x0F
        offset = (id_var >> 3) & 0x01FFFFF
        res2 = (id_var >> 2) & 0x01
        rtr = (id_var >> 1) & 0x01
        res1 = (id_var >> 0) & 0x01
        return res1, rtr, res2, offset, var_id, dev_id

    def _id_var_to_str(self, id_var):
        ret_str = ""
        ret_str += "dev_id:%2d " % self.process_id_var(id_var)[5]
        ret_str += "var_id:%2d " % self.process_id_var(id_var)[4]
        ret_str += "offs:%3d " % self.process_id_var(id_var)[3]
        ret_str += "rtr:%d-%s " % (self.process_id_var(id_var)[1], "rd" if self.process_id_var(id_var)[1] else "wr")
        return ret_str

    def thread_function(self):
        try:
            id_var = 0
            while True:
                nansw = 0
                if self.is_open is True:
                    time.sleep(0.001)
                    # отправка команд
                    if self.com_queue:
                        self.ready_to_transaction = False
                        with self.com_send_lock:
                            packet_to_send = self.com_queue.pop(0)
                            data_to_send = packet_to_send[0]
                            rtr = packet_to_send[1]
                            finish = packet_to_send[2]
                        if self.in_waiting:
                            self._print("In input buffer %d bytes" % self.in_waiting)
                            self.read(self.in_waiting)
                        try:
                            self.read(self.in_waiting)
                            self.write(bytes(data_to_send))
                            nansw = 1 if rtr == 1 else 0
                            self._print("Send packet: ", bytes_array_to_str(data_to_send))
                        except serial.serialutil.SerialException as error:
                            self.state = -3
                            self._print("Send error: ", error)
                            pass
                        with self.log_lock:
                            self.serial_log_buffer.append(get_time() + bytes_array_to_str(bytes(data_to_send)))
                        # прием ответа: ждем ответа timeout ms только в случае rtr=1
                        buf = bytearray(b"")
                        read_data = bytearray(b"")
                        time_start = time.perf_counter()
                        if rtr:
                            while rtr:
                                time.sleep(0.003)
                                timeout = time.perf_counter() - time_start
                                if timeout >= self.read_timeout:
                                    break
                                try:
                                    read_data = self.read(1024)
                                    self.read_data = read_data
                                except (TypeError, serial.serialutil.SerialException, AttributeError) as error:
                                    self.state = -3
                                    self._print("Receive error: ", error)
                                    pass
                                if read_data:
                                    self._print("Receive data with timeout <%.3f>: " % self.timeout, bytes_array_to_str(read_data))
                                    with self.log_lock:
                                        self.serial_log_buffer.append(get_time() + bytes_array_to_str(read_data))
                                    read_data = buf + bytes(read_data)  # прибавляем к новому куску старый кусок
                                    self._print("Data to process: ", bytes_array_to_str(read_data))
                                    if len(read_data) >= 8:
                                        if read_data[0] == 0x00 or read_data[0] == 0x01:
                                            data_len = int.from_bytes(read_data[6:8], byteorder="little")
                                            if len(read_data) >= data_len + 8:  # проверка на достаточную длину приходящего пакета
                                                nansw -= 1
                                                self.state = 1
                                                rtr = 0
                                                if len(self.answer_data_buffer) == 0:
                                                    id_var = int.from_bytes(read_data[2:6], byteorder="little")
                                                    full_time_start = time_start
                                                self.answer_data_buffer.extend(read_data[8:8 + data_len])
                                                if finish:
                                                    with self.ans_data_lock:
                                                        self.last_answer_data = [id_var,
                                                                                 self.answer_data_buffer]
                                                        self.answer_data.append([id_var,
                                                                                 self.answer_data_buffer])
                                                        self._print(self.can_log_str(id_var, self.answer_data_buffer, len(self.answer_data_buffer)))
                                                    with self.log_lock:
                                                        self.can_log_buffer.append(
                                                            self.can_log_str(id_var, self.answer_data_buffer, len(self.answer_data_buffer)))
                                                    self.answer_data_buffer = []
                                                    finish = False
                                            else:
                                                buf = read_data
                                                read_data = bytearray(b"")
                                        else:
                                            buf = read_data[1:]
                                            read_data = bytearray(b"")
                                    else:
                                        buf = read_data
                                        read_data = bytearray(b"")
                                    pass
                                else:
                                    pass
                        elif rtr == 0:
                            while len(read_data) == 0:
                                time.sleep(0.003)
                                timeout = time.perf_counter() - time_start
                                if timeout >= self.read_timeout:
                                    break
                                try:
                                    read_data = self.read(8)
                                except (TypeError, serial.serialutil.SerialException, AttributeError) as error:
                                    self.state = -3
                                    self._print("Receive error: ", error)
                                    pass
                    else:
                        self.ready_to_transaction = True
                else:
                    pass
                if nansw == 1:
                    self.state = -3
                    self.nansw += 1
                    self._print("Timeout error")
                if self._close_event.is_set() is True:
                    self._close_event.clear()
                    self._print("Close usb_can read thread")
                    return
        except Exception as error:
            self._print("Tx thread ERROR: " + str(error))
        pass

    def get_can_log(self):
        log = None
        with self.log_lock:
            log = copy.deepcopy(self.can_log_buffer)
            self.can_log_buffer = []
        return log

    def get_serial_log(self):
        log = None
        with self.log_lock:
            log = copy.deepcopy(self.serial_log_buffer)
            self.serial_log_buffer = []
        return log

    def get_data(self):
        id_var = 0
        data = []
        with self.ans_data_lock:
            if self.answer_data:
                id_var = self.answer_data[-1][0]
                for i in range(len(self.answer_data[-1][1])):
                    data.append(self.answer_data[-1][1][i])
        try:
            self.answer_data.pop(-1)
        except IndexError:
            pass
        return id_var, data

    def get_last_data(self):
        with self.ans_data_lock:
            if self.last_answer_data:
                id_var = self.last_answer_data[0]
                data = []
                for i in range(len(self.last_answer_data[1])):
                    data.append(self.last_answer_data[1][i])
            else:
                id_var = 0
                data = []
        return id_var, data

    def can_log_str(self, id_var, bytes_data, data_len):
        log_str = "Id_var: 0x%08X (%s); len: %3d; data:%s" % (
                    id_var, self._id_var_to_str(id_var),
                    data_len,
                    bytes_array_to_str(bytes_data))
        return log_str

    def state_check(self):
        state_str = self.state_string[self.state]
        if self.state > 0:
            state_color = "seagreen"
        elif self.state < 0:
            state_color = "orangered"
        else:
            state_color = "gray"
        return state_str, state_color


def get_time():
    return time.strftime("%H-%M-%S", time.localtime()) + "." + ("%.3f:" % time.perf_counter()).split(".")[1]


def str_to_list(send_str):  # функция, которая из последовательности шестнадцетиричных слов в строке без
    send_list = []  # идентификатора 0x делает лист шестнадцетиричных чисел
    send_str = send_str.split(' ')
    for i, ch in enumerate(send_str):
        send_str[i] = ch
        send_list.append(int(send_str[i], 16))
    return send_list


def bytes_array_to_str(bytes_array):
    bytes_string = ""
    for num, ch in enumerate(bytes_array):
        byte_str = "" if num % 2 else " "
        byte_str += ("%02X" % bytes_array[num])
        bytes_string += byte_str
    return bytes_string


if __name__ == "__main__":
    my_can = MyUSBCANDevice(serial_numbers=["205135995748"], debug=True)
    my_can.open_id()
    # Проверка команды зеркала
    my_can.request(can_num=0, dev_id=6, mode="write", var_id=4, offset=16, d_len=1, data=[0x2A])
    time.sleep(2)
    my_can.request(can_num=0, dev_id=6, mode="read", var_id=7, offset=0, d_len=128, data=[])
    time.sleep(2)
    print(my_can.get_data())
    # my_can.request(can_num=0, dev_id=6, mode="read", var_id=4, offset=1, d_len=17, data=[])

    pass
