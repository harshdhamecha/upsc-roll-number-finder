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
logging.getLogger('ppocr').setLevel(logging.ERROR)


rec_model = PaddleOCR(lang='en')
unattended_roll_numbers = []


# Function to generate all possible roll numbers list
def generate_roll_numbers():
    roll_numbers = []
    for i in range(1000134, 10000000):  # Start from 1000000 (7 digits)
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


def find_roll_number():

    global unattended_roll_numbers

    base_url = "https://upsconline.nic.in/marksheet/csp_premark_2023/login.php"
    success_page_url = "https://upsconline.nic.in/marksheet/csp_premark_2023/view_detail.php?tikl="

    roll_numbers = generate_roll_numbers()
    roll_numbers = ['1234567', '7654321', '7200344', '1221213']
    driver = webdriver.Chrome()
    driver.get(base_url)

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
            month_dropdown.select_by_visible_text("Aug")

            # Select the year (1999) from the dropdown using Select class
            year_dropdown = Select(driver.find_element(By.CLASS_NAME, "ui-datepicker-year"))
            year_dropdown.select_by_visible_text("1999")

            # Find and click on the date 4th in the date picker
            day_18 = driver.find_element(By.XPATH, "//a[text()='4']")
            day_18.click()

            time.sleep(1)

            # Take a screenshot of the entire webpage
            driver.save_screenshot("screenshot.png")
            captcha_image = cv2.imread("screenshot.png")
            captcha_crop = captcha_image[450: 500, 650: 830, :]
            cv2.imwrite("captcha.png", captcha_crop)

            captcha_text = get_captcha_text("captcha.png")

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
                    return roll_number
                
                else:
                    continue

        except Exception as e:
            print(e)

    driver.quit()
    return None  # Roll number not found


found_roll_number = find_roll_number()
if found_roll_number:
    print("Roll Number Found:", found_roll_number)
else:
    print("Roll Number Not Found")
print('*' * 30)
print(f'Unattended Roll numbers: {unattended_roll_numbers}')
print('*' * 30)
