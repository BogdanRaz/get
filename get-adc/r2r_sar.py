import r2r_adc as r2r
import adc_plot as plott
import time

max_voltage = 3.183

adc = r2r.R2R_ADC(max_voltage, compare_time=0.0001)
voltages = []
times = []
duration = 3.0

try:
    time_start = time.time()
    while time.time() - time_start < duration:
        v = adc.get_sar_voltage()
        t = time.time()
        times += [t]
        voltages += [v]
    plott.plot_voltage_vs_time(times, voltages, max_voltage)
    plott.plot_sampling_period_hist(times)
finally:
    adc.deinit()