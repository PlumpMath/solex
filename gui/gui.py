# ==============
# Solex - gui.py
# ==============


# Local.
import gui.p3gui.p3gui as gui

# Main BG colours.
MENU_COL = (.196,.216,.239,1)
MENU_LIGHT_COL = gui.util.get_mult_col(MENU_COL, 1.4)
MENU_DARK_COL = gui.util.get_mult_col(MENU_COL, .6)
MENU_EXLIGHT_COL = gui.util.get_mult_col(MENU_COL, 1.8)
MENU_EXDARK_COL = gui.util.get_mult_col(MENU_COL, .4)

# Fonts.
FONT_COL = (.453,.555,.621,1)
BUTTON_FONT = {'name':"arial.ttf",
               'size':10,
               'colour':(0,0,0,1)}             
TITLE_FONT = {
    'name':"arial.ttf",
    'size':72,
    'colour':MENU_COL}


# ---------
# Lobby GUI
# ---------

class Menu_Table(gui.Button):
    place = {'anchor':"n",'top':0}
    cell_font = {'name':"cour.ttf",'size':8,'colour':MENU_LIGHT_COL}
    row_height = 20
    row_list = []
    
    # Setup.
    def __children__(self):
        self.layout.refresh({'rows':len(self.row_list), 'row_heights':[self.row_height]})
        self.Children = []
        for i, row_list in enumerate(self.row_list):
            attrs = {'place':       {'anchor':"n",'top':i*self.row_height},
                     'children':    row_list,
                     '_sys_recipe': self.CTRL.sys_recipes[self.row_list[i][0].lower()]}
            row = self.__class__.Table_Row(self, **attrs)
            self.Children.append(row)
        self.Window.mouse_event_widgets.extend(self.Children)
        self.size = (self.Master.size[0], len(self.Children*self.row_height))
        
    # Children.
    class Table_Row(gui.Button):
        border = {'thick':1,'colour':(0,0,0,1)}
        over_bg = (.02,.02,.02,1)
        
        # Events.
        def _on_mouse1_up(self, ue):
            if self._is_pressed:
                self.Master.Master._row_clk(self)
    
        # Setup.
        def __children__(self):
            self.layout.refresh({'cols':len(self.children),
                                 'col_widths':self.Master.Master.col_widths})
            self.Children = []
            for c, _text in enumerate(self.children):
                text_place = {'anchor':"c"}
                align = self.Master.Master.col_align[c]
                if align == "l": text_place = {'anchor':"w",'left':4}
                elif align == "r": text_place = {'anchor':"e",'right':4}
                cell_text_attrs = {
                    'wid':          "{}.cell_{}".format(self.Master.wid, c),
                    'text':         _text,
                    'font':         self.Master.__class__.cell_font,
                    'place':        text_place,
                    'grid':         (0, c)}
                self.Children.append(gui.Text(self, **cell_text_attrs))
            self.size = (self.Master.Master.size[0]-self.__class__.border['thick']*2,
                         self.Master.__class__.row_height)



class _Menu_(gui.Dialog):
    size = (400, 400)
    bg = (0,0,0,1)
    display = False
    border = {'thick':5,'colour':MENU_DARK_COL}
    
    headings = []
    cols = 1
    col_widths = [size[0]]
    col_align = ["c"]
    
    bar_height = 24
    header_height = 20
    table_place = {'anchor':"n",'top':bar_height+header_height}
    bar_font = {'name':"arial.ttf",
                'size':10,
                'colour':gui.util.get_alt_shade(MENU_DARK_COL,.2)}
    
    # Public.
    def open(self):
        self.show()
        self.Button.Border.NP.show()
    def close(self):
        self.hide()
        self.Button.Border.NP.hide()
    def refresh(self, row_list):
        self.Table = Menu_Table(self, row_list=row_list, place=self.table_place)
        self.Window.add_widget(self.Table)
        self.Children.append(self.Table)
        self.Table.render()
        
    # Events.
    def _row_clk(self, row):
        pass
        
    # Children.
    class Header_Button(gui.Button):
        bg = MENU_EXDARK_COL
        font = {'name':"cour.ttf",'size':10,'colour':(1,0,0,1)}
     
    # Setup.
    def __children__(self):
        gui.Dialog.__children__(self)
        self.Table = None
        _left = 1
        for i, heading in enumerate(self.headings):
            _col_w = self.col_widths[i]
            if heading is self.headings[-1]:
                _col_w -= 1
            attrs = {
                'wid':      "{}.{}_header_button".format(self.wid, heading),
                'text':     heading,
                'size':     (_col_w-1, self.header_height),
                'place':    {'anchor':"nw",'top':self.bar_height,'left':_left},
                'over_bg':  gui.util.get_alt_shade(MENU_EXDARK_COL, .1)}
            self.Children.append(self.__class__.Header_Button(self, **attrs))
            _left += _col_w
        
class Profile_Menu(_Menu_):
    name = "Profile"
    headings = ["Char", "Location", "Status"]
    cols = 3
    col_widths = [100, 200, 100]

class Local_Menu(_Menu_):
    name = "Local"
    headings = ["System", "S", "P", "M", "Tot"]
    cols = 4
    col_widths = [200, 40, 40, 40, 80]
    col_align = ["l", "r", "r", "r", "r"]
    _sys_list = []
    
    # Public.
    def open(self):
        self._sys_list = []
        for sys_name, sr in self.CTRL.sys_recipes.items():
            sys_row = [sys_name, sr['_stars'], sr['_planets'], sr['_moons'], sr['_total']]
            self._sys_list.append(sys_row)
        self.refresh(self._sys_list)
        _Menu_.open(self)
    def close(self):
        _Menu_.close(self)
        self.Table.destroy()
        
    # Events.
    def _row_clk(self, row):
        sys_name = row.Children[0].text
        self.CTRL.launch_system_local(sys_name)
        
class Net_Menu(_Menu_):
    name = "Net"
    headings = ["Host", "Cluster", "System", "Ping"]
    cols = 4
    col_widths = [100, 100, 100, 100]
    col_anchors = ["w", "w", "w", "e"]
    


class Tools_Menu(_Menu_):
    name = "Tools"


class Settings_Menu(_Menu_):
    name = "Settings"
class Docs_Menu(_Menu_):
    name = "Docs"
    
# ------------
# Main Buttons
# ------------

# Main Button.
class _Main_Button_(gui.Button):
    bg = MENU_DARK_COL
    font = {
        'name':"arial.ttf",
        'size':16,
        'colour':MENU_LIGHT_COL}
    border = {'thick':1,'colour':(.5,.5,.5,1)}
    pad = (20, 14)
    propagate = "parents"
    border_anim = None
    over_bg = gui.util.get_alt_shade(bg, .1)
    
    # Events.
    def _on_mouse1_up(self, ue):
        """Show/hide menu."""
        if self.Menu.NP.isHidden():
            self.Menu.open()
        else:
            self.Menu.close()
        return True

    # Setup.
    def __init__(self, master):
        gui.Button.__init__(self, master)
        self.name = self.__class__.__name__.split("_")[0]
        _menu_id = "lobby_win.{}_menu".format(self.name.lower())
        self.Menu = self.Window.c_dict[_menu_id]
        self.Menu.Button = self
        self.Border.NP.hide()
    
class Main_Button_Container(gui.Container):
    place = {'anchor':"c",'top':320}
    layout = {'rows':1,'cols':5}
    spacing = 10

    class Local_Button(_Main_Button_):
        text = "Local"
        grid = (0, 0)
    class Net_Button(_Main_Button_):
        text = "Net"
        grid = (0, 1)
    class Tools_Button(_Main_Button_):
        text = "Tools"
        grid = (0, 2)
    class Settings_Button(_Main_Button_):
        text = "Settings"
        grid = (0, 3)
    class Docs_Button(_Main_Button_):
        text = "Docs"
        grid = (0, 4)

    children = [Local_Button,
                Net_Button,
                Tools_Button,
                Settings_Button,
                Docs_Button]
    
    # Setup.
    def __children__(self):
        gui.Container.__children__(self)
        w = 0
        col_widths = []
        for child in self.Children:
            cw, ch = child.get_total_size()
            added_w = cw+self.spacing
            w += added_w
            col_widths.append(added_w)
        h = child.size[1]
        self.size = (w,h)
        self.layout.refresh({'col_widths':col_widths})
    
# Lobby Window.
class Lobby_Win(gui.Window):
    
    # Children.
    class Title_Banner(gui.Text):
        text = "Solex"
        font = TITLE_FONT
        place = {'anchor':"c",'bottom':300}

    class Splash_Image(gui.Image):
        path = "gui/data/solex_splash.jpg"
        edge = 100.0
    
    children = [Title_Banner,
                Splash_Image,
                Local_Menu,
                Net_Menu,
                Tools_Menu,
                Settings_Menu,
                Docs_Menu,
                Main_Button_Container]

    



