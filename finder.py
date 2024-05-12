import argparse
from tqdm import tqdm
import re
from paddleocr import PaddleOCR
import cv2
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
logging.getLogger('ppocr').setLevel(logging.ERROR)


rec_model = PaddleOCR(lang='en')
unattended_roll_numbers = []


# Function to generate all possible roll numbers list
def generate_roll_numbers(start, stop):
    roll_numbers = []
    for i in range(start, stop):  # Start from 1000000 (7 digits)
        roll_numbers.append(str(i))
    return roll_numbers


# Function to extract captcha text from image
def get_captcha_text(image_path):
    try:
        captcha_image = cv2.imread(image_path)
        result = rec_model.ocr(captcha_image)
        captcha_text = ' '.join([line[1][0] for line in result[0]])
        captcha_text = re.sub(r'[^a-zA-Z0-9]', '', captcha_text)  
        return captcha_text.strip()
    except:
        return None


def find_roll_number(args):

    global unattended_roll_numbers
    window = args.window

    base_url = "https://upsconline.nic.in/marksheet/csp_premark_2023/login.php"
    success_page_url = "https://upsconline.nic.in/marksheet/csp_premark_2023/view_detail.php?tikl="

    name = 'NIKHILESH'
    xpath = f"//*[@id='getItP']/div/div/div[2]/div/div/table[1]/tbody/tr[4]/td[2][contains(text(), '{name}')]"

    roll_numbers = generate_roll_numbers(args.start, args.stop)
    chrome_options = Options()
    if args.headless: chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    for roll_number in tqdm(roll_numbers):

        try:
            driver.refresh()
            driver.get(base_url)

            # Find and fill the roll number input field
            rollno_input = driver.find_element(By.NAME, "candidate_rollno")
            rollno_input.send_keys(roll_number)

            # Find and fill the date of birth input field
            dob_input = driver.find_element(By.NAME, "dobrollno")
            dob_input.click()

            # Wait for the date picker to fully load (adjust wait time as needed)
            wait = WebDriverWait(driver, 5)
            wait.until(EC.visibility_of_element_located((By.ID, "ui-datepicker-div")))

            # Select the month (August) from the dropdown using Select class
            month_dropdown = Select(driver.find_element(By.CLASS_NAME, "ui-datepicker-month"))
            month_dropdown.select_by_visible_text("May")

            # Select the year (1999) from the dropdown using Select class
            year_dropdown = Select(driver.find_element(By.CLASS_NAME, "ui-datepicker-year"))
            year_dropdown.select_by_visible_text("1999")

            # Find and click on the date 4th in the date picker
            day_18 = driver.find_element(By.XPATH, "//a[text()='18']")
            day_18.click()

            time.sleep(1)

            # Take a screenshot of the entire webpage
            driver.save_screenshot(f"screenshot_{window}.png")
            captcha_image = cv2.imread(f"screenshot_{window}.png")
            captcha_crop = captcha_image[360: 400, 440: 570, :]
            cv2.imwrite(f"captcha_{window}.png", captcha_crop)

            captcha_text = get_captcha_text(f"captcha_{window}.png")

            if captcha_text is None:
                unattended_roll_numbers.append(roll_number)

            else:
                # Find and fill the captcha input field
                captcha_input = driver.find_element(By.NAME, "letters_code")
                captcha_input.send_keys(captcha_text)

                # Find and click the submit button
                submit_button = driver.find_element(By.NAME, "submitrollnofrm")
                submit_button.click()

                # Wait for the page to load after form submission
                WebDriverWait(driver, 5).until(EC.url_contains(success_page_url))

                # Check if the results page indicates success
                if success_page_url in driver.current_url:
                    time.sleep(1)
                    try:
                        name_element = wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
                        if name_element:
                            return roll_number
                    except:
                        pass
                
        except Exception as e:
            print(e)

    driver.quit()
    return None  # Roll number not found


def parse_args():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, help='roll number from which to start')
    parser.add_argument('--stop', type=int, help='roll number at which to stop')
    parser.add_argument('--window', type=int, help='nth window (for saving captch iamge)')
    parser.add_argument('--headless', action='store_true', help='whether to run in headless or not')
    args = parser.parse_args()
    
    return args


if __name__ == '__main__':
    args = parse_args()
    found_roll_number = find_roll_number(args)
    if found_roll_number:
        print("Roll Number Found:", found_roll_number)
    else:
        print("Roll Number Not Found")
    print('*' * 30)
    print(f'Unattended Roll numbers: {unattended_roll_numbers}')
    print('*' * 30)
