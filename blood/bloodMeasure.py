# bloodMeasure.py - запись отсчётов АЦП MCP3021 (датчик давления в манжете)
#   python3 bloodMeasure.py "40 mmHg" 10
#   python3 bloodMeasure.py rest 90
#   python3 bloodMeasure.py fitness 90
# Файл data/<имя>.txt: заголовок, пустая строка и столбец отсчётов (формат о3).
import os
import sys
import time

import numpy as np

from mcp3021_driver import MCP3021


def save(samples, start, finish, filename):
    with open(filename, "w") as outfile:
        outfile.write("- Blood Lab\n")
        outfile.write("- Date: {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start))))
        outfile.write("- Duration: {:.2f} s\n\n".format(finish - start))
        np.savetxt(outfile, np.array(samples), fmt="%d")


name = sys.argv[1]              # имя файла без .txt
duration = float(sys.argv[2])   # секунд

adc = MCP3021(5.0)
samples = []
try:
    start = time.time()
    while time.time() - start < duration:
        samples.append(adc.get_number())        # в цикле только чтение АЦП
    finish = time.time()
finally:
    adc.deinit()

count = len(samples)
rate = count / (finish - start)
print("Отсчётов: {}, частота {:.0f} Гц".format(count, rate))
if max(samples) == 0:
    print("Внимание: с АЦП читаются нули, проверьте подключение датчика")

os.makedirs("data", exist_ok=True)
save(samples, start, finish, os.path.join("data", name + ".txt"))
