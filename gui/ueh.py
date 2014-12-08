# -------------------
# User Events Handler
# -------------------

# Panda3d imports.
from direct.showbase.DirectObject import DirectObject
### from panda3d.core import ClockObject, Vec3D


# Base UEH.
class _User_Events_Handler_(DirectObject):
    
    class user_events:
        key_events = []
        mouse_events = []
        held_events = []
        mouse_pos = (0,0)
        mouse_coords = (0,0)
        x_diff = 0
        y_diff = 0
        
        def get_cmds(self, obj):
            cmds = []
            # Walk through obj's cmd_map and collect qualifying cmds.
            for cmd, evt in obj.cmd_map.items():
                # Test each evt_part by itself (if compound evt).
                for evt_part in evt.split("-"):
                    # Test for "held" events.
                    if evt_part.startswith("_"):
                        if evt_part not in self.held_events:
                            break
                    # Test for normal down/up evts.
                    elif evt_part not in self.key_events+self.mouse_events:
                        break                    
                else:
                    # Only trigger cmd if all evt_parts are in relevant lists.
                    cmds.append(cmd)                    
            return cmds
    
    def receive_event(self, evt):
        # Only use last evt_part since mod keys will be separate evts by themselves.
        evt = evt.split("-")[-1]
        if "mouse" in evt: self.mouse_events.append(evt)
        else: self.key_events.append(evt)
        # Place evt in held_keys.
        held_evt = "_{}".format(evt)
        if held_evt not in self.ue.held_events:
            self.ue.held_events.append(held_evt)
        # Trigger generic "shift" evt missing from Panda events.
        if evt == "lshift" or evt == "rshift":
            self.receive_event("shift")
    def receive_up_event(self, evt):
        if "mouse" in evt: self.mouse_events.append("{}-up".format(evt))
        else: self.key_events.append("{}-up".format(evt))
        # Remove evt from held_keys.
        held_evt = "_{}".format(evt)
        for h_evt in self.ue.held_events:
            if held_evt == h_evt:
                self.ue.held_events.remove(held_evt)
        # Trigger generic "shift" evt missing from Panda events.
        if evt == "lshift" or evt == "rshift":
            self.receive_up_event("shift")
        
    def __init__(self):
        self.size = (base.win.getXSize(), base.win.getYSize())
        self.key_events = []
        self.mouse_events = []
        self._prev_mouse_x = 0
        self._prev_mouse_y = 0
        self.ue = self.user_events()
        self.__setup_Event_Map()

    def _get_events_(self):
        self.ue.key_events = self.key_events
        self.ue.mouse_events = self.mouse_events
        if base.mouseWatcherNode.hasMouse():
            w, h = self.size
            mx = base.mouseWatcherNode.getMouseX() * w/2 + w/2
            my = h - base.mouseWatcherNode.getMouseY() * h/2 - h/2
            self.ue.mouse_pos = (mx, my)
            self.ue.x_diff = mx - self._prev_mouse_x
            self.ue.y_diff = my - self._prev_mouse_y
            self._prev_mouse_x = mx
            self._prev_mouse_y = my
        self.key_events = []
        self.mouse_events = []
        return self.ue
    def __setup_Event_Map(self):
        for evt in self.accepted_key_events+self.accepted_mouse_events:
            for m_key in ("", "shift-", "control-", "alt-"):
                if evt in m_key: continue
                self.accept(m_key+evt, self.receive_event, [m_key+evt])
            self.accept(evt+"-up", self.receive_up_event, [evt])
            

# Default UEH.
class Default_UEH(_User_Events_Handler_):
    
    accepted_key_events = [
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
        "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
        "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
        ",", ".", "/", ";", "'", "[", "]", "\"", "-", "=", "`",
        "enter", "space", "tab", "backspace", "insert", "delete", "escape",
        "home", "end", "page_up", "page_down", "caps_lock"
        "shift", "lshift", "rshift", "control", "lcontrol", "rcontrol",
        "alt", "lalt", "ralt", "arrow_left", "arrow_right", "arrow_up", "arrow_down"]
                  
    accepted_mouse_events = [
        "mouse1", "mouse2", "mouse3"]
    
