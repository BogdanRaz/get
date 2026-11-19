# bloodProcessing.py - калибровка, давление и пульс по записям АЦП.
#   python3 bloodProcessing.py [папка_с_данными]
# Данные: "40 mmHg.txt" ... "160 mmHg.txt", rest.txt, fitness.txt
# Выход: plots/*.png и results.json (их использует build_report.py)
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

dataPath = sys.argv[1] if len(sys.argv) > 1 else "data"
plotPath = "plots"
os.makedirs(plotPath, exist_ok=True)

PRESSURES = [40, 80, 120, 160]
PULSE_FROM, PULSE_TO = 10, 30       # участок для подсчёта пульса, с
SKIP = 2.5                         # начало записи, которое не анализируем, с
DIA_LEVEL = 0.8                     # диастола: амплитуда ниже 0.8 от наибольшей


def read(filename):
    with open(filename) as f:
        lines = f.readlines()
    duration = float(lines[2].split()[2])
    samples = np.asarray(lines[4:], dtype=int)
    return samples, duration, len(samples)


def calibration():
    means = []
    for pr in PRESSURES:
        samples, _, _ = read(os.path.join(dataPath, "%d mmHg.txt" % pr))
        means.append(samples.mean())
    means = np.array(means)
    fit, cov = np.polyfit(means, PRESSURES, 1, cov=True)
    err = np.sqrt(np.diag(cov))
    dev = np.array(PRESSURES) - np.polyval(fit, means)

    plt.figure(figsize=(7, 4.5))
    plt.plot(means, PRESSURES, "o", label="измерения")
    xs = np.array([means.min() - 10, means.max() + 10])
    plt.plot(xs, np.polyval(fit, xs),
             label="P = %.4f·N %+.2f мм рт. ст." % (fit[0], fit[1]))
    plt.xlabel("Отсчёт АЦП N")
    plt.ylabel("Давление P, мм рт. ст.")
    plt.grid(alpha=.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plotPath, "pressure-calibration.png"), dpi=150)
    plt.close()
    return fit, dict(k=fit[0], b=fit[1], dk=err[0], db=err[1],
                     maxdev=float(np.abs(dev).max()),
                     points=[dict(p=pr, n=round(float(m), 1)) for pr, m in zip(PRESSURES, means)])


def moving(x, window):
    return np.convolve(x, np.ones(window) / window, mode="same")


def process(name, fit, label):
    samples, duration, count = read(os.path.join(dataPath, name + ".txt"))
    p = np.polyval(fit, samples)
    time = np.linspace(0, duration, count)
    rate = count / duration

    p = moving(p, int(rate * 0.05))                # шум квантования, 50 мс
    trend = moving(p, int(rate * 1.5))             # медленный тренд, 1.5 с
    osc = p - trend                                # пульсации

    # --- пульс на участке 10-30 с
    peaks, _ = find_peaks(osc, distance=0.4 * rate, prominence=0.3)
    inside = peaks[(time[peaks] > PULSE_FROM) & (time[peaks] < PULSE_TO)]
    pulse = (len(inside) - 1) * 60 / (time[inside[-1]] - time[inside[0]])

    # --- амплитуда каждой волны: вершина минус предыдущая впадина
    troughs, _ = find_peaks(-osc, distance=0.4 * rate, prominence=0.3)
    amp, tAmp = [], []
    for a, c in zip(troughs[:-1], troughs[1:]):
        top = a + np.argmax(osc[a:c])
        amp.append(osc[top] - osc[a])
        tAmp.append(time[top])
    amp, tAmp = np.array(amp), np.array(tAmp)

    # участок спуска: от начала спуска (максимум давления) до 40 мм рт. ст.
    # первые SKIP с отбрасываем: открытие клапана и искажённые края скользящих средних
    start = max(time[np.argmax(p)], SKIP)
    end = time[np.where(p > 40)[0][-1]]
    sel = (tAmp >= start) & (tAmp <= end)
    amp, tAmp = amp[sel], tAmp[sel]

    # сглаженная амплитуда: медиана по семи соседним волнам, выбросы
    # (в 1.5 раза выше медианы) заменяются медианой
    med = np.array([np.median(amp[max(0, i - 3):i + 4]) for i in range(len(amp))])
    clean = np.where(amp > 1.5 * med, med, amp)
    smooth = np.array([np.median(clean[max(0, i - 3):i + 4]) for i in range(len(clean))])

    # --- систола: 5-я волна после появления волн (начала спуска)
    iSys = 4
    tSys = tAmp[iSys]
    pSys = float(np.interp(tSys, time, p))
    # --- диастола: после максимума первая волна ниже 0.8 от наибольшей
    iMax = int(np.argmax(smooth))
    below = np.where(smooth[iMax:] < DIA_LEVEL * smooth[iMax])[0]
    iDia = iMax + int(below[0])
    tDia = tAmp[iDia]
    pDia = float(np.interp(tDia, time, p))

    # --- графики
    plt.figure(figsize=(8, 4.5))
    plt.plot(time, p, lw=.9)
    plt.plot([tSys, tDia], [pSys, pDia], "r*", ms=12,
             label="давление %.0f/%.0f мм рт. ст." % (pSys, pDia))
    plt.text(tSys + 1, pSys + 4, "Систола")
    plt.text(tDia + 1, pDia + 4, "Диастола")
    plt.xlabel("Время t, с")
    plt.ylabel("Давление P, мм рт. ст.")
    plt.title("Давление в манжете, %s" % label)
    plt.grid(alpha=.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plotPath, name + "-pressure.png"), dpi=150)
    plt.close()

    plt.figure(figsize=(8, 4.5))
    plt.plot(time, osc, lw=.9)
    plt.plot(time[peaks], osc[peaks], "r.", label="пики (удары сердца)")
    plt.xlim(PULSE_FROM, PULSE_TO)
    win = (time >= PULSE_FROM) & (time <= PULSE_TO)
    plt.ylim(osc[win].min() * 1.15, osc[win].max() * 1.15)
    plt.xlabel("Время t, с")
    plt.ylabel("Пульсации, мм рт. ст.")
    plt.title("Пульс %.0f уд/мин, %s" % (pulse, label))
    plt.grid(alpha=.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plotPath, name + "-pulse.png"), dpi=150)
    plt.close()

    plt.figure(figsize=(8, 4.5))
    plt.plot(tAmp, amp, ".", color="lightskyblue", label="амплитуда волны")
    plt.plot(tAmp, smooth, "b-", label="сглаженная (медиана по 7)")
    plt.plot(tAmp[:5], amp[:5], "ro", mfc="none", ms=9, label="первые пять волн")
    plt.axhline(DIA_LEVEL * smooth[iMax], color="g", ls="--",
                label="%.1f от наибольшей" % DIA_LEVEL)
    plt.axvline(tSys, color="r", alpha=.4)
    plt.axvline(tDia, color="g", alpha=.4)
    plt.xlabel("Время t, с")
    plt.ylabel("Амплитуда, мм рт. ст.")
    plt.title("Амплитуда волн, %s" % label)
    plt.grid(alpha=.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(plotPath, name + "-amplitude.png"), dpi=150)
    plt.close()

    slope = (p[int(rate * 2)] - p[int(rate * 30)]) / 28
    return dict(pulse=round(float(pulse)), sys=round(pSys), dia=round(pDia),
                tSys=round(float(tSys), 1), tDia=round(float(tDia), 1),
                nPeaks=int(len(inside)), pMax=round(float(p.max())),
                slope=round(float(slope), 1), rate=round(float(rate)),
                duration=duration, count=int(count))


if __name__ == "__main__":
    fit, cal = calibration()
    result = dict(calibration=cal,
                  rest=process("rest", fit, "покой"),
                  fitness=process("fitness", fit, "после нагрузки"))
    json.dump(result, open("results.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("k = %.4f, b = %.2f" % (fit[0], fit[1]))
    for n in ("rest", "fitness"):
        r = result[n]
        print("%-8s пульс %d уд/мин, давление %d/%d мм рт. ст. (систола %.1f с, диастола %.1f с)"
              % (n + ":", r["pulse"], r["sys"], r["dia"], r["tSys"], r["tDia"]))
