"""Desktop frontend; only Python standard library is needed."""
# Autor: Aldo Machado
import json, os, sys, subprocess, threading, queue
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import venv_manager as core

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('Python Venv Manager'); self.geometry('1050x780'); self.minsize(900,680)
        self.q=queue.Queue(); self.busy=False; self.records={}
        self.vars={k:tk.StringVar() for k in ('project','name','base','python','cache','entry')}
        self.local=tk.BooleanVar(); self.no_cache=tk.BooleanVar()
        self.install_requirements=tk.BooleanVar(value=True); self.upgrade_pip=tk.BooleanVar(value=True)
        outer=ttk.Frame(self,padding=12); outer.pack(fill='both',expand=True)
        ttk.Label(outer,text='Python Venv Manager',font=('TkDefaultFont',18,'bold')).pack(anchor='w')
        self.tree=ttk.Treeview(outer,columns=('path','env'),show='tree headings',height=6)
        self.tree.heading('#0',text='Proyecto'); self.tree.heading('path',text='Carpeta'); self.tree.heading('env',text='Entorno'); self.tree.column('#0',width=160); self.tree.column('path',width=370); self.tree.column('env',width=350)
        self.tree.pack(fill='x',pady=8); self.tree.bind('<<TreeviewSelect>>',self.select)
        row=ttk.Frame(outer); row.pack(fill='x'); ttk.Button(row,text='Nuevo / abrir proyecto',command=self.browse).pack(side='left'); ttk.Button(row,text='Actualizar lista',command=self.refresh).pack(side='left')
        form=ttk.LabelFrame(outer,text='Configuración',padding=8); form.pack(fill='x',pady=8); form.columnconfigure(1,weight=1)
        for i,(k,label) in enumerate([('project','Carpeta del proyecto'),('name','Nombre'),('base','Base de entornos'),('python','Python (versión o ruta)'),('cache','Base de caché'),('entry','Archivo de entrada')]):
            ttk.Label(form,text=label).grid(row=i,column=0,sticky='w',padx=4,pady=3); ttk.Entry(form,textvariable=self.vars[k]).grid(row=i,column=1,sticky='ew',padx=4)
            if k in ('project','base','cache'): ttk.Button(form,text='…',width=4,command=lambda k=k:self.choose(k)).grid(row=i,column=2)
        ttk.Checkbutton(form,text='Entorno local',variable=self.local).grid(row=6,column=1,sticky='w'); ttk.Checkbutton(form,text='Desactivar bytecode',variable=self.no_cache).grid(row=7,column=1,sticky='w')
        ttk.Checkbutton(form,text='Instalar requirements.txt si existe',variable=self.install_requirements).grid(row=8,column=1,sticky='w')
        ttk.Checkbutton(form,text='Actualizar pip',variable=self.upgrade_pip).grid(row=9,column=1,sticky='w')
        for actions in [[('Crear / instalar',lambda:self.command('setup')),('Ejecutar',lambda:self.command('run')),('Verificar y ejecutar',lambda:self.command('run', ['--check'])),('Generar lanzador',lambda:self.command('launcher')),('Detectar Python',self.detect)], [('Listar paquetes',lambda:self.pip(['list'])),('Instalar paquete',lambda:self.package('install')),('Actualizar paquete',lambda:self.package('install',True)),('Desinstalar paquete',lambda:self.package('uninstall')),('Verificar paquetes',lambda:self.pip(['check'])),('Exportar lock',self.freeze),('Abrir carpeta venv',self.open_env)]]:
            bar=ttk.Frame(outer); bar.pack(fill='x',pady=3)
            for label,fn in actions: ttk.Button(bar,text=label,command=fn).pack(side='left',padx=2)
        self.log=tk.Text(outer,height=10,wrap='word',state='disabled'); self.log.pack(fill='both',expand=True,pady=6)
        self.status=tk.StringVar(value='Listo'); footer=ttk.Frame(outer); footer.pack(fill='x'); ttk.Label(footer,textvariable=self.status).pack(side='left'); ttk.Label(footer,text='Aldo',foreground='gray').pack(side='right'); self.defaults(Path.cwd()); self.refresh(); self.after(80,self.poll)
    def defaults(self,p,d=None):
        d=d or {}; vals=dict(project=str(p),name=d.get('name',p.name),base=d.get('base',str(core.BASE)),python=d.get('python') or '',cache=d.get('cache_base',str(core.CACHE)),entry='main.py')
        for k,v in vals.items():self.vars[k].set(v)
        self.local.set(d.get('local',False)); self.no_cache.set(d.get('no_cache',False))
    def refresh(self):
        self.tree.delete(*self.tree.get_children()); self.records={}
        for f in sorted(core.STATE.glob('*.json')):
            try:
                d=json.loads(f.read_text(encoding='utf-8')); p=Path(d['project']); env=p/('venv' if core.WINDOWS else '.venv') if d['local'] else Path(d['base'])/d['name']/'venv'; i=self.tree.insert('', 'end',text=d['name'],values=(str(p),str(env))); self.records[i]=d
            except (KeyError,ValueError,OSError):continue
    def select(self,event=None):
        items=self.tree.selection()
        if items:
            d=self.records[items[0]]; self.defaults(Path(d['project']),d)
    def browse(self):self.choose('project')
    def choose(self,k):
        p=filedialog.askdirectory(initialdir=self.vars[k].get() or str(Path.home()))
        if p:
            if k=='project':
                import hashlib
                path=Path(p).resolve(); key=os.path.normcase(str(path)); f=core.STATE/(hashlib.sha256(key.encode()).hexdigest()[:24]+'.json'); d=json.loads(f.read_text(encoding='utf-8')) if f.exists() else {}; self.defaults(path,d)
            else:self.vars[k].set(p)
    def args(self):
        result=['--name',self.vars['name'].get(),'--path',self.vars['base'].get(),'--cache-path',self.vars['cache'].get(),'--local' if self.local.get() else '--external','--no-cache' if self.no_cache.get() else '--cache']
        if self.vars['python'].get():result+=['--python',self.vars['python'].get()]
        return result
    def command(self,mode,extra=None):
        args=[sys.executable,'-I','-B',str(Path(core.__file__).resolve()),mode]+self.args()+(extra or [])
        if mode=='setup':
            if not self.install_requirements.get():args.append('--no-requirements')
            if not self.upgrade_pip.get():args.append('--no-upgrade-pip')
        else:args+=['--entry',self.vars['entry'].get()]
        if mode=='run':
            try: subprocess.Popen(args,cwd=self.vars['project'].get()); self.status.set('Aplicación iniciada (consulta la consola si hay errores).')
            except OSError as e:messagebox.showerror('Error',str(e))
        else:self.work(args)
    def env_path(self):
        name=self.vars['name'].get()
        if not name or Path(name).name!=name or name in ('.','..'):raise ValueError('Nombre inválido')
        return Path(self.vars['project'].get())/('venv' if core.WINDOWS else '.venv') if self.local.get() else Path(self.vars['base'].get())/name/'venv'
    def pip(self,args,save=None):
        try:
            v=self.env_path().resolve(); p=v/('Scripts/python.exe' if core.WINDOWS else 'bin/python'); project=Path(self.vars['project'].get()).resolve(); marker=v/'.project-owner.json'
            if not p.is_file() or not marker.is_file() or json.loads(marker.read_text(encoding='utf-8'))['project']!=os.path.normcase(str(project)):raise ValueError('Primero configura este entorno desde Crear / instalar.')
            env=core.environment({'no_cache':True},core.CACHE); env['PIP_CONFIG_FILE']=os.devnull
            code='import sys,site,pip; from pathlib import Path; p=Path(sys.prefix).resolve(); assert p==Path(sys.argv[1]).resolve() and sys.prefix!=sys.base_prefix and not site.ENABLE_USER_SITE and p in Path(pip.__file__).resolve().parents'
            subprocess.run([str(p),'-I','-B','-c',code,str(v)],env=env,check=True,capture_output=True)
            self.work([str(p),'-m','pip','--require-virtualenv','--isolated']+args,env,save)
        except (OSError,ValueError,KeyError,subprocess.CalledProcessError) as e:messagebox.showerror('Error',str(e))
    def package(self,action,upgrade=False):
        p=simpledialog.askstring('Paquete','Nombre o especificación del paquete:')
        if not p:return
        if p.startswith('-') or any(c in p for c in '\n\r'):return messagebox.showerror('Error','Paquete inválido')
        if action=='uninstall' and not messagebox.askyesno('Confirmar','¿Desinstalar '+p+'?'):return
        self.pip([action]+(['--upgrade'] if upgrade else [])+(['-y'] if action=='uninstall' else ['--no-compile'])+['--',p])
    def freeze(self):
        target=filedialog.asksaveasfilename(initialdir=self.vars['project'].get(),initialfile='requirements-lock.txt',defaultextension='.txt')
        if target:self.pip(['freeze'],target)
    def open_env(self):
        try:
            p=self.env_path(); os.startfile(str(p)) if core.WINDOWS else subprocess.Popen(['xdg-open',str(p)])
        except (OSError,ValueError) as e:messagebox.showerror('Error',str(e))
    def detect(self): self.work(['py','-0p'] if core.WINDOWS else [sys.executable,'--version'])
    def work(self,args,env=None,save=None):
        if self.busy:return messagebox.showinfo('Ocupado','Ya hay una operación activa.')
        self.busy=True; self.status.set('Procesando...'); cwd=self.vars['project'].get(); self.q.put('> '+subprocess.list2cmdline(args)+'\n')
        def worker():
            try:
                p=subprocess.Popen(args,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE if save else subprocess.STDOUT,text=True,errors='replace')
                if save:
                    out,err=p.communicate(); self.q.put(err)
                    if p.returncode==0:Path(save).write_text(out,encoding='utf-8'); self.q.put('Guardado: '+save+'\n')
                else:
                    for line in p.stdout:self.q.put(line)
                    p.wait()
                self.q.put(('done',p.returncode))
            except Exception as e:self.q.put(str(e)+'\n'); self.q.put(('done',1))
        threading.Thread(target=worker,daemon=True).start()
    def poll(self):
        while True:
            try:item=self.q.get_nowait()
            except queue.Empty:break
            if isinstance(item,tuple):self.busy=False; self.status.set('Finalizado (código '+str(item[1])+')'); self.refresh()
            else:self.log.configure(state='normal'); self.log.insert('end',item); self.log.see('end'); self.log.configure(state='disabled')
        self.after(80,self.poll)

if __name__=='__main__':App().mainloop()
