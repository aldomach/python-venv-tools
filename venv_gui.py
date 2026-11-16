"""Desktop frontend; only Python standard library is needed."""
# Autor: Aldo Machado
import json, os, sys, subprocess, threading, queue
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import venv_manager as core

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('Python Venv Tools 1.2.2'); self.geometry('1050x780'); self.minsize(900,680)
        self.q=queue.Queue(); self.busy=False; self.records={}
        self.vars={k:tk.StringVar() for k in ('project','name','base','python','cache','entry','engine')}
        self.local=tk.BooleanVar(); self.no_cache=tk.BooleanVar()
        self.install_requirements=tk.BooleanVar(value=True); self.upgrade_pip=tk.BooleanVar(value=True)
        outer=ttk.Frame(self,padding=12); outer.pack(fill='both',expand=True)
        ttk.Label(outer,text='Python Venv Tools',font=('TkDefaultFont',18,'bold')).pack(anchor='w')
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
        ttk.Label(form,text='Motor requirements').grid(row=10,column=0,sticky='w'); ttk.Combobox(form,textvariable=self.vars['engine'],values=('pip','uv'),state='readonly').grid(row=10,column=1,sticky='w')
        ttk.Button(form,text='Dependencias / requirements.txt',command=self.dependencies_window).grid(row=10,column=2,sticky='e')
        for actions in [[('Crear / instalar',lambda:self.command('setup')),('Ejecutar',lambda:self.command('run')),('Verificar y ejecutar',lambda:self.command('run', ['--check'])),('Generar lanzador',lambda:self.command('launcher')),('Detectar Python',self.detect)], [('Listar paquetes',lambda:self.pip(['list'])),('Instalar paquete',lambda:self.package('install')),('Actualizar paquete',lambda:self.package('install',True)),('Desinstalar paquete',lambda:self.package('uninstall')),('Verificar paquetes',lambda:self.pip(['check'])),('Exportar lock',self.freeze),('Abrir carpeta venv',self.open_env)]]:
            bar=ttk.Frame(outer); bar.pack(fill='x',pady=3)
            for label,fn in actions: ttk.Button(bar,text=label,command=fn).pack(side='left',padx=2)
        self.log=tk.Text(outer,height=10,wrap='word',state='disabled'); self.log.pack(fill='both',expand=True,pady=6)
        self.status=tk.StringVar(value='Listo'); footer=ttk.Frame(outer); footer.pack(fill='x'); ttk.Label(footer,textvariable=self.status).pack(side='left'); ttk.Label(footer,text='Aldo',foreground='gray').pack(side='right'); self.defaults(Path.cwd()); self.refresh(); self.after(80,self.poll)
    def defaults(self,p,d=None):
        d=d or {}; vals=dict(project=str(p),name=d.get('name',p.name),base=d.get('base',str(core.BASE)),python=d.get('python') or '',cache=d.get('cache_base',str(core.CACHE)),entry='main.py',engine=d.get('engine','pip'))
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
        result=['--engine',self.vars['engine'].get(),'--name',self.vars['name'].get(),'--path',self.vars['base'].get(),'--cache-path',self.vars['cache'].get(),'--local' if self.local.get() else '--external','--no-cache' if self.no_cache.get() else '--cache']
        if self.vars['python'].get():result+=['--python',self.vars['python'].get()]
        return result
    def command(self,mode,extra=None):
        args=self.cli(mode)+self.args()+(extra or [])
        if mode=='setup':
            if not self.install_requirements.get():args.append('--no-requirements')
            if not self.upgrade_pip.get():args.append('--no-upgrade-pip')
        elif mode in ('run','launcher'):args+=['--entry',self.vars['entry'].get()]
        if mode=='run':
            try: subprocess.Popen(args,cwd=self.vars['project'].get()); self.status.set('Aplicación iniciada (consulta la consola si hay errores).')
            except OSError as e:messagebox.showerror('Error',str(e))
        else:self.work(args)
    def cli(self,mode):
        if getattr(sys,'frozen',False):
            return [str(Path(sys.executable).parent/'venv_cli.exe'),mode]
        return [sys.executable,'-I','-B',str(Path(core.__file__).resolve()),mode]
    def dependencies_window(self):
        import re, tempfile, datetime
        project=Path(self.vars['project'].get()).resolve()
        req=project/'requirements.txt'
        if not project.is_dir():
            return messagebox.showerror('Error','Selecciona un proyecto válido.')
        if self.busy:
            return messagebox.showinfo('Ocupado','Hay una operación activa.')
        def read():
            return req.read_bytes() if req.exists() else None
        def decode(data):
            return data.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n') if data is not None else ''
        try:
            original=read()
            initial=decode(original)
        except (OSError,UnicodeError) as e:
            return messagebox.showerror('No se pudo leer el archivo',str(e))
        win=tk.Toplevel(self)
        win.title('Dependencias — '+project.name)
        win.geometry('930x690')
        win.minsize(760,540)
        win.transient(self)
        win.grab_set()
        ttk.Label(win,text=str(req),padding=8).pack(anchor='w')
        tabs=ttk.Notebook(win)
        tabs.pack(fill='both',expand=True,padx=10,pady=4)
        filetab,scantab,envtab=[ttk.Frame(tabs,padding=8) for _ in range(3)]
        tabs.add(filetab,text='1. Archivo requirements.txt')
        tabs.add(scantab,text='2. Escanear código')
        tabs.add(envtab,text='3. Paquetes del entorno')
        ttk.Label(filetab,text='Editar y guardar el archivo no instala paquetes.').pack(anchor='w')
        editor=tk.Text(filetab,undo=True,wrap='none')
        editor.pack(fill='both',expand=True,pady=6)
        editor.insert('1.0',initial)
        editor.edit_modified(False)
        filestatus=tk.StringVar()
        status=tk.StringVar(value='Listo')
        ttk.Label(filetab,textvariable=filestatus).pack(anchor='w')
        ttk.Label(win,textvariable=status,padding=8).pack(anchor='w')
        base_args=self.args()
        busy=False
        buttons=[]
        def content():
            return editor.get('1.0','end-1c')
        def dirty():
            return content()!=decode(original)
        def file_state(event=None):
            if editor.edit_modified():
                editor.edit_modified(False)
            filestatus.set('Cambios sin guardar' if dirty() else 'Archivo guardado' if original is not None else 'Archivo inexistente: pulsa Guardar para crearlo')
        editor.bind('<<Modified>>',file_state)
        file_state()
        def save():
            nonlocal original
            if busy:return False
            tmp=None
            try:
                current=read()
                if current!=original:
                    messagebox.showwarning('Archivo cambiado','El archivo cambió fuera de la aplicación. Recarga antes de guardar. No se escribió nada.',parent=win)
                    return False
                value=content()
                if current is not None and not dirty():
                    return True
                if not value.strip() and not messagebox.askyesno('Archivo vacío','¿Guardar deliberadamente un requirements.txt vacío?',parent=win,default='no'):
                    return False
                if req.is_symlink():
                    raise OSError('No se sobrescriben enlaces simbólicos.')
                if current is not None:
                    backup_dir=core.STATE/'requirements-backups'
                    backup_dir.mkdir(parents=True,exist_ok=True)
                    import hashlib
                    key=hashlib.sha256(str(req).encode()).hexdigest()[:16]
                    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
                    backup=backup_dir/(key+'-'+stamp+'.txt')
                    with backup.open('xb') as f:f.write(current)
                with tempfile.NamedTemporaryFile(mode='wb',dir=project,prefix='.requirements-',delete=False) as f:
                    tmp=Path(f.name)
                    f.write(value.encode('utf-8'))
                    f.flush()
                    os.fsync(f.fileno())
                if read()!=current:
                    raise OSError('El archivo cambió durante el guardado. Recarga antes de continuar.')
                os.replace(tmp,req)
                original=read()
                file_state()
                status.set('Archivo guardado'+(' con respaldo en '+str(backup) if current is not None else ''))
                return True
            except OSError as e:
                messagebox.showerror('No se pudo guardar',str(e),parent=win)
                return False
            finally:
                if tmp is not None:
                    try:tmp.unlink(missing_ok=True)
                    except OSError:pass
        def external():
            if not req.is_file():
                return messagebox.showinfo('Archivo inexistente','Crea el archivo con Guardar antes de abrirlo.',parent=win)
            try:
                os.startfile(str(req)) if core.WINDOWS else subprocess.Popen(['xdg-open',str(req)])
                status.set('Editor externo abierto. Usa Recargar para ver sus cambios.')
            except OSError as e:messagebox.showerror('Error',str(e),parent=win)
        def reload():
            nonlocal original
            if busy:return
            if dirty() and not messagebox.askyesno('Recargar','¿Descartar los cambios sin guardar?',parent=win,default='no'):return
            try:
                data=read()
                value=decode(data)
                original=data
                editor.delete('1.0','end')
                editor.insert('1.0',value)
                file_state()
                status.set('Archivo recargado. No se modificó el disco.')
            except (OSError,UnicodeError) as e:messagebox.showerror('Error',str(e),parent=win)
        def bar(parent,actions):
            row=ttk.Frame(parent)
            row.pack(fill='x',pady=4)
            for label,fn in actions:
                b=ttk.Button(row,text=label,command=fn)
                b.pack(side='left',padx=3)
                buttons.append(b)
        bar(filetab,[('Guardar archivo',save),('Abrir editor externo',external),('Recargar desde disco',reload)])
        ttk.Label(scantab,text='Busca imports sin ejecutar el proyecto. Selecciona sugerencias para incorporarlas al editor; revisa las conjeturas.').pack(anchor='w',wraplength=850)
        def table(parent,columns):
            frame=ttk.Frame(parent)
            frame.pack(fill='both',expand=True,pady=6)
            tree=ttk.Treeview(frame,columns=[x[0] for x in columns],show='headings',selectmode='extended')
            scroll=ttk.Scrollbar(frame,orient='vertical',command=tree.yview)
            tree.configure(yscrollcommand=scroll.set)
            scroll.pack(side='right',fill='y')
            tree.pack(side='left',fill='both',expand=True)
            for key,label,width in columns:
                tree.heading(key,text=label)
                tree.column(key,width=width)
            return tree
        scan_tree=table(scantab,[('package','Paquete sugerido',180),('module','Import',130),('source','Origen',140),('declared','En editor',130)])
        scan_info=tk.StringVar(value='Todavía no se realizó el escaneo.')
        ttk.Label(scantab,textvariable=scan_info,wraplength=850).pack(anchor='w')
        scan_items={}
        def canonical(name):
            return re.sub(r'[-_.]+','-',name).lower()
        def declared():
            names=set()
            for line in content().splitlines():
                match=re.match(r'^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?=[\[<>=!~;@\s#]|$)',line)
                if match:names.add(canonical(match.group(1)))
            return names
        def refresh_scan():
            names=declared()
            for iid,item in scan_items.items():
                scan_tree.set(iid,'declared','Incluido' if canonical(item['package']) in names else 'No declarado')
        def append():
            names=declared()
            new=[]
            for iid in scan_tree.selection():
                item=scan_items[iid]
                key=canonical(item['package'])
                if key not in names:
                    new.append(item['package'])
                    names.add(key)
            if not new:
                return messagebox.showinfo('Sin cambios','Los paquetes seleccionados ya están declarados o no hay selección.',parent=win)
            editor.insert('end',('' if not content() or content().endswith('\n') else '\n')+'\n'.join(new)+'\n')
            file_state()
            refresh_scan()
            tabs.select(filetab)
            status.set('Sugerencias agregadas al editor. Revisa y guarda explícitamente.')
        ttk.Label(envtab,text='Instalar agrega los paquetes faltantes. Actualizar busca versiones permitidas por requirements.txt. Ninguna acción escribe ese archivo.',wraplength=850).pack(anchor='w')
        env_tree=table(envtab,[('req','Requerimiento',330),('version','Versión instalada',160),('state','Estado',180)])
        additional=tk.StringVar(value='')
        ttk.Label(envtab,textvariable=additional,wraplength=850).pack(anchor='w')
        logs=tk.Text(envtab,height=7,wrap='word',state='disabled')
        logs.pack(fill='x',pady=5)
        def log(value):
            logs.configure(state='normal')
            logs.delete('1.0','end')
            logs.insert('1.0',value)
            logs.see('end')
            logs.configure(state='disabled')
        def operation(flag,extra=None):
            nonlocal busy
            if busy:return
            if flag in ('install','upgrade','compare'):
                try:
                    current=read()
                    if current is None:
                        return messagebox.showinfo('Sin requirements.txt','Guarda primero el archivo o genera sugerencias mediante el escaneo.',parent=win)
                    if dirty() or current!=original:
                        return messagebox.showwarning('Cambios pendientes','Guarda o recarga el archivo antes de continuar. No se guardó nada automáticamente.',parent=win)
                except OSError as e:
                    return messagebox.showerror('Error',str(e),parent=win)
            if flag in ('install','upgrade'):
                action='instalar los requerimientos' if flag=='install' else 'actualizar los paquetes respetando los requerimientos'
                if not messagebox.askyesno('Confirmar','¿Deseas '+action+' en el entorno seleccionado?\nNo se modificará requirements.txt.',parent=win,default='no'):return
                if not content().strip():
                    return messagebox.showinfo('Sin requerimientos','El archivo está vacío. No hay paquetes que procesar.',parent=win)
            busy=True
            status.set('Procesando…')
            editor.configure(state='disabled')
            for b in buttons:b.configure(state='disabled')
            q=queue.Queue()
            if flag=='check':
                args=self.cli('requirements')+base_args+['--check-env']
            else:
                args=self.cli('requirements')+base_args+['--'+flag]+(['--json'] if flag in ('scan','compare') else [])+(extra or [])
            def worker():
                try:
                    p=subprocess.run(args,cwd=project,capture_output=True,text=True,encoding='utf-8',errors='replace')
                    q.put((p.returncode,p.stdout,p.stderr))
                except Exception as e:q.put((1,'',str(e)))
            def poll():
                nonlocal busy
                try:rc,out,err=q.get_nowait()
                except queue.Empty:win.after(100,poll);return
                busy=False
                editor.configure(state='normal')
                for b in buttons:b.configure(state='normal')
                status.set('Operación completada' if rc==0 else 'Error de operación (código '+str(rc)+')')
                if rc!=0:
                    log(out+err)
                    messagebox.showerror('Error de operación',(err or out or 'Error desconocido')[-2500:],parent=win)
                    return
                if flag in ('scan','compare'):
                    try:
                        data=json.loads(out.lstrip('\ufeff').strip())
                        if flag=='scan':
                            scan_tree.delete(*scan_tree.get_children())
                            scan_items.clear()
                            sources={'installed':'Instalado','alias':'Alias conocido','guess':'Por verificar'}
                            for item in data['dependencies']:
                                iid=scan_tree.insert('','end',values=(item['package'],item['module'],sources.get(item['source'],item['source']),''))
                                scan_items[iid]=item
                            refresh_scan()
                            missing=sum(canonical(x['package']) not in declared() for x in scan_items.values())
                            scan_info.set(f"{data['files']} archivos analizados · {len(scan_items)} sugerencias · {missing} no declaradas · {len(data['warnings'])} avisos")
                            if data['warnings']:log('\n'.join(data['warnings']))
                        else:
                            env_tree.delete(*env_tree.get_children())
                            for line,version,state in data['requirements']:
                                env_tree.insert('','end',values=(line,version or '—',state))
                            additional.set('Otros paquetes (pueden ser dependencias indirectas): '+', '.join(data['additional']))
                    except (ValueError,KeyError,TypeError) as e:
                        log(out+err)
                        messagebox.showerror('Respuesta inválida','No se pudo interpretar el resultado. Consulta el registro de Entorno.\n'+str(e),parent=win)
                else:
                    log(out+err)
                    if flag in ('install','upgrade'):status.set('Paquetes procesados. Usa Comparar para comprobar versiones.')
            threading.Thread(target=worker,daemon=True).start()
            win.after(100,poll)
        def freeze():
            target=filedialog.asksaveasfilename(parent=win,initialdir=project,initialfile='requirements-lock.txt',defaultextension='.txt')
            if target:
                p=Path(target)
                if p.resolve()==req.resolve() or p.exists():
                    return messagebox.showerror('Error','Elige un archivo nuevo distinto de requirements.txt.',parent=win)
                operation('freeze',['--output',target])
        bar(scantab,[('Escanear proyecto',lambda:operation('scan')),('Agregar seleccionados al editor',append)])
        bar(envtab,[('Comparar versiones',lambda:operation('compare')),('Instalar requerimientos',lambda:operation('install')),('Actualizar paquetes',lambda:operation('upgrade'))])
        bar(envtab,[('Verificar entorno',lambda:operation('check')),('Exportar versiones exactas',freeze)])
        def close():
            if busy:return messagebox.showinfo('Ocupado','Hay una operación activa.',parent=win)
            if dirty() and not messagebox.askyesno('Cerrar','¿Descartar los cambios sin guardar?',parent=win,default='no'):return
            win.destroy()
        win.protocol('WM_DELETE_WINDOW',close)
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
        if target:
            p=Path(target)
            req=Path(self.vars['project'].get())/'requirements.txt'
            if p.resolve()==req.resolve() or p.exists():
                return messagebox.showerror('Error','Elige un archivo nuevo distinto de requirements.txt.')
            self.pip(['freeze'],target)
    def open_env(self):
        try:
            p=self.env_path(); os.startfile(str(p)) if core.WINDOWS else subprocess.Popen(['xdg-open',str(p)])
        except (OSError,ValueError) as e:messagebox.showerror('Error',str(e))
    def detect(self):
        try:self.work(['py','-0p'] if core.WINDOWS and core.shutil.which('py') else core.interpreter(None)+['--version'])
        except Exception as e:messagebox.showerror('Python',str(e))
    def work(self,args,env=None,save=None):
        if self.busy:return messagebox.showinfo('Ocupado','Ya hay una operación activa.')
        self.busy=True; self.status.set('Procesando...'); cwd=self.vars['project'].get(); self.q.put('> '+subprocess.list2cmdline(args)+'\n')
        def worker():
            try:
                p=subprocess.Popen(args,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE if save else subprocess.STDOUT,text=True,errors='replace')
                if save:
                    out,err=p.communicate(); self.q.put(err)
                    if p.returncode==0:
                        with Path(save).open('x',encoding='utf-8') as f:f.write(out)
                        self.q.put('Guardado: '+save+'\n')
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
