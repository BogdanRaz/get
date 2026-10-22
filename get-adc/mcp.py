import mcp3021_driver as mcp
import adc_plot as plott
import time

max_voltage = 5.227

adc = mcp.MCP3021(max_voltage)
voltages = []
times = []
duration = 15.0

try:
    time_start = time.time()
    while time.time() - time_start < duration:
        v = adc.get_voltage()
        t = time.time()
        times += [t]
        voltages += [v]
    plott.plot_voltage_vs_time(times, voltages, max_voltage)
    plott.plot_sampling_period_hist(times)
finally:
    adc.deinit()