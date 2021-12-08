"""

Copyright (c) 2021 xqmmcqs.
"""

from threading import Thread
import unittest
import json
from app import app


class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app
        app.config['TESTING'] = True
        self.client = app.test_client()

    def pressure(self, index):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertIn("token", json_data)
        token = json_data["token"]

        response = self.client.get("/register",
                                   query_string={"username": f"test{index}", "passwd": f"test{index}", "token": token})
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertIn("token", json_data)
        token = json_data["token"]

        for i in range(1, 100):
            response = self.client.get("/send", query_string={"msg": "改名", "token": token})
            self.assertEqual(response.status_code, 200)
            json_data = json.loads(response.data)
            self.assertIn("msg", json_data)
            self.assertEqual(json_data["msg"][0], "请输入您的新名字，不超过30个字符")

            response = self.client.get("/send", query_string={"msg": f"测试用户{index}", "token": token})
            self.assertEqual(response.status_code, 200)
            json_data = json.loads(response.data)
            self.assertIn("msg", json_data)
            self.assertEqual(json_data["msg"][0], f"您的新名字为测试用户{index}")
            self.assertEqual(json_data["msg"][1], f"你好，测试用户{index}")

    def test_connect(self):
        pool = []
        for i in range(100):
            pool.append(Thread(target=self.pressure, args=[i]))
            pool[-1].start()
        for i in range(100):
            pool[i].join()


if __name__ == '__main__':
    unittest.main()
