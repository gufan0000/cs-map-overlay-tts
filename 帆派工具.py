import mss
import cv2
import numpy as np
import time
import tkinter as tk
import tkinter.ttk as ttk
import threading
from queue import Queue
from PIL import Image, ImageTk
from tkinter import filedialog
import sys
import os
import keyboard
import re
import pyttsx3

########################################
# 初始化 TTS 引擎
engine = pyttsx3.init()
# 全局音量变量（0.0 ~ 1.0），初始100%
volume_level = 1.0
def speak_message(message):
    """调用 TTS 播报消息，设置音量，并在当前线程中执行"""
    engine.setProperty("volume", volume_level)
    engine.say(message)
    engine.runAndWait()

########################################
# 全局语音队列，用于存放 (timestamp, message) 元组
voice_queue = Queue()

def voice_worker():
    while True:
        ts, msg = voice_queue.get()
        # 如果该消息延迟超过 1.5 秒，则跳过
        if time.time() - ts > 1.5:
            voice_queue.task_done()
            continue
        speak_message(msg)
        voice_queue.task_done()

threading.Thread(target=voice_worker, daemon=True).start()

########################################
# 资源路径处理函数
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

########################################
# 从 TXT 文件加载区域定义 (dust2.txt)
def load_region_definitions(txt_file):
    """
    支持“区域名:坐标”格式，坐标可跨行，直到下一个区域名出现。
    返回 {区域名: np.array([[x1,y1],[x2,y2],...]), ...}
    """
    with open(txt_file, "r", encoding="utf-8") as f:
        content = f.read()
    re_region = re.compile(
        r'([\w\u4e00-\u9fa5]+)\s*[:：]'
        r'(.*?)'
        r'(?=[\w\u4e00-\u9fa5]+\s*[:：]|$)',
        flags=re.S
    )
    re_coords = re.compile(r'[（(]\s*(\d+)\s*,\s*(\d+)\s*[)）]')
    region_dict = {}
    for match in re_region.finditer(content):
        region_name = match.group(1).strip()
        coords_block = match.group(2)
        points = re_coords.findall(coords_block)
        if not points:
            continue
        poly = []
        for (sx, sy) in points:
            poly.append((int(sx), int(sy)))
        region_dict[region_name] = np.array(poly, dtype=np.int32)
    return region_dict

########################################
# 截屏区域参数
monitor = {"top": 40, "left": 40, "width": 436, "height": 434}

########################################
# 敌人、队友、C4 参数
enemy_color = (23, 22, 223)
enemy_tolerance = 15
teammate_colors = [
    (125, 154, 0),
    (41, 125, 223),
    (237, 200, 132),
    (146, 43, 183),
    (64, 221, 234)
]
teammate_tolerance = 1

########################################
# 加载 dust2.txt 以获取区域定义
dust2_txt_path = resource_path("dust2.txt")
region_definitions = load_region_definitions(dust2_txt_path)
if not region_definitions:
    raise ValueError("无法从 dust2.txt 中读取到任何区域定义，请检查文件格式")

########################################
# 加载 dust2.png (代替原 full_minimap)
dust2_img_path = resource_path("dust2.png")
dust2_map = cv2.imread(dust2_img_path)
if dust2_map is None:
    raise ValueError("无法加载 dust2.png，请检查文件是否存在")

########################################
# 加载 c4_template.png
template = cv2.imread(resource_path("c4_template.png"))
if template is None:
    raise ValueError("无法加载 c4_template.png，请检查文件是否存在")
template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
w_temp, h_temp = template_gray.shape[::-1]

########################################
# 初始化 ORB (nfeatures=300)
orb = cv2.ORB_create(nfeatures=300)
kp_full, des_full = orb.detectAndCompute(dust2_map, None)

########################################
# 根据坐标查找区域名
def get_region_name(full_pt):
    for region_name, poly in region_definitions.items():
        if cv2.pointPolygonTest(poly, full_pt, False) >= 0:
            return region_name
    return None

########################################
# 创建主窗口（文字显示）
root = tk.Tk()
root.title("游戏信息")
root.attributes("-topmost", True)
root.geometry("500x300+10+600")
root.configure(bg="black")
root.overrideredirect(True)
root.attributes("-transparentcolor", "black")

# 全局变量：语音开关（voice_enabled 控制 TTS 播报）
voice_enabled = tk.BooleanVar(value=False)

# 文字显示、检测、队友显示相关变量与快捷键
enable_detection_var = tk.BooleanVar(value=True)  # 是否开启检测
check_var = tk.BooleanVar(value=True)             # 是否显示文字
show_team_var = tk.BooleanVar(value=True)           # 是否显示队友位置

close_shortcut = tk.StringVar(value="F12")
display_toggle_key = tk.StringVar(value="F11")
team_toggle_key = tk.StringVar(value="F10")
detection_toggle_key = tk.StringVar(value="F9")    # 切换检测的快捷键
voice_toggle_key = tk.StringVar(value="F8")        # 切换语音播报的快捷键

team_label_color_var = tk.StringVar(value="white")
team_number_color_var = tk.StringVar(value="yellow")
team_label_size_var = tk.StringVar(value="中")
team_number_size_var = tk.StringVar(value="中")
font_size_map = {"小": 14, "中": 16, "大": 20}

display_text = tk.Text(
    root, bg="black", fg="white",
    font=("KaiTi", 16, "bold"),
    bd=0, highlightthickness=0
)
display_text.configure(state=tk.DISABLED)

########################################
# 定义关闭程序函数
def close_program(event=None):
    root.quit()
    sys.exit()

########################################
# 更新所有快捷键
def update_all_hotkeys():
    for hk in [close_shortcut.get(), display_toggle_key.get(), team_toggle_key.get(),
               detection_toggle_key.get(), voice_toggle_key.get()]:
        if hk:
            try:
                keyboard.remove_hotkey(hk)
            except:
                pass
    if close_shortcut.get():
        keyboard.add_hotkey(close_shortcut.get(), close_program)
    if display_toggle_key.get():
        keyboard.add_hotkey(display_toggle_key.get(), handle_text_display_hotkey)
    if team_toggle_key.get():
        keyboard.add_hotkey(team_toggle_key.get(), handle_team_toggle_hotkey)
    if detection_toggle_key.get():
        keyboard.add_hotkey(detection_toggle_key.get(), handle_detection_hotkey)
    if voice_toggle_key.get():
        keyboard.add_hotkey(voice_toggle_key.get(), handle_voice_toggle_hotkey)

########################################
# 快捷键处理函数
def handle_text_display_hotkey():
    check_var.set(not check_var.get())
    toggle_text_display()

def handle_team_toggle_hotkey():
    show_team_var.set(not show_team_var.get())

def handle_detection_hotkey():
    enable_detection_var.set(not enable_detection_var.get())
    toggle_detection()

def handle_voice_toggle_hotkey():
    voice_enabled.set(not voice_enabled.get())

update_all_hotkeys()

########################################
# 切换文字显示
def toggle_text_display():
    if check_var.get():
        display_text.pack(expand=True, fill=tk.BOTH)
    else:
        display_text.pack_forget()

########################################
# 切换检测开关
def toggle_detection():
    if enable_detection_var.get():
        if check_var.get():
            display_text.pack(expand=True, fill=tk.BOTH)
    else:
        display_text.configure(state=tk.NORMAL)
        display_text.delete("1.0", tk.END)
        display_text.configure(state=tk.DISABLED)
        display_text.pack_forget()

toggle_text_display()
toggle_detection()

########################################
# 文字显示更新函数
def update_gui(team_counts, enemy_text, c4_text):
    display_text.configure(state=tk.NORMAL)
    display_text.delete("1.0", tk.END)
    
    label_color = team_label_color_var.get()
    number_color = team_number_color_var.get()
    label_size = font_size_map[team_label_size_var.get()]
    number_size = font_size_map[team_number_size_var.get()]
    
    display_text.tag_configure("label", foreground=label_color, font=("KaiTi", label_size, "bold"))
    display_text.tag_configure("number", foreground=number_color, font=("KaiTi", number_size, "bold"))
    display_text.tag_configure("red", foreground="red", font=("KaiTi", number_size, "bold"))
    
    if show_team_var.get():
        for region in ["A平台", "A大", "A小"]:
            display_text.insert(tk.END, f"{region}:", "label")
            cnt = team_counts.get(region, 0)
            if cnt > 0:
                display_text.insert(tk.END, str(cnt), "number")
            display_text.insert(tk.END, "  ")
        display_text.insert(tk.END, "\n")
        for region in ["B点", "B通", "沙地"]:
            display_text.insert(tk.END, f"{region}:", "label")
            cnt = team_counts.get(region, 0)
            if cnt > 0:
                display_text.insert(tk.END, str(cnt), "number")
            display_text.insert(tk.END, "  ")
        display_text.insert(tk.END, "\n\n")
    else:
        display_text.insert(tk.END, "\n\n")
    
    # 只播报敌人的位置，直接播区域信息
    display_text.insert(tk.END, "敌人:", "label")
    display_text.insert(tk.END, enemy_text + "\n", "red")
    
    display_text.insert(tk.END, "C4:", "label")
    display_text.insert(tk.END, c4_text, "number")
    
    display_text.configure(state=tk.DISABLED)

########################################
# 创建 Queue
data_queue = Queue()

########################################
# 图像处理线程
def process_image():
    with mss.mss() as sct:
        while True:
            if not enable_detection_var.get():
                time.sleep(0.5)
                continue

            start_time = time.time()
            sct_img = np.array(sct.grab(monitor))
            mini_map = cv2.cvtColor(sct_img, cv2.COLOR_BGRA2BGR)

            markers = []
            # --- 敌人检测 ---
            lower_enemy = np.array([max(c - enemy_tolerance, 0) for c in enemy_color])
            upper_enemy = np.array([min(c + enemy_tolerance, 255) for c in enemy_color])
            enemy_mask = cv2.inRange(mini_map, lower_enemy, upper_enemy)
            contours_enemy, _ = cv2.findContours(enemy_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours_enemy:
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = int(M["m10"]/M["m00"])
                    cy = int(M["m01"]/M["m00"])
                    markers.append({"type": "Enemy", "pt": (cx, cy), "region": None})
            # --- 队友检测 ---
            teammate_mask = np.zeros(mini_map.shape[:2], dtype=np.uint8)
            for color in teammate_colors:
                lower_team = np.array([max(x - teammate_tolerance, 0) for x in color])
                upper_team = np.array([min(x + teammate_tolerance, 255) for x in color])
                mask = cv2.inRange(mini_map, lower_team, upper_team)
                teammate_mask = cv2.bitwise_or(teammate_mask, mask)
            contours_team, _ = cv2.findContours(teammate_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours_team:
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = int(M["m10"]/M["m00"])
                    cy = int(M["m01"]/M["m00"])
                    markers.append({"type": "Teammate", "pt": (cx, cy), "region": None})
            # --- C4检测 (阈值0.7) ---
            mini_gray = cv2.cvtColor(mini_map, cv2.COLOR_BGR2GRAY)
            result = cv2.matchTemplate(mini_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            thresh = 0.7
            loc = np.where(result >= thresh)
            for pt in zip(*loc[::-1]):
                center = (pt[0] + w_temp//2, pt[1] + h_temp//2)
                markers.append({"type": "C4", "pt": center, "region": None})
            # --- ORB 特征匹配 => 坐标映射 ---
            kp_mini, des_mini = orb.detectAndCompute(mini_map, None)
            H = None
            if des_mini is not None and len(des_mini) >= 10:
                bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                matches = bf.match(des_mini, des_full)
                if len(matches) >= 10:
                    src_pts = np.float32([kp_mini[m.queryIdx].pt for m in matches]).reshape(-1,1,2)
                    dst_pts = np.float32([kp_full[m.trainIdx].pt for m in matches]).reshape(-1,1,2)
                    H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            # --- 根据映射结果获取区域 ---
            for marker in markers:
                pt_2d = np.array([[marker["pt"]]], dtype=np.float32)
                if H is not None:
                    transformed_pt = cv2.perspectiveTransform(pt_2d, H)[0][0]
                    full_pt = (int(transformed_pt[0]), int(transformed_pt[1]))
                else:
                    full_pt = marker["pt"]
                marker["region"] = get_region_name(full_pt)
            # --- 统计队友 ---
            team_counts = {"A平台": 0, "A大": 0, "A小": 0, "B点": 0, "B通": 0, "沙地": 0}
            for mk in markers:
                if mk["type"]=="Teammate" and mk["region"] is not None:
                    r = mk["region"]
                    if r in team_counts:
                        team_counts[r] += 1
                    elif r in ("A小楼梯", "A小中路"):
                        team_counts["A小"] += 1
            enemies_text = ",".join(sorted(
                set(mk["region"] for mk in markers if mk["type"]=="Enemy" and mk["region"])
            ))
            c4_text = ",".join(sorted(
                set(mk["region"] for mk in markers if mk["type"]=="C4" and mk["region"])
            ))
            data_queue.put((team_counts, enemies_text, c4_text))
            elapsed_time = time.time() - start_time
            time.sleep(max(0, 0.5 - elapsed_time))

threading.Thread(target=process_image, daemon=True).start()

def poll_queue():
    try:
        data = data_queue.get_nowait()
        if data:
            update_gui(*data)
            # 语音播报逻辑：只针对敌人区域播报
            if voice_enabled.get():
                global last_broadcast
                team_counts, enemy_text, c4_text = data
                current_time = time.time()
                # 对于敌人区域，拆分为单个区域（以逗号分隔）
                regions = [r.strip() for r in enemy_text.split(",") if r.strip()]
                # 对每个区域，如果距离上次播报超过5秒，则入队播报，并更新记录
                for region in regions:
                    last_time = last_broadcast.get(region, 0)
                    if current_time - last_time >= 5:
                        voice_queue.put((time.time(), region))
                        last_broadcast[region] = current_time
        # 如果检测关闭，则不更新文字
    except:
        pass
    root.after(100, poll_queue)

# 全局字典记录每个区域上次播报时间
last_broadcast = {}

root.after(100, poll_queue)

########################################
# 设置窗口（Notebook 标签页）
def create_setting_ui():
    setting_window = tk.Toplevel(root)
    setting_window.title("设置")
    setting_window.geometry("500x600+520+400")  # 扩大窗口
    setting_window.resizable(False, False)
    
    notebook = ttk.Notebook(setting_window)
    notebook.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
    
    # 标签页1：文字设置
    text_frame = tk.Frame(notebook, bg="white")
    notebook.add(text_frame, text="文字设置")
    
    hotkey_frame = tk.Frame(text_frame, bg="white")
    hotkey_frame.pack(pady=8, fill=tk.X)
    # 快捷键顺序：关闭软件、切换检测、切换显示位置、切换队友位置、切换语音播报
    tk.Label(hotkey_frame, text="按键关闭软件", font=("KaiTi", 12), bg="white").grid(row=0, column=0, padx=4)
    close_entry = tk.Entry(hotkey_frame, textvariable=close_shortcut, font=("KaiTi", 12), width=5)
    close_entry.grid(row=0, column=1, padx=4)
    
    tk.Label(hotkey_frame, text="切换检测", font=("KaiTi", 12), bg="white").grid(row=0, column=2, padx=4)
    detect_entry = tk.Entry(hotkey_frame, textvariable=detection_toggle_key, font=("KaiTi", 12), width=5)
    detect_entry.grid(row=0, column=3, padx=4)
    
    tk.Label(hotkey_frame, text="切换显示位置", font=("KaiTi", 12), bg="white").grid(row=0, column=4, padx=4)
    display_entry = tk.Entry(hotkey_frame, textvariable=display_toggle_key, font=("KaiTi", 12), width=5)
    display_entry.grid(row=0, column=5, padx=4)
    
    tk.Label(hotkey_frame, text="切换队友位置", font=("KaiTi", 12), bg="white").grid(row=1, column=0, padx=4)
    team_entry = tk.Entry(hotkey_frame, textvariable=team_toggle_key, font=("KaiTi", 12), width=5)
    team_entry.grid(row=1, column=1, padx=4)
    
    tk.Label(hotkey_frame, text="切换语音播报", font=("KaiTi", 12), bg="white").grid(row=1, column=2, padx=4)
    voice_entry = tk.Entry(hotkey_frame, textvariable=voice_toggle_key, font=("KaiTi", 12), width=5)
    voice_entry.grid(row=1, column=3, padx=4)
    
    update_button = tk.Button(text_frame, text="更新文字快捷键", font=("KaiTi", 12),
                              command=update_all_hotkeys)
    update_button.pack(pady=6)
    
    # 选项部分：依次为：开启检测、显示位置、显示队友位置
    detect_check = tk.Checkbutton(text_frame, text="开启检测",
                                  variable=enable_detection_var,
                                  command=toggle_detection,
                                  font=("KaiTi", 12), bg="white")
    detect_check.pack(pady=6)
    check_button = tk.Checkbutton(text_frame, text="显示位置",
                                  variable=check_var,
                                  command=toggle_text_display,
                                  font=("KaiTi", 12), bg="white")
    check_button.pack(pady=6)
    team_check = tk.Checkbutton(text_frame, text="显示队友位置",
                                variable=show_team_var,
                                font=("KaiTi", 12), bg="white")
    team_check.pack(pady=6)
    
    # 在颜色与字体设置下面加入语音设置部分
    tk.Label(text_frame, text="", bg="white").pack(pady=4)
    tk.Label(text_frame, text="语音设置", font=("KaiTi", 12, "bold"), bg="white").pack()
    voice_check = tk.Checkbutton(text_frame, text="开启语音播报 (TTS)",
                                 variable=voice_enabled,
                                 font=("KaiTi", 12), bg="white")
    voice_check.pack(pady=6)
    
    # 语音音量调节（0~100，默认100）
    volume_label = tk.Label(text_frame, text="语音音量", font=("KaiTi", 12), bg="white")
    volume_label.pack(pady=4)
    volume_scale = tk.Scale(text_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=300)
    volume_scale.set(100)
    volume_scale.pack(pady=4)
    def update_volume(val):
        global volume_level
        volume_level = float(val) / 100.0
    volume_scale.config(command=update_volume)
    
    def on_hotkey_changed(*_):
        update_all_hotkeys()
    for w in [close_entry, display_entry, team_entry, detect_entry, voice_entry]:
        w.bind("<KeyRelease>", on_hotkey_changed)

threading.Thread(target=create_setting_ui, daemon=True).start()

root.mainloop()
