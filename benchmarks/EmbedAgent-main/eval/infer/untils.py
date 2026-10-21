from openai import OpenAI
import random
import time
import json
import re
import copy

deepseek_api_key = ""
deepseek_base_url = ""

hardware_id = {'led':0,'pushbutton':1,'rgb-led':2,'7segment':3,'led-bar-graph':4,'slide-potentiometer':5,'resistor':6,'74hc595':7, 'servo':8}
main_hardware_id = {'led':0,'pushbutton':1,'rgb-led':2,'7segment':3,'led-bar-graph':4,'slide-potentiometer':5,'servo':8}
id_main_hardware = {v: k for k, v in main_hardware_id.items()}

TOT_DATA =126

sevseg_value = {
    'null': [0, 0, 0, 0, 0, 0, 0, 0],
    '0': [1, 1, 1, 1, 1, 1, 0, 0],
    '1': [0, 1, 1, 0, 0, 0, 0, 0],
    '2': [1, 1, 0, 1, 1, 0, 1, 0],
    '3': [1, 1, 1, 1, 0, 0, 1, 0],
    '4': [0, 1, 1, 0, 0, 1, 1, 0],
    '5': [1, 0, 1, 1, 0, 1, 1, 0],
    '6': [1, 0, 1, 1, 1, 1, 1, 0],
    '7': [1, 1, 1, 0, 0, 0, 0, 0],
    '8': [1, 1, 1, 1, 1, 1, 1, 0],
    '9': [1, 1, 1, 1, 0, 1, 1, 0],
    'A': [1, 1, 1, 0, 1, 1, 1, 0],
    'P': [1, 1, 0, 0, 1, 1, 1, 0],
    'E': [1, 0, 0, 1, 1, 1, 1, 0],
    '0.': [1, 1, 1, 1, 1, 1, 0, 1],
    '1.': [0, 1, 1, 0, 0, 0, 0, 1],
    '2.': [1, 1, 0, 1, 1, 0, 1, 1],
    '3.': [1, 1, 1, 1, 0, 0, 1, 1],
    '4.': [0, 1, 1, 0, 0, 1, 1, 1],
    '5.': [1, 0, 1, 1, 0, 1, 1, 1],
    '6.': [1, 0, 1, 1, 1, 1, 1, 1],
    '7.': [1, 1, 1, 0, 0, 0, 0, 1],
    '8.': [1, 1, 1, 1, 1, 1, 1, 1],
    '9.': [1, 1, 1, 1, 0, 1, 1, 1],
    'A.': [1, 1, 1, 0, 1, 1, 1, 1],
    'P.': [1, 1, 0, 0, 1, 1, 1, 1],
    'E.': [1, 0, 0, 1, 1, 1, 1, 1]
}

init_connection = {
    "version": 1,
    "author": "Anonymous maker",
    "editor": "wokwi",
    "parts": [ { "type": "wokwi-arduino-uno", "id": "uno", "top": 0, "left": 0, "attrs": {} } ],
    "connections": [],
    "dependencies": {}
}
platform_parts = {
    "Pi-Pico" : { "id": "pico", "type": "wokwi-pi-pico", "top": 0, "left": 0, "attrs": { "env": "micropython-20231227-v1.22.0" } },
    "Arduino Mega" : { "type": "wokwi-arduino-mega", "id": "mega", "top": 0, "left": 0, "attrs": {} },
    "Arduino Uno Rev3" : { "type": "wokwi-arduino-uno", "id": "uno", "top": 0, "left": 0, "attrs": {} },
    "ESP32": { "type": "board-esp32-devkit-c-v4", "id": "esp", "top": 0, "left": 0, "attrs": { "builder": "esp-idf" }}
}
# size : [up, left, right]
# 看两个硬件判断位置：slide-potentiometer1, 7segment1
platform_message = {
    "Arduino Uno Rev3":{
        "size" : [[-158,-178.4],[-71.82,293.1]],
        "pin_map": [0,1,2,3,4,5,6,7,8,9,10,11,12,13]
    },
    "Arduino Mega":{
        "size" : [[-158,-178.4],[-196.62,408.28]],
        "pin_map": [2,3,4,5,6,7,8,9,10,11,12,13,44,45]
    },
    "Pi-Pico":{
        "size" : [[-158,-178.4],[-71.82,293.1]],
        "version": "v1.22.0"
    },
    "ESP32":{
        "size" : [[-158,-178.4],[-71.82,293.1]],
        "version": "v5.3.1"
    }
}

platform_description = {
    "Pi-Pico":"""type: pi-pico
pins: 
`GP0` to `GP22`: Digital GPIO pins for input/output operations.
`GP26` to `GP28`: Analog input pins (can also be used as digital GPIO pins).
`GND.1` to `GND.8`: Ground pins
`VSYS`, `VBUS`, `3V3`: Positive power supply""",
    "Arduino Uno Rev3":"""type: arduino-uno
pins: 
`0` to `13`: Digital GPIO pins for input/output operations.
`A0` to `A5`: Analog input pins (can also be used as digital GPIO pins).
`GND.1`, `GND.2`, `GND.3`: Ground pins for connecting to the circuit's ground.
`VIN`: Input voltage pin for external power supply (7-12V recommended).
`5V`: Output pin providing 5V power to connected components.""",
    "Arduino Mega":"""type: arduino-mega
pins:
`0` to `53`: Digital GPIO pins for input/output operations.
`A0` to `A15`: Analog input pins (can also be used as digital GPIO pins).
`GND.1` to `GND.5`: Ground pins for connecting to the circuit's ground.
`VIN`: Input voltage pin for external power supply (7-12V recommended).
`5V`: Output pin providing 5V power to connected components.
Digital pins `2` … `13`, `44`, `45`, and `46` have hardware PWM support (total of 15 PWM channels).
""",
    "ESP32":"""type: esp32-devkit-c-v4
pins:
`0`, `2`, `4`, `5`, `12`, `13`, `14`, `15`, `16`, `17`, `18`, `19`, `21`, `22`, `23`, `25`, `26`, `27`, `32`, `33`, `34`, `35`: GPIO pins
`GND.1` to `GND.3`: Ground pins
`3V3`: Positive power supply"""

}

# driver.save_screenshot('screenshot.png')


def extract_code(response,mark,lang=""):
    response = response.split("</think>")[-1]
    response = response.replace("[\\/","[/")
    response = response.replace("[ /","[/")
    mark_end = mark.replace("[", "[/")
    raw_response = response
    flag = False
    if response.find(mark) != -1:
        response = response.split(mark)[1]
        if response.find(mark_end) != -1:
            response = response.split(mark_end)[0]
        flag = True
    if lang != "" and response.find("```" + lang) != -1:
        # use re extrat ```lang ```
        try:
            response = re.findall(r'```' + lang + r'(.+?)```', response, re.DOTALL)[-1]
        except:
            response += "```"
            response = re.findall(r'```' + lang + r'(.+?)```', response, re.DOTALL)[-1]
        flag = True
    if flag == False:
        return False
    return response


def add_retrieve_code(problem, hardware_lst, code_blocks, example_path="/mnt/ceph_home/xuruiyang2022/141nfs/code/iot/dataset/few_shot_examples.json"):
    example_data = read_json(example_path)
    retrieve_code = f"""### Retrieve Code
Here are some retrieved code snippets that may be helpful for solving the problem:
"""
    for index,num in enumerate(hardware_lst):
        if num > 0 and index in id_main_hardware:
            retrieve_code += f"""{code_blocks[0]}
{extract_code(example_data[id_main_hardware[index]]['response'],"[Arduino Code]","arduino")}
{code_blocks[1]}
"""
    return problem + retrieve_code

def gpt_response(prompt, api_key, base_url, parameters, n=100):
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=None)

    for i in range(n):
        try:
            if parameters['stop'] == '':
                parameters['stop'] = None
            response = client.chat.completions.create(
                extra_body={},
                model=parameters['model'],
                messages=prompt,
                temperature = parameters['temperature'],
                stream=False,
                max_tokens=parameters['max_tokens'],
                stop=parameters['stop'],
            )
            try:
                reasoning_content = response.choices[0].message.reasoning_content
                content = response.choices[0].message.content
                return "<think>" + reasoning_content + "</think>\n" + content
            except:
                try:
                    reasoning_content = response.choices[0].message.reasoning
                    content = response.choices[0].message.content
                    return "<think>" + reasoning_content + "</think>\n" + content
                except:
                    return response.choices[0].message.content
        except Exception as e:
            print(e)
            time.sleep(1)
            continue
        
def read_json(path):
    if path.endswith('.json'):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif path.endswith('.jsonl'):
        data = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line))
        return data
    else:
        raise ValueError('Invalid file format. Only .json and .jsonl are supported.')

# def continue_from_previous(path,pre_path,correct_status):
#     compiled_dict = read_json(path)
#     # 如果全对，那就不用继续了
#     flag = False
#     for sample in compiled_dict:
#         if sample['status'] not in correct_status:
#             flag = True
#             break
#     if not flag:
#         print("All samples have been compiled, exit.")
#         exit(0)
#     with open(pre_path, 'w', encoding='utf-8') as f:
#         for sample in compiled_dict:
#             f.write(json.dumps(sample, ensure_ascii=False) + '\n')
#     return compiled_dict

def get_hardwares(diagram):
    hardwares = []
    for hardware in diagram['parts']:
        hardwares.append({"type": hardware['type'].replace("wokwi-", ""), "id": hardware['id']})
    return hardwares


def remove_annotation(code,lang):
    if lang in ['c','cpp']:
        code = re.sub(r'//.*','',code)
        code = re.sub(r'\/\*.*?\*\/','',code,flags=re.DOTALL)
    elif lang == 'python':
        code = re.sub(r'#.*','',code)
    code = code.split('\n')
    code = '\n'.join([i for i in code if i.strip() != ''])
    return code

def click_button(btn, actions, consist_time=0.15):
    actions.move_to_element(btn).click_and_hold().perform()
    time.sleep(consist_time)
    actions.release().perform()


def get_clock(clock):
    miniute, sec = clock.split(':')
    tot_time = int(miniute) * 60 + float(sec)
    return tot_time


def create_hardware_pos(connections, hardwares, platform_pos=[[-158,-178.4],[-71.82,293.1]]):
    # generate the posision of each hardwares
    cnt_hardware = {k:-1 for k in hardware_id.keys()}
    for hardware in hardwares:
        if hardware['type'] in ['arduino-uno','arduino-mega','pi-pico']:
            continue
        cnt_hardware[hardware['type']] += 1
        if hardware['type'] == 'led':
            connections['parts'].append({
                'type': f'wokwi-{hardware["type"]}',
                'id': hardware['id'],
                'top': round(platform_pos[0][0]+87.2,1),
                'left': round(
                    platform_pos[0][1]+191.8+cnt_hardware[hardware['type']]*57.6,
                    1
                ),
                'attrs': { 'color': 'red' }
            })
        elif hardware['type'] == 'pushbutton':
            connections['parts'].append({
                'type': f'wokwi-{hardware["type"]}',
                'id': hardware['id'],
                'top': round(platform_pos[0][0]-37.4,1),
                'left': round(
                    platform_pos[0][1]+197.6+cnt_hardware[hardware['type']]*85.8,
                    1
                ),
                'attrs': { 'color': 'green' }
            })
        elif hardware['type'] == 'rgb-led':
            connections['parts'].append({
                'type': f'wokwi-{hardware["type"]}',
                'id': hardware['id'],
                'top': round(platform_pos[0][0]+27.6,1),
                'left': round(
                    platform_pos[0][1]+217.9+cnt_hardware[hardware['type']]*57.6,
                    1
                ),
                'attrs': {'common': 'cathode'}
            })
        elif hardware['type'] == '7segment':
            connections['parts'].append({
                'type': f'wokwi-{hardware["type"]}',
                'id': hardware['id'],
                'top': round(platform_pos[1][0],1),
                'left': round(
                    platform_pos[1][1]+cnt_hardware[hardware['type']]*86.4,
                    1
                ),
                'attrs': { }
            })
        elif hardware['type'] == 'led-bar-graph':
            connections['parts'].append({
                'type': f'wokwi-{hardware["type"]}',
                'id': hardware['id'],
                'left': round(platform_pos[1][1]+9.3,1),
                'top': round(
                    platform_pos[1][0]+182.4+cnt_hardware[hardware['type']]*115.2,
                    1
                ),
                'attrs': {'color': 'lime'}
            })
        elif hardware['type'] == 'slide-potentiometer':
            connections['parts'].append({
                'type': f'wokwi-{hardware["type"]}',
                'id': hardware['id'],
                'top': round(platform_pos[0][0],1),
                'left': round(
                    platform_pos[0][1]+cnt_hardware[hardware['type']]*(-115.2),
                    1
                ),
                "rotate": 270,
                'attrs': { 'travelLength': '30' }
            })
        elif hardware['type'] == 'resistor':
            connections['parts'].append({
                'type': f'wokwi-{hardware["type"]}',
                'id': hardware['id'],
                'left': round(platform_pos[1][1]+52.5,1),
                'top': round(
                    platform_pos[1][0]+182+cnt_hardware[hardware['type']]*19.2,
                    1
                ),
                'attrs': { 'value': '1000' }
            })
        elif hardware['type'] == '74hc595':
            connections['parts'].append({
                'type': f'wokwi-{hardware["type"]}',
                'id': hardware['id'],
                'top': round(platform_pos[1][0]+109,1),
                'left': round(
                    platform_pos[1][1] + cnt_hardware[hardware['type']]*86.4,
                    1
                ),
                'attrs': {}
            })
        elif hardware['type'] == 'servo':
            connections['parts'].append({
                'type': f'wokwi-{hardware["type"]}',
                'id': hardware['id'],
                'left': round(platform_pos[0][1]-23.2,1),
                'top': round(
                    platform_pos[0][0]+146.4+cnt_hardware[hardware['type']]*91,
                    1
                ),
                'attrs': {}
            })
    return connections

def complete_connection(connections, hardwares, platform):
    try:
        connections = connections.replace('], [','],\n[')
        connections = connections.replace('],',']')
        connections = remove_annotation(connections,'c')
        connections = remove_annotation(connections,'python')
        raw_connections = connections.strip().split("\n")
        connections = []
        for raw_connection in raw_connections:
            if raw_connection == '': continue
            connections.append(raw_connection)
        connections = eval('['+', '.join(connections)+']')
        for connection in connections:
            if len(connection) != 2 : return False
            if len(connection[0].split(':')) != 2 : return False
            if len(connection[1].split(':')) != 2 : return False
    except Exception as e:
        return False
    tgt_connection = copy.deepcopy(init_connection)
    try:
        tgt_connection['parts'] = [platform_parts[platform]]
        tgt_connection = create_hardware_pos(tgt_connection, hardwares, platform_pos=platform_message[platform]['size'])
    except:
        return False
    if platform == "ESP32":
        tgt_connection['connections'].extend(
            [ [ "esp:TX", "$serialMonitor:RX", "", [] ], [ "esp:RX", "$serialMonitor:TX", "", [] ] ]
            )
    for connection in connections:
        connection.append('black')
        tgt_connection['connections'].append(connection)
    return tgt_connection

def correct_connection(hardware,pin_start,Ai,pin_map=[0,1,2,3,4,5,6,7,8,9,10,11,12,13]):
    # hardware: {"type":xx,"id":xx}
    # add the correct connection of each hardware
    if hardware['type'] == 'led':
        connection = [
            [ "uno:GND.1", f"{hardware['id']}:C", "black"],
            [ f"{hardware['id']}:A", f"uno:{pin_map[pin_start]}", "red" ]
        ]
        pin_start += 1
        return connection, pin_start,Ai
    elif hardware['type'] == 'pushbutton':
        connection = [
            [ "uno:GND.1", f"{hardware['id']}:2.r", "black"],
            [ f"uno:{pin_map[pin_start]}", f"{hardware['id']}:1.l", "green" ]
        ]
        pin_start += 1
        return connection, pin_start,Ai
    elif hardware['type'] == 'rgb-led':
        connection = [
            [ "uno:GND.1", f"{hardware['id']}:COM", "black"],
            [ f"uno:{pin_map[pin_start]}", f"{hardware['id']}:R", "red" ],
            [ f"uno:{pin_map[pin_start+1]}", f"{hardware['id']}:G", "green" ],
            [ f"uno:{pin_map[pin_start+2]}", f"{hardware['id']}:B", "blue" ]
        ]
        pin_start += 3
        return connection, pin_start ,Ai
    elif hardware['type'] == '7segment':
        if hardware['id'] == 'sevseg1':
            connection = [
                [ "uno:5V", "sr1:VCC", "red"],
                [ f"uno:A{Ai+2}", "sr1:SHCP", "gray"],
                [ f"uno:A{Ai+1}", "sr1:STCP", "purple"],
                [ f"uno:A{Ai}", "sr1:DS", "blue"],
                [ "sr1:VCC", "sr1:MR", "red"],
                [ "sr1:MR", "sevseg1:COM.1", "red"],
                [ "sr1:Q1", "sevseg1:B", "green"],
                [ "sr1:Q2", "sevseg1:C", "green"],
                [ "sr1:Q3", "sevseg1:D", "green"],
                [ "sr1:Q4", "sevseg1:E", "green"],
                [ "uno:GND.3", "sr1:GND", "black"],
                [ "sr1:GND", "sr1:OE", "black"],
                [ "sr1:Q0", "sevseg1:A", "green"],
                [ "sr1:Q5", "sevseg1:F", "green"],
                [ "sr1:Q6", "sevseg1:G", "green"]
            ]
        elif hardware['id'] == 'sevseg2':
            connection = [
                [ "sr1:SHCP", "sr2:SHCP", "gray"],
                [ "sr1:STCP", "sr2:STCP", "purple"],
                [ "sr1:Q7S", "sr2:DS", "blue"],
                [ "sr1:VCC", "sr2:MR", "red"],
                [ "sr1:VCC", "sr2:VCC", "red"],
                [ "sr1:OE", "sr2:OE", "black"],
                [ "sevseg1:COM.1", "sevseg2:COM.1", "red"],
                [ "sr2:Q0", "sevseg2:A", "green"],
                [ "sr2:Q1", "sevseg2:B", "green"],
                [ "sr2:Q2", "sevseg2:C", "green"],
                [ "sr2:Q3", "sevseg2:D", "green"],
                [ "sr2:Q4", "sevseg2:E", "green"],
                [ "sr2:Q5", "sevseg2:F", "green"],
                [ "sr2:Q6", "sevseg2:G", "green"],
                [ "sr1:GND", "sr2:GND", "black"]
            ]
        else:
            raise ValueError("Unknown sevseg id")
        return connection, pin_start,Ai+3

    elif hardware['type'] == 'led-bar-graph':
        connection = []
        for i in range(pin_start,min(pin_start+10,14)):
            connection.append([f"uno:{pin_map[i]}", f"{hardware['id']}:A{i-pin_start+1}", "green"])
            connection.append([f"uno:GND.1", f"{hardware['id']}:C{i-pin_start+1}", "black"])
        return connection, min(pin_start+10,14), Ai
    elif hardware['type'] == 'slide-potentiometer':
        connection = [
            [ f"{hardware['id']}:GND", "uno:GND.1", "black"],
            [ f"{hardware['id']}:VCC", "uno:5V", "red"],
            [ f"{hardware['id']}:SIG", f"uno:A{Ai}", "black"]
        ]
        return connection, pin_start, Ai+1
        
    elif hardware['type'] == 'servo':
        connection = [
            [f"uno:{pin_map[pin_start]}", f"{hardware['id']}:PWM", "orange"],
            ["uno:5V", f"{hardware['id']}:V+", "red"],
            ["uno:GND.1", f"{hardware['id']}:GND", "black"]
        ]
        return connection, pin_start+1,Ai
    elif hardware['type'] in ['resistor','74hc595']:
        return [], pin_start,Ai
    else:
        raise ValueError("Unknown hardware type")

def create_connection(hardwares, platform="Arduino Uno Rev3"):
    tgt_connection = copy.deepcopy(init_connection)
    tgt_connection['parts'] = [platform_parts[platform]]
    tgt_connection = create_hardware_pos(tgt_connection, hardwares, platform_pos=platform_message[platform]['size'])
    cur_pin = 0
    cur_A = 0
    for hardware in hardwares:
        current_connection, pin_start,cur_A = correct_connection(hardware, cur_pin, cur_A, platform_message[platform]['pin_map'])
        for connection in current_connection:
            for index,pin in enumerate(connection):
                connection[index] = pin.replace("uno:",f"{platform_parts[platform]['id']}:")
        cur_pin = pin_start
        if cur_pin > 14: raise ValueError("Too many hardware")
        tgt_connection['connections'].extend(current_connection)
    return tgt_connection

def correct_sleep(sleep_time,clock):
    cur_time = get_clock(clock.text)
    time.sleep(sleep_time-cur_time)

# embed description and prompt
# {LED : 0, Pushbutton : 1, RGB LED : 2, Seven Segment Display : 3, LED Bar Graph : 4, Slide Potentiometer : 5 , Resistor : 6, 74HC595 Shift Register : 7}
embed_description = {}
# LED
embed_description[0] = {
    "name": "LED",
    "id": 0,
    "description": """type: led
pins: 
`A`: The positive pin of the LED. 
`C`: The negative pin of the LED."""
}
# Pushbutton
embed_description[1] = {
    "name": "Pushbutton",
    "id": 1,
    "description": """type: pushbutton
pins: 
`1.l` / `1.r`: First contact (left and right pins).
`2.l` / `2.r`: Second contact (left and right pins).
usage:
Connect one pin of the first contact (e.g., `1.r` or `1.l`) to a digital pin configured as INPUT_PULLUP.
Connect one pin of the second contact (e.g., `2.r` or `2.l`) to the ground (GND).
The digital pin will read LOW when the button is pressed and HIGH when the button is not pressed.
Note:
When using the pushbutton, consider adding debouncing to handle the **0.15-second** press duration and avoid false triggers caused by mechanical vibrations.
"""
}
# RGB LED
embed_description[2] = {
    "name": "RGB LED",
    "id": 2,
    "description": """type: rgb-led
pins: 
`R`: Controls the brightness of the red LED.
`G`: Controls the brightness of the green LED.
`B`: Controls the brightness of the blue LED.
`COM`: Common pin, connected to the circuit's ground (cathode)"""
}
# Seven Segment Display
embed_description[3] = {
    "name": "Seven Segment Display",
    "id": 3,
    "description": """type: 7segment
pins: 
`A`: Top segment
`B`: Top-right segment
`C`: Bottom-right segment
`D`: Bottom segment
`E`: Bottom-left segment
`F`: Top-left segment
`G`: Middle segment
`DP`: Dot LED
`COM.1` / `COM.2`: Common anode pins for connecting to power supply. (anode)"""
}
# LED Bar Graph
embed_description[4] = {
    "name": "LED Bar Graph",
    "id": 4,
    "description": """type: led-bar-graph
pins: 
`A1` to `A10`: Anode (positive pin) of LED
`C1` to `C10`: Cathode (negative pin) of LED"""
}
# Slide Potentiometer
embed_description[5] = {
    "name": "Slide Potentiometer",
    "id": 5,
    "description": """type: slide-potentiometer
pins: 
`GND`: Ground
`SIG`: Output, connect to an analog input pin
`VCC`: Supply voltage
attributes:
value: the value of the potentiometer is between 0 and 1023."""
}
# Resistor
embed_description[6] = {
    "name": "Resistor",
    "id": 6,
    "description": """type: resistor
pins: 
`1`: First pin of the resistor. It connects to one point in the circuit to allow current to flow through the resistor.
`2`: Second pin of the resistor. It connects to another point in the circuit, completing the path for current to flow through the resistor.
Attributes:
value: Specifies the resistance in ohms (Ω). The value is "1000" (1 kΩ)."""
}
# 74HC595 Shift Register
embed_description[7] = {
    "name": "74HC595 Shift Register",
    "id": 7,
    "description": """type: 74hc595
pins: 
`DS`: Receives serial data to be shifted into the register.
`SHCP`: Clock signal to shift data into the register on each rising edge.
`STCP`: Latches the shifted data to the output pins on a rising edge.
`OE`: Enables the outputs when low. Connect to GND if not used.
`Q0` to `Q7`: 8-bit parallel output pins for driving external devices.
`MR`: Clears the shift register when low. Connect to VCC if not used.
`GND`: Ground pin for connecting to the circuit's ground.
`VCC`: Supply voltage pin (typically 5V) for powering the chip."""
}
# Servo
embed_description[8] = {
    "name": "Servo",
    "id": 8,
    "description": """type: servo
pins: 
`PWM`: Servo control signal.
`V+`: Positive voltage (5V).
`GND`: Ground."""
}
# board-grove-oled-sh1107
embed_description[9] = {
    "name": "board-grove-oled-sh1107",
    "id": 9,
    "type":1,
    "description": """type: board-grove-oled-sh1107
pins: 
`SCL`: I2C Clock.
`SDA`: I2C Data.
`VCC`: Power.
`GND`: Ground."""
}
# a4988
embed_description[10] = {
    "name": "a4988",
    "id": 10,
    "type":4,
    "accompany_id":-1,
    "description": """type: a4988
description: Stepper Motor Driver
pins: 
`ENABLE`: Enable pin, active low (pulled down), default Low(0).
`MS1`: Microstep select pin 1, default Low(0).
`MS2`: Microstep select pin 2, default Low(0).
`MS3`: Microstep select pin 3, default Low(0).
`SLEEP`: Sleep pin, active low (pulled up), default High (1).
`STEP`: Step input, connect to microcontroller.
`DIR`: Direction input: 0=counterclockwise, 1=clockwise.
`GND`: Ground.
`VDD`: Logic power supply.
`1B`: Connect to motor's B-
`1A`: Connect to motor's B+
`2A`: Connect to motor's A+
`2B`: Connect to motor's A-
Note: Digital pins with a default value of Low (0) are pulled-down, and pins with a default value of High (1) are pulled up. Pins without a default value are floating."""
}
# dht22
embed_description[11] = {
    "name": "dht22",
    "id": 11,
    "type":1,
    "description": """type: dht22
description: Digital Humidity and Temperature sensor
pins: 
`VCC`: Positive voltage.
`SDA`: Digital data pin (input/output).
`GND`: Ground."""
}


if __name__ == "__main__":
    # hardwares = [{'type':'led','id':'led1'},
    #             {'type':'pushbutton','id':'pushbutton1'},
    #             {'type':'rgb-led','id':'rgb-led1'},
    #             {'type':'7segment','id':'sevseg1'},
    #             {'type':'led-bar-graph','id':'led-bar-graph1'},
    #             {'type':'slide-potentiometer','id':'slide-potentiometer1'},
    #             {'type':'resistor','id':'resistor1'},
    #             {'type':'74hc595','id':'74hc5951'},
    #             {'type':'servo','id':'servo1'},
    #             {'type':'led','id':'led2'},
    #             {'type':'pushbutton','id':'pushbutton2'},
    #             {'type':'rgb-led','id':'rgb-led2'},
    #             {'type':'7segment','id':'sevseg2'},
    #             {'type':'slide-potentiometer','id':'slide-potentiometer2'},
    #             {'type':'resistor','id':'resistor2'},
    #             {'type':'74hc595','id':'74hc5952'},
    #             {'type':'servo','id':'servo2'},
    #             {'type':'led','id':'led3'},
    #             {'type':'pushbutton','id':'pushbutton3'},
    #             {'type':'rgb-led','id':'rgb-led3'},
    #             {'type':'7segment','id':'sevseg3'},
    #             {'type':'slide-potentiometer','id':'slide-potentiometer3'},
    #             {'type':'resistor','id':'resistor3'},
    #             {'type':'74hc595','id':'74hc5953'},
    #             {'type':'servo','id':'servo3'}]
    # # s = create_connection(hardwares)
    # s = create_hardware_pos(init_connection,hardwares)
    # s = str(s).replace("'", '"')
    # print(s)
    connections = """['pico:GND.1', 'rgb1:COM']
['pico:GP0', 'rgb1:R']
['pico:GP1', 'rgb1:G']
['pico:GP2', 'rgb1:B']
['pot1:GND', 'pico:GND.1']
['pot1:VCC', 'pico:3V3']
['pot1:SIG', 'pico:GP26']"""
    hardwares = [{'type':'rgb-led','id':'rgb1'},
                {'type':'slide-potentiometer','id':'pot1'}
                ]
    s = complete_connection(connections,hardwares,'Pi-Pico')
    s = str(s).replace("'", '"')
    print(s)
                                            