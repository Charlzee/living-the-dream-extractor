import os
import time
from playwright.sync_api import sync_playwright

SHOW_WINDOW = False
UPLOAD_TIMEOUT = 100
MAX_RETRY_ATTEMPTS = 25

def remove_dialog(page):
    print("Wiping blocking dialog overlays from DOM...")
    time.sleep(1)  # Let the modal render completely first
    page.evaluate('''() => {
        const dialogs = document.querySelectorAll('dialog');
        dialogs.forEach(d => d.remove());
    }''')
    print("Dialogs removed successfully.")

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

        time.sleep(0.5)
        
        remove_dialog(page)

        print("Waiting for the website interface to load...")
        page.wait_for_selector('input[type="file"]', state="attached", timeout=10000)

        summary_selector = 'summary:has-text("Export")'
        upload_successful = False

        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            print(f"\n[Attempt {attempt}/{MAX_RETRY_ATTEMPTS}] Uploading {input_file}...")
            try:
                page.set_input_files('input[type="file"]', file_path)
                
                print(f"Waiting {UPLOAD_TIMEOUT}ms for the interface to parse save data...")

                page.wait_for_selector(summary_selector, state="attached", timeout=UPLOAD_TIMEOUT)
                
                print("Verification successful! Save layout detected.")
                upload_successful = True
                remove_dialog(page)
                break  # Exit loop early since it found the thing
            except Exception:
                print(f"Warning: Summary element not found within {UPLOAD_TIMEOUT}ms on attempt {attempt}.")

                if attempt < MAX_RETRY_ATTEMPTS:
                    print("Retrying upload...")
                    remove_dialog(page)
                    time.sleep(0.5)

        if not upload_successful:
            print(f"\nError: Failed to verify upload after {MAX_RETRY_ATTEMPTS} attempts. Aborting.")
            context.close()
            browser.close()
            return

        # Click and download
        try:
            time.sleep(0.5) # Pause for UI to load
            print("Opening the collapsed summary menu...")
            page.click(summary_selector, force=True)
            print("Menu expanded successfully.")
        except Exception as e:
            print(f"Could not open menu via text match. Error: {e}")
            print("Attempting fallback to click the first structure summary tag...")
            try:
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
            output_path = os.path.join(os.getcwd(), "exports", "mii_data.json")
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