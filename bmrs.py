from typing import List

import httplib2

import pandas as pd

from datetime import datetime, date, timedelta
from pathlib import Path

from constants import T_s

version = "V1"
APIKey = "fqfqec6ypagbtoi"
headers = {
    "ROLSYSDEM": ["RecordType", "Timestamp", "Demand"],
    "FUELINST": ["RecordType", "Date", "SP", "Timestamp",
                 "CCGT", "Oil", "Coal", "Nuclear", "WindPower", "PS", "Hydro", "OCGT", "Other",
                 "Int-FR", "Int-IRL", "Int-NED", "Int-EW", "Biomass",
                 "Int-NEM", "Int-ELEC", "Int-IFA2", "Int-NSL"]
}

bmrs_date_format = "%Y-%m-%d %H:%M:%S"
file_date_format = "%Y-%m-%d-%H-%M-%S"

def download_data(path: Path, service, from_date_time: datetime, to_date_time: datetime):
    """Download datafile in given datetime range for service specified."""

    url = f'https://api.bmreports.com/BMRS'
    url += f'/{service}/{version}?APIKey={APIKey}'
    url += f'&FromDateTime={from_date_time.strftime(bmrs_date_format).replace(" ", "%20")}'
    url += f'&ToDateTime={to_date_time.strftime(bmrs_date_format).replace(" ", "%20")}'
    url += f'&ServiceType=csv'
    http_obj = httplib2.Http()
    response, content = http_obj.request(
        uri=url,
        method='GET',
        headers={'Content-Type': 'application/csv; charset=UTF-8'},
    )

    filename = f'{from_date_time.strftime(file_date_format)}'
    filename += f'_{to_date_time.strftime(file_date_format)}'
    filename += f'.csv'
    filepath = path / f'{service}' / filename
    f = filepath.open("wb")
    f.write(content)
    f.close()

    print(f"{from_date_time} - > {to_date_time}: response: {response['status']}")
    return filename

def download_dataset(path: Path, services: List[str], start_date: date, end_date: date) -> List[str]:
    """Download all datafiles in given date range for services specified:
        from_date = date(2019,1,1)
        to_date = date(2020,1,1)
        p = download_dataset(Path("./data"), ["FUELINST"], from_date, to_date)
    """

    file_names = []
    for count in range((end_date-start_date).days):
        from_date = start_date + timedelta(days=count)
        to_date = start_date + timedelta(days=count + 1)
        from_date_time = datetime(year=from_date.year, month=from_date.month, day=from_date.day)
        to_date_time = datetime(year=to_date.year, month=to_date.month, day=to_date.day)

        for service in services:
            file_names.append(download_data(path, service, from_date_time, to_date_time))

    return file_names


def read_generation_file(file_path: Path) -> pd.Series:
    df = pd.read_csv(file_path, header=0, names=headers["FUELINST"], index_col=False)
    df.dropna(inplace=True)
    df.Timestamp = df.Timestamp.astype(int)
    df['Time'] = df.apply(lambda x: pd.to_datetime(x.Timestamp, format='%Y%m%d%H%M%S', errors='ignore'), axis=1)

    # Convert power from MW to GW
    df['WindPower'] /= 1000
    df.set_index('Time', inplace=True)
    return df['WindPower']


def read_generation_files(path: Path) -> pd.Series:
    dss = []
    for file in path.glob('*.csv'):
         dss.append(read_generation_file(file))
    ds = pd.concat(dss)
    # there are duplicate lines, so
    ds.sort_index(inplace=True)
    ds = ds.groupby(ds.index)
    ds = ds.agg('max')
    # and there are holes
    sample_string = str(T_s) + 'S'
    return ds.resample(sample_string).mean().interpolate(method='linear')
