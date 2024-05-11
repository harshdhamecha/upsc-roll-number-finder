import requests
from bs4 import BeautifulSoup
# import pytesseract
from PIL import Image
from tqdm import tqdm
import re
from paddleocr import PaddleOCR
import cv2

rec_model = PaddleOCR(lang='en')
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def generate_roll_numbers():
    roll_numbers = []
    for i in range(1000000, 10000000):  # Start from 1000000 (7 digits)
        roll_numbers.append(str(i))
    return roll_numbers


# Function to extract captcha text from image
def get_captcha_text(image_path):
    captcha_image = cv2.imread(image_path)
    result = rec_model.ocr(captcha_image)
    captcha_text = ' '.join([line[1][0] for line in result[0]])
    # captcha_text = pytesseract.image_to_string(captcha_image)
    captcha_text = re.sub(r'[^a-zA-Z0-9]', '', captcha_text)  # Keep only alphanumeric characters
    return captcha_text.strip()


# # Function to scrape the results page and submit roll numbers
# def find_roll_number():
#     base_url = "https://upsconline.nic.in/marksheet/csp_premark_2023/login.php"
#     success_page_url = "https://upsconline.nic.in/marksheet/csp_premark_2023/view_detail.php?tikl="

#     # Assuming you have a list of possible roll numbers to try
#     # roll_numbers = generate_roll_numbers()
#     # birth_date = "18/05/1999"

#     roll_numbers = ['7200344']
#     birth_date = "04/08/1999"

#     for roll_number in tqdm(roll_numbers):
#         # Get the captcha image URL and download the image
#         response = requests.get(base_url)
#         soup = BeautifulSoup(response.content, "html.parser")
#         captcha_image_url = "https://upsconline.nic.in/marksheet/csp_premark_2023/" + soup.find("img", {"id": "captchaimgroll"})["src"]
#         captcha_image = requests.get(captcha_image_url)

#         # Save the captcha image
#         with open("captcha.png", "wb") as f:
#             f.write(captcha_image.content)

#         # Solve the captcha
#         captcha_text = get_captcha_text("captcha.png")
#         print(captcha_text)
#         # Submit the form with roll number, birth date, and captcha text
#         payload = {
#             "candidate_rollno": roll_number,
#             "dobrollno": birth_date,
#             "letters_code": captcha_text,
#             "submitrollnofrm": "Submit"
#         }
#         print(payload)
#         response = requests.post(base_url, data=payload)
#         print(response.status_code)
#         # print(response.text)
#         # Check if the results page indicates success
#         if success_page_url in response.url:
#             return roll_number

#     return None  # Roll number not foundsss


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from PIL import Image


from tqdm import tqdm
import time

def find_roll_number_selenium():
    base_url = "https://upsconline.nic.in/marksheet/csp_premark_2023/login.php"
    success_page_url = "https://upsconline.nic.in/marksheet/csp_premark_2023/view_detail.php?tikl="

    roll_numbers = ['7200344']
    birth_date = "04/08/1999"

    driver = webdriver.Chrome()
    driver.get(base_url)

    for roll_number in tqdm(roll_numbers):
        # Find and fill the roll number input field
        rollno_input = driver.find_element(By.NAME, "candidate_rollno")
        rollno_input.clear()
        rollno_input.send_keys(roll_number)

        # Find and fill the date of birth input field
        dob_input = driver.find_element(By.NAME, "dobrollno")
        # dob_input.clear()
        # dob_input.send_keys(birth_date)
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

        time.sleep(5)
        captcha_image_element = driver.find_element(By.ID, "captchaimgroll")  # Adjust selector as needed
        # captcha_image_url = captcha_image_element.get_attribute("src")
        # print(captcha_image_url)
        # response = requests.get(captcha_image_url)
        # #  Save the image to a file
        # with open("captcha.png", "wb") as f:
        #     f.write(response.content)

        # Get the location and size of the captcha image
        x = captcha_image_element.location['x']
        y = captcha_image_element.location['y']
        width = captcha_image_element.size['width']
        height = captcha_image_element.size['height']

        # Take a screenshot of the entire webpage
        driver.save_screenshot("screenshot.png")
        print(x, y, width, height)
        # Crop the screenshot to the captcha image region using Pillow
        # captcha_image = Image.open("screenshot.png")
        # captcha_crop = captcha_image.crop((x, y, x + width, y + height))
        # captcha_crop.save("captcha.png")
        captcha_image = cv2.imread('screenshot.png')
        captcha_crop = captcha_image[450: 500, 650: 830, :]
        cv2.imwrite('captcha.png', captcha_crop)

        captcha_text = get_captcha_text("captcha.png")
        print(captcha_text)

        # Find and fill the captcha input field
        captcha_input = driver.find_element(By.NAME, "letters_code")
        # captcha_input.clear()
        captcha_input.send_keys(captcha_text)

        # Find and click the submit button
        submit_button = driver.find_element(By.NAME, "submitrollnofrm")
        submit_button.click()

        # Wait for the page to load after form submission
        WebDriverWait(driver, 20).until(EC.url_contains(success_page_url))

        # Check if the results page indicates success
        if success_page_url in driver.current_url:
            return roll_number

    driver.quit()
    return None  # Roll number not found

found_roll_number = find_roll_number_selenium()
if found_roll_number:
    print("Roll Number Found:", found_roll_number)
else:
    print("Roll Number Not Found")


# Main program
# found_roll_number = find_roll_number()
# if found_roll_number:
#     print("Roll Number Found:", found_roll_number)
# else:
#     print("Roll Number Not Found")
