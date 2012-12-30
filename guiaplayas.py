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
import json

BASE_URL_TEMPLATE = 'http://aplicaciones2.magrama.es/dinamicas/guia_playas_busc/?playa=&municipio=&provincia=Todas&comunidad={CM_CODE}&bonita={CM_NAME}%2F%28Comunidad%29&pregunta={CM_CODE}&gf%5Et9100={CM_NAME}%2F%28Comunidad%29&bf%5Et9998=playa&hf%5Et9999=web3&h1%5Et3001=1&h2%5Et3002=25&id%5Et8000=4'

DEFAULT_RESULTS_PER_PAGE = 25

INFO_TABLE_SUMMARY="nombre y localización de la playa"
CHAR_TABLE_SUMMARY="tabla que muestra características de la playa"

regions = [["CM%3DANDALUCIA", "Andalucia"],
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

def process_beach_page(br):
    html_content = br.response().read()
    soup = BeautifulSoup(html_content)

    info_table = soup.table.find(summary=INFO_TABLE_SUMMARY)
    char_table = soup.table.find(summary=CHAR_TABLE_SUMMARY)

    beach = dict(zip(["name","town","province","region"],[x for x in info_table.stripped_strings][:-1]))
    char_strings = [x for x in char_table.findAll('tr') if x.text!=u'\n\xa0\n']

    description = char_strings.pop(0).text.strip()
    key = char_strings.pop(0).text.strip()
    char = dict({key:{}})

    while len(char_strings):
        item = char_strings.pop(0)
        if item.has_key("class") and item['class'] in (['fondoplayas2'], ['fondoplayas1']):
            if ': ' in item.text:
                char[key].update(dict([tuple(item.text.strip().split(': ', 1))]))
            else:
                text = item.text.strip()
                char[key].update({text:text})
        else:
            key = item.text.strip()
            char[key] = {}

    beach["characteristics"] = char
    return beach

def process_result_page(br, page_results):
    beaches_data = []

    form_index = 0
    while form_index < page_results:
        br.select_form(nr=form_index)
        if br.form.method == 'POST':
            br.submit()
            beaches_data.append(process_beach_page(br))
            br.back()
        form_index += 1

    return beaches_data

if __name__ == '__main__':
    br = mechanize.Browser()

    beaches_data = []

    for region in regions:
        region_url = BASE_URL_TEMPLATE.replace('{CM_CODE}', region[0])
        region_url = region_url.replace('{CM_NAME}', region[1])
        
        print region_url
        br.open(region_url)

        soup = BeautifulSoup(br.response().read())
        total_results = int(soup.table.td.getText().split('registros')[0].split(': ')[1])

        for current_page_results in [DEFAULT_RESULTS_PER_PAGE] * (total_results/DEFAULT_RESULTS_PER_PAGE):
            beaches_data += process_result_page(br, current_page_results)
            br.select_form(name='formsiguientes')
            br.submit()

        beaches_data += process_result_page(br, total_results % DEFAULT_RESULTS_PER_PAGE)
