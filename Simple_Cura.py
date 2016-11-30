#Name: Prepare for Simple 2016
#Created By: Rob Giseburt
#Info: Fixes the code for printing on a Printrbot Simple 2016
#Depend: GCode
#Type: postprocess
#Param: eto(string:A) Change E to (A/B)
#Param: fanOutput(int:4) Cooling Fan Output (4)
#Param: fanMinInValue(float:255) Maximum Fan Input (S) Value (255)
#Param: fanMinOutValue(float:0.2) Minimum Fan Output Value (0.0-1.0)
#Param: fanMaxOutValue(float:1.0) Maximum Fan Output Value (0.0-1.0)
#Param: minTraverseSpeed(float:499.0) Minumum Traverse (G0) speed (500)


#: filamentDiameter(float:1.75) Filament Diameter (mm, copy)
#: layerHeight(float:0.2) Layer Height (mm, copy)
#: adjustCorners(bool:True) Make Corner Adjustments

import re
import math
import copy
import pprint

def write_move(positions, f):
    line_split = []
    print_list = ['x', 'y', 'z', 'a', 'b']
    line_split.append(positions[1]['head'])
    if 'f' in positions[1] and ((positions[1]['g1'] and positions[1]['f'] != positions[0]['last_f']) or (positions[1]['head'] == "G28.2" or positions[1]['head'] == "G38.2")):
        positions[0]['last_f'] = positions[1]['f']
        print_list.append('f')

    for n in print_list:
        if n in positions[1] and (positions[1]['head'] == "G28.2" or positions[1]['head'] == "G38.2" or positions[1]['head'] == "G92" or positions[0][n] != positions[1][n]):
            line_split.append(" %s%.6f"%(n.upper(), positions[1][n]))
            positions[0][n] = positions[1][n]

    for n in ['a-orig', 'b-orig']:
        if n in positions[1]:
            positions[0][n] = positions[1][n]

    line_split.append("%s\n"%positions[1]['tail'])

    line = "".join(line_split)
    f.write(line)

    if 'between' in positions[1] and positions[1]['between'] != "":
        f.write(positions[1]['between'])

    positions.pop(1) # remove the move we "just" (are about to) write form the positions list


with open(filename, "r") as f:
    lines = f.readlines()

    adjustCorners = False
    filamentDiameter = 1.75 # default until we see a comment
    layerHeight = 0.2 # default until we see a comment

    # storage for the last three positions
    positions = [
        {'x': 0.0, 'y': 0.0, 'z': 0.0, 'a': 0.0, 'a-orig': 0.0, 'b': 0.0, 'b-orig': 0.0, 'f': 0.0, 'last_f': 0.0},
        {'g1': False, 'head':"", 'tail': "", 'between': "", 'fake': True}
    ]

    # positions[0] is the "current position" meaning the last position we have
    #              written, and the start position of position [1].
    # positions[1] is the end position of the first unwritten move, and the start
    #              position of positions[2]
    # positions [2] is the last position we have parsed.

    # keep track of ho much we've adjusted E
    filament_offset = {'a': 0.0, 'b': 0.0}
    filament_letter = eto.lower()

    filament_mm3_per_mm = math.pi * math.pow(filamentDiameter/2.0, 2)

    with open(filename, "w") as f:
        f.write(";Modified with G2 postprocess 0.1\n")

        last_layer_height = 0

        for line in lines:
            match = re.search(r"^;CURA_PROFILE_STRING:", line)
            if (match != None):
                continue

            #;$filament_diameter=1.8
            #;$layer_height=0.2
            match = re.search(r"^;\$(filament_diameter|layer_height)=([-+0-9.]+)", line)
            if (match != None):
                if match.group(1) == "filament_diameter":
                    filamentDiameter = float(match.group(2))
                    filament_mm3_per_mm = math.pi * math.pow(filamentDiameter/2.0, 2)
                if match.group(1) == "layer_height":
                    layerHeight = float(match.group(2))
                continue

            line_split = list(line.partition(";"))

            # Fix active comments
            line_split[0] = re.sub(r"\(\?(.*)\?\)", "({\\1})", line_split[0])

            # Fix E to A or B
            line_split[0] = re.sub(r"^([^;\(\)]+)[Ee]([+-.0-9]+)", "\\1"+eto+"\\2", line_split[0])

            # Fix assinine G0 F...
            # line_split[0] = re.sub(r"^[Gg]0 *(.*?)([Ff][-.0-9]+ *)(.*)$", "G1 \\2 ;Feedrate\nG0 \\1\\3", line_split[0])

            # Fix G28
            line_split[0] = re.sub(r"^[Gg]28\b *((?:[XxYxZzAaBbCcDd][+-.0-9]+ *)+)(.*)$", "G28.2\\1;\\2", line_split[0])

            # Fix M84
            line_split[0] = re.sub(r"^[Mm]84\b(.*)$", ";M84\\1", line_split[0])

            # # Retraction should be using G0, not G1 with a feedrate
            # match = re.search(r"^[Gg]1 *((?:[FfAaBb][+-.0-9]+ *?)+)( *;.*)?$", line_split[0])
            # if match != None:
            #     tail = match.group(2)
            #     if tail == None:
            #         tail = ""
            #     new_line = ["G0"]
            #     for option in re.findall(r"([FfAaBb])([+-.0-9]+) *", match.group(1)):
            #         if option[0] in ['a', 'A', 'b', 'B']:
            #             new_line.append("".join(option))
            #     line_split[0] = " ".join(new_line) + tail + "\n"

            # G92 -> G28.3
            # line_split[0] = re.sub(r"^[Gg]92([^0-9.].*)$", "G28.3\\1", line_split[0])

            # Alter fan controls - no speed control available yet
            # line_split[0] = re.sub(r"([Mm]106\s*[sS]([0-9.]+))", "M100 ({out%s:1}); Was: \\1" % (fanOutput), line_split[0])
            match = re.search(r"([Mm]106\s*[sS]([0-9.]+))", line_split[0])
            if match != None:
                in_speed = float(match.group(2))
                out_speed = fanMinOutValue + (in_speed/fanMinInValue) * (fanMaxOutValue-fanMinOutValue)
                line_split[0] = "M100 ({out%s:%.3f}); Was: %s\n" % (fanOutput, out_speed, match.group(1))
            line_split[0] = re.sub(r"([Mm]107\s*(.*))", "M100 ({out%s:0}); Was: \\1" % (fanOutput), line_split[0])

            # Correct temperature controls
            # M104 S190 - "Set the temperature of the current extruder to 190oC and return control to the host immediately"
            line_split[0] = re.sub(r"([Mm]104\s*[sS]([0-9.]+))", "M100 ({he1st:\\2}); Was: \\1", line_split[0])
            line_split[0] = re.sub(r"([Mm]109\s*[sSrR]([0-9.]+))", "M100 ({he1st:\\2}); Was: \\1\nM101 ({he1at:t}); wait for At Temp", line_split[0])
            line_split[0] = re.sub(r"([Mm]140\s*[sS]([0-9.]+))", "M100 ({he3st:\\2}); Was: \\1", line_split[0])
            line_split[0] = re.sub(r"([Mm]190\s*[sSrR]([0-9.]+))", "M100 ({he3st:\\2}); Was: \\1\nM101 ({he3at:t}); wait for At Temp", line_split[0])

            # Remove errant T[01]s
            line_split[0] = re.sub(r"^([Tt][01])\b", ";\\1", line_split[0])

            # Fix text outputs
            line_split[0] = re.sub(r"([Mm]117)(.*)$", "({msg:\\2})", line_split[0])

            # Record last position.
            # Also check for two G1's in a row.
            match = re.search(r"^[Gg]([01]|28\.2|38\.2|92) *((?:[FfXxYyZzAaBb][+-.0-9]+ *?)+)( *;.*)?$", line_split[0])
            if match != None:
                g0_or_1 = match.group(1)
                positionals = match.group(2)
                tail = match.group(3)
                if tail == None:
                    tail = ""

                new_pos = {
                    'g1': (g0_or_1 == "1"),
                    'head': 'G' + g0_or_1,
                    'tail': tail,
                    'between': ""
                }

                has_non_feedrate = False
                has_non_filament = False

                for option in re.findall(r"([XxYyZzAaBbFf])([+-.0-9]+) *", positionals):
                    if option[0].lower() in ['a', 'b']:
                        new_pos[option[0].lower()+'-orig'] = float(option[1])
                        new_pos[option[0].lower()] = float(option[1]) + filament_offset[option[0].lower()]
                        has_non_feedrate = True

                    if option[0].lower() in ['x', 'y', 'z']:
                        new_pos[option[0].lower()] = float(option[1])
                        has_non_feedrate = True
                        has_non_filament = True

                    if option[0].lower() in ['f']:
                        new_pos['f'] = float(option[1])
                        feedrate = new_pos['f']
                    elif 'f' in positions[1]:
                        feedrate = positions[1]['f']
                    else:
                        feedrate = minTraverseSpeed+1

                # Here we catch retractions that are using G1 and convert them to G0
                if has_non_filament == False and new_pos['g1'] == True and feedrate > minTraverseSpeed:
                    new_pos['g1'] = False
                    new_pos['head'] = 'G0'

                if has_non_feedrate:
                    positions.append(new_pos)

                    line_split = []

                    if not 'fake' in positions[1]:
                        if adjustCorners and positions[1]['g1'] and positions[2]['g1']:
                            # p1 X
                            p0 = [positions[0]['x'],positions[0]['y']]

                            p1 = copy.copy(p0)
                            p1 = [positions[0]['x'],positions[0]['y']]
                            if 'x' in positions[1]:
                                p1[0] = positions[1]['x']
                            if 'y' in positions[1]:
                                p1[1] = positions[1]['y']

                            # vector from 1 to 2
                            v0_1 = [p1[0]-p0[0], p1[1]-p0[1]]
                            # magnitude of vector from 1 to 2
                            m0_1 = math.sqrt(v0_1[0]*v0_1[0]+v0_1[1]*v0_1[1])
                            # unit vector from 1 to 2
                            uv0_1 = [v0_1[0]/m0_1, v0_1[1]/m0_1]
                            # filament delta
                            f_d1 = positions[1][filament_letter+'-orig'] - positions[0][filament_letter+'-orig']
                            path_width1 = math.fabs((filament_mm3_per_mm*f_d1)/(layerHeight*m0_1)) # - ((math.pi*layerHeight)/4)

                            p2 = copy.copy(p1)
                            if 'x' in positions[2]:
                                p2[0] = positions[2]['x']
                            if 'y' in positions[2]:
                                p2[1] = positions[2]['y']

                            # vector from 1 to 2
                            v1_2 = [p1[0]-p2[0], p1[1]-p2[1]]
                            # magnitude of vector from 1 to 2
                            m1_2 = math.sqrt(v1_2[0]*v1_2[0]+v1_2[1]*v1_2[1])
                            # unit vector from 1 to 2
                            uv1_2 = [v1_2[0]/m1_2, v1_2[1]/m1_2]
                            # filament delta
                            f_d2 = positions[2][filament_letter+'-orig'] - positions[1][filament_letter+'-orig']
                            path_width2 =  math.fabs((filament_mm3_per_mm*f_d2)/(layerHeight*m1_2)) # - ((math.pi*layerHeight)/4)

                            split_v = [uv1_2[0] - uv0_1[0], uv1_2[1] - uv0_1[1]]
                            split_m = math.sqrt(split_v[0]*split_v[0] + split_v[1]*split_v[1])
                            split_uv = [split_v[0]/split_m, split_v[1]/split_m]

                            overlap_length1 = 0.0
                            overlap_length2 = 0.0

                            split_sin = (split_uv[0]*v0_1[1] - split_uv[1]*v0_1[0]) / m0_1
                            split_cos = -(split_uv[0]*v0_1[0] + split_uv[1]*v0_1[1]) / m0_1
                            if math.fabs(split_sin) > 0.00001:
                                split_cot = (split_cos/split_sin)
                                overlap_length1 = math.fabs(split_cot*(path_width1/2))
                                overlap_length2 = math.fabs(split_cot*(path_width2/2))

                            pos0_1len = (m0_1-overlap_length1)
                            pos1_2len = (m1_2-overlap_length2)
                            # positions[1]['tail'] = ";uv0_1 %f, %f" % (uv0_1[0], uv0_1[1])

                            if (math.fabs(split_sin) > 0.00001 and pos0_1len > 0.0 and pos1_2len > 0.0):
                                #positions[1]['tail'] = ';overlap_length1=%f, overlap_length2=%f, path_width1/2=%f, path_width2/2=%f'%(overlap_length1, overlap_length2, path_width1/2, path_width2/2)

                                # now we make this into four moves
                                # Insert new move between pos0 and pos1
                                pos0_1 = {
                                    'g1': True,
                                    'head': 'G1',
                                    'tail': ";adj1",
                                    'between': "",
                                    'x': p0[0] + uv0_1[0] * (pos0_1len),
                                    'y': p0[1] + uv0_1[1] * (pos0_1len),
                                    filament_letter: positions[0][filament_letter] + (path_width1 * layerHeight * pos0_1len)/filament_mm3_per_mm
                                }
                                # fabricate a-orig or b-orig
                                pos0_1[filament_letter+'-orig'] = positions[0][filament_letter+'-orig'] + (path_width1 * layerHeight * pos0_1len)/filament_mm3_per_mm

                                #pos0_1['tail'] += " a-orig %f" % (pos0_1['a-orig'])

                                # adjust move to pos1
                                positions[1][filament_letter] = pos0_1[filament_letter] + ((path_width1 * layerHeight * overlap_length1)/4)/filament_mm3_per_mm
                                if 'f' in positions[1]:
                                    pos0_1['f'] = positions[1]['f']

                                # add move between pos1 and pos2
                                pos1_2 = {
                                    'g1': True,
                                    'head': 'G1',
                                    'tail': ";adj2",
                                    'between': "",
                                    'x': p1[0] + uv1_2[0] * (overlap_length2),
                                    'y': p1[1] + uv1_2[1] * (overlap_length2),
                                    filament_letter: positions[1][filament_letter] + ((path_width2 * layerHeight * overlap_length2)/4)/filament_mm3_per_mm
                                }
                                # fabricate a-orig or b-orig
                                pos1_2[filament_letter+'-orig'] = positions[1][filament_letter+'-orig'] + (path_width2 * layerHeight * overlap_length2)/filament_mm3_per_mm

                                #pos1_2['tail'] += " a-orig %f" % (pos1_2['a-orig'])

                                # adjust move to pos2
                                old_filament_pos = positions[2][filament_letter]
                                positions[2][filament_letter] = pos1_2[filament_letter] + (path_width2 * layerHeight * pos1_2len)/filament_mm3_per_mm
                                filament_offset[filament_letter] = positions[2][filament_letter] - old_filament_pos
                                if 'f' in positions[2]:
                                    pos1_2['f'] = positions[2]['f']

                                # insert from back to front
                                # pos1_2 before position 2
                                positions.insert(2, pos1_2)
                                # pos0_1 before position 1
                                positions.insert(1, pos0_1)

                                # write our two extra positions and pop them back off
                                write_move(positions, f)
                                write_move(positions, f)

                        # if not fake context
                        write_move(positions, f)
                    else:
                        # if it's fake, pop it off of there after printing the non-moves
                        f.write(positions[1]['between'])
                        positions.pop(1)

            else: # didn't match g0/g1 or position didn't change
                positions[1]['between'] += "".join(line_split)

        # write out what's left over
        write_move(positions, f)

        # inform the machine that we're done
        f.write("M2 ; Completed job, reset state")
