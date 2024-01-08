#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 22:58:20 2023

@author: rafael
"""
# enumerate

def say(name='Default'):
    print(f'Hello {name}')
    
say()

def check_even_list(num_list):
    
    for number in num_list:
        if number % 2 == 0:
            return True
        else:
            pass
        
num_list = [1,2,3,4,5]
num_list2 = [1,3,5]

check_even_list(num_list)
print('next')
check_even_list(num_list2)


# return breaks the function, this won't work
def check_even_list2(num_list):
    
    for number in num_list:
        if number % 2 == 0:
            return True
        else:
            return False

# this works:
def check_even_list3(num_list):
    
    for number in num_list:
        if number % 2 == 0:
            return True
        else:
            pass
    return False

# functions can have several return statemetns

def get_prime_numbers(x):
    
    # check if input is 0 or 1
    if x < 2:
        return 0

    ##########
    # 2 or greater
    ############
    # Store prime numbers below x
    primes = [2]
    
    i = 3
    
    while i <=x:
        # check if i is prime
        for y in range(3,i,2):
            if i%y == 0:   # no rest, so i is not prime
                i += 2 
                break
        else:
            primes.append(i)
            i +=2
    
    return primes
                
# lambda function are not referenced, they are for one useage only and never to be used again
# to be used with map and filter function

def square(num):
    return num**2

my_nums = [1,2,3,4,5]

# map generates an interator

for item in map(square, my_nums):
    print(item)
    
list(map(square, my_nums))


# filter filters with a function that returns True or False
def check_even(num):
    return num%2 == 0

mynums=[1,2,3,4,5,6]

filter(check_even, mynums)

list(filter(check_even, mynums))

# now we go hard on lambda functions!

def square(num): return num ** 2

# convert that into lambda
lambda num: num ** 2

# assign lambda function to variable
square = lambda num: num ** 2
square(2)



map(lambda num: num**2, my_nums)

list(filter(lambda num: num%2==0, mynums))

# grab  first character of a list
names = ['Hugo', 'Anton', 'Berta']
list(map(lambda name:name[0], names))

# complex functions become unreadable when converting into lambda expressions