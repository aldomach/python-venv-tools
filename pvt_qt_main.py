"""Main window for the modular PySide6 frontend."""
# Autor: Aldo Machado
import sys
from pathlib import Path
from PySide6.QtCore import Qt,QUrl,QSettings
from PySide6.QtGui import QDesktopServices,QTextCursor
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLineEdit,QCheckBox,QComboBox,QPushButton,QLabel,QTableWidget,QTableWidgetItem,QAbstractItemView,QTabWidget,QPlainTextEdit,QFileDialog,QMessageBox,QSplitter,QHeaderView,QGridLayout,QGroupBox,QScrollArea,QDialog,QDialogButtonBox,QMenu)
import pvt_storage as storage
import pvt_removal as removal
import pvt_environment as environment
from pvt_qt_workers import Runner
from pvt_qt_dependencies import DependenciesPage

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Venv Tool 1.3.0-alpha.1')
        self.resize(1240,760)
        self.preferences=QSettings('Venv Tool','Preview 1.3')
        self.records=[];self.callback=None
        self.runner=Runner(self);self.runner.output.connect(self.output);self.runner.done.connect(self.completed)
        central=QWidget();self.setCentralWidget(central);layout=QVBoxLayout(central)
        self.vertical=QSplitter(Qt.Orientation.Vertical);layout.addWidget(self.vertical)
        layout.setContentsMargins(6,6,6,6)
        self.tabs=QTabWidget();self.vertical.addWidget(self.tabs)
        projects=QWidget();outer=QVBoxLayout(projects);outer.setContentsMargins(4,4,4,4)
        self.horizontal=QSplitter(Qt.Orientation.Horizontal);outer.addWidget(self.horizontal)
        left=QWidget();box=QVBoxLayout(left);box.setContentsMargins(2,2,4,2);box.setSpacing(5)
        self.horizontal.addWidget(left)
        self.root_label=QLabel();box.addWidget(self.root_label)
        self.search=QLineEdit();self.search.setPlaceholderText('Filtrar proyectos');box.addWidget(self.search)
        self.table=QTableWidget(0,2);self.table.setHorizontalHeaderLabels(['Proyecto','Estado'])
        self.table.verticalHeader().hide();self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
        self.table.setWordWrap(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True);box.addWidget(self.table)
        self.search.textChanged.connect(self.filter)
        self.table.itemSelectionChanged.connect(self.select)
        self.bar(box,[('Nuevo / abrir',self.browse),('Detectar',self.refresh)])
        self.bar(box,[('Migrar anteriores',self.migrate),('Reasociar código',self.reassociate)])
        self.bar(box,[('Eliminar recursos…',self.remove_project)])
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.project_menu)
        scroll=QScrollArea();scroll.setWidgetResizable(True);self.horizontal.addWidget(scroll)
        right=QWidget();scroll.setWidget(right);box=QVBoxLayout(right);box.setContentsMargins(8,4,8,4);box.setSpacing(6)
        group=QGroupBox('Configuración del proyecto');box.addWidget(group)
        form=QFormLayout(group);form.setContentsMargins(8,8,8,8);form.setVerticalSpacing(5)
        self.fields={}
        for k,label in [('project','Código fuente'),('name','Nombre'),('base','Base de entornos'),('python','Python (versión o ruta)'),('entry','Archivo de entrada'),('cache_base','Caché personalizada')]:
            field=QLineEdit();self.fields[k]=field
            if k in ('project','base','cache_base','entry','python'):
                row=QHBoxLayout();row.setSpacing(3);row.addWidget(field)
                choose=QPushButton('…');choose.setFixedWidth(28);choose.clicked.connect(lambda checked=False,k=k:self.guard(lambda:self.pick_field(k)));row.addWidget(choose);form.addRow(label,row)
            else:form.addRow(label,field)
        self.local=QCheckBox('Entorno local');self.no_cache=QCheckBox('Desactivar bytecode');self.custom=QCheckBox('Usar caché personalizada')
        self.install=QCheckBox('Instalar requirements.txt');self.install.setChecked(True)
        self.upgrade=QCheckBox('Actualizar pip');self.upgrade.setChecked(True)
        self.engine=QComboBox();self.engine.addItems(['pip','uv'])
        form.addRow('Motor',self.engine)
        opts=QGridLayout();opts.setSpacing(5)
        for i,c in enumerate((self.local,self.no_cache,self.custom,self.install,self.upgrade)):opts.addWidget(c,i//2,i%2)
        form.addRow(opts)
        self.custom.toggled.connect(self.fields['cache_base'].setEnabled)
        self.bar(box,[('Crear / instalar',lambda:self.run('setup')),('Ejecutar',lambda:self.run('run'))])
        self.bar(box,[('Verificar y ejecutar',lambda:self.run('run',['--check'])),('Generar lanzador',lambda:self.run('launcher'))])
        self.bar(box,[('Abrir entorno',self.open_env),('Abrir código',lambda:self.open_path(self.data()['project']))])
        box.addStretch()
        self.horizontal.setStretchFactor(0,5);self.horizontal.setStretchFactor(1,5);self.horizontal.setSizes([620,600]);self.horizontal.setChildrenCollapsible(False)
        self.tabs.addTab(projects,'Proyectos')
        self.dependencies=DependenciesPage(self.launch);self.tabs.addTab(self.dependencies,'Dependencias')
        self.tabs.currentChanged.connect(self.tab_changed)
        manage=QWidget();box=QVBoxLayout(manage)
        self.info=QLabel('Selecciona un proyecto');self.info.setWordWrap(True);box.addWidget(self.info)
        self.bar(box,[('Verificar paquetes',lambda:self.run('requirements',['--check-env'])),('Abrir código',lambda:self.open_path(self.data()['project'])),('Abrir configuración',lambda:self.open_path(storage.config_path(self.data()).parent))])
        self.bar(box,[('Limpiar bytecode seleccionado',self.clear_cache),('Cambiar almacenamiento',self.change_root)])
        box.addStretch();self.tabs.addTab(manage,'Administración')
        self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setMaximumBlockCount(2000);self.log.setMinimumHeight(0);self.vertical.addWidget(self.log)
        self.vertical.setStretchFactor(0,5);self.vertical.setStretchFactor(1,1);self.vertical.setSizes([640,100]);self.vertical.setCollapsible(0,False)
        for name,obj in [('geometry',self),('horizontal',self.horizontal),('vertical',self.vertical)]:
            value=self.preferences.value(name)
            if value is not None:
                if name=='geometry':obj.restoreGeometry(value)
                else:obj.restoreState(value)
        self.statusBar().showMessage('Listo');self.statusBar().addPermanentWidget(QLabel('Aldo'))
        self.defaults(Path.cwd());self.refresh()
        self.fields['cache_base'].setEnabled(self.custom.isChecked())
    def bar(self,layout,items):
        row=QHBoxLayout()
        for label,fn in items:
            b=QPushButton(label);b.clicked.connect(lambda checked=False,fn=fn:self.guard(fn));row.addWidget(b)
        row.addStretch();layout.addLayout(row)
    def guard(self,fn):
        if self.runner.active:return
        try:fn()
        except (OSError,ValueError,KeyError,RuntimeError) as e:self.error(e)
    def error(self,e):QMessageBox.warning(self,'Venv Tool',str(e))
    def confirm(self,msg):
        return QMessageBox.question(self,'Confirmar',msg,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes
    def defaults(self,p,d=None):
        d=d or {};p=Path(p).resolve()
        self.current=d
        for k,v in dict(project=str(p),name=d.get('name',p.name),base=d.get('base',str(storage.root()/'projects')),python=d.get('python') or '',entry=d.get('entry','main.py'),cache_base=d.get('cache_base','')).items():self.fields[k].setText(v)
        self.local.setChecked(d.get('local',False));self.no_cache.setChecked(d.get('no_cache',False));self.custom.setChecked(d.get('custom_cache',False));self.engine.setCurrentText(d.get('engine','pip'))
    def pick_field(self,k):
        field=self.fields[k]
        if k in ('entry','python'):
            path,_=QFileDialog.getOpenFileName(self,'Seleccionar archivo',self.fields['project'].text())
            if path and k=='entry':
                try:path=str(Path(path).relative_to(Path(self.fields['project'].text())))
                except ValueError:pass
        else:path=QFileDialog.getExistingDirectory(self,'Seleccionar carpeta',field.text() or str(Path.home()))
        if path:
            if k=='project':
                d=storage.load(path)
                if self.dependencies.select(d or None):self.defaults(path,d)
            else:field.setText(path)
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
        selected=self.fields['project'].text()
        self.table.blockSignals(True);self.table.setRowCount(0)
        selected_row=-1
        for d in self.records:
            row=self.table.rowCount();self.table.insertRow(row)
            for col,value in enumerate([d['name'],environment.state(d)]):
                item=QTableWidgetItem(value);item.setToolTip(d['project']+'\n'+str(storage.env_path(d)));self.table.setItem(row,col,item)
            if storage.key(d['project'])==storage.key(selected):selected_row=row
        if selected_row>=0:self.table.selectRow(selected_row)
        self.table.blockSignals(False);self.filter()
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
    def project_menu(self,pos):
        item=self.table.itemAt(pos)
        if item is None or self.runner.active:return
        self.table.selectRow(item.row())
        menu=QMenu(self)
        action=menu.addAction('Eliminar recursos…')
        action.triggered.connect(lambda:self.guard(self.remove_project))
        menu.exec(self.table.viewport().mapToGlobal(pos))
    def remove_project(self):
        row=self.table.currentRow()
        if row<0 or row>=len(self.records) or not self.table.selectedItems():
            raise ValueError('Selecciona un proyecto de la lista')
        d=dict(self.records[row])
        if self.dependencies.dirty():
            raise ValueError('Guarda o descarta los cambios pendientes antes de eliminar recursos')
        dialog=QDialog(self);dialog.setWindowTitle('Eliminar recursos — '+d['name']);dialog.resize(660,420)
        layout=QVBoxLayout(dialog)
        label=QLabel('Código fuente protegido (no se elimina nada de esta carpeta):\n'+d['project']);label.setWordWrap(True);layout.addWidget(label)
        layout.addWidget(QLabel('Selecciona únicamente los recursos que deseas eliminar.'))
        checks={}
        for k,title in removal.LABELS.items():
            c=QCheckBox(title);layout.addWidget(c);checks[k]=c
            if k=='venv' and d['local']:
                c.setEnabled(False);c.setToolTip('Los entornos dentro del código fuente están protegidos')
            if k=='pycache' and d.get('custom_cache'):
                c.setEnabled(False);c.setToolTip('Las rutas personalizadas están protegidas')
        preview=QPlainTextEdit();preview.setReadOnly(True);layout.addWidget(preview)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        ok=buttons.button(QDialogButtonBox.StandardButton.Ok);ok.setText('Eliminar seleccionados')
        layout.addWidget(buttons);buttons.rejected.connect(dialog.reject)
        def choices():return [k for k,c in checks.items() if c.isChecked()]
        def update():
            ok.setEnabled(False)
            if not choices():preview.setPlainText('No hay recursos seleccionados.');return
            try:
                paths=removal.plan(d,choices())
                preview.setPlainText('\n'.join(str(p) for _,p in paths) or 'No existen los recursos seleccionados.')
                ok.setEnabled(bool(paths))
            except (OSError,ValueError,KeyError,TypeError) as e:preview.setPlainText(str(e))
        def execute():
            try:
                paths=removal.plan(d,choices())
                if not paths:return
                if not self.confirm('Cierra cualquier proceso que esté utilizando este entorno.\n¿Eliminar definitivamente los recursos listados?\nEl código fuente no se toca.'):return
                removed=removal.remove(d,choices(),paths)
                dialog.accept()
                self.refresh()
                self.output('\nRecursos eliminados:\n'+'\n'.join(removed)+'\n')
                self.statusBar().showMessage('Recursos eliminados')
            except (OSError,ValueError,KeyError,RuntimeError,TypeError) as e:
                self.error(e);update();self.refresh()
        for c in checks.values():c.toggled.connect(update)
        buttons.accepted.connect(execute);update();dialog.exec()
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
        self.log.moveCursor(QTextCursor.MoveOperation.End);self.log.insertPlainText(text)
    def closeEvent(self,event):
        if self.runner.active or (self.dependencies.dirty() and not self.confirm('¿Descartar cambios sin guardar?')):event.ignore()
        else:
            self.preferences.setValue('geometry',self.saveGeometry())
            self.preferences.setValue('horizontal',self.horizontal.saveState())
            self.preferences.setValue('vertical',self.vertical.saveState())
            event.accept()

def main():
    app=QApplication(sys.argv);win=Window();win.show();return app.exec()
