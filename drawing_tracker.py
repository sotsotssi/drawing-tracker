import math
import time
import platform
import os
import sys
import datetime
import tkinter.messagebox as messagebox
import customtkinter as ctk
from pynput import mouse, keyboard
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont


if platform.system() == "Windows":
    UI_FONT = "Malgun Gothic"
elif platform.system() == "Darwin":
    UI_FONT = "Apple SD Gothic Neo"
else:
    UI_FONT = "sans-serif"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class WorkTracker:
    def __init__(self, dpi=96):
        self.clicks = 0
        self.strokes = 0
        self.undo_count = 0
        self.total_pixels = 0.0
        self.dpi = dpi
        
        self.is_dragging = False
        self.current_drag_distance = 0.0
        self.movement_threshold = 5.0
        self.last_pos = (0, 0)
        self.points = []
        self.running = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.ctrl_pressed = False

    def get_distance_in_meters(self):
        inches = self.total_pixels / self.dpi
        return inches * 0.0254

    def on_move(self, x, y):
        if self.is_dragging and self.running:
            dx = x - self.last_pos[0]
            dy = y - self.last_pos[1]
            distance = math.hypot(dx, dy)
            
            self.total_pixels += distance
            self.current_drag_distance += distance
            self.last_pos = (x, y)
            self.points.append((x, y))

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left and self.running:
            if pressed:
                self.is_dragging = True
                self.current_drag_distance = 0.0
                self.last_pos = (x, y)
                self.points.append((x, y))
            else:
                self.is_dragging = False
                if self.current_drag_distance > self.movement_threshold:
                    self.strokes += 1
                else:
                    self.clicks += 1

    def on_key_press(self, key):
        if not self.running:
            return
        
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.cmd, keyboard.Key.cmd_r):
            self.ctrl_pressed = True
            
        if self.ctrl_pressed:
            is_z = False
            if hasattr(key, 'char') and key.char in ('z', 'Z', '\x1a'):
                is_z = True
            elif hasattr(key, 'vk') and key.vk in (90, 122):
                is_z = True
                
            if is_z:
                self.undo_count += 1

    def on_key_release(self, key):
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.cmd, keyboard.Key.cmd_r):
            self.ctrl_pressed = False

    def start(self):
        self.running = True
        self.mouse_listener = mouse.Listener(on_move=self.on_move, on_click=self.on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def stop(self):
        self.running = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()


class ReportGenerator:
    @staticmethod
    def get_metaphor(meters):
        if meters < 1: return "귀여운 고양이 한 마리 길이"
        if meters < 5: return "중형 자동차 한 대 길이"
        if meters < 15: return "커다란 시내버스 길이"
        if meters < 50: return "10층짜리 아파트 높이"
        if meters < 100: return "자유의 여신상 높이"
        if meters < 300: return "63빌딩 높이"
        if meters < 500: return "에펠탑 높이"
        if meters < 1000: return "부르즈 할리파 높이"
        return "백두산 정상을 향해! (1km 돌파)"

    @staticmethod
    def get_korean_font(size):
        system = platform.system()
        font_path = None
        if system == 'Windows':
            font_path = 'C:/Windows/Fonts/malgun.ttf'
        elif system == 'Darwin':
            font_path = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
        
        try:
            return ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
        except:
            return ImageFont.load_default()

    @staticmethod
    def create_summary_card(tracker, start_time):
        if not tracker.points:
            return False

        print("요약 카드를 생성 중입니다...")
        
        x_coords = [p[0] for p in tracker.points]
        y_coords = [p[1] for p in tracker.points]
        
        max_x = max(max(x_coords), 1920)
        max_y = max(max(y_coords), 1080)
        aspect_ratio = max_y / max_x
        
        fig_width = 8
        fig_height = fig_width * aspect_ratio
        
        plt.figure(figsize=(fig_width, fig_height), dpi=150)
        plt.hist2d(
            x_coords, y_coords, 
            bins=[150, int(150 * aspect_ratio)], 
            range=[[0, max_x], [0, max_y]], 
            cmap='turbo', cmin=1
        )
        
        plt.gca().invert_yaxis()
        plt.gca().set_aspect('equal', adjustable='box')
        plt.axis('off')
        
        temp_heatmap = "temp_heatmap.png"
        plt.savefig(temp_heatmap, bbox_inches='tight', pad_inches=0, transparent=True)
        plt.close()

        card_size = (1000, 1000)
        card = Image.new('RGB', card_size, color='#18181b')
        draw = ImageDraw.Draw(card)
        
        heatmap_img = Image.open(temp_heatmap).convert("RGBA")
        heatmap_img.thumbnail((900, 560))
        hm_x = (card_size[0] - heatmap_img.width) // 2
        hm_y = 170
        card.paste(heatmap_img, (hm_x, hm_y), heatmap_img)
        os.remove(temp_heatmap)

        font_title = ReportGenerator.get_korean_font(46)
        font_stat = ReportGenerator.get_korean_font(34)
        font_sub = ReportGenerator.get_korean_font(28)
        
        meters = tracker.get_distance_in_meters()
        metaphor = ReportGenerator.get_metaphor(meters)
        work_time = str(datetime.timedelta(seconds=int(time.time() - start_time)))
        date_str = datetime.datetime.now().strftime("%Y년 %m월 %d일의 기록")

        draw.text((50, 50), "오늘의 작업 요약", font=font_title, fill="#10b981")
        draw.text((50, 110), date_str, font=font_sub, fill="#a1a1aa")
        
        draw.line((50, 160, 950, 160), fill="#27272a", width=2)
        draw.line((50, 750, 950, 750), fill="#27272a", width=2)

        stat_y = 780
        draw.text((50, stat_y), f"작업 시간 :  {work_time}", font=font_stat, fill="#ffffff")
        
        draw.text((50, stat_y + 60), f"클릭 :  {tracker.clicks:,} 회", font=font_stat, fill="#60a5fa")
        draw.text((380, stat_y + 60), f"선 긋기 :  {tracker.strokes:,} 회", font=font_stat, fill="#c084fc")
        draw.text((700, stat_y + 60), f"취소 :  {tracker.undo_count:,} 회", font=font_stat, fill="#fbbf24")
        
        draw.text((50, stat_y + 120), f"그린 거리 :  {meters:.2f} m", font=font_stat, fill="#f472b6")
        draw.text((450, stat_y + 123), f"({metaphor})", font=font_sub, fill="#9ca3af")

        # 파일 저장
        output_filename = f"work_summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        card.save(output_filename)
        return output_filename


class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("그림 만보기")
        self.root.geometry("420x580")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass
        
        self.tracker = WorkTracker()
        self.start_time = 0
        self.is_tracking = False

        self.setup_ui()
        self.update_loop()

    def create_stat_card(self, parent, row, col, title, initial_value, text_color):
        """2x2 대시보드 형태의 통계 카드를 생성하는 유틸리티 함수"""
        card = ctk.CTkFrame(parent, fg_color="#18181b", corner_radius=12)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        
        title_label = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family=UI_FONT, size=13), text_color="#a1a1aa")
        title_label.pack(pady=(12, 2))
        
        value_label = ctk.CTkLabel(card, text=initial_value, font=ctk.CTkFont(family=UI_FONT, size=20, weight="bold"), text_color=text_color)
        value_label.pack(pady=(0, 12))
        
        return value_label

    def setup_ui(self):
        self.header_label = ctk.CTkLabel(self.root, text="그림 만보기 @bb_uu_t", font=ctk.CTkFont(family=UI_FONT, size=22, weight="bold"), text_color="#10b981")
        self.header_label.pack(pady=(20, 5))
        
        self.time_label = ctk.CTkLabel(self.root, text="00:00:00", font=ctk.CTkFont(family=UI_FONT, size=40, weight="bold"), text_color="#f4f4f5")
        self.time_label.pack(pady=(5, 15))
        
        self.grid_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.grid_frame.pack(padx=20, fill="x")
        self.grid_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.clicks_label = self.create_stat_card(self.grid_frame, 0, 0, "클릭", "0 회", "#60a5fa")
        self.strokes_label = self.create_stat_card(self.grid_frame, 0, 1, "선 긋기", "0 회", "#c084fc")
        self.undo_label = self.create_stat_card(self.grid_frame, 1, 0, "뒤로가기 (Ctrl+Z)", "0 회", "#fbbf24")
        self.dist_label = self.create_stat_card(self.grid_frame, 1, 1, "그린 거리", "0.00 m", "#f472b6")
        
        self.slider_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.slider_frame.pack(fill="x", padx=30, pady=(20, 5))
        
        self.slider_label = ctk.CTkLabel(self.slider_frame, text="타블렛 민감도 (클릭/선 구분 거리)", font=ctk.CTkFont(family=UI_FONT, size=12), text_color="#a1a1aa")
        self.slider_label.pack(pady=(0, 5))
        
        self.thresh_scale = ctk.CTkSlider(self.slider_frame, from_=1, to=20, command=self.update_threshold)
        self.thresh_scale.set(5)
        self.thresh_scale.pack(fill="x")
        
        self.start_btn = ctk.CTkButton(self.root, text="기록 시작", font=ctk.CTkFont(family=UI_FONT, size=16, weight="bold"), 
                                       fg_color="#10b981", hover_color="#059669", text_color="black", height=48, corner_radius=10, command=self.toggle_tracking)
        self.start_btn.pack(pady=(20, 10), padx=30, fill="x")


    def update_threshold(self, val):
        self.tracker.movement_threshold = float(val)

    def toggle_tracking(self):
        if not self.is_tracking:
            self.tracker.points = []
            self.tracker.clicks = 0
            self.tracker.strokes = 0
            self.tracker.undo_count = 0
            self.tracker.total_pixels = 0
            self.start_time = time.time()
            self.tracker.start()
            
            self.is_tracking = True
            self.start_btn.configure(text="기록 종료 및 요약 카드 저장", fg_color="#f43f5e", hover_color="#e11d48", text_color="white")
        else:
            self.tracker.stop()
            self.is_tracking = False
            self.start_btn.configure(text="기록 시작", fg_color="#10b981", hover_color="#059669", text_color="black")
            
            saved_file = ReportGenerator.create_summary_card(self.tracker, self.start_time)
            if saved_file:
                messagebox.showinfo("저장 완료", f"작업 요약 카드가 저장되었습니다!\n파일명: {saved_file}")
            else:
                messagebox.showwarning("데이터 없음", "기록된 작업이 없어 카드를 생성하지 않았습니다.")
            
            self.time_label.configure(text="00:00:00")
            self.clicks_label.configure(text="0 회")
            self.strokes_label.configure(text="0 회")
            self.undo_label.configure(text="0 회")
            self.dist_label.configure(text="0.00 m")

    def update_loop(self):
        if self.is_tracking:
            elapsed = int(time.time() - self.start_time)
            self.time_label.configure(text=str(datetime.timedelta(seconds=elapsed)))
            self.clicks_label.configure(text=f"{self.tracker.clicks:,} 회")
            self.strokes_label.configure(text=f"{self.tracker.strokes:,} 회")
            self.undo_label.configure(text=f"{self.tracker.undo_count:,} 회")
            self.dist_label.configure(text=f"{self.tracker.get_distance_in_meters():.2f} m")
        
        self.root.after(100, self.update_loop)

    def on_closing(self):
        if self.is_tracking:
            self.tracker.stop()
        self.root.destroy()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("green")
    
    root = ctk.CTk()
    app = AppGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()