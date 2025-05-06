import streamlit as st
import fitz  # PyMuPDF
import os
import tempfile

def analyze_pdf(file):
    """Analyze PDF to determine which pages are color and which are black and white."""
    try:
        # Create a temporary file to save the uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(file.getbuffer())
            temp_file_path = temp_file.name
        
        doc = fitz.open(temp_file_path)
        color_pages = []
        bw_pages = []
        
        # Create a progress bar
        progress_bar = st.progress(0)
        total_pages = len(doc)
        
        for page_num in range(total_pages):
            # Update progress bar
            progress_bar.progress((page_num + 1) / total_pages)
            
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
        
        # Remove temporary file
        os.unlink(temp_file_path)
        
        return color_pages, bw_pages, total_pages
    
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return [], [], 0

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

def main():
    st.set_page_config(
        page_title="PDF Color Page Analyzer",
        page_icon="📄",
        layout="centered"
    )
    
    st.title("PDF Color Page Analyzer")
    st.write("Upload a PDF to analyze which pages are color and which are black and white.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file is not None:
        with st.spinner("Analyzing PDF..."):
            color_pages, bw_pages, total_pages = analyze_pdf(uploaded_file)
        
        st.success(f"Analysis complete: {uploaded_file.name}")
        
        # Display results
        st.subheader("Results")
        
        if total_pages == 0:
            st.warning("No pages were analyzed. The file might be empty or corrupted.")
        else:
            # Display summary in a colored box
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Pages", total_pages)
            with col2:
                st.metric("Color Pages", len(color_pages))
        
            # Create expandable sections for detailed results
            if color_pages:
                with st.expander("Color Pages", expanded=True):
                    if len(color_pages) == total_pages:
                        st.write(f"All {total_pages} pages contain color.")
                    else:
                        st.write(f"Color pages ({len(color_pages)}/{total_pages}): {format_page_list(color_pages)}")
            
            if bw_pages:
                with st.expander("Black and White Pages", expanded=True):
                    if len(bw_pages) == total_pages:
                        st.write(f"All {total_pages} pages are black and white.")
                    else:
                        st.write(f"Black and white pages ({len(bw_pages)}/{total_pages}): {format_page_list(bw_pages)}")

if __name__ == "__main__":
    main()