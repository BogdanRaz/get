import time
from r2r_adc import R2R_ADC
from adc_plot import plot_voltage_vs_time

if __name__ == "__main__":
    DYNAMIC_RANGE = 3.3
    adc = R2R_ADC(dynamic_range=DYNAMIC_RANGE, compare_time=0.0001, verbose=False)
    voltage_values = []
    time_values = []
    duration = 3.0

    try:
        start_time = time.time()
        while (time.time() - start_time) < duration:
            voltage_values.append(adc.get_sc_voltage())
            time_values.append(time.time() - start_time)

        plot_voltage_vs_time(time_values, voltage_values)
        plot_sampling_period_hist(time_values)

    finally:
        adc.__del__()
