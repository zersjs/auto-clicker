#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Optimizasyon için import işlemleri
import os
import sys
import time
import json
import pickle  # JSON yerine pickle kullanacağız
import random
import threading
import multiprocessing
from datetime import datetime
from functools import lru_cache, partial
from PIL import Image, ImageTk, ImageGrab, ImageChops
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import customtkinter as ctk
from pynput.mouse import Button, Controller as MouseController, Listener as MouseListener
from pynput.keyboard import Key, Controller as KeyboardController, Listener as KeyboardListener

# Performans optimizasyonu
ctk.deactivate_automatic_dpi_awareness()  # Windows'ta DPI farkındalığını devre dışı bırak (daha hızlı açılır)
ctk.set_appearance_mode("System")  # Sistem temasını kullan
ctk.set_default_color_theme("blue")

# Performans iyileştirme için cache fonksiyonları
@lru_cache(maxsize=32)
def cached_rgb_to_hex(r, g, b):
    """RGB renk değerini hex string'e dönüştürme (önbellekli)"""
    return f"#{r:02x}{g:02x}{b:02x}"

@lru_cache(maxsize=32)
def cached_hex_to_rgb(hex_color):
    """Hex renk değerini RGB'ye dönüştürme (önbellekli)"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Ana uygulama sınıfı
class ProOtomatikTiklayici(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Başlık ve ikon ayarlama
        self.title("✨ Pro Otomatik Tıklayıcı v1.5 | Created by ZERS ©")
        self.iconpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        if os.path.exists(self.iconpath):
            icon = tk.PhotoImage(file=self.iconpath)
            self.iconphoto(True, icon)
            self.wm_iconbitmap(default=self.iconpath)
        
        # Ekran boyutu ayarları
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.width = 900
        self.height = 700
        
        # Pencere boyutu ve konumu
        x = (self.screen_width - self.width) // 2
        y = (self.screen_height - self.height) // 2
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")
        self.minsize(800, 600)
        
        # Şeffaflık ayarı (Windows'ta çalışır)
        self.transparency = 1.0  # 0.0-1.0 arası değer
        
        # Ana değişkenleri başlat
        self.running = False
        self.recording = False
        self.click_positions = []
        self.record_listener = None
        self.click_thread = None
        self.mouse = MouseController()
        self.keyboard_controller = KeyboardController()
        self.current_position = (0, 0)
        self.key_listener = None
        self.start_hotkey = ctk.StringVar(value="F6")
        self.stop_hotkey = ctk.StringVar(value="F7")
        self.region_capture_active = False
        self.screen_detection_running = False
        self.anti_afk_running = False
        self.anti_afk_thread = None
        self.anti_afk_keys = ctk.StringVar(value="w,a,s,d,space")
        self.anti_afk_movement = ctk.BooleanVar(value=True)
        self.anti_afk_jump = ctk.BooleanVar(value=True)
        self.anti_afk_rotate = ctk.BooleanVar(value=True)
        self.anti_afk_interval = ctk.DoubleVar(value=30.0)
        
        # Macro değişkenleri
        self.recording_macro = False
        self.macro_events = []
        self.macro_start_time = 0
        self.macro_recording_listeners = []
        self.macro_keyboard_listener = None
        self.macro_mouse_listener = None
        self.macro_playback_running = False
        self.macro_playback_thread = None
        self.macros = {}  # Kayıtlı makrolar
        self.current_macro_name = ctk.StringVar(value="")
        self.macro_repeat_count = ctk.IntVar(value=1)
        self.macro_repeat_infinite = ctk.BooleanVar(value=False)  # Eksik olan değişken
        self.macro_play_speed = ctk.DoubleVar(value=1.0)
        self.macro_random_delay = ctk.BooleanVar(value=False)
        self.macro_random_min = ctk.DoubleVar(value=0.9)
        self.macro_random_max = ctk.DoubleVar(value=1.1)
        
        # Görünüm değişkenleri
        self.transparency_var = ctk.DoubleVar(value=1.0)
        
        # Tıklama ayarları
        self.click_button = ctk.StringVar(value="sol")
        self.click_interval = ctk.DoubleVar(value=1.0)
        self.click_pattern = ctk.StringVar(value="sabit")
        self.random_min = ctk.DoubleVar(value=0.5)
        self.random_max = ctk.DoubleVar(value=1.5)
        self.infinite_clicks = ctk.BooleanVar(value=True)
        self.max_clicks = ctk.IntVar(value=100)
        self.clicks_count = ctk.IntVar(value=0)
        self.multiple_positions = ctk.BooleanVar(value=False)
        self.mouse_pos_var = ctk.StringVar(value="0, 0")
        self.enable_time_stop = ctk.BooleanVar(value=False)
        self.stop_after_mins = ctk.IntVar(value=30)
        
        # Ekran algılama değişkenleri
        self.detection_running = False
        self.detection_thread = None
        self.color_to_detect = ctk.StringVar(value="#FF0000")
        self.threshold = ctk.IntVar(value=50)
        self.check_interval = ctk.DoubleVar(value=1.0)
        self.region_coords = None
        self.preview_image = None
        self.auto_click_when_detect = ctk.BooleanVar(value=False)
        self.auto_click_delay = ctk.DoubleVar(value=0.5)
        
        # Arayüz hazırla
        self.setup_ui()
        
        # Ayarları yükle
        self.load_settings()
        
        # Klavye dinleyiciyi başlat
        self.setup_keyboard_listener()
        
        # Fare pozisyon güncelleyicisini başlat
        self.start_position_updater()
        
        # Kapandığında ayarları kaydet
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_ui(self):
        # Ana çerçeve grid yapısını yapılandır
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Ana sekme görünümü
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        
        # Sekmeleri oluştur
        self.tabview.add("Kontrol")
        self.tabview.add("Gelişmiş")
        self.tabview.add("Konumlar")
        self.tabview.add("Oyun Araçları")
        self.tabview.add("Ekran Tanıma")
        self.tabview.add("Makro")
        self.tabview.add("Görünüm")
        
        # Varsayılan sekmeyi seç
        self.tabview.set("Kontrol")
        
        # Sekme içeriklerini doldur
        self.setup_control_tab()
        self.setup_advanced_tab()
        self.setup_positions_tab()
        self.setup_game_tools_tab()
        self.setup_screen_detection_tab()
        self.setup_macro_tab()
        self.setup_appearance_tab()
        
        # Durum çubuğu
        status_frame = ctk.CTkFrame(self, corner_radius=0, height=30)
        status_frame.grid(row=1, column=0, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)
        status_frame.grid_columnconfigure(2, weight=1)
        
        # Durum etiketi
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="Hazır | Başlatmak için F6 tuşuna basın",
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Telif hakkı bilgisi
        self.copyright_label = ctk.CTkLabel(
            status_frame,
            text="Created by ZERS © | LİSANS HAKLARI BANA AİT",
            font=("Segoe UI", 9),
            text_color="#FFB700"
        )
        self.copyright_label.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Fare pozisyonu göstergesi
        self.pos_label = ctk.CTkLabel(
            status_frame, 
            text="X: 0, Y: 0",
            anchor="e"
        )
        self.pos_label.grid(row=0, column=2, padx=10, pady=5, sticky="e")
    
    def setup_control_tab(self):
        tab = self.tabview.tab("Kontrol")
        tab.grid_columnconfigure(0, weight=1)
        
        # Kontrol paneli çerçevesi
        control_frame = ctk.CTkFrame(tab)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        
        # Tıklama aralığı
        ctk.CTkLabel(control_frame, text="Tıklama Aralığı (saniye):", anchor="w").grid(row=0, column=0, padx=15, pady=5, sticky="w")
        interval_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        interval_frame.grid(row=0, column=1, padx=15, pady=5, sticky="e")
        
        ctk.CTkSlider(
            interval_frame, 
            from_=0.01, 
            to=5.0, 
            variable=self.click_interval, 
            width=200
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkEntry(
            interval_frame,
            textvariable=self.click_interval,
            width=70
        ).pack(side="left")
        
        # Tıklama tuşu
        ctk.CTkLabel(control_frame, text="Tıklama Tuşu:", anchor="w").grid(row=1, column=0, padx=15, pady=5, sticky="w")
        button_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_frame.grid(row=1, column=1, padx=15, pady=5, sticky="e")
        
        ctk.CTkRadioButton(button_frame, text="Sol Tık", variable=self.click_button, value="sol").pack(side="left", padx=10)
        ctk.CTkRadioButton(button_frame, text="Sağ Tık", variable=self.click_button, value="sag").pack(side="left", padx=10)
        ctk.CTkRadioButton(button_frame, text="Orta Tık", variable=self.click_button, value="orta").pack(side="left", padx=10)
        
        # Tıklama sayısı
        ctk.CTkLabel(control_frame, text="Tıklama Sayısı:", anchor="w").grid(row=2, column=0, padx=15, pady=5, sticky="w")
        count_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        count_frame.grid(row=2, column=1, padx=15, pady=5, sticky="e")
        
        ctk.CTkRadioButton(count_frame, text="Sonsuz", variable=self.infinite_clicks, value=True).pack(anchor="w")
        
        limited_frame = ctk.CTkFrame(count_frame, fg_color="transparent")
        limited_frame.pack(anchor="w", pady=5)
        
        ctk.CTkRadioButton(limited_frame, text="Sınırlı:", variable=self.infinite_clicks, value=False).pack(side="left")
        
        ctk.CTkEntry(
            limited_frame,
            textvariable=self.max_clicks,
            width=70
        ).pack(side="left", padx=10)
        
        # Kısayol tuşları
        ctk.CTkLabel(control_frame, text="Kısayol Tuşları:", anchor="w").grid(row=3, column=0, padx=15, pady=5, sticky="w")
        hotkey_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        hotkey_frame.grid(row=3, column=1, padx=15, pady=5, sticky="e")
        
        ctk.CTkLabel(hotkey_frame, text="Başlat:").pack(side="left")
        ctk.CTkOptionMenu(
            hotkey_frame, 
            variable=self.start_hotkey,
            values=["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"],
            width=70
        ).pack(side="left", padx=10)
        
        ctk.CTkLabel(hotkey_frame, text="Durdur:").pack(side="left")
        ctk.CTkOptionMenu(
            hotkey_frame, 
            variable=self.stop_hotkey,
            values=["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"],
            width=70
        ).pack(side="left", padx=10)
        
        # Butonlar
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.grid(row=1, column=0, pady=20, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Başlat butonu
        self.start_button = ctk.CTkButton(
            button_frame,
            text="BAŞLAT",
            command=self.start_clicking,
            fg_color="#2D7738",
            hover_color="#225C2B",
            height=40,
            font=("Segoe UI", 14, "bold")
        )
        self.start_button.grid(row=0, column=0, padx=10, sticky="ew")
        
        # Durdur butonu
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="DURDUR",
            command=self.stop_clicking,
            fg_color="#C42B1C",
            hover_color="#951409",
            height=40,
            font=("Segoe UI", 14, "bold"),
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=10, sticky="ew")
        
        # İstatistikler çerçevesi
        stats_frame = ctk.CTkFrame(tab)
        stats_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(stats_frame, text="Toplam Tıklama Sayısı:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.click_counter = ctk.CTkLabel(stats_frame, textvariable=self.clicks_count, font=("Segoe UI", 14, "bold"))
        self.click_counter.grid(row=0, column=1, padx=15, pady=10, sticky="e")
    
    def setup_advanced_tab(self):
        tab = self.tabview.tab("Gelişmiş")
        tab.grid_columnconfigure(0, weight=1)
        
        # Gelişmiş ayarlar çerçevesi
        adv_frame = ctk.CTkFrame(tab)
        adv_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        adv_frame.grid_columnconfigure(0, weight=1)
        adv_frame.grid_columnconfigure(1, weight=1)
        
        # Tıklama deseni
        ctk.CTkLabel(adv_frame, text="Tıklama Deseni:", anchor="w").grid(row=0, column=0, padx=15, pady=15, sticky="w")
        pattern_frame = ctk.CTkFrame(adv_frame, fg_color="transparent")
        pattern_frame.grid(row=0, column=1, padx=15, pady=15, sticky="e")
        
        ctk.CTkRadioButton(pattern_frame, text="Sabit Aralık", variable=self.click_pattern, value="sabit").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(pattern_frame, text="Rastgele Gecikmeli", variable=self.click_pattern, value="rastgele").pack(anchor="w", pady=2)
        
        # Rastgele gecikme ayarları
        delay_frame = ctk.CTkFrame(adv_frame, fg_color="transparent")
        delay_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="ew")
        
        ctk.CTkLabel(delay_frame, text="Gecikme Aralığı (saniye):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        min_frame = ctk.CTkFrame(delay_frame, fg_color="transparent")
        min_frame.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(min_frame, text="Min:").pack(side="left")
        ctk.CTkEntry(min_frame, textvariable=self.random_min, width=60).pack(side="left", padx=5)
        
        max_frame = ctk.CTkFrame(delay_frame, fg_color="transparent")
        max_frame.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ctk.CTkLabel(max_frame, text="Max:").pack(side="left")
        ctk.CTkEntry(max_frame, textvariable=self.random_max, width=60).pack(side="left", padx=5)
        
        # Otomatik durdurma ayarları
        auto_stop_frame = ctk.CTkFrame(adv_frame)
        auto_stop_frame.grid(row=2, column=0, columnspan=2, padx=15, pady=15, sticky="ew")
        auto_stop_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(auto_stop_frame, text="Otomatik Durdurma Seçenekleri", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.stop_after_mins = ctk.IntVar(value=0)
        stop_time_frame = ctk.CTkFrame(auto_stop_frame, fg_color="transparent")
        stop_time_frame.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.enable_time_stop = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(stop_time_frame, text="Belirli süre sonra durdur:", variable=self.enable_time_stop).pack(side="left", padx=5)
        ctk.CTkEntry(stop_time_frame, textvariable=self.stop_after_mins, width=60).pack(side="left", padx=5)
        ctk.CTkLabel(stop_time_frame, text="dakika").pack(side="left", padx=5)
    
    def setup_positions_tab(self):
        tab = self.tabview.tab("Konumlar")
        tab.grid_columnconfigure(0, weight=1)
        
        # Kontrol çerçevesi
        control_frame = ctk.CTkFrame(tab)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        
        # Çoklu konum desteği
        ctk.CTkLabel(control_frame, text="Çoklu Konum Desteği:", anchor="w").grid(row=0, column=0, padx=15, pady=15, sticky="w")
        ctk.CTkSwitch(control_frame, text="Aktif", variable=self.multiple_positions).grid(row=0, column=1, padx=15, pady=15, sticky="e")
        
        # Kayıt butonları
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        self.record_button = ctk.CTkButton(
            button_frame,
            text="Konumları Kaydet",
            command=self.start_recording,
            fg_color="#0063B1",
            hover_color="#004881"
        )
        self.record_button.grid(row=0, column=0, padx=10, sticky="ew")
        
        self.clear_button = ctk.CTkButton(
            button_frame,
            text="Konumları Temizle",
            command=self.clear_positions,
            fg_color="#5D5A58",
            hover_color="#3B3A39"
        )
        self.clear_button.grid(row=0, column=1, padx=10, sticky="ew")
        
        # Konum listesi
        list_frame = ctk.CTkFrame(tab)
        list_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(list_frame, text="Kaydedilen Konumlar:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=15, pady=5, sticky="w")
        
        self.position_list = tk.Listbox(list_frame, bg="#2B2B2B", fg="white", selectbackground="#0078D7", font=("Segoe UI", 10))
        self.position_list.grid(row=1, column=0, padx=15, pady=10, sticky="nsew")
    
    def setup_game_tools_tab(self):
        tab = self.tabview.tab("Oyun Araçları")
        tab.grid_columnconfigure(0, weight=1)
        
        # Roblox Anti-AFK
        roblox_frame = ctk.CTkFrame(tab)
        roblox_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        roblox_frame.grid_columnconfigure(0, weight=1)
        
        # Başlık
        ctk.CTkLabel(roblox_frame, text="Roblox Anti-AFK Sistemi", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        ctk.CTkLabel(roblox_frame, text="Roblox oyunlarında AFK kalmayı önlemek için otomatik hareket").grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")
        
        # Ayarlar çerçevesi
        settings_frame = ctk.CTkFrame(roblox_frame)
        settings_frame.grid(row=2, column=0, padx=15, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # Zaman aralığı
        ctk.CTkLabel(settings_frame, text="Hareket Aralığı (saniye):", anchor="w").grid(row=0, column=0, padx=15, pady=10, sticky="w")
        interval_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        interval_frame.grid(row=0, column=1, padx=15, pady=10, sticky="e")
        
        ctk.CTkSlider(
            interval_frame, 
            from_=10, 
            to=120, 
            variable=self.anti_afk_interval, 
            width=150
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkEntry(
            interval_frame,
            textvariable=self.anti_afk_interval,
            width=60
        ).pack(side="left")
        
        # Hareket türleri
        movement_frame = ctk.CTkFrame(settings_frame)
        movement_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=10, sticky="ew")
        movement_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(movement_frame, text="Hareket Türleri:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Hareket seçenekleri
        options_frame = ctk.CTkFrame(movement_frame, fg_color="transparent")
        options_frame.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        ctk.CTkCheckBox(options_frame, text="WASD ile Hareket", variable=self.anti_afk_movement).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkCheckBox(options_frame, text="Zıplama", variable=self.anti_afk_jump).grid(row=0, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkCheckBox(options_frame, text="Kamera Döndürme", variable=self.anti_afk_rotate).grid(row=0, column=2, padx=10, pady=5, sticky="w")
        
        # Özel tuşlar
        keys_frame = ctk.CTkFrame(settings_frame)
        keys_frame.grid(row=2, column=0, columnspan=2, padx=15, pady=10, sticky="ew")
        keys_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(keys_frame, text="Özel Tuşlar:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkEntry(keys_frame, textvariable=self.anti_afk_keys, width=250).grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(keys_frame, text="Virgülle ayırın, örn: w,a,s,d,space").grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="w")
        
        # Butonlar
        button_frame = ctk.CTkFrame(roblox_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, pady=20, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Başlat butonu
        self.afk_start_button = ctk.CTkButton(
            button_frame,
            text="ANTI-AFK BAŞLAT",
            command=self.start_anti_afk,
            fg_color="#2D7738",
            hover_color="#225C2B",
            height=40,
            font=("Segoe UI", 14, "bold")
        )
        self.afk_start_button.grid(row=0, column=0, padx=10, sticky="ew")
        
        # Durdur butonu
        self.afk_stop_button = ctk.CTkButton(
            button_frame,
            text="ANTI-AFK DURDUR",
            command=self.stop_anti_afk,
            fg_color="#C42B1C",
            hover_color="#951409",
            height=40,
            font=("Segoe UI", 14, "bold"),
            state="disabled"
        )
        self.afk_stop_button.grid(row=0, column=1, padx=10, sticky="ew")
        
        # Bilgi çerçevesi
        info_frame = ctk.CTkFrame(tab)
        info_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            info_frame, 
            text="Bu özellik Roblox'ta otomatik olarak karakterinizi hareket ettirir ve\nAFK sisteminin sizi oyundan atmasını engeller.",
            font=("Segoe UI", 11),
            justify="left"
        ).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        # Durum
        self.anti_afk_status = ctk.CTkLabel(
            info_frame, 
            text="Durum: Hazır", 
            font=("Segoe UI", 12, "bold")
        )
        self.anti_afk_status.grid(row=1, column=0, padx=15, pady=10, sticky="w")
    
    def setup_screen_detection_tab(self):
        tab = self.tabview.tab("Ekran Tanıma")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)  # Önizleme alanı için ağırlık
        
        # Ekran bölgesi tanıma başlık ve açıklama
        header_frame = ctk.CTkFrame(tab)
        header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header_frame, 
            text="Ekran Renk/Bölge Tanıma", 
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        
        ctk.CTkLabel(
            header_frame, 
            text="Belirli bir rengin veya bölgenin ekranda görünmesini bekleyin ve otomatik tıklayın.",
            font=("Segoe UI", 11)
        ).grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")
        
        # Ayarlar çerçevesi
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # Bölge seçimi
        ctk.CTkLabel(settings_frame, text="Ekran Bölgesi:", anchor="w").grid(row=0, column=0, padx=15, pady=10, sticky="w")
        region_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        region_frame.grid(row=0, column=1, padx=15, pady=10, sticky="e")
        
        self.region_button = ctk.CTkButton(
            region_frame,
            text="Bölge Seç",
            command=self.capture_screen_region,
            width=120
        )
        self.region_button.pack(side="left", padx=5)
        
        self.region_info = ctk.CTkLabel(region_frame, text="Seçilmedi")
        self.region_info.pack(side="left", padx=5)
        
        # Renk seçimi
        ctk.CTkLabel(settings_frame, text="Renk Tanıma:", anchor="w").grid(row=1, column=0, padx=15, pady=10, sticky="w")
        color_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        color_frame.grid(row=1, column=1, padx=15, pady=10, sticky="e")
        
        self.color_button = ctk.CTkButton(
            color_frame,
            text="Renk Seç",
            command=self.pick_color,
            width=120
        )
        self.color_button.pack(side="left", padx=5)
        
        self.color_preview = ctk.CTkFrame(color_frame, width=30, height=20, fg_color=self.rgb_to_hex(self.color_to_detect.get()))
        self.color_preview.pack(side="left", padx=5)
        
        # Tolerans ayarı
        ctk.CTkLabel(settings_frame, text="Renk Toleransı:", anchor="w").grid(row=2, column=0, padx=15, pady=10, sticky="w")
        tolerance_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        tolerance_frame.grid(row=2, column=1, padx=15, pady=10, sticky="e")
        
        ctk.CTkSlider(
            tolerance_frame, 
            from_=5, 
            to=100, 
            variable=self.threshold, 
            width=150
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(tolerance_frame, textvariable=self.threshold).pack(side="left")
        
        # Tarama aralığı
        ctk.CTkLabel(settings_frame, text="Tarama Aralığı (saniye):", anchor="w").grid(row=3, column=0, padx=15, pady=10, sticky="w")
        interval_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        interval_frame.grid(row=3, column=1, padx=15, pady=10, sticky="e")
        
        ctk.CTkSlider(
            interval_frame, 
            from_=0.1, 
            to=5.0, 
            variable=self.check_interval, 
            width=150
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkEntry(
            interval_frame,
            textvariable=self.check_interval,
            width=60
        ).pack(side="left")
        
        # Butonlar
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.grid(row=3, column=0, pady=10, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Başlat butonu
        self.detect_start_button = ctk.CTkButton(
            button_frame,
            text="TARAMAYI BAŞLAT",
            command=self.start_screen_detection,
            fg_color="#2D7738",
            hover_color="#225C2B",
            height=40,
            font=("Segoe UI", 14, "bold")
        )
        self.detect_start_button.grid(row=0, column=0, padx=10, sticky="ew")
        
        # Durdur butonu
        self.detect_stop_button = ctk.CTkButton(
            button_frame,
            text="TARAMAYI DURDUR",
            command=self.stop_screen_detection,
            fg_color="#C42B1C",
            hover_color="#951409",
            height=40,
            font=("Segoe UI", 14, "bold"),
            state="disabled"
        )
        self.detect_stop_button.grid(row=0, column=1, padx=10, sticky="ew")
        
        # Önizleme alanı
        preview_frame = ctk.CTkFrame(tab)
        preview_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        
        # Önizleme etiketi
        self.preview_label = ctk.CTkLabel(preview_frame, text="Bölge seçildiğinde önizleme burada görünecek")
        self.preview_label.grid(row=0, column=0, sticky="nsew")
        
        # Durum
        self.detection_status = ctk.CTkLabel(
            tab, 
            text="Durum: Hazır", 
            font=("Segoe UI", 12, "bold")
        )
        self.detection_status.grid(row=4, column=0, padx=15, pady=10, sticky="w")
    
    def setup_macro_tab(self):
        tab = self.tabview.tab("Makro")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(3, weight=1)  # Makro liste alanı için ağırlık
        
        # Makro kayıt başlık ve açıklama
        header_frame = ctk.CTkFrame(tab)
        header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header_frame, 
            text="Makro Kayıt ve Oynatma", 
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
        
        ctk.CTkLabel(
            header_frame, 
            text="Fare ve klavye hareketlerinizi kaydedip otomatik olarak tekrarlayabilirsiniz.",
            font=("Segoe UI", 11)
        ).grid(row=1, column=0, padx=15, pady=(0, 15), sticky="w")
        
        # Makro isim ve kayıt kontrolleri
        controls_frame = ctk.CTkFrame(tab)
        controls_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        controls_frame.grid_columnconfigure(1, weight=1)
        
        # Makro ismi
        ctk.CTkLabel(controls_frame, text="Makro İsmi:", anchor="w").grid(row=0, column=0, padx=15, pady=10, sticky="w")
        ctk.CTkEntry(controls_frame, textvariable=self.current_macro_name, width=250).grid(row=0, column=1, padx=15, pady=10, sticky="ew")
        
        # Kayıt butonları
        button_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        button_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=10, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        
        self.record_macro_button = ctk.CTkButton(
            button_frame,
            text="KAYDI BAŞLAT",
            command=self.start_macro_recording,
            fg_color="#2D7738",
            hover_color="#225C2B",
            font=("Segoe UI", 12, "bold")
        )
        self.record_macro_button.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.stop_macro_button = ctk.CTkButton(
            button_frame,
            text="KAYDI DURDUR",
            command=self.stop_macro_recording,
            fg_color="#C42B1C",
            hover_color="#951409",
            font=("Segoe UI", 12, "bold"),
            state="disabled"
        )
        self.stop_macro_button.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.play_macro_button = ctk.CTkButton(
            button_frame,
            text="MAKROYU OYNAT",
            command=self.play_macro,
            fg_color="#0063B1",
            hover_color="#004881",
            font=("Segoe UI", 12, "bold")
        )
        self.play_macro_button.grid(row=0, column=2, padx=5, sticky="ew")
        
        # Ayarlar çerçevesi
        settings_frame = ctk.CTkFrame(tab)
        settings_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # Tekrarlama seçenekleri
        repeat_frame = ctk.CTkFrame(settings_frame)
        repeat_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        repeat_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(repeat_frame, text="Tekrarlama:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        repeat_options = ctk.CTkFrame(repeat_frame, fg_color="transparent")
        repeat_options.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        ctk.CTkRadioButton(repeat_options, text="Belirli Sayıda:", variable=self.macro_repeat_infinite, value=False).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkEntry(repeat_options, textvariable=self.macro_repeat_count, width=60).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkRadioButton(repeat_options, text="Sonsuz Tekrar", variable=self.macro_repeat_infinite, value=True).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Hız ayarları
        speed_frame = ctk.CTkFrame(settings_frame)
        speed_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        speed_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(speed_frame, text="Hız ve Zamanlama:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Hız çarpanı
        speed_control = ctk.CTkFrame(speed_frame, fg_color="transparent")
        speed_control.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(speed_control, text="Hız Çarpanı:").pack(side="left", padx=5)
        ctk.CTkSlider(
            speed_control, 
            from_=0.1, 
            to=3.0, 
            variable=self.macro_play_speed, 
            width=150
        ).pack(side="left", padx=5)
        ctk.CTkLabel(speed_control, textvariable=self.macro_play_speed).pack(side="left", padx=5)
        
        # Rastgele gecikme
        random_delay = ctk.CTkFrame(speed_frame, fg_color="transparent")
        random_delay.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkCheckBox(random_delay, text="Rastgele Gecikme Ekle", variable=self.macro_random_delay).pack(side="left", padx=5)
        
        delay_values = ctk.CTkFrame(speed_frame, fg_color="transparent")
        delay_values.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(delay_values, text="Min:").pack(side="left", padx=5)
        ctk.CTkEntry(delay_values, textvariable=self.macro_random_min, width=60).pack(side="left", padx=5)
        
        ctk.CTkLabel(delay_values, text="Max:").pack(side="left", padx=5)
        ctk.CTkEntry(delay_values, textvariable=self.macro_random_max, width=60).pack(side="left", padx=5)
        ctk.CTkLabel(delay_values, text="çarpan").pack(side="left", padx=5)
        
        # Makro listesi
        list_frame = ctk.CTkFrame(tab)
        list_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        
        # Liste başlığı
        ctk.CTkLabel(list_frame, text="Kaydedilen Makrolar:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=15, pady=5, sticky="w")
        
        # Makro listesi
        self.macro_listbox = tk.Listbox(list_frame, bg="#2B2B2B", fg="white", selectbackground="#0078D7", font=("Segoe UI", 10), height=6)
        self.macro_listbox.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")
        self.macro_listbox.bind("<<ListboxSelect>>", self.on_macro_select)
        
        # Liste kontrol butonları
        list_controls = ctk.CTkFrame(list_frame, fg_color="transparent")
        list_controls.grid(row=2, column=0, padx=15, pady=10, sticky="ew")
        list_controls.grid_columnconfigure(0, weight=1)
        list_controls.grid_columnconfigure(1, weight=1)
        list_controls.grid_columnconfigure(2, weight=1)
        
        ctk.CTkButton(
            list_controls,
            text="Kaydet",
            command=self.save_macro,
            width=100
        ).grid(row=0, column=0, padx=5, sticky="ew")
        
        ctk.CTkButton(
            list_controls,
            text="Sil",
            command=self.delete_macro,
            width=100
        ).grid(row=0, column=1, padx=5, sticky="ew")
        
        ctk.CTkButton(
            list_controls,
            text="Dışa Aktar",
            command=self.export_macro,
            width=100
        ).grid(row=0, column=2, padx=5, sticky="ew")
        
        # Durum
        self.macro_status = ctk.CTkLabel(
            tab, 
            text="Durum: Hazır", 
            font=("Segoe UI", 12, "bold")
        )
        self.macro_status.grid(row=4, column=0, padx=15, pady=10, sticky="w")
        
        # Makro listesini doldur
        self.update_macro_list()
    
    def start_macro_recording(self):
        if self.recording_macro:
            return
        
        self.recording_macro = True
        self.record_macro_button.configure(state="disabled")
        self.stop_macro_button.configure(state="normal")
        self.play_macro_button.configure(state="disabled")
        
        # Makro olaylarını sıfırla
        self.macro_events = []
        self.macro_start_time = time.time()
        
        # Durum güncelle
        self.macro_status.configure(text="Durum: Kaydediliyor... Fare ve klavye hareketlerini takip ediyorum.")
        
        # Fare dinleyicisi
        def on_move(x, y):
            if self.recording_macro:
                current_time = time.time() - self.macro_start_time
                self.macro_events.append({"type": "move", "x": x, "y": y, "time": current_time})
        
        def on_click(x, y, button, pressed):
            if self.recording_macro:
                current_time = time.time() - self.macro_start_time
                btn = "left" if button == Button.left else "right" if button == Button.right else "middle"
                self.macro_events.append({"type": "click", "x": x, "y": y, "button": btn, "pressed": pressed, "time": current_time})
        
        def on_scroll(x, y, dx, dy):
            if self.recording_macro:
                current_time = time.time() - self.macro_start_time
                self.macro_events.append({"type": "scroll", "x": x, "y": y, "dx": dx, "dy": dy, "time": current_time})
        
        # Klavye dinleyicisi
        def on_press(key):
            if self.recording_macro:
                current_time = time.time() - self.macro_start_time
                key_str = str(key).replace("'", "")
                self.macro_events.append({"type": "key_press", "key": key_str, "time": current_time})
        
        def on_release(key):
            if self.recording_macro:
                current_time = time.time() - self.macro_start_time
                key_str = str(key).replace("'", "")
                self.macro_events.append({"type": "key_release", "key": key_str, "time": current_time})
                
                # ESC tuşu ile durdurma
                if key == keyboard.Key.esc:
                    self.after(10, self.stop_macro_recording)
        
        # Dinleyicileri başlat
        self.macro_mouse_listener = MouseListener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        self.macro_mouse_listener.start()
        
        self.macro_keyboard_listener = KeyboardListener(on_press=on_press, on_release=on_release)
        self.macro_keyboard_listener.start()
    
    def stop_macro_recording(self):
        if not self.recording_macro:
            return
        
        self.recording_macro = False
        self.record_macro_button.configure(state="normal")
        self.stop_macro_button.configure(state="disabled")
        self.play_macro_button.configure(state="normal")
        
        # Dinleyicileri durdur
        if self.macro_mouse_listener:
            self.macro_mouse_listener.stop()
        
        if self.macro_keyboard_listener:
            self.macro_keyboard_listener.stop()
        
        # Kayıt istatistiklerini göster
        event_count = len(self.macro_events)
        duration = self.macro_events[-1]["time"] if self.macro_events else 0
        
        self.macro_status.configure(text=f"Durum: Kayıt tamamlandı - {event_count} olay, {duration:.2f} saniye")
        
        # Makroyu otomatik kaydet
        if self.macro_events:
            self.save_macro()
    
    def play_macro(self):
        if self.macro_playback_running or not self.macro_events:
            return
        
        # Makro verilerini kontrol et
        if len(self.macro_events) == 0:
            self.macro_status.configure(text="Durum: Oynatılacak makro bulunamadı!")
            return
        
        self.macro_playback_running = True
        self.record_macro_button.configure(state="disabled")
        self.stop_macro_button.configure(state="disabled")
        self.play_macro_button.configure(state="disabled")
        
        # Makro oynatma thread'ini başlat
        self.macro_playback_thread = threading.Thread(target=self.macro_playback_task)
        self.macro_playback_thread.daemon = True
        self.macro_playback_thread.start()
        
        self.macro_status.configure(text="Durum: Makro oynatılıyor...")
    
    def macro_playback_task(self):
        # Tekrarlama sayısını al
        if self.macro_repeat_infinite.get():
            repeat_count = float('inf')  # Sonsuz
        else:
            repeat_count = max(1, self.macro_repeat_count.get())
        
        # Hız çarpanını al
        speed_factor = self.macro_play_speed.get()
        
        for repeat in range(int(repeat_count)):
            if not self.macro_playback_running:
                break
            
            # İlk olay zamanını al
            if self.macro_events:
                start_time = self.macro_events[0]["time"]
            else:
                break
            
            # Her olayı oynat
            play_start_time = time.time()
            
            for i, event in enumerate(self.macro_events):
                if not self.macro_playback_running:
                    break
                
                # Önceki olaydan bu yana gereken süreyi hesapla
                if i > 0:
                    wait_time = (event["time"] - self.macro_events[i-1]["time"]) / speed_factor
                    
                    # Rastgele gecikme ekle
                    if self.macro_random_delay.get():
                        min_factor = self.macro_random_min.get()
                        max_factor = self.macro_random_max.get()
                        random_factor = min_factor + (max_factor - min_factor) * random.random()
                        wait_time *= random_factor
                    
                    # Bekle
                    time.sleep(max(0, wait_time))
                
                # Olayı gerçekleştir
                self.execute_macro_event(event)
                
                # Durum güncelle
                progress = (i + 1) / len(self.macro_events) * 100
                if repeat_count != float('inf'):
                    self.after(10, lambda p=progress, r=repeat+1, t=repeat_count: 
                               self.macro_status.configure(text=f"Durum: Makro oynatılıyor... %{p:.1f} (Tekrar {r}/{t})"))
                else:
                    self.after(10, lambda p=progress, r=repeat+1: 
                               self.macro_status.configure(text=f"Durum: Makro oynatılıyor... %{p:.1f} (Tekrar {r})"))
        
        # Tamamlandı
        self.macro_playback_running = False
        self.after(10, lambda: self.record_macro_button.configure(state="normal"))
        self.after(10, lambda: self.play_macro_button.configure(state="normal"))
        self.after(10, lambda: self.macro_status.configure(text="Durum: Makro oynatma tamamlandı"))
    
    def execute_macro_event(self, event):
        try:
            event_type = event["type"]
            
            if event_type == "move":
                self.mouse.position = (event["x"], event["y"])
            
            elif event_type == "click":
                x, y = event["x"], event["y"]
                button = Button.left if event["button"] == "left" else Button.right if event["button"] == "right" else Button.middle
                
                # Fareyi konuma taşı
                self.mouse.position = (x, y)
                
                # Basma veya bırakma
                if event["pressed"]:
                    self.mouse.press(button)
                else:
                    self.mouse.release(button)
            
            elif event_type == "scroll":
                self.mouse.position = (event["x"], event["y"])
                self.mouse.scroll(event["dx"], event["dy"])
            
            elif event_type == "key_press":
                key_str = event["key"]
                self.simulate_key_press(key_str)
            
            elif event_type == "key_release":
                key_str = event["key"]
                self.simulate_key_release(key_str)
            
        except Exception as e:
            print(f"Macro playback error: {str(e)}")
    
    def simulate_key_press(self, key_str):
        try:
            # Özel tuşları işle
            if key_str.startswith("Key."):
                key_name = key_str.replace("Key.", "")
                special_key = getattr(keyboard.Key, key_name, None)
                if special_key:
                    self.keyboard_controller.press(special_key)
            else:
                # Normal tuşları işle
                self.keyboard_controller.press(key_str)
        except Exception as e:
            print(f"Key press error: {str(e)}")
    
    def simulate_key_release(self, key_str):
        try:
            # Özel tuşları işle
            if key_str.startswith("Key."):
                key_name = key_str.replace("Key.", "")
                special_key = getattr(keyboard.Key, key_name, None)
                if special_key:
                    self.keyboard_controller.release(special_key)
            else:
                # Normal tuşları işle
                self.keyboard_controller.release(key_str)
        except Exception as e:
            print(f"Key release error: {str(e)}")
    
    def save_macro(self):
        if not self.macro_events:
            self.macro_status.configure(text="Durum: Kaydedilecek makro yok!")
            return
        
        # Yeni makro nesnesi oluştur
        macro_name = self.current_macro_name.get()
        if not macro_name:
            macro_name = f"Makro {len(self.macros) + 1}"
            self.current_macro_name.set(macro_name)
        
        # Mevcut seçili makro mu yoksa yeni mi?
        if self.selected_macro_index >= 0 and self.selected_macro_index < len(self.macros):
            # Mevcut makroyu güncelle
            self.macros[self.selected_macro_index] = {
                "name": macro_name,
                "events": self.macro_events,
                "repeat_count": self.macro_repeat_count.get(),
                "repeat_infinite": self.macro_repeat_infinite.get(),
                "speed": self.macro_play_speed.get(),
                "random_delay": self.macro_random_delay.get(),
                "random_min": self.macro_random_min.get(),
                "random_max": self.macro_random_max.get()
            }
        else:
            # Yeni makro ekle
            self.macros.append({
                "name": macro_name,
                "events": self.macro_events,
                "repeat_count": self.macro_repeat_count.get(),
                "repeat_infinite": self.macro_repeat_infinite.get(),
                "speed": self.macro_play_speed.get(),
                "random_delay": self.macro_random_delay.get(),
                "random_min": self.macro_random_min.get(),
                "random_max": self.macro_random_max.get()
            })
        
        # Listeyi güncelle
        self.update_macro_list()
        self.save_settings()
        
        self.macro_status.configure(text=f"Durum: '{macro_name}' ismiyle makro kaydedildi")
    
    def delete_macro(self):
        if self.selected_macro_index < 0 or self.selected_macro_index >= len(self.macros):
            self.macro_status.configure(text="Durum: Silinecek makro seçilmedi!")
            return
        
        # Makro ismini al
        macro_name = self.macros[self.selected_macro_index]["name"]
        
        # Makroyu sil
        self.macros.pop(self.selected_macro_index)
        
        # Listeyi güncelle
        self.update_macro_list()
        self.selected_macro_index = -1
        self.save_settings()
        
        self.macro_status.configure(text=f"Durum: '{macro_name}' makrosu silindi")
    
    def export_macro(self):
        if self.selected_macro_index < 0 or self.selected_macro_index >= len(self.macros):
            self.macro_status.configure(text="Durum: Dışa aktarılacak makro seçilmedi!")
            return
        
        try:
            macro_data = self.macros[self.selected_macro_index]
            macro_name = macro_data["name"]
            
            # JSON olarak kaydet
            file_name = f"{macro_name.replace(' ', '_')}.macro"
            
            with open(file_name, "w") as f:
                json.dump(macro_data, f, indent=2)
            
            self.macro_status.configure(text=f"Durum: '{macro_name}' makrosu '{file_name}' dosyasına aktarıldı")
        except Exception as e:
            self.macro_status.configure(text=f"Durum: Dışa aktarma hatası - {str(e)}")
    
    def on_macro_select(self, event):
        try:
            # Seçilen indeksi al
            selected_indices = self.macro_listbox.curselection()
            if not selected_indices:
                return
            
            index = selected_indices[0]
            if index < 0 or index >= len(self.macros):
                return
            
            # Seçilen makroyu yükle
            self.selected_macro_index = index
            macro_data = self.macros[index]
            
            # Arayüzü güncelle
            self.current_macro_name.set(macro_data["name"])
            self.macro_events = macro_data["events"]
            self.macro_repeat_count.set(macro_data.get("repeat_count", 1))
            self.macro_repeat_infinite.set(macro_data.get("repeat_infinite", False))
            self.macro_play_speed.set(macro_data.get("speed", 1.0))
            self.macro_random_delay.set(macro_data.get("random_delay", False))
            self.macro_random_min.set(macro_data.get("random_min", 0.9))
            self.macro_random_max.set(macro_data.get("random_max", 1.1))
            
            # Durum güncelle
            self.macro_status.configure(text=f"Durum: '{macro_data['name']}' makrosu yüklendi - {len(self.macro_events)} olay")
        except Exception as e:
            self.macro_status.configure(text=f"Durum: Makro yükleme hatası - {str(e)}")
    
    def update_macro_list(self):
        # Listeyi temizle
        self.macro_listbox.delete(0, tk.END)
        
        # Makroları ekle
        for macro in self.macros:
            name = macro["name"]
            events_count = len(macro["events"])
            self.macro_listbox.insert(tk.END, f"{name} ({events_count} olay)")
    
    def save_settings(self):
        settings = {
            "interval": self.click_interval.get(),
            "button": self.click_button.get(),
            "infinite": self.infinite_clicks.get(),
            "max_clicks": self.max_clicks.get(),
            "start_hotkey": self.start_hotkey.get(),
            "stop_hotkey": self.stop_hotkey.get(),
            "click_pattern": self.click_pattern.get(),
            "random_min": self.random_min.get(),
            "random_max": self.random_max.get(),
            "multiple_positions": self.multiple_positions.get(),
            "theme": self.theme_var.get(),
            "color_theme": self.color_var.get(),
            "transparency": self.transparency_var.get(),
            "enable_time_stop": self.enable_time_stop.get(),
            "stop_after_mins": self.stop_after_mins.get(),
            "anti_afk_interval": self.anti_afk_interval.get(),
            "anti_afk_keys": self.anti_afk_keys.get(),
            "anti_afk_movement": self.anti_afk_movement.get(),
            "anti_afk_jump": self.anti_afk_jump.get(),
            "anti_afk_rotate": self.anti_afk_rotate.get(),
            # Ekran tanıma ayarları
            "color_tolerance": self.threshold.get(),
            "detection_interval": self.check_interval.get(),
            "target_color": self.color_to_detect.get(),
            "macro_list": self.macros
        }
        
        try:
            # Gizli klasöre kaydet
            cache_file = self.get_cache_path()
            with open(cache_file, "wb") as f:
                pickle.dump(settings, f)
            # Konsola mesaj yazdırma kaldırıldı - daha gizli olması için
        except Exception as e:
            # Konsola hata mesajı yazdırma kaldırıldı
            pass
    
    def load_settings(self):
        try:
            # Gizli klasörden yükle
            cache_file = self.get_cache_path()
            
            if os.path.exists(cache_file):
                with open(cache_file, "rb") as f:
                    settings = pickle.load(f)
                    
                    self.click_interval.set(settings.get("interval", 1.0))
                    self.click_button.set(settings.get("button", "sol"))
                    self.infinite_clicks.set(settings.get("infinite", True))
                    self.max_clicks.set(settings.get("max_clicks", 100))
                    self.start_hotkey.set(settings.get("start_hotkey", "F6"))
                    self.stop_hotkey.set(settings.get("stop_hotkey", "F7"))
                    self.click_pattern.set(settings.get("click_pattern", "sabit"))
                    self.random_min.set(settings.get("random_min", 0.5))
                    self.random_max.set(settings.get("random_max", 1.5))
                    self.multiple_positions.set(settings.get("multiple_positions", False))
                    self.theme_var.set(settings.get("theme", "System"))
                    self.color_var.set(settings.get("color_theme", "blue"))
                    self.transparency_var.set(settings.get("transparency", 1.0))
                    self.enable_time_stop.set(settings.get("enable_time_stop", False))
                    self.stop_after_mins.set(settings.get("stop_after_mins", 30))
                    self.anti_afk_interval.set(settings.get("anti_afk_interval", 30.0))
                    self.anti_afk_keys.set(settings.get("anti_afk_keys", "w,a,s,d,space"))
                    self.anti_afk_movement.set(settings.get("anti_afk_movement", True))
                    self.anti_afk_jump.set(settings.get("anti_afk_jump", True))
                    self.anti_afk_rotate.set(settings.get("anti_afk_rotate", True))
                    # Ekran tanıma ayarları
                    self.threshold.set(settings.get("color_tolerance", 50))
                    self.check_interval.set(settings.get("detection_interval", 1.0))
                    if "target_color" in settings:
                        color_value = settings.get("target_color")
                        # Eğer renk RGB tuple formatında ise hex'e çevir
                        if isinstance(color_value, tuple):
                            try:
                                r, g, b = color_value
                                color_value = f"#{r:02x}{g:02x}{b:02x}"
                            except:
                                color_value = "#FF0000"  # Hata durumunda varsayılan kırmızı
                        self.color_to_detect.set(color_value)
                        self.color_preview.configure(fg_color=self.rgb_to_hex(color_value))
                    
                    # Tema ayarlarını uygula
                    ctk.set_appearance_mode(self.theme_var.get())
                    ctk.set_default_color_theme(self.color_var.get())
                    self.attributes("-alpha", self.transparency_var.get())
                    
                    # Makro ayarları
                    if "macro_list" in settings:
                        self.macros = settings["macro_list"]
                        self.update_macro_list()
                        
                    # Konsola mesaj yazdırma kaldırıldı
        except Exception as e:
            # Konsola hata mesajı yazdırma kaldırıldı
            pass
            # Hata durumunda varsayılan değerleri kullan - zaten __init__ içinde tanımlanmış
    
    def on_close(self):
        self.save_settings()
        self.running = False
        self.anti_afk_running = False
        self.screen_detection_running = False
        self.recording_macro = False
        
        if self.key_listener:
            self.key_listener.stop()
        
        if self.macro_keyboard_listener:
            self.macro_keyboard_listener.stop()
        
        if self.record_listener:
            self.record_listener.stop()
        
        self.destroy()

    def rgb_to_hex(self, rgb):
        # RGB renk değerini hex string'e dönüştürme
        if isinstance(rgb, str):
            return rgb  # Zaten hex ise
        r, g, b = rgb
        return cached_rgb_to_hex(r, g, b)

    def hex_to_rgb(self, hex_color):
        # Hex renk değerini RGB'ye dönüştürme
        return cached_hex_to_rgb(hex_color)

    def capture_screen_region(self):
        if self.region_capture_active:
            self.region_capture_active = False
            self.region_button.configure(text="Bölge Seç")
            self.detection_status.configure(text="Durum: Bölge seçimi iptal edildi")
            return
        
        self.region_capture_active = True
        self.region_button.configure(text="İptal")
        
        self.detection_status.configure(text="Durum: Sol üst köşeye tıklayın, sonra sağ alt köşeye tıklayın")
        self.region_start = None
        self.region_end = None
        
        # Fare tıklamalarını dinlemeye başla
        def on_click(x, y, button, pressed):
            try:
                if not pressed or not self.region_capture_active or button != Button.left:
                    return True
                
                if self.region_start is None:
                    # İlk tıklama - başlangıç noktası
                    self.region_start = (x, y)
                    self.after(100, lambda: self.detection_status.configure(text=f"Durum: Başlangıç ({x},{y}) seçildi. Şimdi bitiş noktasına tıklayın"))
                else:
                    # İkinci tıklama - bitiş noktası
                    self.region_end = (x, y)
                    
                    # Bölgeyi normalleştir (sol üst köşe ve sağ alt köşe)
                    x1, y1 = self.region_start
                    x2, y2 = self.region_end
                    
                    self.region_coords = (
                        min(x1, x2),
                        min(y1, y2),
                        max(x1, x2),
                        max(y1, y2)
                    )
                    
                    # Ekranı yakala ve önizleme göster - ayrı thread'de yap
                    threading.Thread(target=self.update_preview, daemon=True).start()
                    
                    # Bilgi metni güncelle
                    try:
                        if self.region_coords:
                            x, y, w, h = self.region_coords[0], self.region_coords[1], self.region_coords[2] - self.region_coords[0], self.region_coords[3] - self.region_coords[1]
                            self.region_info.configure(text=f"{w}x{h} px @ ({x},{y})")
                            
                            # Durum güncelle - güvenli lambda kullanımı
                            coords = self.region_coords  # Yerel değişkene kopyala
                            self.after(100, lambda: self.detection_status.configure(
                                text=f"Durum: Bölge seçildi ({coords[0]},{coords[1]}) - ({coords[2]},{coords[3]})"
                                if coords else "Durum: Bölge seçimi tamamlandı"
                            ))
                    except Exception as e:
                        self.detection_status.configure(text=f"Durum: Koordinatları okurken hata - {str(e)}")
                    
                    # İşlem tamamlandı
                    self.region_capture_active = False
                    self.region_button.configure(text="Bölge Seç")
                    self.region_start = None
                    self.region_end = None
                    
                    # Dinleyiciyi durdur
                    listener.stop()
                    return False
            except Exception as e:
                self.detection_status.configure(text=f"Durum: Hata - {str(e)}")
                self.region_capture_active = False
                self.region_button.configure(text="Bölge Seç")
                listener.stop()
                return False
                
            return True
        
        listener = MouseListener(on_click=on_click)
        listener.start()

    def update_preview(self):
        if not self.region_coords:
            return
        
        try:
            # Ekran görüntüsü al
            screenshot = ImageGrab.grab(bbox=self.region_coords)
            
            # Boyutu düzenle - daha küçük boyut için maksimum boyutu azalttım
            max_size = 250
            width, height = screenshot.size
            
            # En-boy oranını koru
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            # Daha hızlı olan BILINEAR kullan
            resized = screenshot.resize((new_width, new_height), Image.BILINEAR)
            
            # CTkImage'a dönüştür
            ctk_image = ctk.CTkImage(light_image=resized, dark_image=resized, size=(new_width, new_height))
            
            # Önizleme etiketini ana thread üzerinde güncelle
            self.after(10, lambda: self.preview_label.configure(image=ctk_image, text=""))
            self.preview_image = ctk_image  # Referansı sakla
        except Exception as e:
            self.after(10, lambda: self.preview_label.configure(text=f"Önizleme hatası: {str(e)}", image=None))

    def pick_color(self):
        if not self.region_coords:
            self.detection_status.configure(text="Uyarı: Önce bir ekran bölgesi seçmelisiniz!")
            return
        
        self.detection_status.configure(text="Durum: Bölgede istediğiniz renge tıklayın")
        
        def on_click(x, y, button, pressed):
            if not pressed or button != Button.left:
                return True
            
            # Seçilen renk bölge içinde mi kontrol et
            x1, y1, x2, y2 = self.region_coords
            if x1 <= x <= x2 and y1 <= y <= y2:
                try:
                    # Tıklanan pikselin rengini al
                    screenshot = ImageGrab.grab(bbox=(x, y, x+1, y+1))
                    pixel_color = screenshot.getpixel((0, 0))  # RGB renk
                    
                    # Hedef rengi ayarla
                    self.color_to_detect.set(pixel_color)
                    
                    # Renk önizlemesini güncelle
                    self.after(10, lambda: self.color_preview.configure(fg_color=self.rgb_to_hex(pixel_color)))
                    
                    # Mesaj kutusu yerine durum güncellemesi
                    self.after(10, lambda: self.detection_status.configure(text=f"Durum: Renk seçildi - RGB: {pixel_color}"))
                    
                    listener.stop()
                    return False
                except Exception as e:
                    self.after(10, lambda: self.detection_status.configure(text=f"Hata: {str(e)}"))
            
            return True
        
        listener = MouseListener(on_click=on_click)
        listener.start()

    def start_screen_detection(self):
        if self.screen_detection_running:
            return
        
        if not self.region_coords:
            messagebox.showwarning("Uyarı", "Önce bir ekran bölgesi seçmelisiniz!")
            return
        
        self.screen_detection_running = True
        self.detect_start_button.configure(state="disabled")
        self.detect_stop_button.configure(state="normal")
        self.detection_status.configure(text="Durum: Taranıyor...")
        
        # Ekran tanıma thread'ini başlat
        self.detection_thread = threading.Thread(target=self.screen_detection_task)
        self.detection_thread.daemon = True
        self.detection_thread.start()

    def stop_screen_detection(self):
        self.screen_detection_running = False
        self.detect_start_button.configure(state="normal")
        self.detect_stop_button.configure(state="disabled")
        self.detection_status.configure(text="Durum: Hazır")

    def screen_detection_task(self):
        try:
            target_color = self.color_to_detect.get()
            if isinstance(target_color, str):
                target_r, target_g, target_b = self.hex_to_rgb(target_color)
            else:
                target_r, target_g, target_b = target_color
            
            # Hesaplamaları hızlandırmak için değerleri önceden hazırla
            tolerance = self.threshold.get()
            check_interval = self.check_interval.get()
            region = self.region_coords
            
            while self.screen_detection_running:
                try:
                    # Ekran bölgesini yakala
                    screenshot = ImageGrab.grab(bbox=region)
                    img_np = np.array(screenshot)
                    
                    # Performans için: RGB yerine BGR mi kontrol et
                    if len(img_np.shape) == 3 and img_np.shape[2] == 3:
                        # BGR->RGB dönüşümü gerekmiyorsa atla
                        img_rgb = img_np
                    
                    # Renk toleransına göre maske oluştur - NumPy vektörizasyonu kullan
                    lower_bound = np.array([max(0, target_r - tolerance), max(0, target_g - tolerance), max(0, target_b - tolerance)])
                    upper_bound = np.array([min(255, target_r + tolerance), min(255, target_g + tolerance), min(255, target_b + tolerance)])
                    
                    # Boolean maske oluştur
                    mask = np.logical_and(
                        np.logical_and(
                            img_rgb[:,:,0] >= lower_bound[0],
                            img_rgb[:,:,0] <= upper_bound[0]
                        ),
                        np.logical_and(
                            np.logical_and(
                                img_rgb[:,:,1] >= lower_bound[1],
                                img_rgb[:,:,1] <= upper_bound[1]
                            ),
                            np.logical_and(
                                img_rgb[:,:,2] >= lower_bound[2],
                                img_rgb[:,:,2] <= upper_bound[2]
                            )
                        )
                    )
                    
                    # NumPy'ı kullanarak maskeyi integer'a dönüştür
                    binary_mask = mask.astype(np.uint8) * 255
                    
                    # Sonuçları göster
                    self.update_detection_preview(binary_mask)
                    
                    # Eşleşme var mı kontrol et
                    if np.any(mask):
                        # İlk eşleşen pikseli bul
                        y_indices, x_indices = np.where(mask)
                        if len(y_indices) > 0:
                            # Orta noktayı hedefle
                            y_center_idx = len(y_indices) // 2
                            x_center_original = x_indices[y_center_idx]
                            y_center_original = y_indices[y_center_idx]
                            
                            # Fare konumunu güncelle ve tıkla
                            x_abs = region[0] + x_center_original
                            y_abs = region[1] + y_center_original
                            
                            # Durum güncelle
                            self.after(10, lambda: self.detection_status.configure(text=f"Durum: Eşleşme bulundu! ({x_abs}, {y_abs})"))
                            
                            # Otomatik tıklama aktifse tıkla
                            if self.auto_click_when_detect.get():
                                self.mouse.position = (x_abs, y_abs)
                                self.mouse.click(Button.left)
                                
                                # Tıklama gecikmesi
                                time.sleep(self.auto_click_delay.get())
                        else:
                            self.after(10, lambda: self.detection_status.configure(text="Durum: Eşleşme bulunamadı"))
                    else:
                        self.after(10, lambda: self.detection_status.configure(text="Durum: Eşleşme bulunamadı"))
                    
                    # Belirlenen aralıkla tara
                    time.sleep(check_interval)
                    
                except Exception as e:
                    print(f"Ekran algılama hatası: {str(e)}")
                    time.sleep(1)
        except Exception as e:
            print(f"Algılama başlatma hatası: {str(e)}")

    def update_detection_preview(self, mask):
        try:
            # Maske görüntüsünü PIL formatına dönüştür
            mask_image = Image.fromarray(mask)
            
            # Boyutu düzenle - daha küçük önizleme
            max_size = 200
            width, height = mask_image.size
            
            # En-boy oranını koru
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            # Daha hızlı yeniden boyutlandırma
            resized = mask_image.resize((new_width, new_height), Image.NEAREST)
            
            # CTkImage'a dönüştür
            ctk_image = ctk.CTkImage(light_image=resized, dark_image=resized, size=(new_width, new_height))
            
            # Önizleme etiketini ana thread üzerinde güncelle
            self.after(10, lambda: self.preview_label.configure(image=ctk_image, text=""))
            self.preview_image = ctk_image  # Referansı sakla
        except Exception as e:
            print(f"Önizleme güncelleme hatası: {str(e)}")

    def setup_appearance_tab(self):
        tab = self.tabview.tab("Görünüm")
        tab.grid_columnconfigure(0, weight=1)
        
        # Tema seçimi
        theme_frame = ctk.CTkFrame(tab)
        theme_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        theme_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(theme_frame, text="Uygulama Teması", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        # Tema seçenekleri
        theme_options = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_options.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        
        themes = [("Sistem", "System"), ("Açık", "Light"), ("Koyu", "Dark")]
        self.theme_var = ctk.StringVar(value="System")
        
        for i, (text, value) in enumerate(themes):
            ctk.CTkRadioButton(
                theme_options, 
                text=text, 
                variable=self.theme_var,
                value=value,
                command=self.change_theme
            ).grid(row=0, column=i, padx=15, pady=5)
        
        # Renk seçimi
        color_frame = ctk.CTkFrame(tab)
        color_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        color_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(color_frame, text="Renk Teması", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        # Renk seçenekleri
        color_options = ctk.CTkFrame(color_frame, fg_color="transparent")
        color_options.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        
        colors = [("Mavi", "blue"), ("Yeşil", "green"), ("Koyu Mavi", "dark-blue")]
        self.color_var = ctk.StringVar(value="blue")
        
        for i, (text, value) in enumerate(colors):
            ctk.CTkRadioButton(
                color_options, 
                text=text, 
                variable=self.color_var,
                value=value,
                command=self.change_color_theme
            ).grid(row=0, column=i, padx=15, pady=5)
        
        # Şeffaflık ayarı
        transparency_frame = ctk.CTkFrame(tab)
        transparency_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        transparency_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(transparency_frame, text="Pencere Şeffaflığı", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        self.transparency_var = ctk.DoubleVar(value=1.0)
        ctk.CTkSlider(
            transparency_frame, 
            from_=0.5, 
            to=1.0, 
            variable=self.transparency_var,
            command=self.change_transparency
        ).grid(row=1, column=0, padx=15, pady=10, sticky="ew")

    def change_theme(self):
        ctk.set_appearance_mode(self.theme_var.get())

    def change_color_theme(self):
        ctk.set_default_color_theme(self.color_var.get())
        messagebox.showinfo("Bilgi", "Renk teması değişikliği tam olarak uygulanması için uygulamayı yeniden başlatmanız gerekebilir.")

    def change_transparency(self, value=None):
        self.attributes("-alpha", self.transparency_var.get())

    def setup_keyboard_listener(self):
        # Eğer varsa mevcut dinleyiciyi durdur
        if self.macro_keyboard_listener:
            self.macro_keyboard_listener.stop()
        
        # F tuşlarını dinleme fonksiyonu
        def on_press(key):
            try:
                # Tuş adını alıp F tuşlarını kontrol et
                key_name = key.name if hasattr(key, 'name') else key.char if hasattr(key, 'char') else str(key)
                
                # F tuşu için string formatları
                if hasattr(key, 'name') and key.name.startswith('f'):
                    f_key = f"F{key.name[1:]}"  # f1 -> F1
                    
                    if f_key == self.start_hotkey.get() and not self.running:
                        self.start_clicking()
                        return True
                    elif f_key == self.stop_hotkey.get() and self.running:
                        self.stop_clicking()
                        return True
            except Exception as e:
                print(f"Tuş işlenirken hata: {str(e)}")
            return True
        
        # Klavye dinleyicisini başlat
        self.macro_keyboard_listener = KeyboardListener(on_press=on_press)
        self.macro_keyboard_listener.daemon = True
        self.macro_keyboard_listener.start()
        
        # Durum çubuğunu güncelle
        self.status_label.configure(text=f"Hazır | Başlatmak için {self.start_hotkey.get()} tuşuna basın")

    def start_position_updater(self):
        def update_position():
            if not self.running:
                try:
                    x, y = self.mouse.position
                    self.current_position = (x, y)
                    self.pos_label.configure(text=f"X: {x}, Y: {y}")
                except:
                    pass
            self.after(100, update_position)
        
        update_position()

    def toggle_clicking(self):
        if not self.running:
            self.start_clicking()
        else:
            self.stop_clicking()

    def start_clicking(self):
        if self.running:
            return
        
        # Kısayol tuşları değişmişse güncelle
        self.setup_keyboard_listener()
        
        self.running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text=f"Çalışıyor | Durdurmak için {self.stop_hotkey.get()} tuşuna basın")
        
        self.clicks_count.set(0)
        self.click_thread = threading.Thread(target=self.clicking_task)
        self.click_thread.daemon = True
        self.click_thread.start()
        
        # Otomatik durdurma zamanlayıcısı
        if self.enable_time_stop.get() and self.stop_after_mins.get() > 0:
            mins = self.stop_after_mins.get()
            self.after(mins * 60 * 1000, self.check_auto_stop)

    def check_auto_stop(self):
        if self.enable_time_stop.get() and self.running:
            self.stop_clicking()
            messagebox.showinfo("Bilgi", f"Otomatik tıklama {self.stop_after_mins.get()} dakika sonra durduruldu.")

    def stop_clicking(self):
        self.running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_label.configure(text=f"Hazır | Başlatmak için {self.start_hotkey.get()} tuşuna basın")

    def clicking_task(self):
        total_clicks = 0
        max_clicks = 0 if self.infinite_clicks.get() else self.max_clicks.get()
        
        while self.running:
            try:
                # Maksimum tıklama sayısı kontrolü
                if not self.infinite_clicks.get() and total_clicks >= max_clicks:
                    self.after(0, self.stop_clicking)
                    break
                
                # Çoklu konum kullanımı
                if self.multiple_positions.get() and self.click_positions:
                    for pos_x, pos_y in self.click_positions:
                        if not self.running:
                            break
                        
                        # Fareyi konuma taşı
                        self.mouse.position = (pos_x, pos_y)
                        time.sleep(0.1)  # Konum değişikliği için kısa bekleme
                        
                        # Tıklama işlemi
                        self.perform_click()
                        
                        total_clicks += 1
                        self.clicks_count.set(total_clicks)
                        
                        # Bekleme süresi
                        self.wait_between_clicks()
                        
                        # Maksimum tıklama kontrolü
                        if not self.infinite_clicks.get() and total_clicks >= max_clicks:
                            self.after(0, self.stop_clicking)
                            break
                else:
                    # Tek konum tıklama
                    self.perform_click()
                    
                    total_clicks += 1
                    self.clicks_count.set(total_clicks)
                    
                    # Bekleme süresi
                    self.wait_between_clicks()
            except Exception as e:
                print(f"Tıklama hatası: {str(e)}")
                time.sleep(1)  # Hata durumunda kısa bekleme

    def perform_click(self):
        try:
            if self.click_button.get() == "sol":
                self.mouse.click(Button.left)
            elif self.click_button.get() == "sag":
                self.mouse.click(Button.right)
            else:  # orta
                self.mouse.click(Button.middle)
        except Exception as e:
            print(f"Tıklama hatası: {str(e)}")

    def wait_between_clicks(self):
        if self.click_pattern.get() == "rastgele":
            # Rastgele bekleme süresi
            min_delay = self.random_min.get()
            max_delay = self.random_max.get()
            delay = min_delay + (max_delay - min_delay) * random.random()
            time.sleep(max(0.01, delay))
        else:
            # Sabit bekleme süresi
            time.sleep(max(0.01, self.click_interval.get()))

    def start_recording(self):
        if self.recording:
            self.stop_recording()
            return
        
        self.recording = True
        self.record_button.configure(text="Kaydetmeyi Durdur", fg_color="#C42B1C")
        self.click_positions = []
        self.position_list.delete(0, tk.END)
        
        # Dinleyici başlat
        def on_click(x, y, button, pressed):
            if pressed and button == Button.left:
                self.click_positions.append((x, y))
                self.position_list.insert(tk.END, f"Konum {len(self.click_positions)}: X={x}, Y={y}")
        
        self.record_listener = MouseListener(on_click=on_click)
        self.record_listener.start()
        
        messagebox.showinfo("Kayıt", "Konum kaydetme başladı. Kaydetmek istediğiniz yerlere SOL tıklayın. Tamamlandığında 'Kaydetmeyi Durdur' butonuna basın.")

    def stop_recording(self):
        self.recording = False
        self.record_button.configure(text="Konumları Kaydet", fg_color="#0063B1")
        
        if self.record_listener:
            self.record_listener.stop()
            self.record_listener = None
        
        if self.click_positions:
            messagebox.showinfo("Kayıt", f"{len(self.click_positions)} konum başarıyla kaydedildi.")
        else:
            messagebox.showwarning("Kayıt", "Hiç konum kaydedilmedi.")

    def clear_positions(self):
        self.click_positions = []
        self.position_list.delete(0, tk.END)

    def start_anti_afk(self):
        if self.anti_afk_running:
            return
        
        self.anti_afk_running = True
        self.afk_start_button.configure(state="disabled")
        self.afk_stop_button.configure(state="normal")
        self.anti_afk_status.configure(text="Durum: Çalışıyor - Anti-AFK aktif")
        
        # Anti-AFK thread'ini başlat
        self.anti_afk_thread = threading.Thread(target=self.anti_afk_task)
        self.anti_afk_thread.daemon = True
        self.anti_afk_thread.start()
        
        messagebox.showinfo("Anti-AFK", "Roblox Anti-AFK sistemi başlatıldı. Oyun penceresine geçebilirsiniz.")

    def stop_anti_afk(self):
        self.anti_afk_running = False
        self.afk_start_button.configure(state="normal")
        self.afk_stop_button.configure(state="disabled")
        self.anti_afk_status.configure(text="Durum: Hazır")

    def anti_afk_task(self):
        # Anti-AFK döngüsü
        while self.anti_afk_running:
            try:
                if self.anti_afk_movement:
                    self.perform_random_movement()
                
                if self.anti_afk_jump:
                    self.perform_jump()
                
                if self.anti_afk_rotate:
                    self.perform_camera_rotation()
                
                # Özel tuşlara basma
                self.press_custom_keys()
                
                # Bekleme süresi
                time.sleep(self.anti_afk_interval.get())
            
            except Exception as e:
                print(f"Anti-AFK hatası: {str(e)}")
                time.sleep(5)  # Hata durumunda kısa bekleme

    def perform_random_movement(self):
        # Rastgele yön tuşlarından birine basma (WASD)
        movement_keys = ['w', 'a', 's', 'd']
        key = random.choice(movement_keys)
        
        # Tuşa basılı tutma süresi (0.2-1 saniye arası)
        press_duration = random.uniform(0.2, 1.0)
        
        # Tuşa bas
        self.keyboard_controller.press(key)
        time.sleep(press_duration)
        self.keyboard_controller.release(key)

    def perform_jump(self):
        # %30 ihtimalle zıplama
        if random.random() < 0.3:
            # Space tuşuna bas
            self.keyboard_controller.press(' ')
            time.sleep(0.1)
            self.keyboard_controller.release(' ')

    def perform_camera_rotation(self):
        # Fareyi rastgele hareket ettirerek kamerayı döndürme
        x_offset = random.randint(-100, 100)
        y_offset = random.randint(-50, 50)
        
        # Mevcut fare pozisyonunu al
        current_x, current_y = self.mouse.position
        
        # Fareyi hareket ettir
        self.mouse.position = (current_x + x_offset, current_y + y_offset)
        time.sleep(0.2)
        
        # Fareyi orijinal pozisyona geri getir
        self.mouse.position = (current_x, current_y)

    def press_custom_keys(self):
        # Kullanıcı tarafından belirtilen özel tuşlara basma
        if not self.anti_afk_keys.get().strip():
            return
        
        # Tuşları virgülle ayırma
        keys = self.anti_afk_keys.get().split(',')
        
        # Rastgele bir tuş seç
        if keys:
            key = random.choice(keys).strip().lower()
            
            # Özel tuş kontrolü
            if key == "space":
                key = ' '
            elif key == "shift":
                key = keyboard.Key.shift
            elif key == "ctrl":
                key = keyboard.Key.ctrl
            elif key == "alt":
                key = keyboard.Key.alt
            
            # Tuşa bas
            try:
                self.keyboard_controller.press(key)
                time.sleep(0.1)
                self.keyboard_controller.release(key)
            except Exception as e:
                print(f"Özel tuş basma hatası: {str(e)}")

    # Cache dosya yolu alma fonksiyonu - gizli klasör kullanır
    def get_cache_path(self):
        # Windows için AppData klasörünü kullan
        if os.name == 'nt':
            app_data = os.path.join(os.environ['APPDATA'], '.zers_clicker')
        # Linux/Mac için home klasörünü kullan
        else:
            app_data = os.path.join(os.path.expanduser('~'), '.zers_clicker')
            
        # Klasör yoksa oluştur
        if not os.path.exists(app_data):
            os.makedirs(app_data)
            
        # Dosya yolunu döndür - gizli bir isim kullan
        return os.path.join(app_data, ".z_data.bin")

if __name__ == "__main__":
    try:
        app = ProOtomatikTiklayici()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Hata", f"Uygulama başlatılırken bir hata oluştu: {str(e)}") 