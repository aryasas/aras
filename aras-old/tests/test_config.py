import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DevelopmentConfig, TestingConfig, config


class TestConfig(unittest.TestCase):
    def test_config_registry(self):
        self.assertIn("development", config)
        self.assertIn("testing", config)

    def test_dev_sqlalchemy_uri(self):
        uri = DevelopmentConfig.SQLALCHEMY_DATABASE_URI
        if uri:
            self.assertIn("mariadb", uri)

    def test_testing_config(self):
        self.assertTrue(TestingConfig.TESTING)


if __name__ == "__main__":
    unittest.main()
