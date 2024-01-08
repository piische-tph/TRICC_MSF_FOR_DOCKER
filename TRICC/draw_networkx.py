#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 16:38:29 2023

@author: rafael
"""

import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_pydot import graphviz_layout

# this function is optional
# just moves the node labels on the plot so they don't overlap the lines 
def nudge(pos, x_shift, y_shift):
    return {n:(x + x_shift, y + y_shift) for n,(x,y) in pos.items()} 

# start with a directed graph
dag = nx.DiGraph()

dag.add_edges_from(
    [
        ('root', 'a'), 
        ('a', 'b'),
        ('a', 'c'),
        ('b', 'd'),
        ('d', 'e'),
        ('d', 'f')
    ]
)

# plot the graph
pos = graphviz_layout(dag, prog="dot")
pos_labels = nudge(pos, -5, 15)

fig = plt.figure(figsize=(8, 6))
ax = plt.subplot(1, 1, 1)
plt.margins(0.1)

nx.draw(
    dag, 
    pos=pos,
    ax=ax,
    with_labels=False,
    arrows=Tr