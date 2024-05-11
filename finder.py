from tqdm import tqdm
import re
from paddleocr import PaddleOCR
import cv2
import time
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

rec_model = PaddleOCR(lang='en')
unattended_roll_numbers = []


def generate_roll_numbers():
    roll_numbers = []
    for i in range(1000000, 10000000):  # Start from 1000000 (7 digits)
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

    # roll_numbers = ['1234512', '1234568', '1231231', '7200344']
    roll_numbers = ['7200344']

    driver = webdriver.Chrome()
    driver.get(base_url)

    for roll_number in tqdm(roll_numbers):

        try:
            driver.refresh()
            # Find and fill the roll number input field
            rollno_input = driver.find_element(By.NAME, "candidate_rollno")
            rollno_input.clear()
            rollno_input.send_keys(roll_number)

            # Find and fill the date of birth input field
            dob_input = driver.find_element(By.NAME, "dobrollno")
            dob_input.click()

            # Wait for the date picker to fully load (adjust wait time as needed)
            wait = WebDriverWait(driver, 10)
            wait.until(EC.visibility_of_element_located((By.ID, "ui-datepicker-div")))

            # Select the month (August) from the dropdown using Select class
            month_dropdown = Select(driver.find_element(By.CLASS_NAME, "ui-datepicker-month"))
            month_dropdown.select_by_visible_text("Aug")

            # Select the year (1999) from the dropdown using Select class
            year_dropdown = Select(driver.find_element(By.CLASS_NAME, "ui-datepicker-year"))
            year_dropdown.select_by_visible_text("1999")

            # Find and click on the date 4th in the date picker
            day_4 = driver.find_element(By.XPATH, "//a[text()='4']")
            day_4.click()

            time.sleep(2)
            # Find the captcha image element
            captcha_img = driver.find_element(By.CSS_SELECTOR, "img#captchaimgroll")  # Adjust the ID as per your HTML

            # Get the location and size of the captcha image
            x = captcha_img.location['x']
            y = captcha_img.location['y']
            width = captcha_img.size['width']
            height = captcha_img.size['height']
            
            print('\n', x, y, width, height)

            # Take a screenshot of the entire webpage
            driver.save_screenshot("screenshot.png")
            captcha_image = Image.open("screenshot.png")
            captcha_crop = captcha_image.crop((x, y, x + width, y + height))
            captcha_crop.save("captcha.png")
            # captcha_image = cv2.imread("screenshot.png")
            # captcha_crop = captcha_image[y: y+height, x: x+width, :]
            # cv2.imwrite("captcha.png", captcha_crop)

            captcha_text = get_captcha_text("captcha.png")

            print('\n', captcha_text)

            if captcha_text is None:
                unattended_roll_numbers.append(roll_number)

            else:
                # Find and fill the captcha input field
                captcha_input = driver.find_element(By.NAME, "letters_code")
                # captcha_input.clear()
                captcha_input.send_keys(captcha_text)

                # Find and click the submit button
                submit_button = driver.find_element(By.NAME, "submitrollnofrm")
                submit_button.click()

                # Wait for the page to load after form submission
                WebDriverWait(driver, 10).until(EC.url_contains(success_page_url))

                # Check if the results page indicates success
                if success_page_url in driver.current_url:
                    return roll_number
                
        except Exception as e:
            print(e)
            unattended_roll_numbers.append(roll_number)

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
