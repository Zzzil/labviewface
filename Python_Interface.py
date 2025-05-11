import sys
import json
import os.path
import base64
import requests # 用于手势识别的直接调用示例
import traceback # 用于在 call_baidu_api 中打印更详细的错误堆栈

# --- 模块导入处理 ---
# 尝试导入核心逻辑模块 finally_face 和 finally_hand
# 这两个模块包含了与百度AI平台API交互的具体实现
try:
    import finally_face
    import finally_hand
except ImportError as e:
    # 如果直接导入失败（例如，当脚本被其他路径下的程序如LabVIEW调用时），
    # 尝试将当前脚本所在的目录添加到Python的模块搜索路径 (sys.path)
    # 这样Python解释器就能找到位于同一目录下的 finally_face.py 和 finally_hand.py
    script_dir = os.path.dirname(os.path.abspath(__file__)) # 获取当前脚本的绝对路径的目录部分
    if (script_dir not in sys.path):
        sys.path.append(script_dir) # 将脚本目录添加到sys.path
    try:
        # 再次尝试导入
        import finally_face
        import finally_hand
    except ImportError:
        # 如果再次导入仍然失败，则不执行任何操作 (pass)。
        # 错误将在后续调用这些模块内函数时通过 NameError 捕获，
        # 或者在 call_baidu_api 函数中进行更明确的检查和错误返回。
        # 对于直接通过命令行运行此脚本的情况，如果模块无法加载，
        # 后续对 finally_face 或 finally_hand 的引用会直接导致程序因 NameError 退出。
        pass

# --- 固定照片保存路径 ---
# 为 "take_photo_and_search" 操作指定固定的照片保存目录和文件名
PHOTO_SAVE_DIR = "C:\\Users\\12742\\Desktop\\APIface\\image"
PHOTO_FILENAME = "captured_face.jpg" # 可以考虑使用时间戳命名以避免覆盖
FULL_PHOTO_PATH = os.path.join(PHOTO_SAVE_DIR, PHOTO_FILENAME)

# --- 命令行参数处理 (当脚本直接执行时) ---
# 这部分代码块仅在脚本通过 `python Python_Interface.py ...` 方式直接执行时生效。
# 如果此脚本是被其他Python模块导入或被LabVIEW等外部程序通过函数调用方式使用，
# 这部分代码不会执行。

# 检查命令行参数数量是否足够
# 脚本至少需要3个参数: 脚本名, 操作类型, 图像路径
if __name__ == '__main__' and len(sys.argv) < 3:
    print(json.dumps({"error": "错误: 缺少参数。需要提供操作类型和图像路径。"}, ensure_ascii=False))
    sys.exit(1) # 参数不足，打印错误信息并退出

# 仅当作为主脚本运行时才从 sys.argv 获取参数
if __name__ == '__main__':
    operation = sys.argv[1]  # 第一个参数: 操作类型 (例如: "face_detect", "gesture_recognize")
    image_path = sys.argv[2]  # 第二个参数: 图像文件的路径

    # 获取API密钥和秘钥，优先从命令行参数获取，如果未提供则使用占位符
    # 第三个参数 (可选): API Key
    api_key = "您的API_KEY" if len(sys.argv) <= 3 else sys.argv[3]
    # 第四个参数 (可选): Secret Key
    secret_key = "您的SECRET_KEY" if len(sys.argv) <= 4 else sys.argv[4]

    # --- 主逻辑 (当脚本直接执行时) ---
    try:
        result = {} # 用于存储API调用结果的字典

        # 根据操作类型调用不同的函数
        if operation == "face_detect":
            # 获取access_token
            access_token = finally_face.get_access_token(api_key, secret_key)
            # 执行人脸检测
            result = finally_face.face_detect(image_path, access_token)
        
        elif operation == "face_add":
            # 人脸注册操作需要额外的参数: user_id 和可选的 group_id
            if len(sys.argv) < 5: # 脚本名, operation, image_path, api_key, secret_key, user_id
                print(json.dumps({"error": "错误: 人脸注册需要用户ID。"}, ensure_ascii=False))
                sys.exit(1)
            
            user_id = sys.argv[5] # 第五个参数: 用户ID
            group_id = "1" if len(sys.argv) <= 6 else sys.argv[6] # 第六个参数 (可选): 用户组ID，默认为"1"
            
            access_token = finally_face.get_access_token(api_key, secret_key)
            result = finally_face.face_add(image_path, access_token, user_id, group_id)
        
        elif operation == "face_search":
            # 人脸搜索操作可选的 group_id
            group_id = "1" if len(sys.argv) <= 5 else sys.argv[5] # 第五个参数 (可选): 用户组ID，默认为"1"
            
            access_token = finally_face.get_access_token(api_key, secret_key)
            result = finally_face.face_search(image_path, access_token, group_id)
        
        elif operation == "gesture_recognize":
            access_token = finally_hand.get_access_token(api_key, secret_key)
            # 注意: finally_hand.py 中的 preprocess_image 函数返回 PIL Image 对象，
            # 而 gesture_recognize 通常期望的是图像路径。
            # 如果需要预处理，应确保 gesture_recognize 能处理预处理后的图像或其路径。
            # 此处假设 gesture_recognize 直接使用原始 image_path。
            # preprocessed_img = finally_hand.preprocess_image(image_path) # 此行可能需要调整
            if hasattr(finally_hand, 'gesture_recognize'): # 检查 finally_hand 模块是否有 gesture_recognize 函数
                result = finally_hand.gesture_recognize(image_path, access_token) # 直接使用原始路径
            else:
                print(json.dumps({"error": "错误: 手势识别功能 (gesture_recognize) 在 finally_hand 模块中未实现。"}, ensure_ascii=False))
                sys.exit(1)
        
        else:
            print(json.dumps({"error": f"错误: 不支持的操作类型 '{operation}'"}, ensure_ascii=False))
            sys.exit(1)

        # 将API调用结果以JSON格式打印到标准输出
        print(json.dumps(result, ensure_ascii=False))

    except NameError as e:
        # 捕获因模块 (finally_face, finally_hand) 未成功导入而产生的错误
        print(json.dumps({"error": f"名称错误 (模块导入可能失败): {str(e)}"}, ensure_ascii=False))
        sys.exit(1)
    except FileNotFoundError:
        print(json.dumps({"error": f"错误: 图片文件未找到于路径 '{image_path}'"}, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        # 捕获其他所有在主逻辑中可能发生的异常
        print(json.dumps({"error": f"执行操作 '{operation}' 时发生错误: {str(e)}"}, ensure_ascii=False))
        sys.exit(1)

# --- LabVIEW 和 GUI 调用接口函数 ---
def call_baidu_api(operation: str, 
                   image_path: str, # 对于拍照操作，这是GUI拍照后保存的路径；对于其他，是用户选择的路径
                   image_type: str, # 主要由GUI设置，例如 "PATH"
                   group_id_list: str = "", # 用于人脸搜索
                   user_id: str = "",       # 用于人脸注册
                   group_id: str = "",      # 用于人脸注册
                   quality_control: str = "NONE",
                   liveness_control: str = "NONE"
                   # api_key 和 secret_key 将从 finally_face/finally_hand 模块内部获取
                   ) -> dict:
    """
    核心函数，设计用于从LabVIEW或新的GUI调用，以执行百度人脸识别和手势识别API操作。
    支持: "take_photo_and_search", "gesture_recognize", "face_add"。
    对于 "take_photo_and_search" 和 "face_add" 将返回一个包含详细信息的字典而不仅仅是描述性字符串。

    Args:
        operation (str): 要执行的操作类型。
        image_path (str): 图像文件的路径。
                          对于 "take_photo_and_search" 和 "gesture_recognize" (当通过GUI的摄像头拍照时)，
                          这应该是GUI拍照后保存的图像的完整路径。
                          对于 "face_add" 和 "gesture_recognize" (当通过GUI的文件浏览选择时)，这是用户选择的图像路径。
        image_type (str): 图像的类型，例如 "PATH", "URL", "BASE64"。
                          GUI通常会设置为 "PATH" 当图像来自本地文件。
                          finally_face/finally_hand 内部可能会根据此值或文件扩展名处理图像。
        group_id_list (str, optional): 用户组ID列表 (逗号分隔)，主要用于 "take_photo_and_search"。
        user_id (str, optional): 用户ID，主要用于 "face_add" 操作。
        group_id (str, optional): 单个用户组ID，主要用于 "face_add" 操作。
        quality_control (str, optional): 图片质量控制。
        liveness_control (str, optional): 活体检测控制。

    Returns:
        dict: 一个包含操作结果的字典。
              对于 "take_photo_and_search"，包含是否成功、匹配用户信息、相似度等。
              对于 "face_add"，包含是否成功、用户ID、面部标识等。
              其他操作仍返回描述性字符串但包装在字典中。
    """
    # 检查核心模块是否已成功导入
    if 'finally_face' not in globals() or 'finally_hand' not in globals():
        return "调用错误: 核心功能模块 (finally_face.py 或 finally_hand.py) 未能加载。"

    face_api_key = None
    face_secret_key = None
    hand_api_key = None
    hand_secret_key = None

    try:
        if hasattr(finally_face, 'API_KEY') and hasattr(finally_face, 'SECRET_KEY'):
            face_api_key = finally_face.API_KEY
            face_secret_key = finally_face.SECRET_KEY
        
        if hasattr(finally_hand, 'API_KEY') and hasattr(finally_hand, 'SECRET_KEY'):
            hand_api_key = finally_hand.API_KEY
            hand_secret_key = finally_hand.SECRET_KEY

        if (not face_api_key or not face_secret_key) and operation in ["take_photo_and_search", "face_add"]:
            return "配置错误: finally_face.py 中未找到 API_KEY 或 SECRET_KEY。"
        if (not hand_api_key or not hand_secret_key) and operation == "gesture_recognize":
            return "配置错误: finally_hand.py 中未找到 API_KEY 或 SECRET_KEY。"

    except Exception as e_keys: # More general exception for key retrieval
        return f"获取API密钥时出错: {str(e_keys)}"


    try:
        access_token = "" 

        if operation == "take_photo_and_search":
            if not image_path or not os.path.exists(image_path):
                return f"调用错误: '拍照并搜索人脸'操作需要一个有效的图像文件路径，但收到 '{image_path}'。"
            if not group_id_list:
                return "参数错误: '拍照并搜索人脸'操作需要提供用户组ID列表 (group_id_list)。"
            
            if not hasattr(finally_face, 'get_access_token') or not hasattr(finally_face, 'face_search'):
                return "内部错误: 人脸搜索所需功能在 finally_face.py 中未实现。"
            
            try:
                access_token = finally_face.get_access_token(face_api_key, face_secret_key)
                raw_result = finally_face.face_search(
                    image_path=image_path, 
                    access_token=access_token, 
                    group_id_list=group_id_list,
                    quality_control=quality_control,
                    liveness_control=liveness_control,
                    image_type_hint=image_type 
                )
            except requests.exceptions.RequestException as e_req:
                return f"网络请求错误 (人脸搜索): 调用百度API失败 - {str(e_req)}"
            except Exception as e_search_init:
                return f"人脸搜索执行错误: {str(e_search_init)}\\n{traceback.format_exc()}"
            
            if raw_result.get("error_code") == 0 and raw_result.get("result") and raw_result["result"].get("user_list"):
                best_match = None
                highest_score = 0
                for user_info_item in raw_result["result"]["user_list"]:
                    score = float(user_info_item["score"])
                    if score > highest_score:
                        highest_score = score
                        best_match = user_info_item
                
                if best_match and highest_score >= 80:
                    return f"操作 '拍照并搜索人脸' 完成:\n拍照并搜索成功: 用户ID='{best_match['user_id']}', 相似度得分='{highest_score:.2f}', 用户组='{best_match['group_id']}', 照片路径='{os.path.basename(image_path)}'"
                elif best_match:
                    return f"操作 '拍照并搜索人脸' 完成:\n拍照并搜索无高分匹配: 最高相似度得分 {highest_score:.2f} (用户ID='{best_match['user_id']}'), 未达到阈值80, 照片路径='{os.path.basename(image_path)}'"
                else:
                    return f"操作 '拍照并搜索人脸' 完成:\n拍照并搜索无匹配: 未在指定用户组中找到匹配的人脸, 照片路径='{os.path.basename(image_path)}'"
            elif raw_result.get("error_code") == 222207:
                return f"操作 '拍照并搜索人脸' 完成:\n拍照并搜索失败: 未在照片中检测到人脸, 照片路径='{os.path.basename(image_path)}' (API代码: {raw_result.get('error_code')}) - {raw_result.get('error_msg', '')}"
            elif raw_result.get("error_code") != 0:
                return f"操作 '拍照并搜索人脸' 完成:\n人脸搜索API错误: 代码='{raw_result.get('error_code', '未知')}', 信息='{raw_result.get('error_msg', '未知API错误')}', 照片路径='{os.path.basename(image_path)}'"
            else:
                return f"操作 '拍照并搜索人脸' 完成:\n拍照并搜索无匹配: 未检测到匹配的人脸或API响应格式非预期, 照片路径='{os.path.basename(image_path)}'"
            
        elif operation == "gesture_recognize":
            if not image_path or not os.path.exists(image_path):
                return f"调用错误: '手势识别'操作需要一个有效的图像文件路径，但收到 '{image_path}'。"

            if not hasattr(finally_hand, 'get_access_token') or not hasattr(finally_hand, 'gesture_recognize'):
                return "内部错误: 手势识别所需功能在 finally_hand.py 中未实现。"

            try:
                access_token = finally_hand.get_access_token(hand_api_key, hand_secret_key)
                raw_result = finally_hand.gesture_recognize(
                    image_path=image_path, 
                    access_token=access_token,
                    image_type_hint=image_type 
                )
                print(f"[DEBUG] 手势识别原始结果: {raw_result}")  # 调试信息

                # 检查结果格式
                if isinstance(raw_result, dict):
                    if "result" in raw_result and isinstance(raw_result["result"], list):
                        gestures = []
                        for item in raw_result["result"]:
                            if isinstance(item, dict) and "classname" in item and "probability" in item:
                                gesture_name = item["classname"]
                                probability = item["probability"]
                                gestures.append(f"{gesture_name} (置信度: {probability:.2f})")
                        
                        if gestures:
                            return f"手势识别成功: 检测到手势 - {', '.join(gestures)}, 图片: '{os.path.basename(image_path)}'"
                    
                    if "error_code" in raw_result and raw_result["error_code"] != 0:
                        return f"手势识别API错误: 代码='{raw_result.get('error_code', '未知')}', 信息='{raw_result.get('error_msg', '未知API错误')}', 图片: '{os.path.basename(image_path)}'"
                
                return f"手势识别结果: 未检测到明确手势, 图片: '{os.path.basename(image_path)}'"

            except requests.exceptions.RequestException as e_req:
                return f"网络请求错误 (手势识别): 调用百度API失败 - {str(e_req)}"
            except Exception as e_gesture_init:
                return f"手势识别执行错误: {str(e_gesture_init)}\\n{traceback.format_exc()}"

        elif operation == "face_add":
            if not image_path or not os.path.exists(image_path):
                return f"调用错误: '人脸注册'操作需要一个有效的图像文件路径，但收到 '{image_path}'。"
            if not user_id or not group_id:
                return "参数错误: '人脸注册'操作需要用户ID和用户组ID。"

            if not hasattr(finally_face, 'get_access_token') or not hasattr(finally_face, 'face_add'):
                return "内部错误: 人脸注册所需功能在 finally_face.py 中未实现。"

            try:
                access_token = finally_face.get_access_token(face_api_key, face_secret_key)
                raw_result = finally_face.face_add(
                    image_path=image_path, 
                    access_token=access_token, 
                    user_id=user_id, 
                    group_id=group_id,
                    quality_control=quality_control,
                    liveness_control=liveness_control,
                    image_type_hint=image_type 
                )
            except requests.exceptions.RequestException as e_req:
                return f"网络请求错误 (人脸注册): 调用百度API失败 - {str(e_req)}"
            except Exception as e_add_init:
                return f"人脸注册执行错误: {str(e_add_init)}\\n{traceback.format_exc()}"
                
            if raw_result.get("error_code") == 0 and raw_result.get("result"):
                face_token = raw_result["result"]["face_token"]
                return f"操作 '人脸注册' 完成:\n人脸注册成功: 用户ID='{user_id}', 用户组='{group_id}', 面部标识='{face_token}', 图片='{os.path.basename(image_path)}'"
            elif raw_result.get("error_code") != 0:
                error_msg = raw_result.get('error_msg', '未知API错误')
                if raw_result.get("error_code") == 222202 and "already exist" in error_msg.lower(): 
                     return f"操作 '人脸注册' 完成:\n人脸注册失败: 该图片中的人脸可能已在库中与用户ID '{user_id}' 关联。错误信息: {error_msg}"
                elif raw_result.get("error_code") == 222207: 
                     return f"操作 '人脸注册' 完成:\n人脸注册失败: 未在提供的图片 '{os.path.basename(image_path)}' 中检测到人脸。错误信息: {error_msg}"
                return f"操作 '人脸注册' 完成:\n人脸注册API错误: 代码='{raw_result.get('error_code', '未知')}', 信息='{error_msg}', 图片='{os.path.basename(image_path)}'"
            else: 
                return f"操作 '人脸注册' 完成:\n人脸注册失败: API响应格式非预期, 图片='{os.path.basename(image_path)}'"

        else:
            return f"调用错误: 不支持的操作类型 '{operation}'。"

    except NameError as e_name:
        return f"内部错误 (模块导入可能失败): {str(e_name)}\\n{traceback.format_exc()}"
    except FileNotFoundError as e_fnf: 
        return f"文件未找到错误: {str(e_fnf)}" # Should be caught by os.path.exists earlier
    except Exception as e_main:
        return f"执行操作 '{operation}' 时发生未知错误: {str(e_main)}\\n{traceback.format_exc()}"

# --- 测试代码 (仅当脚本作为主程序直接运行时执行) ---
if __name__ == '__main__':
    print("Python_Interface.py 正在作为主脚本运行 (用于测试)")

    # 默认API密钥 (请替换为您的真实密钥进行测试)
    # 注意：请确保您的百度AI账号已开通人脸识别和手势识别服务，并且API Key/Secret Key具有相应权限。
    test_api_key = "MXGoFiOVcDaxC2WFLvpPwaqK"  # 替换为你的API Key
    test_secret_key = "MVJJ3zXuaKNEDxIb7DGWAKWDQwWVnUEn"  # 替换为你的Secret Key
    
    # 确保测试图片目录和文件存在
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    test_image_for_add_gesture_dir = os.path.join(current_script_dir, "test Images")
    # 使用一张清晰的人脸图片进行注册和手势测试
    test_image_for_add_path = os.path.join(test_image_for_add_gesture_dir, "1.jpg") 
    
    if not os.path.exists(test_image_for_add_path):
        print(f"警告: 测试图片 '{test_image_for_add_path}' 不存在，部分测试可能无法进行或结果不准确。")
        # 可以尝试使用一个备用图片，或者让用户知道需要准备测试图片
        # test_image_for_add_path = "" # 如果图片不存在，后续测试会跳过或报错

    print(f"将使用API Key: {test_api_key[:5]}... , Secret Key: {test_secret_key[:5]}...")
    print(f"照片将保存到: {FULL_PHOTO_PATH}")
    if test_image_for_add_path and os.path.exists(test_image_for_add_path):
        print(f"用于注册/手势的测试图片: {test_image_for_add_path}")
    else:
        print(f"警告: 无法找到用于注册/手势的测试图片 '{test_image_for_add_path}'")


    # 1. 测试 take_photo_and_search
    print("\n--- 测试拍照并搜索 (take_photo_and_search) ---")
    # 对于此操作，image_path 参数在 call_baidu_api 中被忽略, user_id 也不需要
    result_photo_search = call_baidu_api("take_photo_and_search", "", test_api_key, test_secret_key, group_id="1")
    print("拍照并搜索结果:", result_photo_search)
    # 可以在这里添加对结果字符串的简单检查，例如是否包含 "成功" 或 "失败"

    # 2. 测试 gesture_recognize (需要一张测试图片)
    print("\n--- 测试手势识别 (gesture_recognize) ---")
    if test_image_for_add_path and os.path.exists(test_image_for_add_path):
        result_gesture = call_baidu_api("gesture_recognize", test_image_for_add_path, test_api_key, test_secret_key)
        print("手势识别结果:", result_gesture)
    else:
        print(f"  跳过手势识别测试，因为测试图片 '{test_image_for_add_path}' 不存在。")

    # 3. 测试 face_add (需要一张测试图片和用户ID)
    print("\n--- 测试人脸注册 (face_add) ---")
    # 每次测试建议使用不同的 user_id 以避免 "user is already exist" 错误，或者先确保该用户不存在
    # 可以考虑使用时间戳生成测试 user_id
    import time
    test_user_for_add = f"test_user_{int(time.time()) % 10000}" # 生成一个基于时间戳的测试用户ID
    test_group_for_add = "test_group_py" # 可以指定一个测试组

    print(f"  尝试注册用户ID: '{test_user_for_add}' 到组 '{test_group_for_add}'")
    if test_image_for_add_path and os.path.exists(test_image_for_add_path):
        result_face_add = call_baidu_api("face_add", test_image_for_add_path, test_api_key, test_secret_key, user_id=test_user_for_add, group_id=test_group_for_add)
        print(f"人脸注册结果 (用户ID: {test_user_for_add}):", result_face_add)
        # 如果注册成功，下次用同一个user_id和图片（或不同图片但同一个人脸）注册会报错
        # 可以尝试再次注册同一个用户，预期会得到API错误
        if "成功" in result_face_add:
             print(f"  尝试再次用相同图片注册用户 '{test_user_for_add}' (预期API会报错人脸或用户已存在)...")
             result_face_add_again = call_baidu_api("face_add", test_image_for_add_path, test_api_key, test_secret_key, user_id=test_user_for_add, group_id=test_group_for_add)
             print("  再次注册结果:", result_face_add_again)
    else:
        print(f"  跳过人脸注册测试，因为测试图片 '{test_image_for_add_path}' 不存在。")
    
    print("\n--- 测试一个不支持的操作 ---")
    result_unsupported = call_baidu_api("face_detect_removed", "", test_api_key, test_secret_key)
    print("不支持操作的结果:", result_unsupported)

    print("\n测试完成。请检查上面的输出。")
    print("提示: 如果 take_photo_and_search 持续返回 '未在照片中检测到人脸', 请确保：")
    print("1. 摄像头正常工作且未被其他程序占用。")
    print("2. 拍摄环境光线充足，人脸清晰且占画面主体。")
    print("3. 如果您的人脸尚未注册到百度人脸库的对应组中，搜索自然无法匹配成功，但至少应能检测到人脸。")
# --- 命令行接口的主执行部分 (如果脚本被直接运行) ---
if __name__ == '__main__':
    # 确保至少有操作类型和图像路径两个参数 (脚本名本身是 sys.argv[0])
    # 对于 take_photo_and_search，image_path 是保存路径
    if len(sys.argv) < 3:
        print(json.dumps({"error": "错误: 缺少参数。至少需要提供操作类型和图像/保存路径。"}, ensure_ascii=False))
        sys.exit(1)

    # 从命令行参数获取操作所需的基本信息
    operation_arg = sys.argv[1]
    image_path_arg = sys.argv[2]
    
    # API密钥和秘钥：优先从命令行参数获取，若未提供则使用占位符或默认值
    # 建议：对于生产环境或频繁使用，应通过更安全的方式管理密钥，例如环境变量或配置文件
    api_key_arg = "MXGoFiOVcDaxC2WFLvpPwaqK" # 默认或从配置读取
    secret_key_arg = "MVJJ3zXuaKNEDxIb7DGWAKWDQwWVnUEn" # 默认或从配置读取
    if len(sys.argv) > 3: api_key_arg = sys.argv[3]
    if len(sys.argv) > 4: secret_key_arg = sys.argv[4]

    # 特定操作可能需要的额外参数
    user_id_arg = None
    group_id_arg = "1" # 默认用户组ID

    if operation_arg == "face_add":
        if len(sys.argv) > 5:
            user_id_arg = sys.argv[5]
        else:
            print(json.dumps({"error": "错误: 人脸注册 (face_add) 操作需要 user_id。"}, ensure_ascii=False))
            sys.exit(1)
        if len(sys.argv) > 6: group_id_arg = sys.argv[6]
    elif operation_arg == "face_search" or operation_arg == "take_photo_and_search":
        if len(sys.argv) > 5: group_id_arg = sys.argv[5] # group_id 是可选的第五个参数 (在api_key, secret_key之后)
        # 注意：对于 take_photo_and_search，如果命令行参数顺序固定为 op, path, ak, sk, group_id，
        # 那么 group_id 会是 sys.argv[5]。如果 ak, sk 省略，则 group_id 可能是 sys.argv[3]。
        # 这里假设 ak, sk 总是提供或有默认值，group_id 是它们之后的参数。
        # 为了更清晰，可以调整参数解析逻辑，例如使用 argparse 模块。
        # 当前的简单实现：如果提供了第五个参数，就认为是 group_id。
        # 如果 API Key 和 Secret Key 是通过命令行传入的，那么 group_id 应该是 sys.argv[5] (如果 api_key, secret_key 在 image_path 之后)
        # 或者 sys.argv[7] (如果 api_key, secret_key 在 user_id 之后，但这不适用于 face_search)
        # 假设顺序: python Python_Interface.py <operation> <image_path> [api_key] [secret_key] [group_id_for_search]
        # 如果 api_key 和 secret_key 是通过 sys.argv[3] 和 sys.argv[4] 传入的，那么 group_id 就是 sys.argv[5]
        if len(sys.argv) > 5 and operation_arg != "face_add": # 避免与 face_add 的 user_id 冲突
             # 如果 api_key 和 secret_key 是通过 sys.argv[3] 和 sys.argv[4] 传入的
            if len(sys.argv) == 6: # op, path, ak, sk, group_id
                 group_id_arg = sys.argv[5]
            elif len(sys.argv) > 5 and not (len(sys.argv) > 3 and sys.argv[3] != api_key_arg) and not (len(sys.argv) > 4 and sys.argv[4] != secret_key_arg):
                # 这个条件复杂了，简化：如果提供了第5个参数，且不是face_add，就认为是group_id
                # 更好的做法是使用argparse
                pass # group_id_arg 保持默认 "1" 或从上面已设置的 sys.argv[5] 获取

    # 调用核心函数处理请求
    response_json = call_baidu_api(
        operation_arg,
        image_path_arg,
        api_key_arg,
        secret_key_arg,
        user_id=user_id_arg,
        group_id=group_id_arg
    )
    
    # 打印最终的JSON响应
    print(response_json)

    # 根据返回结果决定退出码 (可选)
    try:
        response_data = json.loads(response_json)
        if "error" in response_data:
            sys.exit(1) # 如果响应中包含错误，以状态码1退出
        else:
            sys.exit(0) # 成功则以状态码0退出
    except json.JSONDecodeError:
        sys.exit(2) # 如果响应不是有效的JSON，以状态码2退出
