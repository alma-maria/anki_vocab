"""Short and long word descriptions from vocabulary.com.

The site blocks plain HTTP clients, so a real Chrome is driven through
Selenium. One browser session is reused for all words.
"""

import random
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.vocabulary.com/dictionary/{word}"


class VocabularyCom:
    def __init__(self, headless=False, timeout=10, delay=(1.0, 3.0)):
        self.headless = headless
        self.timeout = timeout
        self.delay = delay
        self.driver = None

    def __enter__(self):
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1280,900")
        # Selenium Manager (built into Selenium 4.6+) finds or downloads chromedriver.
        self.driver = webdriver.Chrome(options=options)
        return self

    def __exit__(self, *exc):
        if self.driver is not None:
            self.driver.quit()

    def lookup(self, word):
        """Return {"short": ..., "long": ...}; missing parts are empty strings.

        Raises LookupError if the page has no description at all
        (unknown word, or a redirect to a different headword).
        """
        self.driver.get(URL.format(word=word))
        try:
            short = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p.short"))
            ).text.strip()
        except TimeoutException:
            short = ""
        long_ = self._text("p.long")
        time.sleep(random.uniform(*self.delay))  # be polite to the site

        if not short and not long_:
            raise LookupError("no description on vocabulary.com")
        return {"short": short, "long": long_}

    def _text(self, selector):
        found = self.driver.find_elements(By.CSS_SELECTOR, selector)
        return found[0].text.strip() if found else ""
