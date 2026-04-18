from pages.base_page import BasePage
from locators.inventory_locators import InventoryLocators

class InventoryPage(BasePage):
    def execute_workflow(self, data):
        self.fill(InventoryLocators.USER_NAME, data.get('user_name'))
        self.fill(InventoryLocators.PASSWORD, data.get('password'))
        self.fill(InventoryLocators.LOGIN_BUTTON, data.get('login_button'))
