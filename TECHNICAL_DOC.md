# TÀI LIỆU KỸ THUẬT — AUTOMATION CONTROL CENTER

> Tài liệu chi tiết giải thích kiến trúc, class, thuộc tính, function, logic, và cách vận hành của toàn bộ hệ thống.

---

## MỤC LỤC

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Cấu trúc thư mục](#2-cấu-trúc-thư-mục)
3. [Lớp cấu hình — `config/config.py`](#3-lớp-cấu-hình--configconfigpy)
4. [Tiện ích — `utils/`](#4-tiện-ích--utils)
5. [Lớp nền tảng — `pages/base_page.py`](#5-lớp-nền-tảng--pagesbase_pagepy)
6. [Core Engine — `core/generic_runner.py`](#6-core-engine--coregeneric_runnerpy)
7. [E2E Runner — `core/e2e_runner.py`](#7-e2e-runner--coree2e_runnerpy)
8. [Setup Runner — `core/setup_runner.py`](#8-setup-runner--coresetup_runnerpy)
9. [Screenshot Manager — `core/screenshot_manager.py`](#9-screenshot-manager--corescreenshot_managerpy)
10. [Report Generator — `core/report_generator.py`](#10-report-generator--corereport_generatorpy)
11. [Performance Monitor — `core/performance_monitor.py`](#11-performance-monitor--coreperformance_monitorpy)
12. [API Tester — `core/api_tester.py`](#12-api-tester--coreapi_testerpy)
13. [DB Verifier — `core/db_verifier.py`](#13-db-verifier--coredb_verifierpy)
14. [Test Scheduler — `core/test_scheduler.py`](#14-test-scheduler--coretest_schedulerpy)
15. [Test History — `core/test_history.py`](#15-test-history--coretest_historypy)
16. [CLI Runner — `core/cli_runner.py`](#16-cli-runner--corecli_runnerpy)
17. [AI Generator — `core/ai_generator.py`](#17-ai-generator--coreai_generatorpy)
18. [AI Auto-Heal — `core/ai_auto_heal.py`](#18-ai-auto-heal--coreai_auto_healpy)
19. [AI Test Suggestion — `core/ai_test_suggestion.py`](#19-ai-test-suggestion--coreai_test_suggestionpy)
20. [AI Natural Language — `core/ai_natural_language.py`](#20-ai-natural-language--coreai_natural_languagepy)
21. [Logic Manager — `logic_manager.py`](#21-logic-manager--logic_managerpy)
22. [UI Layer — `ui/`](#22-ui-layer--ui)
23. [Pytest Configuration — `conftest.py`](#23-pytest-configuration--conftestpy)
24. [Dependencies — `requirements.txt`](#24-dependencies--requirementstxt)
25. [Sơ đồ luồng dữ liệu](#25-sơ-đồ-luồng-dữ-liệu)
26. [Design Patterns sử dụng](#26-design-patterns-sử-dụng)
27. [Xử lý lỗi toàn hệ thống](#27-xử-lý-lỗi-toàn-hệ-thống)

---

## 1. Tổng quan kiến trúc

Hệ thống được thiết kế theo kiến trúc **multi-layer** với sự tách biệt rõ ràng giữa các tầng:

```
┌─────────────────────────────────────────────────────────┐
│                    UI Layer (Tkinter)                    │
│  main_window → 8 tabs (Notebook)                        │
│  locator_panel │ test_runner │ action_mgr │ api_testing  │
│  db_panel │ scheduler_panel │ history_panel │ ai_tools   │
├─────────────────────────────────────────────────────────┤
│               Logic Layer (Orchestration)                │
│  logic_manager.py — AutomationLogic                     │
│  Kết nối UI ↔ Core, xử lý scan, save, merge            │
├─────────────────────────────────────────────────────────┤
│                   Core Layer (Engine)                    │
│  generic_runner │ e2e_runner │ setup_runner              │
│  screenshot_mgr │ report_gen │ perf_monitor              │
│  api_tester │ db_verifier │ scheduler │ history          │
│  cli_runner │ ai_generator │ ai_auto_heal                │
│  ai_test_suggestion │ ai_natural_language                │
├─────────────────────────────────────────────────────────┤
│                 Foundation Layer                         │
│  config/config.py │ utils/logger.py │ utils/helpers.py  │
│  pages/base_page.py                                     │
├─────────────────────────────────────────────────────────┤
│                External Dependencies                    │
│  Playwright │ Gemini AI │ Pillow │ pandas │ pytest      │
└─────────────────────────────────────────────────────────┘
```

**Nguyên tắc thiết kế:**
- **Separation of Concerns**: Mỗi module xử lý một nhiệm vụ duy nhất
- **Dependency Injection**: Các runner nhận `page` object từ bên ngoài (pytest fixture)
- **Strategy Pattern**: AI fallback models, adaptive pipeline, heuristic/AI healing
- **Observer Pattern**: Callback trong scheduler, UI event binding
- **Factory Pattern**: Database connection dựa trên `db_type`

---

## 2. Cấu trúc thư mục

```
workspace_project_testing_tool/
├── config/
│   ├── config.py               # Cấu hình toàn cục (env vars, paths)
│   └── actions_config.json     # Định nghĩa actions + Playwright functions
├── core/
│   ├── generic_runner.py       # Runner đơn trang
│   ├── e2e_runner.py           # Runner đa trang (E2E)
│   ├── setup_runner.py         # Chạy setup scripts trước test
│   ├── screenshot_manager.py   # Chụp screenshot, visual regression
│   ├── report_generator.py     # Tạo báo cáo HTML/JSON
│   ├── performance_monitor.py  # Đo performance (timing, page load)
│   ├── api_tester.py           # Test API (REST/GraphQL)
│   ├── db_verifier.py          # Kiểm tra database
│   ├── test_scheduler.py       # Lên lịch chạy test tự động
│   ├── test_history.py         # Lịch sử kết quả test
│   ├── cli_runner.py           # CLI cho CI/CD
│   ├── ai_generator.py         # AI tạo test artifacts (pipeline)
│   ├── ai_auto_heal.py         # AI tự sửa locators bị lỗi
│   ├── ai_test_suggestion.py   # AI gợi ý test dựa trên git diff
│   └── ai_natural_language.py  # AI chuyển ngôn ngữ tự nhiên → template
├── pages/
│   └── base_page.py            # Page Object Model base class
├── ui/
│   ├── main_window.py          # Cửa sổ chính, 8 tab Notebook
│   ├── locator_panel.py        # Tab quét & chỉnh sửa locators
│   ├── test_runner_panel.py    # Tab chạy test
│   ├── action_manager_panel.py # Tab quản lý actions
│   ├── api_testing_panel.py    # Tab test API
│   ├── db_panel.py             # Tab kiểm tra DB
│   ├── scheduler_panel.py      # Tab lên lịch
│   ├── history_panel.py        # Tab lịch sử
│   └── ai_tools_panel.py       # Tab AI tools (3 sub-tabs)
├── utils/
│   ├── logger.py               # Logging (loguru)
│   └── helpers.py              # Hàm tiện ích (đọc Excel, JSON, screenshot)
├── tests/
│   ├── test_main.py            # Test file cho single-page mode
│   └── test_e2e.py             # Test file cho E2E mode
├── locators/                   # Locator JSON files (theo domain/page)
├── templates/                  # Workflow template JSON files
├── test_data/                  # Test data Excel files
├── scripts/setup/              # Setup scripts (JSON/Python)
├── reports/                    # Output: HTML, JSON, screenshots, logs
├── conftest.py                 # Pytest fixtures & hooks
├── logic_manager.py            # Tầng logic (orchestration)
├── main_ui.py                  # Entry point
└── requirements.txt            # Dependencies
```

---

## 3. Lớp cấu hình — `config/config.py`

### Mục đích
Tập trung toàn bộ cấu hình hệ thống vào một nơi duy nhất. Đọc biến môi trường (env vars) để cho phép override từ bên ngoài (CLI, CI/CD, Docker).

### Class `Config`

```python
class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent  # Root dự án
```

**Thuộc tính tĩnh (class-level):**

| Thuộc tính | Kiểu | Mô tả | Giá trị mặc định |
|---|---|---|---|
| `BASE_DIR` | `Path` | Đường dẫn gốc dự án | Tự động từ vị trí file |
| `TIMEOUT` | `int` | Timeout mặc định (ms) cho Playwright | `30000` |
| `GEMINI_API_KEY` | `str` | API key cho Google Gemini | `""` (rỗng) |
| `AI_MODEL` | `str` | Tên model AI mặc định | `"gemini-1.5-flash"` |
| `REPORTS_DIR` | `Path` | Thư mục lưu báo cáo | `BASE_DIR / "reports"` |
| `TEST_DATA_DIR` | `Path` | Thư mục dữ liệu test | `BASE_DIR / "test_data"` |
| `SCREENSHOTS_DIR` | `Path` | Thư mục screenshot | `REPORTS_DIR / "screenshots"` |
| `LOCATORS_DIR` | `Path` | Thư mục locator JSON | `BASE_DIR / "locators"` |
| `TEMPLATES_DIR` | `Path` | Thư mục template JSON | `BASE_DIR / "templates"` |

**Phương thức tĩnh (đọc từ env vars):**

| Method | Return | Env Var | Mô tả |
|---|---|---|---|
| `get_base_url()` | `str \| None` | `BASE_URL` | URL mục tiêu test |
| `get_base_browser()` | `str` | `BROWSER` | Trình duyệt (chromium/firefox/webkit) |
| `get_selected_test_data()` | `str \| None` | `SELECTED_TEST_DATA` | Tên file dữ liệu test |
| `get_selected_sheet()` | `str` | `SHEET_NAME` | Tên sheet Excel |
| `get_headless()` | `bool` | `HEADLESS` | Chạy headless hay không |
| `get_page_id()` | `str` | `PAGE_ID` | ID trang cần test |
| `validate_config()` | `None` | — | In ra log trạng thái cấu hình |

**Logic khởi tạo:**
1. Tính `BASE_DIR` từ vị trí file `config.py`
2. Load file `.env` (nếu tồn tại) bằng `python-dotenv`, `override=False` → env vars đã set sẽ không bị ghi đè
3. Gọi `validate_config()` ngay khi module được import → log thông tin cấu hình

---

## 4. Tiện ích — `utils/`

### 4.1 `utils/logger.py`

**Mục đích**: Cung cấp logger toàn cục sử dụng thư viện `loguru`.

**Hàm `setup_logger()`**:
- Tạo thư mục `reports/logs/` nếu chưa tồn tại
- Cấu hình 2 handler:
  - **Console** (`sys.stdout`): level `INFO`, format có màu (green timestamp, cyan module info)
  - **File** (`reports/logs/log_YYYY-MM-DD_HH-MM-SS.log`): level `DEBUG`, encoding UTF-8, rotation 10MB, giữ 30 ngày
- Trả về `logger` instance → export dưới tên `log`

**Sử dụng**: `from utils.logger import log` → `log.info(...)`, `log.error(...)`, `log.debug(...)`

### 4.2 `utils/helpers.py`

#### Class `Helpers`

**Phương thức tĩnh:**

| Method | Tham số | Return | Mô tả |
|---|---|---|---|
| `read_excel_data()` | `file_name`, `site_folder=None`, `max_show=10` | `list[dict]` | Đọc file Excel → list of dicts |
| `load_json_config()` | `file_path` | `dict \| None` | Đọc file JSON config |
| `capture_screenshot()` | `page`, `name` | `str \| None` | Chụp screenshot Playwright |

**Logic `read_excel_data()`:**
1. Nếu có `site_folder`: chuyển domain → folder name (thay `.` → `_`, bỏ ký tự đặc biệt)
2. Tìm file tại `test_data/{site_folder}/{file_name}`
3. Đọc bằng `pandas.read_excel(dtype=str)` → giữ tất cả dưới dạng string
4. `fillna("")` → thay `NaN` bằng chuỗi rỗng
5. Chuyển sang `list[dict]` bằng `to_dict(orient='records')`
6. In preview (tối đa `max_show` dòng) ra console

---

## 5. Lớp nền tảng — `pages/base_page.py`

### Mục đích
Implement **Page Object Model (POM)** pattern — đóng gói tất cả tương tác với browser thông qua Playwright API.

### Class `BasePage`

```python
class BasePage:
    def __init__(self, page: Page):
        self.page = page  # Playwright Page instance
```

**Thuộc tính:**

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `page` | `playwright.sync_api.Page` | Instance trang Playwright |

**Phương thức — Tương tác cơ bản:**

| Method | Tham số | Playwright API | Mô tả |
|---|---|---|---|
| `navigate()` | `url=""` | `page.goto()` | Điều hướng đến URL |
| `click()` | `selector, name=""` | `page.click()` | Click vào element |
| `dblclick()` | `selector, name=""` | `page.dblclick()` | Double-click |
| `fill()` | `selector, value, name=""` | `page.fill()` | Nhập text vào input |
| `check()` | `selector, name=""` | `page.check()` | Check checkbox |
| `uncheck()` | `selector, name=""` | `page.uncheck()` | Uncheck checkbox |
| `hover()` | `selector, name=""` | `page.hover()` | Hover lên element |
| `press()` | `selector, value, name=""` | `page.press()` | Nhấn phím (Enter, Tab, ...) |
| `type()` | `selector, value, name=""` | `page.type()` | Gõ từng ký tự (keyboard) |
| `select_option()` | `selector, value, name=""` | `page.select_option()` | Chọn option trong `<select>` |
| `set_input_files()` | `selector, value, name=""` | `page.set_input_files()` | Upload file |
| `wait_for_timeout()` | `value, name=""` | `page.wait_for_timeout()` | Chờ N milliseconds |
| `wait_for_selector()` | `selector, name=""` | `page.wait_for_selector()` | Chờ element xuất hiện |

**Phương thức — Kiểm tra (Assertions):**

| Method | Tham số | Return | Mô tả |
|---|---|---|---|
| `inner_text()` | `selector, value, name=""` | — (assert) | Kiểm tra text chứa `value` (case-insensitive) |
| `is_visible()` | `selector, name=""` | — (assert) | Kiểm tra element hiển thị |
| `verify_url()` | `expected_url` | — (assert) | Kiểm tra URL hiện tại chứa `expected_url` |

**Phương thức — Query:**

| Method | Tham số | Return | Mô tả |
|---|---|---|---|
| `get_text()` | `selector` | `str` | Lấy text của element |
| `get_element_snapshot()` | `selector` | `dict` | Lấy tag, text, class, id, is_visible |
| `wait_for_element()` | `selector, timeout=10000` | — | Chờ element (không throw) |

**Mẫu xử lý lỗi chung** (áp dụng cho tất cả phương thức tương tác):
```python
def click(self, selector, name=""):
    display_name = name if name else selector
    try:
        log.info(f"Click vao: {display_name}")
        self.page.click(selector)
    except Exception as e:
        log.error(f"Loi khi click: {display_name}: {str(e)}")
        raise  # Re-raise để GenericRunner bắt được
```

---

## 6. Core Engine — `core/generic_runner.py`

### Mục đích
Runner chính cho chế độ **single-page**: thực thi một workflow trên một trang duy nhất, dựa trên template JSON + locators JSON + dữ liệu Excel.

### Class `GenericRunner`

```python
class GenericRunner:
    def __init__(self, page, site_name, page_id):
```

**Thuộc tính:**

| Thuộc tính | Kiểu | Mô tả | Nguồn |
|---|---|---|---|
| `page` | `Page` | Playwright page instance | Constructor |
| `site_name` | `str` | Tên domain (đã chuyển đổi) | Constructor |
| `page_id` | `str` | ID trang (vd: `"login"`) | Constructor |
| `base_page` | `BasePage` | Instance POM wrapper | Tạo trong `__init__` |
| `screenshot_mgr` | `ScreenshotManager` | Quản lý screenshot | Tạo trong `__init__` |
| `perf_monitor` | `PerformanceMonitor` | Đo hiệu năng | Tạo trong `__init__` |
| `auto_heal` | `AIAutoHeal \| None` | AI auto-heal (tùy chọn) | Set từ bên ngoài |
| `step_results` | `list[dict]` | Kết quả từng bước | Cập nhật trong `_execute_step` |
| `locators` | `dict` | Locators JSON đã load | Load từ `locators/{site}/{page_id}.json` |
| `workflow` | `dict` | Template JSON đã load | Load từ `templates/{site}/{page_id}_workflow.json` |

**Phương thức chính:**

#### `run_test(test_data: dict) → bool`

Luồng thực thi:
```
1. Kiểm tra locators & workflow tồn tại → log error nếu thiếu
2. Reset step_results = []
3. Navigate đến URL từ workflow (nếu có)
4. Đo page load performance (measure_page_load)
5. Lặp qua từng step trong workflow["steps"]:
   └── Gọi _execute_step(step, test_data)
6. Return True nếu tất cả thành công
7. Nếu exception: chụp screenshot lỗi → re-raise
```

#### `_execute_step(step: dict, test_data: dict)`

Luồng xử lý:
```
1. Trích step_id, action, data_key từ step
2. Tra locator: locators[step_id] → selector, name
3. Lấy value: ưu tiên test_data[data_key], sau đó step["value"]
4. Kiểm tra selector (bỏ qua nếu action là wait/verify_url/navigate)
5. perf_monitor.start_step()
6. TRY:
   └── _dispatch_action(action, selector, value, ...)
   └── perf_monitor.end_step(success=True)
   └── Ghi step_results: status="passed"
7. CATCH Exception:
   └── perf_monitor.end_step(success=False)
   └── screenshot_mgr.capture_on_failure()
   └── NẾU auto_heal != None VÀ lỗi là "Khong tim thay" hoặc "Timeout":
       └── auto_heal.try_heal() → thử selector mới
       └── Nếu heal thành công: retry action → status="healed"
   └── Nếu không heal được: status="failed" → re-raise
```

#### `_dispatch_action(action, selector, value, step_name, step_id, data_key, test_data)`

Bảng dispatch action → BasePage method:

| Action | BasePage method | Ghi chú |
|---|---|---|
| `click` | `click()` | — |
| `dblclick` | `dblclick()` | — |
| `fill` | `fill()` | — |
| `fill_password` | `fill()` | Tương tự fill |
| `check` | `check()` | — |
| `uncheck` | `uncheck()` | — |
| `hover` | `hover()` | — |
| `press` | `press()` | value = tên phím |
| `type` | `type()` | — |
| `select` | `page.select_option()` | Gọi trực tiếp |
| `set_input_files` | `set_input_files()` | — |
| `verify_text` | `get_element_snapshot()` + assert | So sánh case-insensitive |
| `verify_visible` | `is_visible()` + assert | — |
| `verify_url` | `verify_url()` | — |
| `wait` | `page.wait_for_timeout()` | value ms, default 2000 |
| `wait_for_selector` | `wait_for_selector()` | — |
| `navigate` | `navigate()` | — |

---

## 7. E2E Runner — `core/e2e_runner.py`

### Mục đích
Runner cho chế độ **multi-page E2E**: thực thi workflow trải qua nhiều trang, browser session giữ nguyên (persistent) khi chuyển trang.

### Class `E2ERunner`

```python
class E2ERunner:
    def __init__(self, page, site_name, workflow_path):
```

**Thuộc tính:**

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `page` | `Page` | Playwright page (persistent) |
| `site_name` | `str` | Tên domain |
| `base_page` | `BasePage` | POM wrapper |
| `workflow` | `dict` | Workflow JSON đã load |
| `page_locators` | `dict[str, dict]` | Locators cho TẤT CẢ pages. Key = page_id |

**Khác biệt so với GenericRunner:**

| Đặc điểm | GenericRunner | E2ERunner |
|---|---|---|
| Locators | 1 page_id | Nhiều page_id (dict of dicts) |
| Workflow | `workflow["steps"]` | `workflow["steps"]` + `step["page_id"]` |
| Browser session | Mỗi test mới | Persist xuyên suốt |
| Navigation | 1 URL ban đầu | `start_url` + step-level URL |

**Logic `__init__`:**
1. Load workflow từ `workflow_path`
2. Đọc `workflow["pages"]` → list page_id
3. Lặp qua từng page_id → load `locators/{site}/{page_id}.json`
4. Lưu vào `page_locators[page_id]` = locator dict

**Logic `run_test(test_data)`:**
```
1. Navigate đến start_url
2. current_page_id = None
3. Lặp qua từng step (có index i):
   a. step_page_id = step["page_id"] (hoặc giữ current)
   b. NẾU page_id thay đổi:
      └── Log "Chuyen sang trang: {page_id}"
      └── Navigate nếu step có URL
   c. _execute_step(step, test_data, page_id, i, total)
4. Return True nếu thành công
```

**Logic `_execute_step()`:**
- Tương tự GenericRunner nhưng: `locators = self.page_locators[page_id]`
- Mỗi step tra locator từ page_id tương ứng → cho phép reuse locators trên nhiều trang

---

## 8. Setup Runner — `core/setup_runner.py`

### Mục đích
Chạy các script chuẩn bị trước khi scan URL hoặc chạy test (ví dụ: login, đóng banner GDPR, dismiss popup).

### Class `SetupRunner`

**Thuộc tính class-level:**
```python
SUPPORTED_ACTIONS = {"navigate", "click", "fill", "fill_password",
                     "wait", "select", "check", "uncheck", "press", "hover"}
```

**Phương thức tĩnh:**

#### `list_scripts(project_path) → list[str]`
- Quét thư mục `scripts/setup/`
- Trả về danh sách file `.json` và `.py` (không bắt đầu bằng `_`)
- Sắp xếp theo tên

#### `run(page, script_path) → bool`
Logic phân nhánh theo đuôi file:
- `.json` → `_run_json(page, script_path)`
- `.py` → `_run_python(page, script_path)`
- Khác → log error, return False

#### `_run_json(page, script_path) → bool`
Format JSON setup script:
```json
{
  "name": "Login saucedemo",
  "steps": [
    {"action": "navigate", "value": "https://www.saucedemo.com/"},
    {"action": "fill", "selector": "#user-name", "value": "standard_user"},
    {"action": "click", "selector": "#login-button"}
  ]
}
```

Logic thực thi:
1. Đọc JSON → lấy `steps`
2. Lặp qua từng step → dispatch action:
   - `navigate`: `page.goto(value, timeout=60000)`
   - `fill`/`fill_password`: `page.wait_for_selector()` → `page.fill()`
   - `click`: `page.wait_for_selector()` → `page.click()`
   - `wait`: `page.wait_for_timeout(ms)`
   - Tương tự cho `select`, `check`, `uncheck`, `press`, `hover`
3. Mỗi action có `wait_for_selector` timeout 10s trước khi tương tác

#### `_run_python(page, script_path) → bool`
1. Load module Python bằng `importlib.util.spec_from_file_location()`
2. Kiểm tra module có hàm `run` → error nếu không có
3. Gọi `module.run(page)` — truyền Playwright page object
4. Python script tự do tương tác với page qua API Playwright

---

## 9. Screenshot Manager — `core/screenshot_manager.py`

### Mục đích
Quản lý screenshot: chụp khi test fail, chụp từng bước, lưu baseline, so sánh visual regression.

### Class `ScreenshotManager`

```python
class ScreenshotManager:
    def __init__(self, reports_dir: str = "reports"):
```

**Thuộc tính:**

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `reports_dir` | `Path` | Thư mục gốc báo cáo |
| `screenshots_dir` | `Path` | `reports/screenshots/` |
| `baseline_dir` | `Path` | `reports/visual_baseline/` |
| `diff_dir` | `Path` | `reports/visual_diff/` |

**Phương thức:**

#### `capture_on_failure(page, step_id, page_id, error_msg="") → str`
- Tên file: `FAIL_{page_id}_{step_id}_{timestamp}.png`
- Chụp `full_page=True` (toàn trang)
- Return đường dẫn file, hoặc `""` nếu lỗi
- **Trigger**: Được gọi bởi `GenericRunner._execute_step()` khi step fail

#### `capture_step(page, step_id, page_id) → str`
- Tên file: `STEP_{page_id}_{step_id}_{timestamp}.png`
- Chụp viewport hiện tại (không full_page)
- Dùng cho báo cáo từng bước

#### `save_baseline(page, page_id) → str`
- Tên file: `{page_id}_baseline.png`
- Chụp `full_page=True`
- Lưu vào `visual_baseline/` → làm chuẩn để so sánh

#### `compare_visual(page, page_id, threshold=0.05) → dict`
**Thuật toán Visual Regression:**
```
1. Tìm baseline: visual_baseline/{page_id}_baseline.png
2. Nếu không có baseline → return {match: False, error: "Khong tim thay"}
3. Chụp screenshot hiện tại → visual_diff/{page_id}_current_{timestamp}.png
4. Gọi _compare_images():
   a. Mở 2 ảnh bằng PIL (Pillow)
   b. Chuyển cả 2 sang RGB
   c. Resize nếu khác kích thước
   d. ImageChops.difference() → ảnh diff pixel-by-pixel
   e. Đếm pixel khác: pixel có tổng RGB > 30 = "khác"
   f. diff_pct = diff_pixels / total_pixels
   g. Nếu diff_pct > 0: lưu ảnh diff
5. match = diff_pct <= threshold (mặc định 5%)
6. Return dict: {match, diff_percentage, baseline_path, current_path, diff_image}
```

**Return dict:**

| Key | Kiểu | Mô tả |
|---|---|---|
| `match` | `bool` | True nếu ảnh giống (trong threshold) |
| `diff_percentage` | `float` | Phần trăm pixel khác (0.0 - 1.0) |
| `diff_image` | `str` | Path đến ảnh diff (nếu có khác biệt) |
| `baseline_path` | `str` | Path baseline |
| `current_path` | `str` | Path ảnh hiện tại |
| `error` | `str` | Thông báo lỗi (nếu có) |

---

## 10. Report Generator — `core/report_generator.py`

### Mục đích
Tạo báo cáo HTML/JSON chi tiết sau khi chạy test, bao gồm thống kê, screenshot lỗi, và chi tiết từng bước.

### Data Classes

#### Class `TestResult`
```python
class TestResult:
    def __init__(self, test_name: str, page_id: str = ""):
```

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `test_name` | `str` | Tên test case |
| `page_id` | `str` | ID trang |
| `status` | `str` | `"pending"`, `"running"`, `"passed"`, `"failed"`, `"skipped"` |
| `start_time` | `datetime \| None` | Thời gian bắt đầu |
| `end_time` | `datetime \| None` | Thời gian kết thúc |
| `duration_ms` | `int` | Thời gian chạy (ms) |
| `steps` | `list[StepResult]` | Kết quả từng bước |
| `error_message` | `str` | Thông báo lỗi |
| `screenshot_path` | `str` | Path screenshot lỗi |

Methods: `start()`, `finish(passed, error, screenshot)`, `to_dict()`

#### Class `StepResult`
```python
class StepResult:
    def __init__(self, step_id: str, action: str):
```

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `step_id` | `str` | ID bước |
| `action` | `str` | Loại action |
| `status` | `str` | `"passed"`, `"failed"` |
| `duration_ms` | `int` | Thời gian (ms) |
| `error_message` | `str` | Lỗi (nếu có) |
| `screenshot_path` | `str` | Screenshot (nếu có) |

### Class `ReportGenerator`

```python
class ReportGenerator:
    def __init__(self, reports_dir: str = "reports"):
```

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `reports_dir` | `Path` | Thư mục gốc |
| `html_dir` | `Path` | `reports/html/` |

#### `generate_html(results, suite_name, start_time, end_time) → str`

Luồng xử lý:
```
1. Tạo thư mục html_dir nếu chưa có
2. Tính toán thống kê:
   - total, passed, failed, skipped
   - total_duration, pass_rate
3. Tạo filename: report_{timestamp}.html
4. Tạo JSON data → lưu report_{timestamp}.json (song song)
5. Gọi _build_html() → tạo chuỗi HTML
6. Ghi file HTML
7. Return đường dẫn HTML
```

#### `_build_html(data, results) → str`

Cấu trúc HTML output:
```
├── Header (gradient purple, tên suite + timestamp)
├── Stats Cards (4 cards: Tổng số, Thành công, Thất bại, Thời gian)
├── Progress Bar (thanh % thành công, màu xanh lá)
├── Bảng kết quả chi tiết:
│   ├── Test Case │ Page │ Trạng thái │ Thời gian │ Screenshot
│   ├── Mỗi row có class CSS (passed=xanh, failed=đỏ)
│   ├── Error message (nếu có) → khối đỏ monospace
│   └── Chi tiết bước (collapsible <details>) → bảng phụ
└── Footer (timestamp)
```

CSS đi kèm: modern styling với gradient, shadow, border-radius.

---

## 11. Performance Monitor — `core/performance_monitor.py`

### Mục đích
Thu thập metrics hiệu năng: thời gian từng bước test, page load timing (Navigation Timing API), resource loading.

### Class `PerformanceMonitor`

```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = []         # list[dict] — tất cả metrics
        self._current_step = None # step_id đang đo
        self._step_start = None   # time.perf_counter() bắt đầu
```

**Phương thức:**

#### `start_step(step_id, action)` / `end_step(step_id, success=True)`
- Sử dụng `time.perf_counter()` cho độ chính xác cao
- Mỗi step ghi: `{step_id, duration_ms, success, timestamp}`
- GenericRunner gọi cặp này bao quanh mỗi action

#### `measure_page_load(page, url="") → dict`
**Sử dụng Navigation Timing API** thông qua `page.evaluate()`:

```javascript
performance.getEntriesByType('navigation')[0]
```

Metrics thu thập:

| Metric | Công thức | Ý nghĩa |
|---|---|---|
| `dns` | `domainLookupEnd - domainLookupStart` | DNS resolution |
| `tcp` | `connectEnd - connectStart` | TCP handshake |
| `ttfb` | `responseStart - requestStart` | Time to First Byte |
| `download` | `responseEnd - responseStart` | Response download |
| `dom_interactive` | `domInteractive - navigationStart` | DOM interactive |
| `dom_complete` | `domComplete - navigationStart` | DOM fully loaded |
| `load_event` | `loadEventEnd - navigationStart` | Window load event |
| `total` | `loadEventEnd - navigationStart` | Tổng thời gian |

#### `measure_resource_count(page) → dict`
Đếm resources đã load:
```javascript
performance.getEntriesByType('resource')
```
Return: `{total, by_type: {img: N, script: N, ...}, total_size_kb}`

#### `get_summary() → dict`
Tổng hợp:
- `total_steps_measured`: Số bước đã đo
- `avg_step_duration_ms`: Thời gian trung bình
- `slowest_step`: Bước chậm nhất
- `page_loads`: Danh sách page load metrics
- `all_metrics`: Toàn bộ dữ liệu thô

#### `reset()`
Clear tất cả metrics + state.

---

## 12. API Tester — `core/api_tester.py`

### Mục đích
Framework test API (REST/GraphQL) sử dụng `urllib` của Python standard library (không phụ thuộc external HTTP library).

### Data Classes

#### Class `APITestCase`
```python
class APITestCase:
    def __init__(self, name, method, url, headers=None,
                 body="", params=None, assertions=None):
```

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `name` | `str` | Tên test case |
| `method` | `str` | HTTP method (GET, POST, PUT, PATCH, DELETE) |
| `url` | `str` | URL endpoint (có thể relative) |
| `headers` | `dict` | Custom HTTP headers |
| `body` | `str` | Request body (JSON string) |
| `params` | `dict` | Query parameters |
| `assertions` | `list[dict]` | Danh sách assertions |

Methods: `to_dict()`, `from_dict(data)` (classmethod)

#### Class `APITestResult`
```python
class APITestResult:
    def __init__(self, test_name):
```

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `test_name` | `str` | Tên test |
| `status` | `str` | `"pending"`, `"passed"`, `"failed"`, `"error"` |
| `status_code` | `int` | HTTP status code |
| `response_body` | `str` | Response body (string) |
| `response_headers` | `dict` | Response headers |
| `response_time_ms` | `float` | Thời gian response (ms) |
| `assertions_results` | `list[dict]` | Kết quả từng assertion |
| `error` | `str` | Lỗi network/timeout |

### Class `APITester`

```python
class APITester:
    def __init__(self):
        self.results = []
        self.base_url = ""
        self.default_headers = {"Content-Type": "application/json"}
```

**Phương thức chính:**

#### `run_test(test_case: APITestCase) → APITestResult`

Luồng:
```
1. Xây dựng full URL:
   - Nếu url bắt đầu "http" → dùng trực tiếp
   - Nếu không → prepend base_url
2. Thêm query params (urllib.parse.urlencode)
3. Merge headers: default_headers + test_case.headers
4. Encode body (nếu POST/PUT/PATCH)
5. Tạo urllib.request.Request → urllib.request.urlopen(timeout=30)
6. TRY:
   - Đọc status_code, response_body, response_headers
7. CATCH HTTPError: vẫn đọc status_code + body
8. CATCH Exception: set status="error"
9. Tính response_time_ms = perf_counter diff * 1000
10. Chạy assertions → all_passed?
11. status = "passed" nếu all_passed, "failed" nếu không
```

#### `_check_assertion(assertion, result) → dict`

5 loại assertion:

| Type | Expected | Actual | Logic |
|---|---|---|---|
| `status_code` | int | `result.status_code` | `actual == int(expected)` |
| `body_contains` | string | `result.response_body` | `expected in actual` |
| `body_json_path` | any | Giá trị tại JSON path | `str(actual) == str(expected)` |
| `header` | string | Header value | `expected.lower() in actual.lower()` |
| `response_time` | float (ms) | `result.response_time_ms` | `actual <= float(expected)` |

#### `_resolve_json_path(data, path) → any`
Simple JSON path resolver:
- Input: `"data.user.name"` → split by `.`
- Duyệt: `dict.get(part)` hoặc `list[int(part)]`
- Return giá trị tại path, hoặc `None`

#### `run_collection(test_cases) → list[APITestResult]`
Chạy nhiều test cases tuần tự. Hỗ trợ cả `APITestCase` objects và `dict`.

#### `save_collection(filepath, test_cases)` / `load_collection(filepath)`
Serialize/deserialize test collection ra/vào JSON file.

---

## 13. DB Verifier — `core/db_verifier.py`

### Mục đích
Kiểm tra trạng thái database sau khi chạy UI test — verify dữ liệu đã được tạo/cập nhật đúng.

### Class `DBVerifier`

```python
class DBVerifier:
    SUPPORTED_DRIVERS = {
        "sqlite": "sqlite3",
        "mysql": "pymysql",
        "postgresql": "psycopg2",
        "mssql": "pyodbc",
    }
```

**Thuộc tính:**

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `connection` | `Connection \| None` | Database connection object |
| `db_type` | `str` | Loại DB đang kết nối |
| `connection_string` | `str` | Connection string (cho MSSQL) |

**Phương thức:**

#### `connect(db_type, host, port, database, username, password, connection_string) → bool`

| DB Type | Driver | Default Port | Kết nối |
|---|---|---|---|
| `sqlite` | `sqlite3` (builtin) | — | `sqlite3.connect(database)` |
| `mysql` | `pymysql` | 3306 | `pymysql.connect(host, port, user, password, database)` |
| `postgresql` | `psycopg2` | 5432 | `psycopg2.connect(host, port, user, password, dbname)` |
| `mssql` | `pyodbc` | 1433 | `pyodbc.connect(connection_string)` hoặc ODBC Driver 17 |

#### `disconnect()`
Đóng connection, set `connection = None`.

#### `execute_query(query, params=None) → list[dict]`
1. Kiểm tra connection
2. `cursor.execute(query, params)`
3. Lấy column names từ `cursor.description`
4. `fetchall()` → chuyển thành `list[dict]` bằng `zip(columns, row)`

#### `verify_record_exists(table, conditions) → bool`
```sql
SELECT COUNT(*) as cnt FROM {table} WHERE col1 = ? AND col2 = ?
```
- Tự động chuyển `?` → `%s` cho MySQL/PostgreSQL
- Return `True` nếu count > 0

#### `verify_field_value(table, conditions, field, expected_value) → bool`
```sql
SELECT {field} FROM {table} WHERE ... LIMIT 1
```
- So sánh `str(actual) == str(expected_value)` (string comparison)

#### `verify_row_count(table, conditions=None, expected_count=0) → bool`
```sql
SELECT COUNT(*) FROM {table} [WHERE ...]
```
- So sánh `actual == expected_count` (exact match)

#### `run_verification_script(script: list) → list[dict]`
Chạy danh sách verification steps. Mỗi step là dict:

| Type | Gọi | Expected |
|---|---|---|
| `record_exists` | `verify_record_exists()` | implicit (count > 0) |
| `field_value` | `verify_field_value()` | `step["expected"]` |
| `row_count` | `verify_row_count()` | `step["expected"]` (int) |
| `custom_query` | `execute_query()` | `int` (row count), `str` (contains), default (> 0) |

Return: `[{"step": step_dict, "passed": bool}, ...]`

---

## 14. Test Scheduler — `core/test_scheduler.py`

### Mục đích
Lên lịch chạy test tự động theo pattern: một lần, theo chu kỳ, hoặc hàng ngày.

### Data Class `ScheduledTask`

```python
class ScheduledTask:
    def __init__(self, name, template, data_file, sheet="Sheet1",
                 page_id="", url="", mode="single",
                 schedule_type="once", interval_minutes=60,
                 run_at="", browser="chromium",
                 setup_script="", enabled=True):
```

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `name` | `str` | Tên task |
| `template` | `str` | File template |
| `data_file` | `str` | File dữ liệu test |
| `sheet` | `str` | Sheet Excel |
| `page_id` | `str` | Page ID |
| `url` | `str` | URL test |
| `mode` | `str` | `"single"` hoặc `"e2e"` |
| `schedule_type` | `str` | `"once"`, `"interval"`, `"daily"` |
| `interval_minutes` | `int` | Chu kỳ (phút) cho mode interval |
| `run_at` | `str` | Giờ chạy `"HH:MM"` cho mode daily |
| `browser` | `str` | Trình duyệt |
| `setup_script` | `str` | Setup script (tùy chọn) |
| `enabled` | `bool` | Bật/tắt |
| `last_run` | `datetime \| None` | Lần chạy cuối |
| `last_status` | `str` | Trạng thái lần cuối |
| `next_run` | `datetime \| None` | Lần chạy tiếp theo |
| `run_count` | `int` | Số lần đã chạy |

Methods: `to_dict()`, `from_dict(data)` (classmethod)

### Class `TestScheduler`

```python
class TestScheduler:
    def __init__(self, project_path=""):
```

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `project_path` | `str` | Đường dẫn dự án |
| `tasks` | `list[ScheduledTask]` | Danh sách tasks |
| `_running` | `bool` | Scheduler đang chạy? |
| `_thread` | `Thread \| None` | Background thread |
| `_config_path` | `Path` | `config/schedules.json` |
| `_on_task_complete` | `callable \| None` | Callback khi task xong |

**Phương thức:**

#### `start()` / `stop()`
- `start()`: Tạo daemon thread chạy `_scheduler_loop()`, set `_running = True`
- `stop()`: Set `_running = False` → thread tự dừng ở vòng lặp tiếp theo

#### `_scheduler_loop()` (chạy trên background thread)
```python
while self._running:
    now = datetime.now()
    for task in self.tasks:
        if task.enabled and task.next_run and now >= task.next_run:
            self._execute_task(task)
            self._calculate_next_run(task)
    time.sleep(30)  # Kiểm tra mỗi 30 giây
```

#### `_calculate_next_run(task)`

| schedule_type | Logic tính next_run |
|---|---|
| `once` | Chạy ngay nếu `run_count == 0`, None nếu đã chạy |
| `interval` | `last_run + interval_minutes` phút |
| `daily` | Parse `run_at` "HH:MM" → set ngày hôm nay/ngày mai |

#### `_execute_task(task)`
1. Xác định test file: `test_e2e.py` (e2e) hoặc `test_main.py` (single)
2. Tạo command: `python -m pytest {test_file} -v -s`
3. Set env vars: `BASE_URL`, `SELECTED_TEST_DATA`, `SHEET_NAME`, `PAGE_ID`, `BROWSER`, `SETUP_SCRIPT`, `E2E_WORKFLOW`
4. `subprocess.run(cmd, timeout=300)` — timeout 5 phút
5. Cập nhật: `last_status`, `last_run`, `run_count`
6. Gọi `_on_task_complete` callback (nếu có)

#### `_save_config()` / `load_config()`
Persist tasks ra/vào `config/schedules.json` dạng JSON array.

---

## 15. Test History — `core/test_history.py`

### Mục đích
Lưu trữ và phân tích lịch sử kết quả test qua các lần chạy.

### Data Class `TestHistoryEntry`

```python
class TestHistoryEntry:
    def __init__(self, suite_name="", total=0, passed=0,
                 failed=0, skipped=0, duration_ms=0,
                 timestamp="", details=None):
```

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `suite_name` | `str` | Tên suite |
| `total` | `int` | Tổng test |
| `passed` | `int` | Số passed |
| `failed` | `int` | Số failed |
| `skipped` | `int` | Số skipped |
| `duration_ms` | `int` | Tổng thời gian (ms) |
| `timestamp` | `str` | ISO timestamp |
| `details` | `list[dict]` | Chi tiết từng test: `{name, status, duration_ms}` |

**Property `pass_rate`**: `(passed / total * 100)` — tính tỷ lệ phần trăm.

### Class `TestHistory`

```python
class TestHistory:
    def __init__(self, project_path=""):
```

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `project_path` | `str` | Đường dẫn dự án |
| `entries` | `list[TestHistoryEntry]` | Danh sách entries |
| `_history_path` | `Path` | `reports/test_history.json` |

**Phương thức:**

#### `add_entry(entry)` / `add_from_report(report_data)`
- `add_entry()`: Thêm entry → auto-save
- `add_from_report()`: Tạo entry từ report JSON data (ReportGenerator output)

#### `get_trend(last_n=20) → list[dict]`
Return N entries cuối cùng dưới dạng list dict.

#### `get_summary() → dict`
Thống kê tổng:
```python
{
    "total_runs": int,
    "avg_pass_rate": float,
    "total_tests_executed": int,
    "total_passed": int,
    "total_failed": int,
    "last_run": str,      # timestamp
    "last_status": str,    # "5/5"
}
```

#### `get_failing_tests() → list[dict]`
Phân tích 10 entries gần nhất → tìm test cases fail nhiều nhất:
```python
[{"name": "test_login", "fail_count": 3}, ...]
```
Sắp xếp giảm dần theo `fail_count`.

#### `generate_trend_html() → str`
Tạo HTML table snippet hiển thị trend:
- Columns: Thời gian, Suite, Pass/Total, Tỷ lệ, Thời gian
- Row class: `passed` (100%), `warning` (≥50%), `failed` (<50%)

#### `load()` / `_save()`
Persistence: JSON array tại `reports/test_history.json`.

---

## 16. CLI Runner — `core/cli_runner.py`

### Mục đích
Giao diện command-line cho tích hợp CI/CD. Output: JUnit XML + JSON report.

### Hàm độc lập

#### `create_junit_xml(results, suite_name, output_path) → str`

Tạo XML theo chuẩn JUnit:
```xml
<testsuite name="..." tests="5" failures="1" errors="0" skipped="0" time="12.345">
  <testcase name="test_login" classname="tests" time="2.100">
    <failure message="..." type="AssertionError">...</failure>
  </testcase>
  ...
</testsuite>
```

Sử dụng `xml.etree.ElementTree` để build XML tree.

#### `parse_pytest_output(output) → list[dict]`
Parse output text của pytest để trích kết quả:
- Tìm dòng chứa "PASSED", "FAILED", "ERROR"
- Split `::` để lấy test name
- Return: `[{name, classname, status, duration_s, error_message}]`

### Hàm `main()` — Entry point CLI

**Arguments (argparse):**

| Argument | Short | Default | Mô tả |
|---|---|---|---|
| `--project` | `-p` | **required** | Đường dẫn dự án |
| `--template` | `-t` | None | File template |
| `--data` | `-d` | None | File dữ liệu |
| `--sheet` | `-s` | `"Sheet1"` | Sheet Excel |
| `--page-id` | — | None | Page ID |
| `--url` | `-u` | None | Base URL |
| `--browser` | `-b` | `"chromium"` | Browser (chromium/firefox/webkit) |
| `--mode` | `-m` | `"single"` | Mode (single/e2e) |
| `--setup-script` | — | None | Setup script name |
| `--headless` | — | `True` | Chạy headless |
| `--no-headless` | — | False | Hiện browser |
| `--junit-xml` | — | `reports/junit_results.xml` | Output JUnit XML |
| `--json-report` | — | `reports/cli_report.json` | Output JSON |
| `--parallel` | `-n` | `1` | Số worker (pytest-xdist) |
| `--verbose` | `-v` | False | In output chi tiết |

**Luồng thực thi:**
```
1. Parse arguments
2. Validate project directory exists
3. Build pytest command:
   python -m pytest tests/test_main.py -v -s [--junitxml=...] [-n N]
4. Set environment variables (BASE_URL, BROWSER, HEADLESS, ...)
5. subprocess.run(cmd) → capture output
6. Parse pytest output → results
7. Tạo JSON report → save
8. Print summary
9. sys.exit(process.returncode)
```

---

## 17. AI Generator — `core/ai_generator.py`

### Mục đích
Module AI phức tạp nhất — tạo test artifacts (locators, template, test data, setup script) từ use case + locators đã quét, sử dụng Google Gemini API với các kỹ thuật tiên tiến.

### Hàm helper (module-level)

#### `_is_actionable_locator(name, info) → bool`
Xác định locator có hữu ích cho test hay không:
- `type == "action"` → luôn giữ
- Selector bắt đầu `#` hoặc có `[data-test]`/`[name=]` → giữ
- Tag thuộc `_GENERIC_SELECTORS` (body, div, section...) + `type == "info"` → bỏ

#### `filter_locators(locators) → dict`
Lọc locators không liên quan → giảm token count cho AI prompt.

#### `chunk_use_case(text) → dict`
**Semantic Chunking** — tách use case thành sections:

| Key | Pattern (regex) | Ví dụ |
|---|---|---|
| `full` | Toàn bộ text | — |
| `main_flow` | `Main Flow\|Luong chinh\|Buoc thuc hien` | Các bước chính |
| `exception_flows` | `Exception Flow\|Ngoai le\|EF\d` | Luồng ngoại lệ |
| `preconditions` | `Precondition\|Dieu kien truoc` | Điều kiện tiên quyết |
| `postconditions` | `Postcondition\|Dieu kien sau\|Exit` | Kết quả sau test |

Hỗ trợ cả tiếng Việt và tiếng Anh.

#### `gather_rag_context(project_path, url) → str`
**Retrieval Augmented Generation (RAG)**:
1. Parse URL → domain → folder name
2. Tìm templates có sẵn (`templates/{domain}/*_workflow.json`) — tối đa 3 file
3. Tìm locators có sẵn (`locators/{domain}/*.json`) — tối đa 3 file
4. Ghép thành context string: `"=== DU LIEU THAM KHAO TU DU AN (RAG) ==="`
5. Mỗi file lấy tối đa 1500 ký tự

### Class `AIGenerator`

```python
class AIGenerator:
    FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-3-flash", "gemini-3.1-flash-lite"]
    MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 20
    SMALL_PAGE_THRESHOLD = 15   # ≤15 locators → single_pass
    LARGE_PAGE_THRESHOLD = 40   # ≤40 → filtered, >40 → multi_stage
```

**Thuộc tính:**

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `api_key` | `str` | Gemini API key |
| `_client` | `genai.Client \| None` | Lazy-initialized client |

**Phương thức chính:**

#### `_call_model(client, model_name, prompt) → str | None`

Retry logic cho 1 model:
```
for attempt in 1..MAX_RETRIES:
    TRY: generate_content() → return text
    CATCH:
      - 404 NOT_FOUND → return None (skip model)
      - 429 RESOURCE_EXHAUSTED:
        - Daily quota exhausted (PerDay + limit:0) → return None
        - Per-minute limit → parse delay → sleep → retry
      - Other error → raise
```

#### `_call_with_fallback(client, prompt) → (text, model_name)`
Thử lần lượt từng model trong `FALLBACK_MODELS`. Nếu tất cả fail → raise RuntimeError với hướng dẫn chi tiết.

#### `_select_strategy(locator_count) → str`
**Adaptive Processing**:

| Locator Count | Strategy | Mô tả |
|---|---|---|
| ≤ 15 | `single_pass` | 1 API call cho tất cả artifacts |
| 16 - 40 | `filtered` | Lọc locators + 1 API call |
| > 40 | `multi_stage` | 3 API calls riêng biệt |

#### `generate(use_case_text, locators, template, page_id, url, project_path) → dict`

**Pipeline 5 bước:**
```
1. PRE-AI FILTERING: filter_locators() → loại bỏ locators không liên quan
2. SEMANTIC CHUNKING: chunk_use_case() → tách use case thành sections
3. RAG CONTEXT: gather_rag_context() → thu thập ví dụ từ dự án
4. ADAPTIVE STRATEGY: _select_strategy() → chọn single_pass hoặc multi_stage
5. GENERATION:
   - single_pass → 1 AI call → parse tất cả artifacts
   - multi_stage → 3 AI calls:
     Stage 1: Locators + Template (dùng main_flow)
     Stage 2: Test Data (dùng exception_flows + data_keys từ Stage 1)
     Stage 3: Setup Script (dùng preconditions)
```

**Return dict:**
```python
{
    "locators": dict,       # Locators đã lọc/chỉnh sửa
    "template": dict,       # Workflow template
    "test_data": list,      # [{col: val, expected_result: "success"}, ...]
    "setup_script": dict|None,  # Setup script JSON (hoặc None)
    "summary": str,         # Tóm tắt tiếng Việt
}
```

#### Prompt Format

AI response sử dụng **labeled code blocks**:
```
```json_locators
{...}
```json_template
{...}
```json_testdata
[...]
```json_setup
{...}
```summary
...
```

#### `_extract_block(text, label) → str | None`
Regex: `` ```{label}\s*\n(.*?)``` `` → trích nội dung block.

#### `_parse_response(raw_text, original_locators, original_template, page_id, url) → dict`
Parse toàn bộ response → extract từng block → JSON.loads → trả về dict tổng hợp. Nếu parse lỗi block nào → giữ nguyên original.

---

## 18. AI Auto-Heal — `core/ai_auto_heal.py`

### Mục đích
Khi locator bị lỗi (element not found), tự động tìm selector thay thế bằng heuristic + AI.

### Class `AIAutoHeal`

```python
class AIAutoHeal:
    FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-3-flash", "gemini-3.1-flash-lite"]
```

**Thuộc tính:**

| Thuộc tính | Kiểu | Mô tả |
|---|---|---|
| `api_key` | `str` | Gemini API key |
| `_client` | `genai.Client \| None` | Lazy client |
| `heal_log` | `list[dict]` | Lịch sử tất cả heal attempts |

**Phương thức chính:**

#### `try_heal(page, step_id, original_selector, locator_info, page_source="") → dict`

**Chiến lược 2 bước:**
```
Bước 1: HEURISTIC (nhanh, không cần API)
  └── _try_heuristic() → thử các selector thay thế
  └── Nếu tìm được → return ngay

Bước 2: AI (chậm, cần API key)
  └── _try_ai_heal() → gửi HTML cho AI phân tích
  └── AI đề xuất selector → verify trên page
```

**Return:**
```python
{
    "healed": bool,         # True nếu tìm được selector mới
    "new_selector": str,    # Selector thay thế
    "confidence": float,    # 0-1 (0.7 cho heuristic, AI tự đánh giá)
    "method": str,          # "heuristic", "ai", "none"
}
```

#### `_try_heuristic(page, selector, info) → dict`

**Chiến lược heuristic:**

| Loại selector gốc | Alternatives thử |
|---|---|
| `#id` (ID-based) | `[name="id"]`, `[data-testid="id"]`, `[data-test="id"]`, `[aria-label="name"]` |
| Có `name` | `text="name"`, `[placeholder="name"]`, `[title="name"]` |
| `.class` (class-based) | `[class*="partial"]` cho mỗi class part > 3 ký tự |

Mỗi candidate: `page.query_selector(candidate)` → kiểm tra `is_visible()` → nếu OK return.

#### `_try_ai_heal(page, step_id, selector, info, page_source="") → dict`

1. Lấy page HTML (tối đa 15000 ký tự, cắt gửi 10000)
2. Prompt: yêu cầu AI phân tích HTML → đề xuất selector mới dạng JSON
3. Model fallback: thử lần lượt 3 models
4. Parse response JSON → `new_selector`
5. **Verify**: `page.query_selector(new_selector)` → phải tìm thấy element thực tế
6. Nếu verify fail → thử model tiếp

#### `_record_heal(step_id, old_selector, new_selector, method)`
Ghi vào `heal_log`:
```python
{"step_id": "...", "old_selector": "...", "new_selector": "...",
 "method": "heuristic", "timestamp": "2025-01-15 10:30:00"}
```

#### `update_locator_file(locator_path, step_id, new_selector) → bool`
Cập nhật file locator JSON:
- Đọc JSON → `data[step_id]["selector"] = new_selector`
- Thêm flag: `data[step_id]["auto_healed"] = True`
- Ghi lại file

#### `get_heal_report() → list`
Return toàn bộ `heal_log`.

---

## 19. AI Test Suggestion — `core/ai_test_suggestion.py`

### Mục đích
Phân tích git diff → gợi ý test cases nào cần chạy lại khi có code changes.

### Class `AITestSuggestion`

```python
class AITestSuggestion:
    FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-3-flash", "gemini-3.1-flash-lite"]
```

**Phương thức:**

#### `get_git_diff(project_path, base_branch="main") → str`
Chạy 3 git commands:
1. `git diff main --name-only` → danh sách file thay đổi
2. `git diff main --stat` → thống kê
3. `git diff main` → full diff (cắt 10000 ký tự)

#### `get_uncommitted_changes(project_path) → str`
`git diff HEAD` → uncommitted changes.

#### `analyze_changes(project_path, diff_text="") → dict`
**Phân tích rule-based** (không cần AI):

| File thay đổi | Impact |
|---|---|
| `locators/*` | → page_id affected, risk=high |
| `templates/*` | → page_id affected, risk=high |
| `core/*` hoặc `pages/*` | → risk=high |
| `config/*` | → risk=medium |

**Return:**
```python
{
    "affected_pages": ["login", "inventory"],
    "affected_locators": ["locators/site/login.json"],
    "affected_templates": ["templates/site/login_workflow.json"],
    "risk_level": "high",
    "suggestions": ["Locators da thay doi cho login. Can chay lai test."]
}
```

#### `suggest_with_ai(project_path, diff_text="") → dict`
1. Thu thập context: danh sách templates + locator files hiện có
2. Prompt AI: phân tích diff + suggest tests
3. **Return:**
```python
{
    "suggestions": [
        {"template": "login_workflow", "priority": "high", "reason": "..."}
    ],
    "explanation": "Tóm tắt phân tích",
    "risk_level": "high",
    "new_tests_needed": ["Mô tả test case mới cần tạo"]
}
```
4. Fallback: nếu AI fail → dùng `analyze_changes()` (rule-based)

---

## 20. AI Natural Language — `core/ai_natural_language.py`

### Mục đích
Chuyển đổi mô tả test bằng ngôn ngữ tự nhiên (tiếng Việt/tiếng Anh) thành template, locators, và test data.

### Class `AINaturalLanguage`

```python
class AINaturalLanguage:
    FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-3-flash", "gemini-3.1-flash-lite"]
```

**Phương thức:**

#### `convert_to_template(natural_text, url="", page_id="", existing_locators=None) → dict`

Input:
- `natural_text`: Mô tả bằng tiếng Việt/Anh
- `existing_locators`: Locators đã có → AI sẽ tái sử dụng

Prompt yêu cầu AI tạo:
```json
{
    "template": {"page_id": "...", "url": "...", "steps": [...]},
    "locators": {"ELEMENT": {"selector": "...", "type": "action"}},
    "test_data": [{"col": "val", "expected_result": "success"}],
    "explanation": "Giải thích bằng tiếng Việt"
}
```

Lưu ý trong prompt:
- CSS selector chuẩn cho locators
- Action phải thuộc danh sách hỗ trợ (click, fill, verify_text, ...)
- `data_key` = tên cột Excel
- Tạo ≥ 3 bộ dữ liệu (happy path + negative cases)

#### `parse_scenario_list(text) → list[str]`
Parse danh sách scenarios dạng:
```
1. Đăng nhập thành công với user hợp lệ
2. Đăng nhập thất bại với mật khẩu sai
```
→ Bỏ prefix số/ký tự đầu dòng → return `["Đăng nhập thành công...", ...]`

#### `batch_convert(scenarios, url, page_id, existing_locators) → list`
Chạy `convert_to_template()` cho từng scenario. Nếu scenario nào lỗi → ghi `{"scenario": "...", "error": "..."}`.

#### `suggest_improvements(natural_text) → dict`
AI phân tích chất lượng mô tả test:
```python
{
    "quality_score": 0-10,
    "missing_elements": ["Thiếu preconditions", ...],
    "suggestions": ["Thêm exception flows", ...],
    "improved_text": "Mô tả đã cải thiện"
}
```

---

## 21. Logic Manager — `logic_manager.py`

### Mục đích
Tầng trung gian (orchestration) kết nối UI ↔ Core. Xử lý scan URL, save files, merge templates, AI generation.

### Class `AutomationLogic`

```python
class AutomationLogic:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.ai = AIGenerator()
```

**Phương thức quan trọng:**

#### `get_site_folder_name(url) → str`
Chuyển URL → folder name:
- `https://www.saucedemo.com/` → `www_saucedemo_com`
- Bỏ ký tự đặc biệt: `\/*?:"<>|`

#### `scan_url(url, browser_name="chromium", setup_script="") → list[dict]`
**Luồng quét trang web:**
```
1. Launch Playwright browser (headless=True)
2. Nếu có setup_script → SetupRunner.run(page, script_path)
3. page.goto(url, timeout=60000)
4. page.evaluate(JavaScript) → quét DOM:
   - Selectors: input, button, select, textarea, h1-h6, span, p, a, label, div, section
   - Ưu tiên selector: ID > data-test > name > class (2 cấp cha) > tag (2 cấp cha)
   - Phân loại: action (input, button, select, textarea, a) vs info
   - Tạo tên: từ id/name/text/label
5. Return list[dict]: [{name, type, selector, action, data_key}, ...]
```

#### Các phương thức save/merge
- `save_locators()`: Lưu locators JSON
- `save_template()`: Lưu template JSON
- `merge_templates_to_e2e()`: Gộp nhiều template single-page → 1 workflow E2E
- `save_e2e_workflow()`: Lưu E2E workflow JSON

---

## 22. UI Layer — `ui/`

### 22.1 `ui/main_window.py` — Cửa sổ chính

#### Class `AutomationGeneratorUI`

```python
class AutomationGeneratorUI:
    def __init__(self, root: tk.Tk):
```

**Kiến trúc:**
- `root`: Tk window, title "Automation Control Center", size 1200x950
- `logic`: `AutomationLogic` instance (shared)
- `shared_vars`: Dict `tk.StringVar` dùng chung giữa các panel:
  - `project_path`, `url_path`, `page_id_var`, `browser_var`

**8 Tabs (ttk.Notebook):**

| # | Tab | Panel Class | Mô tả |
|---|---|---|---|
| 1 | Locator Scanner | `LocatorPanel` | Quét, chỉnh sửa locators |
| 2 | Test Runner | `TestRunnerPanel` | Chạy test, queue, parallel |
| 3 | Action Manager | `ActionManagerPanel` | Quản lý action definitions |
| 4 | API Testing | `APITestingPanel` | Test API REST/GraphQL |
| 5 | DB Verify | `DBVerificationPanel` | Kiểm tra database |
| 6 | Scheduler | `SchedulerPanel` | Lên lịch chạy test |
| 7 | History | `HistoryPanel` | Lịch sử kết quả |
| 8 | AI Tools | `AIToolsPanel` | 3 sub-tabs AI |

**Callback inter-panel:**
```python
self.locator_panel.on_project_changed = self._on_project_changed
```
Khi project path thay đổi ở Locator panel → refresh Test Runner lists.

### 22.2 `ui/locator_panel.py` — Tab 1

**Sections:**
1. **Config**: Project path, URL, Page ID
2. **Scan List**: Bảng multi-page scan (URL + PageID), thêm/xóa dòng, quét tất cả
3. **Elements Treeview**: Kết quả quét (Type, Name, Selector, Action, DataKey)
4. **AI Section**: API key, use case textarea, nút "TAO BANG AI", kết quả AI
5. **Log**: Console log realtime
6. **JSON Editors**: View/edit locators + template JSON (popup windows)

**Đặc biệt**: Toàn panel wrapped trong `Canvas` + `Scrollbar` cho scroll dọc.

### 22.3 `ui/test_runner_panel.py` — Tab 2

**Sections:**
1. **Browser selection**: Dropdown chromium/firefox/webkit
2. **Template selection**: Auto-discover `*_workflow.json` files
3. **Data file selection**: Auto-discover `.xlsx` files
4. **Mode**: Radio "Don trang" / "E2E (Da trang)"
5. **Queue**: Treeview với add/remove/move up/move down/clear
6. **Execution**: "CHAY MUC CHON" (selected) / "CHAY TAT CA" (all)
7. **Options**: Parallel workers, HTML report, headless, setup script
8. **Merge Templates**: Nút mở dialog merge → E2E workflow

**Tích hợp:**
- Sau khi chạy xong → tự động tạo HTML report (`ReportGenerator`)
- Ghi vào lịch sử (`TestHistory`)

### 22.4 `ui/action_manager_panel.py` — Tab 3

**Sections:**
1. **Action list**: Treeview 18 actions định sẵn + custom
2. **Editor**: Chọn Playwright function → auto-fill params
3. **Code generator**: Preview generated code cho `base_page.py` + `generic_runner.py`
4. **Config file**: `config/actions_config.json`

### 22.5 `ui/api_testing_panel.py` — Tab 4

**Sections:**
1. **Request builder**: Method, URL, headers, body
2. **Assertions**: Thêm/xóa assertions (status_code, body_contains, ...)
3. **Results**: Hiển thị response
4. **Collections**: Save/load test collections

### 22.6 `ui/db_panel.py` — Tab 5

**Sections:**
1. **Connection**: DB type, host, port, database, username, password
2. **Query**: Execute custom SQL
3. **Verification**: Chạy verification script
4. **Results**: Hiển thị kết quả query/verify

### 22.7 `ui/scheduler_panel.py` — Tab 6

**Sections:**
1. **Task list**: Treeview các scheduled tasks
2. **Add task**: Form thêm task mới (template, data, schedule type, ...)
3. **Controls**: Start/Stop scheduler, Enable/Disable task

### 22.8 `ui/history_panel.py` — Tab 7

**Sections:**
1. **Summary stats**: Total runs, avg pass rate, ...
2. **Trend table**: Bảng lịch sử N lần chạy gần nhất
3. **Failing tests**: Danh sách test fail nhiều nhất

### 22.9 `ui/ai_tools_panel.py` — Tab 8

**3 Sub-tabs (ttk.Notebook lồng nhau):**

| Sub-tab | Core Module | Mô tả |
|---|---|---|
| Natural Language | `AINaturalLanguage` | Nhập mô tả tiếng Việt → tạo template |
| Test Suggestion | `AITestSuggestion` | Phân tích git diff → gợi ý test |
| Auto-Heal Log | `AIAutoHeal` | Xem lịch sử locators đã tự sửa |

---

## 23. Pytest Configuration — `conftest.py`

### Mục đích
Định nghĩa pytest fixtures và hooks cho toàn bộ hệ thống test.

### Fixtures

#### `playwright_instance` (scope=session)
```python
@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as playwright:
        yield playwright
```
Khởi tạo 1 Playwright instance cho toàn bộ session test.

#### `browser` (scope=session)
```python
@pytest.fixture(scope="session")
def browser(playwright_instance):
    browser_name = Config.get_base_browser()  # từ env BROWSER
    headless = Config.get_headless()           # từ env HEADLESS
    browser = browser_type.launch(headless=headless)
    yield browser
    browser.close()
```
Launch browser 1 lần cho cả session.

#### `page` (scope=function)
```python
@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(Config.TIMEOUT)
    
    # Chạy setup script nếu có env var SETUP_SCRIPT
    setup_script = os.environ.get("SETUP_SCRIPT", "")
    if setup_script:
        SetupRunner.run(page, setup_script)
    
    yield page
    context.close()  # Giải phóng bộ nhớ sau mỗi test
```
Tạo context + page mới cho MỖI test function → isolation hoàn toàn.

### Hook `pytest_runtest_makereport`
```python
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
```
- Chạy sau mỗi test (hookwrapper)
- Nếu test FAIL (`report.when == "call" and report.failed`):
  1. Lấy `page` từ fixtures
  2. Chụp screenshot: `FAILED_{test_name}_{timestamp}.png`
  3. Đính kèm vào Allure Report (`allure.attach.file`)

---

## 24. Dependencies — `requirements.txt`

| Package | Version | Mục đích |
|---|---|---|
| `playwright` | `1.43.0` | Browser automation engine |
| `pytest` | `8.1.1` | Test framework |
| `pytest-playwright` | `0.4.4` | Playwright integration cho pytest |
| `allure-pytest` | `2.13.2` | Allure report integration |
| `python-dotenv` | `1.0.1` | Đọc file `.env` |
| `pandas` | `2.2.1` | Đọc/xử lý Excel data |
| `openpyxl` | `3.1.2` | Engine đọc `.xlsx` cho pandas |
| `loguru` | `0.7.2` | Logging library |
| `pytest-xdist` | `3.5.0` | Parallel test execution (`-n N`) |
| `google-genai` | `>=1.0.0` | Google Gemini AI SDK |
| `Pillow` | `>=10.0.0` | Image processing (visual regression) |

---

## 25. Sơ đồ luồng dữ liệu

### 25.1 Luồng chạy test (Single Page)

```
User nhấn "CHAY" trong UI
  │
  ├── TestRunnerPanel._execute_items()
  │     ├── Set env vars (BASE_URL, BROWSER, PAGE_ID, ...)
  │     ├── subprocess: python -m pytest tests/test_main.py
  │     │
  │     │  [Trong pytest process]
  │     │     conftest.py
  │     │       ├── playwright_instance (session)
  │     │       ├── browser (session, chromium/firefox/webkit)
  │     │       └── page (function)
  │     │             ├── new_context + new_page
  │     │             └── SetupRunner.run() [nếu có]
  │     │
  │     │     test_main.py::test_generic(page)
  │     │       ├── GenericRunner(page, site_name, page_id)
  │     │       │     ├── Load locators/{site}/{page_id}.json
  │     │       │     └── Load templates/{site}/{page_id}_workflow.json
  │     │       ├── Helpers.read_excel_data(file, site_folder)
  │     │       │     └── pandas.read_excel → list[dict]
  │     │       └── for row in data:
  │     │             runner.run_test(row)
  │     │               ├── navigate(url)
  │     │               ├── perf_monitor.measure_page_load()
  │     │               └── for step in steps:
  │     │                     ├── perf_monitor.start_step()
  │     │                     ├── _dispatch_action() → BasePage.method()
  │     │                     ├── perf_monitor.end_step()
  │     │                     └── [on fail]:
  │     │                           ├── screenshot_mgr.capture_on_failure()
  │     │                           └── auto_heal.try_heal() [tùy chọn]
  │     │
  │     ├── Parse output → ReportGenerator.generate_html()
  │     └── TestHistory.add_entry()
  │
  └── Hiển thị kết quả trong log panel
```

### 25.2 Luồng AI Generate

```
User nhấn "TAO BANG AI" trong Locator Panel
  │
  ├── Đọc: locators (từ scan), template (hiện tại), use_case (text area)
  │
  ├── AIGenerator.generate()
  │     │
  │     ├── Stage 1: filter_locators() — loại bỏ generic locators
  │     ├── Stage 2: chunk_use_case() — tách sections
  │     ├── Stage 3: gather_rag_context() — thu thập ví dụ có sẵn
  │     ├── Stage 4: _select_strategy() — chọn single/multi
  │     │
  │     └── Stage 5: Gọi Gemini API
  │           ├── Model 1: gemini-2.5-flash
  │           │     └── [fail] → retry (3 lần, sleep delay)
  │           ├── Model 2: gemini-3-flash
  │           └── Model 3: gemini-3.1-flash-lite
  │
  ├── Parse response → {locators, template, test_data, setup_script}
  │
  └── Hiển thị dialog 4 tabs → User edit → "LUU TAT CA"
        ├── Save locators JSON
        ├── Save template JSON
        ├── Save test_data → Excel (.xlsx)
        └── Save setup_script JSON
```

### 25.3 Luồng Auto-Heal

```
GenericRunner._execute_step() gặp lỗi
  │
  ├── screenshot_mgr.capture_on_failure()
  │
  ├── Kiểm tra: auto_heal != None AND lỗi chứa "Khong tim thay"/"Timeout"
  │
  └── auto_heal.try_heal(page, step_id, selector, locator_info)
        │
        ├── Bước 1: _try_heuristic()
        │     ├── #id → thử [name=], [data-testid=], [aria-label=]
        │     ├── text → thử text=, [placeholder=], [title=]
        │     └── .class → thử [class*="partial"]
        │     └── Mỗi candidate: page.query_selector() + is_visible()
        │
        ├── Bước 2: _try_ai_heal() (nếu heuristic fail)
        │     ├── Lấy page HTML (15000 chars max)
        │     ├── Prompt AI: "Tìm selector thay thế cho..."
        │     ├── Parse JSON response → new_selector
        │     └── Verify: page.query_selector(new_selector)
        │
        └── Nếu healed:
              ├── _record_heal() → ghi vào heal_log
              └── GenericRunner retry action với selector mới
```

---

## 26. Design Patterns sử dụng

### 26.1 Page Object Model (POM)
- **File**: `pages/base_page.py`
- **Mô tả**: Đóng gói Playwright API → các method có tên rõ ràng (click, fill, verify_text)
- **Lợi ích**: Nếu Playwright API thay đổi → chỉ sửa 1 chỗ

### 26.2 Strategy Pattern
- **AI Model Fallback**: 3 models thử lần lượt
- **Adaptive Processing**: single_pass / filtered / multi_stage dựa trên locator count
- **Healing Strategy**: heuristic → AI (escalation)
- **DB Connection**: Factory method theo `db_type`

### 26.3 Observer/Callback Pattern
- **TestScheduler**: `_on_task_complete` callback khi task xong
- **UI Panels**: `on_project_changed` callback giữa panels
- **Pytest Hook**: `pytest_runtest_makereport` → screenshot on failure

### 26.4 Template Method Pattern
- **GenericRunner.run_test()**: Định nghĩa luồng chung (navigate → execute steps)
- **Mỗi action**: dispatch qua `_dispatch_action()` → gọi BasePage method

### 26.5 Data Transfer Object (DTO)
- `TestResult`, `StepResult`: Đóng gói dữ liệu test result
- `APITestCase`, `APITestResult`: Đóng gói API test data
- `ScheduledTask`, `TestHistoryEntry`: Đóng gói scheduled task / history

### 26.6 Singleton-like
- `Config`: Module-level instance (`Config.validate_config()` chạy khi import)
- `log`: Module-level logger instance (`setup_logger()` chạy 1 lần)

### 26.7 Pipeline Pattern
- **AIGenerator.generate()**: 5-stage pipeline (filter → chunk → RAG → strategy → generate)
- **CLI Runner**: parse args → set env → subprocess → parse output → create reports

---

## 27. Xử lý lỗi toàn hệ thống

### 27.1 Mô hình xử lý lỗi

```
Layer        | Chiến lược
-------------|------------------------------------------
BasePage     | try/except → log.error → re-raise
GenericRunner| catch → screenshot → try auto-heal → re-raise
E2ERunner    | catch → log → re-raise  
conftest.py  | pytest hook → screenshot → allure attach
UI           | try/except → messagebox.showerror()
AI modules   | retry + model fallback + graceful degradation
DB Verifier  | try/except → log → return False
Scheduler    | try/except → set status="ERROR" → callback
```

### 27.2 AI Error Handling

```
Lỗi 429 (Rate Limit)
  ├── Per-minute: parse retry delay → sleep → retry (tối đa 3 lần)
  └── Per-day (PerDay + limit:0): skip model → thử model tiếp

Lỗi 404 (Model Not Found)
  └── Skip ngay → thử model tiếp (không retry)

Tất cả models fail
  └── Raise RuntimeError với hướng dẫn:
      - Đợi 1-2 phút (per-minute reset)
      - Đợi ngày mai (daily reset)
      - Nâng cấp plan trả phí
      - Tạo API key mới
```

### 27.3 Graceful Degradation

| Module | Nếu dependency thiếu | Hành vi |
|---|---|---|
| `ai_generator.py` | `google-genai` chưa cài | `genai = None`, AI features disabled |
| `ai_auto_heal.py` | Không có API key | Chỉ dùng heuristic healing |
| `screenshot_manager.py` | `Pillow` chưa cài | `_compare_images()` return (0.0, ""), log warning |
| `db_verifier.py` | Driver chưa cài | `connect()` return False, log error |
| `conftest.py` | `allure` import fail | Screenshot vẫn chụp, chỉ thiếu allure attach |

---

*Tài liệu được tạo tự động cho dự án Automation Control Center.*
*Phiên bản: 1.0 — Tháng 4/2026*
