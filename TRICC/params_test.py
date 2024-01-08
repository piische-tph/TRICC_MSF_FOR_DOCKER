#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 08:53:26 2023

@author: rafael
Parameters for Almanach Somalia
"""

folder = '/home/rafael/Documents/git/almsom/diagrams/'
media_folder = folder+'media/images/'
inputfile = folder+'tt_test.drawio'
diagnosis_order = folder+'diagnosis_order.csv'
drugsfile = 'medications_zscores.xlsx'
cafile = folder+'ca.xlsx'
summaryfile = folder+'summary.xlsx'
form_id = 'almsom'
output_xls_tt = folder + form_id+ '_tt.xlsx'
output_xls = folder + form_id+ '.xlsx' # for complete form, required in merge DX + TT script
output_xml = folder + 'tt.xml'
output_commcare = folder + 'tt_commcare.xml'  # if the platform is commcare, we will make a commcare conform xform file
form_title = 'Almanach Somalia'
htmlfolder = '/home/rafael/Documents/git/almsom/html_en/' # folder where the html files are stored (that will replace the text in notes)
htmlcontent = True # whether the diagram contains html in the content of objects
platform = 'commcare'
headerfile = folder+'formheader_commcare.xlsx'
headerfile_pause = folder+'formheader_cht_pause.xlsx' # for CHT tasks are used
testing = False # adds node ID to the text shown to user
context_params_from_facility=False # if False, it will make a selector for context parameters
mhsplit = False  # whether several nodes are combined into 1 (multiheadline split as used in Somalia TT)
input_trans = folder + 'translation.xlsx' # MSF French translation file input
updated_trans = folder + 'to_be_translated.xlsx' # MSF output translation file with new strings
interrupt_flow = False  # whether a PAUSE is implemented
activity = 'treatment' # if treatment, il will contract nodes and sort differently as DX
