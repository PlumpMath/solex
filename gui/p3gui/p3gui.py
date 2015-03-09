
# ===
# GUI
# ===

# System imports.
import sys ### 
import glob
import os.path
from math import isnan, tan, radians
from collections import OrderedDict as odict

# Panda imports.
## import direct.directbase.DirectStart
from panda3d.core import NodePath, PandaNode, TextNode, Point3, VBase4
from panda3d.core import Filename, Texture, PNMImage
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter
from panda3d.core import Geom, GeomNode, GeomTriangles
from panda3d.core import TransparencyAttrib, DynamicTextFont, Camera, OrthographicLens


# Constants
DEFAULT_FONT = {
    'name':"cour.ttf",
    'size':12,
    'colour':(0,1,0,1)
}
TAN_70 = tan(radians(65))

PROP_VERBOSE = False

FONT_PATH = Filename()
FONT_PATH.setDirname("/c/Windows/Fonts/")

# Types.
TupleType = type(())
ListType = type([])
DictType = type({})
IntType = type(0)
FloatType = type(1.1)
StringType = type("")
BoolType = type(True)
def dummy(): pass
FunctionType = type(dummy)
class dummy: pass
ClassType = type(dummy)

class object(object):
    pass
    
# Event Types.
EVENT_TYPES = [
    "_on_mouse1",
    "_on_mouse2",
    "_on_mouse3",
    "_on_mouse1_up",
    "_on_mouse2_up",
    "_on_mouse3_up",
    "_on_mouse_in",
    "_on_mouse_out",
]

# Colours
MID_GREY = (.5,.5,.5,1)

# Gui Exceptions.      
class GuiError(Exception):
    def __init__(self, *args):
        self.e_msg = "Gui Error for {}".format(self)
    def __str__(self):
        return self.e_msg
        
class AttributeMissingError(GuiError):
    def __init__(self, widget, attr_name):
        e_msg = "'{}' missing for '{}'"
        if "wid" in widget.__dict__: wid = widget.wid
        else: wid = widget.__class__.__name__
        self.e_msg = e_msg.format(attr_name, wid)
        
class AttributeValueError(GuiError):
    def __init__(self, obj, attr_name, attr_val, msg):
        e_msg = "\nInvalid value '{}' for attribute '{}' on widget '{}'\n--> {}"
        self.e_msg = e_msg.format(attr_val, attr_name, obj.__class__.__name__, msg)
        
class BuildError(GuiError):
    def __init__(self, widget):
        self.e_msg = "__build__ method not found for {}".format(widget.wid)


# Utility objects.
class util:
    
    @classmethod
    def get_alt_shade(cls, col_tup, inc):
        col_list = []
        for c in col_tup[:-1]:
            _c = c + inc
            if _c > 1: _c = 1.0
            elif _c < 0: _c = 0.0
            col_list.append(_c)
        col_list.append(col_tup[-1])
        return tuple(col_list)
    
    @classmethod
    def get_mult_col(cls, col_tup, multi):
        col_list = []
        for c in col_tup[:-1]:
            _c = c * multi
            if _c > 1: _c = 1.0
            elif _c < 0: _c = 0.0
            col_list.append(_c)
        col_list.append(col_tup[-1])
        return tuple(col_list)
    
    @classmethod
    def get_text_size(cls, text, font, orient="horizontal"):
        text_node = TextNode("temp")
        text_node.setText(text)
        text_node.setGlyphScale(font.size)
        text_node.setFont(font.FONT)
        if orient == "vertical": text_node.setWordwrap(1.0)
        tw = int(text_node.getWidth())+1
        th = int(text_node.getHeight())+1
        return tw, th


class Attr(object):
    
    complex_attrs = ("layout", "grid", "font", "border")
   
    def __new__(cls, obj, attr, val):
        locs = {'attr_cls':None}
        exec("attr_cls = {}_attr".format(attr), locs, globals())
        return attr_cls(obj, val)


class _Attr_:
    
    def refresh(self):
        pass
            
    def __init__(self, obj, val):
        self.obj = obj
        self.__dict__.update(val)
        
    def __str__(self):
        str_list = [self.__class__.__name__]
        for key, val in self.__dict__.items():
            if key.startswith("_"): continue
            str_list.append("  {}: {}".format(key, val))
        return "\n".join(str_list)


class font_attr(_Attr_):
    
    _font_path = FONT_PATH
    _min_size = 6
    _max_size = 64
    
    def __init__(self, obj, font):
        _Attr_.__init__(self, obj, font)
        font_file_path = Filename(self._font_path, Filename(self.name))
        self.FONT = DynamicTextFont(font_file_path)
        self.FONT.setPointSize(18)
        self.FONT.setFg(self.colour)
        self.__text_node = TextNode("font_ref_text")
        self.__text_node.setFont(self.FONT)

class layout_attr(_Attr_):
    """
    rows:           2           -> number of rows [1]
    cols:           3           -> number of cols [1]
    row_heights:    [40,20]     -> height of each row, -1 for auto  [(-1, -1...)]
    col_widths:     [20,80,10]  -> width of each col, -1 for auto  [(-1, -1...)]
    """
    
    def get_coords(self, grid):
        cw, ch = self.get_cell_dimensions(grid)
        x = sum(self.col_widths[:grid.col]) + cw/2
        y = sum(self.row_heights[:grid.row]) + ch/2
        return x, y
        
    def get_cell_dimensions(self, grid):
        w, h = 0, 0
        for i, cw in enumerate(self.col_widths):
            if i >= grid.col and i < grid.col+grid.col_span:
                w += cw
        for i, ch in enumerate(self.row_heights):
            if i >= grid.row and i < grid.row+grid.row_span:
                h += ch
        return w, h
        
    def refresh(self, layout={}):
        if layout:
            self.__dict__.update(layout)
            if "col_widths" in layout:
                # Make sure col_widths is right len and update _orig_col_widths.
                if len(self.col_widths) < self.cols:
                    # Fill any missing col_widths with -1.
                    diff = self.cols - len(self.col_widths)
                    ext = [x*0-1 for x in range(diff)]
                    self.col_widths.extend(ext)
                self._orig_col_widths = tuple(self.col_widths)
            if "row_heights" in layout:
                # Make sure row_heights is right len and update _orig_row_heights.
                if len(self.row_heights) < self.rows:
                    # Fill any missing row_heights with -1.
                    diff = self.rows - len(self.row_heights)
                    ext = [x*0-1 for x in range(diff)]
                    self.row_heights.extend(ext)
                self._orig_row_heights = tuple(self.row_heights)
        self.__fill_Vals()
        
    def __init__(self, obj, layout):
        self.rows = 1
        self.cols = 1
        self.col_widths = [-1]
        self.row_heights = [-1]
        self._orig_col_widths = [-1]  # Keep track of cols needing auto-size.
        self._orig_row_heights = [-1] # Keep track of rows ''.
        _Attr_.__init__(self, obj, layout)
        self.refresh(layout)
        
    def __fill_Vals(self):
        tot_w, tot_h = self.obj.size
        ## print(self.obj, self.obj.size)
        # Rows. 
        i, i_list = 0, []
        for h, oh in zip(self.row_heights, self._orig_row_heights):
            if oh == -1: i_list.append(i)
            else: tot_h -= h
            i += 1
        if i_list:
            fill = tot_h/len(i_list)
            for i in i_list:
                self.row_heights[i] = fill
        # Cols.
        i, i_list = 0, []
        for w, ow in zip(self.col_widths, self._orig_col_widths):
            if ow == -1: i_list.append(i)
            else: tot_w -= w
            i += 1
        if i_list:
            fill = tot_w/len(i_list)
            for i in i_list:
                self.col_widths[i] = fill
        
class grid_attr(_Attr_):
    
    def __init__(self, attr, grid):
        self.row = 0
        self.col = 0
        self.row_span = 1
        self.col_span = 1
        if type(grid) == TupleType:
            grid = {'row':grid[0], 'col':grid[1]}
        self.__dict__.update(grid)
        
class border_attr(_Attr_):
        
    def get_added_size(self):
        w = self.left.thick+self.right.thick
        h = self.top.thick+self.bottom.thick
        return w, h
    def refresh(self):
        self.obj.Border.left.NP.setColor(*self.left.colour)
        self.obj.Border.top.NP.setColor(*self.top.colour)
        self.obj.Border.right.NP.setColor(*self.right.colour)
        self.obj.Border.bottom.NP.setColor(*self.bottom.colour)
        
    def __init__(self, obj, border):
        _Attr_.__init__(self, obj, border)
        if "type" not in self.__dict__:
            self.type = border_basic_side
        if "bevel" in border:
            bevel = border['bevel']
        else:
            bevel = (0,0,0,0)
        sides = ("left", "top", "right", "bottom")
        for side, col_adj in zip(sides, bevel):
            # Create any omitted sides by using general "thick" and "colour" vals.
            if side not in self.__dict__:
                if col_adj: col = util.get_alt_shade(self.colour, col_adj)
                else: col = self.colour
                side_dict = {'thick':self.thick,'colour':col,'type':self.type}
            # Create given sides.
            else:
                if "thick" not in self.__dict__[side]:
                    self.__dict__[side]['thick'] = self.thick
                if "colour" not in self.__dict__[side]:
                    if col_adj: col = util.get_alt_shade(self.colour, col_adj)
                    else: col = self.colour
                else:
                    col = self.__dict__[side]['colour']
                    if col_adj:
                        col = util.get_alt_shade(col, col_adj)
                self.__dict__[side]['colour'] = col
                side_dict = self.__dict__[side]
                
            self.__dict__[side] = _Attr_(obj, side_dict)
        
class line: pass


class tri:
    
    def __init__(self, pts):
        vformat = GeomVertexFormat.getV3c4t2()
        vdata = GeomVertexData("card", vformat, Geom.UHStatic)
        vertices = GeomVertexWriter(vdata, "vertex")
        colours = GeomVertexWriter(vdata, "color")
        texcoords = GeomVertexWriter(vdata, "texcoord")
        
        for pt in pts:
            x, y = pt['pos']
            vertices.addData3f(x, 0, y)
            colours.addData4f(*pt['colour'])
            texcoords.addData2f(*pt['uv'])
        
        triangles = GeomTriangles(Geom.UHStatic)
        triangles.addVertices(0, 1, 2)
        triangles.closePrimitive()
        
        geom = Geom(vdata)
        geom.addPrimitive(triangles)
        geom_node = GeomNode("geom")
        geom_node.addGeom(geom)
        self.NP = NodePath(geom_node)
        self.NP.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MAlpha))


class quad:
    
    def __init__(self, pts):
        vformat = GeomVertexFormat.getV3c4t2()
        vdata = GeomVertexData("card", vformat, Geom.UHDynamic)
        vertices = GeomVertexWriter(vdata, "vertex")
        colours = GeomVertexWriter(vdata, "color")
        texcoords = GeomVertexWriter(vdata, "texcoord")
        
        for pt in pts:
            x, y = pt['pos']
            vertices.addData3f(x, 0, y)
            colours.addData4f(*pt['colour'])
            texcoords.addData2f(*pt['uv'])
        
        triangles = GeomTriangles(Geom.UHDynamic)
        triangles.addVertices(0, 1, 3)
        triangles.addVertices(3, 1, 2)
        triangles.closePrimitive()
        
        geom = Geom(vdata)
        geom.addPrimitive(triangles)
        geom_node = GeomNode("geom")
        geom_node.addGeom(geom)
        self.NP = NodePath(geom_node)
        self.NP.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MAlpha))


class poly: pass


class rectangle(quad):
    
    def __init__(self, size, colour):
        w, h = size
        pt_A = {'pos':(-w/2,-h/2),'colour':(colour),'uv':(0,0)}
        pt_B = {'pos':(-w/2,h/2),'colour':(colour),'uv':(0,1)}
        pt_C = {'pos':(w/2,h/2),'colour':(colour),'uv':(1,1)}
        pt_D = {'pos':(w/2,-h/2),'colour':(colour),'uv':(1,0)}
        pts = (pt_A, pt_B, pt_C, pt_D)
        quad.__init__(self, pts)


class Border:
    
    def __init__(self, border, size):
        self.NP = NodePath("border")
        for side in ("left", "top", "right", "bottom"):
            self.__dict__[side] = border.type(self, border.__dict__[side], side, size)
            

class border_dummy_side:
    
    def __init__(self, master, border, size):
        self.__dict__.update(border)


class border_basic_side(quad):
    
    def __init__(self, master, border, side, size):
        if border.thick:
            # Only contsruct visible border if 'thick' given.
            w, h = size
            t = border.thick
            hw, hh, ht = w/2, h/2, t/2
            if side == "left":
                pos_list = [(-hw-t,-hh-t),(-hw-t,hh+t),(-hw,hh),(-hw,-hh)]
            elif side == "top":
                pos_list = [(-hw,hh),(-hw-t,hh+t),(hw+t,hh+t),(hw,hh)]
            elif side == "right":
                pos_list = [(hw,-hh),(hw,hh),(hw+t,hh+t),(hw+t,-hh-t)]
            elif side == "bottom":
                pos_list = [(-hw-t,-hh-t),(-hw,-hh),(hw,-hh),(hw+t,-hh-t)]
            
            uv_list = [(0,0),(0,1),(1,1),(1,0)]
            pts = []
            for c, pos in enumerate(pos_list):
                pt = {'pos':pos,
                      'colour':border.colour,
                      'uv':uv_list[c]}
                pts.append(pt)
            quad.__init__(self, pts)
        else:
            self.NP = NodePath("empty_border")
        self.__dict__.update(border.__dict__)
        self.NP.reparentTo(master.NP)



class _Widget_:
    # Core vars.
    display = True
    size = (0,0)
    bg = (0,0,0,0)
    layout = {'rows':1,'cols':1}
    grid = {'row':0,'col':0,'row_span':1,'col_span':1}
    place = {'anchor':"c"}
    border = {'thick':0,'colour':(0,0,0,0)}
    pad = (0,0)
    font = DEFAULT_FONT
    distance = 0
    children = []
    # Util vars.
    _takes_mouse_events = False
    _takes_key_events = False
    _track_obj = None
    
    # Public.
    def render(self, grid=None, place=None):
        self._Render(grid, place)
    def destroy(self):
        self.NP.removeNode()
        self.Master.Children.remove(self)
        self.Window.remove_widget(self)
        for child in self.Children:
            child.destroy()
    def show(self):
        self.NP.show()
    def hide(self):
        self.NP.hide()
    def get_total_size(self):
        """Return total size of widget including border contributions."""
        cw, ch = self.size
        bw, bh = self.border.get_added_size()
        pw, ph = self.pad
        return int(cw+bw+pw), int(ch+bh+ph)
    def get_family(self, verbose=False):
        """Returns a flat list of all children and sub-children."""
        return self.__get_Family()
            
    # Main Loop.
    def _drag_(self):
        pass
    
    # Setup.
    def __init__(self, master, **attrs):
        # Setup widget.
        if master: 
            self.Window = master.Window
            self.CTRL = master.CTRL
        self.Master = master
        self.NP = NodePath(PandaNode("widget"))
        self.Border = None
        # Build widget.
        self.__map__(attrs)
        self.__wid__()
        self.__children__()
        self.__layer__()
        self.NP.setName(self.wid)
        self.layout.refresh()
        
    # 1 - Map attrs from parents and/or given init attrs.
    def __map__(self, attrs={}):
        for cls in reversed(list(self.__class__.__mro__)):
            for attr, val in cls.__dict__.items():
                if attr in Attr.complex_attrs:
                    self.__dict__.update({attr:Attr(self, attr, val)})
        # Any 'attrs' given as args to init supersede all others.
        for attr, val in attrs.items():
            if attr in Attr.complex_attrs:
                self.__dict__.update({attr:Attr(self, attr, val)})
            else:
                self.__dict__[attr] = val
    
    # 2 - Give widget custom wid.
    def __wid__(self):
        if "wid" not in dir(self):
            cls_name = self.__class__.__name__.lower()
            self.wid = "{}.{}".format(self.Master.wid, cls_name)
    
    # 3 - Instantiate children.
    def __children__(self):
        self.c_dict = odict()
        for child_cls in self.children:
            child = child_cls(self)
            self.c_dict[child.wid] = child
        self.Children = list(self.c_dict.values())
    
    # 4 - Reparent widget and its children as a batch.
    def __layer__(self):
        if not self.Master: return
        self.NP.reparentTo(self.Master.NP)
        for child in self.Children:
            child.__layer__()
    

      
    # Render.
    def _Render(self, grid=None, place=None):
        master = self.Master
        if not grid: grid = self.grid
        if type(grid) == DictType: grid = grid_attr("grid", grid)
        if not place: place = self.place
        
        # Ensure hidden widgets are not shown.
        if not self.display:
            self.NP.hide()

        # Init coords are center of widget's cell in its master.
        x, null, y = self.Master.NP.getPos(render2d)
        gx, gy = self.Master.layout.get_coords(grid)
        mw, mh = self.Master.size
        x += gx - mw/2
        y += gy - mh/2
        col_w, row_h = master.layout.get_cell_dimensions(grid)
        
        # Adjust coords by "place" values.
        x_offset, y_offset = 0, 0
        if place['anchor'] == "c":
            if "left" in place: x_offset -= place['left']
            elif "right" in place: x_offset += place['right']
            if "top" in place: y_offset += place['top']
            elif "bottom" in place: y_offset -= place['bottom']
        else:
            if "left" in place: x_offset += place['left'] - col_w/2
            elif "right" in place: x_offset += col_w-place['right'] - col_w/2
            if "top" in place: y_offset += place['top'] - row_h/2
            elif "bottom" in place: y_offset += row_h-place['bottom'] - row_h/2
            
        # Adjust for widget size and master border values.
        w, h = self.get_total_size()
        hw, hh = w/2, h/2
        if "e" in place['anchor']: x_offset -= hw
        elif "w" in place['anchor']: x_offset += hw
        if "n" in place['anchor']: y_offset += hh
        elif "s" in place['anchor']: y_offset -= hh
        
        x += x_offset
        y += y_offset
        self._x_offset = x_offset
        self._y_offset = y_offset
        self.NP.setPos(x, 0, -y)
        self._prev_pos = None
        
        # Get x and y screen pos vals for mouse events.
        ww, wh = self.Window.size
        x_per = self._x_per = (float(w)/float(ww)) * ww / 2
        y_per = self._y_per = (float(h-1)/float(wh)) * wh / 2
        if self._takes_mouse_events:
            self._update_event_box_()
        
        # Render all children.
        for child in self.Children:
            child.render()

    def __get_Family(self):
        def recurse_children(w, family, indent=""):
            family.append(w)
            for child in w.Children:
                family = recurse_children(child, family)
            return family
        family = recurse_children(self, [])
        return family


class _Cmd_Propagator_:
    propagate = "none"
    p_map = {}
    _indent = 0          # Static var that tracks report indent level (for nested props).
    
    def propagate_thru_all(self,
        cmd_str,                # name of cmd to propagate.
        widget=None,            # widget to start propagation from.
        handled=None,           # set that holds called handler objects to prevent redundant calls.
        args=[],                # args to be given to handlers.
        kwargs={},              # keyword args ''.
        verbose=PROP_VERBOSE,   # "True" to print detailed report of propagation.
        _solo=True,             # internal flag to control header printing.
        _reset=False):          # internal flag to reset indent
        
        # Set defaults for values not given.
        if not widget: widget = self
        if not handled: handled = set()
        if verbose and _solo:
            if _reset: self._indent = 0
            self.__print_Header(cmd_str, widget.wid, "ALL")
        
        # Propagate cmd_str up through masters starting with self.
        while widget:
            # 'handled' accumulates through each master and its parents.
            handled, res = self.propagate_thru_parents(cmd_str, widget, handled,
                                                       args, kwargs, verbose, _solo=False)
            # "True" res stops propagation.
            if res == True:
                break
            widget = widget.Master
            
        return handled
    
    def propagate_thru_parents(self,
        cmd_str,
        widget=None,
        handled=None,
        args=[],
        kwargs={},
        verbose=PROP_VERBOSE,
        _solo=True,
        _reset=False):
            
        # Set defaults for values not given.
        if not widget: widget = self
        if not handled: handled = set()
        if verbose:
            if _solo:
                if _reset: self._indent = 0
                self.__print_Header(cmd_str, widget.wid, "PARENTS")
            print("{: ^{indent}}<{wid}>".format("", indent=self._indent, wid=widget.wid))
            self._indent += 2
        res = False

        # Propagate cmd up through parent hiearchy starting with base _Widget_.
        for cls in widget.__class__.__mro__:
            handler = None
            # Check if cls defines a handler; call it if it does.
            if cmd_str in cls.__dict__:
                handler = eval("cls.{}".format(cmd_str))
                # If this is part of an "all" propagation then this test
                # prevents any handler from executing twice.
                if handler in handled:
                    continue
                # Mark as handled.
                handled.add(handler)
            # Actually call handler only after its info has been
            # printed (if verbose) b/c otherwise cls info line comes
            # after any props started in handler (_on_mouse1 -> button_clk)
            if verbose:
                self.__print_Handler_Info(cls.__name__, handler)
            if handler:
                res = handler(widget, *args, **kwargs)
            # A "True" res is the signal to stop propagation.
            if res == True:
                break
        
        if verbose: self._indent -= 2
        return handled, res
    
    def propagate_thru_masters(self,
        cmd_str,
        widget=None,
        handled=None,
        args=[],
        kwargs={},
        verbose=PROP_VERBOSE,
        _reset=False):
        
        # Set defaults for values not given.
        if not widget: widget = self
        if not handled: handled = set()
        if verbose:
            if _reset: self._indent = 0
            self.__print_Header(cmd_str, widget.wid, "MASTERS")
            self._indent += 2
        res = False
        # Propagate evt up through master hierarchy.
        while widget:
            handler = None
            if cmd_str in dir(widget):
                # Handle cmd.
                handler = eval("widget.{}".format(cmd_str))
                print("++++>", handler)
                if handler in handled:
                    continue
                handled.add(handler)
            # Print first, then handle, same as above.
            if verbose:
                self.__print_Handler_Info("<{}>".format(widget.wid), handler)
            if handler:
                res = handler(*args, **kwargs)
            # A "True" res is the signal to stop propagation.
            if res == True:
                break
            widget = widget.Master
        
        if verbose: self._indent -= 2
        return handled


    # Verbose.
    def __print_Header(self, cmd_str, wid, prop_type):
        print()
        indent = "{: ^{indent}}".format("", indent=self._indent)
        header = "'{}'".format(cmd_str)
        dec = "{:-^{length}}".format("", length=len(header))
        print("\n{}{}\n{}{} - <{}>\n{}{}".format(indent, dec, indent, header, wid, indent, dec))
        print("{}thru: {}\n".format(indent, prop_type))
        
    def __print_Handler_Info(self, handler_owner, handler):
        msg = "{: ^{indent}}{owner}".format("", indent=self._indent, owner=handler_owner)
        if handler:
            if handler.__doc__:
                msg = "{:42}{}".format(msg, handler.__doc__)
            else:
                msg = "{:42}(???)".format(msg)
        print(msg)

    
class _Mouse_Event_Handler_(_Cmd_Propagator_):
    propagate = "all"
    _takes_mouse_events = True
    _mouse_over = False
    
    # Public.
    def render(self, grid=None, place=None):
        self._Render(grid, place)
        self._update_event_box_()
    
    # Events.
    def _on_mouse1(self, ue):
        """pass"""
        pass
    def _on_mouse2(self, ue):
        """pass"""
        pass
    def _on_mouse3(self, ue):
        """pass"""
        pass
    def _on_mouse1_up(self, ue):
        """pass"""
        pass
    def _on_mouse2_up(self, ue):
        """pass"""
        pass
    def _on_mouse3_up(self, ue):
        """pass"""
        pass
    def _on_mouse_in(self, ue):
        """pass"""
        pass
    def _on_mouse_out(self, ue):
        """pass"""
        pass
    def _on_wheel_up(self, ue):
        """pass"""
        pass
    def _on_wheel_down(self, ue):
        """pass"""
        pass
    
    # Main Loop.
    def _handle_mouse_events_(self, ue, verbosity=PROP_VERBOSE):
        # Handle any raw mouse evts.
        for m_evt in ue.mouse_events:
            cmd_name = "_on_{}".format(m_evt.replace("-","_"))
            # Look for specific handler map first;
            # fall back on generic self.propagate.
            if cmd_name in self.p_map: propagate = self.p_map[cmd_name]
            else: propagate = self.propagate
            # If propagate is set to none attempt 
            # to handle evt with self.
            if propagate == "none":
                if cmd_name in self.__dict__:
                    cmd = eval("self._{}".format(cmd_name))
                    cmd(self, ue)
                # Issue warning on handle failure.
                elif verbosity:
                    msg = "GUI Warning: '{}' evt unhandled for non-propagating widget:\n  {}"
                    print(msg.format(cmd_name, self.wid))
            # If propagation given then use requested type.
            else:
                if propagate == "all":
                    handled = self.propagate_thru_all(cmd_name, args=[ue], _reset=True)
                elif propagate == "parents":
                    handled = self.propagate_thru_parents(cmd_name, args=[ue], _reset=True)
                elif propagate == "masters":
                    handled = self.propagate_thru_masters(cmd_name, args=[ue], _reset=True)
                # Issue warning on handle failure.
                if not handled and verbosity:
                    msg = "GUI Warning: {} evt unhandled for propagating widget:\n  {}"
                    
    def _update_event_box_(self):
        x, null, y = self.NP.getPos(pixel2d)
        w, h = self.size
        px, py = self.pad
        self._x_min = x-(w+px)/2
        self._x_max = x+(w+px)/2
        self._y_min = -y-(h+py)/2
        self._y_max = -y+(h+py)/2

class _Drag_Mask_(_Mouse_Event_Handler_):
    
    # Events.
    def _on_mouse1(self, ue):
        """Add self to Window.drag_widgets."""
        if self not in self.Window.drag_widgets:
            self.Window.drag_widgets.append(self)
    def _on_mouse1_up(self, ue):
        """Fart"""
        if self in self.Window.drag_widgets:
            self.Window.drag_widgets.remove(self)
            
    # Main Loop.
    def _drag_(self, ue):
        self.NP.setPos(self.NP, ue.x_diff, 0, -ue.y_diff)
        return self.get_family()

class _Key_Event_Handler_(_Mouse_Event_Handler_):
    propagate = "none"
    _takes_key_events = True
    
    # Events.
    def _on_mouse_in(self, ue):
        self._key_focus = True
    def _on_mouse_out(self, ue):
        self._key_focus = False
    
    # Main Loop.
    def _handle_key_events_(self, ue):
        pass
    
    # Setup.
    def __build__(self):
        self._key_focus = False
        
class _Text_Processor_(_Key_Event_Handler_):
    tab = 4
    _init_repeat_delay = .5
    _repeat_delay = .1
    _multi_list = False
    _shift_map = {
        '1':"!", '2':"@", '3':"#", '4':"$", '5':"%",
        '6':"^", '7':"&", '8':"*", '9':"(", '0':")",
        '`':"~", '-':"_", '=':"+", '[':"{", ']':"}",
        ';':":", ',':"<", '.':">", '/':"?", '\\':"|",
        "'":'"'}
    
    # Override.
    def refresh_text(self, chars, ind):
        pass
    
    # Main Loop.
    def _handle_key_events_(self, ue):
        # Key down events.
        for chars in ue.key_events:
            taskMgr.remove("chars")
            if len(chars) == 1:
                # Basic alpha/num keys.
                chars = self._handle_char_Clk(chars)
            else:
                # Other keys (enter, space, del, etc.)
                handler = eval("self._handle_{}_Clk".format(chars))
                chars = handler()
            # Enter chars and queue repeat entry task.
            if chars:
                self._enter_chars(chars)
                taskMgr.doMethodLater(self._init_repeat_delay, self._repeat_chars, "chars")
                self._c_chars = chars
                
        # Key up events.
        for chars in ue.key_up_events:
            # Basic alpha/num keys.
            if len(chars) == 1:
                chars = self._handle_char_up_Clk(chars)
                self._c_chars = []
            # Other keys.
            else:
                handler = eval("self._handle_{}_Clk".format(chars))
                chars = handler(up=True)
            self._c_chars = ""
    
    def _enter_chars(self, chars):
        # Add chars to CHARS list.
        for c in chars:
            self.CHARS.insert(self._index, c)
            self._index += 1
        # Convert to str and refresh text.
        chars = "".join(self.CHARS)
        self.refresh_text(chars, self._index)
        
    def _repeat_chars(self, task):
        # Handle key hold char repeating.
        if self._c_chars:
            if self._c_chars == "<BACKSPACE>":
                self._handle_backspace_Clk()
            else:
                self._enter_chars(self._c_chars)
                taskMgr.doMethodLater(self._repeat_delay, self._repeat_chars, "chars")
    
    # Setup.
    def __build__(self):
        self.CHARS = []
        self._c_chars = ""
        self._p_chars = ""
        self._index = 0
        self._shift = False
        self._control = False
        self._alt = False
        self._caps = False


    # Alpha-numeric keys.
    def _handle_char_Clk(self, char):
        if self._shift or self._caps:
            if char.isalpha():
                return char.upper()
            elif not self._caps:
                return self._shift_map[char]
        return char
        
    def _handle_char_up_Clk(self, char):
        pass

    # Main keys.        
    def _handle_space_Clk(self, up=False):
        return " "
    def _handle_enter_Clk(self, up=False):
        pass
    def _handle_tab_Clk(self,up=False):
        spaces = self.tab - (self._index%self.tab)
        return "{}".format("{: ^{spaces}}".format("",spaces=spaces))
    def _handle_backspace_Clk(self, up=False):
        if up:
            self._c_chars = ""
        elif self.CHARS and self._index:
            self._index -= 1
            self.CHARS.pop(self._index)
            self.refresh_text("".join(self.CHARS), self._index)
            self._c_chars = "<BACKSPACE>"
            taskMgr.doMethodLater(0.1, self._repeat_chars, "chars")

    # Cursor keys.
    def _handle_insert_Clk(self, up=False):
        pass
    def _handle_delete_Clk(self, up=False):
        if self.CHARS:
            if len(self.CHARS) != self._index:
                self.CHARS.pop(self._index)
    def _handle_home_Clk(self, up=False):
        self._index = 0
    def _handle_end_Clk(self, up=False):
        self._index = len(self.CHARS)
    def _handle_page_up_Clk(self, up=False):
        pass
    def _handle_page_down_Clk(self, up=False):
        pass
    def _handle_capslock_Clk(self, up=False):
        if not self._caps: self._caps = True
        else: self._caps = False

    # Arrow keys.
    def _handle_arrow_left_Clk(self, up=False):
        if self._index:
            self._index -= 1
    def _handle_arrow_right_Clk(self, up=False):
        if self._index != len(self.CHARS):
            self._index += 1
    def _handle_arrow_up_Clk(self, up=False):
        pass
    def _handle_arrow_down_Clk(self, up=False):
        pass
        
    # Raw modifier keys.
    def _handle_lshift_Clk(self, up=False):
        if up: self._shift = False
        else: self._shift = True
    def _handle_rshift_Clk(self, up=False):
        if up: self._shift = False
        else: self._shift = True
    def _handle_lcontrol_Clk(self, up=False):
        if up: self._control = False
        else: self._control = True
    def _handle_rcontrol_Clk(self, up=False):
        if up: self._control = False
        else: self._control = True
    def _handle_lalt_Clk(self, up=False):
        if up: self._alt = False
        else: self._alt = True
    def _handle_ralt_Clk(self, up=False):
        if up: self._alt = False
        else: self._alt = True



class _Value_Keeper_:
    
    # Public.
    def get_val(self):
        return self.VAL
    def set_val(self, val):
        self.VAL = val
    def has_attr(self, attr):
        if attr in self.__dict__:
            return True
    
    # Setup.
    def __build__(self):
        self.VAL = None

class _Obj_Tracker_:
    _track_obj = None
    _hide_dist = 0
    
    # Main Loop.
    def _track_(self):
        # If the tracked obj hasn't moved return.
        pos = self._track_obj.getPos(self.CTRL.CAMERA.NP)
        if pos == self._prev_pos:
            return None
        # Show/hide widget based on "_hide_dist" attr if given.
        if self._hide_dist > 0:
            dist = pos.length()
            if dist <= self._hide_dist:
                self.NP.show()
            else:
                self.NP.hide()
                return None
        # Reposition widget.
        bx, by, bz = pos
        p_scale = self.Window._unit_y/by
        new_x = bx*p_scale + self.Window._hw + self._x_offset
        new_y = -bz*p_scale + self.Window._hh + self._y_offset
        self.NP.setPos(pixel2d, new_x, 0, -new_y)
        self._prev_pos = pos
        return self.get_family()

class Window(_Widget_):
    size = (0, 0)
    _hw, _hh = size[0]/2, size[1]/2
    _unit_y = 0
    layout = {
        'rows':1,
        'cols':1,
        'col_heights':[size[0]],
        'row_widths':[size[1]]}
    
    # Public.
    def render(self):
        w, h = self.size
        self.NP.reparentTo(pixel2d)
        self.NP.setPos(w/2, 0, -h/2)
        self._x_min, self._y_min = 0, 0
        self._x_max, self._y_max = self.size
        for child in self.Children:
            child.render()
    def add_widget(self, widget):
        self.add_widgets([widget])
    def add_widgets(self, widgets):
        self.__add_Widgets(widgets)
    def remove_widget(self, widget):
        self.remove_widgets([widget])
    def remove_widgets(self, widgets):
        self.__remove_Widgets(widgets)
    
    # Setup.
    def __map__(self, attrs):
        _Widget_.__map__(self, attrs)
        self.size = (self.CTRL.client.win.getXSize(), self.CTRL.client.win.getYSize())
        self._unit_y = tan(radians(90-self.CTRL.client.camLens.getFov()[0]/2)) * self.__class__._hw
    def __init__(self, ctrl):
        self.CTRL = ctrl
        self.Window = self
        _Widget_.__init__(self, None)
        self.EVENT_WIDGET = None
        self.mouse_event_widgets = []
        self.key_event_widgets = []
        self.drag_widgets = []
        self.track_widgets = []
        self.universal_widgets = []
        # Populate above lists with applicable widgets from family; list
        # is reversed so that children get chance to handle event first.
        self.__add_Widgets(reversed(self.get_family()))
        
    def __wid__(self):
        self.wid = self.__class__.__name__.lower()
    
    
    def _main_loop_(self, ue, dt):
        evt_widget = self.EVENT_WIDGET

        # If evt_widget is marked it steals all events,
        # useful for pop up / drop down menus.
        if evt_widget:
            mouse_evt_widgets = evt_widget.get_family()
        else:
            mouse_evt_widgets = list(self.mouse_event_widgets)
            
        # Pass UE to universal widgets (those that 
        # accept mouse evts regardless of mouse pos).
        for widget in self.universal_widgets:
            widget._handle_mouse_events_(ue)
            if widget in mouse_evt_widgets:
                mouse_evt_widgets.remove(widget)
        
        # Pass UE to qualifying mouse evt handlers.
        for widget in mouse_evt_widgets:
            if not widget.NP.isHidden():
                # Test coords to see if mouse evts
                # occurred over this widget.
                mx, my = ue.mouse_pos
                if mx >= widget._x_min\
                and mx <= widget._x_max\
                and my >= widget._y_min\
                and my <= widget._y_max:
                    if not widget._mouse_over:
                        widget._on_mouse_in(ue)
                        widget._mouse_over = True
                    if ue.mouse_events:
                        widget._handle_mouse_events_(ue)
                        ue.mouse_events = []
                else:
                    # Trigger mouse out evt if applicable.
                    if widget._mouse_over:
                        widget._on_mouse_out(ue)
                        widget._mouse_over = False
        
        # Handle key events.
        if ue.key_events:
            if evt_widget:
                # 'event_widget' and family steal all events.
                for widget in evt_widget.get_family():
                    if widget._takes_key_events:
                        widget._handle_key_events_(ue)
            else:
                # Search all 'key_event' widgets for a qualified handler.
                for widget in self.key_event_widgets:
                    if widget._key_focus:
                        widget._handle_key_events_(ue)
        
        # Handle widgets being dragged.
        for widget in self.drag_widgets:
            group = widget._drag_(ue)
            # Update widget's mouse event rectangle if applicable.
            for member in group:
                if member._takes_mouse_events:
                    member._update_event_box_()
        
        # Any L mouse up cancels drag.
        if "mouse1-up" in ue.mouse_events:
            self.drag_widgets = []
            
        # Update tracking widget positions.
        for widget in self.track_widgets:
            group = widget._track_()
            # Update widget's mouse event rectangle if applicable.
            if group:
                for member in group:
                    if member._takes_mouse_events:
                        member._update_event_box_()


    def __add_Widgets(self, widgets):
        for widget in widgets:
            if widget._takes_mouse_events:
                self.mouse_event_widgets.append(widget)
            if widget._takes_key_events:
                self.key_event_widgets.append(widget)
            if widget._track_obj:
                self.track_widgets.append(widget)

    def __remove_Widgets(self, widgets):
        for widget in widgets:
            if widget in self.mouse_event_widgets:
                self.mouse_event_widgets.remove(widget)
            if widget in self.key_event_widgets:
                self.key_event_widgets.remove(widget)
            if widget in self.track_widgets:
                self.track_widgets.remove(widget)

class Container(_Widget_, _Cmd_Propagator_):
    
    # Public.
    def build_primitives(self):
        w, h = self.size
        px, py = self.pad
        body_size = (w+px, h+py)
        self.body = rectangle(body_size, self.bg)
        self.body.NP.reparentTo(self.NP)
        self.Border = Border(self.border, body_size)
        self.Border.NP.reparentTo(self.NP)
    
    # Setup.
    def __init__(self, master, **attrs):
        _Widget_.__init__(self, master, **attrs)
        self.build_primitives()

class Image(Container):
    
    bg = (1,1,1,1)
    size = (-1, -1)
    image = None
    edge = 0.0
    
    # Setup.
    def __init__(self, master, **attrs):
        self._img_path = Filename(self.path)
        self.Image = PNMImage(self._img_path)
        self.Image.setColorType(PNMImage.CTFourChannel)
        w, h = self.size
        if w == -1: w = self.Image.getReadXSize()
        if h == -1: h = self.Image.getReadYSize()
        self.size = (w, h)
        Container.__init__(self, master, **attrs)
        
        self.Texture = Texture()
        self.Texture.load(self.Image)
        self.Texture.setWrapU(Texture.WMClamp)
        self.Texture.setWrapV(Texture.WMClamp)
        self.body.NP.setTexture(self.Texture)
        if self.edge:
            self.__build_Edge()

    # Private.
    def __build_Edge(self):
        w, h = self.size
        for y in range(h-1):
            y_fade = 1.0
            if y < self.edge:
                y_fade = y/self.edge
            elif y > h-self.edge:
                y_fade = (h-y)/self.edge
            for x in range(w-1):
                x_fade = 1.0
                if x < self.edge:
                    x_fade = x/self.edge
                elif x > w-self.edge:
                    x_fade = (w-x)/self.edge
                self.Image.setAlpha(x, y, min(x_fade, y_fade))
        self.Texture.load(self.Image)



class Display_Region(_Mouse_Event_Handler_, _Widget_):
        
    # Public.
    def set_content(self, content):
        if self.Content:
            self.Content.NP.removeNode()
        self.Content = content
        self.Children = [content]
    def render(self, grid=None, place=None):
        self._Render(grid, place)
        self.__build_Region()
        if self.Content:
            self.Content.render()
        self._update_event_box_()
        
    # Main Loop.
    def _update_event_box_(self):
        x, null, y = self.NP.getPos(pixel2d)
        _Mouse_Event_Handler_._update_event_box_(self)
        if self.dr:
            ww, wh = self.Window.size
            l = self._x_min / ww
            r = self._x_max / ww
            b = self._y_min / wh
            t = self._y_max / wh
            self.dr.setDimensions(l, r, 1-t, 1-b)
    
    # Setup.            
    def __build__(self):
        self.dr = None
        self.Content = None
    
    # Private.
    def __build_Region(self):
        self.dr = base.win.makeDisplayRegion()
        self.dr.setSort(20)
        
        cam_np = NodePath(Camera("cam"))
        self.lens = OrthographicLens()
        self.lens.setFilmSize(*self.size)
        self.lens.setNearFar(-1000, 1000)
        cam_np.node().setLens(self.lens)
    
        self.NP.setDepthTest(False)
        self.NP.setDepthWrite(False)
        cam_np.reparentTo(self.NP)
        self.dr.setCamera(cam_np)
        self.NP.setPos(self._x_offset, 2000, self._y_offset)  ## Hack
        

class Text(_Widget_):
    text = ""
    place = {'anchor':"c"}
    orient = "horizontal"
    
    # Public.
    def set_text(self, text, resize=False):
        if text == self.text: return
        self.text = text
        self.text_node.setText(text)
        self.size = self.get_size()
        self.render()
    def get_size(self, isnan=isnan):
        w = self.text_node.getWidth()
        h = self.text_node.getHeight()
        if isnan(w): w = 0
        if isnan(h): h = 0
        return int(w), int(h)
        
    # Setup.
    def __init__(self, master, **attrs):
        _Widget_.__init__(self, master, **attrs)
        self.text_node = TextNode("text")
        self.text_NP = NodePath(self.text_node)
        self.text_NP.reparentTo(self.NP)

        self.text_node.setAlign(TextNode.ACenter)
        self.text_node.setPreserveTrailingWhitespace(True)
        self.text_node.setText(str(self.text))
        self.text_node.setGlyphScale(self.font.size)
        self.text_node.setFont(self.font.FONT)
        
        if self.orient == "vertical":
            self.text_node.setWordwrap(1.0)
        gs = self.font.size / 2 - 1
        if self.orient == "vertical":
            gs -= h / 2 - self.font.size / 2
        self.text_node.setGlyphShift(-gs)
        self.size = self.get_size()
        
class Entry(_Text_Processor_, Container):
    bg = (1,1,1,1)
    error_bg = (.7,0,0,1)
    
    # Public.
    def refresh_text(self, chars, ind):
        self.Text.set_text(chars, resize=True)
        if chars: x, y = util.get_text_size(chars, self.font)
        else: x = 0
        self.Cursor.NP.setX(-self.size[0]/2+x)
        self.Text.render()
        
    # Children.
    class Text(Text):
        text = ""
        place = {'anchor':"w",'left':0}
        def __map__(self):
            Text.__map__(self)
            self.bg = self.Master.font.colour
            self.font = self.Master.font
            self.place.top = self.Master.font.size/2
            self.size = (1,self.Master.font.size)
            
    class Cursor(Container):
        place = {'anchor':"w",'left':0}
        def __map__(self):
            Container.__map__(self)
            self.bg = self.Master.font.colour
            self.place.top = self.Master.font.size/2-1
    
    children = [Text, Cursor]
    
    # Value Handling.
    def get_val(self):  ## Make value handling a mixin widget.
        val_str = self.Text.text
        val = self.check_val(val_str)
        if val:
            self.body.NP.setColor(*self.bg)
            return val
        else:
            self.body.NP.setColor(*self.error_bg)
            return self.handle_val_error(val_str)
    def set_val(self, val):
        self.Text.set_text("", resize=True)
        self.refresh_text("{}".format(val), 0)
    def check_val(self, val):
        return val
    def handle_val_error(self, val):
        return False
    
    # Events.       
    def _on_mouse_in(self, ue):
        self._key_focus = True
        self.Cursor.NP.show()
        taskMgr.doMethodLater(0.5, self._flash_Cursor, "cursor", appendTask=True)
    def _on_mouse_out(self, ue):
        self._key_focus = False
        self.Cursor.NP.hide()
        taskMgr.remove("cursor")
    def _flash_Cursor(self, task):
        if self.Cursor.NP.isHidden():
            self.Cursor.NP.show()
        else:
            self.Cursor.NP.hide()
        return task.again
        
    # Setup.
    def __children__(self):
        Container.__children__(self)
        self.Text, self.Cursor = self.Children
        self.Cursor.NP.hide()
    
    def __build__(self):
        w, h = util.get_text_size("{:_^{width}}".format("",width=self.width), self.Text.font)
        self.size = (w+self.pad_x*2, self.font.size+self.pad_y*2)
        self._char_width = util.get_text_size("_", self.Text.font)
        
        
    


class Button(_Mouse_Event_Handler_, Container):
    orient = "horizontal"
    anim_depth = 1
    anim_border = "default"
    over_bg = None
    toggle = False
    
    # Public.
    def set_text(self, text):
        self.text = text
        self.rebuild()
    
    # Children.
    class Text(Text):
        place = {'anchor':"c"}
        def __init__(self, master):
            self.text = master.text
            self.orient = master.orient
            Text.__init__(self, master)
        def __map__(self, attrs):
            Text.__map__(self, attrs)
            self.font = self.Master.font
            
    children = [Text]
    
    # Events.
    def _on_mouse1(self, ue):
        """Button down anim."""
        self._is_pressed = True
        self.__button_Down()
    def _on_mouse1_up(self, ue):
        """Button up anim."""
        if self._is_pressed:
            self._is_pressed = False
            self.__button_Up()
    def _on_mouse_in(self, ue):
        """Set bg to mouse over col."""
        if self.over_bg:
            self.body.NP.setColor(*self.over_bg)
    def _on_mouse_out(self, ue):
        """Return bg to normal col."""
        if self.over_bg:
            self.body.NP.setColor(*self.bg)
        if self._is_pressed and not self.toggle:
            self._is_pressed = False
            self.__button_Up()
            
    # Setup.
    def __init__(self, master, **attrs):
        _Widget_.__init__(self, master, **attrs)
        # Make sure button size at least matches text size.
        self.Text = self.Children[0]
        tw, th = self.Text.size
        w, h = self.size
        if tw > w: w = tw
        if th > h: h = th
        pw, ph = self.pad
        self.size = w, h
        self.layout.refresh()
        self.build_primitives()

        # Set mouse over bg.
        if self.over_bg != None:
            if type(self.over_bg) == FloatType:
                self.over_bg = util.get_alt_shade(self.bg, self.over_bg)
        # Set anim border.
        if self.border:
            if self.anim_border == "default":
                bl, bt = self.border.right, self.border.bottom
                br, bb = self.border.left, self.border.top
                self._anim_border = {'left':{'thick':bl.thick,'colour':bl.colour},
                                     'top':{'thick':bt.thick,'colour':bt.colour},
                                     'right':{'thick':br.thick,'colour':br.colour},
                                     'bottom':{'thick':bb.thick,'colour':bb.colour}}
                self.anim_border = border_attr(self, self._anim_border)
        self._orig_border = self.border
        self._is_pressed = False  # Make attr unique to instance.

    # Private.
    def __button_Down(self):
        if self.anim_depth:
            x, null, y = self.Text.NP.getPos()
            self.Text.NP.setPos(x+self.anim_depth, 0, y-self.anim_depth)
        if self.anim_border != None:
            self.border = self.anim_border
            self.border.refresh()
            
    def __button_Up(self):
        if self.anim_depth:
            x, null, y = self.Text.NP.getPos()
            self.Text.NP.setPos(x-self.anim_depth, 0, y+self.anim_depth)
        if self.anim_border != None:
            self.border = self._orig_border
            self.border.refresh()
    
class Scroll_Bar(_Drag_Mask_, Button):
    text = "- "
    _width = 14
    
    # Public.
    def set_scrollee(self, scrollee):
        """Scrollee is the widget to be scrolled by the bar."""
        self.scrollee = scrollee
        self.__set_Scrollee(scrollee)
        
    # Events.
    def _on_mouse1(self, ue):
        """Start scroll."""
        self.__being_scrolled = True
        self.Window.universal_widgets.append(self)
    def _on_mouse1_up(self, ue):
        """End scroll."""
        self.__being_scrolled = False
        if self in self.Window.universal_widgets:
            self.Window.universal_widgets.remove(self)
        
    # Main Loop.
    def _drag_(self, ue):
        """Dragging results in y-axis only movement for scrollbar and scrollee."""
        # Apply y-axis movement to scrollbar.
        if self.__scroll_max:
            if self.__being_scrolled and self.scrollee:
                self.NP.setPos(self.NP, 0, 0, -ue.y_diff)
            # Test if bar is past its top or bottom border and correct
            # both its position and the scrollee's pos if necessary.
            y = self.NP.getZ()
            if y > self.__scroll_max:
                self.NP.setZ(self.__scroll_max)
                self.scrollee.NP.setZ(-self.__scroll_max*self.__scroll_multi)
            elif y < self.__scroll_min:
                self.NP.setZ(self.__scroll_min)
                self.scrollee.NP.setZ(-self.__scroll_min*self.__scroll_multi)
            # If bar is in range and being scrolled then scroll scrollee.
            else:
                if self.__being_scrolled:
                    self.scrollee.NP.setZ(self.scrollee.NP, ue.y_diff*self.__scroll_multi)
            return self.__family
        return []
    
    # Setup.
    def __map__(self):
        cls = self.__class__
        cls.border = {'thick':1,'colour':self.Master.bg, 'bevel':(.1,.1,-.5,-.5)}
        Button.__map__(self)
        self.scrollee = None
        self.__being_scrolled = False
        self.__scroll_multi = 1
        self.__scroll_max = 0.0
        self.__scroll_min = 0.0
    def __build__(self):
        self.__family = self.get_family()
            
    # Private. 
    def __set_Scrollee(self, scrollee):
        # Set scrollee dependent variables.
        sh = float(scrollee.size[1])
        trough_h = self.Master.size[1]
        h = trough_h * (trough_h/float(sh))
        if h > trough_h:
            h = trough_h
        self.__scroll_multi = sh / float(trough_h)
        self.__scroll_max = trough_h/2.0 - h/2.0
        self.__scroll_min = -self.__scroll_max
        self.size = (self.size[0], int(h))
        self.rebuild()
        ## scrollee.NP.setZ(scrollee.NP, -self.__scroll_min*self.__scroll_multi)
        self.NP.setZ(0)
        self._update_event_box_()
        
class _Menu_Bar_(Container):
    bg = (0,0,0,0)
    spacing = 0
    
    class Menu_Bar_Button(Button):        
        def __map__(self):
            Button.__map__(self)
            self.pad_y = self.Master.button_pad_y
            self.pad_x = self.Master.button_pad_x
            self.font = self.Master.font
            self.orient = self.Master.orient
        def __wid__(self):
            self.wid = "{}_{}_button".format(self.Master.wid, self.text.lower())
        def _on_mouse1_up(self, ue):
            """Call -> menu_bar_button_clk."""
            self.propagate_thru_masters("menu_bar_button_clk", args=[self])
            
    # Events.
    def menu_bar_button_clk(self, button):
        """Show/hide menu. <STOP>"""
        menu = button.Menu
        if menu.NP.isHidden():
            for m in self.Menus:
                m.hide()
            menu.show()
        else:
            menu.hide()
        return True

    # Setup.
    def __children__(self):
        self.c_dict = {}
        buttons, menus = [], []
        for Menu in self.Menus:
            class MB_Button(self.__class__.Menu_Bar_Button):
                text = ""
                if "button_text" in Menu.__dict__:
                    text = Menu.button_text
                bg = Menu.bg
            button = MB_Button(self)
            menu = Menu(self)
            button.Menu = menu
            self.c_dict[button.wid] = button
            self.c_dict[menu.wid] = menu
            buttons.append(button)
            menus.append(menu)
        self.Children = list(self.c_dict.values())
        self.Buttons = buttons
        self.Menus = menus


class Horizontal_Menu_Bar(_Menu_Bar_):
    
    orient = "horizontal"
    
    def __build__(self):
        w, h = 0, 0
        for button, menu in zip(self.Buttons, self.Menus):
            if button.size[1] > h :
                h = button.size[1]
            button.place.refresh({'anchor':"nw",'top':0,'left':w})
            menu.place.refresh({'anchor':"nw",'top':h+1,'left':w+1})
            w += button.size[0] + self.spacing
        self.size = (w, h)
        self.layout.refresh()
        

class Left_Vertical_Menu_Bar(_Menu_Bar_):
    
    orient = "vertical"
    anchor = "nw"
    side = "left"
    
    def __build__(self):
        w, h = self.size
        for button, menu in zip(self.Buttons, self.Menus):
            if button.size[0] > w:
                w = button.size[0]
            button.place.refresh({'anchor':"nw",'top':h,'left':0})
            menu.place.refresh({'anchor':self.anchor,'top':h,self.side:w+1})
            h += button.size[1] + self.spacing
        self.size = (w, h)
        self.layout.refresh()


class Right_Vertical_Menu_Bar(Left_Vertical_Menu_Bar):
    
    anchor = "ne"
    side = "right"
    

class Menu(Container, _Mouse_Event_Handler_):
    
    anchor = "nw"
    display = False
    



class Drop_Menu(Menu):
    _button_names = []
    spacing = 0
    
    # Public.
    def set_drop_buttons(self, button_names):
        self._button_names = button_names
        self.rebuild()
    
    # Children.
    class Drop_Menu_Button(Button):
        # Events.
        def _on_mouse1_up(self, ue):
            """Call -> drop_menu_clk."""
            self.propagate_thru_all("drop_button_clk", args=[self])
        # Children.
        class Drop_Menu_Button_Text(Button.Text):
            place = {'anchor':"w",'left':0}
        children = [Drop_Menu_Button_Text]
        # Setup.
        def __map__(self):
            Button.__map__(self)
            ## self.bg = self.Master.bg
            self.font = self.Master.font
        def __wid__(self):
            self.wid = "{}_{}_button".format(self.Master.wid, self.text.lower())

    # Setup.
    def __children__(self):
        if not self.button_names: return []
        # Find the longest button name and use that to determine widths for all buttons.
        bw = max(map(lambda text: util.get_text_size(text.title(), self.font)[0], self.button_names))
        bh = int(util.get_text_size(self.button_names[0].title(), self.font)[1])
        top = self.border.top.thick + 2
        left = self.border.left.thick + 2
        self.c_dict = odict()
        for row, b_name in enumerate(self.button_names):
            class D_Menu_Button(self.__class__.Drop_Menu_Button):
                text = b_name
                bg = (0,1,0,1) ## self.bg
                place = {'anchor':"nw",
                         'top':top,
                         'left':left}
                size = (bw, bh)
            drop_button = D_Menu_Button(self)
            self.c_dict[drop_button.wid] = drop_button
            top += bh + self.spacing
        self.Children = list(self.c_dict.values())
        
        # Set menu size.
        w, h = 0, 0
        for button in self.Children:
            bw, bh = button.get_total_size()
            if bw+self.pad_x*2 > w:
                w = bw + self.pad_x*2
            h += bh + self.spacing
        h += self.pad_y*2
        h -= self.spacing
        self.size = (w, h)

class Select(Button):
    
    text = ""
    bg = (1,1,1,1)
    alt_bg = (.8,.8,.8,1)
    button_spacing = 0
    propagate = "parents"
    border = {
        'thick':2,
        'colour':(.35,.35,.35,1),
        'left':{'colour':(.25,.25,.25,1)},
        'bottom':{'colour':(.25,.25,.25,1)}}
        
    # Public.
    def get_val(self):
        return self.Text.text
    def set_val(self, val):
        self.Text.set_text(val, resize=True)
        
    # Events.
    def _on_mouse1_up(self, ue):
        """Show/hide select drop menu."""
        if self.Menu.NP.isHidden():
            # Need to reparent to get menu above other widgets.
            self.Menu.NP.reparentTo(self.NP)
            self.NP.reparentTo(self.Master.NP)
            self.Menu.NP.show()
            self.Window.EVENT_WIDGET = self.Menu
        else:
            self.Menu.NP.hide()
            self.Window.EVENT_WIDGET = None
        return True
    def _on_mouse_out(self, ue):
        self.body.NP.setColor(*self.bg)
    def _drop_button_clk(self, button):
        """Update Select widget text."""
        self.Text.set_text(button.text, resize=True)
        
    # Children.
    class Select_Drop_Menu(Drop_Menu):
        bg = (1,1,1,1)
        alt_bg = (.8,.8,.8,1)
        border = {
            'thick':1,
            'colour':(0,0,0,1)}
        place = {'anchor':"nw",'left':0}
        # Setup.
        def __map__(self):
            Drop_Menu.__map__(self)
            self.button_names = self.Master.button_names
            if "font" not in self.__class__.__dict__:
                self.font = self.Master.font
            self.spacing = self.Master.button_spacing 
        def __wid__(self):
            self.wid = "{}_drop_menu".format(self.Master.wid)
            
    class Select_Text(Text):
        text = ""
        place = {'anchor':"w",'left':0}
        # Setup.
        def __map__(self):
            Text.__map__(self)
            self.font = self.Master.font
            self.place.top = self.Master.font.size/2
        def __wid__(self):
            self.wid = "{}_text".format(self.Master.wid)
            
    children = [Select_Drop_Menu, Select_Text]
    
    # Setup.    
    def __children__(self):
        Button.__children__(self)
        self.Menu = self.Children[0]
        self.Menu.select = self
        self.Text = self.Children[1]

    def __build__(self):
        w, h = util.get_text_size("{:_^{width}}".format("",width=self.width), self.Text.font)
        self.size = (w+self.pad_x*2, self.font.size+self.pad_y*2)
        self.layout.refresh()

class Num_Switch(Container):
    init_val = 0
    min_val = 0
    max_val = 1
    step = 1
    font = DEFAULT_FONT
    layout = {
        'rows':2,
        'cols':2}
        
    # Public.
    def get_val(self):
        return self.current_val
    def set_val(self, val):
        val = int(val)
        if val > self.max_val: val = self.max_val
        elif val < self.min_val: val = self.min_val
        self.current_val = val
        self.Display_Text.set_text(str(self.current_val))
    
    # Value Display.
    class Val_Display(Container):
        pad_x = 3
        pad_y = 1
        bg = (1,1,1,1)
        border = {
            'thick':2,
            'colour':(.3,.3,.3,1),
            'left':{'colour':(.1,.1,.1,1)},
            'bottom':{'colour':(.1,.1,.1,1)}}
        grid = {'row':0,
                'col':0,
                'row_span':2}
        # Value Display Text.
        class Val_Display_Text(Text):
            text = "0"
            place = {'anchor':"nw", 'top':0, 'left':0}
            def __map__(self):
                Text.__map__(self)
                if "font" not in self.__class__.__dict__:
                    self.font = self.Master.font
            def __wid__(self):
                self.wid = "{}_text".format(self.Master.wid)
        children = [Val_Display_Text]
        def __map__(self):
            Container.__map__(self)
            if "font" not in self.__class__.__dict__:
                self.font = self.Master.font
        def __wid__(self):
            self.wid = "{}_val_display".format(self.Master.wid)
        def __build__(self):
            w, h = self.Children[0].size
            self.size = (w+self.pad_x*2, h+self.pad_y*2)
            
    # Buttons.
    class Plus_Button(Button):
        text = "+"
        grid = {'row':0,'col':1}
        place = {'anchor':"s",'bottom':1}
        propagate = "parents"
        cmd = "plus_button_clk"
        def __map__(self):
            Button.__map__(self)
            self.bg = util.get_alt_shade(self.Master.bg, -.1)
            if "font" in self.Master.__dict__:
                self.font = self.Master.font
        def _on_mouse1_up(self, ue):
            """Prop -> plus_button_clk."""
            self.propagate_thru_all(self.cmd)
        
    class Minus_Button(Button):
        text = "-"
        grid = {'row':1,'col':1}
        place = {'anchor':"n",'top':-1}
        propagate = "parents"
        cmd = "minus_button_clk"
        def __map__(self):
            Button.__map__(self)
            self.bg = util.get_alt_shade(self.Master.bg, -.1)
            if "font" not in self.__class__.__dict__:
                self.font = self.Master.font
        def _on_mouse1_up(self, ue):
            """Prop -> minus_button_clk."""
            self.propagate_thru_all(self.cmd)

    children = [Val_Display, Plus_Button, Minus_Button]
    
    
        
    # Handlers.
    def plus_button_clk(self):
        """Increment value in display. (STOP)"""
        if self.current_val < self.max_val:
            self.current_val += self.step
            if self.current_val > self.max_val:
                self.current_val = self.max_val
            self.Display_Text.set_text(str(self.current_val))
        return True
    def minus_button_clk(self):
        """Decrement value in display. (STOP)"""
        if self.current_val > self.min_val:
            self.current_val -= self.step
            if self.current_val < self.min_val:
                self.current_val = self.min_val
            self.Display_Text.set_text(str(self.current_val))
        return True
    
    # Setup.
    def __children__(self):
        Container.__children__(self)
        self.Val_Display = self.Children[0]
        self.Plus_Button = self.Children[1]
        self.Minus_Button = self.Children[2]
        self.Display_Text = self.Val_Display.Children[0]
        
    def __build__(self):
        self.current_val = int(self.init_val)
        



class Scrolling_Container(Container):
    size = (100,100)
    _scroll_bg = (.1,.1,.1,1)
    _scroll_width = 14
    _header_height = 0  # 0 means no header bar shows up.
    
    # Public.
    def set_display(self, display):
        self.Display_Region.set_content(display)
        self.Scroll_Bar.set_scrollee(display)
    def show(self):
        self.NP.show()
        self.Display_Region.show()
    def hide(self):
        self.NP.hide()
        self.Display_Region.hide()
        
    # Children.
    class Display_Region(Display_Region):
        place = {'anchor':"nw",'left':0,'top':0}
        def __map__(self):
            mw, mh = self.Master.size
            w, h = mw-self.Master._scroll_width, mh-self.Master._header_height
            self.__class__.size = (w, h)
            Display_Region.__map__(self)
    
    class Trough(Container):
        place = {'anchor':"ne",'top':0,'right':0}
        class Scroll_Bar(Scroll_Bar):
            font = {'name':"arial.ttf",'size':10,'colour':(.05,.05,.05,1)}
            place = {'anchor':"n",'top':0}
            def __map__(self):
                Scroll_Bar.__map__(self)
                self.size = (self.Master.Master._scroll_width-self.border.thick*2, 10)
            def __build__(self):
                self.bg = self.Master.Master._scroll_bg
                self._over_bg = util.get_alt_shade(self.bg, .1)
        children = [Scroll_Bar]
        def __map__(self):
            mw, mh = self.Master.size
            self.__class__.place['top'] = self.Master._header_height
            self.__class__.size = (self.Master._scroll_width, mh-self.Master._header_height)
            Container.__map__(self)
            
    class Header_Bar(Container):
        place = {'anchor':"n",'top':0}
        def __map__(self):
            mw, mh = self.Master.size
            hh = self.Master._header_height
            self.__class__.size = (mw, hh)
            Container.__map__(self)
     
    children = [Display_Region, Trough]
    
    # Setup.
    def __children__(self):
        if self._header_height:
            # Append class's Header_Bar to children.
            self.children.append(self.__class__.Header_Bar)
        Container.__children__(self)
    def __build__(self):
        self.Display_Region = self.Children[0]
        self.Trough = self.Children[1]
        self.Scroll_Bar = self.Trough.Children[0]
        if self._header_height:
            self.Header_Bar = self.Children[2]
    
    
class Dialog(Container):
    bg = (.2,.2,.2,1)
    size = (200,200)
    border = {'colour':(.3,.3,.3,1),
              'thick':5}
    name = "Dialog"
    
    bar_height = 16
    bar_y_pad = 4
    bar_font = {'name':"arial.ttf",
                'size':bar_height/2,
                'colour':util.get_alt_shade(bg,.2)}
    
    # Public.
    def show(self):
        Container.show(self)
        self.Top_Bar._drag_on = True
        self.__layer__()
    def close(self):
        self.hide()

    # Children.
    class Top_Bar(_Drag_Mask_, Container):
        propagate = "parents"
        
        # Main loop.
        def _drag_(self, ue):
            if self._drag_on:
                self.Master.NP.setPos(self.Master.NP, ue.x_diff, 0, -ue.y_diff)
                return self.Master.get_family()
            return []

        # Setup.
        def __map__(self, attrs):
            mw, mh = self.Master.get_total_size()
            self.size = (mw, self.Master.bar_height)
            self.pad = (0, self.Master.bar_y_pad)
            self.bg = self.Master.border.colour
            self.place = {'anchor':"n",
                          'top':-self.Master.border.top.thick}
            self._drag_on = True
            Container.__map__(self, attrs)
            
        # Children.
        class Name(Text):
            place = {'anchor':"w",'left':0}
            
        class X_Button(Button):
            text = "x"
            pad = (8,6)
            place = {'anchor':"ne",'top':-2,'right':0}
            bg = (0,0,0,0)
            propagate = "parents"
            
            # Events.
            def _on_mouse1_up(self, ue):
                """Hide Dialog NP."""
                self.Master.Master.close()
        
        def __children__(self):
            Container.__children__(self)
            # Name.
            name_attrs = {'text':self.Master.name,
                          'font':self.Master.bar_font}
            self.Name_Text = self.__class__.Name(self, **name_attrs)
            # Close button.
            x_button_attrs = {'bg':self.Master.border.colour,
                              'over_bg':util.get_alt_shade(self.Master.bg, .1),
                              'font':self.Master.bar_font}
            self.X_Button = self.__class__.X_Button(self, **x_button_attrs)   
            self.Children.extend([self.Name_Text, self.X_Button])
                
    # Setup.
    def __children__(self):
        self.Top_Bar = self.__class__.Top_Bar(self)
        self.Children = [self.Top_Bar]
        



