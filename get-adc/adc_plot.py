import matplotlib.pyplot as plt

def plot_voltage_vs_time(time, voltage, max_voltage):
    plt.figure(figsize=(10, 6))

    plt.plot(time, voltage)

    plt.title("График зависимости напряжения на входе АЦП от времени")
    plt.xlabel("Время, с")
    plt.ylabel("Напряжение, В")
    
    plt.axis([min(time), max(time), 0, max_voltage])

    plt.minorticks_on()
    plt.grid(visible=True, which='major')
    plt.grid(visible=True, which='minor')

    plt.show()


def plot_sampling_period_hist(time):
    sampling_periods = [time[i + 1] - time[i] for i in range(len(time) - 1)]

    plt.figure(figsize=(10,6))

    plt.hist(sampling_periods)

    plt.title("Распределение периодов дискретизации измерений по времени на одно измерение")
    plt.xlabel("Период измерения, с")
    plt.ylabel("Количество измерений")

    plt.xlim(0, 0.06)

    plt.minorticks_on()
    
    plt.grid(visible=True, which='major')
    plt.grid(visible=True, which='minor')

    plt.show()