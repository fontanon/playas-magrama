#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ts=4
###
#
# Copyright (c) 2013 J. Félix Ontañón
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors : J. Félix Ontañón <felixonta@gmail.com>
#
###

import mechanize
from bs4 import BeautifulSoup
import simplejson

BASE_URL_TEMPLATE = 'http://aplicaciones2.magrama.es/dinamicas/guia_playas_busc/?playa=&municipio=&provincia=Todas&comunidad={CM_CODE}&bonita={CM_NAME}%2F%28Comunidad%29&pregunta={CM_CODE}&gf%5Et9100={CM_NAME}%2F%28Comunidad%29&bf%5Et9998=playa&hf%5Et9999=web3&h1%5Et3001=1&h2%5Et3002=25&id%5Et8000=4'

DEFAULT_RESULTS_PER_PAGE = 25

INFO_TABLE_SUMMARY= 'nombre y localización de la playa'
CHAR_TABLE_SUMMARY= u'tabla que muestra características de la playa'

regions = [["CM%3DANDALUCIA", "Andalucia"]]
"""
["CM%3DASTURIAS", "Asturias"],
["CM%3DCANTABRIA", "Cantabria"],
["CM%3DCATALUNA", "Catalu&ntilde;a"],
["CM%3DCEUTA", "Ceuta"],
["CM%3DCOMUNIDAD VALENCIANA", "Com. Valenciana"],
["CM%3DGALICIA", "Galicia"],
["CM%3DISLAS CANARIAS", "Islas Canarias"],
["CM%3DISLAS BALEARES", "Islas Baleares"],
["CM%3DMELILLA", "Melilla"],
["CM%3DREGION DE MURCIA", "Murcia"],
["CM%3DPAIS VASCO", "Pais Vasco"]
]
"""

BEACH_CHAR_CLASS = ['fondoplayas2','fondoplayas1']

class Beach(dict):
    def __init__(self, name='', town='', province='', region='', description ='', characteristics={}):
        dict.__init__(self)
        self['name'] = name
        self['town'] = town
        self['province'] = province
        self['region'] = region
        self['description'] = description
        self['characteristics'] = characteristics

    def toJSON(self):
        return simplejson.dumps(self, ensure_ascii=False)

def process_beach_page(soup):   
    html_content = br.response().read()
    soup = BeautifulSoup(html_content)

    info_table = soup.table.find(summary=INFO_TABLE_SUMMARY)
    beach = Beach(*[x for x in info_table.stripped_strings][:-1])

    char_table = soup.table.find(summary=CHAR_TABLE_SUMMARY)
    char_strings = [x for x in char_table.findAll('tr') if x.text!=u'\n\xa0\n']

    beach['description'] = char_strings.pop(0).text.strip()
    key = char_strings.pop(0).text.strip()
    char = dict({key:{}})

    while len(char_strings):
        item = char_strings.pop(0)
        if item.has_key("class") and item['class'][0] in BEACH_CHAR_CLASS:
            if ': ' in item.text:
                stripped = item.text.strip().split(': ', 1)
                if len(stripped) == 1: stripped.append('')
                char[key].update(dict([tuple(stripped)]))
            else:
                text = item.text.strip()
                char[key].update({text:text})
        else:
            key = item.text.strip()
            char[key] = {}

    beach["characteristics"] = char
    return beach

def process_result_page(browser, page_results):
    beaches_data = []

    form_index = 0
    while form_index < page_results:
        br.select_form(nr=form_index)
        if browser.form.method == 'POST':
            browser.submit()
            beaches_data.append(process_beach_page(browser))
            browser.back()
        form_index += 1

    return beaches_data

if __name__ == '__main__':
    br = mechanize.Browser()

    beaches_data = []

    for region in regions:
        region_url = BASE_URL_TEMPLATE.replace('{CM_CODE}', region[0])
        region_url = region_url.replace('{CM_NAME}', region[1])
        print region_url

        # Workaround to fix shitty markup on html result page
        # See http://pastebin.com/0HARTFDr
        response = br.open(region_url)
        soup = BeautifulSoup(response.read())
        response.set_data(soup.prettify(encoding='utf-8'))
        br.set_response(response)

        total_results = int(soup.table.td.getText().split('registros')[0].split(': ')[1])

        for current_page_results in [DEFAULT_RESULTS_PER_PAGE] * (total_results/DEFAULT_RESULTS_PER_PAGE):
            beaches_data += process_result_page(br, current_page_results)
            br.select_form(name='formsiguientes')
            br.submit()

        beaches_data += process_result_page(br, total_results % DEFAULT_RESULTS_PER_PAGE)

    open('utf-8.out', 'w').write(simplejson.dumps(beaches_data).encode('UTF-8'))
