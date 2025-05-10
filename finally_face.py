import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import requests
import base64
import json
from PIL import Image, ImageTk
import cv2
import os

# --- 百度智能云人脸识别 API 的相关配置 ---
# API Key，用于标识应用，调用API时必需
API_KEY = "MXGoFiOVcDaxC2WFLvpPwaqK"  # 替换为你的百度智能云 API Key
# Secret Key，用于签名和验证请求，调用API时必需
SECRET_KEY = "MVJJ3zXuaKNEDxIb7DGWAKWDQwWVnUEn"  # 替换为你的百度智能云 Secret Key
# 获取 Access Token 的 URL
ACCESS_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
# 人脸检测 API 的 URL
FACE_DETECT_URL = "https://aip.baidubce.com/rest/2.0/face/v3/detect"
# 人脸注册（添加用户到人脸库） API 的 URL
FACE_ADD_URL = "https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/add"
# 人脸搜索 API 的 URL
FACE_SEARCH_URL = "https://aip.baidubce.com/rest/2.0/face/v3/search"
# 默认的用户组 ID，人脸会被添加到此组或在此组中搜索
GROUP_ID = "1"  # 替换为你的用户组 ID

# --- 输出文件路径 ---
# 用于保存程序运行结果（例如识别到的用户ID）的文件路径
OUTPUT_FILE_PATH = r"C:\Users\FZC\Desktop\homework\电子测量与仪器\KESHE_MASTER\pytolab.txt"

# --- 函数定义 ---

def get_access_token(api_key, secret_key):
    """
    使用 API Key 和 Secret Key 从百度智能云获取 Access Token。

    Access Token 是调用百度AI平台各服务接口的临时凭证，具有一定的时效性。

    Args:
        api_key (str): 应用的 API Key。
        secret_key (str): 应用的 Secret Key。

    Returns:
        str: 获取到的 Access Token。

    Raises:
        Exception: 如果获取 Access Token 失败（例如，网络错误、API Key/Secret Key无效等），
                   则抛出异常，异常信息包含API返回的错误文本。
    """
    # 请求参数
    params = {
        "grant_type": "client_credentials",  # 获取Access Token的授权类型，固定为client_credentials
        "client_id": api_key,               # 应用的API Key
        "client_secret": secret_key         # 应用的Secret Key
    }
    # 发送POST请求到Access Token URL
    response = requests.post(ACCESS_TOKEN_URL, data=params)
    # 检查响应状态码
    if response.status_code == 200:
        # 如果状态码为200，表示请求成功，从返回的JSON中提取access_token
        return response.json().get("access_token")
    else:
        # 如果状态码非200，表示获取失败，抛出异常
        raise Exception("Failed to get access token: " + response.text)

def face_detect(image_path, access_token):
    """
    调用百度AI开放平台的人脸检测API，检测图片中的人脸信息。

    Args:
        image_path (str): 待检测图片的本地路径。
        access_token (str): 有效的Access Token。

    Returns:
        dict: 包含人脸检测结果的JSON对象 (从API响应解析而来)。
              通常包含人脸位置、数量、以及请求的属性（如年龄、性别、美貌度）等。

    Raises:
        FileNotFoundError: 如果指定的 image_path 文件不存在。
        requests.exceptions.RequestException: 如果在API请求过程中发生网络错误或连接问题。
        Exception: 如果API返回非200状态码，表示检测失败，异常信息包含API的错误文本。
                   或者在文件读取、编码过程中发生其他错误。
    """
    # 以二进制读取模式打开图片文件
    with open(image_path, "rb") as image_file:
        # 读取图片文件的全部二进制数据
        image_data = image_file.read()
    # 将图片的二进制数据进行Base64编码，并将结果从bytes转换为UTF-8字符串
    image_base64 = base64.b64encode(image_data).decode("UTF-8")

    # 设置请求头部，指定内容类型为JSON
    headers = {"Content-Type": "application/json"}
    # 构建请求参数的JSON体
    params = {
        "image": image_base64,          # Base64编码的图像数据
        "image_type": "BASE64",         # 指定图像数据类型为BASE64
        "face_field": "age,gender,beauty",  # 请求返回的人脸属性，例如年龄、性别、美貌度等，可根据需求调整
        "max_face_num": 10              # 最多检测的人脸数量
    }
    # 构建完整的请求URL，将access_token作为查询参数
    request_url = f"{FACE_DETECT_URL}?access_token={access_token}"
    # 发送POST请求到人脸检测API
    response = requests.post(request_url, headers=headers, data=json.dumps(params))
    # 检查响应状态码
    if response.status_code == 200:
        # 请求成功，返回JSON响应内容
        return response.json()
    else:
        # 请求失败，抛出异常
        raise Exception("Failed to detect face: " + response.text)

def face_add(image_path, access_token, user_id, group_id, quality_control="NONE", liveness_control="NONE", image_type_hint="BASE64"):
    """
    调用百度AI开放平台的人脸注册API，将图片中的人脸添加到指定用户组的用户下。

    Args:
        image_path (str): 包含待注册人脸的图片的本地路径，或者已经Base64编码的图片数据（取决于image_type_hint）。
        access_token (str): 有效的Access Token。
        user_id (str): 用户ID，用于唯一标识一个用户。
        group_id (str): 用户组ID，指定人脸要添加到的组。
        quality_control (str): 图片质量控制，可选值 "NONE"、"LOW"、"NORMAL"、"HIGH"。
        liveness_control (str): 活体检测控制，可选值 "NONE"、"LOW"、"NORMAL"、"HIGH"。
        image_type_hint (str): 提示函数如何处理 image_path 参数的方式。"PATH"表示 image_path 是文件路径，需要读取并编码；"BASE64" 表示它已经是 Base64 编码的图片数据。

    Returns:
        dict: 包含人脸注册结果的JSON对象 (从API响应解析而来)。
              通常包含操作日志ID、人脸token等信息。

    Raises:
        FileNotFoundError: 如果指定的 image_path 文件不存在且 image_type_hint 为 "PATH"。
        requests.exceptions.RequestException: 如果在API请求过程中发生网络错误或连接问题。
        Exception: 如果API返回非200状态码，表示注册失败，异常信息包含API的错误文本。
                   或者在文件读取、编码过程中发生其他错误。
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
        image_base64 = image_path

    # 设置请求头部
    headers = {"Content-Type": "application/json"}
    # 构建请求参数
    params = {
        "image": image_base64,          # Base64编码的图像数据
        "image_type": "BASE64",         # 图像类型
        "group_id": group_id,           # 用户组ID
        "user_id": user_id,             # 用户ID
        "user_info": "test",            # 用户自定义信息（可选）
        "liveness_control": liveness_control, # 活体检测控制
        "quality_control": quality_control    # 图片质量控制
    }
    # 构建请求URL
    request_url = f"{FACE_ADD_URL}?access_token={access_token}"
    # 发送POST请求
    response = requests.post(request_url, headers=headers, data=json.dumps(params))
    # 检查响应
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to add face: " + response.text)

def face_search(image_path, access_token, group_id_list=GROUP_ID, quality_control="NONE", liveness_control="NONE", image_type_hint="BASE64"):
    """
    调用百度AI开放平台的人脸搜索API，在指定用户组中搜索与图片中人脸最相似的用户。

    Args:
        image_path (str): 包含待搜索人脸的图片的本地路径，或者已经Base64编码的图片数据（取决于image_type_hint）。
        access_token (str): 有效的Access Token。
        group_id_list (str): 用户组ID列表，指定在哪些组中进行搜索（此处API接受字符串形式的单个组ID或逗号分隔的多个组ID）。默认使用 GROUP_ID 常量。
        quality_control (str): 图片质量控制，可选值 "NONE"、"LOW"、"NORMAL"、"HIGH"。
        liveness_control (str): 活体检测控制，可选值 "NONE"、"LOW"、"NORMAL"、"HIGH"。
        image_type_hint (str): 提示函数如何处理 image_path 参数的方式。"PATH"表示 image_path 是文件路径，需要读取并编码；"BASE64" 表示它已经是 Base64 编码的图片数据。

    Returns:
        dict: 包含人脸搜索结果的JSON对象 (从API响应解析而来)。
              通常包含匹配到的用户列表及其相似度得分。

    Raises:
        FileNotFoundError: 如果指定的 image_path 文件不存在且 image_type_hint 为 "PATH"。
        requests.exceptions.RequestException: 如果在API请求过程中发生网络错误或连接问题。
        Exception: 如果API返回非200状态码，表示搜索失败，异常信息包含API的错误文本。
                   或者在文件读取、编码过程中发生其他错误。
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
        image_base64 = image_path

    # 设置请求头部
    headers = {"Content-Type": "application/json"}
    # 构建请求参数
    params = {
        "image": image_base64,            # Base64编码的图像数据
        "image_type": "BASE64",           # 图像类型
        "group_id_list": group_id_list,   # 要在其中搜索的用户组ID列表
        "liveness_control": liveness_control, # 活体检测控制
        "quality_control": quality_control    # 图片质量控制
    }
    # 构建请求URL
    request_url = f"{FACE_SEARCH_URL}?access_token={access_token}"
    # 发送POST请求
    response = requests.post(request_url, headers=headers, data=json.dumps(params))
    # 检查响应
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to search face: " + response.text)

def take_photo(photo_path):
    """
    使用系统默认摄像头（通常是索引为0的摄像头）拍摄一张照片并保存到指定路径。

    Args:
        photo_path (str): 拍摄的照片的保存路径。

    Raises:
        Exception: 如果无法打开摄像头。
        cv2.error: 如果OpenCV在摄像头操作或图像保存过程中遇到错误。
    """
    # 初始化摄像头捕获对象，参数0表示使用系统中的第一个摄像头
    cap = cv2.VideoCapture(0)
    # 检查摄像头是否成功打开
    if not cap.isOpened():
        raise Exception("无法打开摄像头")
    
    # 从摄像头读取一帧图像
    # ret: 布尔值，表示是否成功读取到帧 (True表示成功)
    # frame: 读取到的图像帧 (一个NumPy数组)
    ret, frame = cap.read()
    
    # 检查是否成功读取到帧
    if ret:
        # 如果成功读取到帧，将该帧图像保存到指定的 photo_path
        cv2.imwrite(photo_path, frame)
    
    # 释放摄像头资源
    cap.release()
    # 关闭所有由OpenCV创建的窗口（如果在其他地方有显示图像的窗口）
    # 在此GUI应用中，图像显示由Tkinter处理，此调用主要用于确保OpenCV窗口被清理
    cv2.destroyAllWindows()

def write_result_to_file(result):
    """
    将人脸搜索的结果（主要是识别到的用户ID）写入到预定义的输出文件中。

    如果成功识别到用户，则写入 "YES user<用户ID>"。
    如果未识别到用户或结果为空，则写入 "NO  user0"。

    Args:
        result (dict): 人脸搜索API返回的JSON对象。
    """
    # 以写入模式打开输出文件
    with open(OUTPUT_FILE_PATH, "w") as file:
        # 检查API返回结果中是否包含有效的识别信息
        if "result" in result and result["result"] and "user_list" in result["result"] and result["result"]["user_list"]:
            # 提取第一个匹配用户的用户ID
            user_id = result["result"]["user_list"][0]["user_id"]
            # 将识别成功的标记和用户ID写入文件
            file.write(f"YES user{user_id}\n")
        else:
            # 如果未识别到用户，写入表示未成功的标记
            file.write("NO  user0\n")

# --- GUI 界面类定义 ---
class FaceRecognitionApp:
    """
    一个使用Tkinter创建的GUI应用程序，用于百度智能云的人脸识别与注册功能。

    提供了选择图片进行人脸检测（当前隐藏）、注册人脸（从文件选择图片并输入用户ID）、
    拍照进行人脸识别（搜索）的功能。
    识别结果会显示在文本框中，并可将识别到的用户ID写入文件。
    """
    def __init__(self, root):
        """
        初始化GUI应用程序。

        Args:
            root (tk.Tk): Tkinter的主窗口实例。
        """
        self.root = root
        self.root.title("百度智能云人脸识别与注册") # 设置窗口标题
        
        # 尝试获取Access Token，如果失败，程序启动时会抛出异常
        try:
            self.access_token = get_access_token(API_KEY, SECRET_KEY)
        except Exception as e:
            messagebox.showerror("初始化错误", f"获取Access Token失败: {str(e)}")
            self.root.destroy() # 获取Token失败则关闭应用
            return

        # --- GUI控件创建和布局 ---
        self.label = tk.Label(root, text="人脸识别与注册", font=("Arial", 14))
        self.label.pack(pady=10) # pady增加垂直方向的外部填充

        # “选择图片”按钮（用于人脸检测，当前被隐藏）
        self.select_button = tk.Button(root, text="选择图片", command=self.select_image)
        self.select_button.pack(pady=10)
        self.select_button.pack_forget()  # 调用pack_forget()将按钮从布局中移除，使其不可见

        # “注册人脸”按钮
        self.register_button = tk.Button(root, text="注册人脸", command=self.register_face)
        self.register_button.pack(pady=10)

        # “拍照识别”按钮（用于人脸搜索）
        self.search_button = tk.Button(root, text="拍照识别", command=self.search_face)
        self.search_button.pack(pady=10)

        # “关闭程序”按钮
        self.close_button = tk.Button(root, text="关闭程序", command=self.close_app)
        self.close_button.pack(pady=10)

        # 用于显示结果的文本框
        self.result_text = tk.Text(root, height=10, width=50)
        self.result_text.pack(pady=10)

        # 用于显示图片的标签
        self.image_label = tk.Label(root)
        self.image_label.pack(pady=10)

    def select_image(self):
        """
        处理“选择图片”按钮的点击事件（当前此按钮被隐藏）。
        打开文件对话框让用户选择图片，然后调用人脸检测API并显示结果。
        """
        # 打开文件选择对话框，允许用户选择指定类型的图片文件
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.png;*.jpeg;*.bmp")])
        if file_path: # 如果用户选择了文件
            try:
                # 调用人脸检测函数
                result = face_detect(file_path, self.access_token)
                # 清空文本框的旧内容
                self.result_text.delete(1.0, tk.END)
                # 将JSON结果格式化后插入文本框
                self.result_text.insert(tk.END, json.dumps(result, ensure_ascii=False, indent=4))
                # 显示选择的图片
                self.display_image(file_path)
            except Exception as e:
                # 如果发生错误，显示错误信息对话框
                messagebox.showerror("错误", str(e))

    def register_face(self):
        """
        处理“注册人脸”按钮的点击事件。
        让用户选择图片文件，并输入用户ID，然后调用人脸注册API。
        """
        # 打开文件选择对话框
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.png;*.jpeg;*.bmp")])
        if file_path: # 如果用户选择了文件
            # 弹出对话框让用户输入用户ID
            user_id = simpledialog.askstring("输入", "请输入用户ID")
            if user_id: # 如果用户输入了ID
                try:
                    # 调用人脸注册函数
                    result = face_add(file_path, self.access_token, user_id, GROUP_ID)
                    self.result_text.delete(1.0, tk.END)
                    self.result_text.insert(tk.END, json.dumps(result, ensure_ascii=False, indent=4))
                    self.display_image(file_path)
                except Exception as e:
                    messagebox.showerror("错误", str(e))

    def search_face(self):
        """
        处理“拍照识别”按钮的点击事件。
        调用摄像头拍照，然后对拍摄的照片进行人脸搜索，并将结果写入文件。
        """
        photo_path = "temp_photo.jpg" # 临时保存拍摄照片的文件名
        try:
            # 调用拍照函数
            take_photo(photo_path)
            # 调用人脸搜索函数
            result = face_search(photo_path, self.access_token, GROUP_ID)
            self.result_text.delete(1.0, tk.END)
            # 解析并显示搜索结果
            if "result" in result and result["result"] and "user_list" in result["result"] and result["result"]["user_list"]:
                user_id = result["result"]["user_list"][0]["user_id"] # 获取最匹配的用户ID
                score = result["result"]["user_list"][0]["score"] # 获取匹配得分
                self.result_text.insert(tk.END, f"检测到人脸，用户ID: {user_id}, 相似度: {score:.2f}")
                write_result_to_file(result)  # 将结果写入文件
            else:
                self.result_text.insert(tk.END, "未检测到匹配的人脸")
                write_result_to_file(result)  # 即使未检测到，也调用写入（会写入"NO user0"）
            # 显示拍摄的图片
            self.display_image(photo_path)
        except Exception as e:
            messagebox.showerror("错误", str(e))
        finally:
            # 清理：无论成功与否，都尝试删除临时照片文件
            if os.path.exists(photo_path):
                os.remove(photo_path)

    def display_image(self, image_path):
        """
        在GUI界面上显示指定的图片。

        Args:
            image_path (str): 要显示的图片的路径。
        """
        try:
            # 使用Pillow库打开图片
            img = Image.open(image_path)
            # 调整图片大小以适应显示区域（最大300x300），保持宽高比
            img.thumbnail((300, 300))
            # 将Pillow图像对象转换为Tkinter可以显示的PhotoImage对象
            img_tk = ImageTk.PhotoImage(img)
            # 更新Label控件以显示新图片
            self.image_label.config(image=img_tk)
            # 保持对PhotoImage对象的引用，防止被垃圾回收导致图片不显示
            self.image_label.image = img_tk
        except FileNotFoundError:
            messagebox.showerror("错误", f"图片文件未找到: {image_path}")
        except Exception as e:
            messagebox.showerror("图片显示错误", str(e))


    def close_app(self):
        """
        处理“关闭程序”按钮的点击事件。
        销毁主窗口，从而退出应用程序。
        """
        self.root.destroy()

# --- 主程序入口 ---
if __name__ == "__main__":
    # 创建Tkinter主窗口
    root = tk.Tk()
    # 创建应用程序类的实例
    app = FaceRecognitionApp(root)
    # 进入Tkinter事件循环，等待用户交互
    root.mainloop()