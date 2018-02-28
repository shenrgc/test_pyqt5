import time
import traceback, sys

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

STYLE = """
QPushButton{
    margin: 15px;
    width: 100px;
    height: 50px;
}
"""

class WorkerSignals(QObject):
    # Signals for Workers
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    progress = pyqtSignal(int)


class Worker(QRunnable):

    def __init__(self, fn, *args, **kwargs):

        super(Worker, self).__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):

        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit()

class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):

        super(MainWindow, self).__init__(*args, **kwargs)

        self.init_UI()

    def init_UI(self):

        # Initialize variables
        self.step = 0
        self.active = False
        self.interrupt = False

        # Layouts
        main_layout = QVBoxLayout()
        sub_layout = QHBoxLayout()

        # Start button
        btn_start = QPushButton('Start')
        btn_start.pressed.connect(self.start_process)
        sub_layout.addWidget(btn_start)
        # Stop button
        btn_stop = QPushButton('Stop')
        btn_stop.pressed.connect(self.stop_process)
        sub_layout.addWidget(btn_stop)

        # Progress bar
        self.pbar = QProgressBar()
        main_layout.addWidget(self.pbar)
        sub_layout.setContentsMargins(0, 30, 0, 0)
        main_layout.addLayout(sub_layout)
        main_layout.setContentsMargins(30, 50, 30, 20)

        # Widget
        w = QWidget()
        w.setLayout(main_layout)

        #Window
        self.setWindowTitle('Progress Bar Thread')
        self.setCentralWidget(w)
        self.setStyleSheet(STYLE)
        self.show()

        # Threads
        self.threadpool = QThreadPool()

    # Signals worker functions
    def execute_thread(self, progress_callback):
        print("Thread started")
        self.active = True
        self.interrupt = False
        while self.step < 20 and not self.interrupt:
            progress_callback.emit(self.step*100/19)
            self.step += 1
            time.sleep(0.25)

    def progress_fn(self, n):
        self.pbar.setValue(n)
        print("%d%% done" % n)

    def thread_complete(self):
        self.active = False
        if not self.interrupt:
            self.step = 0
        print("Thread finished")

    def start_process(self):
        if not self.active:
            # Pass the function to execute
            self.worker = Worker(self.execute_thread)
            self.worker.signals.progress.connect(self.progress_fn)
            self.worker.signals.finished.connect(self.thread_complete)
            # Execute
            self.threadpool.start(self.worker)

    def stop_process(self):
        if self.active:
            self.interrupt = True

if __name__ == '__main__':
    # Main
    app = QApplication([])
    window = MainWindow()
    app.exec_()