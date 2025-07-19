import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import atexit
import shutil
from pydub import AudioSegment
from pathlib import Path
from parse_book import parse
from generate_audio import *
from chunk import generate_chunks
import simpleaudio

class AudiobookApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window initially
        self.current_gui = None
        self.book_data = None
        self.script_names = {}
        self.show_main_menu()
    
    def show_main_menu(self):
        """Display the main menu GUI"""
        if self.current_gui:
            self.current_gui.destroy()
        
        self.current_gui = MainMenuGUI(self)
    
    def show_audiobook_creation(self):
        """Display the audiobook creation GUI"""
        if self.current_gui:
            self.current_gui.destroy()
        
        self.current_gui = AudiobookCreationGUI(self)
    
    def show_character_labeling(self, book_path):
        """Display the character labeling GUI"""
        if self.current_gui:
            self.current_gui.destroy()
        
        self.current_gui = CharacterLabelingGUI(self, book_path)
    
    def show_processing_gui(self, book_path):
        """Display the TTS processing GUI"""
        if self.current_gui:
            self.current_gui.destroy()
        
        self.current_gui = ProcessingGUI(self, book_path)
    
    def show_voice_editor(self):
        """Display the voice editing GUI"""
        if self.current_gui:
            self.current_gui.destroy()
        
        self.current_gui = VoiceEditorGUI(self)
    
    def show_processing_status(self):
        """Display the processing status GUI"""
        if self.current_gui:
            self.current_gui.destroy()
        
        self.current_gui = ProcessingStatusGUI(self)
    
    def show_export_book(self):
        """Display the export book GUI"""
        if self.current_gui:
            self.current_gui.destroy()
        
        self.current_gui = ExportBookGUI(self)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

class MainMenuGUI:
    def __init__(self, app):
        self.app = app
        self.root = tk.Toplevel(app.root)
        self.root.title("Audiobook Generator")
        self.root.geometry("500x450")  # Increased height for new button
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.minsize(400, 350)
        self.root.lift()
        self.root.focus_force()
        self.root.after(100, lambda: self.root.focus_force())
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.build_ui()
    
    def build_ui(self):
        # Main frame
        mainframe = ttk.Frame(self.root, padding="20")
        mainframe.grid(row=0, column=0, sticky="NSEW")
        mainframe.rowconfigure(1, weight=1)
        mainframe.columnconfigure(0, weight=1)
        
        # Title
        title_frame = ttk.Frame(mainframe)
        title_frame.grid(row=0, column=0, sticky="EW", pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="Audiobook Generation", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0)
        
        # Center the title
        title_frame.columnconfigure(0, weight=1)
        
        # Menu options frame
        menu_frame = ttk.LabelFrame(mainframe, text="Select an Option")
        menu_frame.grid(row=1, column=0, sticky="NSEW", pady=10)
        menu_frame.rowconfigure(0, weight=1)
        menu_frame.columnconfigure(0, weight=1)
        
        # Button container for centering
        button_container = ttk.Frame(menu_frame)
        button_container.grid(row=0, column=0)
        
        # Menu buttons
        button_width = 20
        button_pady = 10
        
        create_btn = ttk.Button(
            button_container, 
            text="Create Audiobook", 
            command=self.app.show_audiobook_creation,
            width=button_width
        )
        create_btn.grid(row=0, column=0, pady=button_pady)
        
        resume_btn = ttk.Button(
            button_container, 
            text="Resume Audiobook", 
            command=self.resume_audiobook,
            width=button_width
        )
        resume_btn.grid(row=1, column=0, pady=button_pady)
        
        voices_btn = ttk.Button(
            button_container, 
            text="Edit Voices", 
            command=self.app.show_voice_editor,
            width=button_width
        )
        voices_btn.grid(row=2, column=0, pady=button_pady)
        
        # NEW: Export button
        export_btn = ttk.Button(
            button_container, 
            text="Export Audiobook", 
            command=self.app.show_export_book,
            width=button_width
        )
        export_btn.grid(row=3, column=0, pady=button_pady)
        
        # Separator
        separator = ttk.Separator(button_container, orient="horizontal")
        separator.grid(row=4, column=0, sticky="EW", pady=20)
        
        # Exit button
        exit_btn = ttk.Button(
            button_container, 
            text="Exit", 
            command=self.on_closing,
            width=button_width
        )
        exit_btn.grid(row=5, column=0, pady=button_pady)
        
        # Status bar
        status_frame = ttk.Frame(mainframe)
        status_frame.grid(row=2, column=0, sticky="EW", pady=(10, 0))
        
        status_label = ttk.Label(status_frame, text="Ready", relief="sunken", anchor="w")
        status_label.grid(row=0, column=0, sticky="EW")
        status_frame.columnconfigure(0, weight=1)
    
    def resume_audiobook(self):
        """Resume an existing audiobook project"""
        project_folder = filedialog.askdirectory(title="Select Audiobook Project Folder", initialdir=Path('books'))
        
        if project_folder:
            self.app.show_processing_gui(project_folder)
        else:
            messagebox.showinfo("Info", "No folder selected")
    
    def on_closing(self):
        """Handle window closing"""
        self.app.root.quit()
    
    def destroy(self):
        """Clean up the window"""
        self.root.destroy()

class AudiobookCreationGUI:
    def __init__(self, app):
        self.app = app
        self.root = tk.Toplevel(app.root)
        self.root.title("Create Audiobook")
        self.root.geometry("700x400")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.minsize(500, 300)
        self.root.lift()
        self.root.focus_force()
        self.root.after(100, lambda: self.root.focus_force())
        
        self.file_path = None
        self.title_var = tk.StringVar()
        self.multi_voice = tk.BooleanVar(value=True)
        self.output_var = tk.StringVar(value="Ready to start...")
        
        self.build_ui()
    
    def build_ui(self):
        mainframe = ttk.Frame(self.root, padding="10")
        mainframe.grid(row=0, column=0, sticky="NSEW")
        
        for i in range(5):
            mainframe.rowconfigure(i, weight=1)
        mainframe.columnconfigure(1, weight=1)
        
        # Project Title
        ttk.Label(mainframe, text="Project Title:").grid(row=0, column=0, sticky="W")
        ttk.Entry(mainframe, textvariable=self.title_var).grid(row=0, column=1, columnspan=2, sticky="EW", pady=5)
        
        # File upload
        ttk.Label(mainframe, text="Import Book:").grid(row=1, column=0, sticky="W")
        self.file_label = ttk.Label(mainframe, text="No file selected")
        self.file_label.grid(row=1, column=1, sticky="W")
        ttk.Button(mainframe, text="Browse", command=self.browse_file).grid(row=1, column=2, sticky="E")
        
        # Multi-voice toggle
        ttk.Checkbutton(mainframe, text="Use Multiple Voices", variable=self.multi_voice).grid(row=2, column=0, columnspan=3, sticky="W", pady=10)
        
        # Status label
        ttk.Label(mainframe, text="Status:").grid(row=3, column=0, sticky="W")
        self.status_label = ttk.Label(mainframe, textvariable=self.output_var, foreground="white")
        self.status_label.grid(row=3, column=1, columnspan=2, sticky="W")
        
        # Button row
        btn_frame = ttk.Frame(mainframe)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10, sticky="EW")
        btn_frame.columnconfigure((0, 1), weight=1)
        
        ttk.Button(btn_frame, text="Back", command=self.app.show_main_menu).grid(row=0, column=0, sticky="W")
        self.cont_btn = ttk.Button(btn_frame, text="Continue", command=self.start_processing)
        self.cont_btn.grid(row=0, column=1, sticky="E")
    
    def browse_file(self):
        """Browse for a book file"""
        filetypes = [("Text or PDF Files", "*.txt *.pdf")]
        path = filedialog.askopenfilename(title="Select Book File", filetypes=filetypes)
        if path:
            self.file_path = Path(path)
            self.file_label.config(text=self.file_path.name)
    
    def start_processing(self):
        """Start the book processing workflow"""
        if not self.file_path or not self.title_var.get().strip():
            messagebox.showwarning("Missing Info", "Please provide a project title and import a file.")
            return
        
        self.cont_btn.config(state="disabled")
        self.output_var.set("Processing...")
        self.root.config(cursor="watch")  # Show processing cursor
        for child in self.root.winfo_children():
            self._disable_widget_tree(child)
        threading.Thread(target=self.process_book, daemon=True).start()
    
    def _disable_widget_tree(self, widget):
        """Recursively disable all widgets in a widget tree"""
        try:
            widget.config(state="disabled")
        except:
            pass  # Some widgets don't support state
        
        for child in widget.winfo_children():
            self._disable_widget_tree(child)

    def process_book(self):
        """Process the book file"""
        try:
            # Create destination path
            book_folder = Path('books') / self.title_var.get()
            book_folder.mkdir(parents=True, exist_ok=True)

            # TODO: Call your parse function here
            parse(self.file_path, book_folder)
            
            # Simulate processing
            self.root.after(0, lambda: self.output_var.set("Parsing complete!"))
            
            # Move to next step based on multi-voice setting
            if self.multi_voice.get():
                # Go to character labeling
                self.root.after(1000, lambda: self.app.show_character_labeling(book_folder))
            else:
                # TODO: Call your chunking function with multivoice=False
                # TODO: Call your chunking function with multivoice=False
                # create_chunks(book_folder, multivoice=False)
                generate_chunks(book_folder, {}, multivoice = False, max_length = 80)
                
                # Go directly to processing
                self.root.after(1000, lambda: self.app.show_processing_gui(book_folder))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to process book: {e}"))
            self.root.after(0, lambda: self.cont_btn.config(state="normal"))
    
    def destroy(self):
        """Clean up the window"""
        self.root.destroy()

class CharacterLabelingGUI:
    def __init__(self, app, book_path):
        self.app = app
        self.book_path = Path(book_path)
        self.root = tk.Toplevel(app.root)
        self.root.title("Character Labeling")
        self.root.geometry("800x600")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.minsize(400, 300)
        self.root.lift()
        self.root.focus_force()
        self.root.after(100, lambda: self.root.focus_force())
        
        self.data = None
        self.script_names = {}
        self.char_items = {}
        
        self.load_data()
        self.build_ui()
    
    def load_data(self):
        """Load the parsed book data"""
        try:
            parsed_file = self.book_path / "parsed" / "book.book"
            if parsed_file.exists():
                with open(parsed_file, 'r') as f:
                    self.data = json.load(f)
            else:
                messagebox.showerror("Error", "Parsed book data not found")
                self.app.show_main_menu()
                return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load book data: {e}")
            self.app.show_main_menu()
    
    def get_valid_options(self):
        """Get valid voice options"""
        # Get names of folders in the voices folder
        tr = []
        voices = Path('voices')
        for i in os.listdir(voices):
            if i != ".DS_Store":
                tr.append(i)
        return tr
    
    def build_ui(self):
        mainframe = ttk.Frame(self.root, padding="10")
        mainframe.grid(row=0, column=0, sticky="NSEW")
        mainframe.rowconfigure(0, weight=1)
        mainframe.columnconfigure(0, weight=1)
        
        # Character tree
        tree_frame = ttk.Frame(mainframe)
        tree_frame.grid(row=0, column=0, sticky="NSEW")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_frame, columns=("MostUsedName", "ScriptName"), show="tree headings")
        self.tree.heading("#0", text="Character")
        self.tree.heading("MostUsedName", text="Most Used Name")
        self.tree.heading("ScriptName", text="Script Name")
        self.tree.grid(row=0, column=0, sticky="NSEW")
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.grid(row=0, column=1, sticky="NS")
        
        # Populate tree
        self.populate_tree()
        
        # Script name edit area
        edit_frame = ttk.LabelFrame(mainframe, text="Edit Script Name")
        edit_frame.grid(row=1, column=0, sticky="EW", pady=10)
        
        self.edit_id_var = tk.StringVar()
        self.edit_name_var = tk.StringVar()
        
        ttk.Label(edit_frame, text="Character ID:").grid(row=0, column=0)
        id_entry = ttk.Entry(edit_frame, textvariable=self.edit_id_var, width=10)
        id_entry.grid(row=0, column=1)
        
        ttk.Label(edit_frame, text="Script Name:").grid(row=0, column=2)
        name_combobox = ttk.Combobox(edit_frame, textvariable=self.edit_name_var, values=self.get_valid_options(), width=20)
        name_combobox.grid(row=0, column=3)
        
        ttk.Button(edit_frame, text="Save", command=self.save_script_name).grid(row=0, column=4)
        
        # Tree selection binding
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # Auto-assign menu
        auto_frame = ttk.LabelFrame(mainframe, text="Auto-Assign Script Names")
        auto_frame.grid(row=2, column=0, sticky="EW", pady=10)
        
        self.generic_male_var = tk.StringVar(value="GenericMale")
        self.generic_female_var = tk.StringVar(value="GenericFemale")
        self.generic_ungendered_var = tk.StringVar(value="GenericUngendered")
        
        ttk.Label(auto_frame, text="Generic Male:").grid(row=0, column=0)
        ttk.Combobox(auto_frame, textvariable=self.generic_male_var, values=self.get_valid_options(), width=15).grid(row=0, column=1)
        ttk.Label(auto_frame, text="Generic Female:").grid(row=0, column=2)
        ttk.Combobox(auto_frame, textvariable=self.generic_female_var, values=self.get_valid_options(), width=15).grid(row=0, column=3)
        ttk.Label(auto_frame, text="Generic Ungendered:").grid(row=0, column=4)
        ttk.Combobox(auto_frame, textvariable=self.generic_ungendered_var, values=self.get_valid_options(), width=15).grid(row=0, column=5)
        
        ttk.Button(auto_frame, text="Auto-Assign Script Names", command=self.auto_assign_names).grid(
            row=1, column=0, columnspan=6, sticky="EW", pady=(10, 0)
        )
        
        # Narrator name frame
        narrator_frame = ttk.LabelFrame(mainframe, text="Narrator Script Name")
        narrator_frame.grid(row=3, column=0, sticky="EW", pady=10)
        
        self.narrator_var = tk.StringVar(value="Narrator")
        ttk.Label(narrator_frame, text="Narrator Name:").grid(row=0, column=0)
        narrator_combobox = ttk.Combobox(narrator_frame, textvariable=self.narrator_var, values=self.get_valid_options(), width=20)
        narrator_combobox.grid(row=0, column=1)
        
        ttk.Button(narrator_frame, text="Set", command=self.set_narrator_name).grid(row=0, column=2)
        
        # Continue button
        ttk.Button(mainframe, text="Continue to Processing", command=self.continue_to_processing).grid(row=4, column=0, sticky="EW", pady=10)
    
    def populate_tree(self):
        """Populate the character tree"""
        if not self.data or "characters" not in self.data:
            return
        
        for idx, char in enumerate(self.data["characters"]):
            if not char or "id" not in char:
                continue
            
            proper_mentions = char.get("mentions", {}).get("proper", [])
            if not proper_mentions:
                continue
            
            char_id = char["id"]
            most_used_name = self.get_most_used_name(char)
            script_name = self.script_names.get(char_id, "")
            
            parent = self.tree.insert("", "end", text=f"ID: {char_id}", values=(most_used_name, script_name))
            self.char_items[char_id] = parent
            
            # Add names sub-item
            names_item = self.tree.insert(parent, "end", text="names", values=("", ""))
            for mention in proper_mentions:
                self.tree.insert(names_item, "end", text=f'{mention["n"]} (x{mention["c"]})', values=("", ""))
            
            # Add gender info
            gender_info = char.get("g")
            if gender_info:
                gender_value = gender_info.get("argmax", "Unknown") if gender_info else "Unknown"
                self.tree.insert(parent, "end", text=f'Gender: {gender_value}', values=("", ""))
    
    def get_most_used_name(self, char):
        """Get the most used name for a character"""
        proper_mentions = char.get("mentions", {}).get("proper", [])
        if not proper_mentions:
            return ""
        return max(proper_mentions, key=lambda m: m.get("c", 0)).get("n", "")
    
    def save_script_name(self):
        """Save a script name for a character"""
        try:
            cid = int(self.edit_id_var.get())
            name = self.edit_name_var.get()
            if cid and name:
                self.script_names[cid] = name
                item_id = self.char_items.get(cid)
                if item_id:
                    most_used_name = self.tree.set(item_id, "MostUsedName")
                    self.tree.item(item_id, values=(most_used_name, name))
        except ValueError:
            messagebox.showerror("Error", "Invalid character ID")
    
    def on_tree_select(self, event):
        """Handle tree selection"""
        selected = self.tree.selection()
        if not selected:
            return
        
        item_id = selected[0]
        for cid, tid in self.char_items.items():
            if tid == item_id:
                self.edit_id_var.set(str(cid))
                self.edit_name_var.set(self.script_names.get(cid, ""))
                break
    
    def auto_assign_names(self):
        """Auto-assign script names based on gender"""
        if not self.data or "characters" not in self.data:
            return
        
        count = 0
        for char in self.data["characters"]:
            cid = char["id"]
            if not self.script_names.get(cid):
                try:
                    gender = char.get("g", {}).get("argmax", "they/them/their")
                except:
                    gender = "they/them/their"
                
                if gender == "he/him/his":
                    script_name = self.generic_male_var.get()
                elif gender == "she/her":
                    script_name = self.generic_female_var.get()
                else:
                    script_name = self.generic_ungendered_var.get()
                
                self.script_names[cid] = script_name
                
                # Update tree
                item_id = self.char_items.get(cid)
                if item_id:
                    most_used_name = self.tree.set(item_id, "MostUsedName")
                    self.tree.item(item_id, values=(most_used_name, script_name))
                count += 1
        
        messagebox.showinfo("Auto-Assign", f"Assigned names to {count} characters")
    
    def set_narrator_name(self):
        """Set the narrator name"""
        name = self.narrator_var.get()
        if name:
            self.script_names[-1] = name
    
    def continue_to_processing(self):
        """Continue to the processing GUI"""
        # TODO: Call your chunking function with the script_names
        # create_chunks(self.book_path, script_names=self.script_names, multivoice=True)
        generate_chunks(self.book_path, self.script_names, max_length = 80)

        self.app.show_processing_gui(self.book_path)
    
    def destroy(self):
        """Clean up the window"""
        self.root.destroy()

class ProcessingGUI:
    def __init__(self, app, book_path):
        self.app = app
        self.book_path = Path(book_path)
        self.root = tk.Toplevel(app.root)
        self.root.title("TTS Processing")
        self.root.geometry("600x400")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.minsize(400, 300)
        self.root.lift()
        self.root.focus_force()
        self.root.after(100, lambda: self.root.focus_force())
        
        self.threading_enabled = tk.BooleanVar(value=False)
        self.thread_count = tk.StringVar(value="4")
        self.device_selection = tk.StringVar(value="default")
        
        self.build_ui()
    
    def get_available_devices(self):
        """Return available device options for TTS processing"""
        return ["default", "cpu", "cuda", "mps"]
    
    def build_ui(self):
        # Main frame
        mainframe = ttk.Frame(self.root, padding="10")
        mainframe.grid(row=0, column=0, sticky="NSEW")
        mainframe.rowconfigure(0, weight=1)
        mainframe.columnconfigure(0, weight=1)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(mainframe, text="Processing Configuration")
        config_frame.grid(row=0, column=0, sticky="EW", pady=10)
        config_frame.columnconfigure(1, weight=1)
        
        # Threading options
        threading_frame = ttk.LabelFrame(config_frame, text="Threading Options")
        threading_frame.grid(row=0, column=0, columnspan=2, sticky="EW", pady=10)
        
        ttk.Checkbutton(threading_frame, text="Enable Threading", variable=self.threading_enabled).grid(row=0, column=0, sticky="W")
        
        ttk.Label(threading_frame, text="Number of Threads:").grid(row=1, column=0, sticky="W")
        self.thread_spinbox = ttk.Spinbox(threading_frame, from_=1, to=16, textvariable=self.thread_count, width=10)
        self.thread_spinbox.grid(row=1, column=1, sticky="W", padx=(10, 0))
        
        self.threading_enabled.trace("w", lambda *args: self.toggle_threading())
        self.toggle_threading()  # Initialize state
        
        # Device selection
        device_frame = ttk.LabelFrame(config_frame, text="Device Selection")
        device_frame.grid(row=1, column=0, columnspan=2, sticky="EW", pady=10)
        
        ttk.Label(device_frame, text="Processing Device:").grid(row=0, column=0, sticky="W")
        device_combobox = ttk.Combobox(device_frame, textvariable=self.device_selection, values=self.get_available_devices(), width=20)
        device_combobox.grid(row=0, column=1, sticky="W", padx=(10, 0))
        device_combobox.configure(state="readonly")
        
        # Source path display
        path_frame = ttk.LabelFrame(config_frame, text="Source Path")
        path_frame.grid(row=2, column=0, columnspan=2, sticky="EW", pady=10)
        
        ttk.Label(path_frame, text=f"Processing: {self.book_path}").grid(row=0, column=0, sticky="W")
        
        # Processing controls
        control_frame = ttk.Frame(mainframe)
        control_frame.grid(row=1, column=0, sticky="EW", pady=10)
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0)
        
        ttk.Button(button_frame, text="Start Processing", command=self.start_processing).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="Back to Menu", command=self.app.show_main_menu).grid(row=0, column=1)
        
        # Center the button frame
        control_frame.columnconfigure(0, weight=1)
        
        # Status information
        status_frame = ttk.LabelFrame(mainframe, text="Status")
        status_frame.grid(row=2, column=0, sticky="EW", pady=10)
        
        ttk.Label(status_frame, text="Ready to start processing").grid(row=0, column=0, sticky="W")
    
    def toggle_threading(self):
        """Toggle threading spinbox state"""
        if self.threading_enabled.get():
            self.thread_spinbox.configure(state="normal")
        else:
            self.thread_spinbox.configure(state="disabled")
    
    def start_processing(self):
        """Start the TTS processing and quit the GUI"""
        use_threading = self.threading_enabled.get()
        num_threads = int(self.thread_count.get()) if use_threading else 1
        device = self.device_selection.get()
        voices_path = Path('voices/')
        
        print(f"Starting TTS processing with:")
        print(f"  Source path: {self.book_path}")
        print(f"  Threading enabled: {use_threading}")
        print(f"  Number of threads: {num_threads}")
        print(f"  Device: {'cpu' if device == 'default' else device}")
        
        # TODO: Replace this with your actual processing function
        # your_processing_function(self.book_path, use_threading, num_threads, device)
        event = threading.Event()
        thread = threading.Thread(target=start_processing, args=[self.book_path, use_threading, num_threads, device, voices_path, event], daemon=True)
        atexit.register(signal_exit, thread, event)
        thread.start()
        
        self.app.show_processing_status()

    def destroy(self):
        """Clean up the window"""
        self.root.destroy()

class ProcessingStatusGUI:
    def __init__(self, app):
        self.app = app
        self.root = tk.Toplevel(app.root)
        self.root.title("Processing Audiobook")
        self.root.geometry("600x200")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.minsize(300, 150)
        self.root.lift()
        self.root.focus_force()
        self.root.after(100, lambda: self.root.focus_force())
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.build_ui()
    
    def build_ui(self):
        # Main frame
        mainframe = ttk.Frame(self.root, padding="20")
        mainframe.grid(row=0, column=0, sticky="NSEW")
        mainframe.rowconfigure(1, weight=1)
        mainframe.columnconfigure(0, weight=1)
        
        # Processing message
        message_frame = ttk.Frame(mainframe)
        message_frame.grid(row=0, column=0, sticky="EW", pady=(0, 20))
        message_frame.columnconfigure(0, weight=1)
        
        processing_label = ttk.Label(
            message_frame, 
            text="Processing Audiobook...", 
            font=("Arial", 14, "bold")
        )
        processing_label.grid(row=0, column=0)
        
        status_label = ttk.Label(
            message_frame,
            text="This may take several minutes. Or several hours. Or several days. Check the terminal for progress.",
            font=("Arial", 10)
        )
        status_label.grid(row=1, column=0, pady=(10, 0))
        
        # Quit button (centered)
        button_frame = ttk.Frame(mainframe)
        button_frame.grid(row=1, column=0)
        
        quit_btn = ttk.Button(
            button_frame,
            text="Quit Application",
            command=self.on_closing,
            width=20
        )
        quit_btn.grid(row=0, column=0)
    
    def on_closing(self):
        """Handle window closing"""
        self.app.root.quit()
        self.app.root.destroy()
    
    def destroy(self):
        """Clean up the window"""
        self.root.destroy()

class VoiceEditorGUI:
    def __init__(self, app):
        self.app = app
        self.root = tk.Toplevel(app.root)
        self.root.title("Voice Editor")
        self.root.geometry("800x400")
        self.root.minsize(500, 300)
        self.root.lift()
        self.root.focus_force()
        self.root.after(100, lambda: self.root.focus_force())
        
        # TODO: Initialize VoiceArguments class
        self.voice_args = VoiceArguments(name="Untitled")
        
        self.sample_text = tk.StringVar(value="That quick beige fox jumped in the air over each thin dog. \"Look out!\" I shout, for he's foiled you again, creating chaos.")
        self.voice_name = tk.StringVar(value="")
        self.exaggeration = tk.DoubleVar(value=0.4)  # Default values
        self.cfg_weight = tk.DoubleVar(value=0.7)
        self.temperature = tk.DoubleVar(value=0.7)
        self.pitch = tk.DoubleVar(value=0.0)
        
        self.save_location = Path('voices/')
        self.save_location.mkdir(parents=True, exist_ok=True)
        
        self.build_ui()
    
    def build_ui(self):
        """Build the voice editor UI"""
        mainframe = ttk.Frame(self.root, padding=10)
        mainframe.grid(row=0, column=0, sticky="NSEW")

        # Configure root and mainframe resizing behavior
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        mainframe.columnconfigure(0, weight=1)
        for i in range(8):
            mainframe.rowconfigure(i, weight=0)
        mainframe.rowconfigure(4, weight=1)  # Make sample text row expandable

        # Upload Frame (Upload button + voice label)
        upload_frame = ttk.Frame(mainframe)
        upload_frame.grid(row=0, column=0, sticky="EW", pady=(0, 15))
        upload_frame.columnconfigure(1, weight=1)

        # Voice Name Frame
        name_frame = ttk.Frame(mainframe)
        name_frame.grid(row=1, column=0, sticky="EW", pady=(0, 15))
        name_frame.columnconfigure(1, weight=1)

        ttk.Label(name_frame, text="Voice Name:").grid(row=0, column=0, sticky="W")
        name_entry = ttk.Entry(name_frame, textvariable=self.voice_name, width=30)
        name_entry.grid(row=0, column=1, sticky="EW", padx=(10, 0))

        ttk.Button(upload_frame, text="Upload Reference Voice", command=self.upload_voice).grid(row=0, column=0, sticky="W")
        self.voice_label = ttk.Label(upload_frame, text="No file selected", foreground="gray")
        self.voice_label.grid(row=0, column=1, sticky="W", padx=(10, 0))

        # Info button frame
        info_frame = ttk.Frame(mainframe)
        info_frame.grid(row=2, column=0, sticky="EW", pady=(0, 10))

        ttk.Button(info_frame, text="Parameter Info", command=self.show_parameter_info).grid(row=0, column=0, sticky="W")

        # Sliders + Entry boxes
        self._add_slider(mainframe, "Exaggeration", self.exaggeration, 3, 0.0, 1.0)
        self._add_slider(mainframe, "CFG Weight", self.cfg_weight, 4, 0.0, 1.0)
        self._add_slider(mainframe, "Temperature", self.temperature, 5, 0.0, 1.0)
        self._add_slider(mainframe, "Pitch", self.pitch, 6, -24.0, 24.0)

        # Sample Text Label
        ttk.Label(mainframe, text="Sample Text:").grid(row=7, column=0, sticky="W", pady=(10, 2))

        # Sample Text Entry (resizable)
        entry = ttk.Entry(mainframe, textvariable=self.sample_text)
        entry.grid(row=8, column=0, sticky="EW")
        mainframe.rowconfigure(6, weight=1)  # Make this entry row expandable
        entry.focus_set()

        # Status Label
        self.status_label = ttk.Label(mainframe, text="Ready to generate audio sample", foreground="white")
        self.status_label.grid(row=9, column=0, sticky="W", pady=(5, 0))

        # Buttons Frame
        button_frame = ttk.Frame(mainframe)
        button_frame.grid(row=10, column=0, sticky="EW", pady=10)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        ttk.Button(button_frame, text="Generate Sample", command=self.generate_and_play).grid(row=0, column=0, sticky="EW", padx=2)
        ttk.Button(button_frame, text="Save Voice Settings", command=self.save_voice_settings).grid(row=0, column=1, sticky="EW", padx=2)
        ttk.Button(button_frame, text="Return to Menu", command=self.return_to_menu).grid(row=0, column=2, sticky="EW", padx=2)

    def _add_slider(self, parent, label, variable, row, minv, maxv):
        """Add a slider with label and entry box"""
        ttk.Label(parent, text=f"{label}:").grid(row=row, column=0, sticky="W", pady=2)
        container = ttk.Frame(parent)
        container.grid(row=row, column=1, sticky="EW", pady=2)
        container.columnconfigure(0, weight=1)

        slider = ttk.Scale(container, from_=minv, to=maxv, variable=variable)
        slider.grid(row=0, column=0, sticky="EW", padx=(0, 5))
        entry = ttk.Entry(container, textvariable=variable, width=8)
        entry.grid(row=0, column=1)

    def play_sample(self, sample, sr):
        simpleaudio.play_buffer(sample, num_channels=1, bytes_per_sample=2, sample_rate=sr)

    def show_parameter_info(self):
        """Show information about voice parameters"""
        info_text = """Voice Parameter Guide:

    CFG Weight:
    - Controls speaking pace and timing
    - Higher values = faster, more energetic speech
    - Lower values = slower, more deliberate speech

    Exaggeration:
    - Controls emotional intensity and variation
    - Higher values = more dramatic, faster pace
    - Lower values = more neutral, steady delivery

    Temperature:
    - Controls randomness and creativity
    - Higher values = more variation between generations
    - Lower values = more consistent, predictable output
    
    Pitch:
    - Controls the pitch
    - Zero means no pitch shift

    """
        
        messagebox.showinfo("Parameter Information", info_text)

    def upload_voice(self):
        """Upload a reference voice file"""
        file = filedialog.askopenfilename(
            title="Select Reference Voice File",
            filetypes=[("Audio Files", "*.wav",), ("All Files", "*.*")]
        )
        if file:
            # TODO: Set reference path in VoiceArguments
            self.voice_args.reference_path = Path(file)
            self.voice_label.config(text=f"Selected: {Path(file).name}", foreground="white")
            self.reference_file = Path(file)

    def generate_and_play(self):
        """Generate and play audio sample"""
        if hasattr(self, 'reference_file'):
            self.voice_args.reference_path = self.reference_file
        else:
            self.voice_args.reference_path = None

        def run():
            self.status_label.config(text="Generating audio sample...")
            try:
                # TODO: Call your generate_sample function here
                
                #set self.voice_args cfg_weight, exaggeration, temperature, pitch to values in sliders aboce
                self.voice_args.cfg_weight = self.cfg_weight.get()
                self.voice_args.exaggeration = self.exaggeration.get()
                self.voice_args.temperature = self.temperature.get()
                self.voice_args.pitch = self.pitch.get()

                audio, sr = Generate.generate_sample(self.sample_text.get(), self.voice_args)
                self.play_sample(audio, sr)
                self.status_label.config(text="Done.")
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text="Error generating audio."))
                messagebox.showerror("Error", f"Failed to generate audio:\n{e}")

        threading.Thread(target=run, daemon=True).start()

    def save_voice_settings(self):
        """Save voice settings to file"""
        self.voice_args.cfg_weight = self.cfg_weight.get()
        self.voice_args.exaggeration = self.exaggeration.get()
        self.voice_args.temperature = self.temperature.get()
        self.voice_args.pitch = self.pitch.get()
        
        voice_name = self.voice_name.get().strip()
        if not voice_name:
            messagebox.showwarning("Missing Name", "Please enter a name for this voice.")
            return
        
        target_dir = self.save_location / voice_name
        
        # Check if directory already exists
        if target_dir.exists():
            if not messagebox.askyesno("Overwrite", f"Voice '{voice_name}' already exists. Overwrite?"):
                return
        
        target_dir.mkdir(parents=True, exist_ok=True)

        # Save settings
        settings = {
            "name": voice_name,  # Store original name
            "exaggeration": self.exaggeration.get(),
            "cfg_weight": self.cfg_weight.get(),
            "temperature": self.temperature.get(),
            "pitch": self.pitch.get()
        }

        if hasattr(self, "reference_file"):
            voice_copy_path = target_dir / ("reference" + self.reference_file.suffix)
            shutil.copy(self.reference_file, voice_copy_path)
            settings["reference_path"] = str(voice_copy_path.absolute())

        with open(target_dir / "settings.json", "w") as f:
            json.dump(settings, f, indent=2)

        messagebox.showinfo("Saved", f"Voice '{voice_name}' saved as '{voice_name}' to: {target_dir}")
        self.status_label.config(text=f"Voice '{voice_name}' saved successfully!")

    def return_to_menu(self):
        """Return to the main menu"""
        self.app.show_main_menu()

    def destroy(self):
        """Clean up the window"""
        self.root.destroy()

class ExportBookGUI:
    def __init__(self, app):
        self.app = app
        self.root = tk.Toplevel(app.root)
        self.root.title("Export Audiobook")
        self.root.geometry("800x400")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.minsize(400, 300)
        self.root.lift()
        self.root.focus_force()
        self.root.after(100, lambda: self.root.focus_force())
        
        self.book_dir = None
        self.output_path = None
        self.output_var = tk.StringVar(value="Select a book directory to begin")
        
        self.build_ui()
    
    def build_ui(self):
        mainframe = ttk.Frame(self.root, padding="20")
        mainframe.grid(row=0, column=0, sticky="NSEW")
        
        # Configure grid weights
        for i in range(6):
            mainframe.rowconfigure(i, weight=1)
        mainframe.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(mainframe, text="Export Audiobook to MP3", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Book directory selection
        ttk.Label(mainframe, text="Book Directory:").grid(row=1, column=0, sticky="W")
        self.book_dir_label = ttk.Label(mainframe, text="No directory selected", foreground="gray")
        self.book_dir_label.grid(row=1, column=1, sticky="W", padx=(10, 0))
        ttk.Button(mainframe, text="Browse", command=self.browse_book_directory).grid(row=1, column=2, sticky="E")
        
        # Output file selection
        ttk.Label(mainframe, text="Output MP3:").grid(row=2, column=0, sticky="W")
        self.output_path_label = ttk.Label(mainframe, text="No output file selected", foreground="gray")
        self.output_path_label.grid(row=2, column=1, sticky="W", padx=(10, 0))
        ttk.Button(mainframe, text="Browse", command=self.browse_output_path).grid(row=2, column=2, sticky="E")
        
        # Status
        ttk.Label(mainframe, text="Status:").grid(row=3, column=0, sticky="W")
        self.status_label = ttk.Label(mainframe, textvariable=self.output_var, foreground="white")
        self.status_label.grid(row=3, column=1, columnspan=2, sticky="W", padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(mainframe)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        button_frame.columnconfigure((0, 1, 2), weight=1)
        
        ttk.Button(button_frame, text="Back", command=self.app.show_main_menu).grid(row=0, column=0, sticky="W")
        
        self.export_btn = ttk.Button(button_frame, text="Export to MP3", command=self.start_export)
        self.export_btn.grid(row=0, column=1)
        self.export_btn.config(state="disabled")
        
        # Progress info
        info_frame = ttk.LabelFrame(mainframe, text="Information")
        info_frame.grid(row=5, column=0, columnspan=3, sticky="EW", pady=(10, 0))
        
        info_text = ("This will combine all WAV files in the book's audio directory "
                    "into a single MP3 file. Files will be combined in alphabetical order.")
        ttk.Label(info_frame, text=info_text, wraplength=500).grid(row=0, column=0, sticky="W", padx=10, pady=10)
    
    def browse_book_directory(self):
        """Browse for book directory"""
        directory = filedialog.askdirectory(
            title="Select Book Directory", 
            initialdir=Path('books')
        )
        
        if directory:
            book_path = Path(directory)
            audio_path = book_path / "audio"
            
            if not audio_path.exists():
                messagebox.showerror("Error", f"Audio directory not found: {audio_path}")
                return
            
            # Check for WAV files
            wav_files = list(audio_path.glob("*.wav"))
            if not wav_files:
                messagebox.showwarning("Warning", f"No WAV files found in: {audio_path}")
                return
            
            self.book_dir = book_path
            self.book_dir_label.config(text=str(book_path.name), foreground="white")
            self.output_var.set(f"Found {len(wav_files)} WAV files ready for export")
            
            # Auto-suggest output filename
            suggested_name = f"{book_path.name}_audiobook.mp3"
            self.output_path = book_path / suggested_name
            self.output_path_label.config(text=suggested_name, foreground="white")
            
            self.update_export_button()
    
    def browse_output_path(self):
        """Browse for output MP3 file"""
        if not self.book_dir:
            messagebox.showwarning("Warning", "Please select a book directory first")
            return
        
        initial_name = f"{self.book_dir.name}_audiobook.mp3"
        file_path = filedialog.asksaveasfilename(
            title="Save MP3 As",
            defaultextension=".mp3",
            initialfile=initial_name,
            filetypes=[("MP3 Files", "*.mp3"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.output_path = Path(file_path)
            self.output_path_label.config(text=self.output_path.name, foreground="white")
            self.update_export_button()
    
    def update_export_button(self):
        """Enable export button when both paths are selected"""
        if self.book_dir and self.output_path:
            self.export_btn.config(state="normal")
        else:
            self.export_btn.config(state="disabled")
    
    def combine_wavs_to_mp3(self, wav_dir, output_mp3_path):
        """Combine WAV files into MP3"""
        combined = AudioSegment.empty()
        wav_files = sorted([f for f in os.listdir(wav_dir) if f.lower().endswith(".wav")])
        
        total_files = len(wav_files)
        
        for i, fname in enumerate(wav_files):
            path = os.path.join(wav_dir, fname)
            audio = AudioSegment.from_wav(path)
            combined += audio
            
            # Update status
            progress = (i + 1) / total_files * 100
            self.root.after(0, lambda p=progress, f=fname: 
                          self.output_var.set(f"Processing: {f} ({p:.1f}%)"))
        
        # Export to MP3
        self.root.after(0, lambda: self.output_var.set("Exporting to MP3..."))
        combined.export(output_mp3_path, format="mp3")
    
    def start_export(self):
        """Start the export process"""
        if not self.book_dir or not self.output_path:
            messagebox.showwarning("Warning", "Please select both book directory and output file")
            return
        
        # Disable UI during export
        self.export_btn.config(state="disabled")
        self.output_var.set("Starting export...")
        
        def export_thread():
            try:
                audio_dir = self.book_dir / "audio"
                self.combine_wavs_to_mp3(str(audio_dir), str(self.output_path))
                
                # Success message
                self.root.after(0, lambda: self.output_var.set("Export completed successfully!"))
                self.root.after(0, lambda: messagebox.showinfo(
                    "Export Complete", 
                    f"Audiobook exported to:\n{self.output_path}"
                ))
                
            except Exception as e:
                self.root.after(0, lambda: self.output_var.set("Export failed!"))
                self.root.after(0, lambda: messagebox.showerror(
                    "Export Error", 
                    f"Failed to export audiobook:\n{str(e)}"
                ))
            finally:
                # Re-enable button
                self.root.after(0, lambda: self.export_btn.config(state="normal"))
        
        # Run export in separate thread
        threading.Thread(target=export_thread, daemon=True).start()
    
    def destroy(self):
        """Clean up the window"""
        self.root.destroy()


def start_processing(path, threaded, num_threads, device, voices, event):
    gen = Generate(
        Device(device=device),
        path,
        voices,
        num_threads,
        event
        )
    if threaded:
        gen.generate_threaded()
    else:
        gen.generate()

def signal_exit(thread, event):
    event.set()
    thread.join()
