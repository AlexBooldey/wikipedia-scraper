<img src="http://municipalmagazine.com/wp-content/uploads/2017/04/jayankondam-wiki.png" width=110 height=90 align="left"/>

Wiki Cralwer
=======================

The Python project for capturing random pages in Wikipedia, extracting information from the page:
  **Title, Content, Categories, History(User, Date of change)**.
For further storage in the MySQL database.

# Installing & Running
- Python 3.6.5
- MySQL (I'm using the version 5.7.22-0ubuntu0.16.04.1)
- All libraries used are in the Python Standard Library except:
  - BeautifulSoup4 (```pip install beautifulsoup4```)
  - pymysql
  - requests


## Running
1. Create the necessary tables and additional fields in the table
    - Run bash **create_wiki_tables.sh**
2. Create stored procedures
    - Run bash **create_wiki_procedures.sh**

3. Edit file **config.json**
```json
      "mysql": {
            "host": " ",
            "user": " ",
            "password": " ",
            "database": " "
      }
```

4. Run **wikipedia-crawler.py**
```bash
    python3 wikipedia-crawler.py
```

