"""Main window for the modular PySide6 frontend."""
# Autor: Aldo Machado
import sys
from pathlib import Path
from PySide6.QtCore import Qt,QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLineEdit,QCheckBox,QComboBox,QPushButton,QLabel,QTableWidget,QTableWidgetItem,QAbstractItemView,QTabWidget,QPlainTextEdit,QFileDialog,QMessageBox)
import pvt_storage as storage
import pvt_environment as environment
from pvt_qt_workers import Runner
from pvt_qt_dependencies import DependenciesPage

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Python Venv Tools 1.3.0-alpha.1')
        self.resize(1100,780)
        self.records=[];self.callback=None
        self.runner=Runner(self);self.runner.output.connect(self.output);self.runner.done.connect(self.completed)
        central=QWidget();self.setCentralWidget(central);layout=QVBoxLayout(central)
        self.tabs=QTabWidget();layout.addWidget(self.tabs)
        projects=QWidget();box=QVBoxLayout(projects)
        self.root_label=QLabel();box.addWidget(self.root_label)
        self.search=QLineEdit();self.search.setPlaceholderText('Filtrar proyectos');box.addWidget(self.search)
        self.table=QTableWidget(0,4);self.table.setHorizontalHeaderLabels(['Proyecto','Código fuente','Entorno','Estado'])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True);box.addWidget(self.table)
        self.search.textChanged.connect(self.filter)
        self.table.itemSelectionChanged.connect(self.select)
        self.bar(box,[('Nuevo / abrir',self.browse),('Detectar proyectos',self.refresh),('Migrar anteriores',self.migrate),('Reasociar código',self.reassociate)])
        form=QFormLayout();box.addLayout(form)
        self.fields={}
        for k,label in [('project','Código fuente'),('name','Nombre'),('base','Base de entornos'),('python','Python (versión o ruta)'),('entry','Archivo de entrada'),('cache_base','Caché personalizada')]:
            field=QLineEdit();self.fields[k]=field;form.addRow(label,field)
        self.local=QCheckBox('Entorno local');self.no_cache=QCheckBox('Desactivar bytecode');self.custom=QCheckBox('Usar caché personalizada')
        self.install=QCheckBox('Instalar requirements.txt');self.install.setChecked(True)
        self.upgrade=QCheckBox('Actualizar pip');self.upgrade.setChecked(True)
        self.engine=QComboBox();self.engine.addItems(['pip','uv'])
        form.addRow('Motor',self.engine)
        for c in (self.local,self.no_cache,self.custom,self.install,self.upgrade):form.addRow(c)
        self.bar(box,[('Crear / instalar',lambda:self.run('setup')),('Ejecutar',lambda:self.run('run')),('Verificar y ejecutar',lambda:self.run('run',['--check'])),('Generar lanzador',lambda:self.run('launcher')),('Abrir entorno',self.open_env)])
        self.tabs.addTab(projects,'Proyectos')
        self.dependencies=DependenciesPage(self.launch);self.tabs.addTab(self.dependencies,'Dependencias')
        self.tabs.currentChanged.connect(self.tab_changed)
        manage=QWidget();box=QVBoxLayout(manage)
        self.info=QLabel('Selecciona un proyecto');self.info.setWordWrap(True);box.addWidget(self.info)
        self.bar(box,[('Verificar paquetes',lambda:self.run('requirements',['--check-env'])),('Abrir código',lambda:self.open_path(self.data()['project'])),('Abrir configuración',lambda:self.open_path(storage.config_path(self.data()).parent))])
        self.bar(box,[('Limpiar bytecode seleccionado',self.clear_cache),('Cambiar almacenamiento',self.change_root)])
        box.addStretch();self.tabs.addTab(manage,'Administración')
        self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setMaximumBlockCount(2000);self.log.setMaximumHeight(155);layout.addWidget(self.log)
        self.statusBar().showMessage('Listo');self.statusBar().addPermanentWidget(QLabel('Aldo'))
        self.defaults(Path.cwd());self.refresh()
    def bar(self,layout,items):
        row=QHBoxLayout()
        for label,fn in items:
            b=QPushButton(label);b.clicked.connect(lambda checked=False,fn=fn:self.guard(fn));row.addWidget(b)
        row.addStretch();layout.addLayout(row)
    def guard(self,fn):
        if self.runner.active:return
        try:fn()
        except (OSError,ValueError,KeyError,RuntimeError) as e:self.error(e)
    def error(self,e):QMessageBox.warning(self,'Python Venv Tools',str(e))
    def confirm(self,msg):
        return QMessageBox.question(self,'Confirmar',msg,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes
    def defaults(self,p,d=None):
        d=d or {};p=Path(p).resolve()
        self.current=d
        for k,v in dict(project=str(p),name=d.get('name',p.name),base=d.get('base',str(storage.root()/'projects')),python=d.get('python') or '',entry=d.get('entry','main.py'),cache_base=d.get('cache_base','')).items():self.fields[k].setText(v)
        self.local.setChecked(d.get('local',False));self.no_cache.setChecked(d.get('no_cache',False));self.custom.setChecked(d.get('custom_cache',False));self.engine.setCurrentText(d.get('engine','pip'))
    def data(self):
        d={k:w.text().strip() for k,w in self.fields.items()}
        if not d['project'] or not d['base']:raise ValueError('Selecciona un proyecto y una base')
        d.update(project=storage.key(d['project']),base=str(Path(d['base']).resolve()),local=self.local.isChecked(),no_cache=self.no_cache.isChecked(),custom_cache=self.custom.isChecked(),engine=self.engine.currentText(),python=d['python'] or None)
        if d['custom_cache']:
            if not d['cache_base']:raise ValueError('Indica una ruta para la caché')
            d['cache_base']=str(Path(d['cache_base']).resolve())
        else:d['cache_base']=str(storage.folder(d)/'pycache')
        if self.current and storage.key(self.current['project'])==d['project'] and self.current.get('id'):d['id']=self.current['id']
        return storage.validate(d)
    def refresh(self):
        self.root_label.setText(str(storage.root()))
        try:
            _,warnings=storage.recover()
            self.records=storage.registered()
            for w in warnings:self.output(w+'\n')
        except (OSError,ValueError,KeyError) as e:self.error(e);return
        self.table.blockSignals(True);self.table.setRowCount(0)
        for d in self.records:
            row=self.table.rowCount();self.table.insertRow(row)
            for col,value in enumerate([d['name'],d['project'],str(storage.env_path(d)),environment.state(d)]):self.table.setItem(row,col,QTableWidgetItem(value))
        self.table.blockSignals(False);self.table.resizeColumnsToContents();self.filter()
    def filter(self):
        term=self.search.text().casefold()
        for row,d in enumerate(self.records):self.table.setRowHidden(row,term not in (d['name']+' '+d['project']).casefold())
    def select(self):
        row=self.table.currentRow()
        if 0<=row<len(self.records):
            d=self.records[row]
            if self.dependencies.select(d):self.defaults(d['project'],d);self.info.setText(str(storage.folder(d)))
    def browse(self):
        p=QFileDialog.getExistingDirectory(self,'Carpeta del código fuente')
        if p:
            d=storage.load(p)
            if self.dependencies.select(d or None):self.defaults(p,d)
    def tab_changed(self,index):
        if index==1:
            try:self.dependencies.select(self.data())
            except (ValueError,KeyError,OSError) as e:self.error(e)
    def migrate(self):
        p=QFileDialog.getExistingDirectory(self,'Base antigua de entornos',str(storage.LEGACY_BASE))
        if p and self.confirm('Registrar entornos antiguos en su ubicación actual. No mover ni borrar archivos.'):
            count,errors=storage.migrate_legacy(p);self.output('\n'.join(errors));self.refresh();self.statusBar().showMessage(f'{count} registros recuperados')
    def reassociate(self):
        d=self.data();p=QFileDialog.getExistingDirectory(self,'Nueva carpeta del código fuente')
        if p and self.confirm('¿Reasociar el entorno a esta nueva carpeta?'):
            d=storage.reassociate(d,p);self.defaults(p,d);self.refresh()
    def open_path(self,p):
        if not Path(p).exists():raise ValueError('Ruta inexistente: '+str(p))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))
    def open_env(self):self.open_path(storage.env_path(self.data()))
    def clear_cache(self):
        d=self.data()
        if self.confirm('¿Eliminar únicamente el bytecode administrado de este proyecto?'):storage.clear_cache(d)
    def change_root(self):
        p=QFileDialog.getExistingDirectory(self,'Directorio de datos',str(storage.root()))
        if p and self.confirm('Cambiar ubicación activa sin mover los entornos existentes.'):
            storage.set_root(p);self.refresh()
    def run(self,mode,extra=()):
        d=self.data();extra=list(extra)
        if not Path(d['project']).is_dir():raise ValueError('El código fuente no existe')
        if mode=='setup':
            if not self.install.isChecked():extra+=['--no-requirements']
            if not self.upgrade.isChecked():extra+=['--no-upgrade-pip']
        if mode in ('run','launcher'):extra+=['--entry',d['entry'] or 'main.py']
        self.launch(environment.command(mode,d,extra),d['project'])
    def launch(self,args,cwd,callback=None):
        if self.runner.active:return
        self.callback=callback
        self.log.clear();self.output('> '+str(args)+'\n')
        self.tabs.setEnabled(False);self.statusBar().showMessage('Procesando...')
        self.runner.start(args,cwd)
    def completed(self,code,out):
        self.tabs.setEnabled(True);self.statusBar().showMessage('Finalizado' if code==0 else 'Error: '+str(code))
        cb=self.callback;self.callback=None
        if cb:cb(code,out)
        elif code==0:self.refresh()
        if code:self.error('Operación fallida. Consulta el registro.')
    def output(self,text):
        self.log.moveCursor(self.log.textCursor().MoveOperation.End);self.log.insertPlainText(text)
    def closeEvent(self,event):
        if self.runner.active or (self.dependencies.dirty() and not self.confirm('¿Descartar cambios sin guardar?')):event.ignore()
        else:event.accept()

def main():
    app=QApplication(sys.argv);win=Window();win.show();return app.exec()
