import click


@click.command()
@click.option('--token')
@click.option('--date')
@click.option('--ville')
def run(token, date, ville):
    print(token, date, ville)


if __name__ == '__main__':
    run()
