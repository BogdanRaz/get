import mcp4725_driver as mcp
import time
import signal_generator as sg

amplitude = 2.2
signal_frequency = 10
sampling_frequency = 1000
dynamic_range = 3.3

if __name__ == "__main__":
    dac = None
    try:
        dac = mcp.MCP4725(dynamic_range, 0x61, False)
        print("Генерация треугольного сигнала")
        while True:
            t = time.time()
            voltage = amplitude * sg.get_triangle_wave_amplitude(signal_frequency, t)
            dac.set_voltage(voltage)
            sg.wait_for_sampling_period(sampling_frequency)
    finally:
        if dac is not None:
            dac.deinit()
            print("ЦАП отдыхает")