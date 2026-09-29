import struct
from decimal import Decimal, getcontext
import time
from fixedpoint import FixedPoint
import math
import numpy as np
from dataclasses import dataclass
from typing import List, Literal
from binary_support import twos_complement, append_msbs, binary_comparator, binary_point_removal, list_to_string, binary_point_alignment

enable_print_statements = False

def binary_division(numerator, denominator, max_size):
	if (enable_print_statements == True):
		print("numerator = ", "".join(map(str, numerator)), "denominator = ", "".join(map(str, denominator)))
	
#	f = open("division_result.txt", "w")

	if ('.' in numerator):
		num_bin_point_index = numerator.index('.')
	else:
		num_bin_point_index = len(numerator)
	
	if ('.' in denominator):
		denom_bin_point_index = denominator.index('.')
	else:
		denom_bin_point_index = len(denominator)
	
	if ('.' in numerator):
		num_frac_size = len(numerator) - (num_bin_point_index + 1)
	else:
		num_frac_size = 0
	
	if ('.' in denominator):
		denom_frac_size = len(denominator) - (denom_bin_point_index + 1)
	else:
		denom_frac_size = 0

	if (enable_print_statements == True):
		print(num_bin_point_index, denom_bin_point_index, num_frac_size, denom_frac_size)
	
	if '.' in numerator:
		num_no_bin_point = numerator[:num_bin_point_index] + numerator[num_bin_point_index+1:]
	else:
		num_no_bin_point = numerator[:]

	if '.' in denominator:
		denom_no_bin_point = denominator[:denom_bin_point_index] + denominator[denom_bin_point_index+1:]
	else:
		denom_no_bin_point = denominator[:]

	while len(num_no_bin_point) > 1 and num_no_bin_point[0] == 0:
		num_no_bin_point.pop(0)
	while len(denom_no_bin_point) > 1 and denom_no_bin_point[0] == 0:
		denom_no_bin_point.pop(0)

	if denom_frac_size > num_frac_size:
		num_padded = num_no_bin_point + [0] * (denom_frac_size - num_frac_size)
		denom_padded = denom_no_bin_point
	else:
		num_padded = num_no_bin_point
		denom_padded = denom_no_bin_point + [0] * (num_frac_size - denom_frac_size)

	num_size = len(num_padded)
	denom_size = len(denom_padded)

	if (num_size > denom_size):
		partial_remainder = num_padded[:denom_size]
	else:
		partial_remainder = num_padded

	denom_2s_comp, denom_carry = twos_complement(denom_padded)

	if (enable_print_statements == True):
		print(num_size, denom_size, num_bin_point_index, denom_bin_point_index, num_frac_size, denom_frac_size)
		print(list_to_string(num_no_bin_point), list_to_string(denom_no_bin_point))
		print("".join(map(str, num_padded)), "".join(map(str, denom_padded)), "".join(map(str, denom_2s_comp)), denom_carry)
	
	quotient = []
	offset = denom_size
	allow_bit_growth = False
	
#	f.write(' '*(23+denom_size) + '_'*(num_size+1) + "\n")
#	f.write(' '*22 + str("".join(map(str, denom_padded))) + '|' + str("".join(map(str, num_padded))) + "\n")
	
	# All outputs are positive since the 2's complement is taken above
	quotient.append(0)
	
	for i in range(0, max_size):
#		print("".join(map(str, partial_remainder)), "".join(map(str, denom_padded)), "".join(map(str, quotient)))
#		print('------------------------------------------------------------------------------')
		a_comp, b_comp = append_msbs(partial_remainder, denom_padded, 0, 0)
		
		if (binary_comparator(a_comp, b_comp, 'GT') == True) or (partial_remainder == denom_padded):
			addend_a, addend_b = append_msbs(partial_remainder, denom_2s_comp, 0, denom_2s_comp[0])
			partial_remainder, carry = binary_adder(addend_a, addend_b)
			quotient.append(1)
			partial_remainder.pop(0)

			if (allow_bit_growth == True):
				if (1 in partial_remainder):
					while partial_remainder[0] == 0:
						partial_remainder.pop(0)
				else:
					if (enable_print_statements == True):
						print("".join(map(str, quotient)))
					return quotient				
		else:
			addend_a, addend_b = append_msbs(partial_remainder, [0]*len(partial_remainder), 0, 0)
			partial_remainder, carry = binary_adder(addend_a, addend_b)

			quotient.append(0)			
			
			if (len(partial_remainder) > denom_size):	# and (allow_bit_growth == False):
				partial_remainder.pop(0)

#		f.write(' '*(23+denom_size+i) + str("".join(map(str, addend_b))) + "\n")
#		f.write(' '*(23+denom_size+i) + '-'*len(addend_b) + ' ' + str("".join(map(str, quotient))) + ' ' + str(allow_bit_growth) + ' ' + str(carry) + "\n")
#		f.write(' '*(24+denom_size+i) + str("".join(map(str, partial_remainder))) + "\n")

		if (offset < num_size):
			partial_remainder.append(num_padded[offset])
		else:
			if (offset == num_size) or ((denom_size > num_size) and (i == 0)):
				quotient.append('.')

			partial_remainder.append(0)
			allow_bit_growth = True

		offset += 1		
		
	return quotient

def binary_multiplier(operand_a, operand_b):
#	print("".join(map(str, operand_a)), "".join(map(str, operand_b)))
	
#	print(list_to_string(operand_a), list_to_string(operand_b))
#	operand_a_normalized, operand_b_normalized, a_radix_index, b_radix_index, fraction_size = binary_point_removal(operand_a, operand_b)

	if ('.' in operand_a):	
		a_has_binary_point = True
	else:
		a_has_binary_point = False
		
	if ('.' in operand_b):
		b_has_binary_point = True
	else:
		b_has_binary_point = False
		
	operand_a_padded, operand_b_padded, a_fraction_size, b_fraction_size = binary_point_alignment(operand_a, operand_b, True)
	
	if (a_fraction_size > b_fraction_size):
		total_fraction_size = a_fraction_size * 2
	elif (b_fraction_size >= a_fraction_size):
		total_fraction_size = b_fraction_size * 2
	
#	print(a_fraction_size, b_fraction_size, total_fraction_size)
#	print(list_to_string(operand_a_padded), list_to_string(operand_b_padded))
	
	negative_output = operand_a[0] ^ operand_b[0]
	
	a_size = len(operand_a_padded)
	b_size = len(operand_b_padded)
	current_sum = [0]*a_size
	
	for i in range(a_size-1, -1, -1):
		if (operand_b_padded[i] == 1):
			addend_a = current_sum
			addend_b = operand_a_padded + [0]*((a_size-1)-i)
		else:	
			addend_a = current_sum
			addend_b = [0]*a_size + [0]*((a_size-1)-i)
		
		current_sum, current_carry = binary_adder(addend_a, addend_b)
		current_sum = [current_carry] + current_sum
#		print("i = ", i, "Current sum = ", list_to_string(current_sum))
	
	if (negative_output == 1):
		product_2s_comp, product_carry = twos_complement(current_sum)
	else:
		product_2s_comp = current_sum

	product_size = len(product_2s_comp)
	
#	print("".join(map(str, product_2s_comp)))
	
	if (a_has_binary_point == True) or (b_has_binary_point == True):
		product = product_2s_comp[:product_size-total_fraction_size] + ['.'] + product_2s_comp[product_size-total_fraction_size:]
	else:
		product = product_2s_comp
	
	return product

def binary_adder(n, addend):
	n_sum = []
	carry = 0

#	if (enable_print_statements == True):
#		print("operand a = ", list_to_string(n), "operand b = ", list_to_string(addend))

	for i in range(len(n)-1, -1, -1):
		n_sum.append((addend[i] ^ n[i]) ^ carry)
		carry = (carry & n[i]) | (n[i] & addend[i]) | (carry & addend[i])

	if (len(n_sum) > len(n)):
		carry_out = carry | n_sum[-1]
	else:
		carry_out = carry

	n_sum.reverse()
	return n_sum, carry_out

def binary_subtraction(A, B):
#	operand_a_normalized, operand_b_normalized, a_radix_index, b_radix_index, fraction_size = binary_point_removal(A, B)	
	operand_a_padded, operand_b_padded, a_fraction_size, b_fraction_size = binary_point_alignment(A, B, False)
	
#	if (B[0] != 1):
	operand_b_2s_comp, carry = twos_complement(operand_b_padded)	
#	else:
#		operand_b_2s_comp = operand_b_padded
#		carry = 0
	
	if (a_fraction_size > b_fraction_size):
		fraction_size = a_fraction_size
	elif (b_fraction_size >= a_fraction_size):
		fraction_size = b_fraction_size
	
	difference_sum, difference_carry = binary_adder(operand_a_padded, operand_b_2s_comp)
	
	if ((A[0] == 1) and (B[0] == 0)) or ((A[0] == 0) and (B[0] == 1)):
		difference = [difference_carry] + difference_sum
	else:
		difference = difference_sum
		
	binary_point_index = len(difference) - fraction_size
	difference_bin_point = difference[:binary_point_index] + ['.'] + difference[binary_point_index:]
	
	if (enable_print_statements == True):
		print(list_to_string(operand_a_padded), list_to_string(operand_b_padded), a_fraction_size, b_fraction_size)
		print(list_to_string(difference))
		
	return difference_bin_point

	
	