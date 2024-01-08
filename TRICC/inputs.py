#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 28 20:09:04 2022

@author: rafael
Function that help reading the xml drawio
"""

from lxml import etree
import pandas as pd

# store -r form_id testing multiple_labels summaryfile drugsfile cafile inputfile_dx inputfile_tt dxfile ttfile output form_title input_trans updated_trans diagnose_order

def parse_drawio(inputfile):
    '''Function to parse the drawio-drawing into an objects
    '''
    data = etree.parse(inputfile) # 'data' is a wrapper for the entire tree
    root = data.getroot() # get the name of the highest element of the tree, put it into the variable 'root'
    pages = root.findall('.//diagram') # gets all the tabs of the document

    objects = [] # all objects of all pages combined

    for page in pages:
        print('Page ID:', page.attrib['id'], 'Page name:', page.attrib['name'])
        objects_in_page = page.findall('.//mxGraphModel//mxCell')
        objects = objects + objects_in_page
        
    return objects


def treetodataframe(objects):
    i=0
    df_raw=pd.DataFrame()
    
    for item in objects:
        row = item.attrib # get attributes of 'mxCell' 
        itemParent = item.getparent()
        itemParentRow = itemParent.attrib # get all attributes of its parent
        try: 
            itemGeometry = item.find('.//mxGeometry') # get the Geometry, if it exists
            itemGeometryRow = itemGeometry.attrib
            row = {**row, **itemParentRow, **itemGeometryRow}
            tabname = item.xpath("./ancestor::diagram")[0].attrib['name'] # get tab name in diagram
            row['activity'] = tabname
        except:
            row = {**row, **itemParentRow}
        dfa = pd.DataFrame(row, index = [i])
        i+=1
        df_raw = pd.concat([df_raw, dfa])
        
        # if several pages, there will be duplicate ids:
        df_raw.drop_duplicates(subset='id', ignore_index = True, inplace = True) 
    
    return df_raw
