#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 20 13:48:01 2023

@author: rafael
"""

import os    
from chardet import detect

# get file encoding type
def get_encoding_type(filename):
    with open(filename, 'rb') as f:
        rawdata = f.read()
    return detect(rawdata)['encoding']

def encodeUTF8(filename):
    '''function that encodes a textfile with unknown encoding into UTF-8. The result will be saved on the input filename'''
    try:
        from_codec = get_encoding_type(filename)
        # add try: except block for reliability
        try: 
            with open(filename, 'r', encoding=from_codec) as f, open(filename+'l', 'w', encoding='utf-8') as e:
                text = f.read() # for small files, for big use chunks
                e.write(text)
        
            os.remove(filename) # remove old encoding file
            os.rename(filename+'l', filename) # rename new encoding
        except UnicodeDecodeError:
            print('Decode Error')
        except UnicodeEncodeError:
            print('Encode Error')
            
        
    except IOError:
        print('File', filename, 'not found')
