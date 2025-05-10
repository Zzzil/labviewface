import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import requests
import base64
import json
from PIL import Image, ImageEnhance, ImageTk
import cv2
import numpy as np
import os

# 百度智能云手势识别 API 的相关配置
API_KEY = "LRR4zXxAW2HtlxL2QBcH1d"  # 更新为您提供的手势识别 API Key
SECRET_KEY = "9G6yz3sMqzzt8SLcyruGPIrzNEvfiUwu"  # 更新为您提供的手势识别 Secret Key
ACCESS_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
GESTURE_RECOGNIZE_URL = "https://aip.baidubce.com/rest/2.0/image-classify/v1/gesture"  # 手势识别 API URL

# 输出文件路径
OUTPUT_FILE_PATH = r"C:\Users\FZC\Desktop\homework\电子测量与仪器\KESHE_MASTER\pytolab2.txt"
BASE64_FILE_PATH = "base64.txt"  # 保存 base64 编码的文件路径

# 获取百度智能云的 access_token
def get_access_token(api_key, secret_key):
    print(f"[DEBUG - finally_hand.py] 获取access_token - API密钥: {api_key[:5]}...，Secret: {secret_key[:5]}...")
    params = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": secret_key
    }
    
    try:
        print(f"[DEBUG - finally_hand.py] 请求access_token URL: {ACCESS_TOKEN_URL}")
        response = requests.post(ACCESS_TOKEN_URL, data=params)
        print(f"[DEBUG - finally_hand.py] access_token响应状态码: {response.status_code}")
        print(f"[DEBUG - finally_hand.py] access_token响应内容: {response.text[:200]}...")
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"[DEBUG - finally_hand.py] 成功获取access_token: {token[:10]}...")
            return token
        else:
            error_message = f"Failed to get access token: HTTP status {response.status_code}, response: {response.text}"
            print(f"[DEBUG - finally_hand.py] 获取access_token失败: {error_message}")
            raise Exception(error_message)
    except Exception as e:
        print(f"[DEBUG - finally_hand.py] 获取access_token异常: {str(e)}")
        raise

# 图像预处理
def preprocess_image(image_path):
    img = Image.open(image_path)
    # 调整亮度和对比度
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.2)  # 增加亮度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)  # 增加对比度
    return img

# 手部检测并裁剪
def detect_and_crop_hand(image_path):
    # 读取图像
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 定义皮肤颜色范围
    lower_skin = np.array([0, 20, 70], dtype=np.uint8)
    upper_skin = np.array([20, 255, 255], dtype=np.uint8)

    # 根据皮肤颜色范围创建掩膜
    mask = cv2.inRange(hsv, lower_skin, upper_skin)

    # 形态学操作，去除小的噪点
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=4)
    mask = cv2.GaussianBlur(mask, (5, 5), 100)

    # 寻找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # 找到最大的轮廓（假设是手部）
    if contours:
        cnt = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(cnt)
        cropped_img = img[y:y+h, x:x+w]
        cv2.imwrite("cropped_hand.jpg", cropped_img)
        return "cropped_hand.jpg"
    else:
        raise Exception("No hand detected in the image.")

# 手势识别函数
def gesture_recognize(image_path, access_token, image_type_hint="PATH"):
    """
    调用百度AI开放平台的手势识别API，识别图像中的手势类型。

    Args:
        image_path (str): 包含待识别手势的图片的本地路径，或者已经Base64编码的图片数据（取决于image_type_hint）。
        access_token (str): 有效的Access Token。
        image_type_hint (str): 提示函数如何处理 image_path 参数的方式。"PATH"表示 image_path 是文件路径，
                               需要读取并编码；"BASE64" 表示它已经是 Base64 编码的图片数据。

    Returns:
        dict: 包含手势识别结果的JSON对象 (从API响应解析而来)。
              通常包含识别出的手势类型及其置信度。

    Raises:
        FileNotFoundError: 如果指定的 image_path 文件不存在且 image_type_hint 为 "PATH"。
        requests.exceptions.RequestException: 如果在API请求过程中发生网络错误或连接问题。
        Exception: 如果API返回非200状态码，表示识别失败，异常信息包含API的错误文本。
    """
    # 根据 image_type_hint 处理图像数据
    image_base64 = ""
    if image_type_hint == "PATH" or os.path.exists(image_path):
        # 以二进制读取模式打开图片文件
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        # 将图片数据进行Base64编码
        image_base64 = base64.b64encode(image_data).decode("UTF-8")
    else: # 假设 image_path 已经是 Base64 编码的图片数据
        image_base64 = image_path    # URL编码
    image_base64_urlencoded = requests.utils.quote(image_base64)

    url = f"{GESTURE_RECOGNIZE_URL}?access_token={access_token}"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    payload = f'image={image_base64_urlencoded}'
    
    # 添加调试信息
    print(f"[DEBUG - finally_hand.py] 请求URL: {url}")
    print(f"[DEBUG - finally_hand.py] 请求头: {headers}")
    print(f"[DEBUG - finally_hand.py] 图像路径: {image_path}")
    
    response = requests.request("POST", url, headers=headers, data=payload)
    print(f"[DEBUG - finally_hand.py] 手势识别 API 响应状态码: {response.status_code}")
    print(f"[DEBUG - finally_hand.py] 手势识别 API 响应内容: {response.text[:500]}...")
    
    if response.status_code == 200:
        json_response = response.json()
        print(f"[DEBUG - finally_hand.py] 手势识别 API JSON 响应: {json_response}")
        return json_response
    else:
        error_message = f"Failed to recognize gesture: HTTP status {response.status_code}, response: {response.text[:200]}..."
        print(f"[DEBUG - finally_hand.py] {error_message}")
        raise Exception(error_message)

# 拍照并保存图片
def take_photo(photo_path):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("无法打开摄像头")
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(photo_path, frame)
        cropped_image_path = detect_and_crop_hand(photo_path)
        with open(cropped_image_path, "rb") as image_file:
            image_data = image_file.read()
        image_base64 = base64.b64encode(image_data).decode("UTF-8")
        with open(BASE64_FILE_PATH, "w") as base64_file:
            base64_file.write(image_base64)  # 将 base64 编码写入文件
        print(f"Base64 编码已保存到 {BASE64_FILE_PATH}")
    cap.release()
    cv2.destroyAllWindows()

# 将结果写入文件
def write_result_to_file(result):
    with open(OUTPUT_FILE_PATH, "w") as file:
        if "result" in result and result["result"]:
            gesture = result["result"][0]["classname"]
            file.write(f"Gesture: {gesture}\n")
        else:
            file.write("No gesture detected\n")

# GUI 界面
class GestureRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("百度智能云手势识别")
        self.access_token = get_access_token(API_KEY, SECRET_KEY)

        self.label = tk.Label(root, text="手势识别", font=("Arial", 14))
        self.label.pack(pady=10)

        self.select_button = tk.Button(root, text="选择图片", command=self.select_image)
        self.select_button.pack(pady=10)

        self.recognize_button = tk.Button(root, text="拍照识别手势", command=self.recognize_gesture)
        self.recognize_button.pack(pady=10)

        self.close_button = tk.Button(root, text="关闭程序", command=self.close_app)
        self.close_button.pack(pady=10)

        self.result_text = tk.Text(root, height=10, width=50)
        self.result_text.pack(pady=10)

        self.image_label = tk.Label(root)
        self.image_label.pack(pady=10)

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.png;*.jpeg;*.bmp")])
        if file_path:
            try:
                result = gesture_recognize(file_path, self.access_token)
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, json.dumps(result, ensure_ascii=False, indent=4))
                self.display_image(file_path)
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def recognize_gesture(self):
        photo_path = "temp_photo.jpg"
        try:
            take_photo(photo_path)
            cropped_image_path = detect_and_crop_hand(photo_path)
            result = gesture_recognize(cropped_image_path, self.access_token)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, json.dumps(result, ensure_ascii=False, indent=4))  # 打印 API 返回的完整响应
            if "result" in result and result["result"]:
                gesture = result["result"][0]["classname"]
                self.result_text.insert(tk.END, f"\n识别到手势: {gesture}")
                write_result_to_file(result)  # 写入文件
            else:
                self.result_text.insert(tk.END, "\n未识别到手势")
                write_result_to_file(result)  # 写入文件
            self.display_image(cropped_image_path)
        except Exception as e:
            messagebox.showerror("错误", str(e))
        finally:
            if os.path.exists(photo_path):
                os.remove(photo_path)
            if os.path.exists("cropped_hand.jpg"):
                os.remove("cropped_hand.jpg")

    def display_image(self, image_path):
        img = Image.open(image_path)
        img.thumbnail((300, 300))
        img = ImageTk.PhotoImage(img)
        self.image_label.config(image=img)
        self.image_label.image = img

    def close_app(self):
        self.root.destroy()

# 主程序
if __name__ == "__main__":
    root = tk.Tk()
    app = GestureRecognitionApp(root)
    root.mainloop()