import lm_data
import time
import crc16
import copy
import random

# класс для управления устройством
lm = lm_data.LMData(serial_numbers=["0000ACF00000", "365938753038"], address=6, debug=False)


def get_time():
    return time.strftime("%H-%M-%S", time.localtime()) + "." + ("%.3f: " % time.perf_counter()).split(".")[1]


def pl_pwr_ctrl(pl_num=0, on_off=0):
    lm.read_cmd_reg(mode="lm_pn_pwr_switch", leng=1)
    time.sleep(0.1)
    state = 0
    if lm.com_registers:
        state = lm.com_registers[0]
    if on_off:
        state |= 1 << pl_num
    else:
        state &= ~(1 << pl_num)
    lm.send_cmd_reg(mode="lm_pn_pwr_switch", data=[state])
    time.sleep(0.1)


def pl_pwr_ctrl_all(on_off=0):
    lm.read_cmd_reg(mode="lm_pn_pwr_switch", leng=1)
    time.sleep(0.1)
    if on_off:
        state = 0xFF
    else:
        state = 0x00
    lm.send_cmd_reg(mode="lm_pn_pwr_switch", data=[state])
    time.sleep(0.1)


def get_pwr_info(channel_type="lm"):
    lm.read_tmi(mode="lm_full_tmi")
    time.sleep(2)
    pl_choosing_dict = {"lm": ["LM:U,V", "LM:I,A"],
                        "pl1": ["PL11A:U,V", "PL11A:I,A"],
                        "pl2": ["PL11B:U,V", "PL11B:I,A"],
                        "pl3": ["PL12:U,V", "PL12:I,A"],
                        "pl4": ["PL20:U,V", "PL20:I,A"],
                        "pl5_1": ["PL_DCR:Umcu,V", "PL_DCR:Imcu,A"],
                        "pl5_2": ["PL_DCR:Umsr,V", "PL_DCR:Imsr,A"]
                        }
    voltage = lm.tmi_dict.get(pl_choosing_dict[channel_type][0], 0.0)
    current = lm.tmi_dict.get(pl_choosing_dict[channel_type][1], 0.0)
    return voltage, current


def mb_answer(ad=0x05, fc=0x03, ar=0x0001, lr=0x01, dr=0x00, dl=None):
    data_to_send = []
    if fc == 0x03:  # F3
        data_to_send = [ad, fc, lr*2]
        data_to_send.extend(dl)
    elif fc == 0x06:  # F6
        data_to_send = [ad, fc, (ar >> 8) & 0xFF, (ar >> 0) & 0xFF, (dr >> 8) & 0xFF, (dr >> 0) & 0xFF]
    elif fc == 0x10:  # F16
        data_to_send = [ad, fc, (ar >> 8) & 0xFF, (ar >> 0) & 0xFF, 0x00, lr]
    crc16_reg = crc16.calc_modbus_crc16_bytes(data_to_send)
    data_to_send.extend(crc16_reg)
    return data_to_send


def mb_request(ad=0x05, fc=0x03, ar=0x0001, lr=0x01, dr=0x00, dl=None):
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
    return data_to_send


def pl_send_instamessage(pl_num=1, data=[], debug=True):
    can_data = [0 for i in range(128)]
    req_param_dict = {"can_num": 0,
                      "dev_id": lm.address, "mode": "write", "var_id": 8, "offset": 0, "d_len": 128, "data": can_data}
    req_param_dict["data"][0] = pl_num
    req_param_dict["data"][127] = len(data)
    req_param_dict["data"][1:1+len(data)] = data

    id_var = lm.usb_can.request(**req_param_dict)
    if debug:
        print("\tTX: ", lm.usb_can.can_log_str(id_var, req_param_dict["data"][1:len(data)+1], len(data)))
    time.sleep(1)
    req_param_dict = {"can_num": 0, "dev_id": lm.address, "mode": "read", "var_id": 5, "offset": 0, "d_len": 128, "data": []}
    pl_offset = [0, 768, 896, 1024, 1152, 640]
    req_param_dict["offset"] = pl_offset[pl_num]
    id_var = lm.usb_can.request(**req_param_dict)
    time.sleep(1)
    rx_len = lm.instamessage_data[127]
    if debug:
        print("\tRX: ", lm.usb_can.can_log_str(id_var, lm.instamessage_data[0:rx_len], rx_len-1))
    time.sleep(1)
    return lm.instamessage_data[0:rx_len]


def pl_send_instamessage_fake(pl_num=1, data=[], data_rx=[], debug=True):
    can_data = [0 for i in range(128)]
    req_param_dict = {"can_num": 0,
                      "dev_id": lm.address, "mode": "write", "var_id": 8, "offset": 0, "d_len": 128, "data": can_data}
    req_param_dict["data"][0] = pl_num
    req_param_dict["data"][127] = len(data)
    req_param_dict["data"][1:1+len(data)] = data

    id_var = lm.usb_can.request(**req_param_dict)
    if debug:
        print("\tTX: ", lm.usb_can.can_log_str(id_var, req_param_dict["data"][1:len(data)+1], len(data)))
    time.sleep(1)
    req_param_dict = {"can_num": 0, "dev_id": lm.address, "mode": "read", "var_id": 5, "offset": 0, "d_len": 128, "data": []}
    pl_offset = [0, 768, 896, 1024, 1152, 640]
    req_param_dict["offset"] = pl_offset[pl_num]
    id_var = lm.usb_can.request(**req_param_dict)
    time.sleep(1)
    rx_data = data_rx
    rx_len = len(rx_data)
    if debug:
        print("\tRX: ", lm.usb_can.can_log_str(id_var, rx_data, rx_len))
    time.sleep(1)
    return lm.instamessage_data[0:rx_len]


def ekkd_test():
    print(get_time(), "Работа с ПН ККД")
    time.sleep(1)
    print("\t", get_time(), "Включение ККД")
    pl_pwr_ctrl(pl_num=1, on_off=1)
    time.sleep(1)
    for i in range(1):
        print("\t", get_time(), "Запрос данных ККД")
        pl_send_instamessage(pl_num=1, data=mb_request(ad=10, fc=3, ar=0x07D0, lr=2))
        time.sleep(1)
    time.sleep(1)
    pl_pwr_ctrl_all(on_off=0)
    pass


def ekkd_autonomus_test():
    print(get_time(), "Автономные испытания ЭО ККД")
    time.sleep(1)
    print("\t", get_time(), "Включение ККД")
    pl_pwr_ctrl(pl_num=1, on_off=1)
    time.sleep(10)
    voltage, current = get_pwr_info(channel_type="pl1")
    print("\t", get_time(), f"Параметры питания: U {voltage:.1f}V, I {current:.3f}A")
    time.sleep(1)
    for i in range(9):
        print("\t", get_time(), f"Запрос данных №{i} ЭО ККД")
        value = random.randint(50, 200)
        pl_send_instamessage_fake(pl_num=1,
                                  data=mb_request(ad=10, fc=3, ar=0x07D0+2*i, lr=2),
                                  data_rx=mb_answer(ad=10, fc=3, ar=0x07D0+2*i, lr=2, dl=[0x00, 0x00,
                                                                                          (value >> 8) & 0xFF,
                                                                                          value & 0xFF]))
        time.sleep(1)
    time.sleep(1)
    print("\t", get_time(), f"Включение режима констант ЭО ККД")
    pl_send_instamessage_fake(pl_num=1,
                              data=mb_request(ad=10, fc=6, ar=0x07E4, lr=1, dl=[0x00, 0x01]),
                              data_rx=mb_answer(ad=10, fc=6, ar=0x07E4, lr=1))
    time.sleep(1)
    print("\t", get_time(), f"Запрос данных 9-ти датчиков ЭО ККД")
    val_list = [i for i in range(18)]
    pl_send_instamessage_fake(pl_num=1,
                              data=mb_request(ad=10, fc=3, ar=0x07D0 + 2 * i, lr=18),
                              data_rx=mb_answer(ad=10, fc=3, ar=0x07D0 + 2 * i, lr=18, dl=val_list))
    time.sleep(1)
    print("\t", get_time(), f"Отключение режима констант ЭО ККД")
    pl_send_instamessage_fake(pl_num=1,
                              data=mb_request(ad=10, fc=6, ar=0x07E4, lr=1, dl=[0x00, 0x00]),
                              data_rx=mb_answer(ad=10, fc=6, ar=0x07E4, lr=1))
    time.sleep(1)
    print("\t", get_time(), f"Запрос данных 9-ти датчиков ЭО ККД")
    val_list = [random.randint(50, 200) for i in range(18)]
    pl_send_instamessage_fake(pl_num=1,
                              data=mb_request(ad=10, fc=3, ar=0x07D0+2*i, lr=2*9),
                              data_rx=mb_answer(ad=10, fc=3, ar=0x07D0+2*i, lr=2*9, dl=val_list))
    time.sleep(1)
    pl_pwr_ctrl_all(on_off=0)
    print(get_time(), "Автономные испытания ЭО ККД закончены")
    pass


def aznv_autonomus_test():
    print(get_time(), "Автономные испытания АЗНВ")
    time.sleep(1)
    print("\t", get_time(), "Включение АЗНВ")
    pl_pwr_ctrl(pl_num=2, on_off=1)
    time.sleep(15)
    voltage, current = get_pwr_info(channel_type="pl2")
    print("\t", get_time(), f"Параметры питания: U {voltage:.1f}V, I {current:.3f}A")
    for i in range(1):
        #
        print("\n\t", get_time(), "___Проверка чтения регистров___\n")
        print("\t", get_time(), "Запрос Регулярной телеметрии")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0, lr=4))
        time.sleep(1)
        print("\t", get_time(), "Запрос Основной телеметрии")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=4, lr=28))
        time.sleep(1)
        print("\t", get_time(), "Запрос Дополнительной телеметрии")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0x20, lr=32))
        time.sleep(1)
        print("\t", get_time(), f"Запрос Целевой информации (самое старое сообщение АЗНВ)")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0x40, lr=11))
        time.sleep(1)
        #
        print("\n\t", get_time(), "___Проверка записи регистров___\n")
        print("\t", get_time(), "Запись регистра состояния")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=6, ar=0, lr=1, dl=[0xFF, 0xFF]))
        time.sleep(1)
        print("\t", get_time(), "Запрос Основной телеметрии")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=4, lr=28))
        time.sleep(1)
        print("\t", get_time(), "Запись регистров маски")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=16, ar=1, lr=2, dl=[0xAA, 0x55, 0xFF, 0x00]))
        time.sleep(1)
        print("\t", get_time(), "Запрос Основной телеметрии")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=4, lr=28))
        time.sleep(1)
        print("\t", get_time(), "Запись регистров времени")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=16, ar=0, lr=3, dl=[0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF]))
        time.sleep(1)
        print("\t", get_time(), "Запрос Основной телеметрии")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=4, lr=28))
        #
        print("\n\t", get_time(), "___Перезагрузка АЗНВ для сброса параметров в значения по умолчанию___\n")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=6, ar=6, lr=1, dl=[0x3E, 0x3F]))
        time.sleep(15)
        #
        print("\n\t", get_time(), "___Проверка приема сообщений АЗНВ___\n")
        print("\t", get_time(), "Запрос регулярной телеметрии раз в ~10 секунд до появления сообщений")
        msg_num = 0
        while msg_num == 0:
            msg = pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0, lr=4), debug=False)
            msg_num = (msg[3] << 8) + msg[4]
            if msg_num:
                pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0, lr=4))
            time.sleep(10)
        print("\t", get_time(), f"Запрос Целевой информации (самое старое сообщение АЗНВ)")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0x40, lr=11))
        time.sleep(1)
    time.sleep(1)
    pl_pwr_ctrl_all(on_off=0)
    print("\n", get_time(), "Автономные испытания АЗНВ окончены", "\n")
    pass


def aznv_test():
    print(get_time(), "Работа с АЗНВ")
    time.sleep(1)
    print("\t", get_time(), "Включение АЗНВ")
    pl_pwr_ctrl(pl_num=2, on_off=1)
    time.sleep(15)
    for i in range(1):
        print("\t", get_time(), "Запрос Температуры ВИП и платы")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=0, lr=4))
        time.sleep(1)
        print("\t", get_time(), "Запрос самого старого сообщения АЗНВ")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=3, ar=64, lr=11))
        time.sleep(1)
        print("\t", get_time(), "Запись параметров времени")
        pl_send_instamessage(pl_num=2, data=mb_request(ad=37, fc=16, ar=3, lr=3, dl=[0xAA, 0xBB, 0xCC, 0xDD, 0xCC, 0xEE]))
        time.sleep(1)
    time.sleep(1)
    pl_pwr_ctrl_all(on_off=0)
    pass


def telescope_test():
    print(get_time(), "Работа с Телескоп")
    time.sleep(1)
    print("\t", get_time(), "Включение Телескоп")
    pl_pwr_ctrl(pl_num=4, on_off=1)
    time.sleep(3)
    for i in range(100):
        print("\t", get_time(), "Reset command")
        pl_send_instamessage(pl_num=5, data=[0x56, 0x00, 0x26, 0x00])
        time.sleep(1)
    time.sleep(1)
    pl_pwr_ctrl_all(on_off=0)
    pass


def telescope_autonomus_test():
    print(get_time(), "Работа с ГФО")
    time.sleep(1)
    print("\t", get_time(), "Включение ГФО")
    pl_pwr_ctrl(pl_num=4, on_off=1)
    time.sleep(3)
    voltage, current = get_pwr_info(channel_type="pl4")
    print("\t", get_time(), f"Параметры питания: U {voltage:.1f}V, I {current:.3f}A")
    time.sleep(3)
    print("\t", get_time(), "Stop current frame")
    pl_send_instamessage(pl_num=5, data=[0x56, 0x00, 0x36, 0x01, 00])
    time.sleep(3)
    print("\t", get_time(), "Frame length request")
    data = pl_send_instamessage(pl_num=5, data=[0x56, 0x00, 0x34, 0x01, 00])
    frame_size = int.from_bytes(bytes(data[5:5+4]), 'big')
    time.sleep(1)
    print("\t", get_time(), "Frame request (first 32 bytes)")
    pl_send_instamessage(pl_num=5, data=[0x56, 0x00, 0x32, 0x0C, 0x00, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20, 0x00, 0x64])
    time.sleep(1)
    print("\t", get_time(), "Back to normal operation mode")
    pl_send_instamessage(pl_num=5, data=[0x56, 0x00, 0x36, 0x01, 0x03])
    time.sleep(1)
    pl_pwr_ctrl_all(on_off=0)
    print(get_time(), "Конец работы с ГФО")
    pass


def read_ft_mem(ft=0, step_num=1):
    ft_name = f"ft{ft}_mem"
    ft_volume_in_frame = step_num//2
    lm.send_cmd_reg(mode="mem_rd_ptr", data=[ft+3, 0, 0, 0, 0])
    time.sleep(0.3)
    data_str = ""
    for i in range(ft_volume_in_frame):
        lm.read_mem(mode=ft_name)
        time.sleep(1.0)
        data_str += lm.get_mem_data(ft+3+1)
    return data_str


def read_mem_part(part=0, num=0):
    lm.send_cmd_reg(mode="mem_rd_ptr", data=[part, 0, 0, 0, 0])
    time.sleep(0.2)
    data_str = ""
    for i in range(num):
        lm.read_mem(part=part)
        time.sleep(1.0)
        data_str += lm.get_mem_data(part + 1)
        percentage = (i/num)*100
        print("\r", "<", int((percentage//10))*"▓"+ int(10-(percentage//10))*"░", f">{percentage:.1f}%", end="")
    print("\n")
    return data_str


def form_step_data(type: int, cmd: int, rpt_cnt: int, delay_ms: int, settings: int, go_to: int, go_cnt: int, data: list):
    """
    /**
     * @brief функция формирования шага полетного задания
     *
     * @param step указатель на структуру шага
     * @param type тип команды
     * @param cmd номер команды
     * @param rpt_cnt счетчик повторов шага
     * @param delay_ms пауза до следующего шага
     * @param settings настройка работы (пока не используется)
     * @param data данные для функции
     */
    void ft_create_ft_step(typeFTStep* step, uint8_t type, uint8_t cmd, uint8_t rpt_cnt, uint16_t delay_ms, uint16_t settings, uint8_t*data)
    {
        step->fields.label      = 0xFAFB;
        step->fields.type       = type;
        step->fields.cmd        = cmd;
        step->fields.rpt_cnt    = rpt_cnt;
        step->fields.go_to      = 0x00;
        step->fields.go_cnt     = 0x00;
        step->fields.delay_ms   = delay_ms;
        step->fields.settings   = settings;
        memset(step->fields.reserve, 0x00, sizeof(step->fields.reserve));
        memcpy(step->fields.data, data, sizeof(step->fields.data));
        step->fields.crc16      = norby_crc16_calc(step->array, sizeof(typeFTStep) - 2);
    }
    :return:
    """
    order = 'little'
    step = b""
    step += 0xFAFB.to_bytes(2, byteorder=order, signed=False)  # flight task mark
    step += type.to_bytes(1, order, signed=False)  # command type
    step += cmd.to_bytes(1, order, signed=False)  # command number
    step += rpt_cnt.to_bytes(2, order, signed=False)  # repeate count
    step += go_to.to_bytes(1, order, signed=False)  # go_to (reserve to future functionality)
    step += go_cnt.to_bytes(1, order, signed=False)  # go_cnt (reserve to future functionality)
    step += delay_ms.to_bytes(4, order, signed=False)  # next function run delay
    step += settings.to_bytes(2, order, signed=False)  # настройки выполнения шага
    step += bytes([0 for i in range(2*8)])  # reserve
    # дополняем данные до 32 байт
    while len(data) < 32:
        data.append(0x00)
    #
    step += bytes(data)  # task step data
    step_crc_16 = crc16.norby_crc16_calc(step, 64-2)
    step += step_crc_16.to_bytes(2, order, signed=False)  # crc16
    print(" ".join([f"{int.from_bytes(step[2*n:2*n+2], byteorder='little'):04X}" for n in range(len(step)//2)]))
    return step


def write_ft_regs(num=0):
    """

    """
    delay = 0.2
    lm.write_ft_regs(num=num, step=0, step_data=form_step_data(0, 0, 0, 3000, 0, 0x00, 0x00, [0x01]))
    time.sleep(delay)
    lm.write_ft_regs(num=num, step=1, step_data=form_step_data(0, 1, 0, 1000, 0x01, 0x00, 0x00, [0]))
    time.sleep(delay)
    lm.write_ft_regs(num=num, step=2, step_data=form_step_data(0, 0, 0, 3000, 0, 0x00, 0x00, [0x00]))
    time.sleep(delay)
    lm.write_ft_regs(num=num, step=3, step_data=form_step_data(0, 1, 0, 1000, 0x01, 0x00, 0x02, [0]))
    for i in range(4, 32):
        time.sleep(delay)
        lm.write_ft_regs(num=num, step=i, step_data=[0 for i in range(64)])


def write_ft_from_reg_to_mem(num=0):
    lm.send_cmd_reg(mode="write_ft_to_mem", data=[num])


def read_ft_from_mem(num=0):
    lm.send_cmd_reg(mode="read_ft_from_mem", data=[num])


def read_ft_from_regs(num=0):
    lm.send_cmd_reg(mode="read_ft_from_regs", data=[num])


def run_ft(num=0):

    lm.send_cmd_reg(mode="run_ft", data=[num])


print(get_time(), "Начало работы")
lm.usb_can.reconnect()
while lm.usb_can.state != 1:
    print(get_time(), "Попытка переподключения")
    time.sleep(1)
    lm.usb_can.reconnect()
print(get_time(), "Старт циклограммы")
ft_num = 3
#general
write_ft_regs(num=ft_num)
time.sleep(1)
write_ft_from_reg_to_mem(num=ft_num)
time.sleep(1)
read_ft_from_mem(num=ft_num)
time.sleep(1)
run_ft(num=ft_num)
time.sleep(1)
print(get_time(), "Конец")


