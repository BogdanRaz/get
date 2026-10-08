import pwm_dac as pwm
import time
import signal_generator as sg

amplitude = 3.2
signal_frequency = 10
sampling_frequency = 1000

dynamic_range = 3.183
if __name__ == "__main__":
    dac = None 
    try:
        dac = pwm.PwM_DAC(12, 1000, dynamic_range, verbose=False)
        print(" Генерация запущена")


        while True:
            t = time.time()
            voltage = amplitude * sg.get_sin_wave_amplitude(signal_frequency, t)

            dac.set_voltage(voltage)
            sg.wait_for_sampling_period(sampling_frequency)
    finally:
        if dac is not None:
            dac.deinit()
            print("ЦАП деиницилизирован, порты очищены")