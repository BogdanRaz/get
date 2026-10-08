import mcp4725_driver as mcp
import time
import signal_generator as sg

amplitude = 4
signal_frequency = 10
sampling_frequency = 1000
dynamic_range = 5.11

if __name__ == "__main__":
    dac = None 
    try:
        dac = mcp.MCP4725(dynamic_range, 0x61, False)

        print(" Генерация запущена")


        while True:
            voltage = amplitude * sg.get_sin_wave_amplitude(signal_frequency, time.time())

            dac.set_voltage(voltage)
            sg.wait_for_sampling_period(sampling_frequency)
    finally:
        if dac is not None:
            dac.deinit()
            print("ЦАП деиницилизирован, порты очищены")




