import RPi.GPIO as GPIO
import time

class R2R_ADC:
    def __init__(self, dynamic_range, compare_time = 0.01, verbose = False):
        self.dynamic_range = dynamic_range
        self.verbose = verbose
        self.compare_time = compare_time

        self.bits_gpio = [26, 20, 19, 16, 13, 12, 25, 11]
        self.comp_gpio = 21

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.bits_gpio, GPIO.OUT, initial = 0)
        GPIO.setup(self.comp_gpio, GPIO.IN)

    def __del__(self):
        self.number_to_dac(0)
        GPIO.cleanup()
    def number_to_dac(self, number):
        GPIO.output(self.bits_gpio, [int(b) for b in bin(number)[2:].zfill(8)])
    def sequential_counting_adc(self):
        for number in range(256):
            self.number_to_dac(number)
            time.sleep(self.compare_time)
            comp_state = GPIO.input(self.comp_gpio)
            if self.verbose:
                print(f"DAC: {number}, Comparator: {comp_state}")
            if comp_state == GPIO.HIGH:
                return number
        return 255
    
    def get_sc_voltage(self):
        value = self.sequential_counting_adc()
        voltage = (value / 255.0) * self.dynamic_range
        return voltage

if __name__ == "__main__":
    DYNAMIC_RANGE = 3.30
    adc = R2R_ADC(dynamic_range=DYNAMIC_RANGE, verbose=False)
    try:
        while True:
            measured_voltage = adc.get_sc_voltage()
            print(f"Наряжение {measured_voltage:.3f}")
    finally:
        adc.__del__()


