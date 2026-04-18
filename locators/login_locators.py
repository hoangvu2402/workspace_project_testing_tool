class LoginLocators:
    """
    Template chứa các selectors cho trang Đăng nhập.
    Lưu ý: Các giá trị dưới đây là ví dụ cho trang SauceDemo.
    Khi chuyển sang dự án khác, bạn có thể tạo một class mới kế thừa hoặc thay đổi giá trị tại đây.
    """
    
    # Nhóm các trường nhập liệu (Inputs)
    USERNAME_INPUT = "id=user-name"
    PASSWORD_INPUT = "id=password"
    
    # Nhóm các điều hướng/hành động (Actions)
    LOGIN_BUTTON = "id=login-button"
    
    # Nhóm các thành phần kiểm tra (Assertions/Status)
    ERROR_MESSAGE = "h3[data-test='error']"
    APP_LOGO = ".app_logo"

class ShopeeLoginLocators(LoginLocators):
    """
    Ví dụ về tính linh hoạt: Nếu test Shopee, bạn chỉ cần tạo class mới 
    và ghi đè (override) các selector tương ứng mà không làm hỏng code cũ.
    """
    USERNAME_INPUT = "xpath=//input[@name='loginKey']"
    PASSWORD_INPUT = "xpath=//input[@name='password']"
    LOGIN_BUTTON = "css=button.vyS6_g"