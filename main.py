import os
import time
from playwright.sync_api import sync_playwright

SHOW_WINDOW = False

def run_extractor():
    user_profile = os.environ.get("USERPROFILE") # Gets "C:\Users\<CurrentName>"
    
    save_folder = os.path.join(
        user_profile, 
        "AppData", "Roaming", "Ryujinx", "bis", "user", "save", "0000000000000001", "0"
    )
    
    input_file = "Mii.sav"
    file_path = os.path.join(save_folder, input_file)

    # Check if Ryujinx has a save file for LTD
    if not os.path.exists(file_path):
        print(f"Error: Could not find your save file at:\n{file_path}")
        print("Attempting to find local Mii.sav...")
        file_path = os.path.join(os.getcwd(), input_file)
        if not os.path.exists(file_path):
            print("No local file found!")
            return

    print(f"Found save file at: {file_path}")

    with sync_playwright() as p:
        print("Launching optimized browser...")
        
        # Low RAM flags
        low_ram_args = [
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--js-flags='--max-old-space-size=256'",
            "--disable-extensions",
            "--blink-settings=imagesEnabled=false",
        ]

        browser = p.chromium.launch(
            headless=not SHOW_WINDOW,
            args=low_ram_args
        ) 

        print("Clearing browser cache and creating a fresh session...")
        context = browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        context.clear_cookies()

        page = context.new_page()

        # Block everything except the structure and engine scripts
        def block_bloat_assets(route):
            allowed_types = ["document", "script", "xhr", "fetch"]
            if route.request.resource_type not in allowed_types:
                route.abort()
            else:
                route.continue_()
        
        page.route("**/*", block_bloat_assets)
        
        # Open the save editor
        print("Navigating to LTD Save Editor...")
        page.goto("https://ltdsave.app/mii")

        print("Removing images...")
        try:
            page.evaluate('''() => {
                const imgs = document.querySelectorAll('img, svg, picture, canvas');
                imgs.forEach(i => i.remove());

                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    if (el.style && el.style.backgroundImage) {
                        el.style.backgroundImage = 'none';
                    }
                });
            }''')
        except Exception as e:
            print(f"Warning during visual cleanup: {e}")

        time.sleep(0.5)

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
            page.wait_for_selector(summary_selector, state="attached", timeout=15000)
            
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