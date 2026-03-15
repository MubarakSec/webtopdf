import sys
import argparse
from src.gui.app import WebToPDFApp
from src.utils.logger import app_logger

def main():
    parser = argparse.ArgumentParser(description="Web to PDF Toolkit - Pro")
    parser.add_argument(
        "--tab", 
        choices=["extract", "convert"], 
        default="extract",
        help="The tab to open by default (extract or convert)."
    )
    
    args = parser.parse_args()

    try:
        app_logger.info("Starting WebToPDF application...")
        app_logger.debug(f"Startup arguments: {args}")
        app = WebToPDFApp(start_tab=args.tab)
        app.mainloop()
        app_logger.info("Application closed normally.")
    except Exception as e:
        app_logger.critical(f"Fatal error starting application: {e}", exc_info=True)
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
