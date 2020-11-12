import requests

from makeDataset import RNN     # 학습된 모델을 load 하기 위해 필요함
import sys
import os
import re
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtGui, QtWidgets
from selenium import webdriver as wd
import time
import numpy as np
from hanspell import spell_checker
from tqdm import tqdm, trange
import csv
import pandas as pd
import torch
import urllib.request
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from matplotlib import style, font_manager



# 옵션 추가 (브라우저 띄우지 않음)
options = wd.ChromeOptions()
options.add_argument('headless')
options.add_argument('disable-gpu')
driver = wd.Chrome(executable_path='./chromedriver', options=options)


# driver = wd.Chrome(executable_path='./chromedriver')

class PicButton(QAbstractButton):
    def __init__(self, pixmap, parent=None):
        super(PicButton, self).__init__(parent)
        self.pixmap = pixmap

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(event.rect(), self.pixmap)

    def sizeHint(self):
        return self.pixmap.size()

class MyApp(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Reviewstagram')
        #self.move(100, 100)
        #self.resize(500, 800)

        # 타이틀 바의 왼쪽에 아이콘 추가
        self.setWindowIcon(QIcon('./icon/로고.png'))
        #self.setGeometry(300, 300, 300, 200)

        # 배경 이미지 삽입
        palette = QPalette()
        pixmap = QPixmap('./icon/배경색.png')
        pixmap = pixmap.scaled(500, 800)
        palette.setBrush(QPalette.Background, QBrush(pixmap))
        self.setPalette(palette)
        self.resize(500, 800)
        self.center()
        #self.setFixedSize(500, 800)

        # 로고 이미지
        self.pixmap_logo = QPixmap('./icon/로고워터마크.png')
        self.pixmap_logo = self.pixmap_logo.scaled(280, 220)
        self.logo_img = QLabel()
        self.logo_img.setPixmap(self.pixmap_logo)
        self.logo_layout = QGridLayout()
        self.logo_layout.addWidget(QLabel("          "), 0, 0)
        self.logo_layout.addWidget(self.logo_img, 0, 1)
        self.logo_layout.addWidget(QLabel("          "), 0, 2)

        # 아이디 입력창
        self.id_layout = QGridLayout()
        # id_layout.setGeometry(QtCore.QRect(10,10,50,10))
        self.id_label = QLabel()
        self.id_pixmap = QPixmap('icon/id이미지.png')
        self.id_pixmap = self.id_pixmap.scaled(80, 70)
        self.id_label.setPixmap(self.id_pixmap)
        self.id_layout.addWidget(self.id_label, 0, 2)
        self.id_text = QLineEdit()
        self.id_text.setFont(QtGui.QFont("맑은 고딕", 13))
        self.id_layout.addWidget(self.id_text, 0, 3)

        # 비번 입력창
        self.id_layout.addWidget(QLabel("          "), 1, 1)
        self.pw_label = QLabel()
        self.pw_pixmap = QPixmap('icon/pw이미지.png')
        self.pw_pixmap = self.pw_pixmap.scaled(80, 70)
        self.pw_label.setPixmap(self.pw_pixmap)
        self.id_layout.addWidget(self.pw_label, 1, 2)
        self.pw_text = QLineEdit()
        self.pw_text.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pw_text.setFont(QtGui.QFont("맑은 고딕", 13))
        self.id_layout.addWidget(self.pw_text, 1, 3)
        self.id_layout.addWidget(QLabel("                     "), 1, 4)

        # 로그인 버튼
        self.login_layout = QGridLayout()
        self.login_pixmap = QPixmap('icon/login이미지.png')
        self.login_pixmap = self.login_pixmap.scaled(300, 80)
        self.login_btn = PicButton(QPixmap(self.login_pixmap), self)
        self.login_btn.clicked.connect(self.login_event)
        self.login_layout.addWidget(QLabel("                    "), 0, 0)
        self.login_layout.addWidget(self.login_btn, 0, 1)
        self.login_layout.addWidget(QLabel("                    "), 0, 2)

        # 메인 레이아웃 배치
        self.main_layout = QVBoxLayout()
        self.main_layout.addSpacing(220)
        self.main_layout.addLayout(self.logo_layout)
        self.main_layout.addLayout(self.id_layout)
        self.main_layout.addSpacing(20)
        self.main_layout.addLayout(self.login_layout)
        self.main_layout.addSpacing(80)
        self.setLayout(self.main_layout)

        self.show()

    def center(self):   # 창 위치를 중앙으로 이동
        frame_info = self.frameGeometry()
        #print(f'-> frame_info : {frame_info}')
        display_center = QDesktopWidget().availableGeometry().center()
        #print(f'-> display_center : {display_center}')
        frame_info.moveCenter(display_center)
        self.move(frame_info.topLeft())

    def login_event(self):
        username = self.id_text.text()
        userpw = self.pw_text.text()

        # 인스타그램 로그인 URL
        loginUrl = 'https://www.instagram.com/accounts/login/'

        driver.implicitly_wait(5)

        # 웹 사이트 접속
        driver.get(loginUrl)

        driver.find_element_by_name('username').send_keys(username)
        driver.find_element_by_name('password').send_keys(userpw)

        # driver.implicitly_wait(5)
        driver.find_element_by_xpath('//*[@id="loginForm"]/div/div[3]/button').submit()
        time.sleep(3)   # 로그인 완료될 때 까지 대기
        cur_url = driver.current_url
        # 유저 정보 입력했는데 여전히 로그인 페이지에 머물러 있으면 로그인 실패
        if cur_url == "https://www.instagram.com/accounts/login/":
            fail_message = QMessageBox.question(self, 'Login Fail', '아이디 또는 비밀번호가 틀렸습니다.\n 다시 입력해주세요', QMessageBox.Ok)
            # self.clearLayout(self.id_layout)
            # self.clearLayout(self.login_layout)
            # self.set_selectLayout()

        # 유저 정보 입력하고 다음 페이지로 넘어가면 로그인 성공
        else:
            self.clearLayout(self.id_layout)
            self.clearLayout(self.login_layout)
            self.set_selectLayout()


    # 메뉴 선택 레이어
    def set_selectLayout(self):
        # 평점검색 버튼 생성 및 이벤트 핸들러 연결
        self.score_pixmap = QPixmap('icon/평점검색.png')
        self.score_pixmap = self.score_pixmap.scaled(300, 80)
        self.score_btn = PicButton(QPixmap(self.score_pixmap), self)
        self.score_btn.clicked.connect(self.set_scoreLayout)
        self.id_layout.addWidget(QLabel("          "), 0, 0)
        self.id_layout.addWidget(self.score_btn,0,1)
        self.id_layout.addWidget(QLabel("          "), 0, 2)

        # 맛집순위 버튼 생성 및 이벤트 핸들러 연결
        self.ranking_pixmap = QPixmap('icon/순위버튼.png')
        self.ranking_pixmap = self.ranking_pixmap.scaled(300, 80)
        self.ranking_btn = PicButton(QPixmap(self.ranking_pixmap), self)
        self.ranking_btn.clicked.connect(self.set_rankingLayout)
        self.id_layout.addWidget(QLabel("          "), 1, 0)
        self.id_layout.addWidget(self.ranking_btn, 1, 1)
        self.id_layout.addWidget(QLabel("          "), 1, 2)

    def set_scoreLayout(self):
        self.scoreTab = UIscoreTab(self)
        self.scoreTab.show()

    def set_rankingLayout(self):
        self.rankingTab = UIrankingTab(self)
        self.rankingTab.show()

    def clearLayout(self, layout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)

class UIrankingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__()

        self.resize(560, 800)
        self.setFixedWidth(560)
        self.setWindowTitle('Reviewstagram_맛집순위')

        self.numimageList = ['icon/rank1.PNG', 'icon/rank2.PNG', 'icon/rank3.PNG', 'icon/rank4.PNG']

        # 배경색 지정
        palette = QPalette()
        palette.setBrush(QPalette.Background, QColor(255, 255, 255, 255))
        self.setPalette(palette)

        # 맛집순위 타이틀 이미지 삽입
        self.top_title_pixmap = QPixmap('icon/맛집순위.png')
        self.top_title_pixmap = self.top_title_pixmap.scaled(500, 80)
        self.top_title_img = QLabel()
        self.top_title_img.setPixmap(self.top_title_pixmap)

        top_title_hbox = QHBoxLayout()
        top_title_hbox.addWidget(self.top_title_img)

        # 검색창 및 검색 버튼 삽입
        self.serchWindow = QLineEdit()
        self.serchWindow.setFont(QtGui.QFont("맑은 고딕", 13))
        self.serchBtn = QPushButton('검색')
        self.serchBtn.clicked.connect(self.serchBtn_event)

        serch_hbox = QHBoxLayout()
        serch_hbox.addWidget(self.serchWindow)
        serch_hbox.addWidget(self.serchBtn)

        # rank1 영역
        rank1_hbox = QHBoxLayout()
        rank1_vbox = QVBoxLayout()

        self.rank1_num_label = QLabel()  # 숫자 1 이미지 삽입
        self.show_num_image(self.rank1_num_label, 0)
        rank1_hbox.addWidget(self.rank1_num_label)

        self.rank1_name = QLabel('loading...')  # 1위 식당 이름 영역
        self.rank1_name.setFont(QtGui.QFont("맑은 고딕", 20))
        rank1_vbox.addWidget(self.rank1_name)

        self.rank1_post_num = QLabel('loading...')  # 2위 게시글 수 영역
        self.rank1_post_num.setFont(QtGui.QFont("맑은 고딕", 15))
        rank1_vbox.addWidget(self.rank1_post_num)

        w = QWidget()  # vbox 레이아웃을 웨젯에 붙여서 hbox에 추가
        w.setLayout(rank1_vbox)
        rank1_hbox.addWidget(w)

        self.rank1_img_label = QLabel()
        self.show_image(self.rank1_img_label, './stores', 0)
        rank1_hbox.addWidget(self.rank1_img_label)

        # rank2 영역
        rank2_hbox = QHBoxLayout()
        rank2_vbox = QVBoxLayout()

        self.rank2_num_label = QLabel()  # 숫자 2 이미지 삽입
        self.show_num_image(self.rank2_num_label, 1)
        rank2_hbox.addWidget(self.rank2_num_label)

        self.rank2_name = QLabel('loading...')  # 2위 식당 이름 영역
        self.rank2_name.setFont(QtGui.QFont("맑은 고딕", 20))
        rank2_vbox.addWidget(self.rank2_name)

        self.rank2_post_num = QLabel('loading...')  # 2위 게시글 수 영역
        self.rank2_post_num.setFont(QtGui.QFont("맑은 고딕", 15))
        rank2_vbox.addWidget(self.rank2_post_num)

        w = QWidget()  # vbox 레이아웃을 웨젯에 붙여서 hbox에 추가
        w.setLayout(rank2_vbox)
        rank2_hbox.addWidget(w)

        self.rank2_img_label = QLabel()
        self.show_image(self.rank2_img_label, './stores', 0)
        rank2_hbox.addWidget(self.rank2_img_label)

        # rank3 영역
        rank3_hbox = QHBoxLayout()
        rank3_vbox = QVBoxLayout()

        self.rank3_num_label = QLabel()  # 숫자 3 이미지 삽입
        self.show_num_image(self.rank3_num_label, 2)
        rank3_hbox.addWidget(self.rank3_num_label)

        self.rank3_name = QLabel('loading...')  # 3위 식당 이름 영역
        self.rank3_name.setFont(QtGui.QFont("맑은 고딕", 20))
        rank3_vbox.addWidget(self.rank3_name)

        self.rank3_post_num = QLabel('loading...')  # 3위 게시글 수 영역
        self.rank3_post_num.setFont(QtGui.QFont("맑은 고딕", 15))
        rank3_vbox.addWidget(self.rank3_post_num)

        w = QWidget()  # vbox 레이아웃을 웨젯에 붙여서 hbox에 추가
        w.setLayout(rank3_vbox)
        rank3_hbox.addWidget(w)

        self.rank3_img_label = QLabel()
        self.show_image(self.rank3_img_label, './stores', 0)
        rank3_hbox.addWidget(self.rank3_img_label)

        # rank4 영역
        rank4_hbox = QHBoxLayout()
        rank4_vbox = QVBoxLayout()

        self.rank4_num_label = QLabel()  # 숫자 4 이미지 삽입
        self.show_num_image(self.rank4_num_label, 3)
        rank4_hbox.addWidget(self.rank4_num_label)

        self.rank4_name = QLabel('loading...')  # 4위 식당 이름 영역
        self.rank4_name.setFont(QtGui.QFont("맑은 고딕", 20))
        rank4_vbox.addWidget(self.rank4_name)

        self.rank4_post_num = QLabel('loading...')  # 4위 게시글 수 영역
        self.rank4_post_num.setFont(QtGui.QFont("맑은 고딕", 15))
        rank4_vbox.addWidget(self.rank4_post_num)

        w = QWidget()  # vbox 레이아웃을 웨젯에 붙여서 hbox에 추가
        w.setLayout(rank4_vbox)
        rank4_hbox.addWidget(w)

        self.rank4_img_label = QLabel()
        self.show_image(self.rank4_img_label, './stores', 0)
        rank4_hbox.addWidget(self.rank4_img_label)


        self.vbox = QVBoxLayout()
        self.vbox.addLayout(top_title_hbox)
        self.vbox.addLayout(serch_hbox)
        self.vbox.addStretch(1)
        self.vbox.addLayout(rank1_hbox)
        self.vbox.addLayout(rank2_hbox)
        self.vbox.addLayout(rank3_hbox)
        self.vbox.addLayout(rank4_hbox)
        self.vbox.addStretch(1)

        self.main_vbox = QVBoxLayout()
        self.qw = QWidget()
        self.qw.setLayout(self.vbox)
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.qw)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(800)
        self.main_vbox.addWidget(self.scroll)

        self.setLayout(self.main_vbox)

    def show_num_image(self, label, num):
        pixmap = QPixmap(self.numimageList[num])
        label.setPixmap(pixmap)
        label.setFixedSize(100, 140)
        label.setScaledContents(True)

    def show_image(self, label, file_path, num):
        pixmap = QPixmap(file_path+'/'+str(num)+'.jpg')
        label.setPixmap(pixmap)
        label.setFixedSize(140, 140)
        label.setScaledContents(True)

    # 검색 버튼 눌렀을 경우 이벤트 핸들러
    def serchBtn_event(self):
        place_name = self.serchWindow.text()    # place_name은 지역명

        if not os.path.exists('./stores/' + place_name):
            os.mkdir('./stores/' + place_name)

        if os.path.isfile('./stores/' + place_name + '/'+ '맛집리스트.txt') != True:
            f = open('./stores/' + place_name + '/' + '맛집리스트.txt', 'w')

            driver.execute_script('window.open("about:blank", "_blank");')  # 새 탭 생성
            driver.switch_to.window(driver.window_handles[-1])  # 새 탭으로 이동

            naverplace_url = 'https://map.naver.com/v5/search?c=14287043.2153244,4311325.4795115,14,0,0,0,dh'
            driver.get(naverplace_url)
            search_word = place_name+'맛집\n'
            # driver.find_element_by_xpath('//*[@id="container"]/div[1]/shrinkable-layout/search-layout/search-box/div/div[1]').click()   # 검색창 클릭
            # driver.find_element_by_xpath('//*[@id="container"]/div[1]/shrinkable-layout/search-layout/search-box/div/div[1]').send_keys(search_word)    # 검색어 입력
            driver.find_element_by_xpath('//*[@id="container"]/shrinkable-layout/div/app-base/search-input-box/div/div[1]/div').click()  # 검색창 클릭
            driver.find_element_by_xpath('//*[@id="container"]/shrinkable-layout/div/app-base/search-input-box/div/div[1]/div').send_keys(search_word)  # 검색어 입력
            driver.implicitly_wait(3)
            store_list=[]
            # 식당 이름을 store_list에 저장
            for k in range(3):
                list = driver.find_elements_by_class_name('link_search')
                for data in list:
                    name = data.find_element_by_class_name('search_title_text').text
                    if len(name) > 1:
                        store_list.append(name)
                        f.write(name+'\n')
                if k == 1:
                    driver.find_element_by_xpath('//*[@id="container"]/div[1]/shrinkable-layout/search-layout/search-list/search-list-contents/div/div[2]/a[2]').click()
                elif k == 2:
                    driver.find_element_by_xpath('//*[@id="container"]/div[1]/shrinkable-layout/search-layout/search-list/search-list-contents/div/div[2]/a[3]').click()
                time.sleep(2)
            f.close()
            driver.close()  # 현재 탭 닫기
            driver.switch_to.window(driver.window_handles[0])  # 인스타 페이지로 돌아가기
        else:
            f = open('./stores/' + place_name + '/' + '맛집리스트.txt', 'r')
            store_list = []
            for line in f.readlines():
                line = line.strip('\n')
                store_list.append(line)
            f.close()

        store_list = repetition_del(store_list)
        store_list = spacing_del(store_list)

        if os.path.isfile('./stores/' + place_name + '/'+ '결과.txt') != True:
            rf = open('./stores/' + place_name + '/'+ '결과.txt', 'w')
            post_nums = []
            for index, store_name in enumerate(store_list):
                tagUrl = 'https://www.instagram.com/explore/tags/' + store_name + '/'
                driver.get(tagUrl)  # 해시태그 검색 url 접속
                xpath = '//*[@id="react-root"]/section/main/header/div[2]/div/div[2]/span/span'
                if hasxpath(xpath):
                    post_num = driver.find_element_by_xpath('//*[@id="react-root"]/section/main/header/div[2]/div/div[2]/span/span').text   # 게시글 수 읽어오기
                    post_nums.append(post_num)
                    img_elem = driver.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div[1]/div/div/div[1]/div[1]/a/div/div[1]/img')
                    img_src = img_elem.get_attribute('src')
                    img_file_path = './stores/' + place_name + '/' + str(index) + '.jpg'
                    urllib.request.urlretrieve(img_src, img_file_path)
                else:
                    post_nums.append('0')
            post_nums = str_to_int(post_nums)
            a = np.array(post_nums)
            s = a.argsort()
            s = s[::-1]
            s = s[:4]
            for n in post_nums:
                rf.write(str(n)+' ')
            rf.write('\n')
            for s_index in s:
                rf.write(str(s_index)+' ')
            rf.close()
        else:
            rf = open('./stores/' + place_name + '/' + '결과.txt', 'r')
            first_line = rf.readline()
            post_nums = first_line.split(' ')
            post_nums = str_to_int(post_nums)
            second_line = rf.readline()
            s = second_line.split(' ')
            s = str_to_int(s)
            rf.close()

        for i in range(4):
            index = s[i]
            if i == 0:
                self.rank1_name.setText(store_list[index])
                self.rank1_post_num.setText('총 게시글 수 '+str(post_nums[index])+'개')
                self.show_image(self.rank1_img_label, './stores/'+place_name, index)
            elif i == 1:
                self.rank2_name.setText(store_list[index])
                self.rank2_post_num.setText('총 게시글 수 '+str(post_nums[index])+'개')
                self.show_image(self.rank2_img_label, './stores/'+place_name, index)
            elif i == 2:
                self.rank3_name.setText(store_list[index])
                self.rank3_post_num.setText('총 게시글 수 ' + str(post_nums[index]) + '개')
                self.show_image(self.rank3_img_label, './stores/' + place_name, index)
            else:
                self.rank4_name.setText(store_list[index])
                self.rank4_post_num.setText('총 게시글 수 ' + str(post_nums[index]) + '개')
                self.show_image(self.rank4_img_label, './stores/' + place_name, index)



def repetition_del(list):
    new_list = []
    for v in list:
        if v not in new_list:
            new_list.append(v)
    return new_list

def spacing_del(list):
    new_list=[]
    for v in list:  # 식당 이름에 띄어쓰기가 있을 경우 제거(ex. BBQ 상모점)
        vs = v.split(' ')
        vs = vs[0]
        new_list.append(vs)
    return new_list

def str_to_int(list):
    new_list = []
    for v in list:
        if v != '\n' and v != "":
            v = v.strip('\n')
            v = v.replace(',', '')
            vi = int(v)
            new_list.append(vi)
    return new_list

class UIscoreTab(QWidget):

    def __init__(self, parent=None):
        #super(UIscoreTab, self).__init__(parent)
        super().__init__()
        self.resize(560,800)
        self.setFixedWidth(560)
        self.setWindowTitle('Reviewstagram_평점검색')

        self.heart_imageList = ['icon/하트0.png', 'icon/하트1.png', 'icon/하트2.png', 'icon/하트3.png', 'icon/하트4.png', 'icon/하트5.png']
        self.imageList = ['icon/이미지로딩.png']

        palette = QPalette()
        palette.setBrush(QPalette.Background, QColor(255,255,255,255))
        self.setPalette(palette)

        self.sBack_pixmap = QPixmap('icon/평점검색타이틀_합체버전.png')
        self.sBack_pixmap = self.sBack_pixmap.scaled(500, 80)
        self.sBack_img = QLabel()
        self.sBack_img.setPixmap(self.sBack_pixmap)

        title_hbox = QHBoxLayout()
        title_hbox.addWidget(self.sBack_img)

        self.serchWindow = QLineEdit()
        self.serchWindow.setFont(QtGui.QFont("맑은 고딕", 13))
        # self.serchWindow.setFixedWidth(80)
        self.serchBtn = QPushButton('검색')
        self.serchBtn.clicked.connect(self.serchBtn_event)


        serch_hbox = QHBoxLayout()
        # serch_hbox.addStretch(1)
        serch_hbox.addWidget(self.serchWindow)
        serch_hbox.addWidget(self.serchBtn)
        # serch_hbox.addStretch(1)

        self.heart_label = QLabel()
        self.show_heart(self.heart_label, 0)

        heart_hbox = QHBoxLayout()
        heart_hbox.addWidget(self.heart_label)

        # 총 게시글 수 타이틀 이미지 및  삽입
        self.post_num_title_pixmap = QPixmap('icon/게시글수.png')
        self.post_num_title_pixmap = self.post_num_title_pixmap.scaled(230, 60)
        self.post_num_title_img = QLabel()
        self.post_num_title_img.setPixmap(self.post_num_title_pixmap)
        self.post_num_label = QLabel('0')
        self.post_num_label.setFont(QtGui.QFont("맑은 고딕", 25))

        self.gae_pixmap = QPixmap('icon/개.png')
        self.gae_pixmap = self.gae_pixmap.scaled(80, 60)
        self.gae_img = QLabel()
        self.gae_img.setPixmap(self.gae_pixmap)

        post_num_hbox = QHBoxLayout()
        post_num_hbox.addWidget(self.post_num_title_img)
        post_num_hbox.addStretch(1)
        post_num_hbox.addWidget(self.post_num_label)
        post_num_hbox.addWidget(self.gae_img)

        self.img1_label = QLabel()
        self.show_image(self.img1_label, 0)
        self.img2_label = QLabel()
        self.show_image(self.img2_label, 0)
        self.img3_label = QLabel()
        self.show_image(self.img3_label, 0)

        photo_hbox = QHBoxLayout()
        photo_hbox.addWidget(self.img1_label)
        photo_hbox.addWidget(self.img2_label)
        photo_hbox.addWidget(self.img3_label)

        self.wc_label = QLabel()
        self.show_wc_or_plt(self.wc_label, 'wc로딩')
        wc_hbox = QHBoxLayout()
        wc_hbox.addWidget(self.wc_label)

        self.plt_label = QLabel()
        self.show_wc_or_plt(self.plt_label, 'plot로딩')
        plot_hbox = QHBoxLayout()
        plot_hbox.addWidget(self.plt_label)

        self.vbox = QVBoxLayout()
        self.vbox.addLayout(title_hbox)
        self.vbox.addLayout(serch_hbox)
        self.vbox.addLayout(heart_hbox)
        self.vbox.addLayout(post_num_hbox)
        self.vbox.addLayout(photo_hbox)
        self.vbox.addLayout(wc_hbox)
        self.vbox.addLayout(plot_hbox)

        self.main_vbox = QVBoxLayout()
        self.qw = QWidget()
        self.qw.setLayout(self.vbox)
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.qw)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(800)
        self.main_vbox.addWidget(self.scroll)

        self.setLayout(self.main_vbox)

    def show_heart(self, label, score):
        pixmap = QPixmap(self.heart_imageList[score])
        label.setPixmap(pixmap)
        label.setFixedSize(450, 70)
        label.setScaledContents(True)

    def show_image(self, label, num):
        pixmap = QPixmap(self.imageList[num])
        label.setPixmap(pixmap)
        label.setFixedSize(160, 160)
        label.setScaledContents(True)

    def show_wc_or_plt(self, label, hashTag):
        if label == self.wc_label:
            pixmap = QPixmap('./wordclouds/'+hashTag+'.png')
            label.setPixmap(pixmap)
            label.setFixedSize(480, 300)
            label.setScaledContents(True)

        elif label == self.plt_label:
            pixmap = QPixmap('./plots/' + hashTag + '.png')
            label.setPixmap(pixmap)
            label.setFixedSize(480, 350)
            label.setScaledContents(True)

    # 검색 버튼 눌렀을 경우 이벤트 핸들러
    def serchBtn_event(self):
        hashTag = self.serchWindow.text()
        self.show_heart(self.heart_label, 0)    # 새로 검색을 누르면 하트 초기화
        self.imageList = ['이미지로딩.png']      # 이미지 리스트 초기화
        if os.path.isfile('./contents/'+hashTag+'.tsv') != True:

            # 해시태그 URL
            tagUrl = 'https://www.instagram.com/explore/tags/' + hashTag + '/'

            driver.implicitly_wait(5)

            # 게시글 내용 저장
            cf = open('./contents/'+hashTag+'.txt', 'w', encoding='utf-8')
            df = open('./datetimes/'+hashTag+'.txt', 'w', encoding='utf-8')
            np = open('./postnums/'+hashTag+'.txt', 'w', encoding='utf-8')

            # 웹 사이트 접속
            driver.get(tagUrl)

            post_num = driver.find_element_by_xpath('//*[@id="react-root"]/section/main/header/div[2]/div/div[2]/span/span').text
            np.write(post_num)
            np.close()

            if not os.path.exists('./photos/' + hashTag):
                os.mkdir('./photos/'+hashTag)

            for j in range(1, 4):   # 이미지 3개 저장
                img_elem = driver.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div[1]/div/div/div[1]/div['+str(j)+']/a/div/div[1]/img')
                img_src = img_elem.get_attribute('src')
                img_file_path = './photos/'+hashTag +'/'+ hashTag + str(j) + '.jpg'
                urllib.request.urlretrieve(img_src, img_file_path)
                self.imageList.append(img_file_path)

            # 게시글 클릭
            driver.find_element_by_css_selector('div.v1Nh3.kIKUG._bz0w').click()

            for i in range(20):

                time.sleep(2)
                # 게시글에 텍스트가 있으면 읽어들임
                if hasxpath('/html/body/div[5]/div[2]/div/article/div[3]/div[1]/ul/div/li/div/div/div[2]/span'):
                    post = driver.find_element_by_xpath('/html/body/div[5]/div[2]/div/article/div[3]/div[1]/ul/div/li/div/div/div[2]/span').text
                    post = re.findall('[가-힣]+', post)  # 한국어로 된 게시글만 찾기
                    post = ' '.join(post)
                    check_result = spell_checker.check(post)
                    cor_post = check_result.checked  # 맞춤법 체크
                    if len(cor_post) > 1:
                        cf.write(cor_post + '\n')

                        # 포스팅 시간대 크롤링
                        datetime = driver.find_element_by_tag_name('time')
                        datetime = datetime.get_attribute('datetime')[11:13]
                        df.write(datetime + '\n')

                # 다음 게시글로 넘어가는 화살표 클릭
                driver.find_element_by_css_selector('a._65Bje.coreSpriteRightPaginationArrow').click()
            cf.close()
            df.close()
        else:
            post_num_path = './postnums/' + hashTag + '.txt'
            f = open(post_num_path, 'r', encoding='utf-8')
            post_num = f.readline()
            f.close()
            for p in range(1, 4):
                img_file_path = 'photos/' + hashTag + '/' + hashTag + str(p) + '.jpg'
                self.imageList.append(img_file_path)

        tsv_path = './contents/'+hashTag+'.tsv'
        txt_path = './contents/'+hashTag+'.txt'
        time_path = './datetimes/'+hashTag+'.txt'
        change_tsv(txt_path, hashTag, 'text')
        test_data = pd.read_csv(tsv_path, encoding='utf-8', sep='\t')
        vocab_path = 'dataset/vocab.txt'

        x_test = read_data(test_data, vocab_path, 50)
        predict = test(model, x_test, 1)
        avg_score = round(avg(predict))     # 평균 점수에서 소수점 버림
        self.show_heart(self.heart_label, avg_score)    # 평점에 따라 이미지 변경
        self.post_num_label.setText(str(post_num))  # 총 게시글 수를 gui 라벨에 나타내기
        self.show_image(self.img1_label, 1)
        self.show_image(self.img2_label, 2)
        self.show_image(self.img3_label, 3)
        make_wordcloud(txt_path, hashTag)
        self.show_wc_or_plt(self.wc_label, hashTag)
        make_timeplt(time_path, hashTag)
        self.show_wc_or_plt(self.plt_label, hashTag)
        self.show()


def make_wordcloud(txt_path, hashTag):
    f = open(txt_path, 'r', encoding='utf-8')
    wc = WordCloud(font_path='./font/BMJUA_ttf.ttf', background_color='white').generate(f.read())
    f.close()
    wc.to_file('./wordclouds/'+hashTag+'.png')

def make_timeplt(time_path, hasgTag):
    f = open(time_path, 'r', encoding='utf-8')
    arr = np.zeros(24)
    for line in f.readlines():
        line = line.strip('\n')
        arr[int(line)] += 1
    f.close()
    plt.style.use('ggplot')
    plt.plot(arr, color='mediumseagreen')
    fontprop = font_manager.FontProperties(fname='./font/나눔고딕.ttf', size=18)
    plt.title('시간대별 방문자 수', fontproperties=fontprop)
    plt.xticks(np.arange(0, 24, 1))
    plt.yticks(np.arange(0, np.max(arr)+2))
    plt.savefig('./plots/'+hasgTag+'.png', bbox_inches='tight')
    plt.cla()

def avg(list):
    return sum(list)/len(list)

def test(model, x, batch_size):
    model.eval()
    x = torch.from_numpy(x).long()
    data_loader = torch.utils.data.DataLoader(x, batch_size, shuffle=False)

    predict = []
    for batch_data in data_loader:
        pred = model(batch_data)
        for p in pred:
            pv, pi = p.max(0)
            predict.append(pi.item())

    return predict

def hasxpath(xpath):
    try:
        driver.find_element_by_xpath(xpath)
        return True
    except:
        return False

def read_data(test, vocab_path, max_len):   # 문자를 vocab에 저장된 숫자로 변환하는 메소드
    vocab = {}
    if os.path.isfile(vocab_path):
        file = open(vocab_path, 'r', encoding='utf-8')
        for line in file.readlines():
            line = line.rstrip()
            key, value = line.split('\t')
            vocab[key] = value
        file.close()

    x_test = np.ones(shape=(len(test), max_len))
    for i, data in tqdm(enumerate(test['text']), desc='make x_test data', total=len(test)):
      tokens = data.split(' ')    # 공백을 기준으로 토큰을 자른다
      for j, token in enumerate(tokens):
        if j == max_len:
          break
        if token not in vocab.keys():
          x_test[i][j] = 0
        else :
          x_test[i][j] = vocab[token]

    return x_test

def change_tsv(txt_path, file_name, row_name):   # 인스타그램 게시글 txt 파일을 tsv 파일로 저장하는 메소드
    with open('./contents/'+file_name+'.tsv', 'wt', encoding='utf-8', newline="") as out_file:
        f = open(txt_path, encoding='utf-8')
        tsv_writer = csv.writer(out_file, delimiter='\t')
        tsv_writer.writerow([row_name])
        for line in f.readlines():
            line = line.strip('\n')
            tsv_writer.writerow([line])
    out_file.close()
    f.close()

if __name__ == '__main__':
    model = torch.load('./model.out')
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())