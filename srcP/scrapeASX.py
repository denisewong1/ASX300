import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
from pandas.compat import StringIO
import os
from io import StringIO
import requests
from urllib.request import Request, urlopen
import urllib.parse, urllib.error
from urllib.request import build_opener, HTTPCookieProcessor
from bs4 import BeautifulSoup
import shutil
from yahoo_historical import Fetcher

import urllib.request
import requests
import docx2txt
from glob import glob
import re
import win32com.client as win32
from win32com.client import constants

#import re
#import tempfile

## Scrape all data by year - can be used daily
def scrapeASX_AllbyYear(xYear,xDirectory,lstCode) :
    dfASXAnnTitle = lstASXAnnouncements(xYear,xDirectory,lstCode)
    dfASXPrice = lstASXPrice(xYear,xDirectory,lstCode)
    dfASXDividends = lstASXDividends(xYear,xDirectory,lstCode)
    dfASXSplits = lstASXSplits(xYear,xDirectory,lstCode)
    dfASXShortInt = lstASXShortint(xYear,xDirectory) # gets upset if we do too many requests at once


## Scrape ASX300 Index
def scrapeASX_Index(xYear):
    mainurl = "https://www.asx300list.com/uploads/csv/"
    header = {'User-Agent':'Chrome/76.0.3809.132'}
    ASX_Index = pd.DataFrame([])
    for xMonth in range(0,12) :
        xDate = date(xYear,xMonth+1,1)
        xToday = date.today() - datetime.timedelta(days=7)
        length = 1024
        if (xDate < xToday) :
            url = mainurl + str(xYear) + str(xDate.strftime('%m')) + "01-asx300.csv"
            #filename = str(xYear) + str(xDate.strftime('%m')) + "01-asx300.csv"
            filename = "asx300.csv"
            try:
                req = Request(url, headers=header)
                with open(filename, 'wb') as writer:
                    request = urlopen(req, timeout=3)
                    shutil.copyfileobj(request, writer, length)
            except Exception as e:
                print('File cannot be downloaded:', e)
            finally:
                #print('File downloaded with success!')
                df = pd.read_csv(filename,skiprows=[0],usecols=[0,1,2,3,4],header=0)
                df['Date'] = xDate
                ASX_Index = pd.concat([ASX_Index, df], ignore_index=True)
                os.remove(filename)
    return(ASX_Index)


## Make Master list of stocks and save to xdirectory
def lstASXIndex(xYearStart,xYearEnd,xdirectory):  

    dfASXIndex = pd.DataFrame([])
    for xYear in range(xYearStart,xYearEnd) :
        xASXIndex = scrapeASX_Index(xYear)   #xASXIndex = func_scrape.scrapeASX_Index(xYear)
        dfASXIndex = pd.concat([dfASXIndex,xASXIndex], axis=0)
    xfilename = xdirectory + "/ASXIndex.csv"
    dfASXIndex.to_csv(xfilename, encoding='utf-8', index=False)
    return(dfASXIndex)


## Scrape ASX Announcements from ASX website
def scrapeASX_announcements(xCode,xYear):
    mainurl = "https://www.asx.com.au/asx/statistics/announcements.do?by=asxCode&asxCode="
    url = mainurl + xCode + "&timeframe=Y&year=" + str(xYear)  # by year
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')
    ## start scraping here
    tags = soup("td")
    xcount = 0
    lstDate = []
    lstTime = []
    lstTitle = []
    lstHref = []
    for tag in tags:
        if (tag is None) : continue
        if (xcount%3 == 0) :
            xdate = tag.get_text().split()[0]
            xtime = tag.get_text().split()[1] + ' ' + tag.get_text().split()[2]
        if (xcount%3==2) :
            xtitle = tag.get_text().replace('\t','').replace('\r','').split('\n\n')[1]
            xhref = tag.find('a').get('href')
            xrow = int(xcount // 3)
            lstTime.append(xtime)
            lstDate.append(xdate)
            lstTitle.append(xtitle)
            lstHref.append(xhref)
        xcount +=1
    ASX_announcements = pd.DataFrame({'Date':lstDate,'Time':lstTime,'Title':lstTitle,'Link':lstHref})
    ASX_announcements['Code'] = xCode
    return(ASX_announcements)


## Make Master list of announcements and save to xdirectory
def lstASXAnnouncements(xYear,xdirectory,lstCode):  
    dfASXAnnouncements = pd.DataFrame([])
    for xCode in lstCode:
        xASXAnnouncements = scrapeASX_announcements(xCode,xYear)
        dfASXAnnouncements = pd.concat([dfASXAnnouncements,xASXAnnouncements], axis=0)
    xfilename = xdirectory + "/ASXAnnTitle_" + str(xYear) + ".csv"
    dfASXAnnouncements.to_csv(xfilename, encoding='utf-8', index=False)
    return(dfASXAnnouncements)


## https://www.stockmetric.net/asx-indices/
## dictionary of codes to sectors
dictSector = {'XJO' : 'ASX200', 
              'XKO' : 'ASX300', 
              'AXJOA' : 'ASX200 Accumulation', 
              'AXKOA' : 'ASX300 Accumulation', 
              'XSJ' : 'Consumer Staples', 
              'XDJ' : 'Consumer Discretionary', 
              'XMJ' : 'Materials', 
              'XRE' : 'Real Estate', 
              'XIJ' : 'Information Technology', 
              'XUJ' : 'Utilities', 
              'XNJ' : 'Industrials', 
              'XFJ' : 'Financials', 
              'XHJ' : 'Health Care', 
              'XEJ' : 'Energy', 
              'XTJ' : 'Telecommunication Services',
              'XPJ' : 'A-Reit',
              'XFJ' : 'Financial',
              'XXJ' : 'Financial xREIT', 
              'XJR' : 'Resources', 
              'XGD' : 'Gold',
              'XMM' : 'Metals and Mining',
              'XBK' : 'Banks',
              'XET' : 'Emerging Companies',
              'XVI' : 'VIX Index',
              'USD' : 'US Dollar ETF',
              'POU' : 'British Pound ETF', 
              'EEU' : 'Euro ETF'}


## get list of sectors
def lstASXSector() :
    lstSector = pd.DataFrame(list(dictSector.items()), columns=['Code', 'Sector'])
    #lstSector = pd.DataFrame({'Code' : dictSector.keys() , 'Sector' : dictSector.values() })
    return(lstSector)


## scrape stock price by year
## Scrape ASX prices from Yahoo
## Documentation - https://github.com/AndrewRPorter/yahoo-historical/blob/master/yahoo_historical/fetch.py
def scrapeASX_price(xCode,xYear):
    xDateStart = [xYear,1,1]
    xDateEnd = [xYear,12,31]
    try :
        ASX_price = Fetcher(xCode+".AX", xDateStart, xDateEnd).get_historical()
        ASX_price['Code'] = xCode
    except Exception as e:
        ASX_price = pd.DataFrame()
    return(ASX_price)


## Make Master list of prices by year and save to xdirectory
def lstASXPrice(xYear,xdirectory,lstCode):  
    dfASXPrice = pd.DataFrame([])
    for xCode in lstCode:
        # print(xCode)
        xASXPrice = scrapeASX_price(xCode,xYear)
        if not xASXPrice.empty:
            dfASXPrice = pd.concat([dfASXPrice,xASXPrice], axis=0)
    xfilename = xdirectory + "/ASXPrice_" + str(xYear) + ".csv"
    dfASXPrice.to_csv(xfilename, encoding='utf-8', index=False)
    return(dfASXPrice)


## scrape dividends for single stock
def scrapeASX_dividends(xCode,xYear):
    xDateStart = [xYear,1,1]
    xDateEnd = [xYear,12,31]
    try :
        ASX_dividends = Fetcher(xCode+".AX", xDateStart, xDateEnd).getDividends()
        ASX_dividends['Code'] = xCode
    except Exception as e:
        ASX_dividends = pd.DataFrame()        
    return(ASX_dividends)


## Make Master list of dividends by year and save to xdirectory
def lstASXDividends(xYear,xdirectory,lstCode):  
    dfASXDividends = pd.DataFrame([])
    for xCode in lstCode:
        # print(xCode)
        xASXDividends = scrapeASX_dividends(xCode,xYear)
        if not xASXDividends.empty:
            dfASXDividends = pd.concat([dfASXDividends,xASXDividends], axis=0)
    xfilename = xdirectory + "/ASXDividends_" + str(xYear) + ".csv"
    dfASXDividends.to_csv(xfilename, encoding='utf-8', index=False)
    return(dfASXDividends)


## scrape stock split for single stock
def scrapeASX_splits(xCode,xYear):
    xDateStart = [xYear,1,1]
    xDateEnd = [xYear,12,31]
    try :
        ASX_splits = Fetcher(xCode+".AX", xDateStart, xDateEnd).getSplits()
        ASX_splits['Code'] = xCode
    except Exception as e:
        ASX_splits = pd.DataFrame()        
    return(ASX_splits)


## Make Master list of dividends by year and save to xdirectory
def lstASXSplits(xYear,xdirectory,lstCode):  
    dfASXSplits = pd.DataFrame([])
    for xCode in lstCode:
        # print(xCode)
        xASXSplits = scrapeASX_splits(xCode,xYear)
        if not xASXSplits.empty:
            dfASXSplits = pd.concat([dfASXSplits,xASXSplits], axis=0)
    xfilename = xdirectory + "/ASXSplits_" + str(xYear) + ".csv"
    dfASXSplits.to_csv(xfilename, encoding='utf-8', index=False)
    return(dfASXSplits)


## Scrape ASX Code Short Interest
def lstASXShortint(xYear,xdirectory):
    mainurl = "https://asic.gov.au/Reports/Daily/"
    ASX_shortint = pd.DataFrame([])
    for xMonth in range(0,12) :
        d0 = datetime.datetime(year=xYear, month=xMonth+1, day=1)
        d1 = d0 + relativedelta(months=1)
        nDays = (d1 - d0).days
        for xDay in range(0,nDays) :
            xDate = d0 + relativedelta(days=xDay)
            if (xDate.weekday()<5) :
                url = mainurl + str(xYear) + "/" + str(xDate.strftime('%m')) + "/RR" + \
                    str(xYear) + str(xDate.strftime('%m')) + str(xDate.strftime('%d')) + "-001-SSDailyAggShortPos.csv"
                r = requests.get(url,timeout=5)
                if (r.status_code == 200) :
                    xdownload = r.text
                    df = pd.read_csv(pd.compat.StringIO(xdownload), skiprows = 1, header = None, sep=r'\t', engine='python')
                    df['Date'] = xDate
                    ASX_shortint = pd.concat([ASX_shortint, df], ignore_index=True,sort=False)
    ASX_shortint.columns = ['Name', 'Code', 'Short Units', 'Total Units','Short Percent','Date']
    xfilename = ''.join([xdirectory, "/ASXShortInt_", str(xYear), ".csv"])
    ASX_shortint.to_csv(xfilename, encoding='utf-8', index=False)
    return(ASX_shortint)


## Scrape list of standard ASX forms
def lstASXforms(xdirectory) :
    opener = build_opener(HTTPCookieProcessor())
    url = "https://www.asxonline.com/companies/html/ASICForms.html"
    html = opener.open(url)
    soup = BeautifulSoup(html, 'html.parser')
    tags = soup.select("td")
    lstTitle = []
    lstHref = []
    for tag in tags:
        xtitle = tag.get_text()
        if not (tag.find('a')) :
            lstTitle.append(xtitle)
        for c in tag.findAll('a') :
            if (c.get('href', '')).startswith('/'):
                xhref = 'https://www.asxonline.com' +c.get("href")
                lstHref.append(xhref)
    dfASXforms = pd.DataFrame({'Title':lstTitle,'Link':lstHref})
    xfilename = xdirectory + "/ASXForms.csv"
    dfASXforms.to_csv(xfilename, encoding='utf-8', index=False)
    return(dfASXforms)


## Make Master list of dividends by year and save to xdirectory
## scrape ASX standard forms
def scrapeASXform(url,formid,xdirectory):
    file_extension = url.split('.')
    file_extension = file_extension[len(file_extension)-1].lower()
    # print('file type ' + str(formid).zfill(3) + ' ' + file_extension)
    response = requests.get(url)
    file_in = xdirectory + "/ASXForm" + str(formid).zfill(3) + "." + file_extension
    file_out = xdirectory + "/ASXForm" + str(formid).zfill(3) + ".txt" 
    with open(file_in, 'wb') as f:
        f.write(response.content)
    # convert .doc to .docx files    
    if file_in.endswith('.doc') :
        saveasdocx(formid,xdirectory)
        os.remove(xdirectory + "/ASXForm" + str(formid).zfill(3) + ".doc") # remove temp file
        file_in = file_in + 'x'
    # convert .docx to .txt files
    if file_in.endswith('.docx'):
        text = docx2txt.process(file_in)  #text = textract.process(file_in)
        text = text.encode('utf-8')
        with open(file_out,'wb') as f:
            f.write(text)
        os.remove(xdirectory + "/ASXForm" + str(formid).zfill(3) + ".docx")  # remove temp file
    return(text)


## convert .doc to .docx files
def saveasdocx(formid,xdirectory):
    file_in = xdirectory + "/ASXForm" + str(formid).zfill(3) + ".doc"
    file_out = xdirectory + "/ASXForm" + str(formid).zfill(3) + ".docx"
    word = win32.gencache.EnsureDispatch('Word.Application')
    doc = word.Documents.Open(file_in)
    doc.Activate ()
    word.ActiveDocument.SaveAs(file_out, FileFormat=constants.wdFormatXMLDocument)
    doc.Close(False)