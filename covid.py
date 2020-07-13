#!/usr/bin/env python

"""Download and plot confirmed Covid-19 cases from UK government data."""

import subprocess as sp
import os
import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

URL = "https://c19downloads.azureedge.net/downloads/csv/"
FNAME = "coronavirus-cases_latest.csv"

# Settings for x-axis ticks.
BIWEEKLY_LOCATOR = mdates.WeekdayLocator(byweekday=mdates.MO, interval=2)
BIDAILY_LOCATOR = mdates.DayLocator(interval=2)
DATE_FORMATTER = mdates.DateFormatter('%b%d')

FIG_SIZE = (10, 6)


def csv_time():
    """
    Return modification time of local copy of data file as datetime.  Since
    this was downloaded by wget, this will be the time the file was last
    updated online before the download.
    """
    lastmodified = os.stat(FNAME).st_mtime
    return datetime.datetime.fromtimestamp(lastmodified)


def update_csv():
    """
    If local copy of data file is more than a day old, download it again from
    government website.
    """
    modified_datetime = csv_time()
    current_datetime = datetime.datetime.now()
    if (current_datetime - modified_datetime).days > 0:
        fname = URL + FNAME
        os.remove(FNAME)
        command = "wget {}".format(fname)
        sp.call(command, shell=True)


def get_values(location):
    """
    Read data for given location from CSV file.

    RETURNS

    dates:      list of datetime
                Validity dates.

    num_cases:  list of int
                Number of confirmed cases for this location.

    kind:       str
                'Nation', 'Region', 'Upper Tier Local Authority' or
                'Lower Tier Local Authority'.
    """
    date_strings = []
    num_cases = []
    with open(FNAME) as fp:
        for line in fp:
            parts = line.split(',')
            if parts[0].strip() == location and parts[3] not in date_strings:
                date_strings.append(parts[3])
                num_cases.append(int(parts[4]))
                kind = parts[2]

    dates = [datetime.datetime.strptime(dt, '%Y-%m-%d') for dt in date_strings]

    return dates, num_cases, kind


def kind_label(kind):
    """
    Shorten 'Local Authority' strings to acronyms for use in plot labels.
    """
    words = kind.split()
    if len(words) > 1:
        return ''.join(word[0] for word in words).upper()
    return kind


def format_axes():
    """
    Update current axes with gridlines, ticklabels, etc.
    """
    plt.grid(axis='y', linestyle='--')
    xaxis = plt.gca().get_xaxis()
    xaxis.set_major_locator(BIWEEKLY_LOCATOR)
    xaxis.set_major_formatter(DATE_FORMATTER)
    xaxis.set_minor_locator(BIDAILY_LOCATOR)


def add_5day_box():
    """
    Government about the data page suggests that data more than 5 days old may
    be considered complete.  This function adds shading to the most recent 5
    days to indicate possible incompleteness.
    https://coronavirus.data.gov.uk/about#cases-over-time
    """
    data_file_datetime = csv_time()
    end_valid_datetime = data_file_datetime - datetime.timedelta(days=1)

    # Bars are all centred on midnight, so use noon to fit shading around them.
    end_valid_datetime.replace(hour=12, minute=0)
    start_valid_datetime = end_valid_datetime - datetime.timedelta(days=5)
    plt.axvspan(start_valid_datetime, end_valid_datetime, color='lavender',
                zorder=-10)


def plot_values(location):
    """
    Make a bar chart of confirmed cases by date for the given location.
    """
    dates, num_cases, kind = get_values(location)
    plt.bar(dates, num_cases)
    plt.title('Confirmed Cases in {} {}'.format(location, kind_label(kind)))
    format_axes()
    add_5day_box()


def plot_devon():
    """
    Devon Upper Tier Local Authority does not include Plymouth or Torbay, so
    add these as a stacked bar chart.  Exeter is included in Devon UTLA but is
    useful to see separately, so overplot this.
    """
    locations = ['Exeter', 'Devon', 'Torbay', 'Plymouth']
    colors = ['tab:red', 'tab:gray', 'tab:blue', 'tab:orange']
    location_values = dict()
    for loc in locations:
        location_values[loc] = get_values(loc)

    # Make sure all locations include all available dates in chronological
    # order, otherwise bar stacking fails.
    all_dates = np.unique(np.concatenate(
        [values[0] for values in location_values.values()]))

    for loc in locations:
        dates, num_cases, _ = location_values[loc]
        for date in all_dates:
            if date not in dates:
                dates.append(date)
                num_cases.append(0)

        _, sorted_num_cases = zip(*sorted(zip(dates, num_cases)))
        location_values[loc] = np.array(sorted_num_cases)

    # Plot data.
    bottom = 0
    for location, color, zorder in zip(locations, colors, range(4)[::-1]):
        if location == 'Devon':
            label = 'Devon UTLA'
        else:
            label = location
        num_cases = location_values.get(location)
        plt.bar(all_dates, num_cases, bottom=bottom, label=label,
                color=color, zorder=zorder)

        if location != 'Exeter':
            bottom = num_cases + bottom

    format_axes()
    plt.legend()
    plt.title('Confirmed Cases in Devon')
    add_5day_box()


def save_fig(location):
    """
    Save the current figure to file, using location in the filename.
    """
    plt.tight_layout()
    loc_str = location.lower().replace(' ', '_')
    plt.savefig('covid_cases_{}.png'.format(loc_str))
    plt.close()


def main(save=False):
    """
    Make bar charts of confirmed cases.

    INPUT

    save:  bool
           If True, saves each figure to a png file, otherwise displays all
           figures in matplotlib gui.
    """
    update_csv()
    for loc in ['South West', 'West Berkshire', 'Leicester', 'Essex',
                'Basildon']:
        plt.figure(figsize=FIG_SIZE)
        plot_values(loc)
        if save:
            save_fig(loc)

    plt.figure(figsize=FIG_SIZE)
    plot_devon()
    if save:
        save_fig('Devon Totals')
    else:
        plt.show()


if __name__ == '__main__':
    main(True)
