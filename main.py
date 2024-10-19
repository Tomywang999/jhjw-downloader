import os
import shutil
import re
import requests
from bs4 import BeautifulSoup
import concurrent.futures

courselist_url = "http://zhwx.jhjw.cn/ajax/Course.ashx"
courselist_payload = "mydate=<timestamp>&actionname=possessCourse&pagesize=200&uid=<uid>&currpage=1&type="
courselist_headers = {
    'Host': 'zhwx.jhjw.cn',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (compatible; ExampleBot/0.1; +http://example.com/bot)',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'http://zhwx.jhjw.cn',
    'Referer': 'http://zhwx.jhjw.cn/PossessCourse.aspx',
    'Accept-Language': 'en-US,en;q=0.9',
    # 'Cookie': 'Cookies_PTZX_OpenID=<open_id>; .ASPXAUTH=<auth_token>', # Remove or secure sensitive cookie information
}
class_url = "http://zhwx.jhjw.cn/CourseInformation.aspx?id="
class_headers = {
    'Host': 'zhwx.jhjw.cn',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (compatible; ExampleBot/0.1; +http://example.com/bot)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Referer': 'http://zhwx.jhjw.cn/PossessCourse.aspx',
    'Accept-Language': 'en-US,en;q=0.9',
    # 'Cookie': 'Cookies_PTZX_OpenID=<open_id>; .ASPXAUTH=<auth_token>', # Remove or secure sensitive cookie information
}
# Get the newest course list (Product list)
courselist = requests.request("POST", courselist_url, headers=courselist_headers, data=courselist_payload).json()
course_ids = [item['CS_ID'] for item in courselist['mydata']]
course_names = [item['C_Name'] for item in courselist['mydata']]
#print(course_ids)
#print(course_names)

def download_video(video_url, folder_path, video_name):
    response = requests.get(video_url, stream=True)
    with open(os.path.join(folder_path, video_name), 'wb') as file:
        shutil.copyfileobj(response.raw, file)
    # Return a success message including the video name
    return f"{video_name} downloaded successfully"

def sanitize_filename(filename):
    # Remove unwanted numbers and patterns from filename
    filename = re.sub(r'\d+', '', filename)  # Remove all digits
    # Keep only letters, spaces, periods, and underscores
    filename = "".join([c for c in filename if c.isalpha() or c in [' ', '.', '_']]).rstrip()
    return filename

for course_id, course_name in zip(course_ids, course_names):
    response = requests.get(f"{class_url}{course_id}", headers=class_headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    video_divs = soup.find_all('div', class_='videos')

    folder_name = f"{course_id}_{sanitize_filename(course_name)}"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Prepare a list of all video download tasks
    download_tasks = []
    for video_div in video_divs:
        video_url = video_div['data-address']
        video_title_div = video_div.find_previous_sibling('div')
        if video_title_div:
            video_title = video_title_div.get_text(strip=True)
            video_name = sanitize_filename(video_title) + ".mp4"
        else:
            video_name = "Unnamed_Video.mp4"
        download_tasks.append((video_url, folder_name, video_name))

    # Use ThreadPoolExecutor to download videos concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(download_video, task[0], task[1], task[2]) for task in download_tasks]
        for future in concurrent.futures.as_completed(futures):
            print(f"Download completed: {future.result()}")
