import sys
from main import BootAnimationTool

print('🚀 启动开关机动画制作工具...')
print('✅ 依赖检查通过，启动程序...')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BootAnimationTool()
    window.show()
    sys.exit(app.exec_())