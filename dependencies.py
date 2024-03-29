import requests
import numpy as np
import pandas as pd
import rasterio as rio
import matplotlib.pyplot as plt
from rasterio.plot import show
from rasterio.transform import from_bounds
from config import directory

def get_lambert(address:str) -> (int,int):
    req = requests.get(f"http://loc.geopunt.be/geolocation/location?q={address}&c=1")
    return (req.json()["LocationResult"][0]["Location"]["X_Lambert72"],
            req.json()["LocationResult"][0]["Location"]["Y_Lambert72"])

class Box:
    def __init__(self, bounds=None, left:int=0, bottom:int=0, right:int=0, top:int=0):
        if bounds is not None: self.left, self.bottom, self.right, self.top = bounds
        else: self.left, self.bottom, self.right, self.top = left, bottom, right, top
        self.width, self.height = self.right -self.left, self.top -self.bottom
        
    def __str__(self):
        return "left:{} bottom:{} right:{} top:{} width:{} height:{}".format(
            self.left, self.bottom, self.right, self.top, self.width, self.height)

    def __repr__(self):
        return "{} {} {} {} {} {}".format(
            str(int(self.left)),  str(int(self.bottom)),
            str(int(self.right)), str(int(self.top)),
            str(int(self.width)), str(int(self.height)))

    def contains_point(self, x:int, y:int) -> bool:
               return self.left <= x < self.right and self.bottom <= y < self.top

    def contains_box(self, other) -> bool:
        return (other.left >= self.left and other.bottom >= self.bottom 
            and other.right <= self.right and other.top <= self.top)
    
    @classmethod
    def around_point(cls, x:int, y:int, size:int):
        return Box(None, x-size/2, y-size/2, x+size/2, y+size/2)

    @classmethod
    def from_string(cls, string:str=""):
        string = string.split(" ")
        return Box(
            None, int(string[0]), int(string[1]), int(string[2]), int(string[3]))    

class GeoTIFF:
    def __init__(self, tif_path:str):
        self.tif_path = tif_path
        with rio.open(directory+tif_path) as tif:
        #with rio.open(tif_path) as tif:
            self.arr = tif.read(1)
            self.box = Box(tif.bounds)
            self.meta = tif.meta

    def load(self): return rio.open(self.tif_path)
    def show(self, cmap:str="cividis"): return show(self.load(), cmap=cmap)

    def save(self, path:str): 
        with rio.open(path, "w", **self.meta) as out:
            out.write(self.arr, indexes=1)
    def png(self, path:str=directory+"/app/static/plot.png"):
        plt.imsave(path, self.arr, format="png")

    def get_neighbour(self, direction:str):
        point = {"left": (self.box.left -10, self.box.top -self.box.height/2),
                 "bottom": (self.box.right -self.box.width/2, self.box.bottom -10),
                 "right": (self.box.right +10, self.box.top -self.box.height/2),
                 "top": (self.box.right -self.box.width/2, self.box.top +10)}
        return GeoTIFF(get_tif_from_point(*point[direction]))

    def crop_location(self, x:float, y:float, width:int=100, height:int=100):
        posx, posy = int(x -self.box.left), int(abs(y -self.box.top))
        slicex = slice(posx -width//2, posx +width//2)
        slicey = slice(posy -height//2, posy +height//2)        
        meta = self.meta
        meta["width"], meta["height"] = width, height
        meta["transform"] = from_bounds(
            self.box.left + slicex.start,
            self.box.top - slicey.stop,
            self.box.left + slicex.stop,
            self.box.top - slicey.start,
            width, height)

        with rio.open("data/crop.tif", "w", **meta) as crop:
            crop.write(self.arr[slicey,slicex], indexes=1)
        return GeoTIFF("/data/crop.tif")
     
    @classmethod
    def get_root_from_point(cls, x:int, y:int) -> str:
        return root[root.BOX.apply(lambda b:Box.from_string(b).contains_point(x,y))].ROOT.values[0]
    
    @classmethod
    def get_sub_from_point(cls, x:int, y:int) -> str:
        df = data_lookup[(data_lookup.ROOT == cls.get_root_from_point(x,y)) & (data_lookup.PATH != "ROOT")]
        return df[df.BOX.apply(lambda b:Box.from_string(b).contains_point(x,y))].PATH.values[0]
    
    @classmethod
    def get_tif_from_point(cls, x:int, y:int, ftype:str="DSM"):
        df = data_lookup[(data_lookup.ROOT == cls.get_root_from_point(x,y)) & (data_lookup.PATH != "ROOT")]
        return GeoTIFF(df[df.BOX.apply(lambda b:Box.from_string(b).contains_point(x,y))][ftype].values[0])
   
    @classmethod
    def get_containing_tif(cls, x:int, y:int, size:int=100, ftype:str="DSM"):
        main = cls.get_tif_from_point(x,y,ftype)
        main_box = main.box
        crop_box = Box.around_point(x,y,size)
        if main_box.contains_box(crop_box): return main

        result = {}
        if crop_box.left < main_box.left: result["left"]  = cls.get_tif_from_point(crop_box.left, y, ftype)
        if crop_box.bottom < main_box.bottom: result["bottom"]  = cls.get_tif_from_point(x, crop_box.bottom, ftype)
        if crop_box.right > main_box.right: result["right"]  = cls.get_tif_from_point(crop_box.right, y, ftype)
        if crop_box.top > main_box.top: result["top"]  = cls.get_tif_from_point(x, crop_box.top, ftype)

        for k, v in result.items():
            return cls.concat_tifs((main, v), k)
    
    @classmethod
    def concat_tifs(cls, tifs:(), key:str):
        meta = tifs[0].meta
        meta["width"] *= 2 if key is "left" or key is "right" else 1
        meta["height"] *= 2 if key is "bottom" or key is "top" else 1
        meta["transform"] = from_bounds(
            tifs[cls.align[key][0]].box.left,
            tifs[cls.align[key][1]].box.bottom,
            tifs[cls.align[key][1]].box.right,
            tifs[cls.align[key][0]].box.top,
            meta["width"], meta["height"])
        arr = np.concatenate((
            np.array(tifs[cls.align[key][0]].arr),
            np.array(tifs[cls.align[key][1]].arr)),
            axis= cls.align[key][2])
        with rio.open("data/temp.tif", "w", **meta) as temp:
            temp.write(arr, indexes=1)
        return GeoTIFF("/data/temp.tif")
    align = {"left": (1,0,1),"bottom": (0,1,0),"right": (0,1,1),"top": (1,0,0)}

data_lookup = pd.read_csv("data_lookup.csv", sep="|")
root = data_lookup[data_lookup.PATH == "ROOT"]
