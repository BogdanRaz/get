import RPI.GPIO as GPIO
import mcp3021_driver as mcp
import adc_plot as plott
import time

if __name__ == "__main__":
    adc = mcp.MCP3021(5.19)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(14, GPIO.OUT)
    voltage_value =[]
    time_values = []
    flag = True
    GPIO.OUTPUT(14, 1)
    try:
        start_time = time.time()
        while True:
            otn_time = time.time() - start_time
            voltage_values.append(adc.get_voltage())
            time_values.append(otn_time)
            print(voltage_value[-1])
            if (voltage_values[-1] > 4.8 and flag):
                flag = False
                GPIO.output(14, 0)
            elif (voltage_values[-1] < 0.1 and not flag):
                break
        adc_plot.plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range)
    finally:
        adc.deinit()
        dac.deinit()