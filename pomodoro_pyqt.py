#!/usr/bin/env python3
"""
Pomodoro Timer Application
"""

import sys
import os
import time
import platform
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QProgressBar, QSystemTrayIcon, 
                             QMenu, QAction, QInputDialog, QListWidget, QListWidgetItem, 
                             QAbstractItemView, QSplitter, QFrame)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPalette, QIcon, QPixmap, QPainter, QBrush, QColor
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
        
        # Task management
        self.tasks = []
        
        # Set up the UI
        self.init_ui()

        # Create the system tray icon immediately for quicker appearance
        self.create_system_tray()

        # Ensure resources are cleaned up on app quit
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.cleanup)
        
    def init_ui(self):
        # Remove window chrome (title bar, borders, etc.)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("Pomodoro Timer")
        
        # Get screen geometry to center the window
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - 600) // 2
        y = (screen_geometry.height() - 700) // 2
        self.setGeometry(x, y, 600, 700)
        self.setFixedSize(600, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main vertical layout
        main_layout = QVBoxLayout()
        
        # Top section: Timer UI
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
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.start_timer)
        button_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setObjectName("pauseButton")
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)

        self.resume_button = QPushButton("Resume")
        self.resume_button.setObjectName("resumeButton")
        self.resume_button.clicked.connect(self.resume_timer)
        self.resume_button.setEnabled(False)
        button_layout.addWidget(self.resume_button)
        
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

        # Apply colorful button styles (green, red, orange, blue)
        self.setStyleSheet("""
            QPushButton#startButton {
                background-color: #2ecc71; color: #ffffff; border: none;
                padding: 10px 22px; border-radius: 12px; font-weight: 600;
            }
            QPushButton#startButton:hover { background-color: #27ae60; }
            QPushButton#pauseButton {
                background-color: #e74c3c; color: #ffffff; border: none;
                padding: 10px 22px; border-radius: 12px; font-weight: 600;
            }
            QPushButton#pauseButton:hover { background-color: #c0392b; }
            QPushButton#resumeButton {
                background-color: #f39c12; color: #ffffff; border: none;
                padding: 10px 22px; border-radius: 12px; font-weight: 600;
            }
            QPushButton#resumeButton:hover { background-color: #d68910; }
            QPushButton#resetButton {
                background-color: #3498db; color: #ffffff; border: none;
                padding: 10px 22px; border-radius: 12px; font-weight: 600;
            }
            QPushButton#resetButton:hover { background-color: #2e86c1; }
        """)
        
        # Bottom section: Task Management
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
        
        central_widget.setLayout(main_layout)
        
        # No custom stylesheet: use system (Qt/Cocoa) theme

        # Add a hide button since we removed the window chrome
        self.hide_button = QPushButton("Hide")
        self.hide_button.setGeometry(self.width() - 60, 10, 50, 25)
        self.hide_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.hide_button.clicked.connect(self.close_to_tray)
        self.hide_button.setParent(central_widget)
        
    def close_to_tray(self):
        """Close to system tray instead of quitting"""
        self.hide()


    def _log(self, *args):
        try:
            log_file = os.path.expanduser('~/Library/Logs/PomodoroTimer.log')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, 'a') as f:
                f.write(' '.join(str(a) for a in args) + '\n')
        except Exception:
            pass

    def _resource_path(self, relative_path: str) -> str:
        """Get absolute path to resource, works for dev and for PyInstaller/macOS app bundle."""
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = getattr(sys, '_MEIPASS', None)
        if base_path:
            return os.path.join(base_path, relative_path)
        # When running from source or inside an app bundle, use the script's directory
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

    def create_system_tray(self):
        """Create system tray icon and menu"""
        from PyQt5.QtCore import QTimer
        
        # Check tray availability and log
        available = QSystemTrayIcon.isSystemTrayAvailable()
        self._log('Tray available:', available)
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Load the pomodoro.png image via a robust path and create a properly sized icon
        icon_path = self._resource_path("pomodoro.png")
        self._log('Icon path:', icon_path, 'exists:', os.path.exists(icon_path))
        original_pixmap = QPixmap(icon_path)
        if original_pixmap.isNull():
            # Fallback: create a simple red circle pixmap if the resource can't be found
            fallback = QPixmap(32, 32)
            fallback.fill(Qt.transparent)
            painter = QPainter(fallback)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(220, 20, 60)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 32, 32)
            painter.end()
            original_pixmap = fallback
        # Scale the image to a larger size for better visibility in system tray (32x32)
        scaled_pixmap = original_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon = QIcon(scaled_pixmap)
        self.tray_icon.setIcon(icon)
        
        # Create context menu
        tray_menu = QMenu()
        # Keep references on self to avoid accidental GC
        self.show_action = QAction("Show", self)
        self.show_action.triggered.connect(self.show_main_window)
        tray_menu.addAction(self.show_action)

        self.quit_action = QAction("Quit", self)
        self.quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(self.quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("Pomodoro Timer")
        
        # Connect double-click to show window
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # Show the tray icon
        # Add retry mechanism for macOS bundled apps
        def show_tray_icon():
            if not self.tray_icon.isVisible():
                self.tray_icon.show()
                self._log("System tray icon shown")
                print("System tray icon shown")  # Debug print
            else:
                self._log("System tray icon already visible")
                print("System tray icon already visible")  # Debug print
        
        # Show immediately and quickly retry a couple times in case the
        # status bar isn’t ready yet during app startup.
        show_tray_icon()
        QTimer.singleShot(100, show_tray_icon)
        QTimer.singleShot(300, show_tray_icon)

    def on_tray_icon_activated(self, reason):
        """Handle system tray icon activation"""
        # On macOS, a single click (Trigger) is typical; support both.
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_main_window()

    def show_main_window(self):
        """Bring the main window to the front and focus it."""
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """Override close event to minimize to system tray instead of quitting"""
        event.ignore()  # Ignore the close event
        self.hide()     # Hide the window instead of closing it

    def quit_app(self):
        """Quit the application completely"""
        self.cleanup()
        # Delay quit slightly to allow deleteLater() to process
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, QApplication.instance().quit)

    def cleanup(self):
        """Cleanly stop threads and tear down tray to avoid macOS aborts on exit."""
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
        """Start the timer"""
        if self.timer_thread is None or self.timer_thread.isFinished():
            # Determine duration based on session type
            if self.current_session == "Work":
                duration = self.POMODORO_DURATION
            elif self.current_session == "Short Break":
                duration = self.SHORT_BREAK
            else:  # Long Break
                duration = self.LONG_BREAK
            
            self.timer_thread = TimerThread(duration)
            self.timer_thread.time_updated.connect(self.update_time)
            self.timer_thread.timer_ended.connect(self.timer_ended)
            self.timer_thread.start()
        
        else:
            # Already initialized; restart fresh instead of overloading Start as Resume
            self.reset_timer()
            return self.start_timer()

        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        if hasattr(self, 'resume_button'):
            self.resume_button.setEnabled(False)

    def pause_timer(self):
        """Pause the timer"""
        if self.timer_thread and self.timer_thread.running:
            self.timer_thread.pause()
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            if hasattr(self, 'resume_button'):
                self.resume_button.setEnabled(True)

    def resume_timer(self):
        """Resume the timer if paused"""
        if self.timer_thread and not self.timer_thread.running:
            self.timer_thread.resume()
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            if hasattr(self, 'resume_button'):
                self.resume_button.setEnabled(False)

    def reset_timer(self):
        """Reset the timer to initial state"""
        if self.timer_thread:
            self.timer_thread.stop()
            self.timer_thread.wait()  # Wait for thread to finish
        
        # Reset based on current session
        if self.current_session == "Work":
            self.remaining_time = self.POMODORO_DURATION
        elif self.current_session == "Short Break":
            self.remaining_time = self.SHORT_BREAK
        else:  # Long Break
            self.remaining_time = self.LONG_BREAK
            
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        if hasattr(self, 'resume_button'):
            self.resume_button.setEnabled(False)
        self.update_display()

    def update_time(self, seconds):
        """Update the time display"""
        self.remaining_time = seconds
        self.update_display()

    def update_display(self):
        """Update all display elements"""
        self.time_label.setText(self.format_time(self.remaining_time))
        self.session_label.setText(f"{self.current_session} Session")
        self.count_label.setText(f"Sessions completed: {self.pomodoro_count} 🍅")
        
        # Update progress bar based on session type
        if self.current_session == "Work":
            total_time = self.POMODORO_DURATION
        elif self.current_session == "Short Break":
            total_time = self.SHORT_BREAK
        else:  # Long Break
            total_time = self.LONG_BREAK
            
        if total_time > 0:
            progress = ((total_time - self.remaining_time) / total_time) * 100
            self.progress_bar.setValue(int(progress))

    def send_notification(self, title, message):
        """Send platform-specific notifications"""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            try:
                subprocess.run([
                    'osascript', '-e', 
                    f'display notification "{message}" with title "{title}"'
                ])
            except:
                # Fallback if osascript fails
                print(f"Notification: {title} - {message}")
                
        elif system == "Linux":  # Linux
            try:
                subprocess.run(['notify-send', title, message])
            except:
                # Fallback if notify-send fails
                print(f"Notification: {title} - {message}")
                
        elif system == "Windows":  # Windows
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=5, icon_path=None)
            except:
                # Fallback if win10toast isn't available
                print(f"Notification: {title} - {message}")
        else:
            print(f"Notification: {title} - {message}")

    def timer_ended(self):
        """Handle what happens when a timer ends"""
        # Determine notification title and message
        if self.current_session == "Work":
            title = "Pomodoro Session Complete!"
            message = "Time for a break! Click here to start your break session."
        else:
            title = "Break Time Over!"
            message = "Break session ended. Time to get back to work!"
        
        # Send platform-specific notification
        self.send_notification(title, message)
        
        # Play system sound based on platform
        system = platform.system()
        try:
            if system == "Darwin":  # macOS
                if self.current_session == "Work":
                    subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'])
                else:
                    subprocess.run(['afplay', '/System/Library/Sounds/Ping.aiff'])
            elif system == "Linux":
                # Try to play a sound using paplay or aplay
                try:
                    subprocess.run(['paplay', '/usr/share/sounds/generic.wav'], check=False)
                except:
                    # Try alternative sound system
                    pass
            elif system == "Windows":
                # On Windows, use winsound
                import winsound
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except:
            # Fallback if sound fails on any platform
            print(f"Could not play sound on {system}")

        # Handle session completion
        if self.current_session == "Work":
            # Work session completed
            self.pomodoro_count += 1
            
            # Check if we need a long break
            if self.pomodoro_count % self.POMODOROS_BEFORE_LONG_BREAK == 0:
                self.current_session = "Long Break"
            else:
                self.current_session = "Short Break"
                
        else:
            # Break session completed, back to work
            self.current_session = "Work"

        # Reset timer for next session
        if self.current_session == "Work":
            self.remaining_time = self.POMODORO_DURATION
        elif self.current_session == "Short Break":
            self.remaining_time = self.SHORT_BREAK
        else:
            self.remaining_time = self.LONG_BREAK

        # Update display
        self.update_display()

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
    # Set application name for macOS
    app.setApplicationName("Pomodoro Timer")
    app.setApplicationVersion("1.0")
    # Ensure the app keeps running in tray when window closes
    app.setQuitOnLastWindowClosed(False)
    
    window = PomodoroApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
