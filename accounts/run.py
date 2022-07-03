import json
import time
from datetime import datetime

from pysinewave import SineWave, sinewave
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, \
    ElementNotInteractableException
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc


class CreateHuobiAccount:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--allow-profiles-outside-user-dir')
        options.add_argument('--enable-profile-shortcut-manager')
        options.add_argument("--test-type")
        options.add_argument("--disable-popup-blocking")
        # options.add_argument(r'user-data-dir=.\User')
        options.add_argument('--profile-directory=Profile 1')

        self.driver = uc.Chrome(options=options)

        self.CODE_LENGTH = 6

        self.MAIL_UPDATE_DELAY = 2

        self.MEDIUM_DELAY = 0.5
        self.LARGE_DELAY = 1

        self.ALGO_ADDRESS = 'ZKYMHWKQ74V2IVACEN3ZXYOZU4PELOR677N56KBQ52COBM25MAL67PGBSA'

        self.code_cache = set()

        self.item = dict()

    def _switch_to_site(self, tag):
        for i in self.driver.window_handles:
            self.driver.switch_to.window(i)
            if tag in self.driver.current_url:
                return

    def get_register_email(self):
        self._switch_to_site('10minutemail')

        email_txt = self.driver.find_element(by=By.ID, value='fe_text')

        print('Email successfully received: ', email_txt.get_attribute('value'))
        self.item['MAIL'] = email_txt.get_attribute('value')
        return email_txt.get_attribute('value')

    def get_register_code(self):
        counter = 0
        while True:
            try:
                counter += 1
                if counter >= 3:
                    print('Trying to get code...')
                    self._switch_to_site('huobi')
                    self.click_send_code_button(True)
                    self._switch_to_site('10minutemail')
                    print('Code successfully sent')
                    counter = 0

                self._switch_to_site('10minutemail')
                self.driver.get('https://10minutemail.net/more.html')
                time.sleep(self.MEDIUM_DELAY)

                ready = False

                timer = 0
                while not ready:
                    try:
                        mails = self.driver.find_elements(by=By.CLASS_NAME, value='row-link')
                        for mail in mails:
                            if 'huobi' in mail.get_attribute("innerHTML").lower() and \
                                    'bold' in mail.find_element(  # только жирные (непрочитанные) сообщения
                                by=By.XPATH,
                                value='..'
                            ).find_element(by=By.XPATH, value='..').find_element(by=By.XPATH, value='..').get_attribute(
                                "innerHTML"
                            ).lower():
                                mail.click()
                                ready = True
                                break
                        if ready:
                            break
                        raise StaleElementReferenceException
                    except StaleElementReferenceException:
                        self.driver.get('https://10minutemail.net/more.html')
                        timer += self.MAIL_UPDATE_DELAY
                        time.sleep(self.MAIL_UPDATE_DELAY)
                        print('Waiting for Huobi register code... ', timer, 's')
                try:
                    message_html = self.driver.page_source
                    for i in range(len(message_html)):
                        if message_html[i] == '>':
                            answer = ''
                            cnt = i + 1
                            while message_html[cnt] != '<':
                                answer += message_html[cnt]
                                cnt += 1
                            try:
                                int(answer)
                                if len(answer) >= self.CODE_LENGTH and answer not in self.code_cache:
                                    print("Code successfully received:", answer)
                                    self.code_cache.add(answer)
                                    return answer
                                elif answer in self.code_cache:
                                    raise RuntimeError
                            except ValueError:
                                continue
                except IndexError:
                    time.sleep(self.MAIL_UPDATE_DELAY)
            except RuntimeError:
                time.sleep(self.MAIL_UPDATE_DELAY)
                continue

    def wait_captcha(self):
        while len(self.driver.find_elements(by=By.CLASS_NAME, value='captcha')) == 0:
            continue

    def register(self):
        print("Starting register...")
        self._switch_to_site('huobi')

        while True:
            try:
                self._switch_to_site('huobi')
                email_inp = self.driver.find_element(by=By.ID, value='email')
                password_inp = self.driver.find_element(by=By.ID, value='password')
                signup_btn = self.driver.find_element(by=By.CSS_SELECTOR, value='button.button.text_button')

                email_txt = self.get_register_email()
                self._switch_to_site('huobi')
                while True:
                    try:
                        email_inp.send_keys(email_txt)
                        password = 'djkshaksjhdFHkjhkF239'
                        self.item['ACCOUNT_PASSWORD'] = password
                        password_inp.send_keys(password)
                        break
                    except (ElementNotInteractableException, NoSuchElementException, StaleElementReferenceException):
                        time.sleep(self.MEDIUM_DELAY)
                        continue

                signup_btn.click()
                time.sleep(self.MEDIUM_DELAY)
                print('Sign up button clicked')

                # captcha_is_now = SineWave(pitch=12)
                # captcha_is_now.play()
                # time.sleep(self.MEDIUM_DELAY)
                # captcha_is_now.stop()

                # ------------------------------------------------------------------------------------------
                while True:
                    try:
                        code_inps_parent = self.driver.find_element(
                            by=By.CSS_SELECTOR,
                            value='div.ui-captcha-input.ui-captcha-input-'
                        )

                        code_inps = code_inps_parent.find_elements(by=By.XPATH, value='./*')
                        code_txt = self.get_register_code()
                        self._switch_to_site('huobi')
                        print("Successfully switched to site Huobi")

                        for code_inp, code_digit in zip(code_inps, code_txt):
                            code_inp.send_keys(code_digit)
                    except (
                            ElementNotInteractableException, NoSuchElementException,
                            StaleElementReferenceException):
                        continue

                    return
            except (ElementNotInteractableException, NoSuchElementException, StaleElementReferenceException):
                time.sleep(self.LARGE_DELAY)
                continue

    def open_pages(self):
        self.driver.execute_script("window.open('https://10minutemail.net/new.html')")
        # self.driver.execute_script("window.open('https://huobi.com/en-us/register')")
        self.driver.get('https://huobi.com/en-us/register')

        time.sleep(4)

    def get_uid(self):
        uuid_spn = self.driver.find_element(
            by=By.CSS_SELECTOR,
            value='span.fedui-header-info-dropdowns-header-uid'
        )

        print(uuid_spn.get_attribute('innerHTML'))
        return uuid_spn.text

    def click_all_permissions_1(self):
        checks_target_inps = []
        while len(checks_target_inps) < 2:
            checks_target_inps = []
            checks_inps = self.driver.find_elements(by=By.CLASS_NAME, value='ui-checkbox-input')
            try:
                for check_inp in checks_inps:
                    if 'WITHDRAW' in check_inp.get_attribute("outerHTML"):
                        checks_target_inps.append(check_inp)
                    elif 'WRITE' in check_inp.get_attribute("outerHTML"):
                        checks_target_inps.append(check_inp)

                if len(checks_target_inps) == 2:
                    for i in checks_target_inps:
                        i.click()

            except StaleElementReferenceException:
                time.sleep(self.MEDIUM_DELAY)
                continue

    def enter_api_name(self):
        notes_inps = self.driver.find_elements(by=By.CLASS_NAME, value='line_group')
        for notes_inp in notes_inps:
            if 'Notes' in notes_inp.get_attribute('innerHTML'):
                note_inp = notes_inp.find_element(by=By.TAG_NAME, value='input')
                note_inp.send_keys(str(datetime.utcnow().date()))

    def click_create_api(self):
        create_btn = self.driver.find_element(by=By.CSS_SELECTOR, value='button.text_button.table_button')
        create_btn.click()

    def click_all_permissions_2(self):
        check_inps = []

        timer = 0
        while len(check_inps) < 3:
            check_inps = self.driver \
                .find_element(by=By.CLASS_NAME, value='v--modal-box.v--modal') \
                .find_elements(by=By.CLASS_NAME, value='ui-checkbox-input')
            time.sleep(self.MEDIUM_DELAY)
            timer += 1
            if timer > 2:
                return

        for check_inp in check_inps:
            if check_inp.get_attribute('value') != check_inp.get_attribute('true-value'):
                check_inp.click()
        print("2 checks series successfully clicked")

    def click_confirm_button(self):
        confirm_buttons = self.driver.find_elements(by=By.CLASS_NAME, value='confirm')
        for i in confirm_buttons:
            if 'I understand' in i.get_attribute('outerHTML'):
                i.click()
                print("Confirm button successfully clicked")
                break

    def click_send_code_button(self, flag=False):
        while flag:
            while True:
                try:
                    links = self.driver.find_element(by=By.CLASS_NAME, value='e_input_control') \
                        .find_elements(by=By.TAG_NAME, value='a')
                    break
                except NoSuchElementException:
                    time.sleep(self.LARGE_DELAY)
            for i in links:
                if 'click to resend' or 'send again' in i.get_attribute('outerHTML').lower():
                    i.click()
                    print("Resend code link successfully clicked")
                    return
            time.sleep(self.MEDIUM_DELAY)

    def enter_api_code(self, code):
        api_code_inp = self.driver.find_element(by=By.ID, value='email')
        print("Code is: ", code)
        api_code_inp.clear()
        api_code_inp.send_keys(code)
        api_code_inp.clear()
        time.sleep(2)
        api_code_inp.send_keys(code)
        print("Code successfully entered")

    def click_api_code_confirm_button_1(self):
        button = self.driver.find_element(by=By.CSS_SELECTOR, value='button.text_button')
        button.click()
        print("Click create code button before getting keys")

    def click_api_code_confirm_button_2(self):
        buttons = self.driver.find_elements(by=By.CSS_SELECTOR, value='button.text_button')
        for button in buttons:
            if 'confirm' in button.get_attribute('outerHTML').lower():
                button.click()
                break
        print("Click create code button after getting keys")

    def get_api_keys(self):
        keys = []
        while len(keys) < 2:
            try:
                keys = self.driver.find_elements(by=By.CLASS_NAME, value='content_left')
            except NoSuchElementException:
                time.sleep(self.MEDIUM_DELAY)
        api_key = ''
        api_secret = ''

        s = keys[0].get_attribute('outerHTML')
        for i in range(len(s)):
            if s[i] == '>':
                j = i + 1
                while s[j] != '<':
                    api_key += s[j]
                    j += 1
                break

        s = keys[1].get_attribute('outerHTML')
        for i in range(len(s)):
            if s[i] == '>':
                j = i + 1
                while s[j] != '<':
                    api_secret += s[j]
                    j += 1
                break
        self.item['API_KEY'] = api_key
        self.item['API_SECRET'] = api_secret

        return api_key, api_secret

    def create_api_keys(self):
        print("Starting creating API keys...")
        self._switch_to_site('huobi')
        time.sleep(self.LARGE_DELAY)
        self.driver.get('https://www.huobi.com/en-us/apikey/')
        self.click_all_permissions_1()
        self.enter_api_name()
        self.click_create_api()
        self.click_all_permissions_2()
        self.click_confirm_button()
        self.click_send_code_button()

        code = self.get_register_code()
        self._switch_to_site('huobi')
        self.enter_api_code(code)
        self.click_api_code_confirm_button_1()

        keys = self.get_api_keys()
        print("Keys received: ", keys)
        self.click_api_code_confirm_button_2()

    def put_chain_name_as_algo(self):
        done = False
        counter = 0
        while not done:
            counter += 1
            if counter > 3:
                counter = 0
                self.driver.refresh()
            try:
                select_dlg = self.driver.find_elements(by=By.CSS_SELECTOR, value='div.ui-select.ui-select-large')
                cnt = 0

                element = None
                for i in select_dlg:
                    cnt += 1
                    if cnt == 2:
                        element = i
                        element.click()
                        break
                select_dv = element.find_elements(by=By.CLASS_NAME, value='ui-select-option')
                for i in select_dv:
                    if 'algo' in i.get_attribute('outerHTML').lower():
                        i.click()
                        print("ALGO chain placed success")
                        done = True
                        break
            except (ElementNotInteractableException, NoSuchElementException, StaleElementReferenceException):
                time.sleep(self.MEDIUM_DELAY)
                continue

    def put_algo_address_and_notes(self):
        done = False
        while not done:
            try:
                inps = self.driver.find_elements(by=By.CSS_SELECTOR, value='div.ui-input.ui-input-large')
                cnt = 0
                for i in inps:
                    if 'Address' in i.get_attribute('innerHTML'):
                        i.find_element(by=By.TAG_NAME, value='input').send_keys(self.ALGO_ADDRESS)
                        print("Algo address placed success")
                        cnt += 1
                    if 'Notes' in i.get_attribute('innerHTML'):
                        i.find_element(by=By.TAG_NAME, value='input').send_keys(self.ALGO_ADDRESS)
                        print("Notes placed success")
                        cnt += 1
                    if cnt == 2:
                        done = True
                        return
            except (ElementNotInteractableException, NoSuchElementException, StaleElementReferenceException):
                time.sleep(self.MEDIUM_DELAY)
                continue

    def click_confirm_algo_address(self):
        while True:
            try:
                button = self.driver.find_element(
                    by=By.CSS_SELECTOR,
                    value='button.ui-button.button-action.ui-button-primary.ui-button-large'
                )
                button.click()
                break

            except (ElementNotInteractableException, NoSuchElementException, StaleElementReferenceException):
                time.sleep(self.MEDIUM_DELAY)
                continue

    def open_algo_deposit(self):
        print('Starting opening Algo deposit...')
        self._switch_to_site('huobi')
        self.driver.get('https://www.huobi.com/en-us/finance/address/')
        self.put_chain_name_as_algo()
        self.put_algo_address_and_notes()
        self.click_confirm_algo_address()

        self.click_send_code_button()
        code = self.get_register_code()
        self._switch_to_site('huobi')
        self.enter_api_code(code)
        self.click_api_code_confirm_button_1()

    def logout_huobi(self):
        self._switch_to_site('huobi')
        while True:
            try:
                menu_button = self.driver.find_element(by=By.CSS_SELECTOR, value='div.fedui-header-info')
                menu_button.click()

                links = menu_button.find_elements(by=By.CSS_SELECTOR, value='a.last-child')
                for i in links:
                    if 'sign out' in i.get_attribute('outerHTML').lower():
                        i.click()
                        time.sleep(self.MEDIUM_DELAY * 2)
                        self.driver.get('https://www.huobi.com/en-us/register/')
                        return
                time.sleep(self.MEDIUM_DELAY)
            except (ElementNotInteractableException, NoSuchElementException, StaleElementReferenceException):
                time.sleep(self.MEDIUM_DELAY)
                continue
        self.driver.get('https://www.huobi.com/en-us/register/')

    def refresh_mail(self):
        self._switch_to_site('10minutemail')
        self.driver.get('https://10minutemail.net/new.html')
        time.sleep(1)

    def out_account(self):
        with open('accounts.json') as file:
            js = json.load(file)
            js.append(self.item)
        with open('accounts.json', 'w') as file:
            json.dump(js, file, indent=2)

    def run(self):
        self.open_pages()
        while True:
            self.item = dict()
            self.code_cache = set()

            with self.driver:
                self.register()
                time.sleep(self.LARGE_DELAY * 2.5)
                self.create_api_keys()
                self.open_algo_deposit()
                time.sleep(self.LARGE_DELAY)
                self.out_account()
                self.logout_huobi()
                self.refresh_mail()

            self.driver.quit()
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')
            options.add_argument('--allow-profiles-outside-user-dir')
            options.add_argument('--enable-profile-shortcut-manager')
            options.add_argument(r'user-data-dir=.\User')
            options.add_argument('--profile-directory=Profile 1')
            self.driver = uc.Chrome(options=options)
            self.open_pages()
            print("--------------------------------------------------------------------------")

while True:
    try:
        worker = CreateHuobiAccount()
        worker.run()
    except RuntimeError:
        continue
        worker.driver.quit()
        continue
