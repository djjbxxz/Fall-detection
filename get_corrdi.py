from tkinter import *
from tkinter import ttk, font
from tkinter import messagebox
import math
import numpy as np

# highlightFont = font.Font(family='Helvetica', name='appHighlightFont', size=12, weight='bold')


class Login:
    def __init__(self) -> None:
        self.GUI()

    def GUI(self):
        self.coor = []
        self.root = Tk()
        self.root.title("跌倒检测系统")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        mainframe = ttk.Frame(self.root, padding="110 50 110 50")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        myimg = PhotoImage(file='result.png').zoom(2)
        self.canvas = Canvas(mainframe, width=320*2,
                             height=240*2, background='gray75')
        id = self.canvas.create_image(0, 0, image=myimg, anchor='nw')
        self.canvas.tag_bind(id, "<Button-1>", self.click_callback)
        self.canvas.tag_bind(id, "<Button-3>", self.clear_coor)
        self.canvas.grid(column=0, row=0, sticky=(N, W, E, S))
        # self.canvas.get
        self.root.mainloop()

    def clear_coor(self, event):
        self.coor = []
        self.canvas.delete('axes')

    def draw_axe(self, point1, point2, color='black'):
        id = self.canvas.create_line(
            point1, point2, arrow='last', fill=color, tags='axes')

    def click_callback(self, click_event):
        # coor order: oringin, x, y, z
        if len(self.coor) < 4:
            self.coor.append((click_event.x, click_event.y))
        if len(self.coor) == 2:  # origin to x
            self.draw_axe(self.coor[0], self.coor[1], 'red')
        elif len(self.coor) == 3:  # origin to y
            self.draw_axe(self.coor[0], self.coor[2], 'green')
        elif len(self.coor) == 4:  # origin to y
            self.draw_axe(self.coor[0], self.coor[3], 'blue')
            print(self.coor)

    def authenticate(self, usrname, password) -> bool:
        return False


class Point_2d:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def distance(self, point) -> float:
        return math.sqrt((self.x-point.x)**2+(self.y-point.y)**2)
    
    def vectorize(self):
        return np.array([self.x,0,self.y,1],dtype=float)


class Point_3d:
    def __init__(self, x: float=0, y: float=0, z: float=0) -> None:
        self.x = x
        self.y = y
        self.z = z

    def distance(self, point) -> float:
        return math.sqrt((self.x-point.x)**2+(self.y-point.y)**2+(self.z-point.z)**2)

    def vectorize(self):
        return np.array([self.x,self.y,self.z,1],dtype=float)


class calculate:
    def __init__(self) -> None:
        pass


    def get_M(self, X, Y):
        '''M = X_T * y'''
        X_inv = np.linalg.inv(X)
        M = np.dot(X_inv, Y)
        return M

    def go(self,points):
        # normalization vectorization
        origin_2d,x_2d,y_2d,z_2d = [Point_2d(*x) for x in points]
        x_3d = Point_3d(x=origin_2d.distance(x_2d)).vectorize()
        y_3d = Point_3d(y=origin_2d.distance(y_2d)).vectorize()
        z_3d = Point_3d(z=origin_2d.distance(z_2d)).vectorize()
        x_2d = x_2d.vectorize()
        y_2d = y_2d.vectorize()
        z_2d = z_2d.vectorize()
        origin_3d = Point_3d(0,0,0).vectorize()

        # get_M

        pass
Login()
# t = [(43, 366), (2, 362), (128, 297), (5, 134)]
# calculate().go(t)
