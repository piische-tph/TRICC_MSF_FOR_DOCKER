#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 03:12:32 2023

@author: rafael
"""
class Foo():
     def __init__(self):
             self.value = 0
     def __str__(self):
             return str(self.value)
     def __repr__(self):
             return str(self.value)


f = Foo()
print(f)

foo = (f,f)

print(foo)

f.value=999

print(foo)



#############33
def list_changer(input_list):
    input_list[0] = 10

    input_list = list(range(1, 10))
    print(input_list)
    input_list[0] = 10
    print(input_list)
    
    return input_list

test_list = [5, 5, 5]
list_changer(test_list)
[1, 2, 3, 4, 5, 6, 7, 8, 9]
[10, 2, 3, 4, 5, 6, 7, 8, 9]
print(test_list)
[10, 5, 5]

input_list=[1,1,1]
list_changer(input_list)
print(input_list)
input_list = list_changer(input_list)
print(input_list)