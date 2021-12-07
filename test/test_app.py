import unittest
import json
from app import app


class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_connect(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertIn("token", json_data)
        token = json_data["token"]

        response = self.client.get("/send", query_string={"msg": "123", "token": ""})
        self.assertEqual(response.status_code, 403)

        response = self.client.get("/send", query_string={"msg": "123"})
        self.assertEqual(response.status_code, 400)

        response = self.client.get("/send", query_string={"msg": "投诉", "token": token})
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertIn("msg", json_data)
        self.assertEqual(json_data["msg"][0], "请输入您的建议，不超过200个字符")

        response = self.client.get("/echo", query_string={"seconds": 60, "token": token})
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertIn("msg", json_data)
        self.assertEqual(json_data["msg"][0], "您已经很久没有操作了，即将返回主菜单")

        response = self.client.get("/send", query_string={"msg": "改名", "token": token})
        self.assertEqual(response.status_code, 401)

        response = self.client.get("/register", query_string={"username": "test1", "passwd": "test1", "token": token})
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertIn("token", json_data)
        token = json_data["token"]

        response = self.client.get("/send", query_string={"msg": "改名", "token": token})
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertIn("msg", json_data)
        self.assertEqual(json_data["msg"][0], "请输入您的新名字，不超过30个字符")

        response = self.client.get("/send", query_string={"msg": "测试用户", "token": token})
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertIn("msg", json_data)
        self.assertEqual(json_data["msg"][0], "您的新名字为测试用户")
        self.assertEqual(json_data["msg"][1], "你好，测试用户")

        response = self.client.get("/send", query_string={"msg": "退出", "token": token})
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertIn("exit", json_data)
        self.assertTrue(json_data["exit"])

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertIn("token", json_data)
        token = json_data["token"]

        response = self.client.get("/login", query_string={"username": "test1", "passwd": "test1", "token": token})
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertIn("token", json_data)


if __name__ == '__main__':
    unittest.main()
