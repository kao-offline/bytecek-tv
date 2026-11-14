#!/usr/bin/env python3
"""Desktop launcher button and an unobtrusive fullscreen Home pill."""
import subprocess
import time
import tkinter as tk
import window_state


def output(*args):
    try:
        return subprocess.check_output(args,stderr=subprocess.DEVNULL,timeout=1).decode().strip()
    except (OSError,subprocess.SubprocessError):
        return ''

root=tk.Tk()
root.title('Bytecek Home Control')
root.overrideredirect(True)
root.configure(bg='#242424')
root.attributes('-topmost',True)
root.geometry(f'{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0')
logo=tk.PhotoImage(file='/opt/bytecek/boot/b.png')
small=logo.subsample(3,3)
tk.Label(root,image=logo,bg='#242424').place(relx=.5,rely=.46,anchor='center')
status=tk.Label(root,text='Starting Bytecek TV...',font=('DejaVu Sans',16),bg='#242424',fg='white')
status.place(relx=.5,rely=.64,anchor='center')
started=time.monotonic()
mode='boot'
last_site=''
last_hover=0
last_service=window_state.service_enabled()
scale=max(.85,min(2,root.winfo_screenwidth()/1920))
def px(value):return round(value*scale)


def home():
    subprocess.Popen(['/opt/bytecek/home.sh',last_site],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    root.withdraw()


def show_launcher():
    subprocess.Popen(['/opt/bytecek/show-launcher.sh'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    root.withdraw()


def toggle_service():
    subprocess.Popen(['/usr/bin/python3','/opt/bytecek/service_mode.py','toggle'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    hover()


def set_mode(value,force=False):
    global mode
    if mode==value and not force:
        if value!='hidden':root.deiconify()
        return
    mode=value
    for child in root.winfo_children():child.destroy()
    if value=='hidden':
        root.withdraw()
        return
    root.attributes('-topmost',value!='desktop')
    root.attributes('-alpha',1 if value=='desktop' else .9)
    right=root.winfo_screenwidth()-px(32)
    if value=='desktop':
        root.geometry(f'300x150+{root.winfo_screenwidth()//2-150}+{root.winfo_screenheight()//2-75}')
        tk.Button(root,text='Open Bytecek TV',image=small,compound='top',command=show_launcher,
                  bg='#303030',fg='white',activebackground='#923030',activeforeground='white',
                  font=('DejaVu Sans',18),relief='flat',cursor='hand2').pack(fill='both',expand=True)
    elif value=='pill':
        root.geometry(f'{px(120)}x{px(44)}+{right-px(120)}+{px(32)}')
        pill=tk.Button(root,text='Menu',font=('DejaVu Sans',px(17)),bg='#643131' if not last_service else '#665020',fg='white',activebackground='#923030',activeforeground='white',relief='flat',borderwidth=0,cursor='hand2',command=expand)
        pill.pack(fill='both',expand=True)
        pill.bind('<Enter>',expand)
    elif value=='expanded':
        root.geometry(f'{px(440)}x{px(164)}+{right-px(440)}+{px(32)}')
        button=tk.Button(root,text='Home  |  F9',command=home,bg='#862b2b',fg='white',
                         activebackground='#b82020',activeforeground='white',font=('DejaVu Sans',px(30)),
                         borderwidth=0,relief='flat',cursor='hand2')
        button.pack(fill='both',expand=True)
        service=tk.Button(root,text='Lock to TV  |  F10' if last_service else 'Service mode  |  F10',command=toggle_service,
                          bg='#665020' if last_service else '#303030',fg='white',activebackground='#555555',activeforeground='white',
                          font=('DejaVu Sans',px(21)),borderwidth=0,relief='flat',cursor='hand2')
        service.pack(fill='both',expand=True)
        button.bind('<Motion>',hover)
        service.bind('<Motion>',hover)
    root.deiconify()
    if value!='desktop':root.lift()


def hover(event=None):
    global last_hover
    last_hover=time.monotonic()


def expand(event=None):
    hover()
    set_mode('expanded')


def poll():
    global last_site,last_service
    active=output('xdotool','getactivewindow')
    name=output('xdotool','getwindowname',active) if active else ''
    if mode=='boot':
        if output('xdotool','search','--onlyvisible','--name','^Bytecek Launcher( - .*)?$'):
            set_mode('hidden')
        elif time.monotonic()-started>20:
            status.configure(text='Still starting Bytecek TV... Please leave the power on.')
        root.after(500,poll)
        return
    current_service=window_state.service_enabled()
    if current_service!=last_service:
        last_service=current_service
        set_mode(mode,force=True)
    if name!='Bytecek Home Control':
        cls=output('xprop','-id',active,'WM_CLASS').lower() if active else ''
        if name.startswith('Bytecek Launcher'):
            set_mode('hidden')
        elif 'chrome' in cls or 'chromium' in cls:
            last_site=active
            if mode not in ('pill','expanded'):set_mode('pill')
        else:set_mode('desktop')
    if mode=='expanded' and time.monotonic()-last_hover>1.8:
        x,y=root.winfo_pointerxy()
        if not(root.winfo_rootx()<=x<root.winfo_rootx()+root.winfo_width() and root.winfo_rooty()<=y<root.winfo_rooty()+root.winfo_height()):
            set_mode('pill')
    root.after(500,poll)

root.after(100,poll)
root.mainloop()
