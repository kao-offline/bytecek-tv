#!/usr/bin/env python3
"""Native Home control outside web content; short dark cover during X startup."""
import subprocess
import time
import tkinter as tk


def output(*args):
    try:
        return subprocess.check_output(args, stderr=subprocess.DEVNULL, timeout=1).decode().strip()
    except (OSError, subprocess.SubprocessError):
        return ''

root = tk.Tk()
root.title('Bytecek Home Control')
root.configure(bg='#242424')
root.overrideredirect(True)
root.attributes('-topmost', True)
root.geometry(f'{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0')
logo = tk.PhotoImage(file='/opt/bytecek/boot/b.png')
splash = tk.Label(root, image=logo, bg='#242424')
splash.place(relx=.5, rely=.5, anchor='center')
started = time.monotonic()
last_site = ''
booting = True


def home():
    global last_site
    subprocess.Popen(['/opt/bytecek/home.sh', last_site], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    root.withdraw()


button = tk.Button(root, text='Home  ?  F9', command=home, bg='#303030', fg='white',
                   activebackground='#b82020', activeforeground='white',
                   font=('DejaVu Sans', 13), relief='flat', borderwidth=0, cursor='hand2')


def poll():
    global booting, last_site
    if booting:
        launcher = output('xdotool', 'search', '--onlyvisible', '--name', '^Bytecek Launcher( - .*)?$')
        if launcher or time.monotonic() - started > 20:
            booting = False
            root.withdraw()
            splash.destroy()
            root.geometry(f'160x44+{root.winfo_screenwidth()-184}+24')
            button.pack(fill='both', expand=True)
        root.after(300, poll)
        return
    active = output('xdotool', 'getactivewindow')
    name = output('xdotool', 'getwindowname', active) if active else ''
    if name == 'Bytecek Home Control':
        root.after(750, poll)
        return
    cls = output('xprop', '-id', active, 'WM_CLASS').lower() if active else ''
    if ('chromium' in cls or 'chrome' in cls) and not name.startswith('Bytecek Launcher'):
        last_site = active
        root.deiconify()
        root.lift()
    else:
        root.withdraw()
    root.after(750, poll)


root.after(100, poll)
root.mainloop()
