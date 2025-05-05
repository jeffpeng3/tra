from recognizer.agents.playwright import SyncChallenger
from camoufox.sync_api import Camoufox

with Camoufox() as browser:
    page = browser.new_page()
    challenger = SyncChallenger(page, click_timeout=1000)
    page.goto("https://example.com")