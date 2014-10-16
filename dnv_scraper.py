# -*- coding: utf-8 -*-
import sys
import os
import time
from bs4 import BeautifulSoup
from urlparse import urljoin
from utils import (get_bs_from_static_site, extract_key_value_pairs_from_bs,
                   remove_accents)
from pprint import pprint
from traffic_data import TrafficData

PARSER = "lxml"


class RoadScraper():

    """Scraper for data of a single road.

    A road has a table where each row has data of a section of the road. All
    sections have data in this "simple_tbl" (the table accessed just with the
    road link).

    Some of them may also have a link to detail tables with more
    information. These detail tables are also grabbed and stored in
    "detail_tables".

    RoadScraper provide methods to iterate through "simple" and "detail"
    records, once a road has been scraped.
    """

    # DATA
    PARSER = "lxml"

    def __init__(self, road_name, base_url, dict_rutas):

        # scrape parameters
        self.road_name = road_name
        self.base_url = base_url
        self.dict_rutas = dict_rutas

        # results
        self.tabla_ruta_ver_detalle_dict = {}

        self.detail_tables = []

        self.simple_tbl = []
        self.details_tbl = []

    # PUBLIC
    def scrape(self):
        """Scrape data of each section of a road.

            toma la url de una ruta y devuelve 3 RVs en un arreglo:

            (1) un arreglo con la tabla con todos los tramos de la ruta con un
            codigo al principio identificador del tramo

            (2) un diccionario con todas las tablas "ver detalle" de aquellos tramos
            que no tienen promedio anual de la composicion pero si tienen un censo cobertura

            (3) un arreglo que almacena todos los datos "ver detalle" incluso de los tramos
            que no los tienen (con dicts vacios)
        """

        # parse base_url into a beautiful soup
        bs_road = get_bs_from_static_site(self.base_url, self.PARSER)

        # crea los arreglos y diccionarios que seran Return Values de la
        # funcion
        tabla_ruta_censo_cobertura = {}
        all_detail_tables = []

        id_section = 0
        # iterate rows
        for tr in bs_road.find_all("tr"):

            # get all elements of a row
            row_elements = tr.find_all("td", {"class": "FILA"})

            # check if row has 8 elements and proceed
            if len(row_elements) == 8:

                # new section has been found
                id_section += 1
                section_code = "{}_{}".format(self.road_name, id_section)
                print "Procesando tramo ", section_code

                # init a new row with section code
                row = [section_code]

                # iterate row elements adding each one to the row
                for element in row_elements:
                    row.append(element.get_text().strip())

                # check if the section has details to be scraped as well
                if self._has_details(row_elements):

                    # find details link
                    link_details_part = self._find_details_link(row_elements)

                    # join details part link with road base link
                    link_details = urljoin(self.dict_rutas[self.road_name],
                                           link_details_part)

                    # append link to simple table row
                    row.append(link_details)

                    # extract all tables from link_details of the section
                    detail_tables = self._extract_detail_tables(link_details)

                    # add new tables to detail_tables
                    all_detail_tables.append(detail_tables)

                # if has no details, append empty string instead of a link
                else:
                    row.append("")

                # add new row to the simple_tbl
                self.simple_tbl.append(row)

        #
        self._create_details_tbl(all_detail_tables)

    def get_simple_records(self):

        for row in self.simple_tbl:
            yield row

    def get_details_records(self):

        for row in self.details_tbl:
            yield row

    # PRIVATE
    def _has_details(self, row_elements):
        return row_elements[6].get_text() == "ver detalle"

    def _find_details_link(self, row_elements):
        return row_elements[6].find_all("a")[0]["href"]

    def _extract_detail_tables(self, details_link):
        """Extract all tables from a static url.

        Returns a dictionary where first index (1) is table id, second index
        (2) is row number (headers are first row) and third index (3) is the
        row variable name.
        """

        # parse details link into a beautiful soup
        bs = get_bs_from_static_site(details_link, PARSER)

        # create empty dict for tables extraction
        extracted_tables = {}

        # iterate tables in the bs
        for bs_table in bs.find_all("table"):
            extracted_table = []  # new empty table to be extracted

            # get table headers
            for thead in bs_table.find_all("thead"):
                for tr in thead.find_all("tr"):
                    row = []  # new empty row

                    # add all elements of headers to the new row
                    for th in tr.find_all("th"):
                        row.append(th.get_text())

                    # add headers row to the new table
                    extracted_table.append(row)

            # get table content
            for tbody in bs_table.find_all("tbody"):

                # iterate rows
                for tr in tbody.find_all("tr"):
                    row = []  # new empty row

                    # iterate through row elements
                    for td in tr.find_all("td"):
                        row.append(td.get_text())

                    # add content row to the new table
                    extracted_table.append(row)

            # get table name
            table_name = remove_accents(
                bs_table.previous_sibling.previous_sibling.get_text())

            # add new table to extracted tables dictionary
            extracted_tables[table_name] = extracted_table

        return extracted_tables

    def _create_details_tbl(self, all_detail_tables):

        # itera con un indice por todos los tramos de la ruta
        for i in xrange(len(all_detail_tables)):

            # toma el id del tramo
            id_tramo = self.simple_tbl[i][0].strip()

            # itera entre las tablas "ver detalle" de ese tramo si es que las
            # hay
            if len(all_detail_tables[i]) > 0:
                for tabla in all_detail_tables[i]:

                    # toma el id de la tabla
                    id_tabla = tabla

                    # itera entre las coordenadas fila-columna de la tabla
                    for nro_fila in xrange(len(all_detail_tables[i][tabla])):
                        for nro_col in xrange(len(all_detail_tables[i][tabla][nro_fila])):

                            # si estamos en una fila con datos, no con encabezados
                            # incorporamos el valor
                            if nro_fila != 0:

                                # tomo la variable
                                variable = all_detail_tables[
                                    i][tabla][0][nro_col].strip()

                                # tomo el nro de fila o la instancia
                                instancia = nro_fila

                                # tomo el valor
                                valor = all_detail_tables[i][
                                    tabla][nro_fila][nro_col].strip()

                                # genero un nuevo registro con los datos tomados y
                                # lo agrego al arreglo
                                row = [
                                    id_tramo, id_tabla, variable, instancia, valor]
                                self.details_tbl.append(row)


# DATA
# scraping parameters
metodo = "GET"
base_url_part1 = "http://transito.vialidad.gov.ar:8080/SelCE_WEB/tmda_libro_web_"
base_url_part2 = "/index.html"


# METHODS
def scrape_link_rutas(base_url, parser):
    """ toma el url base de las rutas y devuelve un
    diccionario con sus links """

    # toma el url base y lo convierte en una bs
    soup_rutas = get_bs_from_static_site(base_url, parser)

    # extrae la tabla que contiene los links de las rutas
    pares_clave_valor_soup = soup_rutas.find_all("td", {"class": "FILA"})

    # para cada regitro de la tabla extrae el texto y el link
    dict_rutas = {}
    for element in pares_clave_valor_soup:
        dict_temp = extract_key_value_pairs_from_bs(element, "a", "href")
        dict_rutas[dict_temp[dict_temp.keys()[0]]] = dict_temp.keys()[0]

    # toma la lista de las rutas cuyos links fueron scrapeados
    lista_rutas = dict_rutas.keys()

    # convierte los link_parts de las rutas en links completos agregandole la
    # url base
    for ruta in lista_rutas:
        dict_rutas[ruta] = urljoin(base_url, dict_rutas[ruta])

    return dict_rutas


def scrape_traffic_data(years, roads=None, excel_output=None):
    """Scrape traffic data from DNV webiste.

    Uses TrafficData to write results and RoadScraper to scrape one year-road
    at a time. Scrape all roads for years passed. If no roads are passed,
    it takes data from all of them."""

    # create a TrafficData object to store scraped data
    traffic_data = TrafficData()

    # iterate years
    for year in years:

        # create base_url for year
        year_base_url = base_url_part1 + year + base_url_part2

        print "\n\nTaking data from year url: ", year_base_url
        print "Taking data from year: ", year, "\n\n"

        # scrape road links for that year
        dict_rutas = scrape_link_rutas(year_base_url, PARSER)

        # if not roads provided, get them all
        if not roads:
            roads = dict_rutas.keys()

        # iterate roads
        for road in roads:

            print "\nTaking data from road: ", road, " at year: ", year, "\n"

            # create scraper for road and scrape it
            road_scraper = RoadScraper(road, dict_rutas[road], dict_rutas)
            road_scraper.scrape()

            # write each simple record scraped to excel
            for record in road_scraper.get_simple_records():
                traffic_data.write_simple_record(record)

            # write each details record scraped to excel
            for record in road_scraper.get_details_records():
                traffic_data.write_details_record(record)

        # save excel with all traffic data scraped
        traffic_data.save(excel_output)


def main():

    years = [str(year) for year in list(xrange(2010, 2011))]
    roads = ["0040"]

    scrape_traffic_data(years, roads)


if __name__ == '__main__':
    main()
