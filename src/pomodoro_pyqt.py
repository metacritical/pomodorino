#!/usr/bin/env python3
"""
Pomodoro Timer Application - Merged UI with Fullscreen Mode
"""

import sys
import os
import time
import platform
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QProgressBar, QSystemTrayIcon, 
                             QMenu, QAction, QInputDialog, QListWidget, QListWidgetItem, 
                             QAbstractItemView)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QBrush, QColor
import subprocess


class TimerThread(QThread):
    """
    Thread to handle the timer in the background
    """
    time_updated = pyqtSignal(int)  # seconds remaining
    timer_ended = pyqtSignal()

    def __init__(self, duration):
        super().__init__()
        self.duration = duration
        self.remaining = duration
        self.running = False
        self.should_stop = False

    def run(self):
        self.running = True
        self.remaining = self.duration

        while self.remaining > 0 and self.running and not self.should_stop:
            self.time_updated.emit(self.remaining)
            time.sleep(1)
            self.remaining -= 1

        if self.remaining <= 0:
            self.timer_ended.emit()

    def pause(self):
        self.running = False

    def resume(self):
        self.running = True

    def stop(self):
        self.should_stop = True
        self.running = False


class PomodoroApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Timer constants
        self.POMODORO_DURATION = 25 * 60  # 25 minutes in seconds
        self.SHORT_BREAK = 5 * 60         # 5 minutes in seconds
        self.LONG_BREAK = 15 * 60         # 15 minutes in seconds
        self.POMODOROS_BEFORE_LONG_BREAK = 4

        # Timer variables
        self.current_session = "Work"
        self.pomodoro_count = 0
        self.remaining_time = self.POMODORO_DURATION
        self.timer_thread = None
        self.is_paused = False
        self.timer_running = False
        self.is_fullscreen = False

        # Task management
        self.tasks = []

        # Store references to fullscreen widgets
        self.fs_time_label = None
        self.fs_session_label = None
        self.fs_count_label = None
        self.fs_pause_button = None
        self.fs_reset_button = None

        # Set up the UI
        self.init_ui()

        # Create the system tray icon
        self.create_system_tray()

        # Ensure resources are cleaned up on app quit
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.cleanup)

    def init_ui(self):
        # Normal window (original view)
        self.setWindowTitle("Pomodoro Timer")

        # Get screen geometry to center the window
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - 600) // 2
        y = (screen_geometry.height() - 700) // 2
        self.setGeometry(x, y, 600, 700)
        self.setFixedSize(600, 700)

        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main vertical layout
        main_layout = QVBoxLayout()

        # Top section: Timer UI (original view)
        timer_layout = QVBoxLayout()
        timer_layout.setAlignment(Qt.AlignCenter)

        # Title
        title_label = QLabel("Pomodoro Timer")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        timer_layout.addWidget(title_label)

        # Session type label
        self.session_label = QLabel("Work Session")
        self.session_label.setAlignment(Qt.AlignCenter)
        self.session_label.setFont(QFont("Arial", 14))
        timer_layout.addWidget(self.session_label)

        # Timer display
        self.time_label = QLabel("25:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont("Arial", 24, QFont.Bold))
        timer_layout.addWidget(self.time_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        timer_layout.addWidget(self.progress_bar)

        # Pomodoro counter
        self.count_label = QLabel(f"Sessions completed: {self.pomodoro_count} 🍅")
        self.count_label.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(self.count_label)

        # Control buttons (simplified - only Start and Reset)
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.on_primary_button_clicked)
        button_layout.addWidget(self.start_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("resetButton")
        self.reset_button.clicked.connect(self.reset_timer)
        button_layout.addWidget(self.reset_button)

        timer_layout.addLayout(button_layout)

        # Session selection buttons
        session_layout = QHBoxLayout()

        work_button = QPushButton("Work")
        work_button.clicked.connect(lambda: self.set_session("Work"))
        session_layout.addWidget(work_button)

        short_break_button = QPushButton("Short Break")
        short_break_button.clicked.connect(lambda: self.set_session("Short Break"))
        session_layout.addWidget(short_break_button)

        long_break_button = QPushButton("Long Break")
        long_break_button.clicked.connect(lambda: self.set_session("Long Break"))
        session_layout.addWidget(long_break_button)

        timer_layout.addLayout(session_layout)

        main_layout.addLayout(timer_layout)

        # Apply colorful button styles (original)
        self.setStyleSheet("""
            QPushButton#startButton {
                background-color: #2ecc71; color: #ffffff; border: none;
                padding: 10px 22px; border-radius: 12px; font-weight: 600;
            }
            QPushButton#startButton:hover { background-color: #27ae60; }
            QPushButton#resetButton {
                background-color: #3498db; color: #ffffff; border: none;
                padding: 10px 22px; border-radius: 12px; font-weight: 600;
            }
            QPushButton#resetButton:hover { background-color: #2e86c1; }
        """)

        # Bottom section: Task Management (original view)
        task_layout = QVBoxLayout()

        task_title_label = QLabel("Tasks")
        task_title_label.setFont(QFont("Arial", 16, QFont.Bold))
        task_title_label.setAlignment(Qt.AlignCenter)
        task_layout.addWidget(task_title_label)

        # Task list
        self.task_list = QListWidget()
        self.task_list.setSelectionMode(QAbstractItemView.SingleSelection)
        task_layout.addWidget(self.task_list)

        # Task buttons
        task_button_layout = QHBoxLayout()

        self.add_task_button = QPushButton("Add Task")
        self.add_task_button.clicked.connect(self.add_task)
        task_button_layout.addWidget(self.add_task_button)

        self.edit_task_button = QPushButton("Edit Task")
        self.edit_task_button.clicked.connect(self.edit_task)
        task_button_layout.addWidget(self.edit_task_button)

        self.delete_task_button = QPushButton("Delete Task")
        self.delete_task_button.clicked.connect(self.delete_task)
        task_button_layout.addWidget(self.delete_task_button)

        task_layout.addLayout(task_button_layout)

        main_layout.addLayout(task_layout)

        self.central_widget.setLayout(main_layout)

    def _log(self, *args):
        try:
            log_file = os.path.expanduser('~/Library/Logs/PomodoroTimer.log')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, 'a') as f:
                f.write(' '.join(str(a) for a in args) + '\n')
        except Exception:
            pass

    def _resource_path(self, relative_path: str) -> str:
        """Get absolute path to resource"""
        base_path = getattr(sys, '_MEIPASS', None)
        if base_path:
            return os.path.join(base_path, relative_path)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

    def create_system_tray(self):
        """Create system tray icon and menu"""
        from PyQt5.QtCore import QTimer

        available = QSystemTrayIcon.isSystemTrayAvailable()
        self._log('Tray available:', available)

        self.tray_icon = QSystemTrayIcon(self)

        # Create icon
        icon_path = self._resource_path("pomodoro.png")
        self._log('Icon path:', icon_path, 'exists:', os.path.exists(icon_path))
        original_pixmap = QPixmap(icon_path)

        if original_pixmap.isNull():
            fallback = QPixmap(32, 32)
            fallback.fill(Qt.transparent)
            painter = QPainter(fallback)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(220, 20, 60)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 32, 32)
            painter.end()
            original_pixmap = fallback

        scaled_pixmap = original_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon = QIcon(scaled_pixmap)
        self.tray_icon.setIcon(icon)

        # Create context menu
        tray_menu = QMenu()

        self.show_action = QAction("Show", self)
        self.show_action.triggered.connect(self.show_main_window)
        tray_menu.addAction(self.show_action)

        self.quit_action = QAction("Quit", self)
        self.quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.update_tray_tooltip()
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        def show_tray_icon():
            if not self.tray_icon.isVisible():
                self.tray_icon.show()
                self._log("System tray icon shown")

        show_tray_icon()
        QTimer.singleShot(100, show_tray_icon)
        QTimer.singleShot(300, show_tray_icon)

    def update_tray_tooltip(self):
        """Update tray icon tooltip with current timer status"""
        if self.timer_running:
            status = f"{self.current_session}: {self.format_time(self.remaining_time)}"
        else:
            status = "Pomodoro Timer - Ready"
        self.tray_icon.setToolTip(status)

    def on_primary_button_clicked(self):
        """Handle Start/Pause/Resume with a single button in normal view"""
        if self.timer_thread is None or self.timer_thread.isFinished():
            # Start
            self.start_timer()
            # If we stayed in normal view, reflect state
            if hasattr(self, 'start_button') and self.start_button:
                self.start_button.setText("Pause")
            return
        # Toggle pause/resume
        if self.timer_thread.running:
            self.pause_timer()
            if hasattr(self, 'start_button') and self.start_button:
                self.start_button.setText("Resume")
        else:
            self.resume_timer()
            if hasattr(self, 'start_button') and self.start_button:
                self.start_button.setText("Pause")

    def on_tray_icon_activated(self, reason):
        """Handle system tray icon activation"""
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_main_window()

    def show_main_window(self):
        """Bring the main window to the front"""
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """Override close event to minimize to system tray"""
        event.ignore()
        self.hide()

    def quit_app(self):
        """Quit the application completely"""
        self.cleanup()
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, QApplication.instance().quit)

    def cleanup(self):
        """Cleanly stop threads and tear down tray"""
        try:
            if self.timer_thread:
                self.timer_thread.stop()
                self.timer_thread.wait()
                self.timer_thread = None
        except Exception:
            pass
        try:
            if hasattr(self, 'tray_icon') and self.tray_icon is not None:
                self.tray_icon.hide()
                self.tray_icon.deleteLater()
                self.tray_icon = None
        except Exception:
            pass

    def format_time(self, seconds):
        """Format seconds to MM:SS format"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def set_session(self, session_type):
        """Set the current session type"""
        self.current_session = session_type

        if session_type == "Work":
            self.remaining_time = self.POMODORO_DURATION
        elif session_type == "Short Break":
            self.remaining_time = self.SHORT_BREAK
        else:  # Long Break
            self.remaining_time = self.LONG_BREAK

        self.update_display()

    def start_timer(self):
        """Start the timer and go fullscreen"""
        if self.timer_thread is None or self.timer_thread.isFinished():
            # Determine duration
            if self.current_session == "Work":
                duration = self.POMODORO_DURATION
            elif self.current_session == "Short Break":
                duration = self.SHORT_BREAK
            else:
                duration = self.LONG_BREAK

            self.timer_thread = TimerThread(duration)
            self.timer_thread.time_updated.connect(self.update_time)
            self.timer_thread.timer_ended.connect(self.timer_ended)
            self.timer_thread.start()

            self.timer_running = True
            self.is_paused = False
            self.is_fullscreen = True

            # Go fullscreen with large timer view
            self.showFullScreen()
            self.setup_fullscreen_ui()

            # Update tray
            self.update_tray_tooltip()
        else:
            self.reset_timer()
            return self.start_timer()

    def setup_fullscreen_ui(self):
        """Setup fullscreen UI with large timer"""
        # Create a new widget for fullscreen
        fullscreen_widget = QWidget()
        self.setCentralWidget(fullscreen_widget)

        # Create fullscreen layout
        fullscreen_layout = QVBoxLayout(fullscreen_widget)
        fullscreen_layout.setContentsMargins(0, 20, 0, 20)
        fullscreen_layout.setSpacing(20)

        # Apply black background to central widget and main window
        black_style = "background-color: #000000;"
        fullscreen_widget.setStyleSheet(black_style)
        self.setStyleSheet(black_style)

        # Top: X button to exit fullscreen
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        exit_button = QPushButton("✕")
        exit_button.setFixedSize(60, 60)
        exit_button.setFont(QFont("Arial", 24, QFont.Bold))
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 30px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        exit_button.clicked.connect(self.exit_fullscreen)
        top_layout.addWidget(exit_button)
        top_layout.setContentsMargins(20, 0, 20, 0)
        fullscreen_layout.addLayout(top_layout)

        # Center: Large timer
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignCenter)

        # Session label (large)
        self.fs_session_label = QLabel(self.current_session + " Session")
        self.fs_session_label.setAlignment(Qt.AlignCenter)
        self.fs_session_label.setFont(QFont("Arial", 32, QFont.Bold))
        self.fs_session_label.setStyleSheet("color: #2c3e50; background-color: #000000;")
        center_layout.addWidget(self.fs_session_label)

        # Timer display (very large)
        self.fs_time_label = QLabel(self.format_time(self.remaining_time))
        self.fs_time_label.setAlignment(Qt.AlignCenter)
        self.fs_time_label.setFont(QFont("Arial", 120, QFont.Bold))
        self.fs_time_label.setStyleSheet("color: #e74c3c; background-color: #000000;")
        center_layout.addWidget(self.fs_time_label)

        # Counter
        self.fs_count_label = QLabel(f"Sessions completed: {self.pomodoro_count} 🍅")
        self.fs_count_label.setAlignment(Qt.AlignCenter)
        self.fs_count_label.setFont(QFont("Arial", 24))
        self.fs_count_label.setStyleSheet("color: #34495e; background-color: #000000;")
        center_layout.addWidget(self.fs_count_label)

        fullscreen_layout.addLayout(center_layout, 1)

        # Bottom: Control buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.setAlignment(Qt.AlignCenter)
        bottom_layout.setSpacing(20)

        self.fs_pause_button = QPushButton("Pause")
        self.fs_pause_button.setFixedSize(150, 60)
        self.fs_pause_button.setFont(QFont("Arial", 18, QFont.Bold))
        self.fs_pause_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #d68910;
            }
        """)
        self.fs_pause_button.clicked.connect(self.toggle_pause_fullscreen)
        bottom_layout.addWidget(self.fs_pause_button)

        self.fs_reset_button = QPushButton("Reset")
        self.fs_reset_button.setFixedSize(150, 60)
        self.fs_reset_button.setFont(QFont("Arial", 18, QFont.Bold))
        self.fs_reset_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #2e86c1;
            }
        """)
        self.fs_reset_button.clicked.connect(self.exit_fullscreen)
        bottom_layout.addWidget(self.fs_reset_button)

        bottom_layout.setContentsMargins(0, 0, 0, 40)
        fullscreen_layout.addLayout(bottom_layout)

    

    def toggle_pause_fullscreen(self):
        """Toggle pause in fullscreen"""
        if self.timer_thread:
            if self.is_paused:
                self.timer_thread.resume()
                self.is_paused = False
                self.fs_pause_button.setText("Pause")
            else:
                self.timer_thread.pause()
                self.is_paused = True
                self.fs_pause_button.setText("Resume")

    def exit_fullscreen(self):
        """Exit fullscreen and return to normal view"""
        self.reset_timer()

    def pause_timer(self):
        """Pause in normal view (no-op UI updates since only two buttons)"""
        if self.timer_thread and self.timer_thread.running:
            self.timer_thread.pause()

    def resume_timer(self):
        """Resume in normal view (no-op UI updates since only two buttons)"""
        if self.timer_thread and not self.timer_thread.running:
            self.timer_thread.resume()

    def reset_timer(self):
        """Reset the timer"""
        if self.timer_thread:
            self.timer_thread.stop()
            self.timer_thread.wait()
            self.timer_thread = None

        self.timer_running = False
        self.is_paused = False
        self.is_fullscreen = False

        # Reset time
        if self.current_session == "Work":
            self.remaining_time = self.POMODORO_DURATION
        elif self.current_session == "Short Break":
            self.remaining_time = self.SHORT_BREAK
        else:
            self.remaining_time = self.LONG_BREAK

        # Exit fullscreen and restore original view
        self.showNormal()
        self.restore_normal_ui()
        self.update_display()
        self.update_tray_tooltip()

    def restore_normal_ui(self):
        """Restore the original normal UI"""
        # Create a new widget for normal view
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Recreate normal layout
        main_layout = QVBoxLayout()

        timer_layout = QVBoxLayout()
        timer_layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("Pomodoro Timer")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        timer_layout.addWidget(title_label)

        self.session_label = QLabel("Work Session")
        self.session_label.setAlignment(Qt.AlignCenter)
        self.session_label.setFont(QFont("Arial", 14))
        timer_layout.addWidget(self.session_label)

        self.time_label = QLabel(self.format_time(self.remaining_time))
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont("Arial", 24, QFont.Bold))
        timer_layout.addWidget(self.time_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        timer_layout.addWidget(self.progress_bar)

        self.count_label = QLabel(f"Sessions completed: {self.pomodoro_count} 🍅")
        self.count_label.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(self.count_label)

        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.on_primary_button_clicked)
        button_layout.addWidget(self.start_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("resetButton")
        self.reset_button.clicked.connect(self.reset_timer)
        button_layout.addWidget(self.reset_button)

        timer_layout.addLayout(button_layout)

        session_layout = QHBoxLayout()

        work_button = QPushButton("Work")
        work_button.clicked.connect(lambda: self.set_session("Work"))
        session_layout.addWidget(work_button)

        short_break_button = QPushButton("Short Break")
        short_break_button.clicked.connect(lambda: self.set_session("Short Break"))
        session_layout.addWidget(short_break_button)

        long_break_button = QPushButton("Long Break")
        long_break_button.clicked.connect(lambda: self.set_session("Long Break"))
        session_layout.addWidget(long_break_button)

        timer_layout.addLayout(session_layout)

        main_layout.addLayout(timer_layout)

        task_layout = QVBoxLayout()

        task_title_label = QLabel("Tasks")
        task_title_label.setFont(QFont("Arial", 16, QFont.Bold))
        task_title_label.setAlignment(Qt.AlignCenter)
        task_layout.addWidget(task_title_label)

        self.task_list = QListWidget()
        self.task_list.setSelectionMode(QAbstractItemView.SingleSelection)
        task_layout.addWidget(self.task_list)

        task_button_layout = QHBoxLayout()

        self.add_task_button = QPushButton("Add Task")
        self.add_task_button.clicked.connect(self.add_task)
        task_button_layout.addWidget(self.add_task_button)

        self.edit_task_button = QPushButton("Edit Task")
        self.edit_task_button.clicked.connect(self.edit_task)
        task_button_layout.addWidget(self.edit_task_button)

        self.delete_task_button = QPushButton("Delete Task")
        self.delete_task_button.clicked.connect(self.delete_task)
        task_button_layout.addWidget(self.delete_task_button)

        task_layout.addLayout(task_button_layout)

        main_layout.addLayout(task_layout)

        self.central_widget.setLayout(main_layout)

        # Restore original styling for normal view
        self.setStyleSheet("""
            QPushButton#startButton {
                background-color: #2ecc71; color: #ffffff; border: none;
                padding: 10px 22px; border-radius: 12px; font-weight: 600;
            }
            QPushButton#startButton:hover { background-color: #27ae60; }
            QPushButton#resetButton {
                background-color: #3498db; color: #ffffff; border: none;
                padding: 10px 22px; border-radius: 12px; font-weight: 600;
            }
            QPushButton#resetButton:hover { background-color: #2e86c1; }
        """)

        # Update task list
        self.update_task_list()

    def update_time(self, seconds):
        """Update the time display"""
        self.remaining_time = seconds
        if self.timer_running and self.is_fullscreen:
            if self.fs_time_label:
                self.fs_time_label.setText(self.format_time(self.remaining_time))
                self.fs_count_label.setText(f"Sessions completed: {self.pomodoro_count} 🍅")
        self.update_tray_tooltip()

    def update_display(self):
        """Update display elements"""
        self.time_label.setText(self.format_time(self.remaining_time))
        self.session_label.setText(f"{self.current_session} Session")
        self.count_label.setText(f"Sessions completed: {self.pomodoro_count} 🍅")

        if self.current_session == "Work":
            total_time = self.POMODORO_DURATION
        elif self.current_session == "Short Break":
            total_time = self.SHORT_BREAK
        else:
            total_time = self.LONG_BREAK

        if total_time > 0:
            progress = ((total_time - self.remaining_time) / total_time) * 100
            self.progress_bar.setValue(int(progress))

    def send_notification(self, title, message):
        """Send platform-specific notifications"""
        system = platform.system()

        if system == "Darwin":
            try:
                subprocess.run([
                    'osascript', '-e', 
                    f'display notification "{message}" with title "{title}"'
                ])
            except:
                print(f"Notification: {title} - {message}")

        elif system == "Linux":
            try:
                subprocess.run(['notify-send', title, message])
            except:
                print(f"Notification: {title} - {message}")

        elif system == "Windows":
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=5, icon_path=None)
            except:
                print(f"Notification: {title} - {message}")
        else:
            print(f"Notification: {title} - {message}")

    def timer_ended(self):
        """Handle timer end"""
        if self.current_session == "Work":
            title = "Pomodoro Session Complete!"
            message = "Time for a break!"
        else:
            title = "Break Time Over!"
            message = "Time to get back to work!"

        self.send_notification(title, message)

        system = platform.system()
        try:
            if system == "Darwin":
                if self.current_session == "Work":
                    subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'])
                else:
                    subprocess.run(['afplay', '/System/Library/Sounds/Ping.aiff'])
            elif system == "Linux":
                try:
                    subprocess.run(['paplay', '/usr/share/sounds/generic.wav'], check=False)
                except:
                    pass
            elif system == "Windows":
                import winsound
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except:
            pass

        if self.current_session == "Work":
            self.pomodoro_count += 1

            if self.pomodoro_count % self.POMODOROS_BEFORE_LONG_BREAK == 0:
                self.current_session = "Long Break"
            else:
                self.current_session = "Short Break"
        else:
            self.current_session = "Work"

        if self.current_session == "Work":
            self.remaining_time = self.POMODORO_DURATION
        elif self.current_session == "Short Break":
            self.remaining_time = self.SHORT_BREAK
        else:
            self.remaining_time = self.LONG_BREAK

        self.timer_running = False
        self.is_paused = False
        self.is_fullscreen = False
        self.showNormal()
        self.restore_normal_ui()
        self.update_display()
        self.update_tray_tooltip()

    def add_task(self):
        """Add a new task"""
        text, ok = QInputDialog.getText(self, 'Add Task', 'Enter task:')
        if ok and text:
            self.tasks.append(text)
            self.update_task_list()

    def edit_task(self):
        """Edit the selected task"""
        current_row = self.task_list.currentRow()
        if current_row >= 0:
            current_task = self.tasks[current_row]
            text, ok = QInputDialog.getText(self, 'Edit Task', 'Edit task:', text=current_task)
            if ok and text:
                self.tasks[current_row] = text
                self.update_task_list()

    def delete_task(self):
        """Delete the selected task"""
        current_row = self.task_list.currentRow()
        if current_row >= 0:
            self.tasks.pop(current_row)
            self.update_task_list()

    def update_task_list(self):
        """Update the task list UI"""
        self.task_list.clear()
        for task in self.tasks:
            item = QListWidgetItem(task)
            self.task_list.addItem(item)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pomodoro Timer")
    app.setApplicationVersion("1.0")
    app.setQuitOnLastWindowClosed(False)

    window = PomodoroApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
