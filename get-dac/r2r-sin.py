import r2r_dac as r2r
import time
import signal_generator as sg

amplitude = 3.183
signal_frequency = 10
sampling_frequency = 1000
dynamic_range = 3.183
if __name__ == "__main__":
    dac = None 
    try:
        dac = r2r.R2R_DAC([16, 20, 21, 25, 26, 17, 27, 22], dynamic_range, verbose=True)
        print(" Генерация запущена")


        while True:
            voltage = amplitude * sg.get_sin_wave_amplitude(signal_frequency, time.time())

            dac.set_voltage(voltage)
            sg.wait_for_sampling_period(sampling_frequency)
    finally:
        if dac is not None:
            dac.deinit()
            print("ЦАП деиницилизирован, порты очищены")




