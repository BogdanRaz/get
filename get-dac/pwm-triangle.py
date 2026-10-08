import pwm_dac as pwm
import time
import signal_generator as sg

amplitude = 2.2
signal_frequency = 1
sampling_frequency = 1000
dynamic_range = 3.3

if __name__ == "__main__":
    dac = None
    try:
        dac = pwm.PWM_DAC(12, 1000, dynamic_range, verbose=False)
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