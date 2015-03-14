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
              "mercurian", "terran", "neptunian", "jovian", "asteroid")
              
# Body Property Qualifiers.
TERRAIN_QUALS = ("terrain", "sea")

# System Qualifiers.
SYS_QUALS = ("star", "planet", "moon", "planetoid", "asteroid", "comet")



# Star class dict.
STAR_SPECS_DICT = {
    'G2V':{ 'radius':696342,    'mass':1.9891*10**30,   'colour':(1,.961,.925,1)},
}

# Body Templates.
_default = {
    'preview_rec': 6,
    'preview_mode': "simple",
    'far_lod':  [(6,400000), (7,160000), (8,0)],
    'near_lod': [(.04,15,16), (.08,11,12), (.16,7,8), (.32,5,6), (.64,3,4), (1.28,1,2), (2.56,0,2)],
    'tex_lod':  [(0,100,12), (50,250,6), (175,575,3), (400,1200,1)],
    'tess_lod': [(.25,1), (.5,2), (1,4), (2,8)]
}

BODY_TEMPLATES = {
    'sub_mercurian':_default,
    'mercurian':_default,
    'super_mercurian':_default,
    'sub_terran':_default,
    'terran':_default,
    'super_terran':_default,
    'sub_neptunian':_default,
    'neptunian':_default,
    'super_neptunian':_default,
    'sub_jovian':_default,
    'jovian':_default,
    'super_jovian':_default,
    'asteroid':_default 
}

# Body basic colours.
BODY_COLS = {
    'mercurian':(.4,.4,.4,1),
    'terran':(0,.5,0,1),
    'neptunian':(0,0,.5,1),
    'jovian':(.5,0,0,1),
    'asteroid':(.7,.7,.7,1)
}
class Shiva_Compiler:
    
    @classmethod
    def compile_body_recipe(cls, shiva_str):
        return cls.__compile_Body_Recipe(shiva_str)
    @classmethod
    def compile_sys_recipe(cls, shiva_str):
        return cls.__compile_Sys_Recipe(shiva_str)
    

    def __compile_Body_Recipe(shiva_str):
        if shiva_str.endswith(".shv"):
            with open(Filename(shiva_str).toOsLongName()) as shiva_file:
                lines = list(shiva_file.readlines())
        else:
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
                continue
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
                    recipe['colour'] = BODY_COLS[tokens[-2]]
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
        _totals = {'_stars':0,'_planets':0,'_moons':0,'_total':0}
        
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
                continue
            if _ignore:
                continue
            
            # Handle code blocks.
            indent = len(line) - len(line.lstrip())
            tokens = strip_line.split(" ")
            
            # End block.
            if indent < _prev_indent:
                for tabs in range(int((_prev_indent-indent) / 4)):
                    block_stack.pop(-1)
                                    
            # New block.
            if tokens[-1].endswith(":"):
                if tokens[0] in SYS_QUALS:
                    new_block = {'name':tokens[-1][:-1].lower(),
                                 'body_type':tokens[0],
                                 'sats':[]}
                    
                    # Update the tip's 'sats' with this body and then
                    # append it to the stack (making it the tip).
                    if block_stack:
                        block_stack[-1]['sats'].append(new_block)
                    block_stack.append(new_block)
                    
                    # Star.
                    if tokens[0] == "star":
                        star_name, cls_str = tokens[1].split("(")
                        star_cls = cls_str.replace("):", "")
                        new_block.update(STAR_SPECS_DICT[star_cls])
                        new_block['name'] = star_name.lower()
                        new_block['type'] = "star"
                    elif tokens[0] == "planet" or tokens[0] == "moon":
                        body_name = tokens[1].split("(")[0].replace(":", "")
                        body_path = "{}/{}/{}.shv".format(_path.BODIES, body_name, body_name)
                        body_recipe = Shiva_Compiler.compile_body_recipe(body_path)
                        new_block.update(body_recipe)
                        new_block['type'] = "planet"
                    _totals["_"+tokens[0]+"s"] +=1
                    _totals['_total'] += 1
            
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
            _prev_indent = indent
        
        recipe = block_stack[0]
        recipe.update(_totals)
        return recipe



