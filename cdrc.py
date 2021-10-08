from datetime import datetime
import numpy as np
from csv import reader

from constants import T_s

def load_domestic_data(filepath: str) -> None:
    """Load CDRC data, aggregate over post code areas and meters, then save to file."""

    # path = 'data/cdrc/DomesticEnergyProviderDataset/DEP2015_SF_CDRC.csv'

    num_meters = 0
    natural_gas_consumption = np.zeros([365,48])
    electricity_consumption = np.zeros([365,48])

    # open file in read mode
    with open(filepath, 'r') as source:
        # pass the file object to reader() to get the reader object
        csv_reader = reader(source)
        # Iterate over each row in the csv using reader object
        header = next(csv_reader)
        # Check file as empty
        if header != None:
            # Iterate over each row after the header in the csv
            for row in csv_reader:
                # row variable is a list that represents a row in csv

                # dataset contains 31st September
                if row[1] == "20150931":
                    continue

                date = datetime.strptime(row[1], "%Y%m%d")
                data = row[5:]
                if not "NA" in data:
                    pc = row[2]
                    t = row[3]
                    num_meters += int(row[4])
                    day = int(date.timetuple().tm_yday)
                    print(f"{date} = {day}: {t}, pc = {pc}")
                    x = np.array(data)
                    y = x.astype(np.float)
                    z = np.nan_to_num(y)
                    if (t == 'G'):
                        natural_gas_consumption[day-1,:] += z
                    if (t == 'E'):
                        electricity_consumption[day-1,:] += z

        natural_gas_energy = natural_gas_consumption.ravel()
        electricity_energy = electricity_consumption.ravel()

        # energy is measured every T_s in kWh, convert to power in GW:
        kWh_p_sample_to_P_GW = 3600 * 1000 / T_s / 1E9
        natural_gas_power = natural_gas_energy * kWh_p_sample_to_P_GW
        electricity_power = electricity_energy * kWh_p_sample_to_P_GW

        print(f"Total number of meters: {num_meters/365}")
        print(f"Total natural gas energy: {np.sum(natural_gas_energy)/1E9} TWh")
        print(f"Total electricity energy: {np.sum(electricity_energy)/1E9} TWh")

        basename = filepath[:-3]
        with open(basename + 'natural_gas.npy', 'wb') as f:
            np.save(f, natural_gas_power)
        with open(basename + 'electricity.npy', 'wb') as f:
            np.save(f, electricity_power)

