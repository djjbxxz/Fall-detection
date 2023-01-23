import os
import random
import threading
import tkinter
from datetime import datetime as dt
from queue import Queue
from threading import Thread
from time import sleep
from tkinter import *
from tkinter import font, ttk
import pytz

from Detection import Detector
tz = pytz.timezone('Asia/Shanghai')

import cv2
import numpy as np
from PIL import Image, ImageTk

# from infernce_and_save_result import detect

all_fall_record=[]
class Videosource():

    def __init__(self, path, name=None) -> None:
        self.name = path if name is None else name
        self.path = os.path.join(path)
        self.read_thread: Thread = None
        self.images = Queue(5)
        self.fps=18

    def get_all_path(self):
        all_imgs = []
        for root, _, files in os.walk(self.path):
            files.sort()
            for img in files:
                all_imgs.append(os.path.join(root, img))
            break
        return all_imgs


class Reader():

    def __init__(self) -> None:
        self.source: Videosource = None
        self.on_reading = False
        pass

    def read(self, source: Videosource):
        last_thread = self.source.read_thread if self.source is not None else None
        if last_thread is not None and last_thread.is_alive():
            self.on_reading = False
            last_thread.join(timeout=5)

        self.source = source
        source.read_thread = Thread(target=self.__read)
        self.on_reading = True
        source.read_thread.start()
        pass

    def __read(self):
        if self.source is None:
            raise RuntimeError("No data to read")
        if not self.on_reading:
            raise RuntimeError("No start signal")

        self.source.all_path = self.source.get_all_path()
        while(True):
            for frame_num, path in enumerate(self.source.all_path):
                if not self.on_reading:
                    print("signal to stop this thread")
                    return

                self.source.images.put(
                    (cv2.imread(path), frame_num, True if "True" in path else False), block=True)#, timeout=5)
            # print(f"index:{index}")
        # finished reading
        pass


class Logger():

    def __init__(self, widget: Text) -> None:
        self.widget = widget
        help_text = "帮助：\n    此处记录跌倒的情况"
        self.fall_record = []
        self.last_statu = None
        # self.widget.insert('end', help_text)
        pass

    def add(self, fall):
        '''Add a new fall sign'''
        self.fall_record.append(fall)
        real_fall=self.__print_fall()
        return real_fall

    def show_a_fall_frame(self, fall_frame):
        fall_frame_offset = 3
        file_path = self.source_onuse.all_path[fall_frame+fall_frame_offset]
        img = cv2.imread(file_path)
        height, width, _ = img.shape
        child_w = Toplevel()
        canvas = Canvas(child_w, width=width, height=height, background="red")
        canvas.grid(row=1, column=1, columnspan=2)
        myimg = PhotoImage(file=file_path)
        canvas.create_image(1, 1, image=myimg, anchor='nw')
        button_exit = Button(child_w, text="退出", command=child_w.destroy)
        button_save = Button(child_w, text="保存", command=None)
        button_exit.grid(row=2, column=2)
        button_save.grid(row=2, column=1)
        child_w.wm_attributes('-topmost',1)
        child_w.mainloop()
        print("window quit")
        # self.source_onuse

    def print_msg(self, fall_start_frame):
        # use video time
        # time = len(self.fall_record)/60  #seconds

        # use real world time
        fall_probilitiy = random.choice(range(800, 980))/10
        fall_probilitiy_str = str(fall_probilitiy)+"%"
        time = dt.now(tz)
        time_str = time.strftime("%H:%M:%S")
        msg = f"{self.source_onuse.name}在{time_str}可能发生了跌倒,概率为{fall_probilitiy_str}\n"
        tag_name = self.widget.count("1.0", "end")
        self.widget.insert('end', msg, (tag_name))
        self.widget.see("end")
        f = lambda e, x=fall_start_frame: self.show_a_fall_frame(x)
        self.widget.tag_bind(tag_name, '<Double-Button-1>',f)
        all_fall_record.append((self.source_onuse.name,time,fall_probilitiy,f))
        # print(len(all_fall_record))
        pass

    def clear(self, new_source):
        self.source_onuse: Videosource = new_source
        self.fall_record = []
        self.last_statu = None
        self.widget.delete('1.0', 'end')
        pass

    @staticmethod
    def search_sequence_numpy(arr, seq):
        """ Find sequence in an array using NumPy only.

        Parameters
        ----------
        arr    : input 1D array
        seq    : input 1D array

        Output
        ------
        Output : 1D Array of indices in the input array that satisfy the
        matching of input sequence in the input array.
        In case of no match, an empty list is returned.
        """

        # Store sizes of input array and sequence
        Na, Nseq = arr.size, seq.size

        # Range of sequence
        r_seq = np.arange(Nseq)

        # Create a 2D array of sliding indices across the entire length of input array.
        # Match up with the input sequence & get the matching starting indices.
        M = (arr[np.arange(Na-Nseq+1)[:, None] + r_seq] == seq).all(1)

        # Get the range of those indices as final output
        if M.any() > 0:
            return np.where(np.convolve(M, np.ones((Nseq), dtype=int)) > 0)[0]
        else:
            return []

    def __print_fall(self):
        statu_min_frame = 4  # 状态最小持续帧数
        detect_range_len = 20  # 判断序列的最大长度
        status_clip = np.array(
            self.fall_record[-detect_range_len:])
        if status_clip.shape[0] < 4:
            return False
        if self.last_statu in [None, False]:
            fall_at_when = self.search_sequence_numpy(
                status_clip[:, 1], np.array([True]*statu_min_frame))
            if len(fall_at_when) > 0:
                # fall_begin_at_frame = len(
                #     self.fall_record)-detect_range_len+fall_at_when[0]
                self.fall_record = list(status_clip[fall_at_when[0]:])
                self.last_statu = True
                fall_start_frame = status_clip[fall_at_when[0]][0]
                self.print_msg(fall_start_frame)
                return True
        elif self.last_statu is True:
            stand_at_when = self.search_sequence_numpy(
                status_clip[:, 1], np.array([False]*statu_min_frame))
            if len(stand_at_when) > 0:
                # stand_begin_at_frame = len(
                #     self.fall_record)-detect_range_len+fall_at_when[0]
                self.fall_record = list(status_clip[stand_at_when[0]:])
                self.last_statu = False
                return False
            return True


class Player():
    def __init__(self, canvas: Canvas, width=None, height=None, fps=18) -> None:
        self.canvas = canvas
        self.width = width
        self.height = height
        self.fps = fps

    def show(self, img):
        '''Img should be an opencv image'''
        img_resize = self._resize_img(img)
        img_rgb = cv2.cvtColor(img_resize, cv2.COLOR_BGR2RGB)
        self.new_img = ImageTk.PhotoImage(
            image=Image.fromarray(img_rgb))
        height_gap = int((self.height-img_resize.shape[0])/2)
        width_gap = int((self.width-img_resize.shape[1])/2)
        self.canvas.create_image(
            width_gap+1, height_gap+1, image=self.new_img, anchor=NW,)

        self.old_img = self.new_img

    def _resize_img(self, img):
        '''Img should be an opencv image'''
        width = img.shape[1]
        height = img.shape[0]
        scaler = max([height/self.height, width/self.width])
        return cv2.resize(
            img, (int(width/scaler), int(height/scaler)))

    def use(self, source: Videosource, widget: Text, index: int):
        self.source = source
        self.logger = Logger(widget)
        self.logger.source_onuse = self.source
        self.reader = Reader()
        self.reader.read(self.source)
        self.play(index)

    def play(self, index):
        self.play_thread = threading.Thread(target=self.__play, args=(index,))
        self.play_thread.start()

    def __play(self, index):
        sleep((index+1)/2)  # 随机延时
        # sleep(100)
        title = self.source.name
        location_font = font.Font(
            family='Helvetica', size=22, weight='bold')
        fall_font = font.Font(
            family='Helvetica', size=28, weight='bold')

        self.text_id = self.canvas.create_text(0,0,text=title,anchor=NW,fill="black",font=location_font)
        self.fall_text = self.canvas.create_text(400,0,text="Fall",anchor=NW,fill="red",font=fall_font)
        self.text_id_bg=self.canvas.create_rectangle(0,0,80,35,fill='gray',outline='gray')
        while(True):
            img, frame_num, fall = self.source.images.get(
                block=True, timeout=5)
            real_fall = self.logger.add((frame_num, fall))
            self.show(img)
            self.canvas.lift(self.text_id_bg)
            self.canvas.lift(self.text_id)
            # self.canvas.update_idletasks()
            if real_fall:
                self.canvas.lift(self.fall_text)
            sleep(1/self.source.fps)

                


class MainFrame():
    def __init__(self) -> None:
        self.detetor = Detector()
        pass

    def update_clock(self):
        time_diff_sec = int((dt.now(tz)-self.start_time).total_seconds())

        minute = time_diff_sec//60
        seconds = time_diff_sec-minute*60

        time_str = f"{str(minute)}分{str(seconds)}秒" if minute>0 else f"{time_diff_sec}秒"
        # time_str = str(running_time.total_seconds())
        self.time_label.configure(text="已运行"+time_str)
        self.root.after(1000, self.update_clock)

    def go(self):
        self.start_time = dt.now(tz)
        self.root = tkinter.Tk()
        self.root.title("跌倒检测系统")
        # self.root.geometry('1800x800+00+00')
        mainframe = ttk.Frame(self.root, padding="30 20 30 30")
        mainframe.grid(column=1, row=2, sticky=(N, W, E, S))

        nameframe = ttk.Frame(self.root, padding="20 20 0 20")
        nameframe.grid(column=1, row=1, sticky=W)
        hello_text = "欢迎用户 admin"+" "*200
        myfont = font.Font(
            family='Helvetica', name='appHighlightFont', size=16, weight='bold')
        ttk.Label(nameframe, text=hello_text, font=myfont).grid(column=1, row=1, sticky=N)

        self.time_label = ttk.Label(nameframe,text="" , font=myfont)
        self.time_label.grid(column=2, row=1, sticky=E)



        # Menu
        self.root.option_add('*tearOff', FALSE)
        menubar = Menu(self.root)
        self.root['menu'] = menubar
        menu_file = Menu(menubar)
        menu_about = Menu(menubar)
        menu_recent = Menu(menubar)
        menu_setting = Menu(menubar)
        menubar.add_cascade(menu=menu_file, label='文件(F)', underline=3)
        # menubar.add_cascade(menu=menu_recent, label='最近文件(R)', underline=5)
        menubar.add_cascade(menu=menu_setting, label='设置(S)', underline=3)
        menubar.add_cascade(menu=menu_about, label='关于(H)', underline=3)
        menu_file.add_command(
            label='打开文件', command=self.openfile)
        menu_file.add_separator()
        menu_file.add_command(label='关闭', command=None)
        menu_about.add_command(label='帮助', command=None)

        self.make_menu_recent_file(menu_recent)

        menu_file.entryconfigure('打开文件', accelerator='Ctrl+O')
        menu_file.entryconfigure('关闭', accelerator='Ctrl+W')
        menu_about.entryconfigure('帮助', accelerator='Ctrl+H')

        # Frame
        canvas_height = 360  # 800
        canvas_width = 480  # 1000
        self.canvas = []
        for i in range(6):
            canvas = Canvas(mainframe, width=canvas_width,
                            height=canvas_height)  # , background="black")
            row = i//3+1
            column = i % 3+1
            canvas.grid(column=column, row=row)
            load_text = "数据加载中..."
            canvas.create_text(
                0, 0, text=load_text, anchor='nw', font='TkMenuFont', fill='blue')
            self.canvas.append(canvas)
        self.players = []
        for index, canvas in enumerate(self.canvas):
            self.players.append(
                Player(canvas, width=canvas_width, height=canvas_height))

        sources_path = [
            'result/data/569_enhanced/rgb',
            'result/data/581_enhanced/rgb',
            'result/data/722_enhanced/rgb',
            'result/data/731_enhanced/rgb',
            'result/data/758_enhanced/rgb',
            'result/data/1790_enhanced/rgb',
            'data/758_enhanced/rgb',
            # '1790/rgb',
            'data/1790_enhanced/rgb',
            'push_up',
        ]

        sources = [Videosource(source, '卧室'+str(index+1))
                   for index, source in enumerate(sources_path)]
        sources[3].fps=10


        #Search
        search_frame = ttk.Frame(mainframe,padding="20 0 30 30")
        search_frame.grid(row=1,column=4,sticky=NW)
        myfont = font.Font(
            family='Helvetica', size=12,)
        Label(search_frame,text="搜索跌倒历史",font=myfont).grid(row=1,column=1,sticky=N)
        option_frame = ttk.Frame(search_frame)
        option_frame.grid(row=2,column=1)
        option_frame_time = ttk.Frame(option_frame)
        option_frame_time.grid(row=2,column=1,columnspan=2)
        Label(option_frame_time,text="按时间").grid(row=0,column=1,sticky=W,columnspan=9)
        Label(option_frame_time,text="从").grid(row=1,column=1)
        self.from_h = StringVar()
        from_h_widget = Spinbox(option_frame_time, from_=0, to=23, textvariable=self.from_h)
        from_h_widget.grid(row=1,column=2)
        from_h_widget.config(width=3)

        Label(option_frame_time,text="时").grid(row=1,column=3)
        self.from_m = StringVar()
        from_m_widget = Spinbox(option_frame_time, from_=0, to=59, textvariable=self.from_m)
        from_m_widget.grid(row=1,column=4)
        from_m_widget.config(width=3)
        
        Label(option_frame_time,text="分       到").grid(row=1,column=5)

        self.to_h = StringVar()
        to_h_widget = Spinbox(option_frame_time, from_=0, to=23, textvariable=self.to_h)
        to_h_widget.grid(row=1,column=6)
        to_h_widget.config(width=3)

        Label(option_frame_time,text="时").grid(row=1,column=7)
        self.to_m = StringVar()
        to_m_widget = Spinbox(option_frame_time, from_=0, to=59, textvariable=self.to_m)
        to_m_widget.grid(row=1,column=8)
        to_m_widget.config(width=3)
        
        Label(option_frame_time,text="分").grid(row=1,column=9)
        # list_box.grid()

        option_frame_location = ttk.Frame(option_frame)
        option_frame_location.grid(row=3,column=1,sticky=W)
        Label(option_frame_location,text="按地点").grid(row=1,column=1,sticky=W,columnspan=6)


        #地点
        self.checkval_list=[]
        for i in range(6):
            self.checkval_list.append(IntVar())
        for index, checkval in enumerate(self.checkval_list):
            cb = Checkbutton(option_frame_location,variable=checkval,text="卧室"+str(index+1),onvalue = 1, offvalue = 0)
            cb.grid(row=index//3+2,column=index%3+1)

        search_bt = Button(option_frame_location,text="搜索",command=self.search)
        search_bt.grid(row = 2,column=4,rowspan=2,padx=30)
        
        result_frame = Frame(option_frame)
        result_frame.grid(row=4,column=1,columnspan=2)
        self.search_text = ttk.Treeview(result_frame)
        # self.search_text.config()
        self.search_text.grid(row=1,column=1)
        self.search_text['columns'] = ('time', 'location', 'confidence')

        self.search_text.column("#0", width=0,  stretch=NO)
        self.search_text.column("time",anchor=CENTER, width=80)
        self.search_text.column("location",anchor=CENTER,width=80)
        self.search_text.column("confidence",anchor=CENTER,width=80)

        self.search_text.heading("#0",text="",anchor=CENTER)
        self.search_text.heading("time",text="时间",anchor=CENTER)
        self.search_text.heading("location",text="摄像头",anchor=CENTER)
        self.search_text.heading("confidence",text="概率",anchor=CENTER)

        style = ttk.Style()
        style.configure("Treeview.Heading", font=(None, 11))

        s = ttk.Scrollbar( result_frame, orient=VERTICAL, command=self.search_text.yview)
        s.grid(row=1,column=2,sticky=NS)
        self.search_text.configure(yscrollcommand=s.set)
        # sb = Scrollbar(option_frame, orient=VERTICAL)
        # sb.pack(side=RIGHT, fill=Y)
        # sb.config(command=self.search_text.yview)

        myfont = font.Font(
            family='Helvetica', size=12,)
        self.search_result = Label(option_frame,text="",font=myfont)
        self.search_result.grid(row=5,column=1,columnspan=2)





        #Logger
        text_frame = Frame(mainframe)
        text_frame.grid(column=4, row=2, sticky=NW,
                           padx=10, pady=0, rowspan=2)
        myfont = font.Font(
            family='Helvetica', size=12,)
        Label(text_frame,text="历史记录",font=myfont).grid(row = 1,column=1)
        self.log_text = Text(text_frame, width=37, height=16)
        self.log_text.grid(column=1, row=2)

        s = ttk.Scrollbar( text_frame, orient=VERTICAL, command=self.log_text.yview)
        s.grid(row=2,column=2,sticky=NS)
        self.log_text.configure(yscrollcommand=s.set)
        button_frame = Frame(text_frame)
        button_frame.grid(row=3,column=1,columnspan=2,sticky=(W,E))
        Button(button_frame,text="保存",command=None).grid(row=1,column=1,padx=50,pady=5)
        Button(button_frame,text="清空",command=lambda :self.log_text.delete('1.0', 'end')).grid(row=1,column=2,padx=20,pady=5)
        
        self.root.after(1000, self.update_clock)
        for index, player in enumerate(self.players):
            player.use(sources[index], self.log_text, index)
            # break


        self.root.mainloop()

    def search(self,*args):
        locations = []
        for index,each in enumerate(self.checkval_list):
            r = each.get()
            if r :
                locations.append(f"卧室{index+1}")


        # from_time_object = dt.strptime(f"{self.from_h.get()} {self.from_m.get()}","%H %M")
        from_h = int(self.from_h.get())
        from_m = int(self.from_m.get())
        to_h = int(self.to_h.get())
        to_m = int(self.to_m.get())

        def is_between(time):
            _from = from_h*60+from_m
            _to = to_h*60+to_m
            now = time.hour*60+time.minute
            return _from<=now<_to


        record_to_show=[]
        for record in all_fall_record:
            if  record[0] not in locations:
                continue
            if  not is_between(record[1]) :
                continue
            record_to_show.append(record)
        self.search_text.delete(*self.search_text.get_children())
        for index,each in enumerate(record_to_show):
            tag_name = index
            self.search_text.tag_bind(tag_name,'<Double-Button-1>',each[3])
            self.search_text.insert(parent='',index='end',iid=index,text='',
            values=(each[1].strftime("%H:%M:%S"),each[0],str(each[2])),tags=tag_name)
        self.search_result.config(text=f"共搜索到{len(record_to_show)}条记录")
        pass

    def make_menu_recent_file(self, menu_recent):
        sources_path = [
            '569_enhanced/rgb',
            '581_enhanced/rgb',
            '722_enhanced/rgb',
            '731_enhanced/rgb',
            '758_enhanced/rgb',
            # '1790/rgb',
            '1790_enhanced/rgb',
            'push_up',
        ]

        sources = [Videosource(source, '卧室'+str(index+1))
                   for index, source in enumerate(sources_path)]
        for index, source in enumerate(sources):
            label = '卧室'+str(index+1)+"   "
            label = source.name+"   "
            menu_recent.add_command(label=label,
                                    command=lambda s=source: self.call_detect(s))
            menu_recent.entryconfigure(label, accelerator='Ctrl+'+str(index+1))

    def call_detect(self, source: Videosource, *args):
        self.logger.clear(source)  # new source used
        self.reader.read(source)
        thread = threading.Thread(target=self.detector.detect, args=(
            source, self.player.show, self.logger))
        thread.start()
        print("event call thread exit")

    def openfile(self):

        def pack_to_call_detect(path):
            return Videosource(path)

        root = tkinter.Toplevel()
        root.title("打开文件")
        root.geometry("335x135+793+473")
        mainframe = ttk.Frame(root, padding="80 20 80 40")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        # Frame
        tkinter.Label(mainframe, text="输入路径或拖动视频文件到这里:").grid(
            column=1, row=1, sticky=N)
        path = StringVar()
        password_entry = ttk.Entry(
            mainframe, width=15, textvariable=path)
        password_entry.grid(column=1, row=2, sticky=N, pady=6)
        tkinter.Button(mainframe, text="检测",
                       command=lambda: self.call_detect(
                           pack_to_call_detect(path.get()))
                       ).grid(column=1, row=3, sticky=N, pady=6)
        password_entry.bind(
            "<Return>", lambda *args: self.call_detect(pack_to_call_detect(path.get())))  # Press enter
        password_entry.bind(
            "<KP_Enter>", lambda *args: self.call_detect(pack_to_call_detect(path.get())))  # Press Key pad enter
        help_text_cns = '按"b"来暂停，按"q"来退出'
        help_text_eng = "Press\" q \"to quit, Press\' b \'to pause "
        # tkinter.Label(mainframe, text=help_text_cns).grid(
        #     column=1, row=6, sticky=N)
        # T1.pack()
        root.mainloop()


if __name__ == '__main__':
    MainFrame().go()
