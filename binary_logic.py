import struct
from decimal import Decimal, getcontext
import time
from fixedpoint import FixedPoint
import math
import numpy as np
from dataclasses import dataclass
from typing import List, Literal
from binary_support import twos_complement, append_msbs, binary_comparator, binary_point_removal, list_to_string, binary_point_alignment, binary_string_to_int_list, add_msbs

enable_print_statements = False

def binary_and(A, B):
	operand1_no_bin_point, operand2_no_bin_point = add_msbs(A, B)
	return [bit_a & bit_b for bit_a, bit_b in zip(operand1_no_bin_point, operand2_no_bin_point)]
	
def binary_or(A, B):
	operand1_no_bin_point, operand2_no_bin_point = add_msbs(A, B)
	return [bit_a | bit_b for bit_a, bit_b in zip(operand1_no_bin_point, operand2_no_bin_point)]	

def binary_xor(A, B):
	operand1_no_bin_point, operand2_no_bin_point = add_msbs(A, B)
	return [bit_a ^ bit_b for bit_a, bit_b in zip(operand1_no_bin_point, operand2_no_bin_point)]	

def binary_not(A):
	operand_inverted = []
	
	for i in range(0, len(A)):
		operand_inverted.append(A[i]^1)
		
	return operand_inverted
	