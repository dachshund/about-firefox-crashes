#!/usr/bin/env python


# 1st-party
import urlparse

# 3rd-party
from bs4 import BeautifulSoup
import requests

BASE_URI = 'https://crash-stats.mozilla.com'
REPORT_URI = BASE_URI + '/report/index/'
MORE_REPORTS_URI = BASE_URI + '/report/list/partials/reports/'

REPORT_IDS = (
    # "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:29.0) Gecko/20100101 Firefox/29.0"
    'bp-b4a4631b-92dd-4c4b-945c-8c6a32140528',
    'bp-f69284d0-288a-4eba-8cb3-f06e12140527',
    'bp-30e11dc2-cbe3-4d2a-98e7-720182140523',
    'bp-71ee645e-e5b6-4fab-8caa-1a6052140521'
)

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
    extensions_in_all_reports = None

    this_report_tree = get_tree(REPORT_URI + report_id)
    product_signature_url = \
        this_report_tree.select('a.sig-overview')[0]['href']
    product_signature_query = urlparse.urlparse(product_signature_url).query

    # TODO: there may be hundreds of reports!
    more_reports_url = MORE_REPORTS_URI + '?' + product_signature_query
    more_reports_tree = get_tree(more_reports_url)
    more_reports_list = more_reports_tree.select('#reportsList')[0].\
                        find('tbody').select('tr')

    for that_report in more_reports_list:
        columns = that_report.select('td')
        date_processed, duplicate_of, product, version, build, \
        os_and_version, cpu_name, reason, address, uptime, install_time, \
        user_comments = [ column.text.strip() for column in columns ]

        that_report_url = BASE_URI + columns[0].find('a')['href']
        that_report_tree = get_tree(that_report_url)
        that_report_extensions = get_extensions(that_report_tree)
        that_report_extension_names = set(that_report_extensions.keys())

        if extensions_in_all_reports is None:
            extensions_in_all_reports = that_report_extension_names
        else:
            extensions_in_all_reports &= that_report_extension_names

    print('Extensions in all reports with the same signature ({}): {}'.\
          format(product_signature_query, extensions_in_all_reports))


def main():
    for report_id in REPORT_IDS:
        walk_crash_report(report_id)


if __name__ == '__main__':
    main()


