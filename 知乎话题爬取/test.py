import csv
import os
import random
import re
import time
import json
from re import Match

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

# 初始化浏览器的选项设置
my_dir = os.path.expanduser("~")
profile_directory = r'--user-data-dir={}\AppData\Local\Google\Chrome Dev\User Data'.format(my_dir)
print(profile_directory)
opt = Options()
opt.binary_location = r'C:\Program Files (x86)\Google\Chrome Dev\Application\chrome.exe'
opt.add_experimental_option('useAutomationExtension', False)
opt.add_experimental_option('excludeSwitches', ['enable-automation'])
opt.add_argument(profile_directory)
opt.add_argument("--disable-blink-features=AutomationControlled")
ser = Service(
    executable_path=r"C:\Program Files (x86)\Google\Chrome Dev\Application\chromedriver-win32\chromedriver.exe")


# 一个鼠标随机小幅度移动的函数
def cheat_mouse():
    pass


# 一个滚轮随机小幅度移动的函数
def cheat_scroll():
    times = random.randint(1, 5)
    for i in range(times):
        y = random.randint(-50, 0)
        duration = random.randint(50, 250)
        action = ActionChains(chrome, duration=duration)
        try:
            action.scroll_by_amount(delta_x=0, delta_y=y).pause(0.2).perform()
        except:
            pass


# 一个优雅地滚动到底部的函数
def scroll_down():
    cheat_scroll()
    # js 往下滚动到底
    js = "window.scrollTo(0,document.body.scrollHeight)"
    chrome.execute_script(js)


# 用于滑动到底部，直到卡片数大于num(还不够健壮,如回答小于num，有待改进)
def enough_cards(card_list: WebElement, card_relative_xpath: str, num: int, sleep_time: float = 1) -> list[WebElement]:
    cards = card_list.find_elements(By.XPATH, card_relative_xpath)
    counter = 0

    # 滑动到底部，直到卡片数大于num(但是由于可能有长文本，所以多取5个)
    while len(cards) < num + 1:
        scroll_down()
        cards = card_list.find_elements(By.XPATH, card_relative_xpath)
        timer = len(cards)
        cheat_scroll()
        if timer == len(cards):
            time.sleep(sleep_time)
            counter += 1
        else:
            counter = 0
        if counter > 9:
            print('卡片数不变，可能是被折叠了，请检查')
            verify()
            counter = 0
        time.sleep(sleep_time)
    return cards[0:num]


# 获取问题
def get_questions(topic_url: str, num: int = 50):
    # 创建csv文件
    fieldnames = ['title', 'url']
    with open('./zhihu_questions.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        pass
    # 定位列表元素
    card_list = chrome.find_element(By.XPATH, '//*[@id="TopicMain"]//div[@role="list"]')
    # 定位每个是问答的卡片，问答卡片数要大于50
    while True:
        try:
            cards = enough_cards(card_list,
                                 './div[@class="List-item TopicFeedItem"]/div/div[@class="ContentItem AnswerItem"]',
                                 num, 0.5)
            break
        except:
            print('检测到验证,退回到话题页面')
            verify()
    # 问答卡片数大于50，开始爬取
    for card in cards:
        data = {}
        # 定位
        blank = card.find_element(By.CSS_SELECTOR, 'h2 > div > a')
        # 获取
        data['title'] = blank.text
        origin_url = blank.get_attribute('href')
        # 去除/answer/后的所有以及/answer/   https://www.zhihu.com/question/499639405/answer/2944357683
        url = re.search(r'(https://www.zhihu.com/question/\d+)', origin_url).group(1)
        data['url'] = url
        # 写入csv
        print(data)
        with open('./zhihu_questions.csv', 'a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerow(data)


# 通过链接获取问题详情
def get_rich_text() -> str:
    rich_text = ""
    # 判断是否有详情。没有则返回空（class = css-eew49z）
    try:
        chrome.find_element(By.XPATH, '//*[@id="root"]/div/main/div/div/div[1]/div[2]/div/div[1]/div[1]/div[6]/div')
    except:
        return rich_text
    # 找是否有展开按钮，有则点击
    try:
        expand = chrome.find_element(By.XPATH,
                                     '//*[@id="root"]/div/main/div/div/div[1]/div[2]/div/div[1]/div[1]/div['
                                     '6]/div/div/div/button')
        expand.click()
    except:
        pass
    # 获取问题富文本
    rich_text = chrome.find_element(By.XPATH,
                                    '//*[@id="root"]/div/main/div/div/div[1]/div[2]/div/div[1]/div[1]/div[6]/div').text
    return rich_text


# 通过问题链接获取所有回答
def get_anwsers(num: int) -> list[dict[str, str | Match[str] | None]] | bool:
    answer = []
    # 定位回答列表
    answers_list_main = chrome.find_element(By.XPATH, '//*[@id="QuestionAnswers-answers"]/div/div/div/div[2]/div')
    text = chrome.find_element(By.XPATH,
                               '/html/body/div[1]/div/main/div/div/div[3]/div[1]/div/div/div/div/div/div[1]/h4/span').text
    all_ans = text.split(' ')[0]
    all_ans = all_ans.replace(',', '')
    if int(all_ans) < num:
        print('回答数不足,自修改为全部回答')
        num = int(all_ans) - 1
    # 先向下滚动，直到有足够问题
    answers_list = enough_cards(answers_list_main, './div[@class="List-item"]', num, 0.5)
    # 获取回答
    for anwser in answers_list:
        anwser_dict = {}
        # 获取回答文本
        anwser_text = anwser.find_element(By.XPATH, './/div[@class="css-376mun"]')
        print(anwser_text.text)
        # # 获取回答赞同数
        # try:
        #     anwser_approve_element = anwser.find_element(By.XPATH, './div/div/div[2]/div[2]/div/span/button')
        #     print(anwser_approve_element.text)
        # except:
        #     print('error')
        # anwser_approve = anwser_approve_element.text
        # 获取回答时间
        anwser_time = anwser.find_element(By.XPATH, './/div[@class="ContentItem-time"]').text
        print(anwser_time)
        # 保存  2023-03-02 22:59
        anwser_dict['text'] = anwser_text.text
        # anwser_dict['approve'] = anwser_approve
        anwser_dict['time'] = re.search(r"[\d*?]-[\d*?]-[\d*?] [\d*?]:[\d*?]", anwser_time)
        answer.append(anwser_dict)
    return answer


# 手动验证
def verify():
    print('进行手动操作')
    while (True):
        x = input('请输入ok:')
        if x == 'ok':
            return


# 基于问题链接创建一个新的csv文件，包含所有问题的富文本以及回答
def create_res_csv(num: int = 20, topic_name: str = ''):
    fieldnames = ['title', 'url', 'QuestionRichText', 'Answers']
    f = open(f'./{topic_name}_res.csv', 'w', newline='', encoding='utf-8')
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    fd = open('./zhihu_questions.csv', 'r', encoding='utf-8')
    reader = csv.DictReader(fd)
    for row in reader:
        # 浏览器跳转到问题链接
        chrome.get(row['url'])
        # 什么？会有检测，引导跳转到验证页面，所以get到后先检查url是否正确
        # 如果不正确，等我人工输入验证码后再继续
        while (chrome.current_url != row['url']):
            print(chrome.current_url)
            print(row['url'])
            print('检测到验证，等待人工输入验证码')
            verify()
            chrome.get(row['url'])
        # 获取富文本
        while True:
            try:
                rich_text = get_rich_text()
                break
            except:
                print('请手动重新回到这个问题的回答界面')
                verify()
        row['QuestionRichText'] = rich_text
        # 获取回答
        while True:
            try:
                anwsers = get_anwsers(num)
                break
            except:
                print('请手动重新回到这个问题的回答界面')
                verify()
        row['Answers'] = json.dumps(anwsers, ensure_ascii=False)

        writer.writerow(row)
    f.close()
    fd.close()


# 主函数
def topic_q_and_a(topic_url, num_q: int = 50, num_a: int = 20):
    # 指纹伪装
    with open('./stealth.min.js') as f:
        chrome.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": f.read()
        })
    chrome.get(topic_url)
    # 获取话题名
    topic_name = chrome.find_element(By.CSS_SELECTOR, '#root > div > main > div > div.css-fvdsnr > div.Card > div > div > div.ContentItem.TopicMetaCard-item > div > div.ContentItem-head > h2 > span > div').text
    get_questions(topic_url, num_q)
    create_res_csv(num_a,topic_name)
    chrome.quit()


# 启动
if __name__ == '__main__':
    chrome = webdriver.Chrome(options=opt, service=ser)
    topic_q_and_a('https://www.zhihu.com/topic/19555513/hot', 50, 20)
