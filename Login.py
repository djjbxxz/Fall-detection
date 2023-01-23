from tkinter import *
from tkinter import ttk
from tkinter import messagebox

# highlightFont = font.Font(family='Helvetica', name='appHighlightFont', size=12, weight='bold')


class Login:
    def __init__(self) -> None:
        self.login_success=False

    def go(self):
        self.root = Tk()
        self.root.title("跌倒检测系统")
        self.root.geometry('500x380+710+350')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        mainframe = ttk.Frame(self.root, padding="110 50 110 50")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

        picture_frame = ttk.Frame(mainframe, padding="0 0 0 20")
        picture_frame.grid(column=0, row=0, sticky=N)

        myimg = PhotoImage(file='test.png')
        canvas = Canvas(picture_frame, width=300,
                        height=200)
        canvas.create_image(0, 0, image=myimg, anchor='nw')
        canvas.grid(column=0, row=0, sticky=(N, S))
        # mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

        content_frame = ttk.Frame(mainframe)
        content_frame.grid(column=0, row=1, sticky=N)

        ttk.Label(content_frame, text="用户名").grid(
            column=1, row=1, sticky=E, padx=(0, 10), pady=8)
        ttk.Label(content_frame, text="密   码").grid(
            column=1, row=2, sticky=E, padx=(0, 10), pady=8)
        ttk.Label(content_frame, text="").grid(
            column=1, row=2, sticky=E, padx=(0, 10), pady=4)

        self.username = StringVar()
        self.password = StringVar()
        username_entry = ttk.Entry(
            content_frame, width=15, textvariable=self.username)
        password_entry = ttk.Entry(
            content_frame, width=15, textvariable=self.password, show="*")
        username_entry.grid(column=2, row=1, sticky=W)
        password_entry.grid(column=2, row=2, sticky=W)

        ttk.Button(content_frame, text="登录", command=self.login_callback).grid(
            column=3, row=1, rowspan=2, sticky=W, padx=(20, 0))

        password_entry.bind("<Return>", self.login_callback)  # Press enter
        self.root.mainloop()
        return self.login_success

    def login_callback(self, *args):
        success = self.authenticate(
            str(self.username.get()), str(self.password.get()))
        if success:
            self.login_success = True
            self.root.destroy()
        else:
            messagebox.showerror(title="错误", message="密码错误！")
            self.password.set("")
            pass

    def authenticate(self, usrname, password) -> bool:
        if usrname == 'admin' and password == 'admin':
            return True
        else:
            return False

if __name__=='__main__':

    Login().go()
