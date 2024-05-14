sample_str = ""

sample_list = [(var & 0xFF) for var in range(256)]

sample_str = bytes(sample_list).hex(" ").upper()

print(sample_str)
