from pages.base_page import BasePage
from locators.demo_index_1_locators import demo_index_1Locators

class demo_index_1Page(BasePage):
    def execute_workflow(self, data):
        self.fill(demo_index_1Locators.USERNAME, data.get('username'))
        self.fill(demo_index_1Locators.PASSWORD, data.get('password'))
        self.click(demo_index_1Locators.LOGINBUTTON)
