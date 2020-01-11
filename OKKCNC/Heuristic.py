# -*- coding: ascii -*-
"""Heuristic.py
Created on Dec 2019

This module contains the Heuristic approach to determine some value analyzing
the Gcode, it is used to detect the "pass" Z height permitting "last pass"
detection to implement the Z height override to cut some material that could
have slight differences in Stock height, usually the wood and plywood

It works, analyzing and modyfing in place the Blocks of gcode created in the
Gcode file loading phase.

@author: carlo.dormeletti@gmail.com
"""

from __future__ import absolute_import
from __future__ import print_function

import OCV
from Block import Block
# from CNC import CNC


def parse_line(line):
    """@return
        lines breaking a line containing list of commands,
        None if empty or comment
    """
    # skip empty lines
    if len(line) == 0 or line[0] in ("%", "#", ";", "("):
        return None

    # remove comments
    line = OCV.PARENPAT.sub("", line)
    line = OCV.SEMIPAT.sub("", line)

    # process command
    # strip all spaces
    line = line.replace(" ", "")

    # Insert space before each command
    line = OCV.CMDPAT.sub(r" \1", line).lstrip()
    return line.split()


def trim_blocks():
    """Trim blocks - delete empty blocks"""
    if not OCV.blocks:
        return

    process = True
    idx = 0
    while (process is True):
        block = OCV.blocks[idx]

        if len(block) == 0 or (len(block) == 1 and len(block[0]) == 0):
            # print("delete block")
            del OCV.blocks[idx]
            if idx > 1:
                idx -= 1

        if idx < (len(OCV.blocks) - 1):
            idx += 1
        else:
            process = False


def process_blocks():
    # first task, process the event detected in GCode.pre_process_gcode
    process_events()
    # now we have some blocks, see the comments in process_events
    # try to detect the G0 moves between the MOPS
    process_rapids()

    # refresh block in editor
    OCV.APP.event_generate("<<Modified>>")


def print_events(l_idx, ev_msg):
    print(OCV.str_sep)
    print(l_idx, ev_msg)
    print("act ev", OCV.blocks_ev[l_idx])
    print("prec ev", OCV.blocks_ev[l_idx - 1])
    print("next ev", OCV.blocks_ev[l_idx + 1])


def print_block(b_num):
    print(OCV.str_sep)
    print("Block number {0} dump".format(b_num))
    print("Block info ", OCV.blocks_info[b_num])
    print(OCV.str_sep)
    for l_idx, line in enumerate(OCV.blocks[b_num]):
        print(l_idx, line)
    print(OCV.str_sep)


def print_blocks_debug_info(b_idx):
    print(OCV.str_sep)
    print("block prior", OCV.blocks[b_idx - 1])
    print("\n", OCV.str_sep)
    print("block actual", OCV.blocks[b_idx])
    print("\n", OCV.str_sep)
    print("block next", OCV.blocks[b_idx + 1])
    print("\n", OCV.str_sep)

    OCV.APP.event_generate("<<Modified>>")


def insert_mark(event, label):
    block_num = OCV.blocks_pos
    b_start = OCV.blocks_info[block_num][0]
    ev_pos = event[1]
    line_pos = ev_pos - b_start + OCV.block_add_l

    # process Mark
    st_pos = event[3][0]
    in_pos = event[3][2]
    z_abs = event[3][1]
    z_move = in_pos[2]
    ev_label = "empty label"

    if label in ("RAPID", "Z_UP"):

        rm_lab = OCV.b_mdata_rm
        rm_lab += " X{0:.{5}f} Y{1:.{5}f}"
        rm_lab += " to X{2:.{5}f} Y{3:.{5}f}"
        rm_lab += " at Z{4:.{5}f}"
        en_pos = (st_pos[0] + in_pos[0], st_pos[1] + in_pos[1])

        if OCV.DEBUG_HEUR > 2:
            print("RAPID Event Mark", event)

        if z_move > 0:
            ev_label = "Z_RS {0:.{2}f} ABS_Z {1:.{2}f}".format(
                z_move, z_abs, OCV.digits)
        elif z_move < 0:
            ev_label = "Z_DW {0:.{2}f} ABS_Z {1:.{2}f}".format(
                z_move, z_abs, OCV.digits)
        else:
            ev_label = rm_lab.format(
                st_pos[0], st_pos[1],
                en_pos[0], en_pos[1],
                z_abs, OCV.digits)

    if label[:2] == "GM":
        gm_lab = OCV.b_mdata_gm
        gm_lab += " X{0:.{5}f} Y{1:.{5}f}"
        gm_lab += " to X{2:.{5}f} Y{3:.{5}f}"
        gm_lab += " at Z{4:.{5}f} <{6}>"
        en_pos = (st_pos[0] + in_pos[0], st_pos[1] + in_pos[1])
        ev_label = gm_lab.format(
                st_pos[0], st_pos[1],
                en_pos[0], en_pos[1],
                z_abs, OCV.digits, label)

    # add mark  line, we need to add 1 to position it after the event
    OCV.blocks[-1].insert(line_pos + 1, OCV.b_mdata_h + " " + ev_label)
    # incrment the added lines counter
    OCV.block_add_l += 1
    # set the new block line count
    OCV.blocks_info[block_num][1] = len(OCV.blocks[-1])


def process_events():
    """process event list and make the appropriate actions like:
        block change
        inject metadata
        add comments to the gcode

    ideally this will create at least 3 blocks:
        - "Header" block
        - Command block
        - "End Job" block with the end Gcode commands detected using
            some heuristic, usually a G0 Z_max followed by:
                M5 (Spindle Stop) or M9 (Coolant Stop)
                M2 or M30 (Program End)
    more blocks are created detecting the custom '(MOP Start:' supplied
    by CamBam postprocessor modified by onekk.
    """
    OCV.blocks_info = []
    OCV.blocks_pos = 0  # only one block is created by pre_process_gcode
    # index start from 1 as the first line is a dummy marker
    OCV.blocks_info.append([1, 0])

    print_block(0)

    if OCV.DEBUG_HEUR > 2:
        print(OCV.blocks_info)

    process = True
    l_idx = 1

    while process is True:
        if l_idx < (len(OCV.blocks_ev) - 2):
            l_idx += 1
        else:
            # continue here is to force the loop to terminate here
            # if not present last line is scanned again
            process = False
            continue
        act_ev = OCV.blocks_ev[l_idx]
        pre_ev = OCV.blocks_ev[l_idx - 1]
        nex_ev = OCV.blocks_ev[l_idx + 1]

        if OCV.DEBUG_HEUR > 2:
            print("Processing event >> ", act_ev)

        if act_ev[0] == "MS":
            if pre_ev[0] == "ZU" and nex_ev[0] == "G0":
                # proper names are added in the process_rapids method
                pe_new_block(
                    act_ev[1], "First MOP")
            else:
                pe_new_block(
                    act_ev[1], "Other MOP")

        elif act_ev[0] == "ME":
            if nex_ev[0] == "MS":
                # this occur in the middle of file, no action needed
                pass
            elif nex_ev[0] == "ZU":
                nex1_ev = OCV.blocks_ev[l_idx + 2]
                if nex1_ev[0] in OCV.end_cmds:
                    pe_new_block(
                        act_ev[1] + 1, "End Block")
                    # if this is the end block we have done
                    process = False
        elif act_ev[0][:2] == "GM":
            insert_mark(act_ev, act_ev[0])
        elif act_ev[0] == "G0":
            insert_mark(act_ev, "RAPID")

        elif act_ev[0] == "ZU":
            insert_mark(act_ev, "Z_UP")
        else:
            if OCV.DEBUG_HEUR > 1:
                print_events(l_idx, "NO catch")


def pe_new_block(ev_line, b_name):
    """Add a new block to the block list during a process_event run
    ev_line >> position in which the event occurs
    b_name  >> block name
    DEBUG   >> used to print some useful infos on console
    """
    # retain actual block_pos
    old_block_num = OCV.blocks_pos

    # calculate the block length
    for b_idx in range(0, OCV.blocks_pos):
        block = OCV.blocks[b_idx]
        print(b_idx, len(block))

    # increment block_pos
    OCV.blocks_pos += 1
    # retain new block_pos
    new_block_num = OCV.blocks_pos

    added_lines = OCV.block_add_l
    # determine the start
    line_num = ev_line - OCV.blocks_info[old_block_num][0] + added_lines

    if OCV.DEBUG_HEUR > 3:
        print(OCV.str_sep)
        print("New Block {0}".format(b_name))
        print(">> Event Line = {0} , added_lines {1}".format(
            ev_line, added_lines))
        print(OCV.gcodelines[ev_line])
        print("New Block: start at {0}\n".format(line_num))
        print_block(old_block_num)

    # a list is needed as we have to modify the values later
    OCV.blocks_info.append([ev_line, added_lines])
    OCV.blocks.append(Block(b_name))

    # reset the added lines counter
    OCV.block_add_l = 0

    l_idx = 0
    l2mov = len(OCV.blocks[old_block_num]) - line_num

    while l_idx < l2mov:
        l_idx += 1

        if OCV.DEBUG_HEUR > 3:
            print(
                "l2mov = {0} l_idx = {1} line_num {2}".format(
                    l2mov, l_idx, line_num),
                        OCV.blocks[old_block_num][line_num])

        line = OCV.blocks[old_block_num].pop(line_num)
        OCV.blocks[new_block_num].append(line)


def process_rapids():
    """This has to identify the rapids between the MOPs and eventually those
    between shapes (profiles or pockets) in each MOP"""

    #  Blocks loop counter
    b_idx = 0
    # process control while flow if set to True will end the loop
    process = True
    # Not using a for loop due to OCV.Blocks in-place modifications
    md_mkl = len(OCV.b_mdata_h)
    md_mk_rm = md_mkl + len(OCV.b_mdata_rm) + 1  # space between the markers

    while process is True:
        l_idx = 0  # reset line counter
        mop_name = ""  # reset mop_name
        # wf_block flag is used to check if the block correctly
        # start with "MOP Start:"
        # and end with "Mop End:"
        wf_block = False
        process2 = True  # reset internal loop exit flag

        cur_block = OCV.blocks[b_idx]
        # obtain header and footer of the block
        cur_head = cur_block[0]
        cur_foot = cur_block[-1]

        # get the mop_name if there is any
        if cur_head[1:11] == "MOP Start:":
            mop_name = cur_head.split(":")[1].lstrip().rstrip(" )")
        # elif cur_head[md_mkl:11] == "":

        if cur_foot[1:9] == "MOP End:":
            if mop_name != "":
                wf_block = True
                cur_block.b_name = mop_name

        if OCV.DEBUG_HEUR > 2:
            print(OCV.str_sep)
            print("Block {0} = ".format(b_idx))
            if wf_block is True:
                print("Well formed MOP Block")
            print("MOP Name = ", mop_name)
            print(OCV.str_sep)

        while process2 is True:
            line = cur_block[l_idx]

            if OCV.DEBUG_HEUR > 2:
                print("Block {0} - Line {1} >>".format(b_idx, l_idx), line)

            # detect rapid move marker and split the block if present
            if line[:md_mkl] == OCV.b_mdata_h:
                if line[md_mkl + 1:md_mk_rm] == OCV.b_mdata_rm:
                    mv_d = extract_rapid_move_value(line)
                    split_block(b_idx, l_idx, "TM", [mv_d[1]], mop_name)
                    # as following lines are now in new block
                    # exit from lines loop
                    process2 = False
                    continue

            if l_idx < (len(cur_block) - 1):
                l_idx += 1
            else:
                process2 = False

        if b_idx < (len(OCV.blocks) - 1):
            b_idx += 1
        else:
            process = False

    else:
        if OCV.DEBUG_HEUR > 0:
            OCV.printout_header("{0}", "END PROCESS_RAPIDS")


def split_block(b_idx, l_idx, action, ac_data, mop_name):
    cur_block = OCV.blocks[b_idx]
    old_name = cur_block.b_name

    if OCV.DEBUG_HEUR > 3:
        print("Split {0} Block = {1} at Line {2}".format(
                old_name, b_idx, l_idx))

    if action == "TM":  # Travel move between blocks
        new_name = old_name + " init move"
        cur_block.b_name = new_name
        new_block_name = old_name + " cut"

    new_block = Block(new_block_name)
    l_cnt = 0
    l2mov = len(OCV.blocks[b_idx]) - l_idx

    while l_cnt < l2mov:

        if OCV.DEBUG_HEUR > 4:  # only for troubleshooting split idx > 4
            print("l2mov = {0} l_cnt = {1} l_idx {2}".format(
                    l2mov, l_cnt, l_idx), OCV.blocks[b_idx][l_idx])

        line = OCV.blocks[b_idx].pop(l_idx)
        new_block.append(line)
        l_cnt += 1

    OCV.blocks.insert(b_idx + 1, new_block)
    added_block = OCV.blocks[b_idx + 1]

    # arrange block metadata if needed

    if action == "TM":
        head_line = added_block[0]
        cur_block.append(head_line)
        label = OCV.b_mdata_ss.format(mop_name, str(1))
        label += " SP: X{0:.{2}f} Y{1:.{2}f}".format(
            ac_data[0][0], ac_data[0][1], OCV.digits)
        added_block[0] = OCV.b_mdata_h + " " + label


def extract_rapid_move_value(md_string):
    """extract values of moves from RAPID MOVE string
    return a tuple (from coord, to coord, z_height)
    from_coord and to_coord have Z = -inf
    x_height have X, Y = -inf
    """
    # detect split points for the coordinates in line
    from_p = md_string.find(' from ')  # to position
    to_p = md_string.find(' to ')  # to position
    at_p = md_string.find(' at ')  # at position

    f_val = parse_line(md_string[from_p + 6:to_p])
    t_val = parse_line(md_string[to_p + 4:at_p])
    a_val = parse_line(md_string[at_p + 4:].rstrip(")"))

    return (extract_value(f_val), extract_value(t_val), extract_value(a_val))


def extract_value(cmds):
    """extract X Y Z value from commands"""
    x_val = y_val = z_val = float('-inf')

    for cmd in cmds:
        # print(cmd)
        c = cmd[0].upper()

        try:
            value = float(cmd[1:])
        except ValueError:
            value = float('-inf')

        # print("EV > ",cmd, c, value)
        if c == "X":
            x_val = value*OCV.unit
        elif c == "Y":
            y_val = value*OCV.unit
        elif c == "Z":
            z_val = value*OCV.unit

    return (x_val, y_val, z_val)
