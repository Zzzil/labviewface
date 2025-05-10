import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import Python_Interface # 确保 Python_Interface.py 在同一目录或 PYTHONPATH 中
import cv2
from PIL import Image, ImageTk
import os

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("百度AI接口操作界面")
        self.root.geometry("650x850")

        self.cap = None
        self.current_frame = None
        self.camera_preview_active = False

        # 更新图像保存的基础目录
        self.base_capture_dir = "C:\\\\Users\\\\12742\\\\Desktop\\\\labviewface\\\\image"
        self.capture_filename_face_search = "captured_face_search.jpg"
        self.capture_filename_gesture = "captured_gesture.jpg"
        self.capture_filename_registration = "captured_face_registration.jpg"
        
        # 确保图像保存目录存在
        os.makedirs(self.base_capture_dir, exist_ok=True)

        # --- 操作选择 ---
        ttk.Label(root, text="选择操作:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.operation_var = tk.StringVar()
        self.operation_options = {
            "拍照并搜索人脸": "take_photo_and_search",
            "手势识别": "gesture_recognize",
            "人脸注册": "face_add"
        }
        self.operation_menu = ttk.Combobox(root, textvariable=self.operation_var,
                                           values=list(self.operation_options.keys()), width=30, state="readonly")
        self.operation_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew", columnspan=2)
        self.operation_menu.bind("<<ComboboxSelected>>", self.update_fields)

        # --- 参数输入 ---
        self.param_frame = ttk.LabelFrame(root, text="参数输入")
        self.param_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # 图像路径 - 标签文本根据上下文调整
        self.image_path_label = ttk.Label(self.param_frame, text="图像路径:")
        self.image_path_label.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.image_path_var = tk.StringVar()
        self.image_path_entry = ttk.Entry(self.param_frame, textvariable=self.image_path_var, width=40)
        self.image_path_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.browse_button = ttk.Button(self.param_frame, text="浏览...", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, padx=5, pady=2)

        # 用户组ID列表 (group_id_list)
        ttk.Label(self.param_frame, text="用户组ID列表 (逗号分隔):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.group_id_list_var = tk.StringVar()
        self.group_id_list_entry = ttk.Entry(self.param_frame, textvariable=self.group_id_list_var, width=40)
        self.group_id_list_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew", columnspan=2)

        # 用户ID (user_id)
        ttk.Label(self.param_frame, text="用户ID:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.user_id_var = tk.StringVar()
        self.user_id_entry = ttk.Entry(self.param_frame, textvariable=self.user_id_var, width=40)
        self.user_id_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew", columnspan=2)

        # 用户组ID (group_id)
        ttk.Label(self.param_frame, text="用户组ID (单个):").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.group_id_var = tk.StringVar()
        self.group_id_entry = ttk.Entry(self.param_frame, textvariable=self.group_id_var, width=40)
        self.group_id_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew", columnspan=2)

        # 图片质量控制 (quality_control)
        ttk.Label(self.param_frame, text="图片质量控制:").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.quality_control_var = tk.StringVar(value="NONE")
        self.quality_control_entry = ttk.Combobox(self.param_frame, textvariable=self.quality_control_var,
                                                 values=["NONE", "LOW", "NORMAL", "HIGH"], width=38, state="readonly")
        self.quality_control_entry.grid(row=4, column=1, padx=5, pady=2, sticky="ew", columnspan=2)

        # 活体检测控制 (liveness_control)
        ttk.Label(self.param_frame, text="活体检测控制:").grid(row=5, column=0, padx=5, pady=2, sticky="w")
        self.liveness_control_var = tk.StringVar(value="NONE")
        self.liveness_control_entry = ttk.Combobox(self.param_frame, textvariable=self.liveness_control_var,
                                                  values=["NONE", "LOW", "NORMAL", "HIGH"], width=38, state="readonly")
        self.liveness_control_entry.grid(row=5, column=1, padx=5, pady=2, sticky="ew", columnspan=2)
        
        self.param_frame.columnconfigure(1, weight=1)

        # --- 摄像头预览区域 ---
        self.camera_frame = ttk.LabelFrame(root, text="摄像头预览")
        # Initially hidden, will be shown by update_fields
        # self.camera_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew") 

        self.video_label = ttk.Label(self.camera_frame)
        self.video_label.pack(pady=5)

        self.capture_button = ttk.Button(self.camera_frame, text="拍照", command=self.capture_photo)
        self.capture_button.pack(pady=5)
        
        self.photo_status_label = ttk.Label(self.camera_frame, text="")
        self.photo_status_label.pack(pady=2)


        # --- 执行按钮 ---
        # Row adjusted due to camera_frame
        self.execute_button = ttk.Button(root, text="执行操作", command=self.execute_action, width=20)
        self.execute_button.grid(row=3, column=0, columnspan=3, padx=5, pady=10)

        # --- 结果显示 ---
        # Row adjusted
        ttk.Label(root, text="结果:").grid(row=4, column=0, padx=5, pady=5, sticky="nw")
        self.result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=10) # Adjusted height
        self.result_text.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.result_text.config(state="disabled")
        
        root.columnconfigure(1, weight=1) 

        # 初始化字段状态
        self.update_fields()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing) # Handle window close

    def on_closing(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.root.destroy()

    def start_camera(self):
        if not self.cap or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0) # Use camera 0
            if not self.cap.isOpened():
                self.show_result("错误：无法打开摄像头。请检查摄像头是否连接并可用。")
                self.cap = None
                return
        self.camera_preview_active = True
        self.photo_status_label.config(text="") # Clear previous status
        self.show_frame_loop()

    def stop_camera(self):
        self.camera_preview_active = False # Stops the loop in show_frame_loop
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
        # Clear the video label if needed
        self.video_label.config(image='') 
        self.video_label.image = None


    def show_frame_loop(self):
        if not self.camera_preview_active or not self.cap or not self.cap.isOpened():
            # If camera became inactive or cap is released, clear label and stop.
            self.video_label.config(image='')
            self.video_label.image = None
            return

        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame.copy() # Keep a copy of the current frame for capture
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)

            # --- 添加图像缩放以适应UI ---
            preview_max_width = 400  # 设置预览区域的最大宽度
            original_width, original_height = img.size
            if original_width > preview_max_width:
                aspect_ratio = original_height / original_width
                preview_height = int(preview_max_width * aspect_ratio)
                # For Pillow >= 9.1.0, use Image.Resampling.LANCZOS
                # For older versions, Image.LANCZOS or Image.ANTIALIAS might be used
                try:
                    img = img.resize((preview_max_width, preview_height), Image.Resampling.LANCZOS)
                except AttributeError: # Fallback for older Pillow versions
                    img = img.resize((preview_max_width, preview_height), Image.LANCZOS) # Or Image.ANTIALIAS
            # --- 图像缩放结束 ---
            
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.config(image=imgtk)
        else:
            # Handle error or end of video if it were a file
            self.current_frame = None 
        
        if self.camera_preview_active : # Continue loop only if active
             self.video_label.after(15, self.show_frame_loop)


    def capture_photo(self):
        if self.current_frame is not None:
            selected_op_key = self.operation_options.get(self.operation_var.get())
            save_path = ""
            photo_purpose = ""

            if selected_op_key == "take_photo_and_search":
                save_path = os.path.join(self.base_capture_dir, self.capture_filename_face_search)
                photo_purpose = "人脸搜索"
            elif selected_op_key == "gesture_recognize":
                save_path = os.path.join(self.base_capture_dir, self.capture_filename_gesture)
                photo_purpose = "手势识别"
            elif selected_op_key == "face_add":
                save_path = os.path.join(self.base_capture_dir, self.capture_filename_registration)
                photo_purpose = "人脸注册"
            else:
                messagebox.showwarning("拍照警告", "未知操作，无法确定照片保存路径。")
                return

            try:
                cv2.imwrite(save_path, self.current_frame)
                self.photo_status_label.config(text=f"照片已保存到: {os.path.basename(save_path)}")
                
                if selected_op_key == "gesture_recognize" or selected_op_key == "face_add":
                    self.image_path_var.set(save_path) # 自动填充图像路径
                    self.show_result(f"照片已捕获用于“{self.operation_var.get()}”，路径已填入: {os.path.basename(save_path)}。\n请填写其他必要参数后执行操作。")
                elif selected_op_key == "take_photo_and_search":
                     self.show_result(f"照片已捕获用于“{self.operation_var.get()}”并保存到 {os.path.basename(save_path)}。\n现在可以点击“执行操作”进行人脸搜索。")

            except Exception as e:
                messagebox.showerror("拍照错误", f"保存照片失败: {str(e)}")
                self.photo_status_label.config(text="拍照失败")
        else:
            messagebox.showwarning("拍照警告", "无法捕获照片，摄像头无画面。")
            self.photo_status_label.config(text="无有效画面")


    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="选择图像文件",
            filetypes=(("JPEG files", "*.jpg;*.jpeg"), ("PNG files", "*.png"), ("All files", "*.*"))
        )
        if filepath:
            self.image_path_var.set(filepath)

    def update_fields(self, event=None):
        selected_op_display = self.operation_var.get()
        operation_key = self.operation_options.get(selected_op_display)

        # 默认隐藏摄像头，按需显示
        self.camera_frame.grid_remove()
        if self.camera_preview_active and operation_key not in ["take_photo_and_search", "gesture_recognize", "face_add"]:
            self.stop_camera()

        # 默认全部禁用，然后按需启用
        self.image_path_entry.config(state="disabled")
        self.browse_button.config(state="disabled")
        self.group_id_list_entry.config(state="disabled")
        self.user_id_entry.config(state="disabled")
        self.group_id_entry.config(state="disabled")
        self.quality_control_entry.config(state="normal")
        self.liveness_control_entry.config(state="normal")
        self.image_path_label.config(text="图像路径:") # Reset label

        if not selected_op_display: # 初始状态或未选择
            # 确保所有特定字段都禁用
            if self.camera_preview_active: self.stop_camera() # Stop camera if no op selected
            return

        if operation_key == "take_photo_and_search":
            self.camera_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
            if not self.camera_preview_active: self.start_camera()
            self.image_path_label.config(text="图像路径 (固定):")
            # image_path_entry 和 browse_button 保持 disabled
            self.group_id_list_entry.config(state="normal")
            self.photo_status_label.config(text="点击“拍照”按钮捕获图像用于搜索")
        
        elif operation_key == "gesture_recognize":
            self.camera_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
            if not self.camera_preview_active: self.start_camera()
            self.image_path_label.config(text="图像路径 (拍照或浏览):")
            self.image_path_entry.config(state="normal")
            self.browse_button.config(state="normal")
            self.quality_control_entry.config(state="disabled")
            self.liveness_control_entry.config(state="disabled")
            self.quality_control_var.set("NONE")
            self.liveness_control_var.set("NONE")
            self.photo_status_label.config(text="可拍照或浏览选择手势图片")

        elif operation_key == "face_add":
            self.camera_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
            if not self.camera_preview_active: self.start_camera()
            self.image_path_label.config(text="图像路径 (拍照或浏览):")
            self.image_path_entry.config(state="normal")
            self.browse_button.config(state="normal")
            self.user_id_entry.config(state="normal")
            self.group_id_entry.config(state="normal")
            self.photo_status_label.config(text="可拍照或浏览选择人脸图片进行注册")

    def execute_action(self):
        selected_op_display = self.operation_var.get()
        if not selected_op_display:
            self.show_result("错误：请先选择一个操作。")
            return
        
        operation = self.operation_options[selected_op_display]
        
        # 从GUI获取参数值 - 改进值的获取逻辑
        image_path_gui = self.image_path_var.get() 
        
        # 检查控件状态是否为禁用，如果不是就获取值
        group_id_list = "" if self.group_id_list_entry.cget("state") == "disabled" else self.group_id_list_var.get()
        user_id = "" if self.user_id_entry.cget("state") == "disabled" else self.user_id_var.get()
        group_id = "" if self.group_id_entry.cget("state") == "disabled" else self.group_id_var.get()
        quality_control = "NONE" if self.quality_control_entry.cget("state") == "disabled" else self.quality_control_var.get()
        liveness_control = "NONE" if self.liveness_control_entry.cget("state") == "disabled" else self.liveness_control_var.get()

        # 调试信息
        print(f"操作: {operation}")
        print(f"图像路径: {image_path_gui}")
        print(f"用户组ID列表: {group_id_list}")
        print(f"用户ID: {user_id}")
        print(f"单个用户组ID: {group_id}")
        print(f"图像质量控制: {quality_control}")
        print(f"活体检测: {liveness_control}")
        
        actual_image_path = ""
        image_type = "PATH" # All images from GUI will be local paths

        if operation == "take_photo_and_search":
            actual_image_path = os.path.join(self.base_capture_dir, self.capture_filename_face_search)
            if not os.path.exists(actual_image_path):
                self.show_result(f"错误：未找到用于搜索的人脸照片。请先使用“拍照”按钮捕获。路径: {actual_image_path}")
                messagebox.showerror("操作错误", "未找到已拍摄的人脸搜索照片。请先点击“拍照”按钮。")
                return
            
            # 更严格检查 group_id_list
            group_id_list_trimmed = group_id_list.strip() if group_id_list else ""
            
            if not group_id_list_trimmed:
                self.show_result(f"错误：“拍照并搜索人脸”操作需要填写“用户组ID列表”。\n"
                                f"检测到的原始输入为: '{group_id_list}'\n"
                                f"去除首尾空格后: '{group_id_list_trimmed}'\n"
                                f"控件状态: {self.group_id_list_entry.cget('state')}")
                messagebox.showerror("参数错误", "请填写有效的“用户组ID列表”。")
                return
            
            # 使用去除首尾空格后的值
            group_id_list = group_id_list_trimmed

        elif operation == "gesture_recognize":
            if not image_path_gui: # Path from entry (either browsed or captured)
                self.show_result("错误：手势识别操作需要提供图像路径 (通过拍照或浏览)。")
                messagebox.showerror("参数错误", "请提供手势图像路径。")
                return
            if not os.path.exists(image_path_gui):
                self.show_result(f"错误：手势识别提供的图像路径不存在: {image_path_gui}")
                messagebox.showerror("文件错误", f"提供的图像路径不存在: {image_path_gui}")
                return
            actual_image_path = image_path_gui
        
        elif operation == "face_add":
            if not image_path_gui: # Path from entry (either browsed or captured)
                self.show_result("错误：人脸注册操作需要提供图像路径 (通过拍照或浏览)。")
                messagebox.showerror("参数错误", "请提供人脸图像路径。")
                return
            if not os.path.exists(image_path_gui):
                self.show_result(f"错误：人脸注册提供的图像路径不存在: {image_path_gui}")
                messagebox.showerror("文件错误", f"提供的图像路径不存在: {image_path_gui}")
                return
            actual_image_path = image_path_gui
            
            # 更详细和严格地检查 user_id 和 group_id
            user_id_trimmed = user_id.strip() if user_id else ""
            group_id_trimmed = group_id.strip() if group_id else ""
            
            if not user_id_trimmed or not group_id_trimmed:
                error_detail = []
                if not user_id_trimmed:
                    error_detail.append(f"用户ID为空 (原始值: '{user_id}')")
                if not group_id_trimmed:
                    error_detail.append(f"单个用户组ID为空 (原始值: '{group_id}')")
                
                error_msg = "错误：“人脸注册”操作需要填写“用户ID”和“用户组ID (单个)”。\n"
                error_msg += "问题: " + "、".join(error_detail)
                self.show_result(error_msg)
                messagebox.showerror("参数错误", "请填写“用户ID”和“用户组ID (单个)”。")
                return
            
            # 使用去除首尾空格后的值
            user_id = user_id_trimmed
            group_id = group_id_trimmed

        self.show_result(f"正在执行操作: {selected_op_display} (图像: {os.path.basename(actual_image_path)})...")
        self.root.update_idletasks() 

        try:
            # Note: For "take_photo_and_search", image_path is now self.fixed_capture_path
            # and image_type should be "PATH" or similar, as Python_Interface will no longer call take_photo()
            result = Python_Interface.call_baidu_api(
                operation=operation,
                image_path=actual_image_path, # This is key
                image_type=image_type,       # This is key
                group_id_list=group_id_list,
                user_id=user_id,
                group_id=group_id,
                quality_control=quality_control,
                liveness_control=liveness_control
            )
            self.show_result(f"操作 '{selected_op_display}' 完成:\n{result}")
        except Exception as e:
            self.show_result(f"执行操作时发生错误:\n{str(e)}")
            import traceback
            traceback.print_exc() # For debugging in console

    def show_result(self, message):
        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, message)
        self.result_text.config(state="disabled")

if __name__ == "__main__":
    main_root = tk.Tk()
    app = App(main_root)
    main_root.mainloop()
