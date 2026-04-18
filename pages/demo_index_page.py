from pages.base_page import BasePage
from locators.demo_index_locators import demo_indexLocators
from utils.logger import log

class demo_indexPage(BasePage):
    def execute_workflow(self, data):
        log.info("Bắt đầu thực hiện workflow trên demo_index")
        self.click(demo_indexLocators.LOGIN_BUTTON, "LOGIN_BUTTON")
        self.fill(demo_indexLocators.PASSWORD_INPUT, data.get('password_input'), "PASSWORD_INPUT")
        self.fill(demo_indexLocators.USERNAME_INPUT, data.get('username_input'), "USERNAME_INPUT")
