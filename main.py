import click
import requests
from datetime import timedelta
import pandas as pd

STOPS = {
    "Rennes": "87471003",
}


@click.command()
@click.option('--token')
@click.option('--date', type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option('--ville')
def run(token, date, ville):
    start_date = date.strftime("%Y%m%dT%H%M%S")
    end_date = (date + timedelta(days=1)).strftime("%Y%m%dT%H%M%S")
    url = f"https://api.navitia.io/v1/coverage/sncf/stop_areas/stop_area%3ASNCF%3A{STOPS[ville]}/physical_modes/physical_mode%3ALongDistanceTrain/arrivals?from_datetime={start_date}&until_datetime={end_date}&count=1000&"

    response = requests.get(url, headers={"Authorization": token})
    data = response.json()
    df = pd.DataFrame(data["arrivals"])

    output = []
    for col in df[["display_informations", "stop_date_time"]].columns:
        output.append(pd.json_normalize(df[col]))
    trains = pd.concat(output, axis=1)

    trains["arrival_date_time"] = pd.to_datetime(trains["arrival_date_time"])
    trains["base_arrival_date_time"] = pd.to_datetime(trains["base_arrival_date_time"])
    trains["delay"] = trains["arrival_date_time"] - trains["base_arrival_date_time"]
    trains["is_delayed"] = trains["delay"].astype(int) != 0

    trains.to_csv(f"{date.strftime('%Y-%m-%d')}_{ville}.csv", index=False)


if __name__ == '__main__':
    run()
