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

def print_ev(l_idx, ev_msg):
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
    rm_lab = OCV.b_mdata_rm
    rm_lab += " X{0:.{5}f} Y{1:.{5}f}"
    rm_lab += " to X{2:.{5}f} Y{3:.{5}f}"
    rm_lab += " at Z{4:.{5}f}"
    en_pos = (st_pos[0] + in_pos[0], st_pos[1] + in_pos[1])

    if label in ("RAPID", "Z_UP"):
        print("RAPID Event Mark", event)
        if z_move > 0:
            label = " Z_RAISE {0:.{2}f} Z_Q {1:.{2}f}".format(
                z_move, z_abs, OCV.digits)
        elif z_move < 0:
            label = " Z_DOWN {0:.{2}f} Z_Q {1:.{2}f}".format(
                z_move, z_abs, OCV.digits)
        else:
            label = rm_lab.format(
                st_pos[0], st_pos[1],
                en_pos[0], en_pos[1],
                z_abs, OCV.digits)

    # add mark  line, we need to add 1 to position it after the event
    OCV.blocks[-1].insert(line_pos + 1, OCV.b_mdata_h + " " + label)
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
    INT_DEBUG = True
    OCV.blocks_info = []
    OCV.blocks_pos = 0  # only one block is created by pre_process_gcode
    # index start from 1 as the first line is a dummy marker
    OCV.blocks_info.append([1, 0])

    print_block(0)

    if INT_DEBUG is True:
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

        if act_ev[0] == "MS":
            if pre_ev[0] == "ZU" and nex_ev[0] == "G0":
                # TODO add a proper name
                pe_new_block(
                    act_ev[1], "First MOP", INT_DEBUG)
            else:
                pe_new_block(
                    act_ev[1], "Other MOP", INT_DEBUG)

        elif act_ev[0] == "ME":
            if nex_ev[0] == "MS":
                # this occur in the middle of file, no action needed
                pass
            elif nex_ev[0] == "ZU":
                nex1_ev = OCV.blocks_ev[l_idx + 2]
                if nex1_ev[0] in OCV.end_cmds:
                    pe_new_block(
                        act_ev[1] + 1, "End Block", INT_DEBUG)
                    # if this is the end block we have done
                    process = False
        elif act_ev[0] == "GM":
            pass
        elif act_ev[0] == "G0":
            insert_mark(act_ev, "RAPID")

        elif act_ev[0] == "ZU":
            insert_mark(act_ev, "Z_UP")
        else:
            if INT_DEBUG is True:
                print_ev(l_idx, "NO catch")


def pe_new_block(ev_line, b_name, DEBUG):
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

    if DEBUG is True:
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
    match = False
    # Not using a for loop due to OCV.Blocks in-place modifications
    z_pass = []
    while process is True:
        l_idx = 0  # reset line counter
        process2 = True  # reset counter for internal loop

        while process2 is True:
            line = OCV.blocks[b_idx][l_idx]
            print("Block {0} - Line {1} >>".format(b_idx, l_idx), line)

            if line[:5] == OCV.b_mdata_h:
                if line[6:17] == OCV.b_mdata_rm:
                    print("BMD RM Det")
                    print(extract_rapid_move_value(line))

            if l_idx < (len(OCV.blocks[b_idx]) - 1):
                l_idx += 1
            else:
                process2 = False

        if match is False:
            if b_idx < (len(OCV.blocks) - 1):
                b_idx += 1
            else:
                process = False
        else:
            b_idx -= 1
            match = False

    else:
        OCV.printout_header("{0}", "END PROCESS_RAPIDS")

    return z_pass


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

    f_val = parse_line(md_string[from_p + 6:to_p]) # from is st
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


# Here for now to reuse some code, it is intended to be deleted
# ASA refactoring is finished

class CodeAnalizer(object):
    """Analyze for Z raise and XY pos of  actual and peceding blocks
    to detect the consecutive paths,
    If preceding path end and actual path start have the same XY position
    they belongs to the same shape the z raises could be the tabs,
    if they are not at the maximum Z
    This euristics works, at least for "profiles"

    Some assumptions are made:
        First move serve to place the gantry at the path starts, and generally
            is done at Z max-height, maybe if there are some auto z adjust,
            or tool lenght probe some code has to be added to cope with this
            case

        Subsequent moves aren't higher than this first move Z, generally is
            true as the endmill is lowered at Z safe_height at the beginning
            of the work

        Moves that aren't at Z safe_height are generally tabs or pecks_heights
            maybe defining some Z values for the race cases would be a good
            approach

        Actually it seems that pockets are not correctly detected, some more
        deep analisys is needed
        """

    def __init__(self):
        self.z_min = 1000.0
        self.z_max = 1000.0
        self.first_z = 10000.0
        self.block_moved = False

    def detect_profiles(self):
        """analyze start and ending points to 'detect' the shapes at least
        profile """
        z_pass = self.pre_process_md()

        if z_pass == []:
            print("empty z_pass")

        process = True

        zp_cnt = 0
        p_bl_id = -1
        block = []

        while (process is True):
            bl_id = z_pass[zp_cnt][0]
            print(bl_id, zp_cnt, z_pass[zp_cnt])

            if bl_id == p_bl_id:
                pass
            else:
                block = OCV.blocks[bl_id]
                print(block[0], bl_id, zp_cnt)

            print(block[z_pass[zp_cnt][1]])

            print(OCV.str_sep)
            if zp_cnt < (len(z_pass) - 1):
                p_bl_id = bl_id
                zp_cnt += 1
            else:
                process = False


    def joinblocks(self, index):
        """perfrom a join of the two block, the actual and the preceding
        rearranging metadata"""
        # delete last line with end position
        OCV.blocks[index-1][-1] = "( End Z  pass ? )"
        for line in OCV.blocks[index]:
            if line.startswith(OCV.b_mdata_sp[:8]):
                # match block start point no write
                pass
            else:
                # no match of start, end or pass z_height
                OCV.blocks[index-1].append(line)

        del OCV.blocks[index]

        # print("JoinBlock >>", OCV.blocks[index - 1])

    def parse_blocks(self):
        """perform a block analisys and track all the detection"""
        al_cnt = 0
        self.first_z = 10000.0  # dummy height in hobby machine may be enough
        process = True
        b_idx = 0
        self.block_head_mod = False
        self.block_advance = False
        # we are not using loops as the Block count could be modified
        while (process is True):
            print(OCV.str_sep)
            print("Scanning Block {0} adv = {1} h_mod = {2}".format(
                    b_idx,
                    self.block_advance, self.block_head_mod))

            l_cnt = 0
            block = OCV.blocks[b_idx]
            # avoid the recheck of the first (moved) line of new block
            # as it generate a loop that end in a AttributeError for
            # OCV.blocks
            if self.block_advance is True:
                if self.block_head_mod is True:
                    l_cnt += 1
                    self.block_head_mod = False

                l_cnt += 1
                self.block_advance = False

            process2 = True
            while (process2 is True):

                line = block[l_cnt]
                msg = []
                print(l_cnt, line)
                cmds = parse_line(line)

                # print(cmds)
                if cmds is not None and self.first_z > 9999 \
                        and cmds[0] == "G0" and cmds[1][:1] == "Z":
                    self.first_z = self.extract_value(cmds)[2]
                    msg.append("--- first z_detected {0}".format(self.first_z))

                if cmds is not None and self.first_z < 9999 \
                        and cmds[0] == "G0" and cmds[1][:1] == "Z":
                    other_z = self.extract_value(cmds)[2]
                    if other_z == self.first_z:
                        msg.append(
                            "--- z_safe {0} detected ?".format(other_z))
                    else:
                        msg.append(
                            "--- GO single z_move {0}".format(other_z))

                if cmds is None:
                    if line[:8] == "(B_MD SP":
                        msg.append("--- Block metadata START")
                    elif line[:8] == "(B_MD EP":
                        msg.append("--- Block metadata END")
                    elif line[:10] == "(MOP Start":
                        mop_desc = line[11:].rstrip(" )").lstrip()
                        #print("MOP name >{0}<".format(mop_desc))
                        self.process_mop(mop_desc, b_idx, l_cnt)
                        process2 = False
                    else:
                        msg.append("--- comment detected?")

                print(al_cnt, l_cnt, line)
                if msg is not []:
                    print("\n".join(msg))

                if l_cnt < (len(block) - 1):
                    l_cnt += 1
                    al_cnt += 1
                else:
                    process2 = False

            # Check all blocks are scanned
            if b_idx < (len(OCV.blocks) - 1):
                b_idx += 1
            else:
                process = False

        # rearrange blocks
        OCV.APP.event_generate("<<Modified>>")

    def process_mop(self, mop_desc, b_idx, boundary):
        shape_end = False
        INT_DEBUG = True
        proc_block = OCV.blocks[b_idx]
        # print("Proc_Block 0", proc_block[0])
        s_part = proc_block[:boundary]
        e_part = proc_block[boundary:]

        if INT_DEBUG is True:
            print(OCV.str_sep)
            print("Block {0} \n".format(b_idx))
            print(OCV.str_sep)
            print("Boundary {0} S_part\n".format(b_idx),
                  OCV.str_sep, "\n", s_part)
            print("Boundary {0} E_part\n".format(b_idx),
                  OCV.str_sep, "\n", e_part)
            print(OCV.str_sep)
            print("Next block {0} \n".format(b_idx + 1))
            print(OCV.blocks[b_idx + 1], "\n", OCV.str_sep)

        # create an empty block for the new block
        block = Block()
        # place the lines after MOP Start: in the block
        block.extend(e_part)

        # check if the first line of the processed block contains shape start
        if proc_block[0][:8] == "(B_MD SP":
            # extract the line from the block and place it after "MOP Start:"
            b_sp = proc_block.pop(0)

            print(OCV.str_sep)
            print("DEBUG ARRANGE SHAPE START END \n{0}".format(b_sp))
            print("-- Following line", proc_block[0])
            print("-- Following line", proc_block[1])
            print("-- Following line", proc_block[2])
            print("block", block)
            print(OCV.str_sep)

            # delete it also from s_part
            del s_part[0]
            # decrement the boundary variable
            boundary -= 1
            block.insert(1, "( Shape Start )")
            block.insert(1, b_sp)
            self.block_head_mod = True

        if block[-1][:8] == "(B_MD EP":
            shape_end = True
            block.append("( Shape End )")

        # create and empty block for the intial part
        cur_block = Block()

        if s_part[0][:8] == "(B_MD SP":
            if shape_end is True:
                cur_block.append("( Shape Start )")

        cur_block.extend(s_part)

        self.sanitize_block(block, cur_block)

        # check if line before boundary is a MOP End
        if s_part[-1][:8] == "(MOP End":
            # if is MOP End we should leave the block with the relevant info
            OCV.blocks[b_idx] = cur_block
            OCV.blocks.insert(b_idx + 1, block)
            self.block_advance = True
        else:
            # if is not MOP End, the prior part is appended
            # to the preceding block
            OCV.blocks[b_idx - 1].extend(cur_block)
            OCV.blocks[b_idx] = block

        # self.debug_blocks(self, b_idx)

    def debug_blocks(self, b_idx):
        print(OCV.str_sep)
        print("block prior", OCV.blocks[b_idx - 1])
        print("\n", OCV.str_sep)
        print("block actual", OCV.blocks[b_idx])
        print("\n", OCV.str_sep)
        print("block next", OCV.blocks[b_idx + 1])
        print("\n", OCV.str_sep)

        OCV.APP.event_generate("<<Modified>>")

    def sanitize_block(self, block, cur_block):
        # scan the block for commands or comments not relevant for MOP
        # like Spindle start and stop and Spindle Speed,  Tool change
        # commands plus tooltable comments and others...
        # move them to the to preceding block for clarity

        l_cnt = 0
        b_scan = True

        while (b_scan is True):
            line = block[l_cnt]
            cmds = parse_line(line)
            detection = False

            if cmds is not None:
                # print("BA >> ", line, cmds)

                if cmds[0] in ("G17", "M3", "M4", "M8"):
                    detection = True
                elif cmds[0][:1] in ("T", "S"):
                    detection = True
                else:
                    detection = False
            else:
                # print("BA COMMENT > ", line)
                if line[:3] in ("( T",):
                    detection = True

            if detection is True:
                # print("Match {0}".format(line))
                cur_block.append(line)
                del block[l_cnt]
                # rearrange counter
                l_cnt -= 1

            # If the command is relevant for the MOP terminate the scan
            if cmds is not None:
                if cmds[0] in ("G0", "G1", "G2", "G3"):
                    b_scan = False

            # end of block check to avoid Errors
            if l_cnt < (len(block) - 1):
                l_cnt += 1
            else:
                b_scan = False

