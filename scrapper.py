import tkinter as tk
import sys
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine, text
import threading
import os
from PIL import Image
import io
import json
import traceback
from datetime import datetime
from urllib.parse import urljoin
import re
from pathlib import WindowsPath, Path

class WheelersScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Wheeler's Books ISBN Scraper")
        self.root.geometry("800x700")
        
        # Configuration file for database settings
        self.config_file = "db_config.json"
        self.load_config()
        
        # Variables
        self.isbn_list = []
        self.scraped_data = []
        self.is_scraping = False
        self.images_folder = "book_images"  # Default folder for images
        
        self.setup_gui()
        
    def load_config(self):
        """Load database configuration from file"""
        default_config = {
            "host": "localhost",
            "port": "3306",
            "database": "books_db",
            "username": "root",
            "password": ""
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.db_config = json.load(f)
            else:
                self.db_config = default_config
                self.save_config()
        except:
            self.db_config = default_config
    
    def save_config(self):
        """Save database configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.db_config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def setup_gui(self):
        # Main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Main Scraper
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="ISBN Scraper")
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="Input File Selection", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(file_frame, text="Select CSV/Excel File", 
                  command=self.select_file).pack(side=tk.LEFT)
        
        self.file_label = ttk.Label(file_frame, text="No file selected")
        self.file_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Scraping Options", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Image download options
        image_frame = ttk.Frame(options_frame)
        image_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.download_images_var = tk.BooleanVar()
        ttk.Checkbutton(image_frame, text="Download Book Images", 
                       variable=self.download_images_var,
                       command=self.toggle_image_options).pack(side=tk.LEFT)
        
        # Image folder selection
        self.image_folder_frame = ttk.Frame(options_frame)
        self.image_folder_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(self.image_folder_frame, text="Images Folder:").pack(side=tk.LEFT)
        self.images_folder_var = tk.StringVar(value=self.images_folder)
        self.folder_label = ttk.Label(self.image_folder_frame, textvariable=self.images_folder_var)
        self.folder_label.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(self.image_folder_frame, text="Browse", 
                  command=self.select_images_folder).pack(side=tk.LEFT, padx=(10, 0))
        
        # Initially hide image folder options
        self.image_folder_frame.pack_forget()
        
        self.save_to_db_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Save to Database", 
                       variable=self.save_to_db_var).pack(anchor=tk.W)
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="Start Scraping", 
                                      command=self.start_scraping)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.export_csv_button = ttk.Button(control_frame, text="Export to CSV", 
                                           command=self.export_csv, state=tk.DISABLED)
        self.export_csv_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.export_excel_button = ttk.Button(control_frame, text="Export to Excel", 
                                             command=self.export_excel, state=tk.DISABLED)
        self.export_excel_button.pack(side=tk.LEFT)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=10)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="Ready to start...")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Tab 2: Database Settings
        db_frame = ttk.Frame(notebook)
        notebook.add(db_frame, text="Database Settings")
        
        self.setup_db_tab(db_frame)
    
    def toggle_image_options(self):
        """Show/hide image folder options based on checkbox state"""
        if self.download_images_var.get():
            self.image_folder_frame.pack(fill=tk.X, pady=(0, 5))
        else:
            self.image_folder_frame.pack_forget()
    
    def select_images_folder(self):
        """Select folder for storing downloaded images"""
        folder_path = filedialog.askdirectory(title="Select Images Folder")
        if folder_path:
            self.images_folder = folder_path
            self.images_folder_var.set(folder_path)
            self.log_message(f"Images folder set to: {folder_path}")
    
    def setup_db_tab(self, parent):
        """Setup database configuration tab"""
        db_config_frame = ttk.LabelFrame(parent, text="MySQL Database Configuration", padding=20)
        db_config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Database fields
        fields = [
            ("Host:", "host"),
            ("Port:", "port"),
            ("Database:", "database"),
            ("Username:", "username"),
            ("Password:", "password")
        ]
        
        self.db_entries = {}
        
        for i, (label, key) in enumerate(fields):
            ttk.Label(db_config_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            
            if key == "password":
                entry = ttk.Entry(db_config_frame, show="*", width=30)
            else:
                entry = ttk.Entry(db_config_frame, width=30)
                
            entry.grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=5)
            entry.insert(0, str(self.db_config.get(key, "")))
            self.db_entries[key] = entry
        
        # Buttons frame
        btn_frame = ttk.Frame(db_config_frame)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Test Connection", 
                  command=self.test_db_connection).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="Save Settings", 
                  command=self.save_db_settings).pack(side=tk.LEFT)
    
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def sanitize_filename(self, filename):
        """Sanitize filename to be safe for file system"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        return filename
    
    def download_image(self, image_url, isbn, title=None):
        """Download and save book image"""
        try:
            # Create images folder if it doesn't exist
            os.makedirs(self.images_folder, exist_ok=True)
            
            # Get image data
            response = requests.get(image_url, timeout=30, 
                                  headers={"User-Agent": "Mozilla/5.0 (compatible)"})
            response.raise_for_status()
            
            # Determine file extension from URL or content type
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'gif' in content_type:
                ext = '.gif'
            else:
                # Try to get extension from URL
                ext = os.path.splitext(image_url.split('?')[0])[1].lower()
                if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                    ext = '.jpg'  # Default to jpg
            
            # Create filename
            filename = f"{isbn}{ext}"
            
            # Full path
            filepath = os.path.join(self.images_folder, filename)
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Verify it's a valid image by trying to open it
            try:
                with Image.open(filepath) as img:
                    img.verify()
            except Exception:
                # If verification fails, remove the file
                os.remove(filepath)
                return None
            
            self.log_message(f"Downloaded image: {filename}")

            filepath = str(Path(filepath).absolute())

            if sys.platform not in ['linux', 'darwin']:
                filepath = filepath.replace("/", "\\")

            return filepath
            
        except Exception as e:
            self.log_message(f"Failed to download image for ISBN {isbn}: {str(e)}")
            return None
    
    def select_file(self):
        """Select CSV or Excel file containing ISBNs"""
        file_path = filedialog.askopenfilename(
            title="Select ISBN File",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Read the file and extract ISBNs
                if file_path.lower().endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                # Look for ISBN column (case insensitive)
                isbn_col = None
                for col in df.columns:
                    if 'isbn' in col.lower():
                        isbn_col = col
                        break
                
                if isbn_col is None:
                    # If no ISBN column found, assume first column contains ISBNs
                    isbn_col = df.columns[0]
                
                self.isbn_list = df[isbn_col].astype(str).tolist()
                self.isbn_list = [isbn.strip() for isbn in self.isbn_list if isbn.strip()]
                
                self.file_label.config(text=f"File loaded: {len(self.isbn_list)} ISBNs found")
                self.log_message(f"Loaded {len(self.isbn_list)} ISBNs from {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {str(e)}")
                self.log_message(f"Error reading file: {str(e)}")
    
    def test_db_connection(self):
        """Test database connection"""
        try:
            # Update config from entries
            for key, entry in self.db_entries.items():
                self.db_config[key] = entry.get()
            
            connection_string = f"mysql+pymysql://{self.db_config['username']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            messagebox.showinfo("Success", "Database connection successful!")
            self.log_message("Database connection test successful")
            
        except Exception as e:
            messagebox.showerror("Error", f"Database connection failed: {str(e)}")
            self.log_message(f"Database connection failed: {str(e)}")
    
    def save_db_settings(self):
        """Save database settings"""
        for key, entry in self.db_entries.items():
            self.db_config[key] = entry.get()
        
        self.save_config()
        messagebox.showinfo("Success", "Database settings saved!")
        self.log_message("Database settings saved")
    
    def extract_book_info(self, isbn):
        """Extract book information from Wheeler's website (robust to quotes)."""
        base_url = "https://www.wheelersbooks.com.au/product/"
        url = base_url + isbn

        try:
            res = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible)"},
                timeout=30,
            )
            if res.status_code != 200:
                return {"isbn": isbn, "error": f"HTTP {res.status_code}"}

            soup = BeautifulSoup(res.text, "html.parser")

            def safe_text(selector: str):
                el = soup.select_one(selector)
                return el.get_text(strip=True) if el else None

            def _row_selector(label_text: str) -> str:
                safe = label_text.replace('"', '\\"')
                return f'div.row:has(label:contains("{safe}")) span'

            def _table_selector(label_text: str) -> str:
                safe = label_text.replace('"', '\\"')
                return f'tr:has(th:contains("{safe}")) td'

            def grab(label: str):
                return safe_text(_row_selector(label)) or safe_text(_table_selector(label))

            def extract_single_book_data(soup_obj, isbn_val, base_url_val):
                """Extract book data from a BeautifulSoup object."""
                categories = [
                    a.get_text(strip=True)
                    for a in soup_obj.select("div.product-description a[href*='/category/']")
                ]
                categories_text = ", ".join(categories) if categories else None

                image_url = None
                local_image_path = None
                
                # Always extract image URL
                img_el = soup_obj.select_one("img.cover")   
                if img_el and img_el.get("src"):
                    src = img_el["src"]

                    # make it absolute
                    if src.startswith("//"):            
                        src = "https:" + src
                    else:                               
                        src = urljoin(base_url_val, src)

                    image_url = src
                    
                    # Download image if option is enabled
                    if self.download_images_var.get() and image_url:
                        # Get title for filename
                        title = grab("Title") or safe_text("h1.title")
                        local_image_path = self.download_image(image_url, isbn_val, title)

                # Use local grab function that works with the passed soup object
                def local_grab(label: str):
                    def local_safe_text(selector: str):
                        el = soup_obj.select_one(selector)
                        return el.get_text(strip=True) if el else None
                    
                    return local_safe_text(_row_selector(label)) or local_safe_text(_table_selector(label))
                
                return {
                    # Identifiers ---------------------------------------------------
                    "isbn": local_grab("ISBN:"),
                    "title": local_grab("Title") or safe_text("h1.title"),
                    "author": local_grab("Author") or safe_text("div.author a[href*='/author/']"),
                    "illustrator": safe_text("div.author div:nth-of-type(2) a.link"),
                    # Publication ---------------------------------------------------
                    "publisher": local_grab("Publisher:") or local_grab("Publisher"),
                    "published": local_grab("Published:"),
                    "published_imported": local_grab("Published (Imported):"),
                    "replaced_by": local_grab("Replaced by:"),
                    "language": local_grab("Language:"),
                    "series": local_grab("Series:") or safe_text("span.series a"),
                    "interest_age": local_grab("Interest age:"),
                    "ar_level": local_grab("AR:"),
                    "premiers_reading_challenge": local_grab("Premier's Reading Challenge:"),
                    "imprint": local_grab("Imprint"),
                    "publication_country": local_grab("Publication Country"),
                    "edition": local_grab("Edition"),
                    # Physical / meta -----------------------------------------------
                    "page_count": local_grab("Number of pages"),
                    "dimensions": local_grab("Dimensions"),
                    "weight": local_grab("Weight"),
                    "dewey_code": local_grab("Dewey Code"),
                    "reading_age": local_grab("Reading Age"),
                    "library_of_congress": local_grab("Library of Congress"),
                    "nbs_text": local_grab("NBS Text"),
                    "onix_text": local_grab("Onix Text"),
                    # Misc -----------------------------------------------------------
                    "price": local_grab("Price") or safe_text("div.price.red-text.bold") or safe_text("span.price"),                    "full_description": local_grab("Full Description") or safe_text("div.description"),
                    "categories": categories_text,
                    "image_url": image_url,
                    "local_image_path": local_image_path,  # New field for local image path
                    "scraped_at": datetime.now().isoformat(),
                }

            def get_alternate_data():
                """Extract alternate format data from the current page."""
                alternate_data = []
                all_alt_formats_section = soup.select('#allAltFormats ul li a[href*="/product/"]')

                def abs_url(href: str) -> str:
                    return urljoin('https://www.wheelersbooks.com.au', href)

                current_url_norm = url.rstrip('/')

                for link in all_alt_formats_section:
                    href = link.get('href')
                    if not href:
                        continue
                    href = abs_url(href)
                    if href.rstrip('/') == current_url_norm:
                        continue  # skip current page

                    try:
                        alt_res = requests.get(
                            href,
                            headers={"User-Agent": "Mozilla/5.0 (compatible)"},
                            timeout=30,
                        )
                        if alt_res.status_code != 200:
                            continue

                        alt_soup = BeautifulSoup(alt_res.text, "html.parser")

                        def alt_safe_text(selector: str):
                            el = alt_soup.select_one(selector)
                            return el.get_text(strip=True) if el else None

                        def alt_local_grab(label: str):
                            def _row_selector(label_text: str) -> str:
                                safe = label_text.replace('"', '\\"')
                                return f'div.row:has(label:contains("{safe}")) span'
                            def _table_selector(label_text: str) -> str:
                                safe = label_text.replace('"', '\\"')
                                return f'tr:has(th:contains("{safe}")) td'
                            return (
                                alt_safe_text(_row_selector(label))
                                or alt_safe_text(_table_selector(label))
                            )

                        alt_price = (
                            alt_local_grab("Price")
                            or alt_safe_text("div.price.red-text.bold")
                            or alt_safe_text("span.price.red-text")
                            or alt_safe_text("span.price")
                        )

                        alt_data = {
                            "alternate_edition":        alt_local_grab("Edition"),
                            "alternate_isbn":           alt_local_grab("ISBN:"),
                            "alternate_isbn_pub_date":  alt_local_grab("Published:"),
                            "alternate_isbn_price":     alt_price,
                        }
                        alternate_data.append(alt_data)

                    except Exception:
                        continue

                return alternate_data



            # Extract main book data
            book_data = extract_single_book_data(soup, isbn, url)
            
            # Extract alternate formats
            alternates = get_alternate_data()
            
            # Option 1: Flatten alternates into the main book data (takes first alternate only)
            if alternates:
                first_alt = alternates[0]
                book_data.update(first_alt)
            else:
                # Add empty alternate fields if no alternates found
                book_data.update({
                    "alternate_edition": None,
                    "alternate_isbn": None,
                    "alternate_isbn_pub_date": None,
                    "alternate_isbn_price": None,
                })
            
            return book_data

        except Exception as exc:
            # Bubble up a clean message
            return {"isbn": isbn}

    
    def scrape_books(self):
        """Main scraping function"""
        self.scraped_data = []
        total_books = len(self.isbn_list)
        
        # Create images folder if downloading images
        if self.download_images_var.get():
            try:
                os.makedirs(self.images_folder, exist_ok=True)
                self.log_message(f"Images will be saved to: {self.images_folder}")
            except Exception as e:
                self.log_message(f"Error creating images folder: {str(e)}")
        
        self.progress_bar['maximum'] = total_books
        
        for i, isbn in enumerate(self.isbn_list):
            if not self.is_scraping:  # Check if scraping was stopped
                break
                
            self.progress_var.set(f"Processing ISBN {i+1}/{total_books}: {isbn}")
            self.log_message(f"Scraping data for ISBN: {isbn}")
            
            book_data = self.extract_book_info(isbn)
            self.scraped_data.append(book_data)
            
            if 'error' in book_data:
                self.log_message(f"Error for ISBN {isbn}: {book_data['error']}")
            else:
                title = book_data.get('title', 'Unknown Title')
                self.log_message(f"Successfully scraped: {title}")
                
                # Log if image was downloaded
                if self.download_images_var.get() and book_data.get('local_image_path'):
                    self.log_message(f"  └─ Image saved: {os.path.basename(book_data['local_image_path'])}")
            
            self.progress_bar['value'] = i + 1
            self.root.update_idletasks()
        
        if self.is_scraping:  # Only proceed if scraping wasn't stopped
            self.progress_var.set(f"Completed! Processed {len(self.scraped_data)} books")
            
            # Save to database if requested
            if self.save_to_db_var.get():
                self.save_to_database()
            
            # Enable export buttons
            self.export_csv_button.config(state=tk.NORMAL)
            self.export_excel_button.config(state=tk.NORMAL)
            
            # Log summary
            downloaded_images = sum(1 for book in self.scraped_data if book.get('local_image_path'))
            self.log_message("Scraping completed successfully!")
            if self.download_images_var.get():
                self.log_message(f"Downloaded {downloaded_images} images to {self.images_folder}")
        
        self.is_scraping = False
        self.start_button.config(text="Start Scraping")
    
    def save_to_database(self):
        """Save scraped data to MySQL database"""
        try:
            connection_string = f"mysql+pymysql://{self.db_config['username']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            
            engine = create_engine(connection_string)
            
            # Convert to DataFrame
            df = pd.DataFrame(self.scraped_data)
            
            # Save to database
            df.to_sql("wheelers_books", engine, if_exists="append", index=False)
            
            self.log_message(f"Successfully saved {len(self.scraped_data)} records to database")
            
        except Exception as e:
            self.log_message(f"Error saving to database: {str(e)}")
            messagebox.showerror("Database Error", f"Failed to save to database: {str(e)}")
    
    def start_scraping(self):
        """Start or stop the scraping process"""
        if not self.is_scraping:
            if not self.isbn_list:
                messagebox.showwarning("Warning", "Please select a file with ISBNs first!")
                return
            
            self.is_scraping = True
            self.start_button.config(text="Stop Scraping")
            self.export_csv_button.config(state=tk.DISABLED)
            self.export_excel_button.config(state=tk.DISABLED)
            
            # Start scraping in a separate thread
            threading.Thread(target=self.scrape_books, daemon=True).start()
        else:
            self.is_scraping = False
            self.start_button.config(text="Start Scraping")
            self.progress_var.set("Stopping...")
    
    def export_csv(self):
        """Export scraped data to CSV"""
        if not self.scraped_data:
            messagebox.showwarning("Warning", "No data to export!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save CSV File",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        
        if file_path:
            try:
                df = pd.DataFrame(self.scraped_data)
                df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Data exported to {file_path}")
                self.log_message(f"Data exported to CSV: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")
    
    def export_excel(self):
        """Export scraped data to Excel"""
        if not self.scraped_data:
            messagebox.showwarning("Warning", "No data to export!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Excel File",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if file_path:
            try:
                df = pd.DataFrame(self.scraped_data)
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Success", f"Data exported to {file_path}")
                self.log_message(f"Data exported to Excel: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export Excel: {str(e)}")

def main():
    root = tk.Tk()
    app = WheelersScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
