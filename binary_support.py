import struct
from decimal import Decimal, getcontext
import time
from fixedpoint import FixedPoint
import math
import numpy as np
from dataclasses import dataclass
from typing import List, Literal

@dataclass
class precision_parameters:
	exponent_size: int
	mantissa_size: int
	exp_bias: int 
	exp_mask: int 
	mantissa_mask: int
	exp_nibble_size: int
	mantissa_nibble_size: int
	hexadecimal_size: int
	precision: Literal["SINGLE", "DOUBLE"]

precision_profile = {
					"SINGLE": precision_parameters(exponent_size = 8, mantissa_size = 23, exp_bias = 127, exp_mask = 0x7F, mantissa_mask = 0x7FFFFF, exp_nibble_size = 2, mantissa_nibble_size = 6, hexadecimal_size = 8, precision = "SINGLE"),
					"DOUBLE": precision_parameters(exponent_size = 11,	mantissa_size = 52,	exp_bias = 1023, exp_mask = 0x7FF, mantissa_mask = 0xFFFFFFFFFFFFF, exp_nibble_size = 3, mantissa_nibble_size = 14, hexadecimal_size = 16, precision = "DOUBLE")
					}

lookup_table = [
				('0', '0', "0000"),
				('1', '1', "0001"),
				('2', '2', "0010"),
				('3', '3', "0011"),
				('4', '4', "0100"),
				('5', '5', "0101"),
				('6', '6', "0110"),
				('7', '7', "0111"),
				('8', '8', "1000"),
				('9', '9', "1001"),
				('a', 'A', "1010"),
				('b', 'B', "1011"),
				('c', 'C', "1100"),
				('d', 'D', "1101"),
				('e', 'E', "1110"),
				('f', 'F', "1111")
				]


# Converts one hexadecimal character to binary using a lookup table
def hex_to_binary(n, lut):
	for col1, col2, col3 in lut:
		if n == col1 or n == col2:
			return col3

# Converts binary to hexadecimal four bits at a time
def binary_to_hex(n, lut):
	size = len(n)
	single_binary_string = "".join(n)
	hex_string = []
	
	if ((size % 4) != 0):
		return "ERROR"
	
	for i in range(0, size//4):
		bin_string_value = single_binary_string[i*4:i*4+4]
		
		for col1, col2, col3 in lut:
			if bin_string_value == col3:
				hex_string.append(col2)
		
	return "".join(hex_string)

# Converts a binary string to an integer list
def binary_string_to_int_list(n):
	integer_list = []
	
	for i in range(0, len(n)):
		if (n[i] == '0'):
			integer_list.append(0)
		elif (n[i] == '1'):
			integer_list.append(1)
		elif (n[i] == '.'):
			integer_list.append(n[i])
	
	return integer_list

# Converts an integer list to a binary string
def int_list_to_binary_string(n, size):
	binary_list = []
	
	for i in range(0, size):
		if (n[i] == 0):
			binary_list.append('0')
		elif (n[i] == 1):
			binary_list.append('1')
		elif (n[i] == '.'):
			binary_list.append(n[i])
	
	return binary_list

# The core of the real-to-binary conversion
def real_to_binary(n, default_frac_size):
	if '.' in n:
		decimal_point_index = n.find('.')

		if (n[0] == '-'):
			sign_bit = '1'
			n_integer_abs = n[1:decimal_point_index]		# Drop the sign character
			n_fraction_abs = n[decimal_point_index+1:]
			
			if (n[1] == '0') and (decimal_point_index == 2):
				integer_size = 0
			else:
				integer_size = decimal_point_index - 1
		else:
			sign_bit = '0'
			n_integer_abs = n[:decimal_point_index]
			n_fraction_abs = n[decimal_point_index+1:]
			
			if (n[0] == '0') and (decimal_point_index == 1):
				integer_size = 0
			else:
				integer_size = decimal_point_index
	
		if (decimal_point_index == len(n)):
			fraction_size = 0
		else:
			fraction_size = len(n_fraction_abs)
	else:
		decimal_point_index = len(n)

		if (n[0] == '-'):
			sign_bit = '1'
			n_integer_abs = n[1:]		# Drop the sign character
			n_fraction_abs = "0"
			
			if (n[1] == '0') and (decimal_point_index == 2):
				integer_size = 0
			else:
				integer_size = decimal_point_index - 1
		else:
			sign_bit = '0'
			n_integer_abs = n
			n_fraction_abs = 0
			
			if (n[0] == '0') and (decimal_point_index == 1):
				integer_size = 0
			else:
				integer_size = decimal_point_index
		
		fraction_size = 0
	
	integer_value = int(n_integer_abs)
	fraction_value = int(n_fraction_abs)
	
	fraction_sum = fraction_value
	fraction_compare_value = 1 * (10**fraction_size)
	binary_frac_value = []

#	print(fraction_compare_value, fraction_sum)
	
	if (fraction_size > 0):
		for i in range(0, default_frac_size):
			fraction_sum = fraction_sum * 2
			
			if (fraction_sum >= fraction_compare_value):
				fraction_sum -= fraction_compare_value
				binary_frac_value.append('1')
			else:
				binary_frac_value.append('0')
			
#			print(fraction_sum, "".join(binary_frac_value))
	else:
		binary_frac_value.append('0')

	integer_quotient = integer_value
	binary_int_value = []
	
	if (integer_size > 0):
		while (integer_quotient != 0):
			binary_bit = integer_quotient % 2
			binary_int_value.append(str(binary_bit))
			integer_quotient = integer_quotient//2
	else:
		binary_int_value.append('0')
	
	binary_int_value.reverse()
	
	single_binary_int = "".join(binary_int_value)
	single_binary_frac = "".join(binary_frac_value)

	return '0' + single_binary_int + '.' + single_binary_frac

def binary_point_removal(operand_a, operand_b):
	a_size = len(operand_a)
	b_size = len(operand_b)
	
	if ('.' in operand_a):
		a_radix_index = operand_a.index('.')
	else:
		a_radix_index = 0
	
	if ('.' in operand_b):
		b_radix_index = operand_b.index('.')
	else:
		b_radix_index = 0
	
	if (a_radix_index > 0):
		if (a_radix_index == 1) and (operand_a[0] == 0):
			a_integer_size = 0
			a_fraction_size = a_size - (a_radix_index + 1)
		else:
			a_integer_size = a_radix_index
			a_fraction_size = a_size - (a_radix_index + 1)
	else:
		if (operand_a[0] != '.'):
			a_integer_size = a_size
			a_fraction_size = 0
		else:
			a_integer_size = 0
			a_fraction_size = a_size - 1

	if (b_radix_index > 0):
		if (b_radix_index == 1) and (operand_b[0] == 0):
			b_integer_size = 0
			b_fraction_size = b_size - (b_radix_index + 1)
		else:
			b_integer_size = b_radix_index
			b_fraction_size = b_size - (b_radix_index + 1)
	else:
		if (operand_b[0] != '.'):
			b_integer_size = b_size
			b_fraction_size = 0
		else:
			b_integer_size = 0
			b_fraction_size = b_size - 1
			
	if (a_integer_size > 0):
		if (a_fraction_size > 0):
			a_no_radix_point = operand_a[:a_radix_index] + operand_a[a_radix_index+1:]
		else:
			if (a_radix_index == 0):
				a_no_radix_point = operand_a
			else:
				a_no_radix_point = operand_a[:a_radix_index]
	else:
		if (a_fraction_size > 0):
			a_no_radix_point = operand_a[a_radix_index+1:]
		else:
			return "ERROR"
				
	if (b_integer_size > 0):
		if (b_fraction_size > 0):
			b_no_radix_point = operand_b[:b_radix_index] + operand_b[b_radix_index+1:]
		else:
			if (b_radix_index == 0):
				b_no_radix_point = operand_b
			else:
				b_no_radix_point = operand_b[:b_radix_index]
	else:
		if (b_fraction_size > 0):
			b_no_radix_point = operand_b[b_radix_index+1:]
		else:
			return "ERROR"

	if (1 in a_no_radix_point):
		a_msb = a_no_radix_point.index(1)
		
		if (a_msb < a_radix_index):
			a_integer_size -= a_msb
	else:
		a_msb = 0
	
	if (1 in b_no_radix_point):
		b_msb = b_no_radix_point.index(1)
		
		if (b_msb < b_radix_index):
			b_integer_size -= b_msb
	else:
		b_msb = 0
	
#	print("a integer size = ", a_integer_size, "b integer size", b_integer_size)
	
	if (a_integer_size > b_integer_size):
		operand_a_padded = a_no_radix_point
		operand_b_padded = [0]*a_msb + [b_no_radix_point[0]]*(a_integer_size-b_integer_size) + b_no_radix_point
	elif (b_integer_size > a_integer_size):
		operand_a_padded = [0]*b_msb + [a_no_radix_point[0]]*(b_integer_size-a_integer_size) + a_no_radix_point
		operand_b_padded = b_no_radix_point
	else:
		operand_a_padded = a_no_radix_point
		operand_b_padded = b_no_radix_point
		
	if (a_fraction_size > b_fraction_size):
		padding_size_a = 0
		padding_size_b = a_fraction_size-b_fraction_size
		operand_a_out = operand_a_padded
		operand_b_out = operand_b_padded + [0]*padding_size_b
		fraction_size = a_fraction_size
	elif (b_fraction_size > a_fraction_size):
		padding_size_a = b_fraction_size-a_fraction_size
		padding_size_b = 0
		operand_a_out = operand_a_padded + [0]*padding_size_a
		operand_b_out = operand_b_padded
		fraction_size = b_fraction_size
	else:
		padding_size_a = 0
		padding_size_b = 0
		operand_a_out = operand_a_padded
		operand_b_out = operand_b_padded
		fraction_size = a_fraction_size
	
	a_size_out = len(operand_a_out)
	b_size_out = len(operand_b_out)
	
	if (a_size_out > b_size_out):
		result_a = operand_a_out;
		result_b = [0]*(a_size_out - b_size_out) + operand_b_out
	elif (b_size_out > a_size_out):
		result_a = [0]*(b_size_out - a_size_out) + operand_a_out
		result_b = operand_b_out
	else:
		result_a = operand_a_out;
		result_b = operand_b_out
		
	return result_a, result_b, a_radix_index, b_radix_index, fraction_size

def twos_complement(n_int_list):
	n_int_list_inverted = []
	
	for i in range(0, len(n_int_list)):
		n_int_list_inverted.append(n_int_list[i] ^ 1)
	
	addend = [0]*(len(n_int_list)-1) + [1]
	
	addend_a, addend_b = append_msbs(n_int_list_inverted, addend, 0, 0)
	n_sum, n_carry = binary_adder(addend_a, addend_b)

	return n_sum, n_carry

def twos_complement_bin_rational(n):
	binary_point_index = n.find('.')
	size = len(n)
	fraction_size = size - binary_point_index - 1
	n_int_list = binary_string_to_int_list(n)
	
	n_int_list_inverted = []
	
	for i in range(0, size):
		if (n_int_list[i] != '.'):
			n_int_list_inverted.append(n_int_list[i] ^ 1)
		else:
			n_int_list_inverted.append(n_int_list[i])
	
	addend = [0] * binary_point_index + ['.'] + [0] * (fraction_size - 1) + [1]

	n_inverted_sum = []
	carry = 0
	binary_point_location = 0
	
	for i in range(size-1, -1, -1):
		if (n_int_list_inverted[i] != '.'):
			n_inverted_sum.append((addend[i] ^ n_int_list_inverted[i]) ^ carry)
			carry = (carry & n_int_list_inverted[i]) | (n_int_list_inverted[i] & addend[i]) | (carry & addend[i])
		else:
			binary_point_location = size-1-i
	
	n_inverted_sum.append(carry | n_inverted_sum[-1])
	
	twos_comp_sum = n_inverted_sum[:binary_point_location] + ['.'] + n_inverted_sum[binary_point_location:]
	
	twos_comp_sum.reverse()
	
	return twos_comp_sum

def binary_comparator(a, b, operation):
	a_size = len(a)
	b_size = len(b)

	if (operation == 'GT'):
		a_2s_comp = a
		b_2s_comp, b_carry = twos_complement(b)
	elif (operation == 'LT'):
		a_2s_comp, a_carry = twos_complement(a)
		b_2s_comp = b
	else:
		a_2s_comp = a
		b_2s_comp = b
	
	if (a_size > b_size):
		addend_a = a_2s_comp
		addend_b = [0]*(a_size - b_size) + b_2s_comp
	elif (b_size > a_size):
		addend_a = [0]*(b_size - a_size) + a_2s_comp
		addend_b = b_2s_comp
	else:
		addend_a = a_2s_comp
		addend_b = b_2s_comp

	difference, carry = binary_adder(addend_a, addend_b)		
	
	if (carry == 1):
		return True
	else:
		return False

def append_msbs(A, B, a_msb, b_msb):
	a_len = len(A)
	b_len = len(B)
	
	if (a_len > b_len):
		a_output = A
		b_output = [b_msb]*(a_len-b_len) + B
	elif (b_len > a_len):
		a_output = [a_msb]*(b_len-a_len) + A
		b_output = B
	else:
		a_output = A
		b_output = B
	
	return a_output, b_output

def binary_adder(n, addend):
	n_sum = []
	carry = 0

	for i in range(len(n)-1, -1, -1):
		n_sum.append((addend[i] ^ n[i]) ^ carry)
		carry = (carry & n[i]) | (n[i] & addend[i]) | (carry & addend[i])

	if (len(n_sum) > len(n)):
		carry_out = carry | n_sum[-1]
	else:
		carry_out = carry

	n_sum.reverse()
	return n_sum, carry_out

def list_to_string(n):
	return "".join(map(str, n))

def remove_msbs(n):
	if (1 in n):
		msb_index = n.index(1)
	else:
		msb_index = 0
	
	if ('.' in n):
		binary_point_index = n.index('.')
	else:
		binary_point_index = len(n)
	
	if (msb_index < binary_point_index):
		if (n[0] == 0):
			binary_value = [0] + n[msb_index:]
		else:
			binary_value = n[msb_index:]
	else:
		binary_value = n[binary_point_index-1:]
	
	return binary_value

def binary_point_alignment(operand_a, operand_b, enable_twos_complement):
	if ('.' in operand_a):
		a_has_binary_point = True
	else:
		a_has_binary_point = False
	
	if ('.' in operand_b):
		b_has_binary_point = True
	else:
		b_has_binary_point = False

	if (a_has_binary_point == True):
		a_radix_index = operand_a.index('.')
	else:
		a_radix_index = len(operand_a)

	operand_a_normalized = []

	if (a_has_binary_point == True):
		operand_a_normalized = operand_a
		operand_a_normalized.pop(a_radix_index)
	else:
		operand_a_normalized = operand_a
	
	if (b_has_binary_point == True):
		b_radix_index = operand_b.index('.')
	else:
		b_radix_index = len(operand_b)
	
	operand_b_normalized = []

	if (b_has_binary_point == True):
		operand_b_normalized = operand_b
		operand_b_normalized.pop(b_radix_index)
	else:
		operand_b_normalized = operand_b
		
	a_size = len(operand_a)
	b_size = len(operand_b)

	if (a_has_binary_point == True):
		a_integer_size = a_radix_index
		a_fraction_size = a_size - a_radix_index
	else:
		a_integer_size = a_size
		a_fraction_size = 0
	
	if (b_has_binary_point == True):
		b_integer_size = b_radix_index
		b_fraction_size = b_size - b_radix_index
	else:
		b_integer_size = b_size
		b_fraction_size = 0

	if (enable_twos_complement == True):	
		if (operand_a_normalized[0] == 1):
			operand_a_2s_comp, carry_a = twos_complement(operand_a_normalized)
		else:
			operand_a_2s_comp = operand_a_normalized

		if (operand_b_normalized[0] == 1):
			operand_b_2s_comp, carry_b = twos_complement(operand_b_normalized)
		else:
			operand_b_2s_comp = operand_b_normalized
	else:
		operand_a_2s_comp = operand_a_normalized
		operand_b_2s_comp = operand_b_normalized
	
	if (a_integer_size > b_integer_size):
		operand_a_padded_left = operand_a_2s_comp
		
		if (enable_twos_complement == True):	
			operand_b_padded_left = [0]*(a_integer_size - b_integer_size) + operand_b_2s_comp
		else:
			operand_b_padded_left = [operand_b_2s_comp[0]]*(a_integer_size - b_integer_size) + operand_b_2s_comp
	elif (b_integer_size > a_integer_size):
		if (enable_twos_complement == True):
			operand_a_padded_left = [0]*(b_integer_size - a_integer_size) + operand_a_2s_comp	
		else:
			operand_a_padded_left = [operand_a_2s_comp[0]]*(b_integer_size - a_integer_size) + operand_a_2s_comp	
			
		operand_b_padded_left = operand_b_2s_comp
	else:
		operand_a_padded_left = operand_a_2s_comp
		operand_b_padded_left = operand_b_2s_comp
	
	if (a_fraction_size > b_fraction_size):
		operand_a_padded = operand_a_padded_left
		operand_b_padded = operand_b_padded_left + [0]*(a_fraction_size - b_fraction_size)
	elif (b_fraction_size > a_fraction_size):
		operand_a_padded = operand_a_padded_left + [0]*(b_fraction_size - a_fraction_size)
		operand_b_padded = operand_b_padded_left
	else:
		operand_a_padded = operand_a_padded_left
		operand_b_padded = operand_b_padded_left

	return operand_a_padded, operand_b_padded, a_fraction_size, b_fraction_size