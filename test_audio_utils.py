import unittest
import tempfile
import os
import shutil
import numpy as np

from audio_utils import (
    super_clean, 
    is_silent, 
    create_session_folder, 
    create_segment_folder, 
    save_result
)

class TestAudioUtils(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_super_clean_tags(self):
        self.assertEqual(super_clean("[zh]你好<|EMO|>"), "你好")
        self.assertEqual(super_clean("这是一个[测试]句子"), "这是一个句子")

    def test_super_clean_garbage(self):
        self.assertEqual(super_clean("Yeah这个非常好Okay"), "这个非常好")
        self.assertEqual(super_clean("nospeech"), "")
        self.assertEqual(super_clean("This is HAPPY and SAD"), "This is  and")

    def test_super_clean_empty(self):
        self.assertEqual(super_clean(""), "")
        self.assertEqual(super_clean("[zh]"), "")
        self.assertEqual(super_clean("   "), "")

    def test_is_silent_true(self):
        # create silent audio
        audio_data = np.zeros(16000, dtype=np.int16).tobytes()
        self.assertTrue(is_silent(audio_data))

    def test_is_silent_false(self):
        # create loud audio
        audio_data = np.full(16000, 1000, dtype=np.int16).tobytes()
        self.assertFalse(is_silent(audio_data))

    def test_create_session_folder(self):
        session_name = "test_session"
        session_dir = create_session_folder(self.test_dir, session_name)
        self.assertTrue(os.path.exists(session_dir))
        self.assertEqual(os.path.basename(session_dir), session_name)

    def test_create_session_folder_duplicate(self):
        session_name = "test_session"
        # First creation
        dir1 = create_session_folder(self.test_dir, session_name)
        # Second creation should append timestamp
        dir2 = create_session_folder(self.test_dir, session_name)
        
        self.assertTrue(os.path.exists(dir1))
        self.assertTrue(os.path.exists(dir2))
        self.assertNotEqual(dir1, dir2)
        self.assertTrue(os.path.basename(dir2).startswith(session_name + "_"))

    def test_create_segment_folder_naming(self):
        session_name = "test_session"
        session_dir = create_session_folder(self.test_dir, session_name)
        segment_dir = create_segment_folder(session_dir)
        
        self.assertTrue(os.path.exists(segment_dir))
        self.assertEqual(os.path.dirname(segment_dir), session_dir)
        self.assertTrue(session_name in os.path.basename(segment_dir))

    def test_save_result(self):
        session_name = "test_session"
        session_dir = create_session_folder(self.test_dir, session_name)
        segment_dir = create_segment_folder(session_dir)
        
        text = "Hello World"
        file_path = save_result(segment_dir, text)
        
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), text)

    def test_save_result_chinese(self):
        session_name = "test_session"
        session_dir = create_session_folder(self.test_dir, session_name)
        segment_dir = create_segment_folder(session_dir)
        
        text = "语音识别测试结果"
        file_path = save_result(segment_dir, text)
        
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), text)

if __name__ == '__main__':
    unittest.main()
