import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
import os
from tkinter import ttk
import threading

# Try to import TkinterDnD2 for drag and drop functionality
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    dnd_available = True
except ImportError:
    dnd_available = False

def analyze_pdf(file_path):
    """Analyze PDF to determine which pages are color and which are black and white."""
    try:
        doc = fitz.open(file_path)
        color_pages = []
        bw_pages = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(alpha=False)
            
            # Check if the page has color
            if pix.colorspace and pix.colorspace.n >= 3:  # RGB or CMYK
                # Further check by sampling pixels
                is_color = False
                img_data = pix.samples
                
                # Sample pixels to check for color variation
                # If R, G, B values differ significantly, it's color
                for i in range(0, len(img_data), 3 * 10):  # Check every 10th pixel
                    if i + 2 < len(img_data):
                        r, g, b = img_data[i], img_data[i+1], img_data[i+2]
                        if abs(r - g) > 5 or abs(r - b) > 5 or abs(g - b) > 5:
                            is_color = True
                            break
                
                if is_color:
                    color_pages.append(page_num + 1)  # +1 for human-readable page numbers
                else:
                    bw_pages.append(page_num + 1)
            else:
                bw_pages.append(page_num + 1)
        
        doc.close()
        return color_pages, bw_pages
    
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        return [], []

def display_results(color_pages, bw_pages, result_text):
    """Display the results in the text widget."""
    result_text.config(state=tk.NORMAL)  # Enable editing
    result_text.delete(1.0, tk.END)  # Clear previous results
    
    total_pages = len(color_pages) + len(bw_pages)
    
    if color_pages:
        if len(color_pages) == total_pages:  # All pages are color
            result_text.insert(tk.END, f"All {total_pages} pages contain color.\n\n")
        else:
            result_text.insert(tk.END, f"Color pages ({len(color_pages)}/{total_pages}): ")
            # Format as comma-separated, with ranges
            result_text.insert(tk.END, format_page_list(color_pages) + "\n\n")
    
    if bw_pages:
        if len(bw_pages) == total_pages:  # All pages are B&W
            result_text.insert(tk.END, f"All {total_pages} pages are black and white.\n")
        else:
            result_text.insert(tk.END, f"Black and white pages ({len(bw_pages)}/{total_pages}): ")
            # Format as comma-separated, with ranges
            result_text.insert(tk.END, format_page_list(bw_pages) + "\n")
    
    result_text.config(state=tk.DISABLED)  # Make read-only again

def format_page_list(page_list):
    """Format a list of page numbers with ranges for consecutive numbers."""
    if not page_list:
        return ""
    
    page_list.sort()
    result = []
    start = page_list[0]
    end = start
    
    for i in range(1, len(page_list)):
        if page_list[i] == end + 1:
            end = page_list[i]
        else:
            if start == end:
                result.append(str(start))
            else:
                result.append(f"{start}-{end}")
            start = end = page_list[i]
    
    # Add the last range or single page
    if start == end:
        result.append(str(start))
    else:
        result.append(f"{start}-{end}")
    
    return ", ".join(result)

def process_pdf(file_path, result_text, status_label, process_button):
    """Process PDF in a separate thread to prevent GUI freeze."""
    def thread_func():
        status_label.config(text=f"Analyzing PDF: {os.path.basename(file_path)}...")
        process_button.config(state=tk.DISABLED)
        
        color_pages, bw_pages = analyze_pdf(file_path)
        
        # Update GUI in the main thread
        status_label.config(text=f"Analysis complete: {os.path.basename(file_path)}")
        process_button.config(state=tk.NORMAL)
        display_results(color_pages, bw_pages, result_text)
    
    threading.Thread(target=thread_func).start()

def select_file(result_text, status_label, process_button):
    """Open file dialog to select PDF file."""
    file_path = filedialog.askopenfilename(
        title="Select PDF File",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    
    if file_path and file_path.lower().endswith('.pdf'):
        process_pdf(file_path, result_text, status_label, process_button)
    elif file_path:  # A file was selected but not a PDF
        messagebox.showerror("Error", "Please select a PDF file.")

def create_gui():
    """Create the GUI."""
    # If TkinterDnD2 is available, use it for drag and drop
    if dnd_available:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    
    root.title("PDF Color Page Analyzer")
    root.geometry("600x500")
    root.minsize(500, 400)
    
    style = ttk.Style()
    style.configure("TFrame", background="#f5f5f5")
    style.configure("TLabel", background="#f5f5f5", font=('Arial', 10))
    style.configure("TButton", font=('Arial', 10))
    
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title and instructions
    ttk.Label(
        main_frame, 
        text="PDF Color Page Analyzer",
        font=('Arial', 16, 'bold')
    ).pack(pady=(0, 10))
    
    ttk.Label(
        main_frame, 
        text="Upload a PDF to analyze which pages are color and which are black and white.",
        wraplength=550
    ).pack(pady=(0, 10))
    
    # Status label
    status_label = ttk.Label(main_frame, text="Ready")
    status_label.pack(pady=(0, 10))
    
    # Frame for drag and drop
    drop_frame = ttk.LabelFrame(main_frame, text="Drag and Drop", padding="10")
    drop_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    drop_label = ttk.Label(
        drop_frame,
        text="Drag and drop PDF file here",
        background="#f0f0f0",
        padding="40",
        anchor="center"
    )
    drop_label.pack(fill=tk.BOTH, expand=True)
    
    # Results text area
    result_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
    result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    result_text = tk.Text(result_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
    result_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    
    # Scrollbar for results
    scrollbar = ttk.Scrollbar(result_frame, command=result_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    result_text.config(yscrollcommand=scrollbar.set)
    
    # Button to select file
    process_button = ttk.Button(
        main_frame,
        text="Select PDF File",
        command=lambda: select_file(result_text, status_label, process_button)
    )
    process_button.pack(pady=10)
    
    # Setup drag and drop functionality if available
    if dnd_available:
        def on_drop(event):
            file_path = event.data
            
            # Handle file path format differences between OS
            if file_path.startswith('{'):
                file_path = file_path.strip('{}')
            
            # Remove prefix on Windows
            if file_path.startswith('file:///'):
                file_path = file_path[8:]
            
            # Replace URL encoding
            file_path = file_path.replace('%20', ' ')
            
            if os.path.isfile(file_path) and file_path.lower().endswith('.pdf'):
                process_pdf(file_path, result_text, status_label, process_button)
            else:
                messagebox.showerror("Error", "Please drop a valid PDF file.")
        
        drop_label.drop_target_register(DND_FILES)
        drop_label.dnd_bind('<<Drop>>', on_drop)
    else:
        drop_label.config(text="Drag and drop not available.\nPlease use the 'Select PDF File' button.")
    
    root.mainloop()

def main():
    create_gui()

if __name__ == "__main__":
    main()