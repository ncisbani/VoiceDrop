import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import os
import config
from audio_recorder import AudioRecorder

class SettingsWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="VoiceDrop - Settings")
        self.set_default_size(420, 500)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)
        
        # Enable dark theme preference
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)
        
        self.config_data = config.load_config()
        self.recorder = None
        self.is_testing_mic = False
        self.test_timer_id = None
        
        # Apply CSS style for modern look
        self.apply_css()
        
        # Main layout container
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_vbox)
        
        # Header / Title Bar Area
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header_box.set_name("header-box")
        header_box.set_margin_top(20)
        header_box.set_margin_bottom(15)
        
        title_label = Gtk.Label()
        title_label.set_markup("<span font_desc='Outfit 18' weight='bold' color='#38BDF8'>VoiceDrop</span>")
        header_box.pack_start(title_label, False, False, 0)
        
        subtitle_label = Gtk.Label()
        subtitle_label.set_markup("<span font_desc='10' color='#9CA3AF'>Minimal local speech-to-text dictation</span>")
        header_box.pack_start(subtitle_label, False, False, 0)
        
        main_vbox.pack_start(header_box, False, False, 0)
        
        # Settings Content Frame
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        content_box.set_margin_bottom(20)
        main_vbox.pack_start(content_box, True, True, 0)
        
        # --- Section 1: Dictation Settings ---
        section1_label = Gtk.Label()
        section1_label.set_markup("<span font_desc='10' weight='bold' color='#F3F4F6'>DICTATION SETTINGS</span>")
        section1_label.set_xalign(0.0)
        content_box.pack_start(section1_label, False, False, 0)
        
        grid1 = Gtk.Grid(row_spacing=12, column_spacing=12)
        content_box.pack_start(grid1, False, False, 0)
        
        # Language Selector
        lang_label = Gtk.Label(label="Language:")
        lang_label.set_xalign(0.0)
        self.lang_combo = Gtk.ComboBoxText()
        languages = [("en", "English"), ("it", "Italian"), ("es", "Spanish"), ("fr", "French"), ("de", "German")]
        for code, name in languages:
            self.lang_combo.append(code, name)
        self.lang_combo.set_active_id(self.config_data.get("language", "en"))
        
        grid1.attach(lang_label, 0, 0, 1, 1)
        grid1.attach_next_to(self.lang_combo, lang_label, Gtk.PositionType.RIGHT, 1, 1)
        self.lang_combo.set_hexpand(True)
        
        # Smart Correction Toggle (LLM)
        llm_label = Gtk.Label(label="AI Grammar Correction:")
        llm_label.set_xalign(0.0)
        self.llm_switch = Gtk.Switch()
        self.llm_switch.set_active(self.config_data.get("llm_correction", True))
        self.llm_switch.set_halign(Gtk.Align.END)
        
        grid1.attach(llm_label, 0, 1, 1, 1)
        grid1.attach_next_to(self.llm_switch, llm_label, Gtk.PositionType.RIGHT, 1, 1)
        
        # Auto-Paste Toggle (evdev)
        paste_label = Gtk.Label(label="Auto-Paste Text:")
        paste_label.set_xalign(0.0)
        self.paste_switch = Gtk.Switch()
        self.paste_switch.set_active(self.config_data.get("auto_paste", True))
        self.paste_switch.set_halign(Gtk.Align.END)
        
        grid1.attach(paste_label, 0, 2, 1, 1)
        grid1.attach_next_to(self.paste_switch, paste_label, Gtk.PositionType.RIGHT, 1, 1)
        
        # --- Section 2: Diagnostics & Setup ---
        section2_label = Gtk.Label()
        section2_label.set_markup("<span font_desc='10' weight='bold' color='#F3F4F6'>DIAGNOSTICS &amp; SETUP</span>")
        section2_label.set_xalign(0.0)
        section2_label.set_margin_top(10)
        content_box.pack_start(section2_label, False, False, 0)
        
        # Test Microphone
        mic_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.test_mic_btn = Gtk.Button(label="Test Microphone")
        self.test_mic_btn.connect("clicked", self.toggle_mic_test)
        self.test_mic_btn.set_name("test-btn")
        self.mic_level_bar = Gtk.LevelBar()
        self.mic_level_bar.set_min_value(0.0)
        self.mic_level_bar.set_max_value(1.0)
        self.mic_level_bar.set_hexpand(True)
        self.mic_level_bar.set_valign(Gtk.Align.CENTER)
        
        mic_box.pack_start(self.test_mic_btn, False, False, 0)
        mic_box.pack_start(self.mic_level_bar, True, True, 0)
        content_box.pack_start(mic_box, False, False, 0)
        
        # GNOME Shortcut Guide
        shortcut_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        shortcut_box.set_name("guide-box")
        shortcut_box.set_margin_top(4)
        
        guide_title = Gtk.Label()
        guide_title.set_markup("<span font_desc='9' weight='bold' color='#F3F4F6'>How to bind a shortcut in GNOME:</span>")
        guide_title.set_xalign(0.0)
        
        guide_text = Gtk.Label()
        guide_text.set_markup(
            "<span font_desc='9' color='#9CA3AF'>"
            "1. Open <b>Settings</b> → <b>Keyboard</b> → <b>Keyboard Shortcuts</b>.\n"
            "2. Scroll down and click <b>Custom Shortcuts</b> → <b>+</b>.\n"
            "3. Name it: <span color='#38BDF8'>VoiceDrop</span>\n"
            "4. Command: <span color='#10B981'>/usr/bin/python3 /home/ncisbani/Documents/varie/VoiceDrop/main.py --toggle</span>\n"
            "5. Set shortcut to e.g. <span color='#A78BFA'>Super+Space</span> or <span color='#A78BFA'>Alt+S</span>."
            "</span>"
        )
        guide_text.set_xalign(0.0)
        
        shortcut_box.pack_start(guide_title, False, False, 0)
        shortcut_box.pack_start(guide_text, False, False, 0)
        content_box.pack_start(shortcut_box, False, False, 0)
        
        # --- Bottom Buttons ---
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        buttons_box.set_margin_top(10)
        
        self.save_btn = Gtk.Button(label="Save Settings")
        self.save_btn.connect("clicked", self.on_save)
        self.save_btn.set_name("save-btn")
        self.save_btn.set_hexpand(True)
        
        self.cancel_btn = Gtk.Button(label="Close")
        self.cancel_btn.connect("clicked", lambda w: self.close_window())
        self.cancel_btn.set_name("cancel-btn")
        
        buttons_box.pack_start(self.cancel_btn, False, False, 0)
        buttons_box.pack_start(self.save_btn, True, True, 0)
        content_box.pack_start(buttons_box, False, False, 0)
        
        self.connect("destroy", lambda w: self.close_window())
        self.show_all()

    def apply_css(self):
        css_provider = Gtk.CssProvider()
        css = b"""
        window {
            background-color: #111827;
        }
        #header-box {
            border-bottom: 1px solid #1F2937;
        }
        grid {
            background-color: #1F2937;
            border-radius: 8px;
            padding: 12px;
        }
        label {
            color: #E5E7EB;
            font-family: 'Inter', 'Sans', sans-serif;
            font-size: 13px;
        }
        combobox, entry {
            background-color: #374151;
            border: 1px solid #4B5563;
            color: #F9FAFB;
            border-radius: 4px;
            padding: 4px;
        }
        #guide-box {
            background-color: #1F2937;
            border-radius: 8px;
            padding: 12px;
            border: 1px solid #374151;
        }
        #test-btn {
            background-color: #374151;
            color: #F3F4F6;
            border: 1px solid #4B5563;
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: bold;
        }
        #test-btn:hover {
            background-color: #4B5563;
        }
        #save-btn {
            background-color: #0284C7;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        #save-btn:hover {
            background-color: #0369A1;
        }
        #cancel-btn {
            background-color: #374151;
            color: #D1D5DB;
            border: 1px solid #4B5563;
            border-radius: 6px;
            padding: 8px 16px;
        }
        #cancel-btn:hover {
            background-color: #4B5563;
        }
        """
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def toggle_mic_test(self, button):
        if not self.is_testing_mic:
            # Start mic test
            try:
                self.recorder = AudioRecorder(device_index=self.config_data.get("audio_device_index"))
                self.recorder.start()
                self.is_testing_mic = True
                button.set_label("Stop Test")
                # Poll microphone levels every 50ms
                self.test_timer_id = GLib.timeout_add(50, self.update_mic_level)
            except Exception as e:
                print(f"Failed to start mic test: {e}")
                self.mic_level_bar.set_value(0.0)
        else:
            # Stop mic test
            self.stop_mic_test()
            button.set_label("Test Microphone")

    def stop_mic_test(self):
        self.is_testing_mic = False
        if self.test_timer_id:
            GLib.source_remove(self.test_timer_id)
            self.test_timer_id = None
        if self.recorder:
            self.recorder.recording = False
            self.recorder.cleanup()
            self.recorder = None
        self.mic_level_bar.set_value(0.0)

    def update_mic_level(self):
        if not self.is_testing_mic or not self.recorder or not self.recorder.frames:
            return True
            
        try:
            # Calculate RMS of last frame
            import numpy as np
            last_frame = self.recorder.frames[-1]
            # Convert bytes to numpy 16-bit integer array
            audio_data = np.frombuffer(last_frame, dtype=np.int16)
            if len(audio_data) > 0:
                # Calculate root-mean-square (RMS) volume
                rms = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
                # Normalize to 0-1 range (voice peak is usually around 5000-8000 for standard mic gain)
                normalized = min(1.0, rms / 6000.0)
                self.mic_level_bar.set_value(normalized)
        except Exception as e:
            print(f"Error updating mic level: {e}")
            
        return True

    def on_save(self, button):
        self.config_data["language"] = self.lang_combo.get_active_id()
        self.config_data["llm_correction"] = self.llm_switch.get_active()
        self.config_data["auto_paste"] = self.paste_switch.get_active()
        
        config.save_config(self.config_data)
        
        # Show quick dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Settings Saved"
        )
        dialog.format_secondary_text("VoiceDrop settings have been saved successfully.")
        dialog.run()
        dialog.destroy()
        self.close_window()

    def close_window(self):
        self.stop_mic_test()
        self.destroy()
        Gtk.main_quit()
