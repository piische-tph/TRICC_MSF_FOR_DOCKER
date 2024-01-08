# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 09:21:11 2022

@author: kluera
"""

from bs4 import BeautifulSoup
from html import escape
from html.parser import HTMLParser
from unicodedata import normalize as uninorm
import re
from html2text import html2text
import unicodedata

import warnings
warnings.filterwarnings("ignore")

class HTMLFilter(HTMLParser):
    text = ""
    def handle_data(self, data):
        self.text += data

def html2plain(data): 
    f = HTMLFilter()
    f.feed(data)
    return f.text

def clean_name(s):
    s = html2plain(s)
    s = s.rstrip()
    s = s.lstrip()
    s = s.lower()
    s = s.replace(' ','')
    return s

# removes html and outputs a list where each item is a line of text from the box
def clean_multi_headings(string):
    text = html2text(string)
    text = text.strip('\n')
    text = text.split('\n')
    text = [i.strip(' ') for i in text if i]
    return text

def remove_html(string):
    text = html2text(string) # retrieve pure text from html
    text = text.strip('\n') # get rid of empty lines at the end (and beginning)
    text = text.split('\n') # split string into a list at new lines
    text = '\n'.join([i.strip(' ') for i in text if i]) # in each element in that list strip empty space
    text = text.replace('\n',' ') # and delete empty lines
    return text

def remove_html_value(string):
    text = string.strip('\n') # get rid of empty lines at the end (and beginning)
    text = text.split('\n') # split string into a list at new lines
    text = '\n'.join([i.strip(' ') for i in text if i]) # in each element in that list strip empty space
    return text

def _remove_all_attrs(soup):
    for tag in soup.find_all(True): 
        tag.attrs = {}
    return soup


def _remove_tag(soup,tag):
    soup = soup.find('div')
    for elem in soup.find_all(tag):
        elem.unwrap()
    return soup

def _replace_tag(soup, tag, newtag):
    for elem in soup.find_all(tag):
        elem.name = newtag
    return soup

def _clean_fup(filename):
    with open(filename, encoding ='ISO-8859-15', mode='r') as fp:
        soup = BeautifulSoup(fp, 'html.parser')  
    
    for elem in soup.find_all("span", class_= "GramE"): # remove useless MS Word span-class
        elem.unwrap()
    
    soup = _remove_all_attrs(soup)    
    
    while True: 
        weirdoMSstuff = soup.find('o:p')  # oh yes, MS is so bad and rewrites standard html tags out of incompetence, ending up being incompatible to the rest of the world
        if not  weirdoMSstuff:
            break
        weirdoMSstuff.name = 'p'

    # get rid of empty tags because MS has clubbered the file with superficial stuff: 
    for x in soup.find_all():
        if len(x.get_text(strip=True)) == 0:
            x.extract()
    # soup = _remove_tag(soup,'span') # keep span for font-color
    soup = soup.find('div')
    htmlstring = soup.prettify()
    htmlstring = htmlstring.replace('<div>','')
    htmlstring = htmlstring.replace('</div>','')
    htmlstring = htmlstring.replace('\n',' ')
    htmlstring = ' '.join(htmlstring.split())
    return soup, htmlstring


def remove_weirdo_Microsoft_junk(soup):
    for elem in soup.find_all("span", class_= "GramE"): # remove useless MS Word span-class
        elem.unwrap()
    
    soup = _remove_all_attrs(soup)    
    
    while True: 
        weirdoMSstuff = soup.find('o:p')  # oh yes, MS is so bad and rewrites standard html tags out of incompetence, ending up being incompatible to the rest of the world
        if not  weirdoMSstuff:
            break
        weirdoMSstuff.name = 'p'

    # get rid of empty tags because MS has clubbered the file with superficial stuff: 
    for x in soup.find_all():
        if len(x.get_text(strip=True)) == 0:
            x.extract()
            
    return soup
    



def clean_html(s):
    soup = BeautifulSoup(s, 'html.parser')  
    
    # delete empty tags
    for x in soup.find_all():
        if len(x.get_text(strip=True)) == 0:
            x.decompose()
            
    # unwrap font tag
    for x in soup.find_all("font"):
        x.unwrap()
        
    # rename tags
    for x in soup.find_all("b"):
        x.name = 'strong'
    
    # delete all attributes except color (set to brand color)
    for tag in soup.find_all(True): 
        if 'style' in tag.attrs:
            if 'color:' in tag.attrs['style']:
                s = tag.attrs['style']
                try:
                    s = re.search('(?<!-)color(.+?);',s).group(0)
                except AttributeError:
                    tag.attrs = {}
                else:
                    tag.attrs = {'style' : s}
            else:
                tag.attrs = {}
        
    # unwrap span tags without attributes
    for x in soup.find_all("span"):
        if x.attrs == {}:
            x.unwrap()
       
    # delete all attributes except color (set to brand color)
    for tag in soup.find_all(True): 
        if 'style' in tag.attrs:
            if 'color:' in tag.attrs['style']:
                s = tag.attrs['style']
                try:
                    s = re.search('(?<!-)color(.+?);',s).group(0)
                except AttributeError:
                    tag.attrs = {}
                else:
                    tag.attrs = {'style' : s}
            else:
                tag.attrs = {}
        
    # unwrap span tags without attributes
    for x in soup.find_all("span"):
        if x.attrs == {}:
            x.unwrap()
    
    #htmlstring = soup.prettify()
    htmlstring = uninorm('NFKD', str(soup))
    return htmlstring


def cleanhtml_fromfile(htmlpath):
    '''Function to read the string of an html file, the way it is written for Somalia, split of the Somali translation, and clean the html to make it fit for CHT'''
    try:
        with open (htmlpath, 'r') as f:
            contents = f.read()
            contents = re.sub('\n', ' ', contents)
            contents = re.sub('\t', '', contents)
            contents = re.sub('<br/>', '</p><p>', contents)
            contents = re.sub('<br>', '</p><p>', contents)
            soup = BeautifulSoup(contents, 'lxml')
            # unwrap font tag
            for x in soup.find_all("font"):
                x.unwrap()
                
            # rename tags
            for x in soup.find_all("b"):
                x.name = 'strong'
        
            # do this only if there are translations in the same file
            if soup.find(lambda tag:tag.name=='i' and  'Do not write above this' in tag.text):
                translation_cut = soup.find(lambda tag:tag.name=='i' and  'Do not write above this' in tag.text)
                for e in translation_cut.find_all_next():
                    e.clear()
                translation_cut.extract()
        
            # delete empty tags -> this removes all the </br> also!
            for x in soup.find_all():
                if len(x.get_text(strip=True)) == 0:
                    x.decompose()
        
            # unwrap span tags without attributes
            for x in soup.find_all("span"):
                if x.attrs == {}:
                    x.unwrap()
        
            # delete all attributes except color (set to brand color)
            for tag in soup.find_all(True): 
                if 'style' in tag.attrs:
                    if 'color:' in tag.attrs['style']:
                        s = tag.attrs['style']
                        try:
                            s = re.search('(?<!-)color(.+?);',s).group(0)
                        except AttributeError:
                            tag.attrs = {}
                        else:
                            tag.attrs = {'style' : s}
                    else:
                        tag.attrs = {}
                        
            s = ' '.join(str(x) for x in soup.body.contents)
    
            s = unicodedata.normalize('NFKD', s)
            
            s = re.sub(r'(-)\1+', r'', s) # get rid of the --------
            s = re.sub('<p></p>', '', s)
            s = re.sub('<p> </p>', '', s)
        return s

    except:
        print('On conversion to markdown, file', htmlpath, 'not found.')  
    
def make_green_font(x):
    soup = BeautifulSoup(x, 'html.parser')
    for elem in soup.find_all('span'):
        elem['style'] = 'color:#70AD47'
        
    htmlstring = soup.prettify(formatter="minimal")
    #htmlstring = str(soup)
    htmlstring = escape(htmlstring)

    return htmlstring
    
    
def make_red_font(x):
    soup = BeautifulSoup(x, 'html.parser')
    for elem in soup.find_all('span'):
        elem['style'] = 'color:#AD4747'
        
    htmlstring = soup.prettify()
    return htmlstring    

def make_green_background(x):
    x = '<div style="background-color:#70AD47;">' + x + '</div>'

    return x

# color:#70AD47'
