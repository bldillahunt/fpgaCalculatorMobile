import os
from nicegui import ui

# -------------------------
# IMPORT YOUR LOGIC MODULES
# -------------------------
from binary_support import precision_profile, lookup_table, twos_complement, binary_string_to_int_list, int_list_to_binary_string, binary_point_removal, twos_complement_bin_rational, list_to_string, remove_msbs, binary_point_alignment
from binary_conversions import real_to_twos_comp_binary, hexadecimal_to_binary, ieee754_hex_to_binary, binary_to_real, binary_to_hexadecimal, binary_to_ieee754
from binary_math import binary_division, binary_multiplier, binary_adder, binary_subtraction, binary_modulo, binary_twos_complement
from binary_logic import binary_and, binary_or, binary_xor, binary_not
from calculator_top import compute_evaluation_step

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
		main_display_value, calculator_result = compute_evaluation_step(input_box.value, input_mode.value, output_mode.value, int(int_bits_box.value), int(frac_bits_box.value), False)
		input_box.set_value(main_display_value)
		output_box.set_text(calculator_result)
	else:
		main_display += val
		input_box.set_value(main_display)
	return

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
		("7","8","9","/", "%"),
		("4","5","6","*", "&"),
		("1","2","3","-", "|"),
		("0",".","R","+", "^"),
		("A","B","C","D", "~"),
		("E","F","Enter","=", "2's")
	]

	with keypad_container:
		with ui.grid(columns=5).classes("gap-2 mt-4"):
			for row in keypad:
				for key in row:
					ui.button(key, on_click=lambda e, k=key: process_button(k)).classes("h-10 text-sm")

	with pc_buttons_container:
		with ui.row().classes("mt-4"):
			ui.button("Reset", on_click=lambda e: process_button("Reset")).classes("h-10 text-sm")
			ui.button("Enter", on_click=lambda e: process_button("Enter")).classes("h-10 text-sm")

port = int(os.environ.get('PORT', 8080))
ui.run(host='0.0.0.0', port=port, reload=False)
