import RPi.GPIO as GPIO
import mcp3021_driver as mcp
import adc_plot
import time

U_CHARGED = 4.8      # порог "заряжен" (если упирается в 3.3 В, поставь 3.2)
U_DISCHARGED = 0.1   # порог "разряжен"

if __name__ == "__main__":
    adc = mcp.MCP3021(5.19)
    voltage_values = []
    time_values = []
    charging = True
    t_switch = None
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(14, GPIO.OUT)
        GPIO.output(14, 1)          # начинаем зарядку

        start_time = time.time()
        while True:
            t = time.time() - start_time
            u = adc.get_voltage()
            voltage_values.append(u)
            time_values.append(t)
            print(t, u)

            if u > U_CHARGED and charging:
                charging = False
                t_switch = t
                GPIO.output(14, 0)  # начинаем разрядку
            elif u < U_DISCHARGED and not charging:
                break

        # сохраняем данные для LibreOffice
        with open("data.txt", "w") as f:
            f.write("t;U\n")
            for t, u in zip(time_values, voltage_values):
                f.write(f"{t:.4f};{u:.4f}\n")
        print("Момент переключения на разрядку, с:", t_switch)

        adc_plot.plot_voltage_vs_time(time_values, voltage_values, adc.dynamic_range)
    finally:
        adc.deinit()
        GPIO.cleanup()