dnv_scraper
===========

Scraper for argentinian National Roads Department (DNV in spanish) traffic
information.

It is used to scrape traffic data from the site of "Dirección Nacional de
Vialidad" wich is the national roads department authority in Argentina:
http://transito.vialidad.gov.ar:8080/SelCE_WEB/intro.html

I am currently heavy-refactoring and translating into english old pieces
of code from my scratch starts as a self-taught programmer, this one got fairly
prettier but some pieces of code are still obscure. It works very well anyway.

You can download or clone the repository on your local computer to use it.

## Command-line interface

It can be called through command line interface passing from zero to 3
parameters:

1. Excel file name (always with .xlsx)
2. Roads (one road, or many separated by commas)
3. Years (one year, or many separated by commas) - Starting at 2006

```cmd
python dnv_scraper.py some_traffic_data.xlsx 0014,0003 2006,2008,2013
```

Parameters are optional. You could call just the script alone to scrape all
data (all roads, all years from 2006 up to last year) or add less than three
parameters (always in excel-roads-years order).

```cmd
python dnv_scraper.py
python dnv_scraper.py some_traffic_data.xlsx
python dnv_scraper.py some_traffic_data.xlsx 0014,0003
```

## Imports

You could also import ´scrape_traffic_data´ method from inside the directory
method and use it.

```python
from dnv_scraper import scrape_traffic_data
years = [2006, 2008, 2013]
roads = ["0014", "0003"]
excel_output = "some_traffic_data.xlsx"
scrape_traffic_data(years, roads, excel_output)
```

Again, parameters could be "None" or not passed at all.

```python
from dnv_scraper import scrape_traffic_data
scrape_traffic_data()
```

Also, you could call parameters with keyword arguments.
```python
from dnv_scraper import scrape_traffic_data
scrape_traffic_data(years=[2006, 2013], roads=["0014"])
```

## Test

To test the proper functioning of the module you can run the unit test.

```cmd
python test_dnv_scraper.py
```

Or from inside the directory.

```python
import test_dnv_scraper
test_dnv_scraper.main()
```