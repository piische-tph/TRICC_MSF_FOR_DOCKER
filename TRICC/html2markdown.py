#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 20 09:34:31 2023

@author: rafael
"""

from markdownify import markdownify as md

def convert(html):
    print(html)
    s = md(html, escape_underscores=True)
    return s
