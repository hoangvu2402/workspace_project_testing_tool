from pages.base_page import BasePage
from locators.demo_index_2_locators import demo_index_2Locators

class demo_index_2Page(BasePage):
    def execute_workflow(self, data):
        self.fill(demo_index_2Locators.USERNAME, data.get('username'))
        self.fill(demo_index_2Locators.PASSWORD, data.get('password'))
        self.click(demo_index_2Locators.LOGINBUTTON)
