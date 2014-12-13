# ========================
# Panda3d - panda3d_gpu.py
# ========================


# Panda3d imports.
from panda3d.core import NodePath, ClockObject, Filename, Texture
from panda3d.core import Shader, ShaderAttrib, PNMImage
from panda3d.core import LVector3i

'''# Local imports.
from etc import _path'''

# Basic Timer object for local script invocation.

class TimeIt:
    
    def __init__(self, msg=""):
        self.__msg = msg
        self.__clock = ClockObject()
    def __enter__(self):
        self.__start_dt = self.__clock.getRealTime()
        return self
    def __exit__(self, *e_info):
        self.__dur = round(self.__clock.getRealTime()-self.__start_dt, 3)
        if self.__msg:
            print()
            print("{}:  {}".format(self.__msg, self.__dur, 3))
            for attr in self.__dict__:
                if attr.startswith("_TimeIt__"): continue
                print("  {}:  {}".format(attr, round(self.__dict__[attr], 3)))
        self.total_time = self.__dur

class GPU_Image:
    
    lib_path = "/e/dev/solex/gpu/gpu_image_lib.glsl"
        
    def __init__(self, ref_img,
                       workgroup_size = LVector3i(32,32,1),
                       img_format = Texture.FRgba8,
                       print_times = False):
        
        self.workgroup_size = workgroup_size
        self.img_format = img_format
        self.x_size = ref_img.getXSize()
        self.y_size = ref_img.getYSize()
        self.z_size = 1
        self.prepare_time = 0
        self.process_time = 0
        self.extract_time = 0
        
        self.__NP = NodePath("gpu")
        self.__gsg = base.win.getGsg()
        self.__ref_tex = self.__get_Texture(ref_img)
        self.__LINES = self.__Setup()
        self.__print_times = print_times
    
    def __enter__(self):
        self.process_time = 0
        self.extract_time = 0
        return self
            
    def __exit__(self, *e_info):
        if self.__print_times:
            total_time = round(self.prepare_time+self.process_time+self.extract_time, 3)
            prep_time = round(self.prepare_time, 3)
            proc_time = round(self.process_time, 3)
            extr_time = round(self.extract_time, 3)
            print()
            print("GPU_Image total time: {}".format(total_time))
            print("  prepare: {}  ({}%)".format(prep_time, round(prep_time/total_time*100),2))
            print("  process: {}  ({}%)".format(proc_time, round(proc_time/total_time*100),2))
            print("  extract: {}  ({}%)".format(extr_time, round(extr_time/total_time*100),2))
            
    
    def __get_Texture(self, ref_img):
        # Convert ref_img into texture.
        with TimeIt() as prep_timer:
            ref_tex = Texture()
            # Ensure ref image has an alpha channel.
            if not ref_img.hasAlpha():
                ref_img.addAlpha()
                ref_img.alphaFill(1.0)
            # Load tex and set format
            ref_tex.load(ref_img)
            ref_tex.setFormat(self.img_format)
        self.prepare_time += round(prep_timer.total_time, 3)
        return ref_tex

    def __Setup(self):
        """Prepares GPU_Image obj to receive python calls to
        the shader library."""
        
        # Open the shader as a file and get lines so we
        # can extract some setup info from it.
        shader_os_path = Filename(self.lib_path).toOsLongName()
        with open(shader_os_path, "r") as shader_file:
            lines = list(shader_file.readlines())
        
        # Extract lib function names.
        for line in lines:
            # Each function within the image_lib is defined within the confines
            # of an "#ifdef/#endif" block; the name we need immediately follows
            # the "#ifdef" keyword. This name gets mapped directly to "self"
            # as an alias for "self.__Call" so that the user can simply call
            # the shader function as though it were a regular method of "self".
            if line.startswith("#ifdef"):
                func_name = line.split(" ")[1].strip()
                
                # Setup callback that redirects to self.__Call each time
                # "self.<func_name> is called, passing along arguments;
                # return the modified image (as a Texture object).
                def call(func_name=func_name, **kwargs):
                    mod_tex = self.__Call(str(func_name), **kwargs)
                    return mod_tex
                
                # Map "func_name" directly to "self".
                self.__dict__[func_name] = call
                
        # Add workgroup size layout declaration.
        wg = self.workgroup_size
        wg_str = "layout (local_size_x={}, local_size_y={}) in;\n"
        wg_line = wg_str.format(wg.x, wg.y)
        lines.insert(8, wg_line)
        return lines

    def __Call(self, func_name, **kwargs):
        """Receive python call and redirect request to relevant
        function in image shader library; return modified image."""
        
        # Copy self.__Lines (need to keep orig for further calls) and
        # add "#define" statement to top to trigger compilation of
        # relevant "#ifdef/def" function block in shader.
        
        lines = list(self.__LINES)
        lines.insert(2, "#define {}".format(func_name))
        
        # Assemble lines into shader str and compile.
        shader_str = "".join(lines)
        self.__NP.setShader(Shader.makeCompute(Shader.SL_GLSL, shader_str))
        
        # Set block size from workgroup size.
        block_x = int(self.x_size/self.workgroup_size.x)
        block_y = int(self.y_size/self.workgroup_size.y)
        block_z = int(self.z_size/self.workgroup_size.z)
        block_size = LVector3i(block_x,block_y,block_z)
        
        # Create mod_tex for GPU.
        with TimeIt() as prep_timer:
            mod_img = PNMImage(self.x_size, self.y_size, 4)
            mod_tex = Texture()
            mod_tex.load(mod_img)
            mod_tex.setMinfilter(Texture.FTLinear)
            mod_tex.setFormat(self.img_format)
        self.prepare_time += prep_timer.total_time
        
        # Pass textures to shader.
        self.__NP.setShaderInput("ref_tex", self.__ref_tex)
        self.__NP.setShaderInput("mod_tex", mod_tex)
        
        # Set any additional required inputs for this function.
        for input_name, input_val in list(kwargs.items()):
            if type(input_val) == PNMImage:
                input_val = self.__get_Texture(input_val)
            self.__NP.setShaderInput(input_name, input_val)
        
        # Call function in shader library.
        shader_attrib = self.__NP.getAttrib(ShaderAttrib)
        with TimeIt() as proc_timer:
            base.graphicsEngine.dispatch_compute(block_size, shader_attrib, self.__gsg)
        self.process_time += proc_timer.total_time
        
        # Extract modified texture from GPU.
        with TimeIt() as extract_timer: 
            base.graphicsEngine.extractTextureData(mod_tex, self.__gsg)
        self.extract_time += extract_timer.total_time
        return mod_tex



