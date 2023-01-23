from Login import Login
from MainFrame import MainFrame

def main():
    if Login().go():
        MainFrame().go()
    pass

if __name__=='__main__':
    main()