import os
import shutil
import re
import requests
from bs4 import BeautifulSoup
import concurrent.futures

courselist_url = "http://zhwx.jhjw.cn/ajax/Course.ashx"
courselist_payload = "mydate=1721143100488&actionname=possessCourse&pagesize=200&uid=8435&currpage=1&type="
courselist_headers = {
    'Host': 'zhwx.jhjw.cn',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/6.8.0(0x16080000) MacWechat/3.8.8(0x13080812) XWEB/1216 Flue',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'http://zhwx.jhjw.cn',
    'Referer': 'http://zhwx.jhjw.cn/PossessCourse.aspx',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cookie': 'Cookies_PTZX_OpenID=oeW3J5w13PcCIC7ggFoXYoGHm7_E; .ASPXAUTH=0C086A935CB61F7BC6ADB201C38207941A3A5E6CE38C0CB2C53EA82142F2C321F1EE02989B3EB8C8E30864068E955B0C34362F13B2B76DAE46213804CE41BBB1DDECF1FA509A09779F1E954D0D410AE3DB0CD5C988F3F3E983E1DCD1708AD9645DE630C03515C7D2E5D5429E4AC6B5F0B91E8FC21299E9269F0AE7C9C26C622A7B0D6AFCE05499D60FBDCF7E4832B5336A50198A722B3303A1B99772B957D12AAB39AF32B8275EBC19D57A403EE8E841'
}
class_url = "http://zhwx.jhjw.cn/CourseInformation.aspx?id="
class_headers = {
    'Host': 'zhwx.jhjw.cn',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/6.8.0(0x16080000) MacWechat/3.8.8(0x13080812) XWEB/1216 Flue',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Referer': 'http://zhwx.jhjw.cn/PossessCourse.aspx',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cookie': 'Cookies_PTZX_OpenID=oeW3J5w13PcCIC7ggFoXYoGHm7_E; .ASPXAUTH=0C086A935CB61F7BC6ADB201C38207941A3A5E6CE38C0CB2C53EA82142F2C321F1EE02989B3EB8C8E30864068E955B0C34362F13B2B76DAE46213804CE41BBB1DDECF1FA509A09779F1E954D0D410AE3DB0CD5C988F3F3E983E1DCD1708AD9645DE630C03515C7D2E5D5429E4AC6B5F0B91E8FC21299E9269F0AE7C9C26C622A7B0D6AFCE05499D60FBDCF7E4832B5336A50198A722B3303A1B99772B957D12AAB39AF32B8275EBC19D57A403EE8E841; Cookies_PTZX_OpenID=oeW3J5w13PcCIC7ggFoXYoGHm7_E; Cookies_PTZX_OpenID=oeW3J5w13PcCIC7ggFoXYoGHm7_E'
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