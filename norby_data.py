
#    модуль собирающий в себе стандартизованные функции разбора данных
#    Стандарт:
#    параметры:
#        frame - побайтовый листа данных
#    возвращает:
#        table_list - список подсписков (подсписок - ["Имя", "Значение"]) - оба поля текстовые

import threading

# замок для мультипоточного запроса разбора данных
data_lock = threading.Lock()
# раскрашивание переменных
# модули
linking_module = 6
eps = 3
# тип кадров
lm_beacon = 0x80
lm_tmi = 0x81
lm_full_tmi = 0x82
lm_cyclogram_result = 0x89
lm_load_param = 0x8A
# Norby 2
pl_sol_tmi = 0x90
pl_sol_frr = 0x91
pl_sol_fr = 0x92
pl_brk_tmi = 0xA0

pl_brk_tmi_0 = 0x00
pl_brk_tmi_1 = 0x01
pl_brk_tmi_2 = 0x02
pl_brk_tmi_3 = 0x03
pl_brk_tmi_4 = 0x04

pl_kkd_tmi = 0x90
pl_kkd_data = 0x91

pl_aznv_reg_tmi = 0xA0
pl_aznv_base_tmi = 0xA1
pl_aznv_extra_tmi = 0xA2
pl_aznv_single_frame_data = 0xA3

pl_gfo_tmi = 0xB0


def frame_parcer(frame):
    try:
        with data_lock:
            data = []
            #
            while len(frame) < 128:
                frame.append(0xFE)
            #
            try:
                b_frame = bytes(frame)
            except Exception as error:
                print(error)
            if 0x0FF1 == val_from(frame, 0, 2):  # проверка на метку кадра
                if 0x0002 == val_from(frame, 2, 2):
                    if get_id_loc_data(val_from(frame, 4, 2))["dev_id"] == linking_module:
                        if get_id_loc_data(val_from(frame, 4, 2))["data_code"] == lm_beacon:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            data.append(["Статус МС", "0x%02X" % val_from(frame, 12, 2)])
                            data.append(["Стутус ПН", "0x%04X" % val_from(frame, 14, 2)])
                            data.append(["Темп. МС, °С", "%d" % val_from(frame, 16, 1, signed=True)])
                            data.append(["Статус пит. ПН", "0x%02X" % val_from(frame, 17, 1)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == lm_tmi:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            for i in range(6):
                                data.append(["ПН%d статус" % i, "0x%04X" % val_from(frame, (12 + i * 2), 2)])
                            for i in range(7):
                                data.append(["ПН%d напр., В" % i, "%.2f" % (val_from(frame, (24 + i * 2), 1, signed=True) / (2 ** 4))])
                                data.append(["ПН%d ток, А" % i, "%.2f" % (val_from(frame, (25 + i * 2), 1, signed=True) / (2 ** 4))])
                            data.append(["МС темп.,°С", "%.2f" % val_from(frame, 38, 1, signed=True)])
                            data.append(["NU темп.,°С", "%.2f" % val_from(frame, 39, 1, signed=True)])
                            for i in range(9):
                                data.append(["Пам.%d ук.чт." % i, "%d" % (val_from(frame, (40 + i * 8), 2))])
                                data.append(["Пам.%d ук.зап." % i, "%d" % (val_from(frame, (42 + i * 8), 2))])
                                data.append(["Пам.%d объем" % i, "%d" % (val_from(frame, (44 + i * 8), 2))])
                                data.append(["Пам.%d запол,%%" % i, "%.2f" % (val_from(frame, (46 + i * 8), 2)/256)])
                            #
                            pl = "LM"
                            offset = 112
                            data.append([f"{pl}:ft num", "%d" % val_from(frame, offset + 0, 1)])
                            data.append([f"{pl}:ft mode", "%d" % val_from(frame, offset + 1, 1)])
                            data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, offset + 2, 1) & 0xF)])
                            data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, offset + 2, 1) >> 4)])
                            data.append([f"{pl}:ft step_num", "%d" % val_from(frame, offset + 3, 1)])
                            data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, offset + 6, 2)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == lm_full_tmi:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            data.append(["LM:id", "0x%04X" % val_from(frame, 12, 2)])
                            data.append(["LM:status", "0x%04X" % val_from(frame, 14, 2)])
                            data.append(["LM:err.flgs", "0x%04X" % val_from(frame, 16, 2)])
                            data.append(["LM:err.cnt", "%d" % val_from(frame, 18, 1)])
                            data.append(["LM:rst.cnt", "%d" % val_from(frame, 19, 1)])
                            data.append(["LM:U,V", "%.3f" % (val_from(frame, 20, 2, signed=True) / 256)])
                            data.append(["LM:I,A", "%.3f" % (val_from(frame, 22, 2, signed=True) / 256)])
                            data.append(["LM:T,°C", "%.3f" % (val_from(frame, 24, 2, signed=True) / 256)])
                            data.append(["LM:ver", "%d.%d.%d" % ((val_from(frame, 26, 1)),
                                                                 (val_from(frame, 27, 1)),
                                                                 (val_from(frame, 28, 1)))])
                            #
                            pl_dict = ["LM", "PL_SOL", "PL_BRK_0"]
                            #
                            for i, pl in enumerate(pl_dict):
                                if pl != "LM":
                                    offset = 12+i*18
                                    data.append([f"{pl}:id", "%d" % val_from(frame, offset + 0, 2)])
                                    data.append([f"{pl}:err.cnt", "%d" % val_from(frame, offset + 2, 2)])
                                    data.append([f"{pl}:status", "0x%04X" % val_from(frame, offset + 4, 2)])
                                    data.append([f"{pl}:voltage", "%.3f" % (val_from(frame, offset + 6, 2, signed=True) / 256)])
                                    data.append([f"{pl}:current", "%.3f" % (val_from(frame, offset + 8, 2, signed=True) / 256)])
                                    data.append([f"{pl}:wr_ptr", "%d" % val_from(frame, offset + 10, 2)])
                                    data.append([f"{pl}:rd_ptr", "%d" % val_from(frame, offset + 12, 2)])
                                    data.append([f"{pl}:full_volume", "%d" % val_from(frame, offset + 14, 2)])
                                    data.append([f"{pl}:mem_fullness", "%.3f" % val_from(frame, offset + 16, 2)])

                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == lm_load_param:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            data.append(["Версия", "%d.%02d.%02d" % (val_from(frame, 12, 2),
                                                                     val_from(frame, 14, 2),
                                                                     val_from(frame, 16, 2))])
                            data.append(["К. питания", "%d" % val_from(frame, 18, 2, signed=True)])
                            data.append(["К. темп", "%d" % val_from(frame, 20, 2, signed=True)])
                            data.append(["Циклограммы", "%d" % val_from(frame, 22, 2, signed=True)])
                            data.append(["CAN", "%d" % val_from(frame, 24, 2, signed=True)])
                            data.append(["Внеш. память", "%d" % val_from(frame, 26, 2, signed=True)])
                            data.append(["Загр. конфиг.", "%d" % val_from(frame, 28, 2, signed=True)])
                            data.append(["Часть flash", "%d" % val_from(frame, 30, 2, signed=True)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_sol_tmi:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            offset = 12
                            pl = "SOL"
                            data.append([f"{pl}:id", "%d" % val_from(frame, offset + 0, 2)])
                            data.append([f"{pl}:err.cnt", "%d" % val_from(frame, offset + 2, 2)])
                            data.append([f"{pl}:status", "0x%04X" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:voltage", "%.3f" % (val_from(frame, offset + 6, 2, signed=True) / 256)])
                            data.append([f"{pl}:current", "%.3f" % (val_from(frame, offset + 8, 2, signed=True) / 256)])
                            data.append([f"{pl}:wr_ptr", "%d" % val_from(frame, offset + 10, 2)])
                            data.append([f"{pl}:rd_ptr", "%d" % val_from(frame, offset + 12, 2)])
                            data.append([f"{pl}:full_volume", "%d" % val_from(frame, offset + 14, 2)])
                            data.append([f"{pl}:mem_fullness", "%.3f" % val_from(frame, offset + 16, 2)])
                            #
                            data.append([f"{pl}:F/C", "0x%04X" % val_from(frame, 30+0, 2)])
                            data.append([f"{pl}:state", "0x%04X" % val_from(frame, 30+36, 2)])
                            data.append([f"{pl}:temp0", "%d" % (val_from(frame, 30+38, 1, signed=False) + 160 - 273)])
                            data.append([f"{pl}:temp1", "%d" % (val_from(frame, 30+39, 1, signed=False) + 160 - 273)])
                            data.append([f"{pl}:raddr", "%d" % (val_from(frame, 30+64, 2, signed=False))])
                            data.append([f"{pl}:eaddr", "%d" % (val_from(frame, 30+66, 2, signed=False))])
                            #
                            offset = 98
                            data.append([f"{pl}:ft num", "%d" % val_from(frame, offset + 0, 1)])
                            data.append([f"{pl}:ft mode", "%d" % val_from(frame, offset + 1, 1)])
                            data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, offset + 2, 1) & 0xF)])
                            data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, offset + 2, 1) >> 4)])
                            data.append([f"{pl}:ft step_num", "%d" % val_from(frame, offset + 3, 1)])
                            data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, offset + 6, 2)])
                            #
                            offset = 106
                            data.append([f"{pl}:ft num", "%d" % val_from(frame, offset + 0, 1)])
                            data.append([f"{pl}:ft mode", "%d" % val_from(frame, offset + 1, 1)])
                            data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, offset + 2, 1) & 0xF)])
                            data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, offset + 2, 1) >> 4)])
                            data.append([f"{pl}:ft step_num", "%d" % val_from(frame, offset + 3, 1)])
                            data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, offset + 6, 2)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_brk_tmi:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            offset = 12
                            pl = "BRK"
                            data.append([f"{pl}:id", "%d" % val_from(frame, offset + 0, 2)])
                            data.append([f"{pl}:err.cnt", "%d" % val_from(frame, offset + 2, 2)])
                            data.append([f"{pl}:status", "0x%04X" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:voltage", "%.3f" % (val_from(frame, offset + 6, 2, signed=True) / 256)])
                            data.append([f"{pl}:current", "%.3f" % (val_from(frame, offset + 8, 2, signed=True) / 256)])
                            data.append([f"{pl}:wr_ptr", "%d" % val_from(frame, offset + 10, 2)])
                            data.append([f"{pl}:rd_ptr", "%d" % val_from(frame, offset + 12, 2)])
                            data.append([f"{pl}:full_volume", "%d" % val_from(frame, offset + 14, 2)])
                            data.append([f"{pl}:mem_fullness", "%.3f" % val_from(frame, offset + 16, 2)])
                            #
                            data.append([f"{pl}:ft num", "%d" % val_from(frame, 30, 1)])
                            data.append([f"{pl}:ft mode", "%d" % val_from(frame, 31, 1)])
                            data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, 32, 1) & 0xF)])
                            data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, 32, 1) >> 4)])
                            data.append([f"{pl}:ft step_num", "%d" % val_from(frame, 33, 1)])
                            data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, 34, 2)])
                            data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, 36, 2)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        else:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            #
                            data.append(["Неизвестный тип данных", "0"])
                    elif get_id_loc_data(val_from(frame, 4, 2))["dev_id"] == eps:
                        if get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_brk_tmi_0:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            data.append(["Вер. ТМИ СЭС0 (PMM PDM)", "%d" % val_from(frame, 12, 2)])
                            data.append(["Режим констант", "0x%02X" % val_from(frame, 14, 1)])
                            data.append(["Режим СЭС", "0x%02X" % val_from(frame, 15, 1)])
                            data.append(["Перекл осн/рез", "0x%02X" % val_from(frame, 16, 1)])
                            data.append(["Выкл.Pass.CPU", "0x%02X" % val_from(frame, 17, 1)])
                            data.append(["Темп.PMM °C", "0x%02X" % val_from(frame, 18, 1, signed=True)])
                            data.append(["Ключи PMM", "0x%04X" % val_from(frame, 19, 2)])

                            data.append(["PwrGd PMM", "0x%04X" % val_from(frame, 21, 2)])
                            data.append(["Статус отказов PMM", "0x%08X" % val_from(frame, 23, 4)])
                            data.append(["Перезапуски осн", "0x%08X" % val_from(frame, 27, 4)])
                            data.append(["Перезапуски пезерв", "0x%08X" % val_from(frame, 31, 4)])
                            data.append(["U VBAT1, mV", "%d" % val_from(frame, 35, 2)])
                            data.append(["U VBAT2, mV", "%d" % val_from(frame, 37, 2)])
                            data.append(["U VBAT1 mean, mV", "%d" % val_from(frame, 39, 2)])
                            data.append(["U VBAT2 mean, mV", "%d" % val_from(frame, 41, 2)])
                            data.append(["I VBAT1, mA", "%d" % val_from(frame, 43, 2)])
                            data.append(["I VBAT2, mA", "%d" % val_from(frame, 45, 2)])
                            data.append(["I VBAT1 mean, mA", "%d" % val_from(frame, 47, 2)])
                            data.append(["I VBAT2 mean, mA", "%d" % val_from(frame, 49, 2)])
                            #
                            data.append(["I СЭС, мА", "%d" % val_from(frame, 51, 2)])
                            data.append(["U PMM, mV", "%d" % val_from(frame, 53, 2)])
                            data.append(["U сил. СЭС, mV", "%d" % val_from(frame, 55, 2)])
                            data.append(["P СЭС, мВт", "%d" % val_from(frame, 57, 2)])
                            data.append(["P КА+ПН, мВт", "%d" % val_from(frame, 59, 2)])
                            data.append(["Концевики", "0x%04X" % val_from(frame, 61, 2)])
                            data.append(["Версия ПО", "%d" % val_from(frame, 63, 2)])
                            #
                            data.append(["Ключи PDM", "0x%04X" % val_from(frame, 65, 2)])
                            data.append(["PwrGd PDM", "0x%04X" % val_from(frame, 67, 2)])
                            data.append(["Статус отказов PDM", "0x%08X" % val_from(frame, 69, 4)])
                            #
                            for i in range(4):
                                data.append([f"T PDM{i}, °C", "%d" % val_from(frame, 73+i, 1, signed=True)])
                            data.append([f"T PDM median, °C", "%d" % val_from(frame, 73+4, 1, signed=True)])
                            #
                            for i in range(6):
                                data.append([f"U PDM{i}, mV", "%d" % val_from(frame, 78+2*i, 2, signed=False)])
                                data.append([f"U PDM{i} mean, mV", "%d" % val_from(frame, 90+2*i, 2, signed=False)])
                                data.append([f"I PDM{i}, mA", "%d" % val_from(frame, 102+2*i, 2, signed=True)])
                                data.append([f"I PDM{i} mean, mA", "%d" % val_from(frame, 114+2*i, 2, signed=True)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_brk_tmi_1:  # ТМИ солнечных панелей 1
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            data.append(["Вер. ТМИ СЭС1 (PAM)", "%d" % val_from(frame, 12, 2)])
                            data.append(["P полн. PAM, мВт", "%d" % val_from(frame, 14, 2)])
                            data.append(["Ключи пит. PAM)", "0x%04X" % val_from(frame, 16, 2)])
                            data.append(["PWR GD", "0x%04X" % val_from(frame, 18, 2)])
                            data.append(["Статус отк.", "0x%08X" % val_from(frame, 20, 4)])
                            #
                            for i in range(4):
                                data.append([f"T PAM{i}, °C", "%d" % val_from(frame, 24+i, 1, signed=True)])
                            data.append([f"T median, °C", "%d" % val_from(frame, 24+4, 1, signed=True)])
                            #
                            data.append(["Ст. IdealDiod", "0x%04X" % val_from(frame, 29, 1)])
                            data.append(["Ст. ош. входных к.", "0x%04X" % val_from(frame, 30, 1)])
                            #
                            name_list = ["Ch1 Y+", "Ch2 X+", "Ch3 Y-", "Ch4 X-", "Ch5 X- F", "Ch6 Y+ F"]
                            for i, name in enumerate(name_list):
                                data.append([f"U {name}, mV", "%d" % val_from(frame, 31 + 2*i, 2)])
                                data.append([f"I {name}, mA", "%d" % val_from(frame, 43 + 2*i, 2, signed=True)])
                            #
                            name_list = ["Ch1 X- F", "Ch2 X-", "Ch3 X+ F", "Ch4 X+", "Ch5 Y+", "Ch6 Y-"]
                            for i, name in enumerate(name_list):
                                data.append([f"Статус {name}", "0x%04X" % val_from(frame, 55 + 2*i, 2)])
                            #
                            name_list = ["Ch1 X- F", "Ch2 X-", "Ch3 X+ F", "Ch4 X+", "Ch5 Y+", "Ch6 Y-"]
                            for i, name in enumerate(name_list):
                                for j in range(4):
                                    data.append([f"T {name} к{j}, °C", "%d" % val_from(frame, 67 + j + 4*i, 1, signed=True)])
                            #
                            name_list = ["Ch1 X- F", "Ch2 X-", "Ch3 X+ F", "Ch4 X+", "Ch5 Y+", "Ch6 Y-"]
                            for i, name in enumerate(name_list):
                                    data.append([f"T median {name}, °C", "%d" % val_from(frame, 91 + i, 1, signed=True)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_brk_tmi_2:  # ТМИ батарей 1
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            data.append(["Вер. ТМИ СЭС2 (PBM ч1)", "%d" % val_from(frame, 12, 2)])
                            #
                            data.append(["P зар/раз, мВт", "%d" % val_from(frame, 14, 2, signed=True)])
                            data.append(["P нагр, мВт", "%d" % val_from(frame, 16, 2)])
                            data.append(["Заряд, mAh", "%d" % val_from(frame, 18, 2)])
                            data.append(["Заряд, %", "%d" % val_from(frame, 20, 1)])
                            data.append(["Кл. зар/раз", "0x%04X" % val_from(frame, 21, 2)])
                            data.append(["Кл. термост", "0x%02X" % val_from(frame, 23, 1)])
                            data.append(["Кл. нагр. PBM", "0x%02X" % val_from(frame, 24, 1)])
                            data.append(["Кл. ав.зар.", "0x%02X" % val_from(frame, 25, 1)])
                            data.append(["Автокорр. зар.", "0x%02X" % val_from(frame, 26, 1)])
                            #
                            for i in range(4):
                                data.append([f"Ош.PBM{i}", "0x%04X" % val_from(frame, 27+2*i, 2)])
                            for i in range(4):
                                data.append([f"Ош.контр.1 PBM{i}", "0x%04X" % val_from(frame, 35+4*i, 2)])
                                data.append([f"Ош.контр.2 PBM{i}", "0x%04X" % val_from(frame, 37+4*i, 2)])
                            for i in range(4):
                                data.append([f"Ур.зар. в.1 PBM{i}, %", "%d" % val_from(frame, 51+2*i, 1)])
                                data.append([f"Ур.зар. в.2 PBM{i}, %", "%d" % val_from(frame, 52+2*i, 1)])
                            for i in range(4):
                                data.append([f"Ур.зар. в.1 PBM{i}, mAh", "%d" % val_from(frame, 59+4*i, 2)])
                                data.append([f"Ур.зар. в.2 PBM{i}, mAh", "%d" % val_from(frame, 61+4*i, 2)])
                            for i in range(4):
                                data.append([f"I зар. в.1 PBM{i}, mA", "%d" % val_from(frame, 75+4*i, 2, signed=True)])
                                data.append([f"I зар. в.2 PBM{i}, mA", "%d" % val_from(frame, 77+4*i, 2, signed=True)])
                            for i in range(4):
                                data.append([f"T PBM{i} кнтр.1, °C", "%d" % val_from(frame, 91+6*i, 1, signed=True)])
                                data.append([f"T PBM{i} кнтр.2, °C", "%d" % val_from(frame, 92+6*i, 1, signed=True)])
                                for j in range(4):
                                    data.append([f"T PBM{i} пл.{j}, °C", "%d" % val_from(frame, 93+1*j+6*i, 1, signed=True)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_brk_tmi_3:  # ТМИ батарей 2
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            data.append(["Вер. ТМИ СЭС3 (PBM ч2)", "%d" % val_from(frame, 12, 2)])
                            #
                            for i in range(4):
                                for j in range(2):
                                    for k in range(2):
                                        data.append([f"U PBM{i} в{j} акк{k}, мВ", "%d" % val_from(frame, 14 + k*2 + j*4 + 8*i, 2)])
                            #
                            for i in range(4):
                                for j in range(2):
                                        data.append([f"I max PBM{i} в{j}, мA", "%d" % val_from(frame, 46 + j*4 + 8*i, 2, signed=True)])
                                        data.append([f"I min PBM{i} в{j}, мA", "%d" % val_from(frame, 48 + j*4 + 8*i, 2, signed=True)])
                            #
                            for i in range(4):
                                for j in range(2):
                                        data.append([f"Ubat min PBM{i} в{j}, мВ", "%d" % val_from(frame, 78 + j*2 + 4*i, 2)])
                            #
                            for i in range(4):
                                for j in range(2):
                                        data.append([f"I нагр PBM{i} в{j}, мA", "%d" % val_from(frame, 94 + j*2 + 4*i, 2, signed=True)])
                            #
                            for i in range(4):
                                for j in range(2):
                                        data.append([f"Возраст PBM{i} в{j}", "%d" % val_from(frame, 110 + j*1 + 2*i, 1)])
                            #
                            for i in range(4):
                                for j in range(2):
                                        data.append([f"Кол-во циклов PBM{i} в{j}", "%d" % val_from(frame, 118 + j*1 + 2*i, 1)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                    else:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                        #
                        data.append(["Неизвестный определитель", "0"])
                elif 0x0003 == val_from(frame, 2, 2):
                    if get_id_loc_data(val_from(frame, 4, 2))["dev_id"] == linking_module:
                        if get_id_loc_data(val_from(frame, 4, 2))["data_code"] == lm_beacon:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            data.append(["Статус МС", "0x%02X" % val_from(frame, 12, 2)])
                            data.append(["Стутус ПН", "0x%04X" % val_from(frame, 14, 2)])
                            data.append(["Темп. МС, °С", "%d" % val_from(frame, 16, 1, signed=True)])
                            data.append(["Статус пит. ПН", "0x%02X" % val_from(frame, 17, 1)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == lm_tmi:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            for i in range(6):
                                data.append(["ПН%d статус" % i, "0x%04X" % val_from(frame, (12 + i * 2), 2)])
                            for i in range(7):
                                data.append(["ПН%d напр., В" % i, "%.2f" % (val_from(frame, (24 + i * 2), 1, signed=True) / (2 ** 4))])
                                data.append(["ПН%d ток, А" % i, "%.2f" % (val_from(frame, (25 + i * 2), 1, signed=True) / (2 ** 4))])
                            data.append(["МС темп.,°С", "%.2f" % val_from(frame, 38, 1, signed=True)])
                            data.append(["NU темп.,°С", "%.2f" % val_from(frame, 39, 1, signed=True)])
                            for i in range(9):
                                data.append(["Пам.%d ук.чт." % i, "%d" % (val_from(frame, (40 + i * 8), 2))])
                                data.append(["Пам.%d ук.зап." % i, "%d" % (val_from(frame, (42 + i * 8), 2))])
                                data.append(["Пам.%d объем" % i, "%d" % (val_from(frame, (44 + i * 8), 2))])
                                data.append(["Пам.%d запол,%%" % i, "%.2f" % (val_from(frame, (46 + i * 8), 2)/256)])
                            #
                            pl = "LM"
                            offset = 112
                            data.append([f"{pl}:ft num", "%d" % val_from(frame, offset + 0, 1)])
                            data.append([f"{pl}:ft mode", "%d" % val_from(frame, offset + 1, 1)])
                            data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, offset + 2, 1) & 0xF)])
                            data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, offset + 2, 1) >> 4)])
                            data.append([f"{pl}:ft step_num", "%d" % val_from(frame, offset + 3, 1)])
                            data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, offset + 6, 2)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == lm_full_tmi:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            data.append(["LM:id", "0x%04X" % val_from(frame, 12, 2)])
                            data.append(["LM:status", "0x%04X" % val_from(frame, 14, 2)])
                            data.append(["LM:err.flgs", "0x%04X" % val_from(frame, 16, 2)])
                            data.append(["LM:err.cnt", "%d" % val_from(frame, 18, 1)])
                            data.append(["LM:rst.cnt", "%d" % val_from(frame, 19, 1)])
                            data.append(["LM:U,V", "%.3f" % (val_from(frame, 20, 2, signed=True) / 256)])
                            data.append(["LM:I,A", "%.3f" % (val_from(frame, 22, 2, signed=True) / 256)])
                            data.append(["LM:T,°C", "%.3f" % (val_from(frame, 24, 2, signed=True) / 256)])
                            data.append(["LM:ver", "%d.%d.%d" % ((val_from(frame, 26, 1)),
                                                                 (val_from(frame, 27, 1)),
                                                                 (val_from(frame, 28, 1)))])
                            #
                            pl_dict = ["LM", "PL_KKD", "PL_AZNV", "PL_GFO"]
                            #
                            for i, pl in enumerate(pl_dict):
                                if pl != "LM":
                                    offset = 12+i*18
                                    data.append([f"{pl}:id", "%d" % val_from(frame, offset + 0, 2)])
                                    data.append([f"{pl}:err.cnt", "%d" % val_from(frame, offset + 2, 2)])
                                    data.append([f"{pl}:status", "0x%04X" % val_from(frame, offset + 4, 2)])
                                    data.append([f"{pl}:voltage", "%.3f" % (val_from(frame, offset + 6, 2, signed=True) / 256)])
                                    data.append([f"{pl}:current", "%.3f" % (val_from(frame, offset + 8, 2, signed=True) / 256)])
                                    data.append([f"{pl}:wr_ptr", "%d" % val_from(frame, offset + 10, 2)])
                                    data.append([f"{pl}:rd_ptr", "%d" % val_from(frame, offset + 12, 2)])
                                    data.append([f"{pl}:full_volume", "%d" % val_from(frame, offset + 14, 2)])
                                    data.append([f"{pl}:mem_fullness", "%.3f" % val_from(frame, offset + 16, 2)])

                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == lm_load_param:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            data.append(["Версия", "%d.%02d.%02d" % (val_from(frame, 12, 2),
                                                                     val_from(frame, 14, 2),
                                                                     val_from(frame, 16, 2))])
                            data.append(["К. питания", "%d" % val_from(frame, 18, 2, signed=True)])
                            data.append(["К. темп", "%d" % val_from(frame, 20, 2, signed=True)])
                            data.append(["Циклограммы", "%d" % val_from(frame, 22, 2, signed=True)])
                            data.append(["CAN", "%d" % val_from(frame, 24, 2, signed=True)])
                            data.append(["Внеш. память", "%d" % val_from(frame, 26, 2, signed=True)])
                            data.append(["Загр. конфиг.", "%d" % val_from(frame, 28, 2, signed=True)])
                            data.append(["Часть flash", "%d" % val_from(frame, 30, 2, signed=True)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_kkd_tmi:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            offset = 12
                            pl = "KKD"
                            data.append([f"{pl}:id", "%d" % val_from(frame, offset + 0, 2)])
                            data.append([f"{pl}:err.cnt", "%d" % val_from(frame, offset + 2, 2)])
                            data.append([f"{pl}:status", "0x%04X" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:voltage", "%.3f" % (val_from(frame, offset + 6, 2, signed=True) / 256)])
                            data.append([f"{pl}:current", "%.3f" % (val_from(frame, offset + 8, 2, signed=True) / 256)])
                            data.append([f"{pl}:wr_ptr", "%d" % val_from(frame, offset + 10, 2)])
                            data.append([f"{pl}:rd_ptr", "%d" % val_from(frame, offset + 12, 2)])
                            data.append([f"{pl}:full_volume", "%d" % val_from(frame, offset + 14, 2)])
                            data.append([f"{pl}:mem_fullness", "%.3f" % val_from(frame, offset + 16, 2)])
                            #
                            offset = 98
                            data.append([f"{pl}:ft num", "%d" % val_from(frame, offset + 0, 1)])
                            data.append([f"{pl}:ft mode", "%d" % val_from(frame, offset + 1, 1)])
                            data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, offset + 2, 1) & 0xF)])
                            data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, offset + 2, 1) >> 4)])
                            data.append([f"{pl}:ft step_num", "%d" % val_from(frame, offset + 3, 1)])
                            data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, offset + 6, 2)])
                            #
                            offset = 106
                            data.append([f"{pl}:ft num", "%d" % val_from(frame, offset + 0, 1)])
                            data.append([f"{pl}:ft mode", "%d" % val_from(frame, offset + 1, 1)])
                            data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, offset + 2, 1) & 0xF)])
                            data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, offset + 2, 1) >> 4)])
                            data.append([f"{pl}:ft step_num", "%d" % val_from(frame, offset + 3, 1)])
                            data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, offset + 6, 2)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif   (get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_aznv_reg_tmi or
                                get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_aznv_base_tmi or 
                                get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_aznv_extra_tmi):
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            offset = 12
                            pl = "AZNV"
                            data.append([f"{pl}:id", "%d" % val_from(frame, offset + 0, 2)])
                            data.append([f"{pl}:err.cnt", "%d" % val_from(frame, offset + 2, 2)])
                            data.append([f"{pl}:status", "0x%04X" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:voltage", "%.3f" % (val_from(frame, offset + 6, 2, signed=True) / 256)])
                            data.append([f"{pl}:current", "%.3f" % (val_from(frame, offset + 8, 2, signed=True) / 256)])
                            data.append([f"{pl}:wr_ptr", "%d" % val_from(frame, offset + 10, 2)])
                            data.append([f"{pl}:rd_ptr", "%d" % val_from(frame, offset + 12, 2)])
                            data.append([f"{pl}:full_volume", "%d" % val_from(frame, offset + 14, 2)])
                            data.append([f"{pl}:mem_fullness", "%.3f" % val_from(frame, offset + 16, 2)])
                            #
                            offset = 30
                            if get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_aznv_reg_tmi:
                                data.append([f"{pl}:msg cnter", "%d" % val_from(frame, offset + 0, 2, byteorder="big")])
                                data.append([f"{pl}:correct msg last min", "%d" % val_from(frame, offset + 2, 2, byteorder="big")])
                                data.append([f"{pl}:saved msg last min", "%d" % val_from(frame, offset + 4, 2, byteorder="big")])
                                data.append([f"{pl}:T VIP, °C", "%d" % val_from(frame, offset + 6, 1, signed=True)])
                                data.append([f"{pl}:T board T, °C", "%d" % val_from(frame, offset + 7, 1, signed=True)])
                                pass
                            elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_aznv_base_tmi:
                                data.append([f"{pl}:oper. t,s", "%d" % val_from(frame, offset + 0, 4, byteorder="big")])
                                data.append([f"{pl}:mask", "0x%08X" % val_from(frame, offset + 4, 4, byteorder="big")])
                                data.append([f"{pl}:rec msg cnter", "%d" % val_from(frame, offset + 8, 4, byteorder="big")])
                                data.append([f"{pl}:corr msg cnter", "%d" % val_from(frame, offset + 12, 4, byteorder="big")])
                                data.append([f"{pl}:saved msg cnter", "%d" % val_from(frame, offset + 16, 4, byteorder="big")])
                                data.append([f"{pl}:uart err cnter", "%d" % val_from(frame, offset + 20, 4, byteorder="big")])
                                data.append([f"{pl}:last min rec msg", "%d" % val_from(frame, offset + 24, 2)])
                                data.append([f"{pl}:last min corr msg", "%d" % val_from(frame, offset + 26, 2)])
                                data.append([f"{pl}:last min saved msg", "%d" % val_from(frame, offset + 28, 2)])
                                data.append([f"{pl}:last min uart err", "%d" % val_from(frame, offset + 30, 2)])
                                data.append([f"{pl}:reserve", "0x%02X" % val_from(frame, offset + 32, 1)])
                                data.append([f"{pl}:status", "0x%04X" % val_from(frame, offset + 33, 2)])
                                data.append([f"{pl}:reserve", "0x%04X" % val_from(frame, offset + 35, 2)])
                                data.append([f"{pl}:can trans TMI", "%d" % val_from(frame, offset + 37, 2)])
                                data.append([f"{pl}:version", "0x%04X" % val_from(frame, offset + 39, 2)])
                                data.append([f"{pl}:T VIP, °C", "%d" % (127 + val_from(frame, offset + 41, 1, signed=True))])
                                data.append([f"{pl}:T board T, °C", "%d" % (127 + val_from(frame, offset + 42, 1, signed=True))])
                                data.append([f"{pl}:Time BCD", "%012X" % val_from(frame, offset + 43, 6, byteorder="big")])
                                data.append([f"{pl}:icao cnter", "%d" % val_from(frame, offset + 49, 2)])
                                data.append([f"{pl}:msg cnter", "%d" % val_from(frame, offset + 51, 2)])
                                pass
                            elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_aznv_extra_tmi:
                                data.append([f"{pl}:oper. t,s", "%d" % val_from(frame, offset + 0, 4, byteorder="big")])
                                data.append([f"{pl}:can trans TMI", "%d" % val_from(frame, offset + 4, 2)])
                                data.append([f"{pl}:max msg in mem", "%d" % val_from(frame, offset + 6, 2)])
                                data.append([f"{pl}:bild", "%d" % val_from(frame, offset + 8, 2)])
                                data.append([f"{pl}:extra status", "%d" % val_from(frame, offset + 10, 2)])
                                data.append([f"{pl}:mask", "%d" % val_from(frame, offset + 12, 4, byteorder="big")])
                                data.append([f"{pl}:can c1ec", "%d" % val_from(frame, offset + 16, 2)])
                                data.append([f"{pl}:can c2ec", "%d" % val_from(frame, offset + 18, 2)])
                                data.append([f"{pl}:last min rec msg", "%d" % val_from(frame, offset + 20, 2)])
                                data.append([f"{pl}:last min corr msg", "%d" % val_from(frame, offset + 22, 2)])
                                data.append([f"{pl}:last min saved msg", "%d" % val_from(frame, offset + 24, 2)])
                                data.append([f"{pl}:last min uart err", "%d" % val_from(frame, offset + 26, 2)])
                                for cnter_num in range(8):
                                    data.append([f"{pl}:cnter {cnter_num + 1}", "%d" % val_from(frame, offset + 28 + cnter_num*4, 4, byteorder="big")])
                                pass
                            #
                            offset = 98
                            data.append([f"{pl}:ft num", "%d" % val_from(frame, offset + 0, 1)])
                            data.append([f"{pl}:ft mode", "%d" % val_from(frame, offset + 1, 1)])
                            data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, offset + 2, 1) & 0xF)])
                            data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, offset + 2, 1) >> 4)])
                            data.append([f"{pl}:ft step_num", "%d" % val_from(frame, offset + 3, 1)])
                            data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, offset + 6, 2)])
                            #
                            offset = 106
                            data.append([f"{pl}:ft num", "%d" % val_from(frame, offset + 0, 1)])
                            data.append([f"{pl}:ft mode", "%d" % val_from(frame, offset + 1, 1)])
                            data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, offset + 2, 1) & 0xF)])
                            data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, offset + 2, 1) >> 4)])
                            data.append([f"{pl}:ft step_num", "%d" % val_from(frame, offset + 3, 1)])
                            data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, offset + 6, 2)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_aznv_single_frame_data:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            offset = 12
                            for n in range(5):
                                data.append([f"MSG{n}: label", "%d" % val_from(frame, offset + n*22, 2)])
                                data.append([f"MSG{n}: label", "%012X" % val_from(frame, offset + n*22 + 2, 6, byteorder='big')])
                                data.append([f"MSG{n}: label", "0x%08X..." % val_from(frame, offset + n*22 + 8, 4)])
                                pass
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_kkd_data:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            adc_k = 2.5/(2**12)
                            for n in range(2):
                                for pr in range(9):
                                    data.append([f"M{n} pr{pr}: U, V", "%.3f" % (val_from(frame, 12 + n*50 + pr*4, 2) * 0.0390625 - 1)])
                                    data.append([f"M{n} pr{pr}: T, °C", "%d" % val_from(frame, 14 + n*50 + pr*4, 2)])
                                for prt in range(3):
                                    data.append([f"M{n} st{pr}", "0x%04X" % val_from(frame, 12 + 36 + n * 50 + prt * 2, 2)])
                                for prt in range(3):
                                    data.append([f"M{n} ion{pr}: U, V", "%.3f" % (val_from(frame, 12 + 42 + n * 50 + prt * 2, 2) * adc_k)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_gfo_tmi:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                            #
                            offset = 12
                            pl = "GFO"
                            data.append([f"{pl}:id", "%d" % val_from(frame, offset + 0, 2)])
                            data.append([f"{pl}:err.cnt", "%d" % val_from(frame, offset + 2, 2)])
                            data.append([f"{pl}:status", "0x%04X" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:voltage", "%.3f" % (val_from(frame, offset + 6, 2, signed=True) / 256)])
                            data.append([f"{pl}:current", "%.3f" % (val_from(frame, offset + 8, 2, signed=True) / 256)])
                            data.append([f"{pl}:wr_ptr", "%d" % val_from(frame, offset + 10, 2)])
                            data.append([f"{pl}:rd_ptr", "%d" % val_from(frame, offset + 12, 2)])
                            data.append([f"{pl}:full_volume", "%d" % val_from(frame, offset + 14, 2)])
                            data.append([f"{pl}:mem_fullness", "%.3f" % val_from(frame, offset + 16, 2)])
                            #
                            data.append([f"{pl}:resolution", "%d" % val_from(frame, offset + 18, 1)])
                            data.append([f"{pl}:compression", "%d" % val_from(frame, offset + 19, 1)])
                            data.append([f"{pl}:triger time", "%d" % val_from(frame, offset + 20, 6)])
                            data.append([f"{pl}:triger orient", "%d" % val_from(frame, offset + 26, 16)])
                            data.append([f"{pl}:version", "%s" % bytes(frame[offset + 42: offset + 42 + 16])])
                            #
                            offset = 98
                            data.append([f"{pl}:ft num", "%d" % val_from(frame, offset + 0, 1)])
                            data.append([f"{pl}:ft mode", "%d" % val_from(frame, offset + 1, 1)])
                            data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, offset + 2, 1) & 0xF)])
                            data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, offset + 2, 1) >> 4)])
                            data.append([f"{pl}:ft step_num", "%d" % val_from(frame, offset + 3, 1)])
                            data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, offset + 6, 2)])
                            #
                            offset = 106
                            data.append([f"{pl}:ft num", "%d" % val_from(frame, offset + 0, 1)])
                            data.append([f"{pl}:ft mode", "%d" % val_from(frame, offset + 1, 1)])
                            data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, offset + 2, 1) & 0xF)])
                            data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, offset + 2, 1) >> 4)])
                            data.append([f"{pl}:ft step_num", "%d" % val_from(frame, offset + 3, 1)])
                            data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, offset + 4, 2)])
                            data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, offset + 6, 2)])
                            #
                            data.append(["CRC-16", "0x%04X" % norby_crc16_calc(frame, 126)])
                        else:
                            #
                            data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                            data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                            data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                            data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                            #
                            data.append(["Неизвестный тип данных", "0"])
                    else:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                        #
                        data.append(["Неизвестный определитель", "0"])
            else:
                data.append(["Данные не распознаны", "0"])
            return data
    except Exception as error:
        print(error)
        return None


def get_id_loc_data(id_loc):
    """
    разбор переменной IdLoc
    :param id_loc: переменная, содржащая IdLoc по формату описания на протокол СМКА
    :return: кортеж значений полей переменной IdLoc: номер устройства, флаги записи, код данных
    """
    device_id = (id_loc >> 12) & 0xF
    flags = (id_loc >> 8) & 0xF
    data_id = (id_loc >> 0) & 0xFF
    # print({"dev_id": device_id, "flags": flags, "data_code": f"{data_id:04X}"})
    return {"dev_id": device_id, "flags": flags, "data_code": data_id}


def val_from(frame, offset, leng, byteorder="little", signed=False, debug=False):
    """
    обертка для функции сбора переменной из оффсета и длины, пишется короче и по умолчанию значения самый используемые
    :param frame: лист с данными кадра
    :param offset: оффсет переменной в байтах
    :param leng: длина переменной в байтах
    :param byteorder: порядок следования байт в срезе ('little', 'big')
    :param signed: знаковая или не знаковая переменная (True, False)
    :return: интовое значение переменной
    """
    retval = int.from_bytes(frame[offset + 0:offset + leng], byteorder=byteorder, signed=signed)
    if debug:
        print(frame[offset + 0:offset + leng], " %04X" % int.from_bytes(frame[offset + 0:offset + leng], byteorder=byteorder, signed=signed))
    return retval


# crc16 для интерфейса Норби
crc16_ccitt_table_reverse = [
    0x0000, 0x1189, 0x2312, 0x329B, 0x4624, 0x57AD, 0x6536, 0x74BF,
    0x8C48, 0x9DC1, 0xAF5A, 0xBED3, 0xCA6C, 0xDBE5, 0xE97E, 0xF8F7,
    0x1081, 0x0108, 0x3393, 0x221A, 0x56A5, 0x472C, 0x75B7, 0x643E,
    0x9CC9, 0x8D40, 0xBFDB, 0xAE52, 0xDAED, 0xCB64, 0xF9FF, 0xE876,
    0x2102, 0x308B, 0x0210, 0x1399, 0x6726, 0x76AF, 0x4434, 0x55BD,
    0xAD4A, 0xBCC3, 0x8E58, 0x9FD1, 0xEB6E, 0xFAE7, 0xC87C, 0xD9F5,
    0x3183, 0x200A, 0x1291, 0x0318, 0x77A7, 0x662E, 0x54B5, 0x453C,
    0xBDCB, 0xAC42, 0x9ED9, 0x8F50, 0xFBEF, 0xEA66, 0xD8FD, 0xC974,
    0x4204, 0x538D, 0x6116, 0x709F, 0x0420, 0x15A9, 0x2732, 0x36BB,
    0xCE4C, 0xDFC5, 0xED5E, 0xFCD7, 0x8868, 0x99E1, 0xAB7A, 0xBAF3,
    0x5285, 0x430C, 0x7197, 0x601E, 0x14A1, 0x0528, 0x37B3, 0x263A,
    0xDECD, 0xCF44, 0xFDDF, 0xEC56, 0x98E9, 0x8960, 0xBBFB, 0xAA72,
    0x6306, 0x728F, 0x4014, 0x519D, 0x2522, 0x34AB, 0x0630, 0x17B9,
    0xEF4E, 0xFEC7, 0xCC5C, 0xDDD5, 0xA96A, 0xB8E3, 0x8A78, 0x9BF1,
    0x7387, 0x620E, 0x5095, 0x411C, 0x35A3, 0x242A, 0x16B1, 0x0738,
    0xFFCF, 0xEE46, 0xDCDD, 0xCD54, 0xB9EB, 0xA862, 0x9AF9, 0x8B70,
    0x8408, 0x9581, 0xA71A, 0xB693, 0xC22C, 0xD3A5, 0xE13E, 0xF0B7,
    0x0840, 0x19C9, 0x2B52, 0x3ADB, 0x4E64, 0x5FED, 0x6D76, 0x7CFF,
    0x9489, 0x8500, 0xB79B, 0xA612, 0xD2AD, 0xC324, 0xF1BF, 0xE036,
    0x18C1, 0x0948, 0x3BD3, 0x2A5A, 0x5EE5, 0x4F6C, 0x7DF7, 0x6C7E,
    0xA50A, 0xB483, 0x8618, 0x9791, 0xE32E, 0xF2A7, 0xC03C, 0xD1B5,
    0x2942, 0x38CB, 0x0A50, 0x1BD9, 0x6F66, 0x7EEF, 0x4C74, 0x5DFD,
    0xB58B, 0xA402, 0x9699, 0x8710, 0xF3AF, 0xE226, 0xD0BD, 0xC134,
    0x39C3, 0x284A, 0x1AD1, 0x0B58, 0x7FE7, 0x6E6E, 0x5CF5, 0x4D7C,
    0xC60C, 0xD785, 0xE51E, 0xF497, 0x8028, 0x91A1, 0xA33A, 0xB2B3,
    0x4A44, 0x5BCD, 0x6956, 0x78DF, 0x0C60, 0x1DE9, 0x2F72, 0x3EFB,
    0xD68D, 0xC704, 0xF59F, 0xE416, 0x90A9, 0x8120, 0xB3BB, 0xA232,
    0x5AC5, 0x4B4C, 0x79D7, 0x685E, 0x1CE1, 0x0D68, 0x3FF3, 0x2E7A,
    0xE70E, 0xF687, 0xC41C, 0xD595, 0xA12A, 0xB0A3, 0x8238, 0x93B1,
    0x6B46, 0x7ACF, 0x4854, 0x59DD, 0x2D62, 0x3CEB, 0x0E70, 0x1FF9,
    0xF78F, 0xE606, 0xD49D, 0xC514, 0xB1AB, 0xA022, 0x92B9, 0x8330,
    0x7BC7, 0x6A4E, 0x58D5, 0x495C, 0x3DE3, 0x2C6A, 0x1EF1, 0x0F78
]


def norby_crc16_calc(buffer, leng: int):
    """
    подсчет контрольной суммы CRC-16 для кадров (как в AX25)
    :param buffer: буфер с данными для подсчета контрольной суммы
    :param leng: len длина буфера данных
    :return: crc16 финальная контрольная сумма посчитанная на выходные данные
    """
    fcs = 0xFFFF
    for num in range(leng):
        fcs = ((fcs >> 8) & 0xFFFF) ^ crc16_ccitt_table_reverse[(fcs ^ buffer[num]) & 0xFF]
    return fcs ^ 0xFFFF


if __name__ == "__main__":
    # frame_str = "0FF1 0002 6090 0095 6002 001C 0001 001B 0005 0510 0030 0000 0000 3AA3 0000 0040 0040 0002 0003 8000 0005 0006 0007 0000 0009 4222 000B 000C 000D 3472 000F 0002 088C 0100 A26A 03F5 0547 03F5 0547 04A4 05F8 015F 000D 000D 00B1 6D61 001F 0000 0000 0001 0000 0000 0000 0002 0000 0000 0000 FEFE FEFE FEFE FEFE FEFE FEFE 54D6"
    frame_str = "0FF1 0003 60A1 002E 431E 0000 0002 0005 0011 0691 0042 001A 0000 1853 0000 0000 1604 FFFF FFFF 0000 A904 0000 4402 0000 3900 0000 0000 ED00 9000 1500 0000 B600 0020 0000 0123 A645 01A7 0101 1700 0026 0300 0000 0000 FEFE FEFE FEFE FEFE FEFE FEFE FEFE 0003 0000 0000 0000 0204 0C01 0000 0000 FEFE FEFE FEFE FEFE FEFE 7B00"
    frame_b = bytes.fromhex(frame_str.replace(" ", ""))
    print(frame_b.hex(" ", 1))
    frame_list = [frame_b[i+(1-2*(i%2))] for i in range(len(frame_b))]
    print(frame_list)
    parc_result = frame_parcer(frame_list)
    print("\n".join([f"{var}" for var in parc_result]))
