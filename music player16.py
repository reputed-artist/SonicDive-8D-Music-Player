# import sys, os, math
# import numpy as np
# import sounddevice as sd
# import librosa

# from PyQt5.QtWidgets import (
#     QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
#     QPushButton, QFileDialog, QLabel, QComboBox,
#     QTableWidget, QTableWidgetItem, QSlider, QStyle,
#     QFrame, QGroupBox, QGridLayout
    
# )
# from PyQt5.QtGui import QIcon, QPainter, QColor, QFont, QLinearGradient, QBrush, QPen, QPolygonF, QPainterPath, QRadialGradient
# from PyQt5.QtCore import QThread, Qt, QTimer, pyqtSignal, QPointF


# # ================= AUDIO THREAD =================
# class AudioThread(QThread):
#     position_changed = pyqtSignal(float)  # Emits current position in seconds
#     loading_complete = pyqtSignal(str)    # Emits when loading is complete
#     loading_started = pyqtSignal(str)     # Emits when loading starts
    
#     def __init__(self):
#         super().__init__()
#         self.running = False
#         self.effect = "Flat"
#         self.volume = 0.8

#         self.mono = None
#         self.sr = 44100
#         self.current_position = 0.0  # Current position in seconds
#         self.angle = 0.0
#         self.duration = 0.0
#         self.force_seek = None  # Force seek to this position

#         self.visual_samples = np.zeros(256, dtype=np.float32)

#     def load(self, file):
#         """Load audio file"""
#         self.loading_started.emit(os.path.basename(file))
        
#         try:
#             # Load audio file
#             y, self.sr = librosa.load(file, mono=True, sr=22050)
#             y = y / max(np.max(np.abs(y)), 1e-6)
#             self.mono = y.astype(np.float32)
#             self.current_position = 0.0
#             self.angle = 0.0
#             self.duration = len(y) / self.sr
#             self.position_changed.emit(0.0)
#             self.loading_complete.emit(os.path.basename(file))
#             return True
#         except Exception as e:
#             print(f"Error loading file: {e}")
#             return False

#     def seek(self, position):
#         """Force seek to position in seconds"""
#         if self.mono is not None:
#             # Clamp position to valid range
#             position = max(0.0, min(position, self.duration))
#             print(f"AudioThread: Seeking to {position:.2f} seconds")
#             self.force_seek = position
#             self.current_position = position

#     def callback(self, outdata, frames, time, status):
#         if status:
#             print(status)
            
#         if not self.running or self.mono is None:
#             outdata[:] = np.zeros((frames, 2), np.float32)
#             return

#         out = np.zeros((frames, 2), np.float32)
        
#         # Handle force seek
#         if self.force_seek is not None:
#             self.current_position = self.force_seek
#             self.force_seek = None
#             print(f"Callback: Starting from {self.current_position:.2f}s")
        
#         # Calculate starting sample
#         start_sample = int(self.current_position * self.sr)
        
#         # Check bounds
#         if start_sample >= len(self.mono):
#             outdata[:] = np.zeros((frames, 2), np.float32)
#             self.running = False
#             return
        
#         for i in range(frames):
#             if start_sample + i >= len(self.mono):
#                 # End of track
#                 self.running = False
#                 break

#             base = self.mono[start_sample + i] * self.volume
#             self.visual_samples[i % 256] = base

#             pan = (math.sin(self.angle) + 1) * 0.5
#             self.angle += 0.0006

#             L = R = base

#             if self.effect == "Rock":
#                 L *= 1.35
#                 R *= 1.35

#             elif self.effect == "3D":
#                 L = base * (1 - pan) * 1.3
#                 R = base * pan * 1.3

#             elif self.effect == "8D":
#                 depth = 1.0 - abs(math.cos(self.angle)) * 0.3
#                 L = base * (1 - pan) * depth * 1.4
#                 R = base * pan * depth * 1.4

#             elif self.effect == "Dolby":
#                 side = math.sin(self.angle) * 0.3
#                 bass = base * 0.3
#                 L = base + side + bass
#                 R = base - side + bass

#             out[i, 0] = np.tanh(L)
#             out[i, 1] = np.tanh(R)
        
#         # Update current position
#         frames_processed = min(frames, len(self.mono) - start_sample)
#         self.current_position += frames_processed / self.sr
        
#         # Emit position update
#         self.position_changed.emit(self.current_position)

#         outdata[:] = out

#     def run(self):
#         self.running = True
#         with sd.OutputStream(
#             samplerate=self.sr,
#             channels=2,
#             callback=self.callback,
#             blocksize=1024
#         ):
#             while self.running:
#                 sd.sleep(30)

#     def stop(self):
#         self.running = False


# # ================= SPECTRUM VISUALIZER =================
# class Spectrum(QWidget):
#     def __init__(self, audio):
#         super().__init__()
#         self.audio = audio
#         self.mode = "Bars"
#         self.phase = 0.0
#         self.setMinimumHeight(250)

#     def set_mode(self, mode):
#         self.mode = mode
#         self.update()

#     def paintEvent(self, e):
#         if self.audio.visual_samples is None:
#             return

#         data = np.abs(np.fft.rfft(self.audio.visual_samples))[:64]

#         painter = QPainter(self)
#         painter.setRenderHint(QPainter.Antialiasing)

#         w, h = self.width(), self.height()
#         cx, cy = w // 2, h // 2

#         if self.mode == "Bars":
#             bw = w / len(data)
#             for i, v in enumerate(data):
#                 bh = min(v * 40, h)
#                 color = QColor.fromHsv((i * 6) % 360, 255, 255)
#                 painter.setBrush(color)
#                 painter.setPen(Qt.NoPen)
#                 painter.drawRect(
#                     int(i * bw),
#                     h - int(bh),
#                     int(bw - 2),
#                     int(bh)
#                 )

#         elif self.mode == "Wave particle":
#             painter.setBrush(Qt.NoBrush)
#             painter.setPen(QPen(QColor(0, 200, 255, 180), 2))
            
#             self.phase += 0.04
#             for i, v in enumerate(data):
#                 x = int((i / len(data)) * w)
#                 y = int(cy + math.sin(self.phase + i * 0.25) * v * 25)
#                 painter.setBrush(QColor.fromHsv((i * 6) % 360, 255, 255))
#                 painter.drawEllipse(x - 3, y - 3, 6, 6)
                
#         elif self.mode == "Wave":
#             # 保存历史位置用于绘制轨迹
#             if not hasattr(self, 'trail_history'):
#                 self.trail_history = []
            
#             # 限制历史记录长度
#             if len(self.trail_history) > 10:
#                 self.trail_history.pop(0)
            
#             # 绘制轨迹
#             painter.setPen(Qt.NoPen)
#             for trail_idx, trail in enumerate(self.trail_history):
#                 alpha = int(100 * (trail_idx + 1) / len(self.trail_history))
#                 painter.setBrush(QColor(0, 200, 255, alpha))
#                 for x, y in trail:
#                     painter.drawEllipse(x - 2, y - 2, 4, 4)
            
#             # 当前帧粒子位置
#             current_frame = []
#             self.phase += 0.04
            
#             # 绘制当前粒子
#             painter.setPen(QPen(QColor(0, 200, 255, 180), 1))
#             for i, v in enumerate(data):
#                 x = int((i / len(data)) * w)
#                 y = int(cy + math.sin(self.phase + i * 0.25) * v * 25)
                
#                 # 保存位置
#                 current_frame.append((x, y))
                
#                 # 粒子颜色渐变
#                 hue = (i * 6 + int(self.phase * 50)) % 360  # 添加相位影响色相
#                 painter.setBrush(QColor.fromHsv(hue, 255, 255, 220))
#                 painter.drawEllipse(x - 3, y - 3, 6, 6)
                
#                 # 可选：连接相邻粒子
#                 if i > 0 and i % 5 == 0:  # 每5个点连接一次
#                     prev_x = int(((i-1) / len(data)) * w)
#                     prev_y = int(cy + math.sin(self.phase + (i-1) * 0.25) * data[i-1] * 25)
#                     painter.setPen(QPen(QColor(0, 200, 255, 80), 1))
#                     painter.drawLine(prev_x, prev_y, x, y)
            
#             # 保存当前帧到历史
#             self.trail_history.append(current_frame)

#         elif self.mode == "Circle":
#             radius = min(cx, cy) - 30
#             for i, v in enumerate(data):
#                 angle = (i / len(data)) * 2 * math.pi
#                 r = radius + v * 25
#                 x = cx + math.cos(angle) * r
#                 y = cy + math.sin(angle) * r
#                 color = QColor.fromHsv((i * 6) % 360, 255, 255)
#                 painter.setBrush(color)
#                 painter.setPen(Qt.NoPen)
#                 painter.drawEllipse(int(x), int(y), 6, 6)
        
#         elif self.mode == "Disk":
#             # Calculate sizes
#             max_radius = min(cx, cy) - 10
#             disk_radius = max_radius * 0.5  # Disk takes 50% of available space
#             max_bar_length = max_radius - disk_radius - 5  # Space for bars
            
#             # Draw realistic CD disk with rainbow effect
#             # Draw outer metallic ring
#             outer_ring_radius = disk_radius * 0.95
#             painter.setBrush(Qt.NoBrush)
#             painter.setPen(QPen(QColor(180, 180, 200, 200), 3))
#             painter.drawEllipse(int(cx - outer_ring_radius), int(cy - outer_ring_radius), 
#                                int(outer_ring_radius * 2), int(outer_ring_radius * 2))
            
#             # Draw CD rainbow effect (concentric rings with different colors)
#             ring_colors = [
#                 QColor(255, 0, 0, 180),      # Red
#                 QColor(255, 127, 0, 180),    # Orange
#                 QColor(255, 255, 0, 180),    # Yellow
#                 QColor(0, 255, 0, 180),      # Green
#                 QColor(0, 0, 255, 180),      # Blue
#                 QColor(75, 0, 130, 180),     # Indigo
#                 QColor(148, 0, 211, 180)     # Violet
#             ]
            
#             for i, color in enumerate(ring_colors):
#                 ring_radius = disk_radius * (0.7 - (i * 0.08))
#                 if ring_radius > disk_radius * 0.2:  # Don't draw too small
#                     painter.setBrush(Qt.NoBrush)
#                     painter.setPen(QPen(color, 2))
#                     painter.drawEllipse(int(cx - ring_radius), int(cy - ring_radius), 
#                                        int(ring_radius * 2), int(ring_radius * 2))
            
#             # Draw central blue disk area (like a CD's data area)
#             data_area_radius = disk_radius * 0.65
#             gradient = QLinearGradient(cx - data_area_radius, cy - data_area_radius, 
#                                       cx + data_area_radius, cy + data_area_radius)
#             gradient.setColorAt(0, QColor(0, 100, 200, 180))  # Dark blue
#             gradient.setColorAt(0.5, QColor(0, 150, 255, 200))  # Medium blue
#             gradient.setColorAt(1, QColor(0, 100, 200, 180))  # Dark blue
            
#             painter.setBrush(QBrush(gradient))
#             painter.setPen(QPen(QColor(0, 180, 255, 220), 2))
#             painter.drawEllipse(int(cx - data_area_radius), int(cy - data_area_radius), 
#                                int(data_area_radius * 2), int(data_area_radius * 2))
            
#             # Draw CD center hole with silver color
#             center_hole_radius = disk_radius * 0.15
#             center_gradient = QLinearGradient(cx - center_hole_radius, cy - center_hole_radius,
#                                              cx + center_hole_radius, cy + center_hole_radius)
#             center_gradient.setColorAt(0, QColor(220, 220, 220, 200))
#             center_gradient.setColorAt(1, QColor(180, 180, 180, 200))
            
#             painter.setBrush(QBrush(center_gradient))
#             painter.setPen(QPen(QColor(200, 200, 200, 150), 2))
#             painter.drawEllipse(int(cx - center_hole_radius), int(cy - center_hole_radius), 
#                                int(center_hole_radius * 2), int(center_hole_radius * 2))
            
#             # Draw small inner hole (like a CD spindle)
#             spindle_radius = center_hole_radius * 0.4
#             painter.setBrush(QBrush(QColor(100, 100, 120, 200)))
#             painter.setPen(QPen(QColor(80, 80, 100, 150), 1))
#             painter.drawEllipse(int(cx - spindle_radius), int(cy - spindle_radius), 
#                                int(spindle_radius * 2), int(spindle_radius * 2))
            
#             # Draw spectrum bars radiating from disk (same as before)
#             bar_count = len(data)
#             bar_width = 6
            
#             for i, v in enumerate(data):
#                 # Calculate angle for this bar (evenly spaced around the circle)
#                 angle = (i / bar_count) * 2 * math.pi
                
#                 # Calculate bar length based on frequency data
#                 bar_length = min(v * 80, max_bar_length)
                
#                 # Color based on frequency (same rainbow colors as Bars mode)
#                 color = QColor.fromHsv((i * 6) % 360, 255, 255)
#                 painter.setBrush(color)
#                 painter.setPen(Qt.NoPen)
                
#                 # Calculate start point (on disk edge)
#                 start_x = cx + math.cos(angle) * disk_radius
#                 start_y = cy + math.sin(angle) * disk_radius
                
#                 # Calculate end point (extending outward from disk)
#                 end_x = cx + math.cos(angle) * (disk_radius + bar_length)
#                 end_y = cy + math.sin(angle) * (disk_radius + bar_length)
                
#                 # Calculate perpendicular direction for bar width
#                 perp_angle = angle + math.pi / 2
#                 perp_dx = math.cos(perp_angle) * bar_width / 2
#                 perp_dy = math.sin(perp_angle) * bar_width / 2
                
#                 # Create bar polygon (rectangle aligned with angle)
#                 bar_polygon = QPolygonF([
#                     QPointF(start_x - perp_dx, start_y - perp_dy),
#                     QPointF(start_x + perp_dx, start_y + perp_dy),
#                     QPointF(end_x + perp_dx, end_y + perp_dy),
#                     QPointF(end_x - perp_dx, end_y - perp_dy)
#                 ])
                
#                 # Draw the bar
#                 painter.drawPolygon(bar_polygon)
                
#                 # Add a small glow effect at the tip of each bar
#                 if bar_length > 5:
#                     painter.setBrush(Qt.NoBrush)
#                     painter.setPen(QPen(color.lighter(150), 1))
#                     painter.drawEllipse(int(end_x - 2), int(end_y - 2), 4, 4)        

#     def set_mode(self, mode):
#         self.mode = mode
#         self.update()


# # ================= MUSIC PLAYER UI =================
# class MusicPlayer(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("🎧 Professional DJ Music Player")
#         self.resize(1200, 720)
        
#         # Simple dark theme
#         self.setStyleSheet("""
#             QMainWindow {
#                 background-color: #121212;
#             }
#             QWidget {
#                 color: #ffffff;
#                 font-family: 'Segoe UI', Arial, sans-serif;
#             }
#             QPushButton {
#                 background-color: #2d2d2d;
#                 border: none;
#                 padding: 6px 12px;
#                 border-radius: 4px;
#                 font-weight: bold;
#                 font-size: 11px;
#             }
#             QPushButton:hover {
#                 background-color: #3d3d3d;
#             }
#             QPushButton:pressed {
#                 background-color: #1d1d1d;
#             }
#             QSlider::groove:horizontal {
#                 height: 6px;
#                 background: #333;
#                 border-radius: 3px;
#             }
#             QSlider::sub-page:horizontal {
#                 background: #00b4d8;
#                 border-radius: 3px;
#             }
#             QSlider::handle:horizontal {
#                 background: #ffffff;
#                 width: 16px;
#                 margin: -5px 0;
#                 border-radius: 8px;
#                 border: 2px solid #00b4d8;
#             }
#             QTableWidget {
#                 background-color: #1e1e1e;
#                 gridline-color: #333;
#                 selection-background-color: #00b4d8;
#                 border: none;
#                 font-size: 11px;
#                 color: white;
#             }
#             QComboBox {
#                 background-color: #2d2d2d;
#                 border: 1px solid #444;
#                 padding: 4px;
#                 border-radius: 3px;
#                 font-size: 11px;
#                 color: white;
#             }
#             QComboBox::drop-down {
#                 border: none;
#                 width: 20px;
#             }
            
#             QComboBox::down-arrow {
#                 width: 12px;
#                 height: 12px;
#             }
            
#             QComboBox QAbstractItemView {
#                 background-color: #2d2d2d;
#                 border: 1px solid #444;
#                 selection-background-color: #00b4d8;
#                 color: white;
#                 outline: none;
#             }
            
#             QComboBox QAbstractItemView::item {
#                 padding: 4px;
#                 border: none;
#             }
            
#             QComboBox QAbstractItemView::item:hover {
#                 background-color: #3d3d3d;
#             }
            
#             QLabel {
#                 font-size: 11px;
#                 color: #ffffff;
#             }
#         """)

#         self.audio = AudioThread()
#         self.files = []
#         self.durations = []  # Store durations for each track
#         self.current_file_index = -1
#         self.user_is_seeking = False
#         self.playing_color_index = 0  # For rotating colors

#         # Initialize UI
#         self.init_ui()

#         # Connect signals
#         self.audio.position_changed.connect(self.update_progress_from_audio)
#         self.audio.loading_started.connect(self.show_loading)
#         self.audio.loading_complete.connect(self.hide_loading)

#         # Timer for visualizer
#         self.timer = QTimer()
#         self.timer.timeout.connect(self.update_visualizer)
#         self.timer.start(30)

#     def init_ui(self):
#         root = QWidget()
#         self.setCentralWidget(root)
#         main_layout = QVBoxLayout(root)
#         main_layout.setContentsMargins(10, 10, 10, 10)
#         main_layout.setSpacing(8)

#         # ===== TOP BAR =====
#         top_bar = QHBoxLayout()
#         top_bar.setSpacing(10)
        
#         self.title_label = QLabel("🎧 No Track Playing")
#         self.title_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
#         self.title_label.setStyleSheet("""
#             QLabel {
#                 color: #00b4d8; 
#                 background-color: #0a0a0a;
#                 border: 1px solid #333;
#                 border-radius: 4px;
#                 padding: 6px 10px;
#                 font-weight: bold;
#             }
#         """)
#         self.title_label.setMinimumHeight(40)
        
#         self.loading_label = QLabel("")
#         self.loading_label.setVisible(False)
#         self.loading_label.setStyleSheet("color: #ff9900; font-style: italic;")
        
#         top_bar.addWidget(self.title_label)
#         top_bar.addWidget(self.loading_label)
#         top_bar.addStretch()
        
#         main_layout.addLayout(top_bar)

#         # ===== MAIN CONTENT =====
#         content_layout = QHBoxLayout()
#         content_layout.setSpacing(12)

#         # ===== LEFT PANEL - Playlist =====
#         left_panel = QVBoxLayout()
#         left_panel.setSpacing(6)
        
#         playlist_label = QLabel("Playlist")
#         playlist_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #00b4d8;")
#         left_panel.addWidget(playlist_label)
        
#         # Create table with 2 columns: Track and Duration
#         self.table = QTableWidget(0, 2)
#         self.table.setHorizontalHeaderLabels(["💿 Track", "Duration"])
#         self.table.verticalHeader().setVisible(False)
#         self.table.setShowGrid(False)
#         self.table.setEditTriggers(QTableWidget.NoEditTriggers)
#         self.table.setSelectionBehavior(QTableWidget.SelectRows)
#         self.table.setColumnWidth(0, 250)  # Track column
#         self.table.setColumnWidth(1, 200)   # Duration column
#         self.table.cellDoubleClicked.connect(self.play_selected)
        
#         # Set table styles with colorful disc support
#         self.table.setStyleSheet("""
#             QTableWidget {
#                 background-color: #1e1e1e;
#                 color: white;
#                 gridline-color: #333;
#                 border: none;
#                 font-size: 11px;
#                 alternate-background-color: #252525;
#             }
#             QTableWidget::item {
#                 background-color: transparent;
#                 color: #cccccc;
#                 border-bottom: 1px solid #333;
#                 padding: 4px;
#             }
#             QTableWidget::item:selected {
#                 background-color: #00b4d8;
#                 color: white;
#                 font-weight: bold;
#             }
#             /* Gray background for playing track */
#             QTableWidget::item[playing="true"] {
#                 background-color: #404040;
#                 color: white;
#                 font-weight: bold;
#             }
#             /* Colorful disc for playing track - will be set dynamically */
#             QHeaderView::section {
#                 background-color: #2d2d2d;
#                 color: #00b4d8;
#                 font-weight: bold;
#                 padding: 6px;
#                 border: none;
#                 border-bottom: 2px solid #00b4d8;
#             }
#             QTableWidget QScrollBar:vertical {
#                 background-color: #1a1a1a;
#                 width: 12px;
#             }
#             QTableWidget QScrollBar::handle:vertical {
#                 background-color: #444;
#                 border-radius: 6px;
#                 min-height: 20px;
#             }
#             QTableWidget QScrollBar::handle:vertical:hover {
#                 background-color: #555;
#             }
#         """)
        
#         # Enable alternating row colors
#         self.table.setAlternatingRowColors(True)
        
#         left_panel.addWidget(self.table)
        
#         # Simple buttons
#         btn_layout = QHBoxLayout()
#         btn_layout.setSpacing(8)
#         load_btn = QPushButton("📁 Load Folder")
#         load_btn.clicked.connect(self.load_folder)
#         clear_btn = QPushButton("🗑️ Clear")
#         clear_btn.clicked.connect(self.clear_playlist)
        
#         btn_layout.addWidget(load_btn)
#         btn_layout.addWidget(clear_btn)
#         left_panel.addLayout(btn_layout)
        
#         content_layout.addLayout(left_panel, 1)

#         # ===== RIGHT PANEL =====
#         right_panel = QVBoxLayout()
#         right_panel.setSpacing(10)
        
#         # Visualizer
#         self.spectrum = Spectrum(self.audio)
#         self.spectrum.setMinimumHeight(240)
#         self.spectrum.setMaximumHeight(410)
#         right_panel.addWidget(self.spectrum)
        
#         # ===== VISUALIZER CONTROLS - Combined layout =====
#         controls_layout = QHBoxLayout()
#         controls_layout.setSpacing(12)
        
#         # Visualizer mode (left side)
#         mode_layout = QHBoxLayout()
#         mode_layout.setSpacing(8)
#         mode_label = QLabel("Visual Mode:")
#         mode_label.setStyleSheet("font-weight: bold;")
#         self.spectrum_mode = QComboBox()
#         self.spectrum_mode.addItems(["Bars", "Wave", "Circle", "Disk"])
#         self.spectrum_mode.currentTextChanged.connect(self.spectrum.set_mode)
#         self.spectrum_mode.setFixedWidth(90)
        
#         mode_layout.addWidget(mode_label)
#         mode_layout.addWidget(self.spectrum_mode)
        
#         # Add spacing between Visual Mode and Effects
#         mode_layout.addSpacing(20)
        
#         # Effects (middle)
#         effects_label = QLabel("FX:")
#         effects_label.setStyleSheet("font-weight: bold;")
#         self.effects_combo = QComboBox()
#         self.effects_combo.addItems(["Flat", "Rock", "3D", "8D", "Dolby"])
#         self.effects_combo.currentTextChanged.connect(lambda e: setattr(self.audio, 'effect', e))
#         self.effects_combo.setFixedWidth(90)
        
#         mode_layout.addWidget(effects_label)
#         mode_layout.addWidget(self.effects_combo)
        
#         # Add spacing between Effects and Volume
#         mode_layout.addSpacing(20)
        
#         # Volume (right side) - MOVED HERE
#         volume_label = QLabel("Vol:")
#         volume_label.setStyleSheet("font-weight: bold;")
        
#         self.volume_slider = QSlider(Qt.Horizontal)
#         self.volume_slider.setRange(0, 100)
#         self.volume_slider.setValue(80)
#         self.volume_slider.valueChanged.connect(lambda v: setattr(self.audio, 'volume', v/100))
#         self.volume_slider.setFixedWidth(100)
#         self.volume_slider.setStyleSheet("""
#             QSlider::groove:horizontal {
#                 height: 6px;
#                 background: #333;
#                 border-radius: 3px;
#             }
#             QSlider::sub-page:horizontal {
#                 background: #00b4d8;
#                 border-radius: 3px;
#             }
#             QSlider::handle:horizontal {
#                 background: #ffffff;
#                 width: 14px;
#                 margin: -4px 0;
#                 border-radius: 7px;
#                 border: 2px solid #00b4d8;
#             }
#         """)
        
#         mode_layout.addWidget(volume_label)
#         mode_layout.addWidget(self.volume_slider)
        
#         # Add stretch to push everything to the left
#         mode_layout.addStretch()
        
#         # Add the combined layout to the controls layout
#         controls_layout.addLayout(mode_layout)
        
#         right_panel.addLayout(controls_layout)
        
#         # Add spacing before progress bar
#         right_panel.addSpacing(10)
        
#         # ===== PROGRESS BAR SECTION - Labels BELOW =====
#         progress_frame = QFrame()
#         progress_frame.setFixedHeight(90)
#         progress_frame.setStyleSheet("""
#             QFrame {
#                 background-color: #1a1a1a;
#                 border-radius: 6px;
#                 padding: 2px;
#             }
#         """)
#         progress_layout = QVBoxLayout(progress_frame)
#         progress_layout.setContentsMargins(10, 8, 10, 8)
#         progress_layout.setSpacing(5)
        
#         # Progress bar at the TOP
#         self.progress_bar = QSlider(Qt.Horizontal)
#         self.progress_bar.setRange(0, 10000)
#         self.progress_bar.setValue(0)
#         self.progress_bar.setStyleSheet("""
#             QSlider::groove:horizontal {
#                 height: 8px;
#                 background: #333;
#                 border-radius: 4px;
#             }
#             QSlider::sub-page:horizontal {
#                 background: #00b4d8;
#                 border-radius: 4px;
#             }
#             QSlider::handle:horizontal {
#                 background: #ffffff;
#                 width: 18px;
#                 height: 18px;
#                 margin: -6px 0;
#                 border-radius: 9px;
#                 border: 2px solid #00b4d8;
#             }
#         """)
        
#         progress_layout.addWidget(self.progress_bar)
        
#         # Time labels BELOW - in a separate container
#         time_container = QFrame()
#         time_container.setFixedHeight(30)
#         time_container.setStyleSheet("background: transparent;")
#         time_layout = QHBoxLayout(time_container)
#         time_layout.setContentsMargins(1, 2, 2, 2)
        
#         self.current_time_label = QLabel("00:00")
#         self.current_time_label.setStyleSheet("""
#             QLabel {
#                 font-weight: bold;
#                 font-size: 14px;
#                 color: #00b4d8;
#                 min-width: 55px;
#             }
#         """)
#         self.current_time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
#         self.duration_label = QLabel("00:00")
#         self.duration_label.setStyleSheet("""
#             QLabel {
#                 font-weight: bold;
#                 font-size: 14px;
#                 min-width: 55px;
#             }
#         """)
#         self.duration_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
#         time_layout.addWidget(self.current_time_label)
#         time_layout.addStretch()
#         time_layout.addWidget(QLabel(""))
#         time_layout.addWidget(self.duration_label)
        
#         progress_layout.addWidget(time_container)
        
#         # Connect signals
#         self.progress_bar.sliderPressed.connect(self.start_seeking)
#         self.progress_bar.sliderReleased.connect(self.end_seeking)
#         self.progress_bar.sliderMoved.connect(self.update_seek_preview)
        
#         right_panel.addWidget(progress_frame)

#         content_layout.addLayout(right_panel, 2)
#         main_layout.addLayout(content_layout)

#         # ===== CONTROL PANEL =====
#         control_panel = QHBoxLayout()
#         control_panel.setSpacing(12)
        
#         # Transport controls
#         transport_layout = QHBoxLayout()
#         transport_layout.setSpacing(10)
        
#         def create_btn(text, tooltip=""):
#             btn = QPushButton(text)
#             btn.setToolTip(tooltip)
#             btn.setFixedSize(46, 46)
#             btn.setStyleSheet("""
#                 QPushButton {
#                     border-radius: 23px;
#                     background-color: #222;
#                     font-size: 17px;
#                     font-weight: bold;
#                     border: 1px solid #444;
#                 }
#                 QPushButton:hover {
#                     background-color: #333;
#                     border: 1px solid #00b4d8;
#                 }
#                 QPushButton:pressed {
#                     background-color: #111;
#                 }
#             """)
#             return btn
        
#         self.btn_prev = create_btn("⏮", "Previous")
#         self.btn_play = create_btn("▶", "Play/Pause")
#         self.btn_next = create_btn("⏭", "Next")
#         self.btn_stop = create_btn("⏹", "Stop")
        
#         self.btn_prev.clicked.connect(self.prev)
#         self.btn_play.clicked.connect(self.toggle_play)
#         self.btn_next.clicked.connect(self.next)
#         self.btn_stop.clicked.connect(self.stop)
        
#         transport_layout.addWidget(self.btn_prev)
#         transport_layout.addWidget(self.btn_play)
#         transport_layout.addWidget(self.btn_next)
#         transport_layout.addWidget(self.btn_stop)
        
#         # REMOVED VOLUME FROM HERE - it's now above
        
#         control_panel.addLayout(transport_layout)
#         control_panel.addStretch()
        
#         # Add any other controls if needed
#         control_panel.addWidget(QLabel(""))  # Empty spacer
        
#         main_layout.addLayout(control_panel)

#     def show_loading(self, filename):
#         self.loading_label.setText(f"Loading: {filename}...")
#         self.loading_label.setVisible(True)

#     def hide_loading(self, filename):
#         self.loading_label.setText("")
#         self.loading_label.setVisible(False)

#     def load_folder(self):
#         folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
#         if not folder:
#             return

#         self.files.clear()
#         self.durations.clear()
#         self.table.setRowCount(0)

#         for f in os.listdir(folder):
#             if f.lower().endswith((".mp3", ".wav", ".flac", ".ogg", ".m4a")):
#                 file_path = os.path.join(folder, f)
                
#                 # Get duration - FIXED: Try multiple methods to avoid MP3 errors
#                 duration = 0
#                 try:
#                     # Method 1: Try librosa first
#                     duration = librosa.get_duration(path=file_path)
#                 except Exception as e:
#                     print(f"Librosa error for {f}: {e}")
#                     try:
#                         # Method 2: Try loading with shorter duration
#                         y, sr = librosa.load(file_path, mono=True, sr=22050, duration=30)
#                         duration = librosa.get_duration(y=y, sr=sr)
#                     except Exception as e2:
#                         print(f"Alternative method error for {f}: {e2}")
#                         try:
#                             # Method 3: Use mutagen as fallback (install with: pip install mutagen)
#                             from mutagen import File
#                             audio = File(file_path)
#                             if audio is not None:
#                                 duration = audio.info.length
#                             else:
#                                 duration = 0
#                         except ImportError:
#                             duration = 0
#                         except Exception as e3:
#                             print(f"Mutagen error for {f}: {e3}")
#                             duration = 0
                
#                 self.durations.append(duration)
#                 self.files.append(file_path)
                
#                 r = self.table.rowCount()
#                 self.table.insertRow(r)
                
#                 # Track name with gray disc icon
#                 track_item = QTableWidgetItem(f"💿 {f}")
#                 track_item.setData(Qt.UserRole, file_path)
#                 self.table.setItem(r, 0, track_item)
                
#                 # Display duration immediately
#                 if duration > 0:
#                     mins = int(duration // 60)
#                     secs = int(duration % 60)
#                     duration_text = f"{mins:02d}:{secs:02d}"
#                 else:
#                     duration_text = "--:--"
                
#                 duration_item = QTableWidgetItem(duration_text)
#                 duration_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
#                 self.table.setItem(r, 1, duration_item)

#     def clear_playlist(self):
#         self.files.clear()
#         self.durations.clear()
#         self.table.setRowCount(0)
#         self.stop()

#     def play_selected(self, row=None):
#         if row is None:
#             row = self.table.currentRow()
        
#         if 0 <= row < len(self.files):
#             # Clear previous playing track highlight
#             for i in range(self.table.rowCount()):
#                 # Clear playing flag from all items
#                 for col in range(2):
#                     item = self.table.item(i, col)
#                     if item:
#                         item.setData(Qt.UserRole + 1, None)  # Clear playing flag
                        
#                 # Reset track disc to gray for non-playing tracks
#                 track_item = self.table.item(i, 0)
#                 if track_item:
#                     text = track_item.text()
#                     # Remove any color emoji and set back to CD emoji
#                     if "🔴" in text or "🟢" in text or "🔵" in text or "🟡" in text or "🟣" in text or "🟠" in text:
#                         # Extract just the filename
#                         parts = text.split(" ", 1)
#                         if len(parts) > 1:
#                             track_item.setText(f"💿 {parts[1]}")
            
#             self.current_file_index = row
#             file_path = self.files[row]
            
#             if self.audio.load(file_path):
#                 self.title_label.setText(f"🎧 {os.path.basename(file_path)}")
                
#                 if not self.audio.isRunning():
#                     self.audio.start()
                
#                 self.audio.running = True
#                 self.btn_play.setText("⏸")
                
#                 # Update duration display - use the actual duration from audio thread
#                 mins = int(self.audio.duration // 60)
#                 secs = int(self.audio.duration % 60)
#                 duration_text = f"{mins:02d}:{secs:02d}"
                
#                 # Update duration in table (in case it was --:--)
#                 duration_item = self.table.item(row, 1)
#                 if duration_item:
#                     duration_item.setText(duration_text)
                
#                 # Store the actual duration
#                 self.durations[row] = self.audio.duration
                
#                 # Update progress bar duration
#                 self.duration_label.setText(duration_text)
                
#                 # Reset progress
#                 self.progress_bar.setValue(0)
                
#                 # Highlight playing track with colorful disc
#                 track_item = self.table.item(row, 0)
#                 if track_item:
#                     # Get current text (remove the 💿 if present)
#                     current_text = track_item.text()
#                     parts = current_text.split(" ", 1)
#                     filename = parts[1] if len(parts) > 1 else current_text
                    
#                     # Choose a color based on track index (rotating colors)
#                     colors = ["🔴", "🟢", "🔵", "🟡", "🟣", "🟠"]  # Red, Green, Blue, Yellow, Purple, Orange
#                     color_index = row % len(colors)
#                     colorful_disc = colors[color_index]
                    
#                     # Set colorful disc
#                     track_item.setText(f"{colorful_disc} {filename}")
                    
#                     # Set playing flag for styling
#                     track_item.setData(Qt.UserRole + 1, "playing")
                
#                 # Also highlight duration cell
#                 if duration_item:
#                     duration_item.setData(Qt.UserRole + 1, "playing")
                
#                 # Select the row for visual feedback
#                 self.table.selectRow(row)
                
#                 # Force style update
#                 self.table.viewport().update()

#     def toggle_play(self):
#         if self.audio.mono is None and self.files:
#             self.play_selected(0)
#         elif self.audio.mono is not None:
#             if self.audio.running:
#                 # Pause playback
#                 self.audio.running = False
#                 self.btn_play.setText("▶")
#             else:
#                 # Resume playback
#                 self.audio.running = True
#                 self.btn_play.setText("⏸")

#     def stop(self):
#         self.audio.running = False
#         self.btn_play.setText("▶")
#         self.progress_bar.setValue(0)
#         self.current_time_label.setText("00:00")
        
#         # Reset all tracks to CD emoji
#         if self.current_file_index >= 0:
#             for i in range(self.table.rowCount()):
#                 track_item = self.table.item(i, 0)
#                 if track_item:
#                     text = track_item.text()
#                     # Replace any colorful disc with CD emoji
#                     if "🔴" in text or "🟢" in text or "🔵" in text or "🟡" in text or "🟣" in text or "🟠" in text:
#                         parts = text.split(" ", 1)
#                         if len(parts) > 1:
#                             track_item.setText(f"💿 {parts[1]}")
#                     track_item.setData(Qt.UserRole + 1, None)  # Clear playing flag
                
#                 duration_item = self.table.item(i, 1)
#                 if duration_item:
#                     duration_item.setData(Qt.UserRole + 1, None)  # Clear playing flag
        
#         self.table.viewport().update()

#     def next(self):
#         if not self.files:
#             return
#         next_index = (self.current_file_index + 1) % len(self.files)
#         self.table.selectRow(next_index)
#         self.play_selected(next_index)

#     def prev(self):
#         if not self.files:
#             return
#         prev_index = (self.current_file_index - 1) % len(self.files)
#         self.table.selectRow(prev_index)
#         self.play_selected(prev_index)

#     # ===== SEEKING LOGIC =====
#     def start_seeking(self):
#         self.user_is_seeking = True

#     def update_seek_preview(self, value):
#         if self.audio.mono is not None and self.audio.duration > 0:
#             position = (value / 10000.0) * self.audio.duration
#             mins = int(position // 60)
#             secs = int(position % 60)
#             self.current_time_label.setText(f"{mins:02d}:{secs:02d}")

#     def end_seeking(self):
#         if self.audio.mono is not None and self.audio.duration > 0:
#             value = self.progress_bar.value()
#             position = (value / 10000.0) * self.audio.duration
            
#             print(f"Seeking to position: {position:.2f} seconds")
            
#             self.audio.seek(position)
            
#             mins = int(position // 60)
#             secs = int(position % 60)
#             self.current_time_label.setText(f"{mins:02d}:{secs:02d}")
            
#             if not self.audio.running:
#                 self.audio.running = True
#                 self.btn_play.setText("⏸")
            
#             self.user_is_seeking = False

#     def update_progress_from_audio(self, position):
#         if not self.user_is_seeking and self.audio.mono is not None and self.audio.duration > 0:
#             value = int((position / self.audio.duration) * 10000)
#             self.progress_bar.setValue(value)
            
#             mins = int(position // 60)
#             secs = int(position % 60)
#             self.current_time_label.setText(f"{mins:02d}:{secs:02d}")
            
#             if position >= self.audio.duration - 0.5:
#                 self.next()

#     def update_visualizer(self):
#         self.spectrum.update()

#     def closeEvent(self, e):
#         self.audio.stop()
#         if self.audio.isRunning():
#             self.audio.terminate()
#             self.audio.wait()
#         e.accept()


# # ================= MAIN =================
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     app.setStyle('Fusion')
    
#     font = QFont("Segoe UI", 9)
#     app.setFont(font)
    
#     w = MusicPlayer()
#     w.show()
    
#     sys.exit(app.exec_())
import sys, os, math
import numpy as np
import sounddevice as sd
import librosa

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QSlider, QStyle,
    QFrame, QGroupBox, QGridLayout
    
)
from PyQt5.QtGui import QIcon, QPainter,QIcon, QColor, QFont, QLinearGradient, QBrush, QPen, QPolygonF, QPainterPath, QRadialGradient
from PyQt5.QtCore import QThread, Qt, QTimer, pyqtSignal, QPointF, QSize


# ================= AUDIO THREAD =================
class AudioThread(QThread):
    position_changed = pyqtSignal(float)  # Emits current position in seconds
    loading_complete = pyqtSignal(str)    # Emits when loading is complete
    loading_started = pyqtSignal(str)     # Emits when loading starts
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.effect = "Flat"
        self.volume = 0.8

        self.mono = None
        self.sr = 44100
        self.current_position = 0.0  # Current position in seconds
        self.angle = 0.0
        self.duration = 0.0
        self.force_seek = None  # Force seek to this position

        self.visual_samples = np.zeros(256, dtype=np.float32)

    def load(self, file):
        """Load audio file"""
        self.loading_started.emit(os.path.basename(file))
        
        try:
            # Load audio file
            y, self.sr = librosa.load(file, mono=True, sr=22050)
            y = y / max(np.max(np.abs(y)), 1e-6)
            self.mono = y.astype(np.float32)
            self.current_position = 0.0
            self.angle = 0.0
            self.duration = len(y) / self.sr
            self.position_changed.emit(0.0)
            self.loading_complete.emit(os.path.basename(file))
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def seek(self, position):
        """Force seek to position in seconds"""
        if self.mono is not None:
            # Clamp position to valid range
            position = max(0.0, min(position, self.duration))
            print(f"AudioThread: Seeking to {position:.2f} seconds")
            self.force_seek = position
            self.current_position = position

    def callback(self, outdata, frames, time, status):
        if status:
            print(status)
            
        if self.mono is None:
            outdata[:] = np.zeros((frames, 2), np.float32)
            return

        out = np.zeros((frames, 2), np.float32)
        
        # Handle force seek
        if self.force_seek is not None:
            self.current_position = self.force_seek
            self.force_seek = None
            print(f"Callback: Starting from {self.current_position:.2f}s")
        
        # Calculate starting sample
        start_sample = int(self.current_position * self.sr)
        
        # Check bounds
        if start_sample >= len(self.mono):
            outdata[:] = np.zeros((frames, 2), np.float32)
            self.running = False
            return
        
        # Check if we should output audio
        if not self.running:
            # When paused, output silence but still advance time
            outdata[:] = np.zeros((frames, 2), np.float32)
            # Update position even when paused for accurate time display
            self.current_position += frames / self.sr
            self.position_changed.emit(self.current_position)
            return
        
        # Process audio frames
        frames_processed = 0
        for i in range(frames):
            if start_sample + i >= len(self.mono):
                # End of track
                self.running = False
                break

            base = self.mono[start_sample + i] * self.volume
            self.visual_samples[i % 256] = base

            pan = (math.sin(self.angle) + 1) * 0.5
            self.angle += 0.0006

            L = R = base

            if self.effect == "Rock":
                L *= 1.35
                R *= 1.35

            elif self.effect == "3D":
                L = base * (1 - pan) * 1.3
                R = base * pan * 1.3

            elif self.effect == "8D":
                depth = 1.0 - abs(math.cos(self.angle)) * 0.3
                L = base * (1 - pan) * depth * 1.4
                R = base * pan * depth * 1.4

            elif self.effect == "Dolby":
                side = math.sin(self.angle) * 0.3
                bass = base * 0.3
                L = base + side + bass
                R = base - side + bass

            out[i, 0] = np.tanh(L)
            out[i, 1] = np.tanh(R)
            frames_processed += 1
        
        # Update current position
        self.current_position += frames_processed / self.sr
        
        # Emit position update
        self.position_changed.emit(self.current_position)

        outdata[:] = out

    def run(self):
        print("AudioThread.run() started")
        self.running = True
        with sd.OutputStream(
            samplerate=self.sr,
            channels=2,
            callback=self.callback,
            blocksize=1024
        ):
            # Keep the stream open even when paused
            while True:
                sd.sleep(50)  # Sleep a bit to prevent busy waiting
                # Check if we should exit
                if not hasattr(self, '_should_exit'):
                    self._should_exit = False
                if self._should_exit:
                    break
        
        print("AudioThread.run() ended")

    def stop(self):
        self.running = False
        self._should_exit = True  # Signal to exit the run loop


# ================= SPECTRUM VISUALIZER =================
class Spectrum(QWidget):
    def __init__(self, audio):
        super().__init__()
        self.audio = audio
        self.mode = "Bars"
        self.phase = 0.0
        self.setMinimumHeight(250)

    def set_mode(self, mode):
        self.mode = mode
        self.update()

    def paintEvent(self, e):
        if self.audio.visual_samples is None:
            return

        data = np.abs(np.fft.rfft(self.audio.visual_samples))[:64]

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        if self.mode == "Bars":
            bw = w / len(data)
            for i, v in enumerate(data):
                bh = min(v * 40, h)
                color = QColor.fromHsv((i * 6) % 360, 255, 255)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawRect(
                    int(i * bw),
                    h - int(bh),
                    int(bw - 2),
                    int(bh)
                )

        elif self.mode == "Wave particle":
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(0, 200, 255, 180), 2))
            
            self.phase += 0.04
            for i, v in enumerate(data):
                x = int((i / len(data)) * w)
                y = int(cy + math.sin(self.phase + i * 0.25) * v * 25)
                painter.setBrush(QColor.fromHsv((i * 6) % 360, 255, 255))
                painter.drawEllipse(x - 3, y - 3, 6, 6)
                
        elif self.mode == "Wave":
            # 保存历史位置用于绘制轨迹
            if not hasattr(self, 'trail_history'):
                self.trail_history = []
            
            # 限制历史记录长度
            if len(self.trail_history) > 10:
                self.trail_history.pop(0)
            
            # 绘制轨迹
            painter.setPen(Qt.NoPen)
            for trail_idx, trail in enumerate(self.trail_history):
                alpha = int(100 * (trail_idx + 1) / len(self.trail_history))
                painter.setBrush(QColor(0, 200, 255, alpha))
                for x, y in trail:
                    painter.drawEllipse(x - 2, y - 2, 4, 4)
            
            # 当前帧粒子位置
            current_frame = []
            self.phase += 0.04
            
            # 绘制当前粒子
            painter.setPen(QPen(QColor(0, 200, 255, 180), 1))
            for i, v in enumerate(data):
                x = int((i / len(data)) * w)
                y = int(cy + math.sin(self.phase + i * 0.25) * v * 25)
                
                # 保存位置
                current_frame.append((x, y))
                
                # 粒子颜色渐变
                hue = (i * 6 + int(self.phase * 50)) % 360  # 添加相位影响色相
                painter.setBrush(QColor.fromHsv(hue, 255, 255, 220))
                painter.drawEllipse(x - 3, y - 3, 6, 6)
                
                # 可选：连接相邻粒子
                if i > 0 and i % 5 == 0:  # 每5个点连接一次
                    prev_x = int(((i-1) / len(data)) * w)
                    prev_y = int(cy + math.sin(self.phase + (i-1) * 0.25) * data[i-1] * 25)
                    painter.setPen(QPen(QColor(0, 200, 255, 80), 1))
                    painter.drawLine(prev_x, prev_y, x, y)
            
            # 保存当前帧到历史
            self.trail_history.append(current_frame)

        elif self.mode == "Circle":
            radius = min(cx, cy) - 30
            for i, v in enumerate(data):
                angle = (i / len(data)) * 2 * math.pi
                r = radius + v * 25
                x = cx + math.cos(angle) * r
                y = cy + math.sin(angle) * r
                color = QColor.fromHsv((i * 6) % 360, 255, 255)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(x), int(y), 6, 6)
        
        elif self.mode == "Disk":
            # Calculate sizes
            max_radius = min(cx, cy) - 10
            disk_radius = max_radius * 0.5  # Disk takes 50% of available space
            max_bar_length = max_radius - disk_radius - 5  # Space for bars
            
            # Draw realistic CD disk with rainbow effect
            # Draw outer metallic ring
            outer_ring_radius = disk_radius * 0.95
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(180, 180, 200, 200), 3))
            painter.drawEllipse(int(cx - outer_ring_radius), int(cy - outer_ring_radius), 
                               int(outer_ring_radius * 2), int(outer_ring_radius * 2))
            
            # Draw CD rainbow effect (concentric rings with different colors)
            ring_colors = [
                QColor(255, 0, 0, 180),      # Red
                QColor(255, 127, 0, 180),    # Orange
                QColor(255, 255, 0, 180),    # Yellow
                QColor(0, 255, 0, 180),      # Green
                QColor(0, 0, 255, 180),      # Blue
                QColor(75, 0, 130, 180),     # Indigo
                QColor(148, 0, 211, 180)     # Violet
            ]
            
            for i, color in enumerate(ring_colors):
                ring_radius = disk_radius * (0.7 - (i * 0.08))
                if ring_radius > disk_radius * 0.2:  # Don't draw too small
                    painter.setBrush(Qt.NoBrush)
                    painter.setPen(QPen(color, 2))
                    painter.drawEllipse(int(cx - ring_radius), int(cy - ring_radius), 
                                       int(ring_radius * 2), int(ring_radius * 2))
            
            # Draw central blue disk area (like a CD's data area)
            data_area_radius = disk_radius * 0.65
            gradient = QLinearGradient(cx - data_area_radius, cy - data_area_radius, 
                                      cx + data_area_radius, cy + data_area_radius)
            gradient.setColorAt(0, QColor(0, 100, 200, 180))  # Dark blue
            gradient.setColorAt(0.5, QColor(0, 150, 255, 200))  # Medium blue
            gradient.setColorAt(1, QColor(0, 100, 200, 180))  # Dark blue
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(0, 180, 255, 220), 2))
            painter.drawEllipse(int(cx - data_area_radius), int(cy - data_area_radius), 
                               int(data_area_radius * 2), int(data_area_radius * 2))
            
            # Draw CD center hole with silver color
            center_hole_radius = disk_radius * 0.15
            center_gradient = QLinearGradient(cx - center_hole_radius, cy - center_hole_radius,
                                             cx + center_hole_radius, cy + center_hole_radius)
            center_gradient.setColorAt(0, QColor(220, 220, 220, 200))
            center_gradient.setColorAt(1, QColor(180, 180, 180, 200))
            
            painter.setBrush(QBrush(center_gradient))
            painter.setPen(QPen(QColor(200, 200, 200, 150), 2))
            painter.drawEllipse(int(cx - center_hole_radius), int(cy - center_hole_radius), 
                               int(center_hole_radius * 2), int(center_hole_radius * 2))
            
            # Draw small inner hole (like a CD spindle)
            spindle_radius = center_hole_radius * 0.4
            painter.setBrush(QBrush(QColor(100, 100, 120, 200)))
            painter.setPen(QPen(QColor(80, 80, 100, 150), 1))
            painter.drawEllipse(int(cx - spindle_radius), int(cy - spindle_radius), 
                               int(spindle_radius * 2), int(spindle_radius * 2))
            
            # Draw spectrum bars radiating from disk (same as before)
            bar_count = len(data)
            bar_width = 6
            
            for i, v in enumerate(data):
                # Calculate angle for this bar (evenly spaced around the circle)
                angle = (i / bar_count) * 2 * math.pi
                
                # Calculate bar length based on frequency data
                bar_length = min(v * 80, max_bar_length)
                
                # Color based on frequency (same rainbow colors as Bars mode)
                color = QColor.fromHsv((i * 6) % 360, 255, 255)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                
                # Calculate start point (on disk edge)
                start_x = cx + math.cos(angle) * disk_radius
                start_y = cy + math.sin(angle) * disk_radius
                
                # Calculate end point (extending outward from disk)
                end_x = cx + math.cos(angle) * (disk_radius + bar_length)
                end_y = cy + math.sin(angle) * (disk_radius + bar_length)
                
                # Calculate perpendicular direction for bar width
                perp_angle = angle + math.pi / 2
                perp_dx = math.cos(perp_angle) * bar_width / 2
                perp_dy = math.sin(perp_angle) * bar_width / 2
                
                # Create bar polygon (rectangle aligned with angle)
                bar_polygon = QPolygonF([
                    QPointF(start_x - perp_dx, start_y - perp_dy),
                    QPointF(start_x + perp_dx, start_y + perp_dy),
                    QPointF(end_x + perp_dx, end_y + perp_dy),
                    QPointF(end_x - perp_dx, end_y - perp_dy)
                ])
                
                # Draw the bar
                painter.drawPolygon(bar_polygon)
                
                # Add a small glow effect at the tip of each bar
                if bar_length > 5:
                    painter.setBrush(Qt.NoBrush)
                    painter.setPen(QPen(color.lighter(150), 1))
                    painter.drawEllipse(int(end_x - 2), int(end_y - 2), 4, 4)        

    def set_mode(self, mode):
        self.mode = mode
        self.update()


# ================= MUSIC PLAYER UI =================
class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎧 Professional DJ Music Player")
        self.resize(1200, 720)
        
        # Simple dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QWidget {
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #2d2d2d;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #1d1d1d;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #333;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #00b4d8;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
                border: 2px solid #00b4d8;
            }
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #333;
                selection-background-color: #00b4d8;
                border: none;
                font-size: 11px;
                color: white;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #444;
                padding: 4px;
                border-radius: 3px;
                font-size: 11px;
                color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #444;
                selection-background-color: #00b4d8;
                color: white;
                outline: none;
            }
            
            QComboBox QAbstractItemView::item {
                padding: 4px;
                border: none;
            }
            
            QComboBox QAbstractItemView::item:hover {
                background-color: #3d3d3d;
            }
            
            QLabel {
                font-size: 11px;
                color: #ffffff;
            }
        """)

        self.audio = AudioThread()
        self.files = []
        self.durations = []  # Store durations for each track
        self.current_file_index = -1
        self.user_is_seeking = False
        self.playing_color_index = 0  # For rotating colors

        # Initialize UI
        self.init_ui()

        # Connect signals
        self.audio.position_changed.connect(self.update_progress_from_audio)
        self.audio.loading_started.connect(self.show_loading)
        self.audio.loading_complete.connect(self.hide_loading)

        # Timer for visualizer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_visualizer)
        self.timer.start(30)

    def init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # ===== TOP BAR =====
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        
        self.title_label = QLabel("🎧 No Track Playing")
        self.title_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.title_label.setStyleSheet("""
            QLabel {
                color: #00b4d8; 
                background-color: #0a0a0a;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 6px 10px;
                font-weight: bold;
            }
        """)
        self.title_label.setMinimumHeight(40)
        
        self.loading_label = QLabel("")
        self.loading_label.setVisible(False)
        self.loading_label.setStyleSheet("color: #ff9900; font-style: italic;")
        
        top_bar.addWidget(self.title_label)
        top_bar.addWidget(self.loading_label)
        top_bar.addStretch()
        
        main_layout.addLayout(top_bar)

        # ===== MAIN CONTENT =====
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # ===== LEFT PANEL - Playlist =====
        left_panel = QVBoxLayout()
        left_panel.setSpacing(6)
        
        playlist_label = QLabel("Playlist")
        playlist_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #00b4d8;")
        left_panel.addWidget(playlist_label)
        
        # Create table with 2 columns: Track and Duration
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["💿 Track", "Duration"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setColumnWidth(0, 250)  # Track column
        self.table.setColumnWidth(1, 200)   # Duration column
        self.table.cellDoubleClicked.connect(self.play_selected)
        
        # Set table styles with colorful disc support
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: white;
                gridline-color: #333;
                border: none;
                font-size: 11px;
                alternate-background-color: #252525;
            }
            QTableWidget::item {
                background-color: transparent;
                color: #cccccc;
                border-bottom: 1px solid #333;
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #00b4d8;
                color: white;
                font-weight: bold;
            }
            /* Gray background for playing track */
            QTableWidget::item[playing="true"] {
                background-color: #404040;
                color: white;
                font-weight: bold;
            }
            /* Colorful disc for playing track - will be set dynamically */
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #00b4d8;
                font-weight: bold;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #00b4d8;
            }
            QTableWidget QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
            }
            QTableWidget QScrollBar::handle:vertical {
                background-color: #444;
                border-radius: 6px;
                min-height: 20px;
            }
            QTableWidget QScrollBar::handle:vertical:hover {
                background-color: #555;
            }
        """)
        
        # Enable alternating row colors
        self.table.setAlternatingRowColors(True)
        
        left_panel.addWidget(self.table)
        
        # Simple buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        load_btn = QPushButton("📁 Load Folder")
        load_btn.clicked.connect(self.load_folder)
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_playlist)
        
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(clear_btn)
        left_panel.addLayout(btn_layout)
        
        content_layout.addLayout(left_panel, 1)

        # ===== RIGHT PANEL =====
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        
        # Visualizer
        self.spectrum = Spectrum(self.audio)
        self.spectrum.setMinimumHeight(240)
        self.spectrum.setMaximumHeight(410)
        right_panel.addWidget(self.spectrum)
        
        # ===== VISUALIZER CONTROLS - Combined layout =====
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        
        # Visualizer mode (left side)
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        mode_label = QLabel("Visual Mode:")
        mode_label.setStyleSheet("font-weight: bold;")
        self.spectrum_mode = QComboBox()
        self.spectrum_mode.addItems(["Bars", "Wave", "Circle", "Disk"])
        self.spectrum_mode.currentTextChanged.connect(self.spectrum.set_mode)
        self.spectrum_mode.setFixedWidth(90)
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.spectrum_mode)
        
        # Add spacing between Visual Mode and Effects
        mode_layout.addSpacing(20)
        
        # Effects (middle)
        effects_label = QLabel("FX:")
        effects_label.setStyleSheet("font-weight: bold;")
        self.effects_combo = QComboBox()
        self.effects_combo.addItems(["Flat", "Rock", "3D", "8D", "Dolby"])
        self.effects_combo.currentTextChanged.connect(lambda e: setattr(self.audio, 'effect', e))
        self.effects_combo.setFixedWidth(90)
        
        mode_layout.addWidget(effects_label)
        mode_layout.addWidget(self.effects_combo)
        
        # Add spacing between Effects and Volume
        mode_layout.addSpacing(20)
        
        # Volume (right side)
        volume_label = QLabel("Vol:")
        volume_label.setStyleSheet("font-weight: bold;")
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(lambda v: setattr(self.audio, 'volume', v/100))
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #333;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #00b4d8;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
                border: 2px solid #00b4d8;
            }
        """)
        
        mode_layout.addWidget(volume_label)
        mode_layout.addWidget(self.volume_slider)
        
        # Add stretch to push everything to the left
        mode_layout.addStretch()
        
        # Add the combined layout to the controls layout
        controls_layout.addLayout(mode_layout)
        
        right_panel.addLayout(controls_layout)
        
        # Add spacing before progress bar
        right_panel.addSpacing(10)
        
        # ===== PROGRESS BAR SECTION WITH TRANSPORT CONTROLS =====
        progress_frame = QFrame()
        progress_frame.setFixedHeight(140)  # Increased height for transport controls
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 6px;
                padding: 2px;
            }
        """)
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(10, 8, 10, 8)
        progress_layout.setSpacing(8)
        
        # Progress bar at the TOP
        self.progress_bar = QSlider(Qt.Horizontal)
        self.progress_bar.setRange(0, 10000)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #333;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #00b4d8;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
                border: 2px solid #00b4d8;
            }
        """)
        
        progress_layout.addWidget(self.progress_bar)
        
        # Time labels BELOW progress bar
        time_container = QFrame()
        time_container.setFixedHeight(30)
        time_container.setStyleSheet("background: transparent;")
        time_layout = QHBoxLayout(time_container)
        time_layout.setContentsMargins(1, 2, 2, 2)
        
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #00b4d8;
                min-width: 55px;
            }
        """)
        self.current_time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.duration_label = QLabel("00:00")
        self.duration_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                min-width: 55px;
            }
        """)
        self.duration_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(QLabel(""))
        time_layout.addWidget(self.duration_label)
        
        progress_layout.addWidget(time_container)
        
        # Transport controls BELOW time labels (centered)
        transport_container = QFrame()
        transport_container.setFixedHeight(60)
        transport_container.setStyleSheet("background: transparent;")
        transport_layout = QHBoxLayout(transport_container)
        transport_layout.setContentsMargins(0, 5, 0, 5)
        transport_layout.setSpacing(15)
        
        # Create transport buttons
        # Create transport buttons with PNG icons
        def create_transport_btn(icon_path=None, text="", tooltip=""):
            btn = QPushButton()
            btn.setToolTip(tooltip)
            btn.setFixedSize(46, 46)
             # Store the icon path as a property of the button
            if icon_path:
                btn.icon_path = icon_path  # Store for later use
            
            if icon_path and os.path.exists(icon_path):
                # Use PNG icon if available
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(30, 30))
                btn.setText("")  # Clear text if using icon
            else:
                # Fallback to text/emoji
                btn.setText(text)
                btn.setIcon(QIcon())  # Clear icon

            
            btn.setStyleSheet("""
                QPushButton {
                    border-radius: 23px;
                    background-color: #222;
                    font-size: 17px;
                    font-weight: bold;
                    border: 1px solid #444;
                }
                QPushButton:hover {
                    background-color: #333;
                    border: 1px solid #00b4d8;
                }
                QPushButton:pressed {
                    background-color: #111;
                }
            """)
            return btn

        # Create buttons with PNG icons (provide correct paths to your PNG files)
        self.btn_prev = create_transport_btn("icons/prev.png", "⏮", "Previous")
        self.btn_play = create_transport_btn("icons/play.png", "▶", "Play/Pause")
        self.btn_next = create_transport_btn("icons/next.png", "⏭", "Next")
        
        self.btn_play.pause_icon_path = "icons/pause.png"
        
        self.btn_prev.clicked.connect(self.prev)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_next.clicked.connect(self.next)
        # self.btn_stop.clicked.connect(self.stop)
        
        # Center the transport buttons
        transport_layout.addStretch()
        transport_layout.addWidget(self.btn_prev)
        transport_layout.addWidget(self.btn_play)
        transport_layout.addWidget(self.btn_next)
        #transport_layout.addWidget(self.btn_stop)
        transport_layout.addStretch()
        
        progress_layout.addWidget(transport_container)
        
        # Connect signals for progress bar
        self.progress_bar.sliderPressed.connect(self.start_seeking)
        self.progress_bar.sliderReleased.connect(self.end_seeking)
        self.progress_bar.sliderMoved.connect(self.update_seek_preview)
        
        right_panel.addWidget(progress_frame)

        content_layout.addLayout(right_panel, 2)
        main_layout.addLayout(content_layout)

        # ===== REMOVED BOTTOM CONTROL PANEL =====
        # (Transport controls are now in the progress_frame area)

    def show_loading(self, filename):
        self.loading_label.setText(f"Loading: {filename}...")
        self.loading_label.setVisible(True)

    def hide_loading(self, filename):
        self.loading_label.setText("")
        self.loading_label.setVisible(False)

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if not folder:
            return

        self.files.clear()
        self.durations.clear()
        self.table.setRowCount(0)

        for f in os.listdir(folder):
            if f.lower().endswith((".mp3", ".wav", ".flac", ".ogg", ".m4a")):
                file_path = os.path.join(folder, f)
                
                # Get duration - FIXED: Try multiple methods to avoid MP3 errors
                duration = 0
                try:
                    # Method 1: Try librosa first
                    duration = librosa.get_duration(path=file_path)
                except Exception as e:
                    print(f"Librosa error for {f}: {e}")
                    try:
                        # Method 2: Try loading with shorter duration
                        y, sr = librosa.load(file_path, mono=True, sr=22050, duration=30)
                        duration = librosa.get_duration(y=y, sr=sr)
                    except Exception as e2:
                        print(f"Alternative method error for {f}: {e2}")
                        try:
                            # Method 3: Use mutagen as fallback (install with: pip install mutagen)
                            from mutagen import File
                            audio = File(file_path)
                            if audio is not None:
                                duration = audio.info.length
                            else:
                                duration = 0
                        except ImportError:
                            duration = 0
                        except Exception as e3:
                            print(f"Mutagen error for {f}: {e3}")
                            duration = 0
                
                self.durations.append(duration)
                self.files.append(file_path)
                
                r = self.table.rowCount()
                self.table.insertRow(r)
                
                # Track name with gray disc icon
                track_item = QTableWidgetItem(f"💿 {f}")
                track_item.setData(Qt.UserRole, file_path)
                self.table.setItem(r, 0, track_item)
                
                # Display duration immediately
                if duration > 0:
                    mins = int(duration // 60)
                    secs = int(duration % 60)
                    duration_text = f"{mins:02d}:{secs:02d}"
                else:
                    duration_text = "--:--"
                
                duration_item = QTableWidgetItem(duration_text)
                duration_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(r, 1, duration_item)

    def clear_playlist(self):
        self.files.clear()
        self.durations.clear()
        self.table.setRowCount(0)
        self.stop()

    def play_selected(self, row=None):
        if row is None:
            row = self.table.currentRow()
        
        if 0 <= row < len(self.files):
            # Clear previous playing track highlight
            for i in range(self.table.rowCount()):
                # Clear playing flag from all items
                for col in range(2):
                    item = self.table.item(i, col)
                    if item:
                        item.setData(Qt.UserRole + 1, None)  # Clear playing flag
                        
                # Reset track disc to gray for non-playing tracks
                track_item = self.table.item(i, 0)
                if track_item:
                    text = track_item.text()
                    # Remove any color emoji and set back to CD emoji
                    if "🔴" in text or "🟢" in text or "🔵" in text or "🟡" in text or "🟣" in text or "🟠" in text:
                        # Extract just the filename
                        parts = text.split(" ", 1)
                        if len(parts) > 1:
                            track_item.setText(f"💿 {parts[1]}")
            
            self.current_file_index = row
            file_path = self.files[row]
            
            if self.audio.load(file_path):
                self.title_label.setText(f"🎧 {os.path.basename(file_path)}")
                
                if not self.audio.isRunning():
                    self.audio.start()
                
                self.audio.running = True
                #self.btn_play.setText("⏸")
                self.update_play_button_icon(playing=True)

                
                # Update duration display - use the actual duration from audio thread
                mins = int(self.audio.duration // 60)
                secs = int(self.audio.duration % 60)
                duration_text = f"{mins:02d}:{secs:02d}"
                
                # Update duration in table (in case it was --:--)
                duration_item = self.table.item(row, 1)
                if duration_item:
                    duration_item.setText(duration_text)
                
                # Store the actual duration
                self.durations[row] = self.audio.duration
                
                # Update progress bar duration
                self.duration_label.setText(duration_text)
                
                # Reset progress
                self.progress_bar.setValue(0)
                
                # Highlight playing track with colorful disc
                track_item = self.table.item(row, 0)
                if track_item:
                    # Get current text (remove the 💿 if present)
                    current_text = track_item.text()
                    parts = current_text.split(" ", 1)
                    filename = parts[1] if len(parts) > 1 else current_text
                    
                    # Choose a color based on track index (rotating colors)
                    colors = ["🔴", "🟢", "🔵", "🟡", "🟣", "🟠"]  # Red, Green, Blue, Yellow, Purple, Orange
                    color_index = row % len(colors)
                    colorful_disc = colors[color_index]
                    
                    # Set colorful disc
                    track_item.setText(f"{colorful_disc} {filename}")
                    
                    # Set playing flag for styling
                    track_item.setData(Qt.UserRole + 1, "playing")
                
                # Also highlight duration cell
                if duration_item:
                    duration_item.setData(Qt.UserRole + 1, "playing")
                
                # Select the row for visual feedback
                self.table.selectRow(row)
                
                # Force style update
                self.table.viewport().update()

    # def toggle_play(self):
    #     if self.audio.mono is None and self.files:
    #         self.play_selected(0)
    #     elif self.audio.mono is not None:
    #         if self.audio.running:
    #             # Pause playback
    #             self.audio.running = False
    #             self.btn_play.setText("▶")
    #         else:
    #             # Resume playback
    #             self.audio.running = True
    #             self.btn_play.setText("⏸")
    
    # Update toggle_play to also clear text:
    def toggle_play(self):
        print(f"toggle_play called. audio.mono: {self.audio.mono is not None}, audio.running: {self.audio.running}, audio.isRunning(): {self.audio.isRunning()}")
        
        if self.audio.mono is None and self.files:
            print("No audio loaded, loading first track")
            self.play_selected(0)
        elif self.audio.mono is not None:
            if self.audio.running:
                print("Pausing playback")
                self.audio.running = False
                self.update_play_button_icon(playing=False)
            else:
                print("Resuming playback")
                self.audio.running = True
                self.update_play_button_icon(playing=True)
                
                # Make sure the audio thread is actually running
                if not self.audio.isRunning():
                    print("Audio thread not running, starting it...")
                    self.audio.start()
                else:
                    print("Audio thread is already running")

    def update_play_button_icon(self, playing):
        """Update play button icon based on playback state"""
        if playing:
            # Show pause icon
            if hasattr(self.btn_play, 'pause_icon_path') and os.path.exists(self.btn_play.pause_icon_path):
                self.btn_play.setIcon(QIcon(self.btn_play.pause_icon_path))
        else:
            # Show play icon
            if hasattr(self.btn_play, 'icon_path') and os.path.exists(self.btn_play.icon_path):
                self.btn_play.setIcon(QIcon(self.btn_play.icon_path))
        self.btn_play.setText("")  # Always clear text


    def stop(self):
        self.audio.running = False
        #self.btn_play.setText("▶")
        self.update_play_button_icon(playing=False)

        self.progress_bar.setValue(0)
        self.current_time_label.setText("00:00")
        
        # Reset all tracks to CD emoji
        if self.current_file_index >= 0:
            for i in range(self.table.rowCount()):
                track_item = self.table.item(i, 0)
                if track_item:
                    text = track_item.text()
                    # Replace any colorful disc with CD emoji
                    if "🔴" in text or "🟢" in text or "🔵" in text or "🟡" in text or "🟣" in text or "🟠" in text:
                        parts = text.split(" ", 1)
                        if len(parts) > 1:
                            track_item.setText(f"💿 {parts[1]}")
                    track_item.setData(Qt.UserRole + 1, None)  # Clear playing flag
                
                duration_item = self.table.item(i, 1)
                if duration_item:
                    duration_item.setData(Qt.UserRole + 1, None)  # Clear playing flag
        
        self.table.viewport().update()

    def next(self):
        if not self.files:
            return
        next_index = (self.current_file_index + 1) % len(self.files)
        self.table.selectRow(next_index)
        self.play_selected(next_index)

    def prev(self):
        if not self.files:
            return
        prev_index = (self.current_file_index - 1) % len(self.files)
        self.table.selectRow(prev_index)
        self.play_selected(prev_index)

    # ===== SEEKING LOGIC =====
    def start_seeking(self):
        self.user_is_seeking = True

    def update_seek_preview(self, value):
        if self.audio.mono is not None and self.audio.duration > 0:
            position = (value / 10000.0) * self.audio.duration
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")

    def end_seeking(self):
        if self.audio.mono is not None and self.audio.duration > 0:
            value = self.progress_bar.value()
            position = (value / 10000.0) * self.audio.duration
            
            print(f"Seeking to position: {position:.2f} seconds")
            
            self.audio.seek(position)
            
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")
            
            if not self.audio.running:
                self.audio.running = True
                # Update to pause icon when resuming from seek
                self.update_play_button_icon(playing=True)
            
            self.user_is_seeking = False

    def update_progress_from_audio(self, position):
        if not self.user_is_seeking and self.audio.mono is not None and self.audio.duration > 0:
            value = int((position / self.audio.duration) * 10000)
            self.progress_bar.setValue(value)
            
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")
            
            if position >= self.audio.duration - 0.5:
                self.next()

    def update_visualizer(self):
        self.spectrum.update()

    def closeEvent(self, e):
        self.audio.stop()
        if self.audio.isRunning():
            self.audio.terminate()
            self.audio.wait()
        e.accept()


# ================= MAIN =================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    w = MusicPlayer()
    w.show()
    
    sys.exit(app.exec_())
