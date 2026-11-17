"""Dependency editor and scan/comparison views."""
# Autor: Aldo Machado
import json,re,datetime
from pathlib import Path
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QTabWidget,QLabel,QPlainTextEdit,QPushButton,QTableWidget,QTableWidgetItem,QMessageBox,QFileDialog,QAbstractItemView)
import pvt_storage as storage
import pvt_environment as environment

class DependenciesPage(QWidget):
    def __init__(self,launch,parent=None):
        super().__init__(parent)
        self.launch=launch
        self.d=None
        self.original=None
        self.items=[]
        layout=QVBoxLayout(self)
        self.path=QLabel('Selecciona un proyecto')
        layout.addWidget(self.path)
        self.tabs=QTabWidget();layout.addWidget(self.tabs)
        file=QWidget();box=QVBoxLayout(file)
        self.editor=QPlainTextEdit();box.addWidget(self.editor)
        self.status=QLabel();box.addWidget(self.status)
        self.editor.textChanged.connect(self.changed)
        self.buttons(box,[('Guardar archivo',self.save),('Recargar',self.reload)])
        self.tabs.addTab(file,'Archivo requirements.txt')
        scan=QWidget();box=QVBoxLayout(scan)
        self.scan_table=self.table(['Paquete','Import','Origen','En el editor'])
        box.addWidget(self.scan_table)
        self.buttons(box,[('Escanear código',lambda:self.run('scan')),('Agregar seleccionados al editor',self.add_selected)])
        self.tabs.addTab(scan,'Escanear código')
        env=QWidget();box=QVBoxLayout(env)
        self.compare_table=self.table(['Requerimiento','Instalado','Estado'])
        box.addWidget(self.compare_table)
        self.other=QLabel();self.other.setWordWrap(True);box.addWidget(self.other)
        self.buttons(box,[('Comparar',lambda:self.run('compare')),('Instalar requerimientos',lambda:self.run('install')),('Actualizar paquetes',lambda:self.run('upgrade'))])
        self.buttons(box,[('Verificar entorno',lambda:self.run('check-env')),('Exportar versiones exactas',self.freeze)])
        self.tabs.addTab(env,'Entorno')
        self.setEnabled(False)
    def buttons(self,layout,items):
        row=QHBoxLayout()
        for label,fn in items:
            b=QPushButton(label);b.clicked.connect(fn);row.addWidget(b)
        row.addStretch();layout.addLayout(row)
    def table(self,headers):
        t=QTableWidget(0,len(headers));t.setHorizontalHeaderLabels(headers)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.horizontalHeader().setStretchLastSection(True)
        return t
    def fill(self,t,rows):
        t.setRowCount(0)
        for row in rows:
            i=t.rowCount();t.insertRow(i)
            for j,v in enumerate(row):t.setItem(i,j,QTableWidgetItem(str(v)))
        t.resizeColumnsToContents()
    def req(self):
        return Path(self.d['project'])/'requirements.txt'
    def read(self):
        return self.req().read_bytes() if self.req().exists() else None
    def decoded(self):
        return self.original.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n') if self.original is not None else ''
    def dirty(self):
        return self.d is not None and self.editor.toPlainText()!=self.decoded()
    def confirm(self,msg):
        return QMessageBox.question(self,'Confirmar',msg,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes
    def error(self,e):
        QMessageBox.warning(self,'Dependencias',str(e))
    def select(self,d):
        if self.d and d and storage.key(self.d['project'])==storage.key(d['project']):
            self.d=d;return True
        if self.dirty() and not self.confirm('¿Descartar cambios sin guardar?'):return False
        self.d=d;self.original=None;self.editor.clear();self.items=[]
        self.fill(self.scan_table,[]);self.fill(self.compare_table,[]);self.other.clear()
        self.setEnabled(d is not None)
        if d:
            self.path.setText(str(self.req()))
            self.reload(force=True)
        else:self.path.setText('Selecciona un proyecto')
        return True
    def changed(self):
        self.status.setText('Cambios sin guardar' if self.dirty() else 'Archivo guardado' if self.original is not None else 'Archivo inexistente')
    def reload(self,force=False):
        if not self.d:return
        if not force and self.dirty() and not self.confirm('¿Descartar cambios del editor?'):return
        try:
            data=self.read()
            if data is not None:data.decode('utf-8-sig')
            self.original=data;self.editor.setPlainText(self.decoded());self.changed()
        except (OSError,UnicodeError) as e:self.error(e)
    def save(self):
        if not self.d:return
        import tempfile,os
        tmp=None
        try:
            current=self.read()
            if current!=self.original:raise ValueError('El archivo cambió fuera del editor. Recarga primero.')
            if current is not None and not self.dirty():return
            value=self.editor.toPlainText()
            if not value.strip() and not self.confirm('¿Guardar un archivo vacío?'):return
            req=self.req()
            if req.is_symlink():raise ValueError('No se sobrescriben enlaces simbólicos')
            if current is not None:
                backup=storage.config_path(self.d).parent/'backups'
                backup.mkdir(parents=True,exist_ok=True)
                with (backup/(datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.txt')).open('xb') as f:f.write(current)
            with tempfile.NamedTemporaryFile('wb',dir=req.parent,delete=False) as f:
                tmp=Path(f.name);f.write(value.encode('utf-8'));f.flush();os.fsync(f.fileno())
            if self.read()!=current:raise ValueError('El archivo cambió durante el guardado')
            os.replace(tmp,req);self.original=self.read();self.changed()
        except (OSError,ValueError) as e:self.error(e)
        finally:
            if tmp and tmp.exists():tmp.unlink()
    def names(self):
        return {re.sub(r'[-_.]+','-',m.group(1)).lower() for line in self.editor.toPlainText().splitlines() if (m:=re.match(r'^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?=[\[<>=!~;@\s#]|$)',line))}
    def add_selected(self):
        names=self.names();new=[]
        for row in sorted({x.row() for x in self.scan_table.selectedIndexes()}):
            p=self.items[row]['package'];k=re.sub(r'[-_.]+','-',p).lower()
            if k not in names:new.append(p);names.add(k)
        if new:
            old=self.editor.toPlainText();self.editor.setPlainText(old+('\n' if old and not old.endswith('\n') else '')+'\n'.join(new)+'\n');self.tabs.setCurrentIndex(0)
    def run(self,flag,extra=()):
        try:
            if flag in ('install','upgrade','compare'):
                if self.read() is None:raise ValueError('Guarda requirements.txt primero')
                if self.dirty() or self.read()!=self.original:raise ValueError('Guarda o recarga explícitamente antes de continuar')
            if flag in ('install','upgrade'):
                if not self.decoded().strip():raise ValueError('El archivo está vacío')
                if not self.confirm('¿Modificar los paquetes del entorno? No se escribirá requirements.txt.'):return
            args=['--'+flag]+(['--json'] if flag in ('scan','compare') else [])+list(extra)
            self.launch(environment.command('requirements',self.d,args),self.d['project'],lambda rc,out:self.result(flag,rc,out))
        except (OSError,ValueError) as e:self.error(e)
    def result(self,flag,rc,out):
        if rc:return
        try:
            if flag=='scan':
                data=json.loads(out);self.items=data['dependencies'];names=self.names()
                self.fill(self.scan_table,[(x['package'],x['module'],{'installed':'Instalado','alias':'Alias','guess':'Por verificar'}.get(x['source'],x['source']),'Incluido' if re.sub(r'[-_.]+','-',x['package']).lower() in names else 'No declarado') for x in self.items])
            elif flag=='compare':
                data=json.loads(out);self.fill(self.compare_table,data['requirements']);self.other.setText('Adicionales: '+', '.join(data['additional']))
        except (ValueError,KeyError) as e:self.error(e)
    def freeze(self):
        path,_=QFileDialog.getSaveFileName(self,'Exportar versiones exactas',str(Path(self.d['project'])/'requirements-lock.txt'),'Text (*.txt)')
        if path:
            if Path(path).exists() or Path(path).resolve()==self.req().resolve():return self.error('Elige un archivo nuevo')
            self.run('freeze',['--output',path])
