# =====================================================================
# MODULE PART 1 OF 2: MAIN ENTRY, VALIDATION, AND PARSING ROUTINES
# =====================================================================
from binary_support import precision_profile, lookup_table, twos_complement, binary_string_to_int_list, int_list_to_binary_string, binary_point_alignment, list_to_string
from binary_conversions import real_to_twos_comp_binary, hexadecimal_to_binary, ieee754_hex_to_binary, binary_to_real, binary_to_hexadecimal, binary_to_ieee754
from binary_math import binary_division, binary_multiplier, binary_adder, binary_subtraction, binary_modulo, binary_twos_complement
from binary_logic import binary_and, binary_or, binary_xor, binary_not

# Constant Global Mapping
HEX_NEGATIVE_LIST = ["8", "9", "A", "B", "C", "D", "E", "F", "a", "b", "c", "d", "e", "f"]

def compute_evaluation_step(main_display_value, input_mode, output_mode, int_bits, frac_bits, enable_print_statements=False):
	"""
	The universal processing gate. Accepts raw interface strings and configuration 
	integers, handles verification barriers, and returns: (updated_main, updated_aux)
	"""
	nibble_size = int_bits // 4
	
	# Execute the self-less parsing loop state machine
	operand1, operator, operand2, operand1_present, operator_present, operand2_present, input_error = parse_input_string(main_display_value)
	
	operand1_data_error = False
	operand2_data_error = False
	
	if enable_print_statements:			
		print("operand1 =  ", operand1, "operand2 = ", operand2, "operator = ", operator, "error = ", input_error)
		
	if not input_error:
		if input_mode == "REAL":
			operand1_data_error = verify_real_input(operand1)
			if operand2 != "":
				operand2_data_error = verify_real_input(operand2)
		elif input_mode == "HEX":
			if 0 < len(operand1) < nibble_size:
				operand1 = operand1.rjust(nibble_size, "F" if operand1 in HEX_NEGATIVE_LIST else "0")
			operand1_data_error = verify_hex_input(operand1, int_bits, frac_bits)

			if operand2_present:
				if 0 < len(operand2) < nibble_size:
					operand2 = operand2.rjust(nibble_size, "F" if operand2 in HEX_NEGATIVE_LIST else "0")
				operand2_data_error = verify_hex_input(operand2, int_bits, frac_bits)
		elif input_mode == "BIN":
			operand1_data_error = verify_bin_input(operand1)
			if operand2 != "":
				operand2_data_error = verify_bin_input(operand2)
			elif operator_present and not operand2_present:
				operand2_data_error = True
		elif input_mode == "FP32":
			operand1_data_error = verify_fp32_input(operand1)
			if operand2_present:
				operand2_data_error = verify_fp32_input(operand2)
		elif input_mode == "FP64":
			operand1_data_error = verify_fp64_input(operand1)
			if operand2_present:
				operand2_data_error = verify_fp64_input(operand2)

	operator_error = verify_operator(operator, input_mode, output_mode)
	
	# Verification Router Barrier
	if not input_error:
		if (('.' in operand1 or '.' in operand2) and (operator in ("&", "|", "^", "~"))) or (operator_error and operator != ""):
			if enable_print_statements:			
				print("input error", operator_error, operand1, operand2, operator)	
			if operator in ("&", "|", "^", "~"):
				return "", "Enter logic operands without radix point"
			return "", "ERROR"
			
		elif not operand1_data_error and not operand2_data_error and not operator_error:
			operand1_binary = convert_to_binary(operand1, input_mode, int_bits, frac_bits)

			if operand2_present:
				operand2_binary = convert_to_binary(operand2, input_mode, int_bits, frac_bits)
				binary_result = binary_math_operation(operand1_binary, operand2_binary, operator, int_bits, frac_bits, output_mode, enable_print_statements)
				calculator_result = convert_from_binary(binary_result, output_mode)
			elif operator in ("~", "!", "2'S"):
				binary_result = binary_math_operation(operand1_binary, None, operator, int_bits, frac_bits, output_mode, enable_print_statements)
				calculator_result = convert_from_binary(binary_result, output_mode)
			else:
				calculator_result = convert_from_binary(operand1_binary, output_mode)

			return main_display_value, calculator_result
		else:
			if enable_print_statements:			
				print("general error")
			return "", "ERROR"
	else:
		return "", "ERROR"

def parse_input_string(input_string):
	state = 'Empty_String_Check'
	data_length = len(input_string)
	input_index = 0
	left, op, right = "", "", ""
	operand1_present = False
	operator_present = False
	operand2_present = False
	input_error = False
	
	while True:
		match state:
			case 'Empty_String_Check':
				if not input_string:
					return "", "", "", False, False, False, True
				state = 'First_Character'
			case 'First_Character':
				if input_string[input_index] in ('+', '~', '!'):
					if input_string[input_index] in ('~', '!'):
						op = input_string[input_index]
					
					if (data_length > 1):
						input_index += 1
						state = 'First_Operand'
					else:
						return "", "", "", False, False, False, True
				elif input_string[input_index] == '-' or input_string[input_index].isalnum() or input_string[input_index] == ".":
					left += input_string[input_index]
					
					if data_length > 1:
						input_index += 1
						state = 'First_Operand'
					else:
						return left, op, right, operand1_present, operator_present, operand2_present, input_error
				else:
					return "", "", "", False, False, False, True
			case 'First_Operand':
				while input_string[input_index] not in ("+", "-", "*", "/", "%", "&", "|", "^", ""):
					if input_string[input_index].isalnum() or input_string[input_index] == ".":
						left += input_string[input_index]
						if input_index < data_length - 1:
							input_index += 1
						else:
							operand1_present = True
							return left, op, right, operand1_present, operator_present, operand2_present, input_error
					else:
						return "", "", "", False, False, False, True
				else:
					operand1_present = True
					operator_present = True
					if op not in ('~', '!'):
						op = input_string[input_index]
					input_index += 1

				if input_index < data_length:
					if input_string[input_index] != "":
						state = 'Second_Operand'
					else:
						operand2_present = False
						return left, op, right, operand1_present, operator_present, operand2_present, input_error
				else:
					operand2_present = False
					return left, op, right, operand1_present, operator_present, operand2_present, input_error
			case 'Second_Operand':
				while input_string[input_index] != "":
					if input_string[input_index].isalnum() or input_string[input_index] == "." or (right == "" and input_string[input_index] == "-"):
						right += input_string[input_index]
						if input_index < data_length - 1:
							input_index += 1
						else:
							operand2_present = True
							return left, op, right, operand1_present, operator_present, operand2_present, input_error
					else:
						return "", "", "", False, False, False, True
				operand2_present = True
				return left, op, right, operand1_present, operator_present, operand2_present, input_error
# =====================================================================
# MODULE PART 2 OF 2: CODES CONVERSIONS AND ALU MATHEMATIC ROUTING
# =====================================================================

def verify_real_input(input_string):
	try:
		float(input_string)
		return False
	except ValueError:
		return True

def verify_hex_input(input_string, int_bits, frac_bits):
	try:
		int(input_string, 16)
		return len(input_string) > (int_bits + frac_bits) / 4
	except ValueError:
		return True

def verify_bin_input(input_string):
	return (input_string.count('.') > 1 or (input_string[0] != '0' and input_string[0] != '1') or input_string[-1] == '.')

def verify_fp32_input(input_string):
	try:
		int(input_string, 16)
		return len(input_string) != 8
	except ValueError:
		return True
	
def verify_fp64_input(input_string):
	try:
		int(input_string, 16)
		return len(input_string) != 16
	except ValueError:
		return True

def verify_operator(input_string, input_mode, output_mode):
	if input_string in ("&", "|", "^", "~", "!", "2'S"):
		logic_error = (input_mode in ("REAL", "FP32", "FP64")) or (output_mode in ("REAL", "FP32", "FP64"))
	else:
		logic_error = False
	return (input_string not in ("+", "-", "*", "/", "%", "&", "|", "^", "~", "!", "2'S", "")) or logic_error

def convert_to_binary(operand, input_mode, int_bits, frac_bits):
	if input_mode == "REAL":
		return binary_string_to_int_list(real_to_twos_comp_binary(operand, int_bits, frac_bits))
	elif input_mode == "HEX":
		return binary_string_to_int_list(hexadecimal_to_binary(operand, int_bits, frac_bits, lookup_table))
	elif input_mode == "FP32":
		return ieee754_hex_to_binary(operand, precision_profile["SINGLE"], lookup_table)
	elif input_mode == "FP64":
		return ieee754_hex_to_binary(operand, precision_profile["DOUBLE"], lookup_table)
	else: 
		return binary_string_to_int_list(operand)

def binary_math_operation(operand1, operand2, operator, int_bits, frac_bits, output_mode, enable_print_statements=False):
	if operator == "/":
		max_size = int_bits + frac_bits
		if output_mode == "FP32":
			max_size = max(64, int_bits + frac_bits)
		elif output_mode == "FP64":
			max_size = max(128, int_bits + frac_bits)
		return binary_division(operand1, operand2, max_size)
	elif operator == "*":
		return binary_multiplier(operand1, operand2)
	elif operator == "+":
		addend_a, addend_b, op1_f, op2_f = binary_point_alignment(operand1, operand2, False)
		fraction_size = max(op1_f, op2_f)
		n_sum, n_carry = binary_adder(addend_a, addend_b)
		
		if ((operand1[0] == 0) and (operand2[0] == 0) and (n_sum[0] == 1)) or ((operand1[0] == 1) and (operand2[0] == 1) and (n_sum[0] == 0)):
			sum_result = [n_carry] + n_sum
		else:
			sum_result = n_sum
			
		binary_point_index = len(sum_result) - fraction_size
		return sum_result[:binary_point_index] + ['.'] + sum_result[binary_point_index:]
	elif operator == "-":
		return binary_subtraction(operand1, operand2)
	elif operator == "%":
		return binary_modulo(operand1, operand2, int_bits + frac_bits)
	elif operator == "&":
		return binary_and(operand1, operand2)
	elif operator == "|":
		return binary_or(operand1, operand2)
	elif operator == "^":
		return binary_xor(operand1, operand2)
	elif operator == "~":
		return binary_not(operand1)
	elif operator in ("!", "2'S"):
		return binary_twos_complement(operand1)

def convert_from_binary(operand, output_mode):
	if output_mode == "REAL":
		return binary_to_real(operand)
	elif output_mode == "HEX":
		return binary_to_hexadecimal(operand, lookup_table)
	elif output_mode == "FP32":
		return binary_to_ieee754(operand, precision_profile["SINGLE"], lookup_table)
	elif output_mode == "FP64":
		return binary_to_ieee754(operand, precision_profile["DOUBLE"], lookup_table)
	else:
		return "".join(int_list_to_binary_string(operand, len(operand)))
