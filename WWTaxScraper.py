# import the libraries
#selenium for chrome automation
    # instead of importing selenium, you import the webdriver
        # web driver performs actions and links with the browser
from distutils.log import error
import sys
import os
cwd = os.getcwd()
sys.path.append(cwd)
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
#pandas to create dataframe out of scraped data
import pandas as pd
#time to sleep in between requests
import time
#datetime to retrieve current date
from datetime import datetime, date, timedelta
#pymssql to connect to azure db
import pymssql
#logging to create log files locally
import logging
#import values from the config file
import config
#LA county scraper will make a pop-up box that the user has to click
from tkinter import Tk, Button

#creates a log file after every time the code is run
logging.basicConfig(filename='wedgewood_tax.log', encoding='utf-8', level=logging.DEBUG)
logging.debug(f"after all imports")

#service object is the path to chrome webdriver
    #it's going to be used to activate the webdriver
s = Service(config.db_conn['driver-path']) #get the driver path from config file- makes it so that you can change later without breaking .exe file

#add the folder where .exe file is to the executable path
    # need to do this because otherwise the exe won't be able to find/read from the config file
logging.debug(f"Chrome driver path {config.db_conn['driver-path']}")
#print driver path to the console
print(config.db_conn['driver-path'])

#db connection string
conn = pymssql.connect(server=config.db_conn['server'], user=config.db_conn['username'], password=config.db_conn['password'], database=config.db_conn['database'])

logging.debug(f"server={config.db_conn['server']}, user={config.db_conn['username']}, password={config.db_conn['password']}, database={config.db_conn['database']}")

#print db connection string to console
print(f"server={config.db_conn['server']}, user={config.db_conn['username']}, password={config.db_conn['password']}, database={config.db_conn['database']}")

# create cursor to make queries
curs = conn.cursor()
# time.sleep(10)

#
#
#
#                                       COUNTY SCRAPERS
#
#
#
def la_func(apn):
    #need 2 dictionaries for this one
        #since there are 2 sections in the site
    tax_details1 = {
            'TaxYear':[],
            'TaxAmnt':[],
            'DueDate':[],
            'Note':[],
            'RetrievalDate':[],
            'APN':[]
        }
    tax_details2 = {
            'TaxYear':[],
            'TaxAmnt':[],
            'DueDate':[],
            'Note':[],
            'RetrievalDate':[],
            'APN':[]
        }

    #add RetrievalDate and APN, note to the dictionary in case scraper fails
        #these values can still be used for the log
    #retrieval date to dict
    d1 = date.today()
    rdate = str(d1)
    tax_details1['RetrievalDate'].append(rdate)
    tax_details2['RetrievalDate'].append(rdate)
    #apn to dict
    tax_details1['APN'].append(apn)
    tax_details2['APN'].append(apn)
    #note to dict
    note = 'Los Angeles '
    tax_details1['Note'].append(note)
    tax_details2['Note'].append(note)

    try:

        #Use the WebDriver to visit Clark County Search URL
        driver.get("https://vcheck.ttc.lacounty.gov/index.php")

        #get past CAPTcha
        try:
            # make a popup window asking to get past reCATPTCHA
            root=Tk()
            Button(root, text="Please fill out the CAPTCHA and click next on the screen to continue. \n When finished, click on this text.", command=root.destroy).pack()
            root.mainloop()

            #get to search link
            try:
                #Once you've passed CAPTCHA, you can navigate to search link
                driver.get('https://vcheck.ttc.lacounty.gov/proptax.php?page=screen')

                #need to split up the apn so you can enter them into search box
                    #diff sections for map book (mb), page (pg), parcel(pl)
                laapn = apn.split('-')
                mb = laapn[0]
                pg = laapn[1]
                pl = laapn[2]

                #3 input boxes for Map Book, Page, and Parcel
                mbpath = driver.find_element(by=By.NAME, value='mapbook')
                pgpath = driver.find_element(by=By.NAME, value='page')
                plpath = driver.find_element(by=By.NAME, value='parcel')
                #enter the values into the fields
                mbpath.send_keys(mb)
                time.sleep(1)
                pgpath.send_keys(pg)
                time.sleep(1)
                plpath.send_keys(pl)
                time.sleep(1)
                plpath.send_keys(Keys.RETURN)
                time.sleep(1)

                #once the value is entered you need to go to the link showing you the tax info
                infobutton = driver.find_element(by=By.CLASS_NAME, value='submitButton').click()
                time.sleep(1)

                #gather the data
                try:
                    #paths for property with no tax due
                    is1path = '//*[@id="mainContent"]/table/tbody/tr/td[2]/div/div/table[1]/tbody/tr[6]/td[2]'
                    is2path = '//*[@id="mainContent"]/table/tbody/tr/td[2]/div/div/table[1]/tbody/tr[6]/td[5]'
                    #paths for property with tax due
                    ntispath1 = '//*[@id="mainContent"]/table/tbody/tr/td[2]/div/div/table[1]/tbody/tr[6]/td[2]'
                    ntispath2 = '//*[@id="mainContent"]/table/tbody/tr/td[2]/div/div/table[1]/tbody/tr[6]/td[5]'
                    #looks like the layout is the same whether taxes are due or not

                    #there are 2 installment boxes
                        #we're gonna put each separate one into the TaxData table
                    #value from first installment box
                    inst1 = driver.find_element(by=By.XPATH, value=is1path).text
                    inst1 = inst1.replace('$', '')
                    inst1 = inst1.replace(',', '')
                    inst1due = float(inst1)
                    tax_details1['TaxAmnt'].append(inst1due)
                    #due date from first installment box
                    dd1path = '//*[@id="mainContent"]/table/tbody/tr/td[2]/div/div/table[1]/tbody/tr[7]/td[2]'
                    dd1 = driver.find_element(by=By.XPATH, value=dd1path).text
                    tax_details1['DueDate'].append(dd1)

                    typath = '//*[@id="mainContent"]/table/tbody/tr/td[2]/div/div/div[2]'
                    TYR = driver.find_element(by=By.XPATH, value=typath).text
                    TYR2 = TYR.split('Year:')[1].lstrip()
                    TYR3 = TYR2.split(' ')[0]
                    if len(TYR3) < 4:
                        tyear = int('20'+TYR3)
                    else:
                        tyear = int(TYR3)
                    tax_details1['TaxYear'].append(tyear)
                    tax_details2['TaxYear'].append(tyear)
                    # #tax year will usually be the year from installment 1 box
                    # tyear = dd1[-4:]
                    # if tyear == ' ' or tyear == 0:
                    #     tyear = ''
                    # tax_details1['TaxYear'].append(tyear)
                    # tax_details2['TaxYear'].append(tyear)

                    #value from second installment box
                    inst2 = driver.find_element(by=By.XPATH, value=is2path).text
                    inst2 = inst2.replace('$', '')
                    inst2 = inst2.replace(',', '')
                    inst2due = float(inst2)
                    tax_details2['TaxAmnt'].append(inst2due)
                    #due date from second installment box
                    dd2path = '//*[@id="mainContent"]/table/tbody/tr/td[2]/div/div/table[1]/tbody/tr[7]/td[5]'
                    dd2 = driver.find_element(by=By.XPATH, value=dd2path).text
                    if dd2 == ' ':
                        dd2 = ''
                    tax_details2['DueDate'].append(dd2)

                    #turn the 2 dictionaries into pandas dataframes
                    df1 = pd.DataFrame(tax_details1)
                    df2 = pd.DataFrame(tax_details2)

                    #Call writetaxdata function
                    WriteTaxData(df1, curs, conn)
                    WriteTaxData(df2, curs, conn)
                    print(df1)
                    print(df2)
                except Exception as e:
                    err = f'error: unable to scrape tax data for {apn}. {e}'
                    note2 = note + err
                    WriteLogData(note2, rdate, apn)
            except Exception as e:
                err1 = f'error: could not find property with APN {apn}. {e}'
                note2 = note + err1
                WriteLogData(note2, rdate, apn)
        except Exception as e:
            err2 = f'error: could not get past CAPTCHA. {e}'
            note2 = note + err2
            WriteLogData(note2, rdate, apn)
    except Exception as e:
        err3 = f'error: county website could not be reached. {e}'
        note2 = note + err3
        WriteLogData(note2, rdate, apn)


def clark_func(apn):
    #first, make dictionary to store values
    #dict will be the same for each site
    tax_details = {
            'TaxYear':[],
            'TaxAmnt':[],
            'DueDate':[],
            'Note':[],
            'RetrievalDate':[],
            'APN':[]
        }
    #add RetrievalDate and APN, note to the dictionary in case scraper fails
        #these values can still be used for the log
    #retrieval date to dict
    d1 = date.today()
    rdate = str(d1)
    tax_details['RetrievalDate'].append(rdate)
    #apn to dict
    tax_details['APN'].append(apn)
    #note to dict
    note = 'Clark '
    tax_details['Note'].append(note)
    
    #make sure Selenium can reach the county site
    try:
        #Use the WebDriver to visit Clark County Search URL
        driver.get("https://trweb.co.clark.nv.us/")
        search = driver.find_element(by=By.NAME, value="Valid_ID")
        
        #now check to see if the APN can be searched on the site
        try:
            #Enter in the sample ACN
            search.send_keys(apn)
            #Search the APN
            search.send_keys(Keys.RETURN)

            #try adding the property tax data to the dictionary
            try:
                # add tax year to dictionary
                taxyear = driver.find_element(by=By.XPATH, value="/html/body/table[4]/tbody/tr[3]/td/table/tbody/tr/td[4]")
                tax_date = taxyear.text
                short_split_year = tax_date[-2:]
                split_year = '20' + short_split_year
                tax_details['TaxYear'].append(split_year)

                # add tax amount to dictionary
                clarktax1 = '/html/body/table[4]/tbody/tr[5]/td/table[6]/tbody/tr[8]/td[2]/u'
                clarknotax1 = "/html/body/table[4]/tbody/tr[5]/td/table[4]/tbody/tr[3]/td[2]/u"
                try:
                    # tax path for properties with tax value due
                    # looks like there's only one path for these properties
                    amount_due = driver.find_element(by=By.XPATH, value=clarktax1)
                    tax_Due = amount_due.text
                    taxes_Due = tax_Due[1:]
                    taxes_Due = taxes_Due.split(',')
                    tax_Due = ''
                    for x in taxes_Due:
                        tax_Due = tax_Due + x
                    tax_details['TaxAmnt'].append(tax_Due)
                except:
                    try:
                        # tax path for properties with no tax due
                        amount_due = driver.find_element(by=By.XPATH, value=clarknotax1)
                        tax_Due = amount_due.text
                        tax_due_float = float(tax_Due.split('$')[1])
                        tax_details['TaxAmnt'].append(tax_due_float)
                    except Exception as e:
                        #if still not able to scrape anything, write error to Log
                        terr = f'error: unable to scrape tax amount for {apn}: e'
                        note2 = note + terr
                        WriteLogData(note2, rdate, apn)
                # add due date to dictionary
                duedate = ''
                tax_details['DueDate'].append(duedate)

                #assign dict to dataframe
                df = pd.DataFrame(tax_details)
                
                #put df into database
                WriteTaxData(df, curs, conn)
                
            except Exception as e:
                err1 = f'error: Unable to scrape necessary data for {apn}: {e}'
                note2 = note + err1
                WriteLogData(note2, rdate, apn)
        except Exception as e:
            err2 = f'error: {apn} was not found in the system: {e}'
            note2 = note + err2
            WriteLogData(note2, rdate, apn)
    except Exception as e:
        err3 = f'error: Unable to reach county site: {e}'
        note2 = note + err3
        WriteLogData(note2, rdate, apn)
    
def harris_func(apn):
    #first, make dictionary to store values
    tax_details = {
            'TaxYear':[],
            'TaxAmnt':[],
            'DueDate':[],
            'Note':[],
            'RetrievalDate':[],
            'APN':[]
        }
    #add RetrievalDate and APN, note to the dictionary in case scraper fails
        #these values can still be used for the log
    #retrieval date to dict
    d1 = date.today()
    rdate = str(d1)
    tax_details['RetrievalDate'].append(rdate)
    #apn to dict
    tax_details['APN'].append(apn)
    #note to dict
    note = 'Harris '
    tax_details['Note'].append(note)
    
    #make sure Selenium can reach the county site
    try:
        #Use the WebDriver to visit Clark County Search URL
        driver.get("https://www.hctax.net/Property/PropertyTax")
        #set webdriver size to avoid html structure changing
        driver.set_window_position(1124, 1024, windowHandle='current')

        #ACN form in this webpage has name "txtSearchValue"
        search = driver.find_element(by=By.NAME, value="txtSearchValue")
        
        #try entering the apn into the website's search form
        try:
            #Enter in the sample ACN
            APN = apn
            search.send_keys(APN)
            #Search the ACN
            search.send_keys(Keys.RETURN)
            #need to sleep the function for a few seconds while the links load
            time.sleep(5)

            #click on the link taking you to property tax data
                #there are different XPATH values
                    #maybe based on browser window size?
            harrisval2 = "/html/body/div[2]/div/div/div/div/div[2]/fieldset/div/div[2]/table/tbody/tr/td[1]/a"
            harrisval3 = "//*[@id='TaxSearch']/div[2]/table/tbody/tr/td[1]/a"
            try:
                info_link = driver.find_element(by=By.XPATH, value=harrisval3).click()
                
                #add data to the dictionary
                try:
                    #add year to dictionary
                    d1 = datetime.now()
                    year = d1.year
                    tax_details['TaxYear'].append(year)

                    #add tax amount to dictionary
                    amount_due = driver.find_element(by=By.XPATH, value="//*[@id='CurrentStatement']/table[4]/tbody/tr[3]/td[2]")
                    taxes_Due = amount_due.text
                    taxes_Due = taxes_Due[1:]
                    taxes_Due = taxes_Due.split(',')
                    tax_Due = ''
                    for x in taxes_Due:
                        tax_Due = tax_Due + x
                    tax_details['TaxAmnt'].append(tax_Due)

                    #add due date to dictionary
                    duedate = ''
                    tax_details['DueDate'].append(duedate)

                    #assign dict to dataframe
                    df = pd.DataFrame(tax_details)

                    #put df into database
                    WriteTaxData(df, curs, conn)

                except Exception as e:
                    err1 = f'error: Unable to web scrape necessary data for {apn}: {e}'
                    note2 = note.append(err1)
                    WriteLogData(note2, rdate, apn)
                
            except:
                info_link = driver.find_element(by=By.XPATH, value=harrisval2).click()

                #add data to the dictionary
                try:
                    #add year to dictionary
                    d1 = datetime.now()
                    year = d1.year
                    tax_details['TaxYear'].append(year)

                    #add tax amount to dictionary
                    amount_due = driver.find_element(by=By.XPATH, value="//*[@id='CurrentStatement']/table[4]/tbody/tr[3]/td[2]")
                    taxes_Due = amount_due.text
                    taxes_Due = taxes_Due[1:]
                    taxes_Due = taxes_Due.split(',')
                    tax_Due = ''
                    for x in taxes_Due:
                        tax_Due = tax_Due + x
                    tax_details['TaxAmnt'].append(tax_Due)

                    #add due date to dictionary
                    duedate = ''
                    tax_details['DueDate'].append(duedate)

                    #assign dict to dataframe
                    df = pd.DataFrame(tax_details)

                    #put df into database
                    WriteTaxData(df, curs, conn)

                except Exception as e:
                    err1 = f'error: Unable to web scrape necessary data for {apn}: {e}'
                    note2 = note + err1
                    WriteLogData(note2, rdate, apn)
        except Exception as e:
            err2 = f'error: Unable to find property associated with Parcel Number: {apn}: {e}'
            note2 = note + err2
            WriteLogData(note2, rdate, apn)
    except Exception as e:
        err3 = f'error: County website could not be reached: {e}'
        note2 = note + err3
        WriteLogData(note2, rdate, apn)

def maricopa_func(apn):
    #first, make dictionary to store values
    tax_details = {
            'TaxYear':[],
            'TaxAmnt':[],
            'DueDate':[],
            'Note':[],
            'RetrievalDate':[],
            'APN':[]
        }
    #add RetrievalDate and APN, note to the dictionary in case scraper fails
        #these values can still be used for the log
    #retrieval date to dict
    d1 = date.today()
    rdate = str(d1)
    tax_details['RetrievalDate'].append(rdate)
    #apn to dict
    tax_details['APN'].append(apn)
    #note to dict
    note = 'Maricopa '
    tax_details['Note'].append(note)
    
    #for maricopa, you can just put the apn into the url to get to taxdata
    
    #search apn to see if property is in the county's database
    try:
        #take out the dashes in APN and put everything together
        sendkeyfull = apn
        sendkey = sendkeyfull.replace('-','')
        #go to the link that displays property tax data
        driver.get(f'https://treasurer.maricopa.gov/parcel/default.aspx?Parcel={sendkey}')
        
        #scrape tax data
        try:
            #add tax year
            try:
                xpath = "/html/body/form/div[4]/div[2]/div/div/div[2]/div[2]/div[2]/div[1]/h4"
                year = driver.find_element(by=By.XPATH, value=xpath)
                tax_year = year.text
                short_split_year = tax_year[:4]
                split_year = short_split_year
                tax_details['TaxYear'].append(split_year)
            except:
                tax_details['TaxYear'].append('')
            
            #no due date
            duedate = ''
            tax_details['DueDate'].append(duedate)
            
            time.sleep(2)
            
            #add tax amount to dictionary
                #different xpaths for taxes due/not due
                #2 diff paths to get to acutal tax data
                    #taxpath 1 and 2
                #another for paths without tax data
                    #ntpath
            taxpath = '//*[@id="cphMainContent_cphRightColumn_taxDue1"]/tbody/tr/td[6]/a'
            taxpath2 = "//*[@id='cphMainContent_cphRightColumn_taxDue2']/li[6]/a" 
            ntpath = "//*[@id='siteInnerContentContainer']/div/div[2]/div[2]/div[4]/div[2]/ul[1]/li[2]/span"
            try:
                #xpath in case there's tax due 
                #try for both xpaths
                try:
                    #scrape page using taxpath
                    t_due = driver.find_element(by=By.XPATH, value=taxpath)
                    #get the text of amount due (will contain $ and comma)
                    td = t_due.text
                    #remove $ from td object
                    td = td[1:]
                    #split td on comma to turn into int
                    td = td.split(',')
                    #need to make a loop to combine the 2 split values
                    t_due_float = ''
                    for n in td:
                        t_due_float = t_due_float + n
                    tax_details['TaxAmnt'].append(t_due_float)
                except:
                    #scrape page using taxpath2
                    t_due = driver.find_element(by=By.XPATH, value=taxpath2)
                    #get the text of amount due (will contain $ and comma)
                    td = t_due.text
                    #remove $ from td object
                    td = td[1:]
                    #split td on comma to turn into int
                    td = td.split(',')
                    #need to make a loop to combine the 2 split values
                    t_due_float = ''
                    for n in td:
                        t_due_float = t_due_float + n
                    tax_details['TaxAmnt'].append(t_due_float)
            except:
                try:
                    # xpath for properties with no tax due
                    amount_secured = driver.find_element(by=By.XPATH, value=ntpath)
                    amount_due_secured = amount_secured.text
                    amount_due_secured_float = float(amount_due_secured.split('$')[1])
                    tax_details['TaxAmnt'].append(amount_due_secured_float)
                except Exception as e:
                    terr = f'error: Unable to scrape tax amount for {apn}: {e}'
                    note2 = note + terr
                    WriteLogData(note2, rdate, apn)
            #assign dict to dataframe
            df = pd.DataFrame(tax_details)
            #put df into database
            WriteTaxData(df, curs, conn)
        except Exception as e:
            err1 = f'error: Unable to scrape necessary data for {apn}: {e}'
            note2 = note + err1
            WriteLogData(note2, rdate, apn)
    except Exception as e:
        err2 = f'error: Unable to find property associated with parcel no. {apn}: {e}'
        note2 = note + err2
        WriteLogData(note2, rdate, apn)

def travis_func(apn):
    #first, make dictionary to store values
    tax_details = {
            'TaxYear':[],
            'TaxAmnt':[],
            'DueDate':[],
            'Note':[],
            'RetrievalDate':[],
            'APN':[]
        }
    #add RetrievalDate and APN, note to the dictionary in case scraper fails
        #these values can still be used for the log
    #retrieval date to dict
    d1 = date.today()
    rdate = str(d1)
    tax_details['RetrievalDate'].append(rdate)
    #apn to dict
    tax_details['APN'].append(apn)
    #note to dict
    note = 'Travis '
    tax_details['Note'].append(note)
    
    #first make sure Selenium can reach the county site
    try:
        #we could use the send key as different variable that could be directly changed
        sendkeyfull = str(apn)
        sendkey = sendkeyfull.replace('-','')

        #Use the WebDriver to visit San Diego Search URL
        driver.get("https://travis.go2gov.net/cart/responsive/search.do")
        
        #check if apn is in county's database
        try:
            #ACN form in this webpage has name "txtSearchValue"
            search = driver.find_element(by=By.NAME, value="criteria.heuristicSearch")
            #Enter in the sample ACN
            search.send_keys(sendkey)
            #Search the ACN
            search.send_keys(Keys.RETURN)

            #click on the box to proceeed to pay bills
            info_link = driver.find_element(by=By.XPATH, value="/html/body/div[1]/div[2]/div[2]/form[1]/table/tbody/tr/td[1]/div[1]/a/span").click()

            #scrape tax data
            try:
                # add tax year to dict
                d1 = datetime.now()
                year = d1.year
                tax_details['TaxYear'].append(year)
                '''year = driver.find_element(by=By.XPATH, value="/html/body/div/div[2]/div[2]/div[2]/table/tbody/tr/td[1]/a/span")
                tax_year = year.text
                tax_details['TaxYear'].append(tax_year)''' #alternative method

                try:
                    # add tax amount to dict
                    amount_secured = driver.find_element(by=By.XPATH, value="/html/body/div/div[2]/div[2]/div[2]/table/tbody/tr/td[5]")
                    amount_due_secured = amount_secured.text
                    amount_due_secured_float = float(amount_due_secured.split('$')[1])
                    tax_details['TaxAmnt'].append(amount_due_secured_float)
                except Exception as e:
                    #if still not able to scrape anything, write error to Log
                    terr = f'error: Unable to scrape tax amount for {apn}: e'
                    note2 = note + terr
                    WriteLogData(note2, rdate, apn)

                # add due date to dict
                duedate = ''
                tax_details['DueDate'].append(duedate)

                #assign dict to dataframe
                df = pd.DataFrame(tax_details)

                #put df into database
                WriteTaxData(df, curs, conn)

            except Exception as e:
                err1 = f'error: Unable to scrape necessary data for {apn}: {e}'
                note2 = note + err1
                WriteLogData(note2, rdate, apn)
        except Exception as e:
            err2 = f'error: Unable to find property associated with parcel no. {apn}: {e}'
            note2 = note + err2
            WriteLogData(note2, rdate, apn)
    except Exception as e:
        err3 = f'error: Unable to reach county site: {e}'
        note2 = note + err3
        WriteLogData(note2, rdate, apn)

def sd_func(apn):
    #first, make dictionary to store values
    tax_details = {
            'TaxYear':[],
            'TaxAmnt':[],
            'DueDate':[],
            'Note':[],
            'RetrievalDate':[],
            'APN':[]
        }
    #add RetrievalDate and APN to the dictionary in case scraper fails
        #these values can still be used for the log
    #retrieval date to dict
    d1 = date.today()
    rdate = str(d1)
    tax_details['RetrievalDate'].append(rdate)
    #apn to dict
    tax_details['APN'].append(apn)
    #note to dict
    note = 'San Diego '
    
    #make sure Selenium can reach the county site
    try:
        #Use the WebDriver to visit San Diego Search URL
        driver.get("https://iwr.sdttc.com/paymentapplication/Search.aspx")
        #set webdriver size to avoid html structure changing
        driver.set_window_position(1124, 1024, windowHandle='current')
        #click on the arrow to open the input box
        xpath = "/html/body/form/div[3]/div[3]/div[2]/div[3]/div[5]/div[1]/div[1]/h1/a"
        info_link = driver.find_element(by=By.XPATH, value=xpath).click()
        time.sleep(5)
        
        #search the county site to see if the apn is in county's database
        try:
            #APN form in this webpage has name "txtSearchValue"
            sendkeyfull = str(apn)
            sendkey = sendkeyfull.replace('-','')
            id1 = "PaymentApplicationContent_tbParcelNumber"
            search = driver.find_element(by=By.ID, value=id1)
            time.sleep(5)
            #Enter in the sample APN
            search.send_keys(sendkey)
            #Search the ACN
            search.send_keys(Keys.RETURN)
            
            
            #add items to the dictionary
            try:
                # add tax year
                d1 = datetime.now()
                year = d1.year
                tax_details['TaxYear'].append(year)

                # add amount
                try:
                    # path for properties with tax due
                    sdtax1 = '//*[@id="PaymentApplicationContent_gvSecured"]/tbody/tr[2]/td[11]'
                    amount_secured = driver.find_element(by=By.XPATH, value=sdtax1)
                    taxes_Due = amount_secured.text
                    taxes_Due = taxes_Due[1:]
                    # if the amount due is in the thousands, there will be a comma in the number
                    # we have to get rid of the comma so we can add the number to the dict
                    try:
                        taxes_Due = taxes_Due.split(',')
                        tax_Due = ''
                        for x in taxes_Due:
                            tax_Due = tax_Due + x
                        tax_details['TaxAmnt'].append(tax_Due)
                        sdnote = '-NOTICE: this scraper only gathers secured property tax data for this APN.'
                        tax_details['Note'].append(note+sdnote)
                    # process if there is no comma in the tax due
                    except:
                        tax_Due = float(taxes_Due)
                        tax_details['TaxAmnt'].append(tax_Due)
                        sdnote = '-NOTICE: this scraper only gathers secured property tax data for this APN.'
                        tax_details['Note'].append(note+sdnote)
                except:
                    try:
                        # path for if no taxes are due
                        amount_secured = driver.find_element(by=By.XPATH, value="/html/body/form/div[3]/div[3]/div[2]/div[2]/div[5]/div[2]/div/table/tbody/tr[3]/td[7]")
                        amount_due_secured = amount_secured.text
                        tax_Due = ''
                        for x in taxes_Due:
                            tax_Due = tax_Due + x
                        tax_details['TaxAmnt'].append(tax_Due)
                        tax_details['TaxAmnt'].append(amount_due_secured)
                        sdnote = '-NOTICE: this scraper only gathers secured property tax data for this APN.'
                        tax_details['Note'].append(note+sdnote)
                    except Exception as e:
                        #if still not able to scrape anything, write error to Log
                        terr = f'error: Unable to scrape tax amount for {apn}: e'
                        note2 = note + terr
                        WriteLogData(note2, rdate, apn)

                #add due date
                try:
                    duedate = driver.find_element(by=By.XPATH, value="/html/body/form/div[3]/div[3]/div[2]/div[2]/div[5]/div[2]/div/table/tbody/tr[3]/td[9]")
                    tax_date = duedate.text
                    tax_details['DueDate'].append(tax_date)
                except:
                    tax_details['DueDate'].append('NULL')
                
                #assign dict to dataframe
                df = pd.DataFrame(tax_details)
                
                #put df in database
                WriteTaxData(df, curs, conn)
                
            except Exception as e:
                err1 = f'Unable to scrape necessary data for {apn}: {e}'
                note2 = note + err1
                WriteLogData(note2, rdate, apn)
        except Exception as e:
            err2 = f'Unable to find property associated with parcel no. {apn}: {e}'
            note2 = note + err2
            WriteLogData(note2, rdate, apn)
    except Exception as e:
        err3 = f'County website could not be reached: {e}'
        note2 = note + err3
        WriteLogData(note2, rdate, apn)
    
def washoe_func(apn):
    #first, make dictionary to store values
    tax_details = {
            'TaxYear':[],
            'TaxAmnt':[],
            'DueDate':[],
            'Note':[],
            'RetrievalDate':[],
            'APN':[]
        }
    #add RetrievalDate and APN, note to the dictionary in case scraper fails
        #these values can still be used for the log
    #retrieval date to dict
    d1 = date.today()
    rdate = str(d1)
    tax_details['RetrievalDate'].append(rdate)
    #apn to dict
    tax_details['APN'].append(apn)
    #note to dict
    note = 'Washoe '
    tax_details['Note'].append(note)
    
    
    #make sure Selenium can reach the county site
    try:
        #we could use the send key as different variable that could be directly changed
        sendkeyfull = str(apn)
        sendkey = sendkeyfull.replace('-','')
        #now search the apn to see whether it's in the county site
        try:
            #Use the WebDriver to visit Clark County Search URL
            driver.get("https://nv-washoe.publicaccessnow.com/Treasurer/TaxSearch.aspx")
            #set webdriver size to avoid html structure changing
            driver.set_window_position(1124, 1024, windowHandle='current')
            time.sleep(10)

            #rest of the selenium code to get to tax data page
            #ACN form in this webpage has name "txtSearchValue"
            search = driver.find_element(by=By.CLASS_NAME, value="form-control")
            time.sleep(4)
            #Enter in the sample ACN
            search.send_keys(sendkey)
            #Search the ACN
            search.send_keys(Keys.RETURN)
            time.sleep(15)

            # scrape the data and call the inserting function
            try:
                # add tax year
                d1 = datetime.now()
                year = d1.year
                tax_details['TaxYear'].append(year)
                time.sleep(20)

                # add amount due
                xpath_val = '//*[@id="dnn_ctr464_ModuleContent"]/div/payment-bill/div/h2/div[1]/div/span[2]'
                amount_due = driver.find_element(by=By.XPATH, value=xpath_val)
                tax_Due = amount_due.text
                tax_details['TaxAmnt'].append(tax_Due)

                # Add DueDate
                duedate = ''
                tax_details['DueDate'].append(duedate)

                #assign dict to dataframe
                df = pd.DataFrame(tax_details)

                #put df in database
                WriteTaxData(df, curs, conn)
            except Exception as e:
                err1 = f'error: Unable to scrape necessary data for {apn}: {e}'
                note2 = note + err1
                WriteLogData(note2, rdate, apn)
        except Exception as e:
            err2 = f'error: Unable to find property associated with parcel no. {apn}: {e}'
            note2 = note + err2
            WriteLogData(note2, rdate, apn)
    except Exception as e:
        err3 = f'error: County website could not be reached: {e}'
        note2 = note + err3
        WriteLogData(note2, rdate, apn)

#function to add the scraped data to database
def WriteTaxData(df, curs, conn):
    #close the driver
    driver.quit()
    
    #insert the dictionary into the database
    #TaxData table: TaxDataID, TaxYear, TaxAmnt, DueDate, Note, RetrievalDate, APN(FK)
    TY = df.loc[0,'TaxYear']
    if TY == '':
        TY = "NULL"
    else:
        TY = "'{}'".format(TY)
    TA = df.loc[0, 'TaxAmnt']
    N = df.loc[0, 'Note']
    DD = df.loc[0, 'DueDate']
    DD = DD.strip()
    #set duedate to NULL if there are no values for it
    if DD == '':
        DD = "NULL"
    else:
        DD = "'{}'".format(DD)
    #retrieval date can also be created here
    RD = datetime.now()
    RD = RD.strftime('%Y-%m-%d %H:%M:%S')
    #RD = df.loc[0, 'RetrievalDate']
    PN = df.loc[0, 'APN']
    #strip apn of any leading/ending spaces that would mess up the insert
    PN = PN.strip()

    #we wanna see whether there's already tax data for the season that's been pulled
        #and if there is, we wanna update the db to have the new tax data(if there is a diff amount listed on the county site)
    try:
        # select the tax amount from database
        curs.execute(
            "SELECT TaxAmount FROM TaxData WHERE APN = '{}' AND TaxYear = {} AND DueDate = {}".format(PN, TY, DD)
        )
        row2 = curs.fetchall()
        # make it so that if there's tax amount for the apn in the same season, we update the database
        if curs.rowcount > 0:
            if float(row2[0][0]) != TA:
                #update record
                curs.execute(
                "UPDATE TaxData SET TaxAmount = {} WHERE APN = '{}' AND TaxYear = {}".format(TA, PN, TY)
                )
                conn.commit()
        else:
            insert_query = "INSERT INTO TaxData (TaxYear, TaxAmount, DueDate, Note, RetrievalDate, APN) VALUES ({}, {}, {}, '{}', '{}', '{}')".format(TY, TA, DD, N, RD, PN)
            curs.execute(insert_query)
            conn.commit()
        #add successful insert to the log table
        WriteLogData(N, RD, PN)
    except Exception as e:
        N = N+e
        #add unsuccessful insert to the log table
        WriteLogData(N, RD, PN)

#function for adding data to the log table
def WriteLogData(Note, RetrievalDate, APN):
    #close the driver
    driver.quit()
    
    #strip apn of any leading/ending spaces
    PN2 = APN.strip()
    try:
        log_insert_query = "INSERT INTO Log (Note, RetrievalDate, APN) VALUES ('{}', '{}', '{}')".format(Note, RetrievalDate, PN2)
        curs.execute(log_insert_query)
        conn.commit()
        #add info to local log file too
        logging.info(f"Retrieved APN {PN2} Note: {Note}")
    except Exception as e:
        print("ERROR: "+str(e))
        #add info to local log file too
        logging.error("ERROR: "+str(e))

#
#
#
#                                       SETTING UP THE LOOP
#
#
#

# we will be grabbing county id, apn, & parsing func name from the db before scraping
    # get that data from the db & assign it to a df we can loop through
apn_function_dictionary = {"CountyID":[],"APN":[],"ParsingFunction":[]}

#we don't want to scrape apns until 30 days after they've been initially scraped
    #will be using the retrievaldate from BOTH log and taxdata tables
    #so if something's not in the taxdata table that should be there, check for the apn in the log table.
min_days_since_last_scraped = timedelta(30) 
scrape_after = datetime.now() - min_days_since_last_scraped
str_scrape_after = scrape_after.strftime('%Y-%m-%d %H:%M:%S')

#part of the select statement will be seeing whether counties have CAPTCHA on their sites or not
    #the program will be looking at system arguments provided when the loop starts and changing the select statement based off of that
    #if no args are given we'll select all records regardless of CAPTCHA
    #if 0 is given, will only select records with no CAPTCHA
    #if 1 is given will only select CAPTCHA-required properties
captcha_condition = ''
args = sys.argv
if len(args) > 1:
    if args[1] == "0":
        captcha_condition = "AND RequiresCaptcha = 0"
    else:
        captcha_condition = "AND RequiresCaptcha = 1"

#get the countyid, apn, parsingfunction for properties that haven't been scraped yet 
    #& properties that haven't been scraped in the past 30 days
curs.execute("SELECT p.countyID, p.APN, c.ParsingFunction, td.RetrievalDate "+
             "FROM Property AS p "+
             "JOIN County AS c ON p.countyID = c.countyID "+
             "LEFT OUTER JOIN TaxData AS td ON p.APN = td.APN "+ 
             "LEFT OUTER JOIN Log AS lg ON p.APN = lg.APN "+
             "WHERE c.Implemented = 1 AND (td.RetrievalDate IS NULL OR td.RetrievalDate < '{}')".format(str_scrape_after)+
             #the other condition based on CAPTCHA is assigned to the args variable && will be added onto the string
             " AND (lg.RetrievalDate IS NULL OR lg.RetrievalDate < '{}') {}".format(str_scrape_after, captcha_condition)+
             " ORDER BY p.countyID;"
            )
row = curs.fetchone()

#input to close the program
    #any time the file might fail we want to call the closing function
    #also want to call it when the loop runs successfully
def closing_func():
    str(input("Press enter to exit..."))

#append all the gathered rows into the python dictionary so we can loop through
try:
    while row:
        apn_function_dictionary["CountyID"].append(str(row[0]))
        apn_function_dictionary["APN"].append(row[1])
        apn_function_dictionary["ParsingFunction"].append(row[2])
        row = curs.fetchone()
except:
    print('Unable to grab database data to initialize the loop')
    closing_func()

#turn dictionary into dataframe so it'll be easier to loop through
prop_df = pd.DataFrame(apn_function_dictionary)

#create a loop to go through the dict info & get property tax data from those apns
length = len(prop_df.index)
print(f"Number of records selected: {length}")
logging.debug(f"Number of records selected: {length}")
i = 0
prevtime = datetime.now()
records_processed = 0

recs_proc = config.loop_vars['records_processed']
sleep_time = config.loop_vars['sleep_time']

#
#
#
#                                       LOOP
#
#
#

try:
    while i < length:
        #make sure you don't make too many requests in one sitting
        if records_processed == recs_proc:
            break
        
        #activate the WebDriver
            #add options so you don't get weird bluetooth availability errors
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(service=s, options=options)
        
        #grab the apn from the dict
        apn = prop_df.loc[i,'APN']
        #grab scraper name from dict
        pf = prop_df.loc[i, 'ParsingFunction']
        #put the scraper and apn together to call the functions
        strFnToRun="{}(\"{}\")".format(pf,apn)
        print(strFnToRun)
        #add info to log file
        logging.debug(strFnToRun)
        #call the function based on the apn's ParsingFunction we got from the db
        eval(strFnToRun)

        
        #make sure the function waits for at least 15 seconds before making another call
        timenow = datetime.now()
        ntime = timenow - prevtime
        if ntime.total_seconds() > 0 and ntime.total_seconds() < sleep_time:
            time.sleep(15-ntime.total_seconds())
        
        i += 1
        records_processed += 1
        
        prevtime = timenow
        print('-'*50)
    #close the database connection when finished
    curs.close()
    conn.close()

    print("scraper has finished")

    closing_func()
except:
    #failsafe in case the loop isn't able to work
    print(f'Scraper was not able to start.\n Make sure the Chromedriver is installed and that the function has a proper connection to the database, then try again. ')
    closing_func()
