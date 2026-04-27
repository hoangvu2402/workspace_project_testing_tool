"""
Setup script: Login to SauceDemo.
Tu dong dang nhap vao SauceDemo voi tai khoan standard_user.

Python setup scripts nhan mot doi tuong Playwright `page` va thuc hien
cac hanh dong can thiet de chuan bi trang truoc khi quet hoac chay test.
"""


def run(page):
    """Entry point cho setup script. Nhan Playwright page object."""
    page.goto("https://www.saucedemo.com/")
    page.fill("#user-name", "standard_user")
    page.fill("#password", "secret_sauce")
    page.click("#login-button")
    page.wait_for_timeout(2000)
