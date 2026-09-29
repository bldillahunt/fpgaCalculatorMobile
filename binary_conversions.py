import struct
import time
from fixedpoint import FixedPoint
import math
import numpy as np
from dataclasses import dataclass
from typing import List, Literal
from binary_support import twos_complement_bin_rational, real_to_binary, hex_to_binary, int_list_to_binary_string, twos_complement, binary_string_to_int_list, list_to_string, remove_msbs
from decimal import Decimal

debug_enable = False

# Wrapper for the real-to-binary converter that handles negative numbers	
def real_to_twos_comp_binary(n, default_int_size, default_frac_size):
	n_binary = real_to_binary(n, default_frac_size)
	
	if (float(n) < 0):
		binary_list = twos_complement_bin_rational(n_binary)
		binary_string = int_list_to_binary_string(binary_list, len(binary_list))
		n_binary_2s_comp = "".join(binary_string)
	else:
		n_binary_2s_comp = n_binary
		
	return n_binary_2s_comp

# Converts a hexadecimal string to a binary string
def hexadecimal_to_binary(n, integer_size, fraction_size, lookup_table):
	if (len(n) > (integer_size + fraction_size)) or ((integer_size % 4) != 0) or ((fraction_size % 4) != 0):
		return "ERROR"
	else:
		binary_string = []
		
		for i in range(0, len(n)):
			binary_string.append(hex_to_binary(n[i], lookup_table))

		single_binary_string = "".join(binary_string)

		integer_string = single_binary_string[:integer_size]
		fraction_string = single_binary_string[integer_size:]
		
#		print(binary_string, single_binary_string, integer_string, fraction_string)
		
		return integer_string + '.' + fraction_string

# Converts an IEEE754 hexadecimal string to binary
def ieee754_hex_to_binary(ieee754_hex, p, lookup_table):
	binary_string = []
	
	for i in range(len(ieee754_hex)):
		binary_string.append(hex_to_binary(ieee754_hex[i], lookup_table))
	
	single_binary_string = "".join(binary_string)
	
	if '1' not in single_binary_string:
		return "0"*p.hexadecimal_size*4
		
	sign_bit = single_binary_string[0]
	exponent = single_binary_string[1:p.exponent_size+1]
	mantissa = single_binary_string[p.exponent_size+1:]
	
	if (exponent == ('1' * p.exponent_size)):
		return "ERROR"
	
	shift_value = int(exponent, 2) - p.exp_bias
	
	if (shift_value > 0):
		if (shift_value > p.mantissa_size):
			binary_value = '01' + mantissa + '0'*(shift_value - p.mantissa_size)
			binary_int_list = binary_string_to_int_list(binary_value)
	
			if (sign_bit == '1'):
				binary_int_twos_comp, carry = twos_complement(binary_int_list)
			else:
				binary_int_twos_comp = binary_int_list
			
			binary_output = binary_int_twos_comp + ['.'] + [0]
		elif (shift_value <= p.mantissa_size):
			binary_value = '01' + mantissa
			binary_int_list = binary_string_to_int_list(binary_value)
	
			if (sign_bit == '1'):
				binary_int_twos_comp, carry = twos_complement(binary_int_list)
			else:
				binary_int_twos_comp = binary_int_list
			
			binary_output = binary_int_twos_comp[:shift_value+2] + ['.'] + binary_int_twos_comp[shift_value+2:]
	elif (shift_value < 0):
		binary_value = '0'*(abs(shift_value) - 1) + '1' + mantissa
		binary_int_list = binary_string_to_int_list(binary_value)

		if (sign_bit == '1'):
			binary_int_twos_comp, carry = twos_complement(binary_int_list)
			binary_output = [1] + ['.'] + binary_int_twos_comp
		else:
			binary_int_twos_comp = binary_int_list
			binary_output = [0] + ['.'] + binary_int_twos_comp
	else:
		binary_value = '01' + mantissa
		binary_int_list = binary_string_to_int_list(binary_value)
		
		if (sign_bit == '1'):
			binary_int_twos_comp, carry = twos_complement(binary_int_list)
		else:
			binary_int_twos_comp = binary_int_list
		
		binary_output = binary_int_twos_comp[:2] + ['.'] + binary_int_twos_comp[2:]
	
#	print(sign_bit, exponent, mantissa, shift_value)
	
#	print(list_to_string(binary_output))
	return binary_output

def binary_to_real(n):
	if isinstance(n, str):
		if ('E' in n) or ('e' in n):
			return "ERROR"
		else:
			n_int_list = binary_string_to_int_list(n)
	elif isinstance(n, list):
		n_int_list = n
	else:
		return "ERROR"

	n_size = len(n_int_list)
	
#	print("n_int_list = ", n_int_list)
	
	if ('.' in n_int_list):
		binary_point_index = n_int_list.index('.')
		integer_list = n_int_list[:binary_point_index]
		fraction_list = n_int_list[binary_point_index+1:]
		n_reassembled = integer_list + fraction_list
		
		if (n_int_list[0] == 1):
			n_2s_comp, carry = twos_complement(n_reassembled)
		else:
			n_2s_comp = n_reassembled
		
		integer_list = n_2s_comp[:binary_point_index]
		fraction_list = n_2s_comp[binary_point_index:]
		
		fraction_part = 0

		fraction_list_size = len(fraction_list)
		
		for i in range(0, fraction_list_size):
			if (fraction_list[i] == 1):
				fraction_part += 2**(-(i+1))
		
		integer_part = 0

		integer_list_size = len(integer_list)
		
		if (debug_enable == True):
			print(list_to_string(n_int_list), integer_list_size, list_to_string(integer_list))
		
		for i in range(0, integer_list_size):
			if (debug_enable == True):
				print("Made it here")
				
			if (integer_list[i] == 1):
				integer_part += 2**(integer_list_size-1-i)
		
		integer_part_decimal = Decimal(integer_part)
		fraction_part_decimal = Decimal(fraction_part)
		
		if (n_int_list[0] == 1):
			integer_neg = 0 - integer_part_decimal
			fraction_neg = 0 - fraction_part_decimal
			integer_neg_string = str(integer_neg)
			fraction_neg_string = str(fraction_neg)
			
			if (integer_neg != 0) and (fraction_neg != 0):
				if ('.' in integer_neg_string) and ('.' in fraction_neg_string):
					if ('-' in fraction_neg_string):
						real_output = integer_neg_string + fraction_neg_string[2:]
					else:
						real_output = integer_neg_string + fraction_neg_string[1:]
				else:
					if ('-' in fraction_neg_string):
						if ('.' in fraction_neg_string):
							real_output = integer_neg_string + fraction_neg_string[2:]
						else:
							real_output = integer_neg_string
					else:
						if ('.' in fraction_neg_string):
							real_output = integer_neg_string + fraction_neg_string[2:]
						else:
							real_output = integer_neg_string
			elif (integer_neg != 0) and (fraction_neg == 0):
				real_output = integer_neg_string
			elif (integer_neg == 0) and (fraction_neg != 0):
				real_output = fraction_neg_string
			else:
				real_output = str(0)
		else:
			integer_string = str(integer_part_decimal)
			fraction_string = str(fraction_part_decimal)

			if (integer_part_decimal != 0) and (fraction_part_decimal != 0):
				if ('.' in integer_string) and ('.' in fraction_string):
					real_output = integer_string + fraction_string[2:]
				else:
					if ('.' in fraction_string):
						real_output = integer_string + fraction_string[1:]
					else:
						real_output = integer_string
			elif (integer_part_decimal != 0) and (fraction_part_decimal == 0):
				real_output = integer_string
			elif (integer_part_decimal == 0) and (fraction_part_decimal != 0):
				real_output = fraction_string
			else:
				real_output = str(0)
	else:
		integer_list = n_int_list
		integer_part = 0
		fraction_part = 0
		twos_comp_input = integer_list

		if (integer_list[0] == 1):
			n_2s_comp, carry = twos_complement(integer_list)
		else:
			n_2s_comp = integer_list
		
		integer_list_size = len(n_2s_comp)
		
		for i in range(0, integer_list_size):
			if (n_2s_comp[i] == 1):
				integer_part += 2**(integer_list_size-1-i)

		integer_part_decimal = Decimal(integer_part)
		
		if (n_int_list[0] == 1):
			real_int_2s_comp = 0 - integer_part_decimal
			real_output = str(real_int_2s_comp)
		else:
			real_output = str(integer_part_decimal)

	if (debug_enable == True):
		print(integer_part, fraction_part)
					
	return real_output

def binary_to_hexadecimal(n, lut):
	n_size = len(n)
	
	if ('.' in n):
		binary_point_index = n.index('.')
		
		if (binary_point_index > 0):
			n_integer = n[:binary_point_index]
			n_fraction = n[binary_point_index+1:]
			binary_value = n_integer + n_fraction
		else:
			binary_value = n[1:]
		
		n_size -= 1
	else:
		binary_value = n
	
	n_size_remainder = n_size % 4
	n_size_difference = 4 - n_size_remainder
	n_size += n_size_difference
	
	if (n_size_remainder != 0):
		binary_value_padded = [n[0]]*n_size_difference + binary_value
	else:
		binary_value_padded = binary_value

	binary_value_string = "".join(map(str, binary_value_padded))	
	hex_string = []
	
	for i in range(0, n_size//4):
		bin_string_value = binary_value_string[i*4:i*4+4]
		
		for col1, col2, col3 in lut:
			if bin_string_value == col3:
				hex_string.append(col2)
		
	return "".join(hex_string)

def binary_to_ieee754(n, p, lookup_table):
	sign_bit = n[0]
	
	if ('.' in n):
		binary_point_index = n.index('.')
		no_binary_point = False
	else:
		binary_point_index = len(n)
		no_binary_point = True
		
	if (binary_point_index > 0):
		n_no_binary_point = n[:binary_point_index] + n[binary_point_index+1:]
	elif (no_binary_point == False):
		n_no_binary_point = n[1:]
	else:
		n_no_binary_point = n
	
	if (sign_bit == 1):
		n_2s_comp, carry = twos_complement(n_no_binary_point)
	else:
		n_2s_comp = n_no_binary_point

	if (no_binary_point == False):
		n_2s_comp_binary_point = n_2s_comp[:binary_point_index] + ['.'] + n_2s_comp[binary_point_index:]
	else:
		n_2s_comp_binary_point = n_2s_comp
	
	mantissa_offet = 1
	n_stripped = remove_msbs(n_2s_comp_binary_point)

	if ('.' in n_stripped):
		n_stripped_binary_point_index = n_stripped.index('.')
	else:
		n_stripped_binary_point_index = len(n_stripped)
		
	if (1 in n_stripped):
		n_2s_comp_msb_index = n_stripped.index(1)
	else:
		return "0" * p.hexadecimal_size

	if (no_binary_point == False):
		n_2s_comp_size = len(n_stripped) - 1
	else:
		n_2s_comp_size = len(n_stripped)
	
	if (no_binary_point == False):
		if (n_2s_comp_size >= p.mantissa_size):
			if (n_stripped_binary_point_index > n_2s_comp_msb_index):
				if ((n_2s_comp_size-2) >= p.mantissa_size):
					mantissa = n_stripped[n_2s_comp_msb_index+mantissa_offet:n_stripped_binary_point_index] + n_stripped[n_stripped_binary_point_index+1:p.mantissa_size + (mantissa_offet + 1 + n_2s_comp_msb_index)]
				else:
					mantissa = n_stripped[n_2s_comp_msb_index+mantissa_offet:n_stripped_binary_point_index] + n_stripped[n_stripped_binary_point_index+1:] + [0]*(p.mantissa_size-(n_2s_comp_size-(mantissa_offet + 1)))
			else:
				mantissa = 	n_stripped[n_2s_comp_msb_index+mantissa_offet:n_2s_comp_msb_index+1+p.mantissa_size]
		elif (n_2s_comp_size < p.mantissa_size):
			if (n_stripped_binary_point_index > n_2s_comp_msb_index):
				mantissa = n_stripped[n_2s_comp_msb_index+mantissa_offet:n_stripped_binary_point_index] + n_stripped[n_stripped_binary_point_index+1:] + [0]*(p.mantissa_size - (n_2s_comp_size - n_2s_comp_msb_index) + mantissa_offet + 1)
			else:
				mantissa = n_stripped[n_2s_comp_msb_index+mantissa_offet:] + [0]*(p.mantissa_size - (n_2s_comp_size - n_2s_comp_msb_index) + mantissa_offet + 1)
	else:
		if (n_2s_comp_size >= p.mantissa_size):
			if ((n_2s_comp_size-2) >= p.mantissa_size):
				mantissa = n_stripped[n_2s_comp_msb_index+mantissa_offet:n_stripped_binary_point_index] + n_stripped[n_stripped_binary_point_index+1:p.mantissa_size + (mantissa_offet + 1 + n_2s_comp_msb_index)]
			else:
				mantissa = n_stripped[n_2s_comp_msb_index+mantissa_offet:n_stripped_binary_point_index] + n_stripped[n_stripped_binary_point_index+1:] + [0]*(p.mantissa_size-(n_2s_comp_size-(mantissa_offet + 1)))
		elif (n_2s_comp_size < p.mantissa_size):
			mantissa = n_stripped[n_2s_comp_msb_index+mantissa_offet:] + [0]*(p.mantissa_size - (n_2s_comp_size - n_2s_comp_msb_index) + mantissa_offet + 1)

	shift_value = n_stripped_binary_point_index - n_2s_comp_msb_index
	
	if (shift_value > 0):
		exponent = shift_value + p.exp_bias - 1
	else:
		exponent = shift_value + p.exp_bias
	
	exponent_binary = f"{exponent:0{p.exponent_size}b}"
	exponent_int_list = binary_string_to_int_list(exponent_binary)
	
	if (len(exponent_int_list) < p.exponent_size):
		exponent_int_list = [0]*(p.exponent_size - len(exponent_int_list)) + exponent_int_list
		
	ieee754_binary = [sign_bit] + exponent_int_list + mantissa[:p.mantissa_size]
	
	ieee754_hex_value = binary_to_hexadecimal(ieee754_binary, lookup_table)
	
	return ieee754_hex_value
