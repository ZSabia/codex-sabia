"""Testes de estado da interface; não usam rede nem reproduzem áudio."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

spec = importlib.util.spec_from_file_location('sabiacast', Path(__file__).parents[1] / 'sabiacast.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
app = QApplication.instance() or QApplication([])


class ControlsTest(unittest.TestCase):
    def setUp(self):
        self.patches = [patch.object(m, 'get_my_info', return_value=('1', 'test', 'Test')),
                        patch.object(m.TwitchApp, 'load_followed_streams'),
                        patch.object(m.TwitchApp, '_load_usable_emotes'),
                        patch.object(m.StreamTab, 'start_stream_and_chat'),
                        patch.object(m.vlc, 'Instance', side_effect=lambda *a: MagicMock())]
        for p in self.patches:
            p.start()
        self.window = m.TwitchApp()
        self.window.open_channel_tab('one')
        self.first = self.window.tab_widget.currentWidget()
        self.window.open_channel_tab('two')
        self.second = self.window.tab_widget.currentWidget()
        self.window.show()
        app.processEvents()

    def tearDown(self):
        self.window.close()
        app.processEvents()
        for p in reversed(self.patches):
            p.stop()

    def test_volume_and_mute_are_independent(self):
        self.first.volume_slider.setValue(35)
        self.first.mute_button.setChecked(True)
        self.window.cycle_tab(1)
        self.assertEqual(self.first.volume, 35)
        self.assertEqual(self.second.volume, 100)
        self.first.media_player.audio_set_mute.assert_called_with(True)
        self.window.cycle_tab(1)
        self.second.media_player.audio_set_mute.assert_called_with(False)

    def test_cinema_restores_sidebar_and_chat(self):
        self.window.toggle_cinema()
        self.assertTrue(self.window.sidebar.isHidden())
        self.assertTrue(self.first.chat_widget.isHidden())
        self.window.cycle_tab(1)
        self.assertTrue(self.first.chat_widget.isHidden())
        self.window.leave_view_modes()
        self.assertFalse(self.window.sidebar.isHidden())
        self.assertFalse(self.first.chat_widget.isHidden())

    def test_pip_returns_same_frame_and_closes_with_tab(self):
        frame = self.second.video_frame
        self.second.toggle_pip()
        self.assertIs(frame.parentWidget(), self.second.pip_window)
        self.second.pip_window.close()
        self.assertIs(self.second.video_frame, frame)
        self.assertIsNone(self.second.pip_window)
        self.assertIs(frame.parentWidget(), self.second.video_layout.parentWidget())
        self.second.toggle_pip()
        self.window.close_tab_at_index(1)
        self.assertIsNone(self.second.pip_window)

    def test_shortcuts_with_chat_focus(self):
        self.window.activateWindow()
        self.second.input_chat.setFocus()
        app.processEvents()
        QTest.keyClick(self.second.input_chat, Qt.Key.Key_Down, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(self.second.volume, 95)
        QTest.keyClick(self.second.input_chat, Qt.Key.Key_M, Qt.KeyboardModifier.ControlModifier)
        self.assertTrue(self.second.user_muted)


if __name__ == '__main__':
    unittest.main()
