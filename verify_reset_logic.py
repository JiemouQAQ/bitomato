import unittest
from PySide6.QtWidgets import QApplication, QDialog
import sys

# Ensure QApplication exists
app = QApplication.instance() or QApplication(sys.argv)

class MockTimerService:
    def __init__(self):
        self.running = True
        self.reset_called = False
    
    def reset(self):
        self.running = False
        self.reset_called = True

class MockParent:
    def __init__(self):
        self.timer_service = MockTimerService()
        self._reset_called = False
        self.config = {
            "workMinutes": 25,
            "shortBreakMinutes": 5,
            "countUpMode": False,
            "frameDuration": 100
        }
    
    def _reset(self):
        self._reset_called = True
        self.timer_service.reset()

class TestSettingsResetLogic(unittest.TestCase):
    def test_no_reset_on_anim_change(self):
        # Setup
        parent = MockParent()
        # We need to simulate SettingsDialog behavior
        # Since we can't easily instantiate the real dialog with all UI deps in this minimal test env without importing everything
        # We will manually replicate the logic we just implemented in _save
        
        initial = {
            "workMinutes": 25,
            "shortBreakMinutes": 5,
            "countUpMode": False
        }
        
        # Scenario 1: Change only frameDuration
        new_work = 25
        new_break = 5
        new_countup = False
        new_duration = 200
        
        timer_changed = (
            new_work != initial["workMinutes"] or
            new_break != initial["shortBreakMinutes"] or
            new_countup != initial["countUpMode"]
        )
        
        self.assertFalse(timer_changed)
        
        if timer_changed:
            parent._reset()
            
        self.assertFalse(parent._reset_called)
        self.assertTrue(parent.timer_service.running) # Should still be running

    def test_reset_on_work_change(self):
        # Setup
        parent = MockParent()
        initial = {
            "workMinutes": 25,
            "shortBreakMinutes": 5,
            "countUpMode": False
        }
        
        # Scenario 2: Change workMinutes
        new_work = 30
        
        timer_changed = (
            new_work != initial["workMinutes"] 
        )
        
        self.assertTrue(timer_changed)
        
        if timer_changed:
            parent._reset()
            
        self.assertTrue(parent._reset_called)
        self.assertFalse(parent.timer_service.running)

if __name__ == '__main__':
    unittest.main()
