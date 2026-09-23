# PyQt 地面站完整学习路线

> 目标：用 PyQt5 / PySide6 做无人机地面站
> 学习策略：不系统学完整 Qt，按功能模块学

---

## 第一部分：环境准备

```bash
# Ubuntu 下安装
sudo apt install -y python3-pyqt5 pyqt5-dev-tools
pip3 install pyqtgraph --break-system-packages
```

验证安装：

```python
# python3 -c "from PyQt5.QtWidgets import QApplication; print('OK')"
```

---

## 第二部分：基础框架（这是所有界面的起点）

### 2.1 QApplication — Qt 程序的入口

每个 PyQt 程序必须有且只有一个 QApplication。它在背后处理事件循环（鼠标点击、键盘输入、定时器触发等）。

```python
import sys
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
# ... 创建窗口 ...
sys.exit(app.exec_())   # 进入事件循环，等待用户操作
```

**记忆点：** `app.exec_()` 之前的代码是初始化，之后的代码直到窗口关闭都不会执行。没有这行，窗口一闪就关。

---

### 2.2 QMainWindow — 主窗口框架

地面站的主窗口。它自带菜单栏、状态栏、工具栏，以及一个**中央区域**（centralWidget）用来放你的界面。

```python
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("无人机地面站")
        self.resize(800, 600)

        # central widget 是必须的——所有控件都放在它里面
        central = QWidget()
        self.setCentralWidget(central)

        # 布局装在 central widget 上
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("这里是内容"))

# 在 main 里：
# window = MainWindow()
# window.show()
```

**关键理解：** `setCentralWidget()` 只有一个参数，所以如果你要放多个控件，必须用一个 widget 包起来，里面用布局管理。

---

### 2.3 布局管理器 — 控件怎么排列

不要用绝对坐标（`move(100, 200)`），窗口一拉伸就乱套。用布局管理器自动排列。

| 布局 | 作用 |
|:----|:----|
| **QVBoxLayout** | 垂直排列（从上往下） |
| **QHBoxLayout** | 水平排列（从左往右） |
| **QGridLayout** | 网格排列（像 Excel 表格） |
| **QFormLayout** | 表单排列（标签+输入框成对出现） |

**嵌套用法——你的地面站的典型结构：**

```python
# 最外层：垂直布局
main_layout = QVBoxLayout()

    # 第一行：水平布局（放两个面板）
    top_layout = QHBoxLayout()
        top_layout.addWidget(地图面板)    # 左边
        top_layout.addWidget(数据面板)    # 右边

    # 第二行：另一个水平布局
    bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(控制按钮)
        bottom_layout.addWidget(日志区域)

# 最终效果：
# ┌─────────────┬──────────────┐
# │   地图面板    │   数据面板     │
# ├─────────────┴──────────────┤
# │   [起飞] [降落] [返航]      │
# ├────────────────────────────┤
# │  日志输出区域                │
# └────────────────────────────┘
```

**stretch 参数（非常重要）：**
```python
layout.addWidget(widget1, 1)    # stretch=1
layout.addWidget(widget2, 3)    # stretch=3 → widget2 占 3 倍空间
```
数字越大，控件占据的额外空间比例越大。

---

## 第三部分：核心控件（你的地面站 80% 由这些组成）

### 3.1 QLabel — 显示文字和图片

最常用的控件，地面站里 60% 的内容都是这个。

```python
label = QLabel("显示的文字")

# 对齐方式
label.setAlignment(Qt.AlignCenter)                 # 居中
label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) # 左对齐垂直居中

# 样式（CSS 语法）
label.setStyleSheet("font-size: 16px; color: white; background: #333; padding: 5px;")

# 显示数值（更新内容用 setText）
label.setText(f"高度: {height:.1f} m")

# 显示图片
pixmap = QPixmap("photo.jpg")
label.setPixmap(pixmap)
label.setScaledContents(True)  # 自动缩放填满

# HTML 富文本（QLabel 原生支持）
label.setText("<b>加粗</b> <span style='color:red;'>红色</span> 普通")
```

**地面站里的典型用法：**
```python
# 显示飞控状态
self.status_label = QLabel("状态: 等待连接")
self.status_label.setStyleSheet("color: orange; font-weight: bold;")

# 在定时器里更新
def update_status(self):
    self.status_label.setText(f"状态: {status}")
    if status == "已连接":
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
```

---

### 3.2 QPushButton — 按钮

```python
btn = QPushButton("起飞")
btn.clicked.connect(self.on_takeoff)    # 点击时调用 on_takeoff 函数

# 样式
btn.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        color: white;
        padding: 8px 16px;
        font-size: 14px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #45a049;
    }
    QPushButton:pressed {
        background-color: #3d8b40;
    }
""")

# 禁用/启用
btn.setEnabled(False)  # 灰色不可点
btn.setEnabled(True)   # 恢复正常

# 按钮分组——用 QHBoxLayout 排成一行
# [起飞] [降落] [返航] [紧急停止]
```

**信号与槽（最核心的概念）：**
```python
btn.clicked.connect(函数)       # 点击 → 执行函数
btn.pressed.connect(函数)       # 按下瞬间
btn.released.connect(函数)      # 松开瞬间
```

**lambda 传参：**
```python
for i in range(4):
    btn = QPushButton(f"航点 {i}")
    btn.clicked.connect(lambda checked, x=i: self.goto_waypoint(x))
    # checked 是按钮传来的固定参数，x 是你自己要传的参数
```

---

### 3.3 QLineEdit — 输入框

```python
input_box = QLineEdit()
input_box.setPlaceholderText("请输入目标高度...")   # 灰色提示文字

# 获取内容
text = input_box.text()

# 限制输入类型
input_box.setValidator(QDoubleValidator())          # 只允许输入数字
input_box.setMaxLength(10)                          # 最大字符数

# 回车触发
input_box.returnPressed.connect(self.on_submit)
```

---

### 3.4 QComboBox — 下拉选择框

```python
combo = QComboBox()
combo.addItem("手动模式")
combo.addItem("定高模式")
combo.addItem("悬停模式")
combo.addItem("自动模式")

# 当前选中的
current = combo.currentText()   # "定高模式"
index = combo.currentIndex()    # 1（从 0 开始）

# 选择变化时触发
combo.currentTextChanged.connect(self.on_mode_changed)
```

---

### 3.5 QTextEdit / QPlainTextEdit — 日志/多行文本

```python
# QPlainTextEdit 比 QTextEdit 轻量，适合日志
log_area = QPlainTextEdit()
log_area.setReadOnly(True)          # 只读，用户不能编辑
log_area.setMaximumBlockCount(1000) # 最多保留 1000 行，防止内存溢出

# 追加日志
def log(self, message):
    self.log_area.appendPlainText(f"[{time}] {message}")
    # 自动滚动到底部
    self.log_area.moveCursor(QTextCursor.End)
```

---

### 3.6 QTableWidget — 表格

```python
table = QTableWidget()
table.setColumnCount(3)
table.setHorizontalHeaderLabels(["格子", "动物", "数量"])

# 添加一行数据
row = table.rowCount()
table.insertRow(row)
table.setItem(row, 0, QTableWidgetItem("A3B5"))
table.setItem(row, 1, QTableWidgetItem("🐯 虎"))
table.setItem(row, 2, QTableWidgetItem("1"))

# 清空表格（保留表头）
table.setRowCount(0)
```

---

### 3.7 QGroupBox — 分组框

把相关的控件视觉上框在一起，加上标题。

```python
group = QGroupBox("飞控状态")
layout = QVBoxLayout(group)
layout.addWidget(QLabel("连接状态: 已连接"))
layout.addWidget(QLabel("电池: 11.8V"))
layout.addWidget(QLabel("GPS: 12颗星"))

# 放到主布局里
main_layout.addWidget(group)
```

---

## 第四部分：定时器（地面站的核心机制）

地面站的本质就是**每秒刷新 N 次界面**。QTimer 是实现这个的方式。

```python
from PyQt5.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)  # 每次定时到就调用
        self.timer.start(100)   # 每 100ms 刷新一次（10Hz，跟 FAST-LIO 频率一致）

    def update_ui(self):
        """每秒被调用 10 次，刷新所有数据"""
        # 从 ROS 获取最新数据
        # 更新标签
        # 更新图表
        # 什么都不做也 OK，只是保持界面响应
        pass
```

**为什么用定时器而不是每次 ROS 回调直接更新界面？**
ROS 的回调是在 ROS 线程里执行的，直接更新 Qt 界面可能导致崩溃。标准做法是：

```python
# ROS 回调只做一件事：保存数据
def odom_callback(self, msg):
    self.current_pose = msg.pose.pose

# QTimer 更新 UI 时读取保存的数据
def update_ui(self):
    if self.current_pose:
        x = self.current_pose.position.x
        y = self.current_pose.position.y
        self.pos_label.setText(f"位置: ({x:.2f}, {y:.2f})")
```

---

## 第五部分：多线程（不卡界面的关键）

如果你在 `update_ui` 里执行耗时的操作（比如读写文件、网络请求），界面会卡住。需要把耗时任务放到**子线程**。

### 5.1 QThread + 工作对象（推荐）

```python
from PyQt5.QtCore import QThread, pyqtSignal

class RosWorker(QThread):
    data_updated = pyqtSignal(dict)   # 自定义信号，子线程→主线程传数据

    def run(self):
        """在子线程里运行的代码"""
        import rospy
        rospy.init_node("ground_station", anonymous=True)

        def callback(msg):
            data = {
                "x": msg.pose.pose.position.x,
                "y": msg.pose.pose.position.y,
                "z": msg.pose.pose.position.z,
            }
            self.data_updated.emit(data)   # 发射信号，主线程收到后更新 UI

        rospy.Subscriber("/Odometry", Odometry, callback)
        rospy.spin()

# 在主窗口里：
self.ros_thread = RosWorker()
self.ros_thread.data_updated.connect(self.on_data_updated)
self.ros_thread.start()

def on_data_updated(self, data):
    self.pos_label.setText(f"x={data['x']:.2f}")
```

**为什么这样不会卡界面：** `pyqtSignal` 发射的信号会被 Qt 自动放到主线程的事件队列里处理，所以 `on_data_updated` 是在主线程执行的，可以安全更新 UI。

---

## 第六部分：绘图（显示方格地图、飞机轨迹）

### 6.1 QPainter — 手绘界面

在 QWidget 上重写 `paintEvent` 方法，可以画任何图形。适合画你的 9×7 方格地图。

```python
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt5.QtCore import QRect

class MapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.animal_positions = {}  # {(col, row): "tiger", ...}
        self.forbidden_zones = []   # [(col, row), ...]
        self.drone_pos = (0, 0)     # 飞机当前位置

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 计算每个格子的大小
        cell_w = self.width() // 9
        cell_h = self.height() // 7

        # 画网格
        for col in range(9):
            for row in range(7):
                x, y = col * cell_w, row * cell_h
                rect = QRect(x, y, cell_w, cell_h)

                # 禁飞区 → 灰色
                if (col, row) in self.forbidden_zones:
                    painter.fillRect(rect, QColor(180, 180, 180))

                # 有动物 → 不同颜色
                elif (col, row) in self.animal_positions:
                    painter.fillRect(rect, QColor(200, 255, 200))

                painter.drawRect(rect)  # 画边框

        # 画飞机位置（红色圆点）
        cx = self.drone_pos[0] * cell_w + cell_w // 2
        cy = self.drone_pos[1] * cell_h + cell_h // 2
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.drawEllipse(cx - 5, cy - 5, 10, 10)
```

### 6.2 pyqtgraph — 实时折线图

比 matplotlib 快，适合显示实时数据（位置曲线、高度变化等）。

```python
import pyqtgraph as pg

# 在布局里加入图表
self.plot_widget = pg.PlotWidget()
self.plot_widget.setLabel("left", "高度", units="m")
self.plot_widget.setLabel("bottom", "时间", units="s")
self.plot_widget.setYRange(0, 3)
self.plot_curve = self.plot_widget.plot(pen='g')  # 绿色曲线

# 数据缓冲区
self.height_buffer = []
self.time_buffer = []

def update_plot(self, height, t):
    self.height_buffer.append(height)
    self.time_buffer.append(t)

    # 只保留最近 200 个点
    if len(self.height_buffer) > 200:
        self.height_buffer.pop(0)
        self.time_buffer.pop(0)

    self.plot_curve.setData(self.time_buffer, self.height_buffer)
```

---

## 第七部分：完整的模板——无人机地面站雏形

把上面所有东西合起来：

```python
import sys
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
import pyqtgraph as pg

# ========== 子线程收 ROS 数据（占位） ==========
class DataWorker(QThread):
    data_updated = pyqtSignal(dict)

    def run(self):
        """实际使用时替换为 rospy.Subscriber"""
        import random
        while True:
            data = {
                "x": random.uniform(0, 9),
                "y": random.uniform(0, 7),
                "z": random.uniform(1.0, 1.5),
                "battery": random.uniform(11.0, 12.6),
                "mode": random.choice(["悬停", "巡航", "降落"]),
                "animals": {
                    "虎": random.randint(0, 2),
                    "象": random.randint(0, 1),
                    "狼": random.randint(0, 3),
                }
            }
            self.data_updated.emit(data)
            self.msleep(100)

# ========== 方格地图控件 ==========
class MapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.drone_x = 0
        self.drone_y = 0
        self.animals = {}      # {(col, row): "动物名"}
        self.forbidden = set() # {(col, row)}

    def update_drone(self, x, y):
        self.drone_x = x
        self.drone_y = y
        self.update()  # 触发重绘

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        cols, rows = 9, 7
        cw = self.width() // cols
        ch = self.height() // rows

        for col in range(cols):
            for row in range(rows):
                rect = QtCore.QRect(col * cw, row * ch, cw, ch)

                if (col, row) in self.forbidden:
                    p.fillRect(rect, QColor(180, 180, 180))
                elif (col, row) in self.animals:
                    p.fillRect(rect, QColor(200, 255, 200))

                p.drawRect(rect)

                if (col, row) in self.animals:
                    p.drawText(rect, Qt.AlignCenter, self.animals[(col, row)])

        # 飞机位置
        px = int(self.drone_x * cw + cw // 2)
        py = int(self.drone_y * ch + ch // 2)
        p.setBrush(QBrush(QColor(255, 0, 0)))
        p.drawEllipse(px - 6, py - 6, 12, 12)

# ========== 主窗口 ==========
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("无人机地面站")
        self.resize(1000, 700)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # ---- 左侧：地图 ----
        left_layout = QVBoxLayout()
        self.map_widget = MapWidget()
        left_layout.addWidget(QLabel("巡查地图"))
        left_layout.addWidget(self.map_widget)

        # 高度曲线
        self.plot = pg.PlotWidget()
        self.plot.setLabel("left", "高度", units="m")
        self.plot.setYRange(0, 2)
        self.height_curve = self.plot.plot(pen='g')
        left_layout.addWidget(self.plot)
        main_layout.addLayout(left_layout, 2)

        # ---- 右侧：数据面板 ----
        right_layout = QVBoxLayout()

        # 状态分组
        status_group = QGroupBox("飞控状态")
        sl = QFormLayout(status_group)
        self.status_label = QLabel("等待连接")
        self.battery_label = QLabel("-- V")
        sl.addRow("状态:", self.status_label)
        sl.addRow("电池:", self.battery_label)
        right_layout.addWidget(status_group)

        # 位置分组
        pos_group = QGroupBox("当前位置")
        pl = QFormLayout(pos_group)
        self.x_label = QLabel("--")
        self.y_label = QLabel("--")
        self.z_label = QLabel("--")
        pl.addRow("X:", self.x_label)
        pl.addRow("Y:", self.y_label)
        pl.addRow("Z:", self.z_label)
        right_layout.addWidget(pos_group)

        # 控制按钮
        btn_layout = QHBoxLayout()
        self.takeoff_btn = QPushButton("起飞")
        self.land_btn = QPushButton("降落")
        btn_layout.addWidget(self.takeoff_btn)
        btn_layout.addWidget(self.land_btn)
        right_layout.addLayout(btn_layout)

        # 日志
        right_layout.addWidget(QLabel("系统日志"))
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumBlockCount(500)
        right_layout.addWidget(self.log_area)

        # 动物统计表格
        right_layout.addWidget(QLabel("识别结果"))
        self.animal_table = QTableWidget()
        self.animal_table.setColumnCount(2)
        self.animal_table.setHorizontalHeaderLabels(["动物", "数量"])
        right_layout.addWidget(self.animal_table)

        main_layout.addLayout(right_layout, 1)

        # ---- 数据线程和定时器 ----
        self.height_buffer = []
        self.time_buffer = []

        self.worker = DataWorker()
        self.worker.data_updated.connect(self.on_data)
        self.worker.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(50)

        self.log("地面站已启动")

    def log(self, msg):
        self.log_area.appendPlainText(
            f"[{time.strftime('%H:%M:%S')}] {msg}"
        )

    def on_data(self, data):
        """子线程发过来的数据，保存到成员变量"""
        self.latest = data

    def update_ui(self):
        """定时刷新界面（主线程执行）"""
        if not hasattr(self, 'latest'):
            return

        d = self.latest
        self.x_label.setText(f"{d['x']:.2f}")
        self.y_label.setText(f"{d['y']:.2f}")
        self.z_label.setText(f"{d['z']:.2f}")
        self.battery_label.setText(f"{d['battery']:.2f} V")
        self.status_label.setText(d['mode'])
        self.map_widget.update_drone(d['x'], d['y'])

        # 高度曲线
        t = time.time()
        self.height_buffer.append(d['z'])
        self.time_buffer.append(t)
        if len(self.height_buffer) > 200:
            self.height_buffer.pop(0)
            self.time_buffer.pop(0)
        self.height_curve.setData(self.time_buffer, self.height_buffer)

    def closeEvent(self, event):
        self.worker.quit()
        self.worker.wait()
        event.accept()

# ========== 启动 ==========
if __name__ == "__main__":
    # 让 pyqtgraph 用 Qt5
    import PyQt5.QtCore as QtCore

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
```

---

## 第八部分：pyqtgraph 常用绘图模式

```python
# 1. 折线图（上面已经用了）
curve = plot_widget.plot(x_data, y_data, pen='y', name='高度')

# 2. 多条曲线
curve1 = plot_widget.plot(pen='r', name='X')
curve2 = plot_widget.plot(pen='g', name='Y')
curve3 = plot_widget.plot(pen='b', name='Z')
curve1.setData(times, x_data)

# 3. 散点图
scatter = pg.ScatterPlotItem()
scatter.setData(x_pts, y_pts, brush='r')
plot_widget.addItem(scatter)

# 4. 清除重绘
plot_widget.clear()
plot_widget.plot(data)

# 5. 实时更新的关键：不要重新创建 PlotWidget，只更新数据
#    用 setData 而不是 plot()
```

---

## 第九部分：发布 ROS 指令

```python
import rospy
from geometry_msgs.msg import PoseStamped, TwistStamped
from std_msgs.msg import String

class RosPublisher:
    def __init__(self):
        rospy.init_node("ground_station_cmd")
        self.pub_pose = rospy.Publisher(
            "/uav1/mavros/setpoint_position/local",
            PoseStamped, queue_size=1
        )
        self.pub_vel = rospy.Publisher(
            "/uav1/mavros/setpoint_velocity/cmd_vel",
            TwistStamped, queue_size=1
        )
        self.pub_mode = rospy.Publisher(
            "/uav1/prometheus/control_mode",
            String, queue_size=1
        )

    def goto(self, x, y, z):
        msg = PoseStamped()
        msg.pose.position.x = x
        msg.pose.position.y = y
        msg.pose.position.z = z
        msg.pose.orientation.w = 1
        self.pub_pose.publish(msg)

    def set_mode(self, mode):
        self.pub_mode.publish(String(mode))
```

---

## 第十部分：PyQt 排错速查

| 现象 | 原因 | 解决 |
|:----|:----|:----|
| 窗口一闪就关 | 忘了 `app.exec_()` | 加上 `sys.exit(app.exec_())` |
| 界面卡死 | 耗时操作在主线程执行 | 放到 QThread 里 |
| 子线程更新 UI 崩溃 | Qt 控件不是线程安全的 | 用 `pyqtSignal` 发数据到主线程 |
| 布局乱套 | 忘了 setCentralWidget 或 layout 没设置 | 检查嵌套结构 |
| 窗口空白 | paintEvent 没调用 update() | 数据更新后调 `self.update()` |
| 图片不显示 | 路径不对 | 用绝对路径或检查文件存在 |
| 按钮不响应 | connect 写错了函数名 | 检查函数名和参数对齐 |
| 定时器不触发 | 没调用 start() | 在 __init__ 里加 `timer.start(ms)` |

---

## 总结——你真正需要记的

```
控件类：    QWidget, QMainWindow, QLabel, QPushButton, QLineEdit,
            QComboBox, QTextEdit, QTableWidget, QGroupBox, QPlainTextEdit
布局类：    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout
核心机制：  QTimer（定时刷新）, QThread（不卡界面）, pyqtSignal（线程间通信）
绘图：      QPainter（手动画图）, pyqtgraph（实时曲线）
定时器：    timer.start(ms) + timer.timeout.connect(函数)
信号：      控件.信号名.connect(函数)  # clicked, textChanged, currentTextChanged
样式：      setStyleSheet("CSS语法")
```

**你的学习路径：**
1. 先跑通上面的完整模板代码（把 DataWorker 替换成真 ROS 订阅）
2. 按需要加新的控件（搜 "PyQt + 功能名"）
3. 每加一个功能就跑一次，不要一口气写 500 行再调试
