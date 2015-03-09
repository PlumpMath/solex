# =================
# Solex - bodies.py
# =================

# System.

# Panda3d.
from panda3d.core import NodePath


class Body:
    
    def __new__(self, recipe):
        if recipe['type'] == "star":
            return Star(recipe)
        elif recipe['type'] == "planet":
            return Planet(recipe)

class Star:
    
    def __init__(self, recipe):
        self.__dict__.update(recipe)

class Planet:
        
    def __init__(self, recipe):
        self.__dict__.update(recipe)


