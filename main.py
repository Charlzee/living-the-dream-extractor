import os
import time
from playwright.sync_api import sync_playwright

def run_extractor():
    # Define file names
    input_file = "Mii.sav"

    if not os.path.exists(input_file):
        print(f"Error: Place your '{input_file}' file in this exact folder first!")
        return

    file_path = os.path.abspath(input_file)

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True) 

        print("Clearing browser cache and creating a fresh session...")
        context = browser.new_context(
            no_viewport=False,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        context.clear_cookies()

        page = context.new_page()
        
        # Open the save editor
        print("Navigating to LTD Save Editor...")
        page.goto("https://ltdsave.app/mii")
        
        print("Waiting for the website interface to load...")
        page.wait_for_selector('input[type="file"]', state="attached", timeout=10000)

        # Upload
        print(f"Uploading {input_file}...")
        page.set_input_files('input[type="file"]', file_path)

        print("Wiping blocking dialog overlays from DOM...")
        
        time.sleep(1)  # Let the modal render completely first
        
        page.evaluate('''() => {
            const dialogs = document.querySelectorAll('dialog');
            dialogs.forEach(d => d.remove());
        }''')
        print("Dialogs removed successfully.")

        summary_selector = 'summary:has-text("Export")'

        print("Waiting for the app to finish processing and loading the save data...")
        try:
            # Give the website 15 seconds to parse the data
            page.wait_for_selector(summary_selector, state="visible", timeout=15000)
            
            time.sleep(0.5) # Pause for UI to load
            
            print("Opening the collapsed summary menu...")
            page.click(summary_selector, force=True)
            print("Menu expanded successfully.")
        except Exception as e:
            print(f"Could not open menu via text match. Error: {e}")
            print("Attempting fallback to click the first structure summary tag...")
            try:
                # Fallback: click the first summary block on the page
                page.click('details summary', force=True)
                print("Fallback menu expand triggered.")
            except Exception as fallback_err:
                print(f"Fallback also failed: {fallback_err}")
        
        time.sleep(0.5)
        
        # Handle the file download for the JSON
        button_text = "Full snapshot (JSON)"
        print(f"Attempting to download '{button_text}'...")
        
        try:
            with page.expect_download() as download_info:
                page.click(f'button:has-text("{button_text}")', force=True)
            
            download = download_info.value
            output_path = os.path.join(os.getcwd(), "exports", download.suggested_filename)
            download.save_as(output_path)
            
            print("\n" + "="*40)
            print(f"SUCCESS! Extracted file saved to:\n{output_path}")
            print("="*40 + "\n")
            
        except Exception as e:
            print(f"\nFailed to extract snapshot data: {e}")
        
        # Shutdown of the context and browser
        context.close()
        browser.close()

if __name__ == "__main__":
    run_extractor()