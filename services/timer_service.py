from PySide6.QtCore import QObject, Signal, QTimer

class TimerService(QObject):
    ticked = Signal(int, int)
    phase_changed = Signal(str)
    completed = Signal()

    def __init__(self, config, stats_service=None):
        super().__init__()
        self.config = config
        self.stats = stats_service
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_tick)
        self.sessions_completed = 0
        self.phase = "WORK"
        self._mm = self.config.get("workMinutes", 25)
        self._ss = 0
        self.running = False
        self.pending_next_phase = None
        self._countup_seconds = 0
        self._current_session_seconds = 0

    def _finalize_session(self):
        """
        Check if the current session is valid (>2 mins) and save stats.
        Increments sessions_completed only if valid.
        Resets _current_session_seconds.
        """
        if self.phase == "WORK":
            # Only count if duration >= 2 minutes (120 seconds)
            if self._current_session_seconds >= 120:
                self.sessions_completed += 1
                if self.stats:
                    try:
                        self.stats.add_work_seconds(self._current_session_seconds)
                        self.stats.increment_session()
                        self.stats.flush()
                    except Exception:
                        pass
        self._current_session_seconds = 0

    def start(self):
        if self.pending_next_phase:
            nextp = self.pending_next_phase
            if nextp == "LONG_BREAK":
                self._mm = self.config.get("longBreakMinutes", 15)
                self._ss = 0
            elif nextp == "SHORT_BREAK":
                self._mm = self.config.get("shortBreakMinutes", 5)
                self._ss = 0
            else:
                self._mm = self.config.get("workMinutes", 25)
                self._ss = 0
                self._current_session_seconds = 0  # Reset for new work session
            self.phase = nextp
            self.pending_next_phase = None
            self.phase_changed.emit(self.phase)
            self.ticked.emit(self._mm, self._ss)
        self.running = True
        self.timer.start()

    def pause(self):
        self.running = False
        self.timer.stop()

    def reset(self):
        self._finalize_session()  # Check and save stats if valid
        self.running = False
        self.timer.stop()
        self.pending_next_phase = None
        self.phase = "WORK"
        if self.config.get("countUpMode", False):
            self._mm = 0
            self._ss = 0
        else:
            self._mm = self.config.get("workMinutes", 25)
            self._ss = 0
        self._countup_seconds = 0
        self._current_session_seconds = 0
        self.phase_changed.emit(self.phase)
        self.ticked.emit(self._mm, self._ss)

    def text_end(self):
        # helper to signal end for UI flash logic
        pass

    def set_countup_zero(self):
        self._finalize_session()  # Check and save stats if valid
        self.running = False
        self.timer.stop()
        self._countup_seconds = 0
        self._current_session_seconds = 0
        self.phase = "WORK"
        self.ticked.emit(0, 0)
        self.phase_changed.emit(self.phase)

    def skip(self):
        self._next_phase()

    def _on_tick(self):
        if not self.running:
            return

        # Track duration for stats (for both modes)
        if self.phase == "WORK":
            self._current_session_seconds += 1

        if self.config.get("countUpMode", False):
            # count-up mode: increase seconds, cap at 90 minutes
            self._countup_seconds += 1
            total = self._countup_seconds
            if total >= 90 * 60:
                self._countup_seconds = 90 * 60
                self.running = False
                self.timer.stop()
                self.text_end()
                self.ticked.emit(0, 0)
                self._finalize_session()  # Save stats
                self.completed.emit()
                return
            mm = total // 60
            ss = total % 60
            self.ticked.emit(mm, ss)
            return

        # Tomato Mode logic
        if self._mm == 0 and self._ss == 0:
            self._finalize_session()  # Save stats if valid
            self.completed.emit()

            # Always pause at completion and set the next phase as pending
            nextp = None
            if self.phase == "WORK":
                # sessions_completed was incremented in _finalize_session if valid
                if self.sessions_completed > 0 and self.sessions_completed % self.config.get("sessionsBeforeLongBreak", 4) == 0:
                    nextp = "LONG_BREAK"
                else:
                    nextp = "SHORT_BREAK"
            else:
                nextp = "WORK"
            self.pending_next_phase = nextp
            self.running = False
            self.timer.stop()
            self.ticked.emit(0, 0)
            return
        
        if self._ss == 0:
            self._mm -= 1
            self._ss = 59
        else:
            self._ss -= 1
        self.ticked.emit(self._mm, self._ss)

    def _next_phase(self):
        if self.phase == "WORK":
            self._finalize_session()  # Save stats if valid
            
            if self.sessions_completed > 0 and self.sessions_completed % self.config.get("sessionsBeforeLongBreak", 4) == 0:
                self.phase = "LONG_BREAK"
                self._mm = self.config.get("longBreakMinutes", 15)
                self._ss = 0
            else:
                self.phase = "SHORT_BREAK"
                self._mm = self.config.get("shortBreakMinutes", 5)
                self._ss = 0
        else:
            self.phase = "WORK"
            self._mm = self.config.get("workMinutes", 25)
            self._ss = 0
            self._current_session_seconds = 0  # Reset for new work session
        self.phase_changed.emit(self.phase)
        self.ticked.emit(self._mm, self._ss)
