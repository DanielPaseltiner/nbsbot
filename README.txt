NBS Automation Via Selenium

This is a Python library that allows for automation of select tasks in NBS at MaineCDC.

Requirements:
Python 3.9.x (https://www.python.org/)
Selenium (https://selenium-python.readthedocs.io/)
Chrome (https://www.google.com/chrome/?brand=CHBD&geo=US&gclid=Cj0KCQjwt-6LBhDlARIsAIPRQcLic96i0YjSkGCsnv6DsTkPY7Bz7SiJfVAg5MxI5e9fZSmO1dBwlQkaAslREALw_wcB&gclsrc=aw.ds)
Chrome driver that supports the installed version of Chrome. (https://chromedriver.chromium.org/downloads)

## Running the Updated Merged Bots

1. In the root directory, enter this command
```python
python -m RevisedBots.start_bots
```

2. You would be prompted to enter space separated numbers for the bots you'd like to Running

3. You would be prompted to enter your bot username and password for each bot iteration

4. Bots would run and automatically end when done