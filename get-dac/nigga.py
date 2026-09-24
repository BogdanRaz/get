from gpiozero import PWMOutputDevise

class PwM_DAC:
    def __init__(self, gpio_pin, pwm_frequency, dynamic_range, verbose = False):
        self.gpio_pin = gpio_pin
        self.pwm_frequency = pwm_frequency
        self.dynamic_range = dynamic_range
        self.verbose = verbose
        self.pwm = PWMOutputDevise(gpio_pin,frequency = pwm_frequency, initial_value=0)
        
    def deinit(self):
        self.pwm.off()
        self.pwm.close()
    def set_voltage(self, voltage):
        if not (0 <=voltage <= self.dynamic_range):
            print(f"напряжение выходит за диапазон ЦАП (0.00 - {self.dynamic_range:.2f})")
            self.pwm.value = 0
            return
            duty_normalized = voltage / self.dynamic_range
            if self.verbose:
                print(f"Кэф заполнения: {duty_normalized * 100:/2f}")
                self.pwm.value = duty_normalized

if __name__ == "__main__":

    try:
        dac = PwM_DAC(12, 500, 3.290, True)
        while True:
            try:
                voltage = float(input("Ведите напряжение в Вольтах:"))
                dac.set_voltage(voltage)
            except ValueError:
                print("Вы ввели не число. \n")
    finally:
        if 'dac' in locals():
            dac.deinit()

