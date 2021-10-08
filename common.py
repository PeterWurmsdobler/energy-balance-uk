from dataclasses import dataclass
import numpy as np
from scipy.fft import rfft
from scipy.signal.windows import hamming
from scipy.signal import find_peaks

from constants import T_s

@dataclass(frozen=True)
class PowerStatistics:
    average_power: float
    total_energy: float
    frequencies: np.ndarray
    spectrum: np.ndarray
    peak_indices: np.ndarray
    peak_values: np.ndarray

    def print(self) -> None:
        print(f"\tAverage power = {self.average_power:.3f}GW")
        print(f"\tAnnual energy = {(self.total_energy / 3600 / 1000):.3f}TWh")
        for index, value in zip(self.peak_indices, self.peak_values):
            print(f"\tAmplitude @ bin {index} = {value:.3f}GW")


def analyse_power(power: np.ndarray) -> PowerStatistics:
    average_power = np.mean(power)
    total_energy = np.sum(power)*T_s
    fft_length = len(power)
    fft_window = hamming(fft_length)
    fft_gain = sum(fft_window)/fft_length
    frequencies = np.fft.rfftfreq(fft_length, T_s)
    spectrum = abs(2*rfft(fft_window*(power-average_power)/fft_gain)/fft_length)
    spectrum[0] *= 0.5

    median = np.median(spectrum)
    std = np.std(spectrum)
    threshold = median + 10 * std
    peak_indices, properties = find_peaks(spectrum, height=threshold)

    return PowerStatistics(
        average_power,
        total_energy,
        frequencies,
        spectrum,
        peak_indices,
        properties["peak_heights"]
    )

def remove_outliers(data: np.ndarray) -> np.ndarray:
    median = np.median(data)
    std = np.std(data)
    outliers = np.abs(data - median) > 10*std
    data[outliers] = np.nan
    return data