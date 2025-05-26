import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

class BootAnimationTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('开关机动画制作工具')
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BootAnimationTool()
    window.show()
    sys.exit(app.exec_())