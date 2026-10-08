import r2r_dac as r2r
import time
import signal_generator as sg

amplitude = 2.0
signal_frequency = 10
sampling_frequency = 1000
dynamic_range = 3.183

if __name__ == "__main__":
    dac = None
    try:
        dac = r2r.R2R_DAC([16, 20, 21, 25, 26, 17, 27, 22], dynamic_range, verbose=False)
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