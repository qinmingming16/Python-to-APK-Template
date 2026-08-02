import sys
import traceback
import os
import json
import array
import threading
import time
import gc
import base64
# KivyMD核心导入
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
# Kivy核心导入
from kivy.uix.scrollview import ScrollView
from kivy.config import Config
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.clock import Clock, mainthread
from kivy.metrics import dp
from kivy.core.window import Window
from jnius import autoclass, PythonJavaClass, java_method, cast
from jnius import JavaException
from android.runnable import run_on_ui_thread
from android import activity

# ========== 全局日志类 ==========
class GlobalLogger:
    """
    全局日志管理类
    作用：记录全链路日志，限制最大条数，支持UI实时展示
    """
    def __init__(self):
        self.logs = []  # 日志列表
    
    def log(self, level, msg):
        """记录日志：添加时间戳，限制最大条数"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        log_msg = f"[{timestamp}] [{level}] {msg}"
        self.logs.append(log_msg)
        if len(self.logs) > 10:
            self.logs.pop(0)
        print(log_msg)
        return log_msg
    
    def get_all_logs(self):
        """获取所有日志拼接字符串"""
        return "\n".join(self.logs)
# 全局日志实例
logger = GlobalLogger()

# ========== 全局配置 ==========
try:
    LabelBase.register(name='Roboto', fn_regular='fonts/SourceHanSansSC.otf')
    logger.log("INFO", "字体注册成功")
except Exception as e:
    LabelBase.register(name='Roboto', fn_regular=DEFAULT_FONT)
    logger.log("ERROR", f"注册失败，使用默认字体:{e}")
# ========== 多键配置（100%完全保留） ==========
KEY_NAME_TO_GESTURE_COORD_MAP = {
    "Q": (545, 575),
    "W": (755, 575),
    "E": (965, 575),
    "R": (1175, 575),
    "T": (1385, 575),
    "Y": (1595, 575),
    "U": (1805, 575),
    "A": (545, 745),
    "S": (755, 745),
    "D": (965, 745),
    "F": (1175, 745),
    "G": (1385, 745),
    "H": (1595, 745),
    "J": (1805, 745),
    "Z": (545, 915),
    "X": (755, 915),
    "C": (965, 915),
    "V": (1175, 915),
    "B": (1385, 915),
    "N": (1595, 915),
    "M": (1805, 915),
}

SHEET_META_TMP = {}
SHEET_CONFIG = {
    "jianzhu": {
        "need_speed": True,
        "is_int": False,
        "min": 20.0,
        "max": 300.0,
        "suffix": [".txt"]
    },
    "zhijian": {
        "need_speed": False,
        "suffix": [".txt"]
    },
    "guagua": {
        "need_speed": True,
        "is_int": False,
        "min": 10.0,
        "max": 400.0,
        "suffix": [".txt"]
    },
    "midi": {
        "need_speed": True,
        "is_int": True,
        "min": 30,
        "max": 240,
        "suffix": [".mid"]
    }
}

# ========== 新增琴谱全局列表【无原有代码修改】 ==========
SHEET_FILE_LIST = []
FILE_PICK_REQ_CODE = 1001

COLLECT_TIMEOUT = 0.05
CLICK_INTERVAL = 50
# ========== 配置文件路径（仅新增） ==========
CONFIG_FILE = "key_mapping.json"
# ========== 主题独立配置【新增】 ==========
THEME_CONFIG_FILE = "theme_config.json"
DEFAULT_THEME = "Light"
CURR_THEME = DEFAULT_THEME
# 主题读写独立函数【新增，不干扰映射】
def load_theme_config():
    global CURR_THEME
    try:
        with open(THEME_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "app_theme" in data:
                CURR_THEME = data["app_theme"]
    except Exception:
        CURR_THEME = DEFAULT_THEME

def save_theme_config():
    data = {"app_theme": CURR_THEME}
    with open(THEME_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
def async_save_theme_config():
    def worker():
        save_theme_config()
    threading.Thread(target=worker, daemon=True).start()
    


# ========== 全局类缓存（100%完全保留） ==========
ANDROID_CLASS_CACHE = {
    "PythonActivity": None,
    "AccessibilityKeyMonitorService": None,
    "Intent": None,
    "Context": None
}
def _safe_autoclass(class_name):
    try:
        cls = autoclass(class_name)
        logger.log("INFO", f"成功加载Java类:{class_name}")
        return cls
    except Exception as e:
        logger.log("ERROR", f"加载{class_name}未知异常，异常详情:{e}")
        return None

def init_pa_android_classes():
    global ANDROID_CLASS_CACHE
    if not ANDROID_CLASS_CACHE["PythonActivity"]:
        logger.log("INFO", "开始加载PythonActivityAndroid类")
        ANDROID_CLASS_CACHE["PythonActivity"] = _safe_autoclass('org.kivy.android.PythonActivity')
        logger.log("INFO", "PythonActivityAndroid类加载完成")
init_pa_android_classes()

def init_accessibility_android_classes():
    global ANDROID_CLASS_CACHE
    if not ANDROID_CLASS_CACHE["AccessibilityKeyMonitorService"]:
        logger.log("INFO", "开始加载所有无障碍Android类")
        ANDROID_CLASS_CACHE["AccessibilityKeyMonitorService"] = _safe_autoclass('io.github.qinmingming16.magilm.accessibility.AccessibilityKeyMonitorService')
        logger.log("INFO", "所有无障碍Android类加载完成")
init_accessibility_android_classes()

def init_base_android_classes():
    global ANDROID_CLASS_CACHE
    if not (ANDROID_CLASS_CACHE["Intent"] or ANDROID_CLASS_CACHE["Context"]):
        logger.log("INFO", "开始加载所有基础Android类")
        if not ANDROID_CLASS_CACHE["Intent"]:
            ANDROID_CLASS_CACHE["Intent"] = _safe_autoclass('android.content.Intent')
        if not ANDROID_CLASS_CACHE["Context"]:
            ANDROID_CLASS_CACHE["Context"] = _safe_autoclass('android.content.Context')
        logger.log("INFO", "所有基础Android类加载完成")
init_base_android_classes()


class FloatWindowBridge:
    @staticmethod
    @run_on_ui_thread
    def init():
        try:
            Context = ANDROID_CLASS_CACHE["Context"]
            PythonActivity = ANDROID_CLASS_CACHE["PythonActivity"]
            AppFloatWindow = autoclass("org.kivy.android.AppFloatWindow")
            
            AppFloatWindow.init(PythonActivity.mActivity.getApplicationContext())
            logger.log("INFO", "悬浮窗Java类初始化成功")
        except Exception as e:
            logger.log("ERROR", f"悬浮窗初始化失败:{e}")
    @staticmethod
    def can_overlay():
        try:
            PythonActivity = ANDROID_CLASS_CACHE["PythonActivity"]
            AppFloatWindow = autoclass("org.kivy.android.AppFloatWindow")
            return AppFloatWindow.canDrawOverlays(PythonActivity.mActivity.getApplicationContext())
        except:
            return False
    @staticmethod
    @run_on_ui_thread
    def show():
        try:
            AppFloatWindow = autoclass("org.kivy.android.AppFloatWindow")
            AppFloatWindow.show()
            logger.log("INFO", "悬浮窗已显示")
        except Exception as e:
            logger.log("ERROR", f"显示悬浮窗失败:{e}")
    @staticmethod
    @run_on_ui_thread
    def hide():
        try:
            AppFloatWindow = autoclass("org.kivy.android.AppFloatWindow")
            AppFloatWindow.hide()
            logger.log("INFO", "悬浮窗已隐藏")
        except:
            pass

# ========== 文件选择工具类【新增，不改动原有代码】 ==========
class FilePickerHelper:
    @staticmethod
    @run_on_ui_thread
    def open_sheet_picker():
        try:
            PythonActivity = ANDROID_CLASS_CACHE["PythonActivity"]
            Intent = ANDROID_CLASS_CACHE["Intent"]
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
            PythonActivity.mActivity.startActivityForResult(intent, FILE_PICK_REQ_CODE)
            logger.log("INFO", "文件选择器已打开")
        except Exception as e:
            logger.log("ERROR", f"打开文件选择失败:{traceback.format_exc()}")

    @staticmethod
    def uri_to_path(uri):
        try:
            Context = ANDROID_CLASS_CACHE["PythonActivity"].mActivity.getApplicationContext()
            DocumentsContract = autoclass("android.provider.DocumentsContract")
            Environment = autoclass("android.os.Environment")
            uri_authority = uri.getAuthority()
            uri_scheme = uri.getScheme()
            if uri_scheme == "file":
                return uri.getPath()
            if DocumentsContract.isDocumentUri(Context, uri):
                if "com.android.externalstorage.documents" == uri_authority:
                    doc_id = DocumentsContract.getDocumentId(uri)
                    split = doc_id.split(":")
                    storage_type, storage_id = split[0], split[1]
                    if "primary" == storage_type:
                        return f"{Environment.getExternalStorageDirectory()}/{storage_id}"
                    else:
                        return f"/storage/{storage_id}"
                elif "com.android.providers.downloads.documents":
                    doc_id = DocumentsContract.getDocumentId(uri)
                    tree_uri = autoclass("android.net.Uri").parse("content://downloads/tree")
                    uri_dl = DocumentsContract.buildDocumentUriUsingTree(tree_uri, doc_id)
                    return FilePickerHelper.get_cursor_path(Context, uri_dl, None, None, None)
                elif "com.android.providers.media.documents" == uri_authority:
                    doc_id = DocumentsContract.getDocumentId(uri)
                    split = doc_id.split(":")
                    media_type, media_id = split[0], split[1]
                    media_uri_map = {
                        "image": "content://media/external/images/media",
                        "video": "content://media/external/videos/media",
                        "audio": "content://media/external/audio/media"
                    }
                    if media_type in media_uri_map:
                        media_uri = autoclass("android.net.Uri").parse(media_uri_map[media_type])
                        media_uri = media_uri.buildUpon().appendPath(media_id).build()
                        return FilePickerHelper.get_cursor_path(Context, media_uri, None, None, None)
            elif uri_scheme == "content":
                return FilePickerHelper.get_cursor_path(Context, uri, None, None, None)
        except Exception as e:
            logger.log("ERROR", f"URI解析失败:{e}")
        return None

    @staticmethod
    def get_cursor_path(context, uri, sel, sel_args, sort):
        cursor = None
        try:
            ContentResolver = context.getContentResolver()
            # 补齐5个参数，解决jnius参数不匹配崩溃
            cursor = ContentResolver.query(uri, None, sel, sel_args, sort)
            if cursor and cursor.moveToFirst():
                idx = cursor.getColumnIndexOrThrow("_data")
                return cursor.getString(idx)
        finally:
            if cursor:
                cursor.close()
        return None
        
    @staticmethod
    def read_saf_uri(android_uri, is_binary: bool):
        input_stream = None
        br = None
        isr = None
        try:
            Context = ANDROID_CLASS_CACHE["PythonActivity"].mActivity.getApplicationContext()
            resolver = Context.getContentResolver()
            input_stream = resolver.openInputStream(android_uri)
            if input_stream is None:
                logger.log("ERROR", "ContentResolver无法打开URI输入流")
                return None
        
            # ========== 二进制模式（MIDI）==========
            if is_binary:
                ByteArrayOutputStream = autoclass("java.io.ByteArrayOutputStream")
                bos = ByteArrayOutputStream()
                buf = bytearray(4096)
                while True:
                    size = input_stream.read(buf)
                    if size == -1:
                        break
                    bos.write(buf, 0, size)
                java_byte_arr = bos.toByteArray()
                raw_bytes = bytes(java_byte_arr)
                return base64.b64encode(raw_bytes).decode("utf-8")

            # ====== 下面全部是你原来txt读取代码，一字不动 ======
            InputStreamReader = autoclass("java.io.InputStreamReader")
            BufferedReader = autoclass("java.io.BufferedReader")
            # 优先UTF-8，编码失败自动切换GBK
            try:
                isr = InputStreamReader(input_stream, "UTF-8")
            except JavaException:
                isr = InputStreamReader(input_stream, "GBK")
            br = BufferedReader(isr)
            line_buffer = []
            line = br.readLine()
            while line is not None:
                line_buffer.append(line)
                line = br.readLine()
            full_text = "\n".join(line_buffer)
            return full_text
        except JavaException as je:
            logger.log("ERROR", f"SAFJava读取异常:{je}")
            return None
        except Exception as e:
            logger.log("ERROR", f"SAF通用读取异常:{e}")
            return None
        finally:
            # 强制关闭全部流，避免文件占用
            try:
                if br:
                    br.close()
            except Exception:
                pass
            try:
                if isr:
                    isr.close()
            except Exception:
                pass
            try:
                if input_stream:
                    input_stream.close()
            except Exception:
                pass



# ========== 核心App类（仅追加主题相关，原有代码完全不动） ==========
class MainApplication(MDApp):
    _initialized = False
    audio_sample_rate = 44100
    a_wav_pcm_data = None
    is_mapping_service_running = False
    _is_accessibility_service_bound = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = CURR_THEME
        self.theme_cls.primary_palette = "Green"
        
        self.curr_sheet_type = None
        self.curr_sheet_speed = None
    
    # 新增：根据主题获取文字颜色
    def get_text_color(self):
        return (1, 1, 1, 1) if CURR_THEME == "Dark" else (0, 0, 0, 1)
    
    # 新增：切换主题方法
    def _switch_app_theme(self, instance):
        global CURR_THEME
        CURR_THEME = "Light" if CURR_THEME == "Dark" else "Dark"
        self.theme_cls.theme_style = CURR_THEME
        # 修改底部导航颜色
        self.bottom_nav.md_bg_color = "#1e1e1e" if CURR_THEME == "Dark" else "#f5f5f5"
        # 更新设置页文字和按钮
        self.theme_status_label.text = f"当前主题：{CURR_THEME} 模式"
        self.theme_switch_btn.text = "切换到浅色模式" if CURR_THEME == "Dark" else "切换到深色模式"
        self.refresh_all_text_colors()
        async_save_theme_config()
    
    # 新增：全局刷新文字颜色
    def refresh_all_text_colors(self):
        color = self.get_text_color()
        self.mapping_service_hint_label.color = color
        self.map_title1.color = color
        self.map_title2.color = color
        self.playing_map_title1.color = color
        self.playing_map_title2.color = color
        self.log_label.color = (0.2,0.2,0.2,1) if CURR_THEME=="Light" else (0.8,0.8,0.8,1)
        self.theme_status_label.color = color
        self.playing_speed_dialog_title.color = color
    
    def build(self):
        @mainthread
        def _handle_act_result(req_code, result_code, intent):
            try:
                RESULT_OK = -1
                # 第一层：非本次文件选择，直接返回
                if req_code != FILE_PICK_REQ_CODE:
                    return
                # 第二层：用户取消/返回，result_code != RESULT_OK，直接拦截
                if result_code != RESULT_OK:
                    logger.log("INFO", "用户取消文件选择，返回操作")
                    self.show_toast("未选择文件", duration=1.5)
                    return
                # 第三层：intent对象判空
                if intent is None:
                    logger.log("WARN", "文件回调Intent为空")
                    self.show_toast("未选择文件", duration=1.5)
                    return
                # 第四层：关键修复，getData后校验Uri非空
                uri = intent.getData()
                if uri is None:
                    logger.log("WARN", "Intent存在但URI为空")
                    self.show_toast("未获取到有效文件", duration=1.5)
                    return
                real_path = FilePickerHelper.uri_to_path(uri)
                
                if real_path and real_path.lower().endswith((".txt", ".mid")):
                    global SHEET_FILE_LIST, SHEET_META_TMP
                    sheet_type = self.curr_sheet_type
                    cfg = SHEET_CONFIG[sheet_type]
                    file_suffix = os.path.splitext(real_path.lower())[1]
                    
                    # 校验文件后缀与类型匹配
                    if file_suffix not in cfg["suffix"]:
                        suffix_tip = "/".join(cfg["suffix"])
                        self.show_toast(f"{sheet_type}类琴谱仅支持{suffix_tip}文件", duration=1.5)
                        return
                
                    sheet_item = {
                        "path": real_path,
                        "content": ""
                    }

                    # txt、mid统一通过SAF读取内容
                    if uri is not None:
                        
                        ext = os.path.splitext(real_path)[1].lower()
                        # 和旧逻辑判断方式完全一致
                        if ext == ".mid":
                            binary_mode = True
                        else:
                            binary_mode = False
                        
                        file_content = FilePickerHelper.read_saf_uri(uri, binary_mode)
                        if file_content is not None:
                            sheet_item["content"] = file_content
                            logger.log("INFO", f"SAF读取文件成功，存储内容长度:{len(file_content)}")
                        else:
                            logger.log("WARN", f"SAF读取文件失败，文件:{os.path.basename(real_path)}")
                            self.show_toast("文件内容读取失败，仅保存文件路径", duration=1.5)
                    else:
                        logger.log("WARN", "回调URI对象为空，无法读取文件")
                        self.show_toast("文件内容读取失败，仅保存文件路径", duration=1.5)


                    # 去重判断逻辑不变
                    exist_flag = False
                    for item in SHEET_FILE_LIST:
                        if item["path"] == real_path:
                            exist_flag = True
                            break
                    if not exist_flag:
                        SHEET_FILE_LIST.append(sheet_item)
                        SHEET_META_TMP[real_path] = {
                            "type": self.curr_sheet_type,
                            "speed": self.curr_sheet_speed
                        }
                        self.refresh_sheet_file_list()
                        logger.log("INFO", f"添加琴谱列表：{os.path.basename(real_path)}")
                        self.show_toast(f"添加成功:{os.path.basename(real_path)}", duration=1.5)
                    else:
                        self.show_toast("该琴谱已存在于列表", duration=1.5)
                else:
                    self.show_toast("仅支持.txt/.mid文件", duration=1.5)
            except Exception as e:
                logger.log("ERROR", f"文件选择回调异常:{e}")
        activity.bind(on_activity_result=_handle_act_result)
        
        logger.log("INFO", "开始构建UI布局")
        
        if self._initialized:
            logger.log("WARN", "二次启动，跳过重复初始化")
            return self.screen
        
        def _safe_dp(value):
            dp_value = min(dp(value), 2000)
            return dp_value
            
        
        self.home_layout = MDBoxLayout(
            orientation='vertical',
            padding=[_safe_dp(20), _safe_dp(40), _safe_dp(20), _safe_dp(25)],
            spacing=_safe_dp(15),
            size_hint=(1, 1),
        )
        
        self.home_title = MDLabel(
            text="主标题",
            font_name='Roboto',
            font_size=_safe_dp(18),
            halign='center',
            valign='middle',
            size_hint=(1, None),
            height=_safe_dp(60),
            text_size=(_safe_dp(300), _safe_dp(60)),
            color=self.get_text_color()
        )
        self.home_layout.add_widget(self.home_title)
        
        
        self.playing_layout = MDBoxLayout(
            orientation='vertical',
            padding=[_safe_dp(20), _safe_dp(40), _safe_dp(20), _safe_dp(25)],
            spacing=_safe_dp(15),
            size_hint=(1, 1),
        )
        
        # 按钮布局
        self.playing_button_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=_safe_dp(15),
            size_hint=(1, None),
            height=_safe_dp(45)
        )
        
        self.playing_prepare_btn = MDRaisedButton(
            text="准备演奏",
            font_name='Roboto',
            font_size=_safe_dp(18),
            md_bg_color=(0, 0.8, 0, 1),
            text_color=(1, 1, 1, 1),
            size_hint=(1, 1)
        )
        self.playing_prepare_btn.bind(on_press=self._prepare_playing_service)
        self.playing_button_layout.add_widget(self.playing_prepare_btn)
        
        self.playing_stop_btn = MDRaisedButton(
            text="停止演奏",
            font_name='Roboto',
            font_size=_safe_dp(18),
            md_bg_color=(0.8, 0, 0, 1),
            text_color=(1, 1, 1, 1),
            size_hint=(1, 1),
            disabled=True
        )
        
        self.playing_button_layout.add_widget(self.playing_stop_btn)
        
        
        self.playing_open_accessibility_btn = MDRaisedButton(
            text="去开启",
            font_name='Roboto',
            font_size=_safe_dp(18),
            md_bg_color=(0.0, 0.6, 0.8, 1),
            text_color=(1, 1, 1, 1),
            size_hint=(1, 1)
        )
        self.playing_open_accessibility_btn.bind(on_press=self._open_accessibility_settings)
        self.playing_button_layout.add_widget(self.playing_open_accessibility_btn)
        self.playing_layout.add_widget(self.playing_button_layout)
        
        self.playing_service_hint_label = MDLabel(
            text="请先开启无障碍服务",
            font_name='Roboto',
            font_size=_safe_dp(18),
            halign='center',
            valign='middle',
            size_hint=(1, None),
            height=_safe_dp(60),
            text_size=(_safe_dp(300), _safe_dp(60)),
            color=self.get_text_color()
        )
        self.playing_layout.add_widget(self.playing_service_hint_label)
        
        btn_playing_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=_safe_dp(10),
            size_hint=(1, None),
            height=_safe_dp(40)
        )
        
        self.btn_playing_add = MDRaisedButton(text="添加琴谱", font_size=_safe_dp(12))
        self.btn_playing_clear = MDRaisedButton(text="清空列表", font_size=_safe_dp(12))
        self.btn_playing_clear.bind(on_press=self._clear_all_sheet)
        
        btn_playing_layout.add_widget(self.btn_playing_add)
        btn_playing_layout.add_widget(self.btn_playing_clear)
        self.playing_layout.add_widget(btn_playing_layout)
        
        
        self.playing_speed_dialog_layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[dp(10), dp(10), dp(10), dp(10)],
            size_hint_y=None,
            height=dp(100)
        )
        
        self.playing_speed_dialog_title = MDLabel(
            text="设置演奏速度",
            font_size=dp(16),
            halign="left",
            size_hint_y=None,
            height=dp(30)
        )
        
        self.playing_input_speed = MDTextField(hint_text="请输入演奏速度", input_filter="float")
        
        self.playing_speed_dialog_layout.add_widget(self.playing_speed_dialog_title)
        self.playing_speed_dialog_layout.add_widget(self.playing_input_speed)
        
        self.playing_speed_dialog = MDDialog(
            text="设置演奏速度",
            type="custom",
            content_cls=self.playing_speed_dialog_layout,
            buttons=[
                MDRaisedButton(text="取消", on_press=lambda x: self._close_playing_speed_dialog()),
                MDRaisedButton(text="确认", on_press=lambda x: self._confirm_playing_input_speed())
            ]
        )
        
        menu_items = [
            {
                "text": "建筑谱(.txt)",
                "on_press": lambda *args, t="jianzhu": self._select_playing_sheet_type(t)
            },
            {
                "text": "指尖谱(.txt)",
                "on_press": lambda *args, t="zhijian": self._select_playing_sheet_type(t)
            },
            {
                "text": "呱呱谱(.txt)",
                "on_press": lambda *args, t="guagua": self._select_playing_sheet_type(t)
            },
            {
                "text": "MIDI谱(.mid)",
                "on_press": lambda *args, t="midi": self._select_playing_sheet_type(t)
            },
        ]
        self.playing_sheet_type_dropdown = MDDropdownMenu(
            caller=self.btn_playing_add,
            items=menu_items,
            width_mult=4,
        )
        self.btn_playing_add.bind(on_press=self._show_playing_sheet_dropdown)
        
        
        self.playing_scroll_card = MDCard(
            size_hint=(1, None),
            height=_safe_dp(80),
            line_width=1,
            radius=dp(4),
            padding=dp(6),
            line_color=(0.0, 0.6, 0.8, 1)
        )
        
        scroll = ScrollView(size_hint=(1, 1))
        self.playing_list = MDBoxLayout(orientation='vertical', size_hint_y=None, spacing=_safe_dp(2))
        self.playing_list.bind(minimum_height=self.playing_list.setter('height'))
        scroll.add_widget(self.playing_list)
        self.playing_scroll_card.add_widget(scroll)
        self.playing_layout.add_widget(self.playing_scroll_card)
        
        self.playing_map_title1 = MDLabel(
            text="自定义按键映射",
            font_name='Roboto',
            font_size=_safe_dp(16),
            halign='center',
            size_hint=(1, None),
            height=_safe_dp(30),
            color=self.get_text_color()
        )
        self.playing_layout.add_widget(self.playing_map_title1)
        
        input_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=_safe_dp(5),
            size_hint=(1, None),
            height=_safe_dp(30)
        )
        self.playing_input_map_key = MDTextField(hint_text="按键", font_size=_safe_dp(12))
        self.playing_input_map_x = MDTextField(hint_text="X坐标", font_size=_safe_dp(12), input_filter="int")
        self.playing_input_map_y = MDTextField(hint_text="Y坐标", font_size=_safe_dp(12), input_filter="int")
        input_layout.add_widget(self.playing_input_map_key)
        input_layout.add_widget(self.playing_input_map_x)
        input_layout.add_widget(self.playing_input_map_y)
        self.playing_layout.add_widget(input_layout)
        btn_map_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=_safe_dp(10),
            size_hint=(1, None),
            height=_safe_dp(25)
        )
        self.playing_btn_add = MDRaisedButton(text="添加映射", font_size=_safe_dp(12))
        self.playing_btn_save = MDRaisedButton(text="保存配置", font_size=_safe_dp(12))
        
        self.playing_btn_add.bind(on_press=self._playing_add_mapping)
        self.playing_btn_save.bind(on_press=self._playing_save_mapping)
        
        btn_map_layout.add_widget(self.playing_btn_add)
        btn_map_layout.add_widget(self.playing_btn_save)
        self.playing_layout.add_widget(btn_map_layout)
        self.playing_map_title2 = MDLabel(
            text="映射列表",
            font_size=_safe_dp(14),
            size_hint=(1, None),
            height=_safe_dp(20),
            color=self.get_text_color()
        )
        self.playing_layout.add_widget(self.playing_map_title2)
        
        self.playing_mapping_scroll_card = MDCard(
            size_hint=(1, 1),
            line_width=1,
            radius=dp(4),
            padding=dp(6),
            line_color=(0.0, 0.6, 0.8, 1)
        )
        
        scroll = ScrollView(size_hint=(1, 1))
        self.playing_map_list = MDBoxLayout(orientation='vertical', size_hint_y=None, spacing=_safe_dp(2))
        self.playing_map_list.bind(minimum_height=self.playing_map_list.setter('height'))
        scroll.add_widget(self.playing_map_list)
        self.playing_mapping_scroll_card.add_widget(scroll)
        self.playing_layout.add_widget(self.playing_mapping_scroll_card)
        
        
        
        self.mapping_layout = MDBoxLayout(
            orientation='vertical',
            padding=[_safe_dp(20), _safe_dp(40), _safe_dp(20), _safe_dp(25)],
            spacing=_safe_dp(15),
            size_hint=(1, 1)
        )
        
        # 按钮布局
        self.mapping_button_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=_safe_dp(15),
            size_hint=(1, None),
            height=_safe_dp(45)
        )
        
        self.mapping_start_btn = MDRaisedButton(
            text="启动映射",
            font_name='Roboto',
            font_size=_safe_dp(18),
            md_bg_color=(0, 0.8, 0, 1),
            text_color=(1, 1, 1, 1),
            size_hint=(1, 1)
        )
        self.mapping_start_btn.bind(on_press=self._start_mapping_service)
        self.mapping_button_layout.add_widget(self.mapping_start_btn)
        
        self.mapping_stop_btn = MDRaisedButton(
            text="停止映射",
            font_name='Roboto',
            font_size=_safe_dp(18),
            md_bg_color=(0.8, 0, 0, 1),
            text_color=(1, 1, 1, 1),
            size_hint=(1, 1),
            disabled=True
        )
        self.mapping_stop_btn.bind(on_press=self._stop_mapping_service)
        self.mapping_button_layout.add_widget(self.mapping_stop_btn)
        
        
        self.open_accessibility_btn = MDRaisedButton(
            text="去开启",
            font_name='Roboto',
            font_size=_safe_dp(18),
            md_bg_color=(0.0, 0.6, 0.8, 1),
            text_color=(1, 1, 1, 1),
            size_hint=(1, 1)
        )
        self.open_accessibility_btn.bind(on_press=self._open_accessibility_settings)
        self.mapping_button_layout.add_widget(self.open_accessibility_btn)
        self.mapping_layout.add_widget(self.mapping_button_layout)
        
        self.mapping_service_hint_label = MDLabel(
            text="请先开启无障碍服务",
            font_name='Roboto',
            font_size=_safe_dp(18),
            halign='center',
            valign='middle',
            size_hint=(1, None),
            height=_safe_dp(60),
            text_size=(_safe_dp(300), _safe_dp(60)),
            color=self.get_text_color()
        )
        self.mapping_layout.add_widget(self.mapping_service_hint_label)
        
        self.map_title1 = MDLabel(
            text="自定义键盘映射",
            font_name='Roboto',
            font_size=_safe_dp(16),
            halign='center',
            size_hint=(1, None),
            height=_safe_dp(30),
            color=self.get_text_color()
        )
        self.mapping_layout.add_widget(self.map_title1)
        input_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=_safe_dp(5),
            size_hint=(1, None),
            height=_safe_dp(30)
        )
        self.input_map_key = MDTextField(hint_text="按键", font_size=_safe_dp(12))
        self.input_map_x = MDTextField(hint_text="X坐标", font_size=_safe_dp(12), input_filter="int")
        self.input_map_y = MDTextField(hint_text="Y坐标", font_size=_safe_dp(12), input_filter="int")
        input_layout.add_widget(self.input_map_key)
        input_layout.add_widget(self.input_map_x)
        input_layout.add_widget(self.input_map_y)
        self.mapping_layout.add_widget(input_layout)
        btn_map_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=_safe_dp(10),
            size_hint=(1, None),
            height=_safe_dp(25)
        )
        self.btn_add = MDRaisedButton(text="添加映射", font_size=_safe_dp(12))
        self.btn_save = MDRaisedButton(text="保存配置", font_size=_safe_dp(12))
        
        self.btn_add.bind(on_press=self._add_mapping)
        self.btn_save.bind(on_press=self._save_mapping)
        
        btn_map_layout.add_widget(self.btn_add)
        btn_map_layout.add_widget(self.btn_save)
        self.mapping_layout.add_widget(btn_map_layout)
        self.map_title2 = MDLabel(
            text="映射列表",
            font_size=_safe_dp(14),
            size_hint=(1, None),
            height=_safe_dp(20),
            color=self.get_text_color()
        )
        self.mapping_layout.add_widget(self.map_title2)
        
        self.mapping_scroll_card = MDCard(
            size_hint=(1, 1),
            line_width=1,
            radius=dp(4),
            padding=dp(6),
            line_color=(0.0, 0.6, 0.8, 1)
        )
        
        scroll = ScrollView(size_hint=(1, 1))
        self.map_list = MDBoxLayout(orientation='vertical', size_hint_y=None, spacing=_safe_dp(2))
        self.map_list.bind(minimum_height=self.map_list.setter('height'))
        scroll.add_widget(self.map_list)
        self.mapping_scroll_card.add_widget(scroll)
        self.mapping_layout.add_widget(self.mapping_scroll_card)
        
        
        # =========设置页新增主题切换UI【新增】=========
        self.setting_layout = MDBoxLayout(
            orientation='vertical',
            padding=[_safe_dp(20), _safe_dp(40), _safe_dp(20), _safe_dp(25)],
            spacing=_safe_dp(15),
            size_hint=(1, 1)
        )
        
        # 日志标签（完全保留原有位置）
        self.log_label = MDLabel(
            text="日志：\n" + logger.get_all_logs(),
            font_name='Roboto',
            font_size=_safe_dp(12),
            halign='left',
            valign='top',
            size_hint=(1, None),
            height=_safe_dp(30),
            text_size=(None, _safe_dp(80)),
            color=(0.8, 0.8, 0.8, 1)
        )
        self.setting_layout.add_widget(self.log_label)
        
        # 当前主题状态
        self.theme_status_label = MDLabel(
            text=f"当前主题：{CURR_THEME} 模式",
            font_size=dp(16),
            size_hint_y=None,
            height=dp(30),
            color=self.get_text_color()
        )
        # 主题切换按钮
        self.theme_switch_btn = MDRaisedButton(
            text="切换到浅色模式" if CURR_THEME == "Dark" else "切换到深色模式",
            size_hint=(1, None),
            height=dp(50),
            on_press=self._switch_app_theme
        )
        
        self.setting_layout.add_widget(self.theme_status_label)
        self.setting_layout.add_widget(self.theme_switch_btn)
        
        
        
        # 底部导航（100%完全保留，仅修改背景自适应）
        self.screen = MDScreen()
        nav_bg_color = "#1e1e1e" if CURR_THEME == "Dark" else "#f5f5f5"
        self.bottom_nav = MDBottomNavigation(md_bg_color=nav_bg_color)
        item1 = MDBottomNavigationItem(name="tab1", text="主页", icon="home-outline")
        item1.add_widget(self.home_layout)
        item2 = MDBottomNavigationItem(name="tab2", text="自动演奏", icon="play-outline")
        item2.add_widget(self.playing_layout)
        item3 = MDBottomNavigationItem(name="tab3", text="键盘映射", icon="keyboard-outline")
        item3.add_widget(self.mapping_layout)
        item4 = MDBottomNavigationItem(name="tab4", text="琴谱编辑", icon="note-edit-outline")
        item5 = MDBottomNavigationItem(name="tab5", text="模拟原琴", icon="piano")
        item6 = MDBottomNavigationItem(name="tab6", text="设置", icon="cog-outline")
        item6.add_widget(self.setting_layout)
        
        self.bottom_nav.add_widget(item1)
        self.bottom_nav.add_widget(item2)
        self.bottom_nav.add_widget(item3)
        self.bottom_nav.add_widget(item4)
        self.bottom_nav.add_widget(item5)
        self.bottom_nav.add_widget(item6)
        self.screen.add_widget(self.bottom_nav)
        
        # ====================== UI结束 ======================
        
        # 原有UI适配逻辑（100%未改）
        def _update_label_size(*args):
            try:
                mapping_width = self.mapping_layout.width if self.mapping_layout.width > 0 else dp(300)
                setting_width = self.setting_layout.width if self.setting_layout.width > 0 else dp(300)
                
                self.mapping_service_hint_label.text_size = (mapping_width - dp(20), None)
                self.log_label.text_size = (setting_width - dp(20), None)
            except Exception as e:
                logger.log("ERROR", f"更新标签尺寸异常，异常详情:{e}")
        self.mapping_layout.bind(width=_update_label_size)
        @mainthread
        def _update_log():
            try:
                self.log_label.text = "日志：\n" + logger.get_all_logs()
            except Exception as e:
                logger.log("ERROR", f"更新日志异常，异常详情:{e}")
        Clock.schedule_interval(lambda dt: _update_log(), 5.0)
        # 原有初始化逻辑（100%未改）
        def _init_audio(*args):
            logger.log("INFO", "开始预加载A.wav")
            wav_path = "/app/audio/A.wav"
            if not os.path.exists(wav_path):
                wav_path = "audio/A.wav"
            try:
                if os.path.exists(wav_path):
                    with open(wav_path, "rb") as f:
                        wav_data = f.read()
                    if len(wav_data) >= 44:
                        pcm_bytes = wav_data[44:]
                        if len(pcm_bytes) % 2 != 0:
                            pcm_bytes = pcm_bytes[:-1]
                        self.a_wav_pcm_data = array.array('h')
                        self.a_wav_pcm_data.frombytes(pcm_bytes)
                        logger.log("INFO", f"A.wav加载成功，PCM帧数：{len(self.a_wav_pcm_data)}")
                else:
                    logger.log("ERROR", f"A.wav文件不存在，路径: {wav_path}")
            except Exception as e:
                logger.log("ERROR", f"加载失败，异常详情: {e}\n{traceback.format_exc()[:200]}")
        def _init_accessibility(*args):
            logger.log("INFO", "开始无障碍服务初始化")
            PythonActivity = ANDROID_CLASS_CACHE["PythonActivity"]
            accessibilityService = ANDROID_CLASS_CACHE["AccessibilityKeyMonitorService"]
            if not PythonActivity or PythonActivity.mActivity is None:
                self.mapping_service_hint_label.text = "无法获取Android Activity（JNI失败），映射无法使用"
                logger.log("FATAL", "PythonActivity为空，应用上下文失效")
                return
            try:
                if not accessibilityService:
                    self.mapping_service_hint_label.text = "无障碍服务类未加载，映射无法使用"
                    logger.log("FATAL", "AccessibilityKeyMonitorService未加载")
                    return
                self._is_accessibility_service_bound = True
                logger.log("INFO", "无障碍服务初始化成功")
                if not accessibilityService.isServiceRunning():
                    logger.log("WARN", "无障碍服务未运行")
                else:
                    self.mapping_service_hint_label.text = "无障碍服务已就绪，点击【启动映射】启动映射"
                    logger.log("INFO", "无障碍服务服务已运行，就绪")
            except Exception as e:
                self.mapping_service_hint_label.text = f"服务初始化失败:{str(e)[:80]}"
                logger.log("ERROR", f"初始化异常:{e}\n{traceback.format_exc()[:200]}")
        
        Clock.schedule_once(_init_accessibility, 1.0)
        Clock.schedule_once(_init_audio, 1.5)
        
        # 初始化映射列表 + 加载配置
        Clock.schedule_once(lambda dt: (self.load_mapping(), self.refresh_mapping_list(), self.refresh_playing_mapping_list(), self.refresh_sheet_file_list()), 0.5)
        
        Clock.schedule_once(lambda dt: FloatWindowBridge.init(), 2.0)
        Clock.schedule_once(lambda x:self.refresh_all_text_colors(),0.1)
        
        self._initialized = True
        logger.log("INFO", "初始化完成，UI布局创建成功")
        
        return self.screen
        
    
    
    # ====================== 按钮逻辑 + 加载保存（全部原样） ======================
    
    def _playing_add_mapping(self, instance):
        target_key = self.playing_input_map_key.text.strip().upper()
        x_text = self.playing_input_map_x.text.strip()
        y_text = self.playing_input_map_y.text.strip()
        if not target_key or not x_text or not y_text:
            logger.log("WARN", "添加失败:请填写完整按键、X、Y")
            self.show_toast("添加失败:请填写完整按键、X、Y", duration=1.5)
            return
        try:
            tap_x = int(x_text)
            tap_y = int(y_text)
        except:
            logger.log("WARN", "添加失败:坐标必须是数字")
            self.show_toast("添加失败:坐标必须是数字", duration=1.5)
            return
        KEY_NAME_TO_GESTURE_COORD_MAP[target_key] = (tap_x, tap_y)
        self.refresh_mapping_list()
        self.refresh_playing_mapping_list()
        self.playing_input_map_key.text = ""
        self.playing_input_map_x.text = ""
        self.playing_input_map_y.text = ""
        logger.log("INFO", f"添加成功:{target_key} → ({tap_x}, {tap_y})")
        self.show_toast(f"添加成功:{target_key} → ({tap_x}, {tap_y})", duration=1.5)
        
    def _playing_save_mapping(self, instance):
        self.async_save_mapping_config()
        
    def refresh_playing_mapping_list(self, dt=None):
        self.playing_map_list.clear_widgets()
        color = self.get_text_color()
        for target_key, (tap_x, tap_y) in KEY_NAME_TO_GESTURE_COORD_MAP.items():
            item_layout = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(28),
                spacing=dp(5)
            )
            lbl = MDLabel(
                text=f"{target_key} → ({tap_x}, {tap_y})",
                font_size=dp(12),
                size_hint_y=1,
                color=color,
                valign="middle",
                halign="left"
            )
            delete_btn = MDIconButton(
                icon="delete",
                font_size=dp(12),
                size_hint_x=None,
                width=dp(40),
                size_hint_y=None,
                height=dp(28),
                padding=(0, 0, 0, 0),
                pos_hint={"center_y": 0.5},
                icon_size=dp(18),
                on_press=lambda _sender, key_to_delete=target_key: self._playing_delete_mapping(key_to_delete)
            )
            item_layout.add_widget(lbl)
            item_layout.add_widget(delete_btn)
            self.playing_map_list.add_widget(item_layout)
    def _playing_delete_mapping(self, target_key):
        if target_key in KEY_NAME_TO_GESTURE_COORD_MAP:
            del KEY_NAME_TO_GESTURE_COORD_MAP[target_key]
            self.refresh_mapping_list()
            self.refresh_playing_mapping_list()
            logger.log("INFO", f"已删除映射:{target_key}")
            self.show_toast(f"已删除映射:{target_key}", duration=1.5)
    
    
    # ========== 新增：下拉菜单、速度弹窗全套逻辑 ==========
    def _show_playing_sheet_dropdown(self, instance):
        """点击添加琴谱，弹出类型下拉菜单"""
        self.playing_sheet_type_dropdown.open()

    def _select_playing_sheet_type(self, sheet_type):
        """选中下拉菜单某一类琴谱"""
        # 关闭下拉菜单
        self.playing_sheet_type_dropdown.dismiss()
        # 重置临时变量
        self.curr_sheet_type = sheet_type
        self.curr_sheet_speed = None
        cfg = SHEET_CONFIG[sheet_type]
        
        sheet_type_name_map = {
            "jianzhu": "设置建筑谱演奏速度(音距，单位s)",
            "zhijian": "",
            "guagua": "设置呱呱谱演奏速度(按键速度，单位ms)",
            "midi": "设置MIDI谱演奏速度(BPM，单位beats/min)"
        }
        
        self.playing_speed_dialog_title.text = sheet_type_name_map[sheet_type]

        if not cfg["need_speed"]:
            # B类无需速度，直接打开文件选择
            FilePickerHelper.open_sheet_picker()
            return
    
        # A/C/D 需要弹窗输入速度
        self.playing_input_speed.text = ""
        # 根据类型切换输入过滤
        if cfg["is_int"]:
            self.playing_input_speed.input_filter = "int"
            self.playing_input_speed.hint_text = f"整数范围 {cfg['min']} ~ {cfg['max']}"
        else:
            self.playing_input_speed.input_filter = "float"
            self.playing_input_speed.hint_text = f"浮点范围 {cfg['min']} ~ {cfg['max']}"
        # 打开弹窗
        self.playing_speed_dialog.open()

    @mainthread
    def _close_playing_speed_dialog(self):
        """关闭速度弹窗，终止流程"""
        self.playing_speed_dialog.dismiss()
        self.curr_sheet_type = None
        self.curr_sheet_speed = None

    def _confirm_playing_input_speed(self):
        """确认速度输入，校验合法性后打开文件选择"""
        sheet_type = self.curr_sheet_type
        cfg = SHEET_CONFIG[sheet_type]
        input_text = self.playing_input_speed.text.strip()

        # 空值校验
        if not input_text:
            self.show_toast("请输入演奏速度", duration=1.5)
            return

        # 数值解析
        try:
            if cfg["is_int"]:
                speed_val = int(input_text)
            else:
                speed_val = float(input_text)
        except ValueError:
            self.show_toast("输入格式错误，请按要求输入速度", duration=1.5)
            return

        # 区间校验
        if not (cfg["min"] <= speed_val <= cfg["max"]):
            self.show_toast(f"速度超出范围:{cfg['min']} ~ {cfg['max']}", duration=1.5)
            return

        # 校验通过，保存临时速度，关闭弹窗打开文件选择
        self.curr_sheet_speed = speed_val
        self.playing_speed_dialog.dismiss()
        FilePickerHelper.open_sheet_picker()

    
    
    # ====================== 新增琴谱相关方法（无原有代码修改） ======================
    def _open_sheet_file_selector(self, instance):
        FilePickerHelper.open_sheet_picker()

    def refresh_sheet_file_list(self, dt=None):
        self.playing_list.clear_widgets()
        text_color = self.get_text_color()
        for sheet_item in SHEET_FILE_LIST:
            file_path = sheet_item["path"]
            file_name = os.path.basename(file_path)
            item_layout = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(50),
                spacing=dp(5)
            )
            meta = SHEET_META_TMP.get(file_path, {})
            sheet_type = meta.get("type", "")
            sheet_speed = meta.get("speed", None)
            sheet_type_display_name = {
                "jianzhu": "建筑谱",
                "zhijian": "指尖谱",
                "guagua": "呱呱谱",
                "midi": "MIDI谱"
            }
            if sheet_speed is not None:
                display_text = f"{file_name} [类型:{sheet_type_display_name.get(sheet_type, sheet_type)} 速度:{sheet_speed}]"
            else:
                display_text = f"{file_name} [类型:{sheet_type_display_name.get(sheet_type, sheet_type)}]"
            
            file_lbl = MDLabel(
                text=display_text,
                font_size=dp(12),
                size_hint_x=0.9,
                color=text_color,
                valign="middle",
                halign="left"
            )

            delete_btn = MDIconButton(
                icon="delete",
                font_size=dp(12),
                size_hint_x=None,
                width=dp(40),
                size_hint_y=None,
                height=dp(40),
                icon_size=dp(18),
                pos_hint={"center_y": 0.5},
                on_press=lambda x, path=file_path: self._delete_sheet_file(path)
            )
            item_layout.add_widget(file_lbl)
            item_layout.add_widget(delete_btn)
            self.playing_list.add_widget(item_layout)

    def _delete_sheet_file(self, file_path):
        global SHEET_FILE_LIST, SHEET_META_TMP
        del_idx = -1
        for i, item in enumerate(SHEET_FILE_LIST):
            if item["path"] == file_path:
                del_idx = i
                break
        if del_idx != -1:
            del SHEET_FILE_LIST[del_idx]
            # 新增：同步删除元数据缓存
            if file_path in SHEET_META_TMP:
                del SHEET_META_TMP[file_path]
            logger.log("INFO", f"已删除琴谱:{file_path}")
            self.show_toast(f"已删除琴谱:{os.path.basename(file_path)}", duration=1.5)
            self.refresh_sheet_file_list()

    def _clear_all_sheet(self, instance):
        global SHEET_FILE_LIST, SHEET_META_TMP
        if len(SHEET_FILE_LIST) == 0:
            self.show_toast("琴谱列表已为空", duration=1.5)
            return
        SHEET_FILE_LIST.clear()
        SHEET_META_TMP.clear()
        self.refresh_sheet_file_list()
        logger.log("INFO", "已清空所有琴谱文件")
        self.show_toast("已清空全部琴谱", duration=1.5)
        
    @mainthread
    def _prepare_playing_service(self, instance):
        logger.log("INFO", "用户点击启动按钮，准备开启演奏功能")
        if not FloatWindowBridge.can_overlay():
            logger.log("ERROR", "权限未就绪，请检查悬浮窗权限")
            PythonActivity = ANDROID_CLASS_CACHE["PythonActivity"]
            Intent = ANDROID_CLASS_CACHE["Intent"]
            Uri = autoclass("android.net.Uri")
            Settings = autoclass("android.provider.Settings")
            
            intent = Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                            Uri.parse(f"package:{PythonActivity.mActivity.getPackageName()}"))
            intent.setFlags(intent.FLAG_ACTIVITY_NEW_TASK)
            dialog = MDDialog(
                text='''需要悬浮窗(显示在其他应用上层)权限
                启动自动演奏需要开启悬浮窗(显示在其他应用上层)，是否前往设置？''',
                buttons=[
                    MDRaisedButton(text="取消", on_press=lambda x: dialog.dismiss()),
                    MDRaisedButton(text="前往设置", on_press=lambda x: [
                        dialog.dismiss(),
                        PythonActivity.mActivity.startActivity(intent) if (PythonActivity and PythonActivity.mActivity) else None
                    ])
                ]
            )
            dialog.open()
            return
        FloatWindowBridge.show()
    
    
    
    def _add_mapping(self, instance):
        target_key = self.input_map_key.text.strip().upper()
        x_text = self.input_map_x.text.strip()
        y_text = self.input_map_y.text.strip()
        if not target_key or not x_text or not y_text:
            logger.log("WARN", "添加失败:请填写完整按键、X、Y")
            self.show_toast("添加失败:请填写完整按键、X、Y", duration=1.5)
            return
        try:
            tap_x = int(x_text)
            tap_y = int(y_text)
        except:
            logger.log("WARN", "添加失败:坐标必须是数字")
            self.show_toast("添加失败:坐标必须是数字", duration=1.5)
            return
        KEY_NAME_TO_GESTURE_COORD_MAP[target_key] = (tap_x, tap_y)
        self.refresh_mapping_list()
        self.refresh_playing_mapping_list()
        self.input_map_key.text = ""
        self.input_map_x.text = ""
        self.input_map_y.text = ""
        logger.log("INFO", f"添加成功:{target_key} → ({tap_x}, {tap_y})")
        self.show_toast(f"添加成功:{target_key} → ({tap_x}, {tap_y})", duration=1.5)
        
    def _save_mapping_config(self):
        # 纯IO，无任何UI操作
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(KEY_NAME_TO_GESTURE_COORD_MAP, f, ensure_ascii=False, indent=2)
        logger.log("INFO", "配置保存成功，重启APP不会丢失")

    @mainthread
    def _on_save_mapping_config_success(self):
        self.show_toast("配置保存成功", duration=1.5)

    @mainthread
    def _on_save_mapping_config_fail(self, err_msg):
        logger.log("ERROR", f"配置保存失败:{err_msg}")
        self.show_toast("配置保存失败", duration=1.5)

    def async_save_mapping_config(self):
        def worker():
            try:
                self._save_mapping_config()
                # 子线程通过Clock切主线程执行UI
                Clock.schedule_once(lambda dt: self._on_save_mapping_config_success(), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self._on_save_mapping_config_fail(str(e)), 0)
        threading.Thread(target=worker, daemon=True).start()

    # 按钮回调
    def _save_mapping(self, instance):
        self.async_save_mapping_config()
            
    def load_mapping(self, dt=None):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                KEY_NAME_TO_GESTURE_COORD_MAP.clear()
                KEY_NAME_TO_GESTURE_COORD_MAP.update(loaded_config)
                logger.log("INFO", "本地配置加载成功")
            except Exception as e:
                logger.log("ERROR", f"配置加载失败:{e}")
        self.refresh_mapping_list()
        self.refresh_playing_mapping_list()
        
    def refresh_mapping_list(self, dt=None):
        self.map_list.clear_widgets()
        color = self.get_text_color()
        for target_key, (tap_x, tap_y) in KEY_NAME_TO_GESTURE_COORD_MAP.items():
            item_layout = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(28),
                spacing=dp(5)
            )
            lbl = MDLabel(
                text=f"{target_key} → ({tap_x}, {tap_y})",
                font_size=dp(12),
                size_hint_y=1,
                color=color,
                valign="middle",
                halign="left"
            )
            delete_btn = MDIconButton(
                icon="delete",
                font_size=dp(12),
                size_hint_x=None,
                width=dp(40),
                size_hint_y=None,
                height=dp(28),
                padding=(0, 0, 0, 0),
                pos_hint={"center_y": 0.5},
                icon_size=dp(18),
                on_press=lambda _sender, key_to_delete=target_key: self._delete_mapping(key_to_delete)
            )
            item_layout.add_widget(lbl)
            item_layout.add_widget(delete_btn)
            self.map_list.add_widget(item_layout)
    def _delete_mapping(self, target_key):
        if target_key in KEY_NAME_TO_GESTURE_COORD_MAP:
            del KEY_NAME_TO_GESTURE_COORD_MAP[target_key]
            self.refresh_mapping_list()
            self.refresh_playing_mapping_list()
            logger.log("INFO", f"已删除映射:{target_key}")
            self.show_toast(f"已删除映射:{target_key}", duration=1.5)
    def _open_accessibility_settings(self, instance=None):
        # 手动点击才跳转到无障碍设置
        try:
            PythonActivity = ANDROID_CLASS_CACHE["PythonActivity"]
            if PythonActivity and PythonActivity.mActivity:
                intent = ANDROID_CLASS_CACHE["Intent"]("android.settings.ACCESSIBILITY_SETTINGS")
                intent.setFlags(intent.FLAG_ACTIVITY_NEW_TASK)
                PythonActivity.mActivity.startActivity(intent)
                self.show_toast("请开启本应用的无障碍服务", duration=1.5)
        except Exception as e:
            logger.log("ERROR", f"跳转设置失败:{e}")
            self.show_toast("跳转失败，请手动去设置开启无障碍", duration=1.5)
    @mainthread
    def _start_mapping_service(self, instance):
        logger.log("INFO", "用户点击启动按钮，准备开启映射功能")
        accessibilityService = ANDROID_CLASS_CACHE["AccessibilityKeyMonitorService"]
        service_running = accessibilityService.isServiceRunning() if accessibilityService else False
        if not service_running:
            logger.log("ERROR", "服务未就绪，请检查无障碍服务")
            self.mapping_service_hint_label.text = "服务未就绪，请检查无障碍服务是否开启（可手动重启服务）"
            PythonActivity = ANDROID_CLASS_CACHE["PythonActivity"]
            intent = ANDROID_CLASS_CACHE["Intent"]("android.settings.ACCESSIBILITY_SETTINGS")
            intent.setFlags(intent.FLAG_ACTIVITY_NEW_TASK)
            dialog = MDDialog(
                text='''需要无障碍权限
                启动按键映射需要开启无障碍服务，是否前往设置？''',
                buttons=[
                    MDRaisedButton(text="取消", on_press=lambda x: dialog.dismiss()),
                    MDRaisedButton(text="前往设置", on_press=lambda x: [
                        dialog.dismiss(),
                        # 完全使用你原来的跳转代码
                        PythonActivity.mActivity.startActivity(intent) if (PythonActivity and PythonActivity.mActivity) else None
                    ])
                ]
            )
            dialog.open()
            return
        try:
            accessibilityService.stopMap()
            for key_name, (x, y) in KEY_NAME_TO_GESTURE_COORD_MAP.items():
                accessibilityService.setKeyMap(key_name, x, y)
            accessibilityService.startMap()
            logger.log("INFO", "所有按键坐标已同步至Java，映射已启动")
        except Exception as e:
            logger.log("ERROR", f"映射启动失败:{e}")
        self.is_mapping_service_running = True
        self.mapping_start_btn.disabled = True
        self.mapping_stop_btn.disabled = False
        self.mapping_service_hint_label.text = "映射已启动，点击【停止映射】关闭"
    
    @mainthread
    def _stop_mapping_service(self, instance):
        logger.log("INFO", "用户点击停止按钮，准备映射监测功能")
        self.is_mapping_service_running = False
        try:
            accessibilityService = ANDROID_CLASS_CACHE["AccessibilityKeyMonitorService"]
            if accessibilityService:
                accessibilityService.stopMap()
        except:
            pass
        self.mapping_start_btn.disabled = False
        self.mapping_stop_btn.disabled = True
        self.mapping_service_hint_label.text = "映射已停止，点击【启动映射】重新启动"
        logger.log("INFO", "映射功能已完全关闭，所有资源已清理")
        
    def show_toast(self, message: str, duration: float = 1.5):
        try:
            ToastTool = autoclass("org.kivy.android.ToastTool")
            ToastTool.show(message)
        except Exception as e:
            logger.log("INFO", f"Toast弹出错误:{e}")
        
    def _play_audio(self):
        logger.log("DEBUG", "开始播放A.wav,音频功能触发")
        if self.a_wav_pcm_data is None:
            logger.log("WARN", "A.wav数据为空，无法播放")
            return False
        try:
            AudioTrack = autoclass('android.media.AudioTrack')
            AudioFormat = autoclass('android.media.AudioFormat')
            AudioManager = autoclass('android.media.AudioManager')
            sample_rate = self.audio_sample_rate
            channel_config = AudioFormat.CHANNEL_OUT_STEREO
            audio_format = AudioFormat.ENCODING_PCM_16BIT
            stream_type = AudioManager.STREAM_MUSIC
            buffer_size = AudioTrack.getMinBufferSize(sample_rate, channel_config, audio_format)
            buffer_size = buffer_size if buffer_size > 0 else 4096
            track = AudioTrack(stream_type, sample_rate, channel_config, audio_format, buffer_size, AudioTrack.MODE_STREAM)
            if track.getState() != AudioTrack.STATE_INITIALIZED:
                logger.log("ERROR", "AudioTrack初始化失败")
                return False
            track.setStereoVolume(1.0, 1.0)
            track.play()
            audio_bytes = self.a_wav_pcm_data.tobytes()
            total_written = 0
            chunk_size = buffer_size
            while total_written < len(audio_bytes):
                end = min(total_written + chunk_size, len(audio_bytes))
                chunk = audio_bytes[total_written:end]
                written = track.write(chunk, 0, len(chunk))
                if written > 0:
                    total_written += written
                elif written < 0:
                    logger.log("ERROR", f"写入失败，返回值:{written}")
                    break
            track.stop()
            track.release()
            if total_written == len(audio_bytes):
                logger.log("INFO", f"播放成功，写入{total_written}字节")
                return True
            else:
                logger.log("WARN", f"写入不完整，预期{len(audio_bytes)}，实际{total_written}")
                return False
        except Exception as e:
            logger.log("ERROR", f"播放异常:{e}\n{traceback.format_exc()[:200]}")
            return False
    def on_stop(self):
        logger.log("INFO", "应用停止，开始清理资源")
        self._stop_mapping_service(None)
        self._initialized = False
        self.is_mapping_service_running = False
        gc.collect()
        logger.log("INFO", "资源已释放")
        return super().on_stop()
# ========== 应用入口 ==========
if __name__ == '__main__':
    try:
        load_theme_config()
        logger.log("FATAL", "应用开始启动")
        MainApplication().run()
    except Exception as e:
        err_msg = f"启动异常，异常详情:{e}\n{traceback.format_exc()[:300]}"
        logger.log("FATAL", err_msg)
        print(err_msg)

