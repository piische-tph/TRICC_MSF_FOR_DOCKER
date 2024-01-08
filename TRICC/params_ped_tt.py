#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 10:02:12 2023

@author: rafael
"""

### General
form_id = 'ped'
form_title = 'Ped'
htmlcontent = True # whether the diagram  contains html in the content of objects
platform = 'cht'
testing = False
context_params_from_facility=True
mhsplit = False  # whether several nodes are combined into 1 (multiheadline split)
interrupt_flow = True
activity = 'treatment'

### Input Streamlit webapp folder
folder = '/app/'
resource_folder = 'resources/'
inputfile_dx = folder+'uploaded_files/dx.drawio'  # inputfile for jupyter notebook diagnostic
inputfile = folder+'uploaded_files/tt.drawio' # inputfile for tricc-graph tt
diagnosis_order = folder+'uploaded_files/diagnosis_order.csv'
input_trans = folder+'uploaded_files/ped_fr.xlsx'

### Resources
cafile = resource_folder+'ca.xlsx'
summaryfile = resource_folder+'summary.xlsx'

### Output
output_xls = folder + 'tt.xlsx'
output = folder + form_id + '.xlsx'

### Input TRICC Repo folder
repo_folder = '/app/TRICC/'
media_folder = repo_folder+'media/images/'
drugsfile = repo_folder+'medications_zscores.xlsx'
updated_trans = repo_folder+'ped_fr_newest.xlsx'
headerfile = repo_folder+'formheader_cht.xlsx'
headerfile_pause = repo_folder+'formheader_cht_pause.xlsx'
breakpoints = repo_folder+'breakpoints.csv'