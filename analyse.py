#!/usr/bin/env python


# 1st-party
import sys
import time
import urlparse

# 3rd-party
from bs4 import BeautifulSoup
import requests


BASE_URI = 'https://crash-stats.mozilla.com'
REPORT_URI = BASE_URI + '/report/index/'
MORE_REPORTS_URI = BASE_URI + '/report/list/partials/reports/'


def get_tree(url):
    return BeautifulSoup(requests.get(url).text)


def get_extensions(tree):
    extensions = {}
    extensions_list = tree.select('#extensions')[0].find('tbody')

    if extensions_list:
        extensions_list = extensions_list.find_all('tr')

        for extension in extensions_list:
            columns = extension.find_all('td')
            name, version = columns[1].text, columns[2].text
            extensions[name] = extensions.get(name, set()) | set([version])

    return extensions



def walk_crash_report(report_id):
    extensions = {}

    this_report_url = REPORT_URI + report_id
    this_report_tree = get_tree(this_report_url)
    # Sleep for some time until a possibly new report is generated.
    time.sleep(45)
    this_report_tree = get_tree(this_report_url)

    # TODO: better error reporting when report_id is invalid
    product_signature_url = \
        this_report_tree.select('a.sig-overview')[0]['href']
    product_signature_query = urlparse.urlparse(product_signature_url).query

    # TODO: there may be hundreds of reports!
    more_reports_url = MORE_REPORTS_URI + '?' + product_signature_query
    more_reports_tree = get_tree(more_reports_url)
    more_reports_list = more_reports_tree.select('#reportsList')[0].\
                        find('tbody').select('tr')
    more_reports_counter = 0
    skipped_reports_counter = 0

    for that_report in more_reports_list:
        more_reports_counter += 1

        try:
            columns = that_report.select('td')
            date_processed, duplicate_of, product, version, build, \
            os_and_version, cpu_name, reason, address, uptime, install_time, \
            user_comments = [ column.text.strip() for column in columns ]

            that_report_url = BASE_URI + columns[0].find('a')['href']
            that_report_tree = get_tree(that_report_url)
            that_report_extensions = get_extensions(that_report_tree)
        except:
            skipped_reports_counter += 1
            print('Skipping report #{}'.format(more_reports_counter))
        else:
            for name, versions in that_report_extensions.items():
                extensions[name] = extensions.get(name, []) + list(versions)

    processed_reports_counter = more_reports_counter - skipped_reports_counter
    extensions_in_all_reports = {}

    for name, versions in extensions.items():
        # >=, not ==, because there are extensions with the same name, but
        # different versions, on the same computer 
        if len(versions) >= processed_reports_counter:
            extensions_in_all_reports[name] = set(versions)

    print('Extensions in all reports with the same signature ({}): {}'.\
          format(more_reports_url, extensions_in_all_reports))
    print('')


def main(report_ids_filepath):
    with open(report_ids_filepath) as report_ids_file:
        for report_id in report_ids_file:
            walk_crash_report(report_id)


if __name__ == '__main__':
    assert len(sys.argv) == 2
    report_ids_filepath = sys.argv[1]
    main(report_ids_filepath)


