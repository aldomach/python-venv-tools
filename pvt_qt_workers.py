"""Qt process runner: no blocking package operations on the GUI thread."""
# Autor: Aldo Machado
from PySide6.QtCore import QObject,QProcess,Signal

class Runner(QObject):
    output=Signal(str)
    done=Signal(int,str)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.process=QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        self.process.readyReadStandardOutput.connect(self.stdout)
        self.process.readyReadStandardError.connect(self.stderr)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.error)
        self.buffer=bytearray()
        self.active=False
    def start(self,args,cwd):
        if self.active:return False
        self.buffer.clear()
        self.active=True
        self.process.setWorkingDirectory(str(cwd))
        self.process.start(str(args[0]),[str(x) for x in args[1:]])
        return True
    def stdout(self):
        data=bytes(self.process.readAllStandardOutput())
        self.buffer.extend(data)
        self.output.emit(data.decode('utf-8','replace'))
    def stderr(self):
        self.output.emit(bytes(self.process.readAllStandardError()).decode('utf-8','replace'))
    def finished(self,code,status):
        self.stdout();self.stderr()
        if self.active:
            self.active=False
            self.done.emit(code if status==QProcess.ExitStatus.NormalExit else 1,self.buffer.decode('utf-8','replace'))
    def error(self,error):
        self.output.emit(self.process.errorString())
        if error==QProcess.ProcessError.FailedToStart and self.active:
            self.active=False
            self.done.emit(1,'')
