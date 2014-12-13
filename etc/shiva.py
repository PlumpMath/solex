# ===============
# Solex - util.py
# ===============

# Panda3d imports.
from panda3d.core import Filename

# Local imports.
from .settings import _path

# ===================
# Shiva Language defs
# ===================

# Body Qualifiers.
BODY_QUALS = ("hellish", "hot", "warm", "cool", "cold",
              "sub", "super",
              "mercurian", "terran", "neptunian", "jovian",)
              
# Body Property Qualifiers.
TERRAIN_QUALS = ("terrain", "sea")

# System Qualifiers.
SYS_QUALS = ("star", "planet", "moon", "planetoid", "asteroid", "coment")

# Body Templates.
BODY_TEMPLATES = {
    "terran":{
        'far_lod':  [(6,400000), (7,160000), (8,0)],
        'near_lod': [(.05,15,16), (.1,11,12), (.2,7,8), (.4,5,6), (.8,3,4), (1.4,1,2), (4.8,0,2)],
        'tex_lod':  [(0,100,12), (50,250,6), (175,575,3), (400,1200,1)]
    }
}

class Shiva_Compiler:
    
    @classmethod
    def compile_body_recipe(cls, shiva_str):
        return cls.__compile_Body_Recipe(shiva_str)
    @classmethod
    def compile_sys_recipe(cls, shiva_str):
        return cls.__compile_Sys_Recipe(shiva_str)
    

    def __compile_Body_Recipe(shiva_str):
        lines = shiva_str.split("\n")
        recipe = {'terrains':[]}
        current_block = recipe
        _ignore = False
        _prev_indent = 0
        
        for line in lines:
            strip_line = line.strip()
            if not strip_line: continue
            
            # Ignore single line and multi_line comments.
            if strip_line.startswith("/"):
                if strip_line.startswith("/*"):
                    _ignore = True
                continue
            if strip_line.endswith("*/"):
                _ignore = False
            if _ignore:
                continue
            
            # Handle code blocks.
            indent = len(line) - len(line.lstrip())
            tokens = strip_line.split(" ")
            
            # End block.
            if indent < _prev_indent:
                current_block = recipe
                if indent == 0:
                    current_block = None
                
            # New block.
            if tokens[-1].endswith(":"):
                
                # Body definition.
                if tokens[0] in BODY_QUALS:
                    recipe['name'] = tokens[-1][:-1].lower()
                    recipe['zone'] = tokens[0]
                    if len(tokens) == 4:
                        recipe['class'] = "{}_{}".format(tokens[1], tokens[2])
                    else:
                        recipe['class'] = tokens[-2]
                    recipe.update(BODY_TEMPLATES[recipe['class']])
                    
                # Terrain definition.
                elif tokens[0] in TERRAIN_QUALS:
                    current_block = {'name':tokens[-1][:-1].lower()}
                    recipe['terrains'].append(current_block)
                    
            # Body property definitions.
            elif tokens[0].startswith("$"):
                if current_block:
                    property_name = tokens[0][1:]
                    # Convert shiva expressions to python expresions.
                    toks = []
                    for t in tokens[1:]:
                        # Range expression becomes tuple.
                        if "->" in t:
                            t1, t2 = t.split("->")
                            t = "({}, {})".format(t1, t2)
                        toks.append(t.strip())
                    tok_str = " ".join(toks)
                    current_block[property_name] = eval(tok_str)
            
            _prev_indent = indent
        
        return recipe

    def __compile_Sys_Recipe(shiva_str):
        if shiva_str.endswith(".shv"):
            with open(Filename(shiva_str).toOsLongName()) as shiva_file:
                lines = list(shiva_file.readlines())
        else:
            lines = shiva_str.split("\n")
        block_stack = []
        _ignore = False
        _prev_indent = 0
        
        for line in lines:
            strip_line = line.strip()
            if not strip_line: continue
            
            # Ignore single line and multi_line comments.
            if strip_line.startswith("/"):
                if strip_line.startswith("/*"):
                    _ignore = True
                continue
            if strip_line.endswith("*/"):
                _ignore = False
            if _ignore:
                continue
            
            # Handle code blocks.
            indent = len(line) - len(line.lstrip())
            tokens = strip_line.split(" ")
            
            # End block.
            if indent < _prev_indent:
                for tabs in range((_prev_indent-indent) / 4):
                    block_stack.pop(-1)
                                    
            # New block.
            if tokens[-1].endswith(":"):
                lead_token = tokens[0].split("(")[0]
                if lead_token in SYS_QUALS:
                    new_block = {'name':tokens[-1][:-1].lower(), 'sats':[]}
                    if block_stack:
                        block_stack[-1]['sats'].append(new_block)
                    block_stack.append(new_block)
                    
                    if lead_token == "star":
                        star_cls = tokens[0].split("(\"")[1].replace("\")", "")
            
            # Body sys property definitions.
            elif tokens[0].startswith("$"):
                property_name = tokens[0][1:]
                # Convert shiva expressions to python expresions.
                toks = []
                for t in tokens[1:]:
                    # Range expression becomes tuple.
                    if "->" in t:
                        t1, t2 = t.split("->")
                        t = "({}, {})".format(t1, t2)
                    toks.append(t.strip())
                tok_str = " ".join(toks)
                block_stack[-1][property_name] = eval(tok_str)   
        
        recipe = block_stack[0]
        print(recipe)
        return recipe



