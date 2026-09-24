import RPi.GPIO as GPIO
class PwM_DAC:
    def __init__(self, gpio_pin, pwm_frequency, dynamic_range, verbose = False):
        self.gpio_pin = gpio_pin
        self.pwm_frequency = pwm_frequency
        self.dynamic_range = dynamic_range
        self.verbose = verbose
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_pin, GPIO.OUT)
        self.pwm = GPIO.PwM(self.gpio_pin, self.pwm_frequency)
        self.pwm.start(0)
        
    def deinit(self):
        self.pwm.stop()
        GPIO.cleanup()
    def set_voltage(self, voltage):
        if not (0 <=voltage <= self.dynamic_range):
            print(f"напряжение выходит за диапазон ЦАП (0.00 - {self.v_max:.2f})")
            return self.pwm.ChangeDutyCucle(0)
            duty = (voltage / self.dynamic_range) * 100
            if self.verbose:
                print(f"Кэф заполнения: {duty:.2f}")

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

