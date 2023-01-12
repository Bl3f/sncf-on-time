import json
import os
import click
import requests
from datetime import timedelta, date
import pandas as pd
from google.oauth2 import service_account
import base64
import time

STOPS = {
    "Rennes": "87471003",
    "Paris Gare de Lyon Hall 1 &2 (Paris)": "87686006",
    "Paris Est (Paris)": "87113001",
    "Paris Gare du Nord (Paris)": "87271007",
    "Paris Austerlitz (Paris)": "87547000",
    "Paris Saint-Lazare (Paris)": "87384008",
    "Paris Montparnasse Hall 1 &2 (Paris)": "87391003",
    "Marseille Saint-Charles (Marseille)": "87751008",
    "Lyon Perrache (Lyon)": "87722025",
    "Lyon Part Dieu (Lyon)": "87723197",
    "Toulouse Matabiau (Toulouse)": "87611004",
    "Nice-Ville (Nice)": "87756056",
    "Nantes (Nantes)": "87481002",
    "Montpellier Saint-Roch (Montpellier)": "87773002",
    "Montpellier Sud de France (Montpellier)": "87688887",
    "Strasbourg (Strasbourg)": "87212027",
    "Bordeaux Saint-Jean (Bordeaux)": "87581009",
    "Lille Europe (Lille)": "87223263",
}


def get_data(token, start_date, end_date, ville):
    url = f"https://api.navitia.io/v1/coverage/sncf/stop_areas/stop_area%3ASNCF%3A{STOPS[ville]}/physical_modes/physical_mode%3ALongDistanceTrain/arrivals?from_datetime={start_date}&until_datetime={end_date}&count=1000&"

    response = requests.get(url, headers={"Authorization": token})
    data = response.json()
    arrivals = pd.DataFrame(data["arrivals"])
    disruptions = pd.DataFrame(data["disruptions"])

    return arrivals, disruptions


def get_and_prepare_data(token, start_date, end_date, ville):
    disruptions_json_columns = ["severity", "application_periods", "messages", "impacted_objects"]

    arrivals, disruptions = get_data(token, start_date, end_date, ville)
    arrivals = arrivals.applymap(json.dumps)
    if not disruptions.empty:
        disruptions[disruptions_json_columns] = disruptions[disruptions_json_columns].applymap(json.dumps)
    arrivals['gare_label'] = ville
    arrivals['run_date'] = start_date

    return arrivals, disruptions


@click.command()
@click.argument('token')
@click.option('--ville', default='all')
@click.option('--input-date', type=click.DateTime(formats=["%Y-%m-%d"]), default=str(date.today() - timedelta(days=1)))
def run(token, ville, input_date):
    start_date = input_date.strftime("%Y%m%dT%H%M%S")
    end_date = (input_date + timedelta(days=1)).strftime("%Y%m%dT%H%M%S")

    arrivals_output = []
    disruptions_output = []
    for label in (STOPS if ville == 'all' else [ville]):
        print(f"Requesting {label}")
        arrivals, disruptions = get_and_prepare_data(token, start_date, end_date, label)
        arrivals_output.append(arrivals)
        disruptions_output.append(disruptions)
        time.sleep(1)

    service_account_info = base64.b64decode(os.getenv("SERVICE_ACCOUNT_INFO"))
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(service_account_info)
    )

    arrivals = pd.concat(arrivals_output)
    arrivals.to_gbq(
        'raw.arrivals',
        project_id='ensai-2023-373710',
        location='eu',
        credentials=credentials,
        if_exists='append',
    )

    disruptions = pd.concat(disruptions_output)
    disruptions.to_gbq(
        'raw.disruptions',
        project_id='ensai-2023-373710',
        location='eu',
        credentials=credentials,
        if_exists='append',
    )


if __name__ == '__main__':
    run()
