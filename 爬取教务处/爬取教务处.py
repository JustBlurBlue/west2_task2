from multiprocessing.dummy import Pool
import csv, json, os, re, requests, sys
from fake_useragent import UserAgent
from lxml import etree
from tqdm import *
import time as timex

time1 = timex.time()
# 初始化线程池
pool = Pool(7)
pool2 = Pool(1)
#计数器
counter = 0
# 将csv文件清空
with open('notices.csv', 'w', newline='', encoding='utf-8') as csvfiled:
    pass
with open('output.csv', 'w', newline='', encoding='utf-8') as csvfilee:
    pass
class Crawler:
    def __init__(self):
        self.headers = {
            'User-Agent': UserAgent().random,
        }
    def craw_get(self,url):
        self.headers['User-Agent'] = UserAgent().random
        response = requests.get(url, headers=self.headers)
        response.encoding = 'utf-8'
        return response.text
    def craw_post(self,url, data):
        self.headers['User-Agent'] = UserAgent().random
        response = requests.post(url, headers=self.headers, data=data)
        response.encoding = 'utf-8'
        return response.text
    def craw_get_content(self,url):
        self.headers['User-Agent'] = UserAgent().random
        response = requests.get(url, headers=self.headers)
        return response.content

class analysis():
    def __init__(self,html):
        self.html = html
        self.tree = etree.HTML(html)
    def xpath(self,xpath):
        elements = self.tree.xpath(xpath)
        return elements
    def re(self,pattern):
        return re.findall(pattern, self.html, re.S)
def sanitize_filename(filename):
    # 移除不合法的字符
    return re.sub(r'[<>:"/\\|?*]', '_', filename)
def clear_terminal():
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()
# 进度条
def progress_bar(current, total, desc="Processing"):
    clear_terminal()
    percent = (current + 1) / total * 100
    bar = '#' * int(percent // 2) + '-' * (50 - int(percent // 2))
    sys.stdout.write(f'\r{desc}: [{bar}] {percent:.2f}%')
    sys.stdout.flush()
    if current + 1 == total:
        sys.stdout.write('\n')

def check_download(row):
    global counter
    url = row[3]
    html = Crawler.craw_get(url)
    attch_elements = None
    try:
        attch_elements = analysis(html).xpath('/html/body/div/div[2]/div[2]/form/div/div[1]/div/ul/li')
    except:
        return
    num = len(attch_elements)
    if num == 0:
        row[6] = None
        row[5] = None
        notice_dict = {'title': row[1], 'href': row[3], 'time': row[2], 'department': row[0], 'attachment': row[4],
                       'downloaded': row[6], 'downloaded_all': row[5]}
        with open('output.csv', 'a', newline='', encoding='utf-8') as csvfilee:
            # 定义字段名（字典的键）
            fieldnames = ['department', 'title', 'time', 'href', 'attachment', 'downloaded_all', 'downloaded']
            # 创建 DictWriter 对象
            writer = csv.DictWriter(csvfilee, fieldnames=fieldnames)
            # 如果文件为空，则写入表头
            if csvfilee.tell() == 0:
                writer.writeheader()
            # 将字典写入 CSV 文件
            writer.writerow(notice_dict)
            counter += 1
            progress_bar(counter, sum_all, desc="Checking and Downloading")
            print("\t无附件")
        return

    row[4] = num
    download_list = []
    sum = 0
    sanitized_folder_name = sanitize_filename(f'{row[2]}_{row[0]}{row[1]}')
    if not os.path.exists("attachments/"+sanitized_folder_name) and num != 0:
        os.mkdir("attachments/"+sanitized_folder_name)
    for i in attch_elements:
        # 提取附件链接，并下载保存
        url = i.xpath('./a/@href')[0]
        url = "https://jwch.fzu.edu.cn" + url
        print(url)
        title = sanitize_filename(f"{i.xpath('./a/text()')[0]}")
        title = title.strip()
        response = Crawler.craw_get_content(url)
        file_path = f'attachments/{sanitized_folder_name}/{title}'
        with open(file_path, 'wb') as f:
            f.write(response)
        print(f'{title}下载成功')
        # 记录下载次数
        pathx = i.xpath('.//text()')[3]
        pathx = re.findall("getClickTimes(.*?),", pathx)[0][1:]
        k = Crawler.craw_get(f"https://jwch.fzu.edu.cn/system/resource/code/news/click/clicktimes.jsp?wbnewsid={pathx}&owner=1744984858&type=wbnewsfile&randomid=nattach")
        k = json.loads(k)
        numx = (k["wbshowtimes"])
        sum += numx
        download_list.append(str(numx) + '次')
    row[6] = download_list
    row[5] = sum
    notice_dict = {'title': row[1], 'href': row[3], 'time': row[2], 'department': row[0], 'attachment': row[4],
                   'downloaded': row[6], 'downloaded_all': row[5]}
    with open('output.csv', 'a', newline='', encoding='utf-8') as csvfilee:
            # 定义字段名（字典的键）
        fieldnames = ['department', 'title', 'time', 'href', 'attachment', 'downloaded_all','downloaded']
        # 创建 DictWriter 对象
        writer = csv.DictWriter(csvfilee, fieldnames=fieldnames)
        # 如果文件为空，则写入表头
        if csvfilee.tell() == 0:
            writer.writeheader()
        # 将字典写入 CSV 文件
        writer.writerow(notice_dict)
        counter += 1
        progress_bar(counter, sum_all, desc="Checking and Downloading")
        print(f'\t有{num}个附件已经下载完成')


# 初始化爬虫
Crawler = Crawler()
# 获取目录页网址，存储于contents_pages
html = Crawler.craw_get('https://jwch.fzu.edu.cn/jxtz.htm')
page_num = int(analysis(html).xpath('/html/body/div[1]/div[2]/div[2]/div/div/div[3]/div[2]/div[1]/div/span[1]/span[9]/a/text()')[0])
contents_pages_urls = [f'https://jwch.fzu.edu.cn/jxtz/{i}.htm' for i in range(1,page_num)]
contents_pages_urls.append('https://jwch.fzu.edu.cn/jxtz.htm')
contents_pages = pool.map(Crawler.craw_get,contents_pages_urls)
# 0.解析出每页的通知元素
# 1.成字典，存储于notice_dict
# 2.字典内：/html/body/div[1]/div[2]/div[2]/div/div/div[3]/div[1]/ul/li[1]/text()
# ##构建analysis实例们
analysis_list=pool.map(analysis,contents_pages)
for analysise in tqdm(analysis_list, desc="Processing pages"):
    page_num = analysise.xpath(
        r'/html/body/div[1]/div[2]/div[2]/div/div/div[3]/div[2]/div[1]/div/span[1][@class="p_pages"]/span[@class="p_no_d"]/text()')[0]
    notice = analysise.xpath('/html/body/div[1]/div[2]/div[2]/div/div/div[3]/div[1]/ul/li')
    for i in notice:
        url = i.xpath('./a/@href')[0]
        url = url.strip("./")
        url = "https://jwch.fzu.edu.cn/"+url
        title = i.xpath('./a/text()')[0].strip()
        time = i.xpath('./span/text()')[0].strip()
        if time == '':
            time = i.xpath('./span[@class="doclist_time"]/font/text()')[0]
            time=time.strip()
        department = i.xpath(r'./text()')[1].strip()
        notice_dict = {'title': title, 'href': url, 'time': time, 'department': department,'attachment':None,'downloaded':None,'downloaded_all':None}
        # 以追加模式打开 CSV 文件
        with open('notices.csv', 'a', newline='', encoding='utf-8') as csvfile:
            # 定义字段名（字典的键）
            fieldnames = ['department', 'title', 'time', 'href', 'attachment', 'downloaded_all','downloaded']
            # 创建 DictWriter 对象
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            # 如果文件为空，则写入表头
            if csvfile.tell() == 0:
                writer.writeheader()
            # 将字典写入 CSV 文件
            writer.writerow(notice_dict)
        counter += 1

sum_all = counter
counter=0
#读出CSV文件,打开链接,检查是否有附件,若有则下载到附件文件夹中,并在csv里记录下载次数
if not os.path.exists('attachments'):
    os.mkdir('attachments')
with open('notices.csv', 'r', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    data = list(reader)
    chuli:list = data[1:]
    pool2.map(check_download, chuli)

time2 = timex.time()
print('总共耗时：' + str(time2 - time1) + 's')







