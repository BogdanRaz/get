import RPi.GPIO as GPIO

class PwM_DAC:
    def __init__(self, gpio_pin, pwm_frequency, dynamic_range, verbose=False):
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
        if not (0.0 <=voltage <= self.dynamic_range):
            print(f"напряжение выходит за диапазон ЦАП (0.00 - {self.dynamic_range:.2f})")
            self.pwm.ChangeDutyCucle(0)
            return 
            
        duty = (voltage / self.dynamic_range) * 100
        self.pwm.ChangeDutyCycle(duty)
        if self.verbose:
            print(f" {voltage:.2f} Кэф заполнения: {duty:.2f}")

if __name__ == "__main__":
    dac = None
    try:
        dac = PwM_DAC(12, 1000, 3.183, verbose=True)
        while True:
            try:
                v = float(input("Ведите напряжение в Вольтах:"))
                dac.set_voltage(v)
            except ValueError:
                print("Вы ввели не число. \n")
    finally:
        if dac is not None:
            dac.deinit()
            print("GPIO очищены")