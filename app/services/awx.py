import time
import traceback
import requests
import logging
import yaml

from datetime import datetime as dt
from typing import (List,
                    Optional,
                    )

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class AnsibleCrawler:
    def __init__(self, app_name: str, profile: str, project: str):
        # profile 값에 따라 AWX 서버 정보 변경
        if profile == "prod":
            self.target_url = "http://awx.wemakeprice.kr"
            self.inventory_index = 1
        else:
            self.target_url = "http://awx-dev.wemakeprice.kr"
            self.inventory_index = 2

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--incognito')
        chrome_options.add_argument('--headless')

        # default 106으로 설정되어 있으나 Google S3상 해당 버전의 드라이버가 없는 모습
        # 105.0.5195.52 버전으로 명시
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager(version="105.0.5195.52").install()),
                                       options=chrome_options)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers = self.headers

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.logger.info(f'crawler init (URL: {app_name}, profile: {profile})')

        self.app_name = app_name
        self.profile = profile
        self.project = project

    def _awx_login(self):
        awx_id = 'jenkins'
        awx_pw = 'dlswmd.!'
        id_tag = self.driver.find_elements(By.ID, 'pf-login-username-id')
        pw_tag = self.driver.find_elements(By.ID, 'pf-login-password-id')
        login_btn = self.driver.find_elements(By.CLASS_NAME, 'pf-c-button')

        print(id_tag[0], pw_tag[0])
        print(f'login button: {login_btn[0]}')

        id_tag[0].send_keys(awx_id)
        pw_tag[0].send_keys(awx_pw)
        login_btn[0].click()

        # Wait loading time
        time.sleep(1)

        self.driver.get(self.target_url + '/#/inventories/inventory/' + str(self.inventory_index) + '/sources/add')

        return

    def make_inven(self):
        """
        wemakeprice ansible inventory making
        :return:
        """
        ret = 0

        try:
            today = dt.now()
            today = today.strftime("%y%m%d.%H%M")
            print(f'time {today}')

            self._awx_login()

            # Move to inventory page
            # index 2 is Dev-AWX inventory index
            # self.driver.get(self.target_url + '/#/inventories/inventory/2/sources/add')
            self.driver.implicitly_wait(1)
            input_list = self.driver.find_elements(By.CLASS_NAME, 'pf-c-form-control')

            # print(f'{len(input_list)}')
            tag_input_name = input_list[0]
            tag_input_name.send_keys(self.app_name)

            # Source 'SCM' 선택
            dropdown_src = Select(input_list[2])
            dropdown_src.select_by_value('scm')
            self.driver.implicitly_wait(1)

            # 직접 senc key하는 방법으로는 안됨
            btn_project = self.driver.find_elements(By.ID, 'project')
            # print(f'{len(btn_project)}')
            btn_project[0].click()

            # select project input에 awx_project 이름 넣기
            project_wrapper = self.driver.find_elements(By.CLASS_NAME, 'pf-m-filter-group')
            project_wrapper_input = project_wrapper[0].find_element(By.CSS_SELECTOR, "input[class='pf-c-form-control']")
            project_wrapper_input.send_keys(self.project)

            # select project 버튼 클릭
            project_wrapper_btn = project_wrapper[0].find_elements(By.CSS_SELECTOR, "button[aria-label='Search submit button']")
            project_wrapper_btn[0].click()
            time.sleep(1)

            radio_projects = self.driver.find_elements(By.CLASS_NAME, 'pf-c-data-list__item-content')
            # # 프로젝트 선택을 파라미터에 따라 설정할 수 있는 방안을 확인해야 한다.
            # for item in radio_projects:
            #     inner_text = item.text
            #     print(inner_text)
            #     if self.project in inner_text:
            #         radio_project = item

            radio_projects[0].click()
            btn_select = self.driver.find_elements(By.CLASS_NAME, 'pf-m-primary')
            # print(f'{len(btn_select)}')
            btn_select = btn_select[2]
            btn_select.click()
            '''
            Select TAG의 값을 입맛에 맞게 수정하는 과정 진행
            '''
            # inventory/dev/host를 가지고 오지 못하는 경우도 있음..
            # 무조건 가장 첫번째 항복을 선택하도록?
            source_id = self.driver.find_element(By.ID, 'source_path')

            # 파싱 범위 제한, 항상 존재할 수 있는 마지막 항목을 수정하는 식으로 수정
            option_in_select = source_id.find_element(By.CSS_SELECTOR, "option[value='/ (project root)']")

            # js로 속성, 텍스트 수정하는 로직
            # AWX 18.* 문제로 인한 대응 방안
            self.driver.execute_script(
                f"arguments[0].setAttribute('value', 'inventories/{self.app_name}/{self.profile}/hosts')",
                option_in_select)

            self.driver.execute_script(
                f"arguments[0].textContent = 'inventories/{self.app_name}/{self.profile}/hosts';",
                option_in_select)

            dropdown_host = Select(self.driver.find_element(By.ID, 'source_path'))
            # print(dropdown_host)
            dropdown_host.select_by_value(f'inventories/{self.app_name}/{self.profile}/hosts')

            checkbox_options = self.driver.find_elements(By.CLASS_NAME, 'pf-c-check__input')
            print(f'{len(checkbox_options)}')
            opt_overwrite = checkbox_options[0]
            opt_overwrite_vars = checkbox_options[1]
            opt_overwrite.click()
            opt_overwrite_vars.click()

            btn_select = self.driver.find_elements(By.CLASS_NAME, 'pf-m-primary')
            # save button click
            btn_select = btn_select[1]
            btn_select.click()

            # Sleep for page loading time
            time.sleep(1)
            btns_sync = self.driver.find_elements(By.CLASS_NAME, "pf-m-secondary")

            # sync button click
            btn_sync = btns_sync[1]
            btn_sync.click()

        except Exception:
            traceback.print_exc()
            ret = -1

        finally:
            time.sleep(5)
            self.driver.quit()
            print('Quit crawling')
            return ret
