#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 18 22:50:44 2023

@author: rafael
Parameters for Almanach Libya Diagnostic
"""

folder = '/home/rafael/Documents/git/Almanach-Libya/form/'
media_folder = folder+'media/images/'
inputfile = folder+'dx.drawio'
diagnosis_order = folder+'diagnosis_order.csv'
drugsfile = 'medications_zscores.xlsx'
cafile = folder+'ca.xlsx'
summaryfile = folder+'summary.xlsx'
form_id = 'almlib'
output_xls = folder + form_id+ '_dx.xlsx'
output_xml = folder + '_dx.xml'
output_commcare = folder + '_dx_commcare.xml'  # if the platform is commcare, we will make a commcare conform xform file
form_title = 'Almanach Libya'
htmlfolder = folder + 'htm_files/' # folder where the html files are stored (that will replace the text in notes)
htmlcontent = False # whether the diagram contains html in the content of objects
platform = 'cht'
headerfile = folder+'formheader_cht.xlsx'
headerfile_pause = folder+'formheader_cht_pause.xlsx'
testing = False
context_params_from_facility=False
mhsplit = True  # whether several nodes are combined into 1 (multiheadline split)
input_trans = folder + 'translation.xlsx'
updated_trans = folder + 'to_be_translated.xlsx'
interrupt_flow = False
activity = 'diagnostic'