#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 08:53:26 2023

@author: rafael
Parameters for Almanach Somalia
"""

from dotenv import load_dotenv
import os

load_dotenv(override=True)

form_id = os.getenv('form_id')
breakpoints = os.getenv('breakpoints')
interrupt_flow = bool(os.getenv('interrupt_flow'))