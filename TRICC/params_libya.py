#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 08:53:26 2023

@author: rafael
Parameters for Almanach Lybia TT
"""

folder = '/home/rafael/Documents/git/Almanach-Libya/form/'
inputfile_dx = folder+'dx.drawio'
inputfile_tt = folder+'tt.drawio'
diagnosis_order = folder+'diagnosis_order.csv'
drugsfile = 'medications_zscores.xlsx'
cafile = folder+'ca.xlsx'
summaryfile = folder+'summary.xlsx'
form_id = 'almlyb'
output_xls_tt = folder + form_id+ '_tt.xlsx'  # for treatment
output_xls = folder + form_id+ '.xlsx' # for complete form
output_xml = folder + 'tt.xml'
output_commcare = folder + 'tt_commcare.xml'  # if the platform is commcare, we will make a commcare conform xform file
form_title = 'Almanach Lybia'
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
activity = 'treatment'
