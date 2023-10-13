import unittest
from app import app

class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_process(self):
        response = self.app.get('/process')
        self.assertEqual(response.data.decode(), 'hello world')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
