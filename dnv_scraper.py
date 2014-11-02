# -*- coding: utf-8 -*-
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
    "details_tbl" as a list of records.

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

        Feed "simple_tbl" with records taken from the road information table
        scraped where each row has data for one road section.

        Feed "details_tbl" with records taken from special details links found
        at some rows (ie, for some road sections) of the previous table. These
        have tables with more detailed information that are scraped and turned
        into records.
        """

        # parse base_url into a beautiful soup
        bs_road = get_bs_from_static_site(self.base_url, self.PARSER)

        # crea los arreglos y diccionarios que seran Return Values de la
        # funcion
        tabla_ruta_censo_cobertura = {}
        all_detail_tables = []

        # add empty row to simple_table (there will be field names there)
        num_simple_tbl_fields = len(TrafficData.get_simple_tbl_fields())
        # self.simple_tbl.append([""] * num_simple_tbl_fields)

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
                # print "Procesando tramo ", section_code

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

        # add records taken from detail tables to the details_tbl
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
        """Extract all detail tables from a static url.

        Returns a dictionary with "id_table" as keys. Each table is represented
        as a list of lists.

        Arg:
        "http://transito.vialidad.gov.ar:8080/SelCE_WEB/tmda_libro_web_2010/html_tramos/8511.html"

        Return:
        {u'clasificacion': [[u'A\xf1o', u'Mes', u'Horas', u'Autos y Ctas.',
                             u'Bus', u'S/A', u'C/A', u'Semi', u'TMD',
                             u'Cant. Puestos'],
                            [u'2010', u'3', u'48', u'74,2', u'4,2', u'8,4',
                             u'2,3', u'10,9', u'436', u'1'],
                            [u'2010', u'6', u'48', u'68,3', u'2,4', u'9,1',
                             u'4,5', u'15,7', u'290', u'1']],

         u'ruta': [[u'N\xba Distrito', u'Distrito', u'L\xedmites del Tramo',
                    u'Ini.', u'Fin', u'TMDA'],
                   [u'23', u'Santa Cruz', u'RIO TURBIO (I) - INT.R.P.7',
                    u'394,43', u'469,54', u'500']],

         u'velocidad': [[u'Estimador', u'Liv', u'Otros'],
                        [u'P85', u'135,6', u'103,8'],
                        [u'VM', u'110,4', u'84,7']]}
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
        """Create records from detail tables list adding them to details_tbl.

        Arg:
        [
        {u'clasificacion': [[u'A\xf1o', u'Mes', u'Horas', u'Autos y Ctas.',
                             u'Bus', u'S/A', u'C/A', u'Semi', u'TMD',
                             u'Cant. Puestos'],
                            [u'2010', u'3', u'48', u'74,2', u'4,2', u'8,4',
                             u'2,3', u'10,9', u'436', u'1'],
         u'ruta': [[u'N\xba Distrito', u'Distrito', u'L\xedmites del Tramo',
                    u'Ini.', u'Fin', u'TMDA'],
                   [u'23', u'Santa Cruz', u'RIO TURBIO (I) - INT.R.P.7',
                    u'394,43', u'469,54', u'500']]},

        {u'clasificacion': [[u'A\xf1o', u'Mes', u'Horas', u'Autos y Ctas.',
                             u'Bus', u'S/A', u'C/A', u'Semi', u'TMD',
                             u'Cant. Puestos'],
                            [u'2010', u'3', u'48', u'74,2', u'4,2', u'8,4',
                             u'2,3', u'10,9', u'436', u'1'],
         u'ruta': [[u'N\xba Distrito', u'Distrito', u'L\xedmites del Tramo',
                    u'Ini.', u'Fin', u'TMDA'],
                   [u'23', u'Santa Cruz', u'RIO TURBIO (I) - INT.R.P.7',
                    u'394,43', u'469,54', u'500']]}
        ]

        Example records added to self.details_tbl:
        ['0040_1', u'ruta', u'N\xba Distrito', 1, u'23']
        ['0040_1', u'ruta', u'Distrito', 1, u'Santa Cruz']
        ['0040_1', u'ruta', u'L\xedmites del Tramo', 1, u'RIO TURBIO (I) - INT.R.P.7']
        ['0040_1', u'clasificacion', u'A\xf1o', 1, u'2010']
        ['0040_1', u'clasificacion', u'Mes', 1, u'3']
        ['0040_1', u'clasificacion', u'Horas', 1, u'48']
        ['0040_1', u'clasificacion', u'Autos y Ctas.', 1, u'74,2']

        """

        # iterate sections of a road
        for num_section in xrange(len(all_detail_tables)):

            # using the iteration index, get the section id from simple table
            id_section = self.simple_tbl[num_section][0].strip()

            # check if there is any detail table of the section
            if len(all_detail_tables[num_section]) > 0:

                # iterate detail tabales of the section
                for id_table in all_detail_tables[num_section]:

                    # get table
                    table = all_detail_tables[num_section][id_table]

                    # iterate rows of the detail table
                    for num_row in xrange(len(table)):

                        # get row
                        row = table[num_row]

                        # iterate columns of the row
                        for num_col in xrange(len(row)):

                            # dont use first row (headers)
                            if num_row != 0:

                                # get variable of the table (header)
                                variable = table[0][num_col].strip()

                                # get the value
                                value = row[num_col].strip()

                                # create new record
                                record = [id_section, id_table, variable,
                                          num_row, value]

                                # add new record to details table
                                self.details_tbl.append(record)


# DATA
# scraping parameters
base_url_part1 = "http://transito.vialidad.gov.ar:8080/SelCE_WEB/tmda_libro_web_"
base_url_part2 = "/index.html"


# METHODS
def scrape_road_links(year_base_url):
    """Scrape road links from a year url and return them as a dictionary.

    Arg:
    "http://transito.vialidad.gov.ar:8080/SelCE_WEB/tmda_libro_web_2010/index.html"

    Return:
    {u'0001': 'http://transito.vialidad.gov.ar:8080/SelCE_WEB/tmda_libro_web_2010/html_rutas/0001.html',
     u'0003': 'http://transito.vialidad.gov.ar:8080/SelCE_WEB/tmda_libro_web_2010/html_rutas/0003.html',
     u'0005': 'http://transito.vialidad.gov.ar:8080/SelCE_WEB/tmda_libro_web_2010/html_rutas/0005.html'}

    """

    # parse year url into beautiful soup
    bs_roads = get_bs_from_static_site(year_base_url, PARSER)

    # extrae la tabla que contiene los links de las rutas
    bs_key_value_pairs = bs_roads.find_all("td", {"class": "FILA"})

    # para cada regitro de la tabla extrae el texto y el link
    road_links = {}
    for element in bs_key_value_pairs:
        dict_temp = extract_key_value_pairs_from_bs(element, "a", "href")
        road_links[dict_temp[dict_temp.keys()[0]]] = dict_temp.keys()[0]

    # toma la lista de las rutas cuyos links fueron scrapeados
    roads_list = road_links.keys()

    # convierte los link_parts de las rutas en links completos agregandole la
    # url base
    for road in roads_list:
        road_links[road] = urljoin(year_base_url, road_links[road])

    return road_links


def scrape_traffic_data(years, roads=None, excel_output=None):
    """Scrape traffic data from DNV website.

    Uses TrafficData to write results and RoadScraper to scrape one year-road
    at a time. Scrape all roads for years passed. If no roads are passed,
    it takes data from all of them."""

    traffic_data = TrafficData()

    # iterate years
    for year in years:

        # create base_url for year
        year_base_url = base_url_part1 + year + base_url_part2

        # scrape road links for that year
        road_links = scrape_road_links(year_base_url)

        # if not roads provided, get them all
        if not roads:
            roads = road_links.keys()

        # iterate roads
        for road in roads:

            print "Taking data from road: ", road, " at year: ", year

            # create scraper for road and scrape it
            road_scraper = RoadScraper(road, road_links[road], road_links)
            road_scraper.scrape()

            # write each simple record scraped to excel
            for record in road_scraper.get_simple_records():
                traffic_data.write_simple_record(record + [year])

            # write each details record scraped to excel
            for record in road_scraper.get_details_records():
                traffic_data.write_details_record(record + [year])

    # save excel with all traffic data scraped
    traffic_data.save(excel_output)


def main():

    years = [str(year) for year in list(xrange(2006, 2014))]
    roads = ["0014"]

    scrape_traffic_data(years, roads, "Trafico ruta 14 - 2006 a 2013 - TEST.xlsx")

if __name__ == '__main__':
    main()
