import os
from nicegui import ui

# -------------------------
# IMPORT YOUR LOGIC MODULES
# -------------------------
from binary_support import precision_profile, lookup_table, twos_complement, binary_string_to_int_list, int_list_to_binary_string, binary_point_removal, twos_complement_bin_rational, list_to_string, remove_msbs, binary_point_alignment
from binary_conversions import real_to_twos_comp_binary, hexadecimal_to_binary, ieee754_hex_to_binary, binary_to_real, binary_to_hexadecimal, binary_to_ieee754
from binary_math import binary_division, binary_multiplier, binary_adder, binary_subtraction

# -------------------------
# GLOBAL STATE
# -------------------------
main_display = ""
aux_display = ""

HEX_NEGATIVE_LIST = ["8","9","A","B","C","D","E","F","a","b","c","d","e","f"]

MODES = [
    ("REAL"),
    ("HEX"),
    ("BIN"),
    ("FP32"),
    ("FP64")
]

# -------------------------
# VALIDATION FUNCTIONS
# -------------------------
def verify_real_input(s):
    try:
        float(s)
        return False
    except ValueError:
        return True

def verify_hex_input(s, int_bits, frac_bits):
    try:
        int(s, 16)
        return len(s) > (int_bits + frac_bits) / 4
    except ValueError:
        return True

def verify_bin_input(s):
    try:
        int(s.replace('.', ''), 2)
        return (
            s.count('.') > 1 or
            s[0] not in '01' or
            s[-1] == '.'
        )
    except ValueError:
        return True

def is_valid_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

def verify_fp32_input(s):
    return len(s) != 8 or not is_valid_hex(s)

def verify_fp64_input(s):
    return len(s) != 16 or not is_valid_hex(s)

# -------------------------
# PARSER
# -------------------------

def parse_input_string(s):
    left = ""
    op = ""
    right = ""
    i = 0
    n = len(s)

    if n == 0:
        return "", "", ""

    # First char
    if s[0] in "+-" or s[0].isalnum():
        left += s[0]
        i = 1
    else:
        return "", "", ""

    # First operand
    while i < n and s[i] not in "+-*/":
        left += s[i]
        i += 1

    if i >= n:
        return left, "", ""

    op = s[i]
    i += 1

    # Second operand
    while i < n:
        right += s[i]
        i += 1

    return left, op, right

# -------------------------
# CONVERSION FUNCTIONS
# -------------------------

def convert_to_binary(operand, mode, int_bits, frac_bits):
    if mode == "REAL":
        return binary_string_to_int_list(real_to_twos_comp_binary(operand, int_bits, frac_bits))
    elif mode == "HEX":
        return binary_string_to_int_list(hexadecimal_to_binary(operand, int_bits, frac_bits, lookup_table))
    elif mode == "FP32":
        return ieee754_hex_to_binary(operand, precision_profile["SINGLE"], lookup_table)
    elif mode == "FP64":
        return ieee754_hex_to_binary(operand, precision_profile["DOUBLE"], lookup_table)
    else:
        return binary_string_to_int_list(operand)

def convert_from_binary(operand, mode):
    if mode == "REAL":
        return binary_to_real(operand)
    elif mode == "HEX":
        return binary_to_hexadecimal(operand, lookup_table)
    elif mode == "FP32":
        return binary_to_ieee754(operand, precision_profile["SINGLE"], lookup_table)
    elif mode == "FP64":
        return binary_to_ieee754(operand, precision_profile["DOUBLE"], lookup_table)
    else:
        return "".join(int_list_to_binary_string(operand, len(operand)))

# -------------------------
# MATH OPERATION
# -------------------------

def binary_math_operation(operand1, operand2, operator):
	int_bits = int(int_bits_box.value)
	frac_bits = int(frac_bits_box.value)
	
	if (operator == "/"):
		if (output_mode.value == "FP32"):
			current_profile = precision_profile["SINGLE"]
			p = current_profile

			if (1 + p.exponent_size + p.mantissa_size) < (int_bits + frac_bits):
				max_size = int_bits + frac_bits
			else:
				max_size = 64
		elif (output_mode.value == "FP64"):
			current_profile = precision_profile["DOUBLE"]
			p = current_profile

			if (1 + p.exponent_size + p.mantissa_size) < (int_bits + frac_bits):
				max_size = int_bits + frac_bits
			else:
				max_size = 128
		else:
			max_size = int_bits + frac_bits

		operand1_no_bin_point, operand2_no_bin_point, operand1_fraction_size, operand2_fraction_size = binary_point_alignment(operand1, operand2, False)

		if (operand1[0] == 1):
			operand1_2s_comp, op1_carry = twos_complement(operand1_no_bin_point)
			sign_operand1 = 1
		else:
			operand1_2s_comp = operand1_no_bin_point
			sign_operand1 = 0

		if (operand2[0] == 1):
			operand2_2s_comp, op2_carry = twos_complement(operand2_no_bin_point)
			sign_operand2 = 1
		else:
			operand2_2s_comp = operand2_no_bin_point
			sign_operand2 = 0

		quotient = binary_division(operand1_2s_comp, operand2_2s_comp, max_size)

		if ((sign_operand1 ^ sign_operand2) == 1):
			quotient_size = len(quotient)

			if ('.' in quotient):
				quotient_radix_index = quotient.index('.')
				quotient.pop(quotient_radix_index)
			else:
				quotient_radix_index = quotient_size

			if (quotient_radix_index < quotient_size):
				quotient_fraction_size = quotient_size - (quotient_radix_index + 1)
			else:
				quotient_fraction_size = 0

			quotient_no_bin_point = quotient
			quotient_2s_comp, carry_quotient = twos_complement(quotient_no_bin_point)

			quotient_2s_comp_bin_point = quotient_2s_comp[:quotient_size - quotient_fraction_size - 1] + ['.'] + quotient_2s_comp[quotient_size - quotient_fraction_size - 1:]

			math_result_2s_comp = quotient_2s_comp_bin_point
		else:
			math_result_2s_comp = quotient
		math_result = math_result_2s_comp
	elif (operator == "*"):
		math_result = binary_multiplier(operand1, operand2)
	elif (operator == "+"):
		addend_a, addend_b, operand1_fraction_size, operand2_fraction_size = binary_point_alignment(operand1, operand2, False)

		if (operand1_fraction_size > operand2_fraction_size):
			fraction_size = operand1_fraction_size
		else:
			fraction_size = operand2_fraction_size

		n_sum, n_carry = binary_adder(addend_a, addend_b)

		if ((operand1[0] == 0) and (operand2[0] == 0) and (n_sum[0] == 1)) or ((operand1[0] == 1) and (operand2[0] == 1) and (n_sum[0] == 0)):
			sum_result = [n_carry] + n_sum
		else:
			sum_result = n_sum

		binary_point_index = len(sum_result) - fraction_size

		math_result = sum_result[:binary_point_index] + ['.'] + sum_result[binary_point_index:]
	elif (operator == "-"):
		math_result = binary_subtraction(operand1, operand2)

	return math_result
# -------------------------
# BUTTON HANDLER
# -------------------------

def process_button(val):
    global main_display, aux_display
    print(val)

    # RESET
    if val == "R" or val == "Reset":
        main_display = ""
        aux_display = ""
        input_box.set_value("")
        output_box.set_text("")
        return

    # ENTER
    if val in ["Enter", "="]:
        operand1, operator, operand2 = parse_input_string(main_display)
        operand2_present = operand2 != ""

        int_bits = int(int_bits_box.value)
        frac_bits = int(frac_bits_box.value)

        mode_in = input_mode.value
        mode_out = output_mode.value

        err1 = False
        err2 = False
        
        # VALIDATION
        if mode_in == "REAL":
            err1 = verify_real_input(operand1)
            err2 = verify_real_input(operand2) if operand2_present else False

        elif mode_in == "HEX":
            nibble_size = int_bits // 4
            if len(operand1) < nibble_size and len(operand1) > 0:
                operand1 = operand1.rjust(nibble_size, "F" if operand1[0] in HEX_NEGATIVE_LIST else "0")
            err1 = verify_hex_input(operand1, int_bits, frac_bits)

            if operand2_present:
                if len(operand2) < nibble_size and len(operand2) > 0:
                    operand2 = operand2.rjust(nibble_size, "F" if operand2[0] in HEX_NEGATIVE_LIST else "0")
                err2 = verify_hex_input(operand2, int_bits, frac_bits)
            else:
                err2 = False

        elif mode_in == "BIN":
            err1 = verify_bin_input(operand1)
            err2 = verify_bin_input(operand2) if operand2_present else False

        elif mode_in == "FP32":
            err1 = verify_fp32_input(operand1)
            err2 = verify_fp32_input(operand2) if operand2_present else False

        elif mode_in == "FP64":
            err1 = verify_fp64_input(operand1)
            err2 = verify_fp64_input(operand2) if operand2_present else False

        op_err = operator not in "+-*/"

        # EXECUTION
        if not err1 and not err2 and not op_err:
            op1_bin = convert_to_binary(operand1, mode_in, int_bits, frac_bits)

            if operand2_present:
                op2_bin = convert_to_binary(operand2, mode_in, int_bits, frac_bits)
                result_bin = binary_math_operation(op1_bin, op2_bin, operator)
                aux_display = str(convert_from_binary(result_bin, mode_out))
            else:
                aux_display = str(convert_from_binary(op1_bin, mode_out))
        else:
            aux_display = "ERROR"

        output_box.set_text(aux_display)
        return
    
    main_display += val
    input_box.set_value(main_display)

# -------------------------
# UI LAYOUT
# -------------------------

ui.add_head_html("""
<style>
body { background-color: #fef3c7; }
</style>
""")

with ui.card().classes("w-full max-w-md mx-auto p-4 bg-blue-100 border border-blue-300 rounded-sm"):
    ui.label("Input").classes('text-sm')
    input_box = ui.input(value="").classes("text-lg h-13 w-full bg-blue-50 p-2 rounded border border-blue-300")

    ui.label("Output").classes('text-sm')
    output_box = ui.label("").classes("text-sm h-10 w-full bg-blue-50 p-2 rounded border border-blue-300")

    with ui.row():
        int_bits_box = ui.input(label="Integer Bits", value="16").classes("text-xs")
        frac_bits_box = ui.input(label="Fraction Bits", value="16").classes("text-xs")

    ui.add_css('.small-radio .q-radio__label { font-size: 0.50rem; }')
    
    ui.label('Input Format').classes('text-xs')
    input_mode = ui.radio(MODES, value=MODES[0]).props('inline').classes('small-radio')

    ui.label('Output Format').classes('text-xs')
    output_mode = ui.radio(MODES, value=MODES[0]).props('inline').classes('small-radio')

    use_keypad = ui.checkbox("Use Keypad", value=True)

    keypad_container = ui.element()
    pc_buttons_container = ui.element()

    # Bind visibility
    use_keypad.bind_value_to(keypad_container, "visible")
    use_keypad.bind_value_to(pc_buttons_container, "visible", lambda v: not v)

    keypad = [
        ("7","8","9","/"),
        ("4","5","6","*"),
        ("1","2","3","-"),
        ("0",".","R","+"),
        ("A","B","C","D"),
        ("E","F","Enter","=")
    ]

    with keypad_container:
        with ui.grid(columns=4).classes("gap-2 mt-4"):
            for row in keypad:
                for key in row:
                    ui.button(key, on_click=lambda e, k=key: process_button(k)).classes("h-10 text-sm")

    with pc_buttons_container:
        with ui.row().classes("mt-4"):
            ui.button("Reset", on_click=lambda e: process_button("Reset")).classes("h-10 text-sm")
            ui.button("Enter", on_click=lambda e: process_button("Enter")).classes("h-10 text-sm")

port = int(os.environ.get('PORT', 8080))
ui.run(host='0.0.0.0', port=port, reload=False)
