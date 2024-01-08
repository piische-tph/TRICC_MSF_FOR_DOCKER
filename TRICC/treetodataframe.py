#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 12 13:32:54 2022

@author: rafael
"""
import pandas as pd

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
        except:
            row = {**row, **itemParentRow}
        dfa = pd.DataFrame(row, index = [i])
        i+=1
        df_raw = pd.concat([df_raw, dfa])
        
        # if several pages, there will be duplicate ids:
        df_raw.drop_duplicates(subset='id', ignore_index = True, inplace = True) 
    
    return df_raw