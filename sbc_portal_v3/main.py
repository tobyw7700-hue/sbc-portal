"""
SBC Academic Portal - Main Entry Point
"""
import tkinter as tk
from ui.app import SBCApp

def main():
    root = tk.Tk()
    root.title("SBC Academic Portal")
    root.geometry("1100x720")
    root.minsize(900, 600)
    app = SBCApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
