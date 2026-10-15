import matplotlib.pyplot as plt

def plot_voltage_vs_time(time, voltage):
    plt.figure(figsize=(10, 6))
    plt.plot(time, voltage)

    plt.title("График зависимости напряжения на входе АЦП от времени")
    plt.xlabel("Время, с")
    plt.ylabel("Напряжение В")

    plt.xlim(0, max(time) if time else 1)
    plt.ylim(0, 3.5)

    plt.grid(True)
    plt.show
def plot_sampling_period_hist(time):
    sampling_periods = [time[i] - time[i-1] for i in range(1, len(time))]
    plt.figure(figsize=(10, 6))
    plt.hist(sampling_periods)

    plt.title("Распределение периодов дискретизации измерений\ по времени на одно измерение")
    plt.xlabel("Время, с")
    plt.ylabel("Количество измерений")

    plt.xlim(0, 0.06)
    plt.grid(True)
    plt.show