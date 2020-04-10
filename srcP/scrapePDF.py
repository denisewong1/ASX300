import io

import urllib.request
import requests
# convert restricted url
def download_ASX_pdf(restricted_url):
    response = urllib.request.urlopen(url)
    data = response.read().decode('utf-8')
    restricted_url = re.findall(' value=\"(.*?\.pdf)\" ',data) # find all things ending with pdf
    newurl = 'https://www.asx.com.au' + restricted_url[0]
    response = requests.get(newurl)
    tempfile = xDir_Src + "/temp.pdf"
    with open(tempfile, 'wb') as f:
        f.write(response.content)
    return(tempfile)


# scraping using pyPDF2 - good for documents which have been converted from text to pdf first
import PyPDF2
def scrapePDF_pypdf2(xfilename):
    # uses pyPDF2
    pdfFileObj = open(xfilename, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)   # pdf reader object

    totalPageNumber = pdfReader.numPages
    documentInfo = pdfReader.documentInfo
    currentPageNumber = 0
    text = ''
    while(currentPageNumber < totalPageNumber):
        #print('reading page ',currentPageNumber+1)
        pdfPage = pdfReader.getPage(currentPageNumber)
        text = text + pdfPage.extractText()
        currentPageNumber += 1
        
    # if we want to retain lines space
    text = text.replace('\n','').replace('\b','').encode('ascii',errors='ignore').decode('utf-8')
    # return(documentInfo,totalPageNumber,text)
    return(text)
 
    
# scraping with pdfminer3 - removes all newlines
# https://stackoverflow.com/questions/56494070/how-to-use-pdfminer-six-with-python-3
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import PDFPageAggregator
from pdfminer3.converter import TextConverter
def scrapePDF_pdfminer3(xfilename):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle)
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    with open(xfilename, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=False):
            page_interpreter.process_page(page)
    text = fake_file_handle.getvalue()
    
    # close open handles
    converter.close()
    fake_file_handle.close()
    
    text = text.replace('For personal use only\x0c','').replace('\x0c','')
    return(text)