# -*- coding: ascii -*-
"""CNCList.py
This module deal with the blocks of gcode into editor frame.
It manages the variour editing operation on the blocks of gcode

Credits:
    this module code is based on bCNC code
    https://github.com/vlachoudis/bCNC

@author: carlo.dormeletti@gmail.com

    https://github.com/onekk/OKKCNC

"""

from __future__ import print_function
from __future__ import absolute_import

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import Tkinter as Tk
    import tkFont
except ImportError:
    import tkinter as Tk
    import tkinter.font as tkFont

import re

import OCV
from CNC import CNC
import Block
import tkExtra
# import tkDialogs


class CNCListbox(Tk.Listbox):
    """CNC Listbox"""
    def __init__(self, master, app, *kw, **kwargs):
        Tk.Listbox.__init__(self, master, *kw, **kwargs)
        self.bind("<Button-1>", self.button1)
        self.bind("<ButtonRelease-1>", self.release1)
        self.bind("<Double-1>", self.double)
        self.bind("<Return>", self.edit)
        self.bind("<KP_Enter>", self.edit)
        self.bind("<Insert>", self.insertItem)
        self.bind("<Control-Key-Return>", self.insertItem)
        self.bind("<Control-Key-space>", self.commandFocus)
        self.bind("<Left>", self.toggleKey)
        self.bind("<Right>", self.toggleKey)
        self.bind("<Control-Key-d>", self.clone)
        self.bind("<Control-Key-Up>", self.orderUp)
        self.bind("<Control-Key-Prior>", self.orderUp)
        self.bind("<Control-Key-Down>", self.orderDown)
        self.bind("<Control-Key-Next>", self.orderDown)
        self.bind("<Control-Key-p>", lambda e: "break")
        self.bind("<Control-Key-n>", lambda e: "break")
        self.bind("<Control-Key-D>", self.dump)
        self.bind("<Delete>", self.deleteBlock)
        self.bind("<BackSpace>", self.deleteBlock)
        try:
            self.bind("<KP_Delete>", self.deleteBlock)
        except:
            pass

        self.bind("<Control-Key-b>", self.insertBlock)
        self.bind("<Control-Key-r>", self.fill)

        self._blockPos = []  # listbox position of each block
        self._items = []  # each listbox lien which item (bid,lid) shows
        self.app = app
        self.gcode = self.app.gcode
        self.font = tkFont.nametofont(self.cget("font"))
        self._ystart = 0
        self._double = False  # double clicked handled
        self._hadfocus = False
        self.filter = None

    def commandFocus(self, event=None):
        """commandFocus event handler"""
        self.app.commandFocus(event)
        return "break"

    def set(self, index, value):
        """Set/Change the value of a list item
        Change the value of a list item
        and return the value of the old one
        """
        try:
            sel = self.selection_includes(index)
            act = self.index(Tk.ACTIVE)
            self.delete(index)
        except Tk.TclError:
            return
        self.insert(index, value)

        if sel:
            self.selection_set(index)

        self.activate(act)

    def fill(self, event=None):
        """Fill listbox with enable items"""
        ypos = self.yview()[0]
        act = self.index(Tk.ACTIVE)

        # sel = self.curselection()
        items = self.getSelection()
        self.delete(0, Tk.END)

        del self._blockPos[:]
        del self._items[:]
        ydx = 0

        # print("Editor Fill")
        for bidx, block in enumerate(OCV.blocks):
            # print(bidx, block, block.header())
            if self.filter is not None:
                if not (self.filter in block.name() or
                        self.filter == "enable" and block.enable or
                        self.filter == "disable" and not block.enable):
                    self._blockPos.append(None)
                    continue

            self._blockPos.append(ydx)
            self.insert(Tk.END, block.header())
            self._items.append((bidx, None))
            self.itemconfig(Tk.END, background=OCV.COLOR_BLOCK)
            ydx += 1

            if not block.enable:
                self.itemconfig(Tk.END, foreground=OCV.COLOR_DISABLE)

            if not block.expand:
                continue

            for lidx, line in enumerate(block):
                self.insert(Tk.END, line)
                ydx += 1
                if line and line[0] in ("(", "%"):
                    self.itemconfig(Tk.END, foreground=OCV.COLOR_COMMENT)
                self._items.append((bidx, lidx))

        self.select(items)
        # for idx in sel: self.selection_set(idx)
        self.yview_moveto(ypos)
        self.activate(act)
        self.see(act)

    def copy(self, event=None):
        """Copy selected items to clipboard"""
        sio = StringIO()
        pickler = pickle.Pickler(sio)
        # sio.write(_PLOT_CLIP)
        for block, line in self.getCleanSelection():
            if line is None:
                pickler.dump(OCV.blocks[block].dump())
            else:
                pickler.dump(OCV.blocks[block][line])
        self.clipboard_clear()
        self.clipboard_append(sio.getvalue())
        return "break"

    def cut(self, event=None):
        """Cut a Block"""
        self.copy()
        self.deleteBlock()
        return "break"

    def paste(self, event=None):
        """Paste a Block"""
        try:
            clipboard = self.selection_get(selection='CLIPBOARD')
        except:
            return

        ypos = self.yview()[0]
        # paste them after the last selected item
        # bid,lid push them to self so it can be accessed from addLines()
        # python3 might fix this with the inner scope
        try:
            self._bid, self._lid = self._items[self.curselection()[-1]]
        except:
            try:
                self._bid, self._lid = self._items[-1]
            except:
                self._bid = 0
                self._lid = None

        selitems = []
        undoinfo = []

        def add_lines(lines):
            """add lines to block"""
            for line in lines.splitlines():
                # Create a new block
                if self._lid is None:
                    self._bid += 1
                    if self._bid > len(OCV.blocks):
                        self._bid = len(OCV.blocks)
                    self._lid = OCV.MAXINT
                    block = Block.Block()
                    undoinfo.append(self.gcode.addBlockUndo(self._bid, block))
                    selitems.append((self._bid, None))
                else:
                    block = OCV.blocks[self._bid]

                if self._lid == OCV.MAXINT:
                    self._lid = len(block)
                    selitems.append((self._bid, len(block)))
                else:
                    self._lid += 1
                    selitems.append((self._bid, self._lid))
                undoinfo.append(self.gcode.insLineUndo(
                    self._bid, self._lid, line))

        try:
            # try to unpickle it
            unpickler = pickle.Unpickler(StringIO(clipboard))
            try:
                while True:
                    obj = unpickler.load()
                    if isinstance(obj, tuple):
                        block = Block.Block.load(obj)
                        self._bid += 1
                        undoinfo.append(self.gcode.addBlockUndo(
                            self._bid, block))
                        selitems.append((self._bid, None))
                        self._lid = None
                    else:
                        add_lines(obj)
            except EOFError:
                pass
        except pickle.UnpicklingError:
            # Paste as text
            add_lines(clipboard)

        if not undoinfo:
            return

        self.gcode.addUndo(undoinfo)

        self.selection_clear(0, Tk.END)
        self.fill()
        self.yview_moveto(ypos)
        self.select(selitems, clear=True)

        # self.selection_set(Tk.ACTIVE)
        # self.see(Tk.ACTIVE)
        self.winfo_toplevel().event_generate("<<Modified>>")

    def clone(self, event=None):
        """Clone selected blocks"""
        sel = list(map(int, self.curselection()))

        if not sel:
            return

        ypos = self.yview()[0]
        undoinfo = []
        self.selection_clear(0, Tk.END)
        pos = self._items[sel[-1]][0]+1
        blocks = []

        for i in reversed(sel):
            bid, lid = self._items[i]

            if lid is None:
                undoinfo.append(self.gcode.cloneBlockUndo(bid, pos))
                for idx in range(len(blocks)):
                    blocks[idx] += 1

                blocks.append(pos)
            else:
                undoinfo.append(self.gcode.cloneLineUndo(bid, lid))
        self.gcode.addUndo(undoinfo)

        self.fill()
        self.yview_moveto(ypos)
        if blocks:
            self.selectBlocks(blocks)
            self.activate(self._blockPos[blocks[-1]])
        else:
            self.selection_set(Tk.ACTIVE)
        self.see(Tk.ACTIVE)
        self.winfo_toplevel().event_generate("<<Modified>>")
        return "break"

    def deleteBlock(self, event=None):
        """Delete selected blocks of code"""
        sel = list(map(int, self.curselection()))

        if not sel:
            return

        ypos = self.yview()[0]
        undoinfo = []
        for i in reversed(sel):
            bid, lid = self._items[i]
            if isinstance(lid, int):
                undoinfo.append(self.gcode.delLineUndo(bid, lid))
            else:
                undoinfo.append(self.gcode.delBlockUndo(bid))
        self.gcode.addUndo(undoinfo)

        self.selection_clear(0, Tk.END)
        self.fill()
        self.yview_moveto(ypos)
        self.selection_set(Tk.ACTIVE)
        self.see(Tk.ACTIVE)
        self.winfo_toplevel().event_generate("<<Modified>>")

    def edit(self, event=None):
        """Edit active item"""
        active = self.index(Tk.ACTIVE)
        txt = self.get(active)
        if event:
            x_pos = event.x
        else:
            x_pos = 0

        ypos = self.yview()[0]
        bid, lid = self._items[active]
        if lid is None:
            txt0 = txt
            txt = self.gcode[bid].name()
            self.set(active, txt)
            edit = tkExtra.InPlaceEdit(self, select=False, bg=self.cget("bg"))
        else:
            edit = tkExtra.InPlaceEdit(
                self, x=x_pos, select=False, bg=self.cget("bg"))

        if edit.value is None or edit.value == txt:
            if lid is None:
                self.set(active, txt0)
                self.itemconfig(active, background=OCV.COLOR_BLOCK)
                if not self.gcode[bid].enable:
                    self.itemconfig(active, foreground=OCV.COLOR_DISABLE)
            return

        if isinstance(lid, int):
            self.gcode.addUndo(self.gcode.setLineUndo(bid, lid, edit.value))
            self.set(active, edit.value)
            if edit.value and edit.value[0] in ("(", "%"):
                self.itemconfig(active, foreground=OCV.COLOR_COMMENT)

        else:
            self.gcode.addUndo(self.gcode.setBlockNameUndo(bid, edit.value))
            self.set(active, self.gcode[bid].header())
            self.itemconfig(active, background=OCV.COLOR_BLOCK)
            if not self.gcode[bid].enable:
                self.itemconfig(active, foreground=OCV.COLOR_DISABLE)

        self.yview_moveto(ypos)
        self.winfo_toplevel().event_generate("<<Modified>>")

    def activeBlock(self):
        """return active block id"""
        active = self.index(Tk.ACTIVE)
        if self._items:
            bid, lid = self._items[active]
        else:
            bid = 0
        return bid

    def insertItem(self, event=None):
        """Insert a line or a block"""
        active = self.index(Tk.ACTIVE)

        if active is None:
            return

        if len(self._items) == 0 or self._items[active][1] is None:
            self.insertBlock()
        else:
            self.insertLine()

    def insertBlock(self, event=None):
        """Insert New Block"""
        active = self.index(Tk.ACTIVE)
        if self._items:
            bid, lid = self._items[active]
            bid += 1
        else:
            bid = 0

        block = Block.Block()
        block.expand = True
        block.append("G0 X0 Y0")
        block.append("G1 Z0")
        block.append(CNC.zsafe())
        self.gcode.addUndo(self.gcode.addBlockUndo(bid, block))
        self.selection_clear(0, Tk.END)
        self.fill()
        # find location of new block
        while active < self.size():
            if self._items[active][0] == bid:
                break
            active += 1
        self.selection_set(active)
        self.see(active)
        self.activate(active)
        self.edit()
        self.winfo_toplevel().event_generate("<<Modified>>")

    def insertLine(self, event=None):
        """Insert a new line below cursor"""
        active = self.index(Tk.ACTIVE)

        if active is None:
            return

        if len(self._items) == 0:
            self.insertBlock()
            return

        bid, lid = self._items[active]

        active += 1

        self.insert(active, "")
        self.selection_clear(0, Tk.END)
        self.activate(active)
        self.selection_set(active)
        self.see(active)

        edit = tkExtra.InPlaceEdit(self, bg=self.cget("bg"))
        ypos = self.yview()[0]
        self.delete(active)

        if edit.value is None:
            # Cancel and leave
            active -= 1
            self.activate(active)
            self.selection_set(active)
            self.see(active)
            return

        self.insert(active, edit.value)
        self.selection_set(active)
        self.activate(active)

        if edit.value and edit.value[0] in ("(", "%"):
            self.itemconfig(active, foreground=OCV.COLOR_COMMENT)

        self.yview_moveto(ypos)

        # Add line into code

        # Correct pointers
        if lid is None:
            lid = 0
        else:
            lid += 1
        self.gcode.addUndo(self.gcode.insLineUndo(bid, lid, edit.value))

        self._items.insert(active, (bid, lid))

        for idx in range(active+1, len(self._items)):
            i_bid, i_lid = self._items[idx]

            if i_bid != bid:
                break

            if isinstance(i_lid, int):
                self._items[idx] = (i_bid, i_lid + 1)

        for idx in range(bid+1, len(self._blockPos)):
            if self._blockPos[idx] is not None:
                self._blockPos[idx] += 1  # shift all blocks below by one

        self.winfo_toplevel().event_generate("<<Modified>>")

    def toggleKey(self, event=None):
        if not self._items:
            return

        active = self.index(Tk.ACTIVE)
        bid, lid = self._items[active]
        if lid is None:
            self.toggleExpand()
        else:
            # Go to header
            self.selection_clear(0, Tk.END)
            self.activate(self._blockPos[bid])
            self.selection_set(Tk.ACTIVE)
            self.see(Tk.ACTIVE)
            self.winfo_toplevel().event_generate("<<ListboxSelect>>")

    def button1(self, event):
        """Button1 clicked"""
        if self._double:
            return

        # Remember if we had the focus before clicking
        # to be used later in editing
        self._hadfocus = self.focus_get() == self

        # from a single click
        self._ystart = self.nearest(event.y)
        selected = self.selection_includes(self._ystart)
        loc = self._headerLocation(event)
        if loc is None:
            pass
        elif self._headerLocation(event) < 2 and selected:
            return "break"  # do not alter selection!

    def release1(self, event):
        """Release button-1. Warning on separation of double or single click
         or click and drag
        """
        if not self._items:
            return

        if self._double:
            self._double = False
            return

        self._double = False
        active = self.index(Tk.ACTIVE)

        # from a single click
        y_pos = self.nearest(event.y)
        self.activate(y_pos)

        if y_pos != self._ystart:
            return

        loc = self._headerLocation(event)
        if loc is None:
            # Normal line
            if active == y_pos:
                # In place edit if we had already the focus
                if self._hadfocus:
                    self.edit(event)
        elif loc == 0:
            self.toggleExpand()
        elif loc == 1:
            self.toggleEnable()
        return "break"

    def double(self, event):
        if self._headerLocation(event) == 2:
            self.edit()
            self._double = True
        else:
            self._double = False

    def _headerLocation(self, event):
        """Return location where we clicked on header
           0 = expand arrow
           1 = enable ballot box
           2 = name
        """
        if not self._items:
            return None

        # from a single click
        y_pos = self.nearest(event.y)

        block, line = self._items[y_pos]

        if line is not None:
            return None

        txt = self.get(y_pos)
        if event.x <= self.font.measure(txt[:2]):
            return 0
        elif event.x <= self.font.measure(txt[:5]):
            return 1
        else:
            return 2

    def toggleExpand(self, event=None):
        """Toggle expand selection"""
        if not self._items:
            return None

        items = list(map(int, self.curselection()))
        expand = None
        active = self.index(Tk.ACTIVE)
        bactive, lactive = self._items[active]
        blocks = []
        undoinfo = []
        for i in reversed(items):
            bid, lid = self._items[i]
            if lid is not None:
                if bid in blocks:
                    continue

            blocks.append(bid)

            if expand is None:
                expand = not self.gcode[bid].expand

            undoinfo.append(self.gcode.setBlockExpandUndo(bid, expand))

        if undoinfo:
            self.gcode.addUndo(undoinfo)
            self.selection_clear(0, Tk.END)
            self.fill()
            active = self._blockPos[bactive]

            for bid in blocks:
                self.selectBlock(bid)
            self.activate(active)
            self.see(active)

        self.winfo_toplevel().event_generate(
            "<<Status>>", data="Toggled Expand of selected objects")

    def _toggleEnable(self, enable=None):
        if not self._items:
            return None

        items = list(map(int, self.curselection()))
        active = self.index(Tk.ACTIVE)
        ypos = self.yview()[0]
        undoinfo = []
        blocks = []

        for idx in items:
            bid, lid = self._items[idx]
            if lid is not None:
                if bid in blocks:
                    continue

                pos = self._blockPos[bid]
            else:
                pos = idx

            blocks.append(bid)
            block = self.gcode[bid]

            if block.name() in ("Header", "Footer"):
                continue

            if enable is None:
                enable = not block.enable

            undoinfo.append(self.gcode.setBlockEnableUndo(bid, enable))

            sel = self.selection_includes(pos)
            self.delete(pos)
            self.insert(pos, block.header())
            self.itemconfig(pos, background=OCV.COLOR_BLOCK)

            if not block.enable:
                self.itemconfig(pos, foreground=OCV.COLOR_DISABLE)

            if sel:
                self.selection_set(pos)

        if undoinfo:
            self.gcode.calculateEnableMargins()
            self.gcode.addUndo(undoinfo)
            self.activate(active)
            self.yview_moveto(ypos)
            self.winfo_toplevel().event_generate("<<ListboxSelect>>")

    def enable(self, event=None):
        """Enable selected blocks"""
        self._toggleEnable(True)
        self.winfo_toplevel().event_generate(
            "<<Status>>", data="Enabled selected objects")

    def disable(self, event=None):
        """Disable selected blocks"""
        self._toggleEnable(False)
        self.winfo_toplevel().event_generate(
            "<<Status>>", data="Disabled selected objects")

    def toggleEnable(self, event=None):
        """toggle state enable/disable"""
        self._toggleEnable()
        self.winfo_toplevel().event_generate(
            "<<Status>>", data="Toggled Visibility of selected objects")

    def commentRow(self, event=None):
        """comment uncomment row"""
        if not self._items:
            return

        all_items = self._items
        sel_items = list(map(int, self.curselection()))
        mreg = re.compile("^\((.*)\)$")
        change = False
        for idx in sel_items:
            my_item = all_items[idx]
            if my_item[1] is not None:
                change = True
                # check for ()
                line = self.gcode[my_item[0]][my_item[1]]
                m_reg = mreg.search(line)
                if m_reg is None:
                    self.gcode[my_item[0]][my_item[1]] = "("+line+")"
                else:
                    self.gcode[my_item[0]][my_item[1]] = m_reg.group(1)

        if change:
            self.fill()

    def joinBlocks(self, event=None):
        """join blocks"""
        if not self._items:
            return

        # all_items = self._items
        sel_items = list(map(int, self.curselection()))
        change = True
        n_bl = Block.Block(self.gcode[sel_items[0]].name())
        for bid in sel_items:
            for line in self.gcode[bid]:
                n_bl.append(line)
            n_bl.append("( ---------- cut-here ---------- )")
        del n_bl[-1]
        self.gcode.addUndo(self.gcode.addBlockUndo(bid + 1, n_bl))

        if change:
            self.fill()

        self.deleteBlock()
        self.winfo_toplevel().event_generate("<<Modified>>")

    def splitBlocks(self, event=None):
        """splitBlocks"""
        if not self._items:
            return

        # all_items = self._items
        sel_items = list(map(int, self.curselection()))
        change = True
        # newblocks = []

        for bid in sel_items:
            n_bl = Block.Block(self.gcode[bid].name())
            for line in self.gcode[bid]:
                if line == "( ---------- cut-here ---------- )":
                    # newblocks.append(bl)
                    # self.insertBlock(bl)
                    self.gcode.addUndo(self.gcode.addBlockUndo(bid + 1, n_bl))
                    n_bl = Block.Block(self.gcode[bid].name())
                else:
                    n_bl.append(line)
        self.gcode.addUndo(self.gcode.addBlockUndo(bid + 1, n_bl))
        # newblocks.append(bl)
        # self.gcode.extend(newblocks)

        if change:
            self.fill()

        self.deleteBlock()
        self.winfo_toplevel().event_generate("<<Modified>>")

    def changeColor(self, event=None):
        """change color of a block"""
        items = list(map(int, self.curselection()))
        if not items:
            self.winfo_toplevel().event_generate(
                "<<Status>>", data="Nothing is selected")
            return

        # Find initial color
        bid, lid = self._items[items[0]]

        try:
            rgb, color = tkExtra.askcolor(
                title=_("Color"),
                initialcolor=self.gcode[bid].color,
                parent=self)
        except Tk.TclError:
            color = None
        if color is None:
            return

        blocks = []
        undoinfo = []
        for i in reversed(items):
            bid, lid = self._items[i]
            if lid is not None:
                if bid in blocks:
                    continue

            blocks.append(bid)
            oldColor = self.gcode[bid].color
            undoinfo.append(self.gcode.setBlockColorUndo(bid, oldColor))

        if undoinfo:
            self.gcode.addUndo(undoinfo)
            for bid in blocks:
                self.gcode[bid].color = color
            self.winfo_toplevel().event_generate("<<Modified>>")
        self.winfo_toplevel().event_generate(
            "<<Status>>", data="Changed color of block")

    def select(self, items, double=False, clear=False, toggle=True):
        """Select items in the form of (block, item)"""
        if clear:
            self.selection_clear(0, Tk.END)
            toggle = False
        first = None

        for b_it in items:
            bid, lid = b_it
            try:
                block = self.gcode[bid]
            except:
                continue

            if double:
                if block.expand:
                    # select whole block
                    y_pos = self._blockPos[bid]
                else:
                    # select all blocks with the same name
                    name = block.nameNop()
                    for idx, blk in enumerate(OCV.blocks):
                        if name == blk.nameNop():
                            self.selection_set(self._blockPos[idx])
                    continue

            elif not block.expand or lid is None:
                # select whole block
                y_pos = self._blockPos[bid]

            elif isinstance(lid, int):
                # find line of block
                y_pos = self._blockPos[bid]+1 + lid

            else:
                raise
                #continue

            if y_pos is None: continue

            if toggle:
                select = not self.selection_includes(y_pos)
            else:
                select = True

            if select:
                self.selection_set(y_pos)
                if first is None: first = y_pos
            elif toggle:
                self.selection_clear(y_pos)

        if first is not None:
            self.activate(first)
            self.see(first)

    def selectBlock(self, bid):
        """Select whole block lines if expanded"""
        start = self._blockPos[bid]
        while True:
            bid += 1
            if bid >= len(self._blockPos):
                end = Tk.END
                break
            elif self._blockPos[bid] is not None:
                end = self._blockPos[bid]-1
                break
        self.selection_set(start, end)

    def selectBlocks(self, blocks):
        """select all blocks"""
        self.selection_clear(0, Tk.END)
        for bid in blocks:
            self.selectBlock(bid)

    def selectAll(self):
        """select all"""
        self.selection_set(0, Tk.END)

    def selectClear(self):
        """clear selection"""
        self.selection_clear(0, Tk.END)

    def selectInvert(self):
        for i in range(self.size()):
            if self.selection_includes(i):
                self.selection_clear(i)
            else:
                self.selection_set(i)

    def selectLayer(self):
        """Select all blocks with the same name of the selected layer"""
        for bid in self.getSelectedBlocks():
            name = self.gcode[bid].nameNop()
            for idx, blk in enumerate(OCV.blocks):
                if name == blk.nameNop():
                    self.selection_set(self._blockPos[idx])

    def getSelection(self):
        """Return list of [(blocks,lines),...] currently being selected"""
        return [self._items[int(i)] for i in self.curselection()]

    def getSelectedBlocks(self):
        """Return all blocks that at least an item is selected"""
        blocks = {}
        for idx in self.curselection():
            block, line = self._items[int(idx)]
            blocks[block] = True
        return list(sorted(blocks.keys()))

    def getCleanSelection(self):
        """Return list of [(blocks,lines),...] currently being selected
        Filtering all items that the block is also selected
        """
        items = [self._items[int(idx)] for idx in self.curselection()]

        if not items:
            return items

        blocks = {}
        idx = 0
        while idx < len(items):
            bid, lid = items[idx]
            if lid is None:
                blocks[bid] = True
                idx += 1
            elif blocks.get(bid, False):
                del items[idx]
            else:
                idx += 1
        return items

    def getActive(self):
        """get active item"""
        active = self.index(Tk.ACTIVE)

        if active is None:
            return None

        if not self.selection_includes(active):
            try:
                active = self.curselection()[0]
            except:
                return (0, None)
        return self._items[int(active)]

    def orderUp(self, event=None):
        """Move selected items upwards"""
        items = self.getCleanSelection()

        if not items:
            return

        sel = self.gcode.orderUp(items)
        self.fill()
        self.select(sel, clear=True, toggle=False)
        self.winfo_toplevel().event_generate("<<Modified>>")
        return "break"

    def orderDown(self, event=None):
        """Move selected items downwards"""
        items = self.getCleanSelection()

        if not items:
            return

        sel = self.gcode.orderDown(items)
        self.fill()
        self.select(sel, clear=True, toggle=False)
        self.winfo_toplevel().event_generate("<<Modified>>")
        return "break"

    def invertBlocks(self, event=None):
        """Invert selected blocks"""
        blocks = self.getSelectedBlocks()

        if not blocks:
            return

        self.gcode.addUndo(self.gcode.invertBlocksUndo(blocks))
        self.fill()
        # do not send a modified message, no need to redraw
        return "break"

    def dump(self, event=None):
        """Dump list and code, check for mismatch"""

        if not OCV.developer:
            return

        print("*** LIST ***")

        for idx, sel in enumerate(self.get(0, Tk.END)):
            # TODO: do we need .encode()???
            print(idx, sel.encode("ascii", "replace"))

        print("\n*** ITEMS ***")

        for idx, item in enumerate(self._items):
            print(idx, item)

        print("\n*** CODE ***")
        for i, block in enumerate(OCV.blocks):
            print("Block:", i, block.name())

            for j, line in enumerate(block):
                print("   {0:3d} {1}".format(j, line))

        print("\nBLOCKPOS=", self._blockPos)
