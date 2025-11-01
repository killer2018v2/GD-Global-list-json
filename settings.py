# --- Основные настройки ---
BASE_URL = "https://demonlist.org"
# Данные теперь будут храниться в папке data/
OUTPUT_FILE = "data/demonlist.json"

# --- Настройки Playwright ---
HEADLESS = False
SLOW_MO = 50

# --- Тайм-ауты (в миллисекундах) ---
PAGE_LOAD_TIMEOUT = 60000
SELECTOR_TIMEOUT = 30000

# --- Настройки умного скролла ---
SCROLL_PAUSE = 0.5
MAX_WAIT_FOR_NEW = 5
MAX_SCROLL_ROUNDS = 200
MAX_NO_NEW_ATTEMPTS = 5
FAST_SCROLLS_PER_STEP = 3
STUCK_CARD_MULTIPLE = 150


# --- Настройки Github ---
GITHUB_RAW_URL = "https://raw.githubusercontent.com/НИК/НАЗВАНИЕ ПРОЕКТА/main/data/demonlist.json"
LOCAL_DATA_PATH = "data/demonlist.json"

