from selenium import webdriver as wd
import re
import os
import time
from hanspell import spell_checker
from collections import defaultdict
import numpy as np
import pandas as pd
import torch.nn as nn
import torch
from torch import optim
import matplotlib.pyplot as plt
from tqdm import tqdm, trange
import csv


# driver = wd.Chrome(executable_path='./chromedriver')

def hasxpath(xpath):
    try:
        driver.find_element_by_xpath(xpath)
        return True
    except:
        return False

def read_review(url, dataset_path):     # 사이트에서 리뷰 크롤링

    driver.get(url)

    for n in range(1, 20):
        time.sleep(2)

        page_bar = driver.find_elements_by_class_name('num')

        # 맛집 검색 결과 전체 목록을 class 명으로 찾아서 불러오기
        upper_class = driver.find_element_by_class_name('list_place_col1')

        # 클래스 명으로 불러온 목록에서 tag가 li인 데이터만 불러오기, 가게에 대한 개별 데이터가 들어있음
        upper_tag = upper_class.find_elements_by_tag_name('li')
        store_ids = []
        for item in upper_tag: # tag가 li인 데이터 중 id에 해당하는 데이터를 리스트에 저장
            store_ids.append(item.get_attribute('id'))

        df = open(dataset_path, 'a', encoding='utf-8')

        for store_id in store_ids:
            url = '//*[@id="'+store_id+'"]/div/div/div[1]/span/a'
            driver.find_element_by_xpath(url).click()
            # 가게 페이지에 들어가도 드라이버는 검색 페이지를 가리키고 있어서 활성창을 변경해줘야 함
            driver.switch_to.window(driver.window_handles[-1])
            driver.find_element_by_xpath('//*[@id="tab03"]').click() # 영수증 리뷰 탭 열기

            if hasxpath('//*[@id="panel03"]/div/div[2]/span'):  # 영수증 리뷰가 2페이지 이상 존재할 경우에만 리뷰를 읽음
                review_pages = driver.find_element_by_xpath('//*[@id="panel03"]/div/div[2]/span').text
                for page in range(int(review_pages)):
                    if page == 10:
                        break
                    scores = driver.find_elements_by_class_name('score')    # 별점은 scores에 저장
                    review_txts = driver.find_elements_by_class_name('review_txt')  # 리뷰글을 review_txts 저장

                    for score, review_txt in zip(scores, review_txts):
                        df.write(score.text+'\t'+review_txt.text+'\n')
                    driver.find_element_by_xpath('//*[@id="panel03"]/div/div[2]/a[2]').click()
                    time.sleep(2)
            driver.close() # 현재 탭 닫기
            driver.switch_to.window(driver.window_handles[0]) # 검색 페이지로 돌아가기

        try:
            if n % 5 != 0: # 5의 배수가 아닐 경우에는 숫자로 페이지 넘기기
                page_bar[n % 5].click()
                print(n)
            else:
                # 5의 배수인 경우 화살표 누르기
                driver.find_element_by_css_selector('#container > div.placemap_area > div.list_wrapper > div > div.list_area > div > div.pagination_inner > a.btn_direction.btn_next').click()

        except: # 다음 페이지 엾을 경우
            break

def correct_spacing(datasest_path, cor_dataset_path):   # 맞춤법 검사 후 txt 파일로 저장하는 메소드

    dataset_f = open(datasest_path, 'r', encoding='utf-8')
    cor_data_f = open(cor_dataset_path, 'w', encoding='utf-8')
    for line in dataset_f.readlines():
        line = line.strip('\n')
        line = re.sub('[#$%&,*+]', '', line)    # 리뷰에 포함된 특수기호를 제거해 예약어로 인한 xml parser 에러 해결
        score, text = line.split('\t')
        score = round(float(score))
        text = ' '.join(re.findall('[가-힣]+', text)) # 자음, 모음으로만 이루어진 글은 제외한다
        if len(text) > 1:   # 리뷰가 한 글자 이하인 글은 제외한다
            check_result = spell_checker.check(text)
            cor_text = check_result.checked    # 맞춤법 체크
            cor_data_f.write(str(score)+'\t'+cor_text+'\n')
    dataset_f.close()
    cor_data_f.close()

def change_tsv(txt_path):   # 별점, 리뷰가 작성된 txt 파일을 tsv 파일로 저장하는 메소드
    with open('dataset/all_dataset.tsv', 'wt', encoding='utf-8', newline="") as out_file:
        f = open(txt_path, encoding='utf-8')
        tsv_writer = csv.writer(out_file, delimiter='\t')
        tsv_writer.writerow(['score', 'text'])
        for line in f.readlines():
            line = line.strip('\n')
            score, text = line.split('\t')
            tsv_writer.writerow([score, text])

def make_vocab(vocab_path, train=None):
    vocab = {}
    if os.path.isfile(vocab_path):
        file = open(vocab_path, 'r', encoding='utf-8')
        for line in file.readlines():
            line = line.rstrip()
            key, value = line.split('\t')
            vocab[key] = value
        file.close()
    else:
        count_dict = defaultdict(int)
        for index, data in tqdm(train.iterrows(), desc='make vocab', total=len(train)):
          sentence = data['text']
          tokens = sentence.split(' ')
          for token in tokens:
            count_dict[token] += 1

        file = open(vocab_path, 'w', encoding='utf-8')
        file.write('[UNK]\t0\n[PAD]\t1\n')
        vocab = {'[UNK]' : 0, '[PAD]' : 1}
        for index, (token, count) in enumerate(sorted(count_dict.items(), reverse=True,key=lambda item: item[1])):
            vocab[token] = index + 2
            file.write(token + '\t' + str(index + 2) + '\n')
        file.close()

    return vocab

class RNN(nn.Module):
    def __init__(self, input_size, embed_size, hidden_size, output_size, num_layers=1, bidirec=True):
        super(RNN, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers
        if bidirec:
            self.num_directions = 2
        else:
            self.num_directions = 1

        self.embed = nn.Embedding(input_size, embed_size)
        self.lstm = nn.LSTM(embed_size, hidden_size, num_layers, batch_first=True, bidirectional=bidirec)
        self.linear = nn.Linear(hidden_size * self.num_directions, output_size)

    def init_hidden(self, batch_size):
        # (num_layers * num_directions, batch_size, hidden_size)
        hidden = torch.zeros(self.num_layers * self.num_directions, batch_size, self.hidden_size)
        cell = torch.zeros(self.num_layers * self.num_directions, batch_size, self.hidden_size)
        return hidden, cell

    def forward(self, inputs):
        """
        inputs : B,T
        """
        embed = self.embed(inputs)  # word vector indexing
        hidden, cell = self.init_hidden(inputs.size(0))  # initial hidden,cell

        output, (hidden, cell) = self.lstm(embed, (hidden, cell))

        # Many-to-Many
        # output = self.linear(output) # B,T,H -> B,T,V

        # Many-to-One
        hidden = hidden[-self.num_directions:]  # (num_directions,B,H)
        hidden = torch.cat([h for h in hidden], 1)
        output = self.linear(hidden)  # last hidden

        return output

def read_data(train, vocab, max_len):   # 문자를 vocab에 저장된 숫자로 변환하는 메소드
    x_train = np.ones(shape=(len(train), max_len))
    for i, data in tqdm(enumerate(train['text']), desc='make x_train data', total=len(train)):
      tokens = data.split(' ')    # 공백을 기준으로 토큰을 자른다
      for j, token in enumerate(tokens):
        if j == max_len:
          break
        # if token not in vocab.keys():   # test 데이터에는 unknown 토큰이 존재
        #   x_train[i][j] = 0
        else :
          x_train[i][j] = vocab[token]

    y_train = train['score'].to_numpy()

    return x_train, y_train

def get_acc(pred, answer):
    correct = 0
    for p, a in zip(pred, answer):
        pv, pi = p.max(0)
        if pi == a:
            correct += 1
    return correct / len(pred)

def train(x, y, max_len, embed_size, hidden_size, output_size, batch_size, epochs, lr, model = None):
    x = torch.from_numpy(x).long()
    y = torch.from_numpy(y).long()
    if model is None:
        model = RNN(max_len, embed_size, hidden_size, output_size)
    model.train()
    loss_function = nn.CrossEntropyLoss()
    # loss_function = nn.MSELoss(reduction="mean")
    optimizer = optim.Adam(model.parameters(), lr=lr)
    data_loader = torch.utils.data.DataLoader(list(zip(x, y)), batch_size, shuffle=True)
    loss_total = []
    acc_total = []
    for epoch in trange(epochs):
        epoch_loss = 0
        epoch_acc = 0
        for batch_data in data_loader:
            x_batch, y_batch = batch_data
            pred = model(x_batch)

            loss = loss_function(pred, y_batch)
            optimizer.zero_grad()
            loss.backward()

            optimizer.step()

            epoch_loss += loss.item()
            epoch_acc += get_acc(pred, y_batch)
        epoch_loss /= len(data_loader)
        epoch_acc /= len(data_loader)
        loss_total.append(epoch_loss)
        acc_total.append(epoch_acc)
        print("\nEpoch [%d] Loss: %.3f\tAcc:%.3f"%(epoch+1, epoch_loss, epoch_acc))

    torch.save(model, 'model.out')

    return model, loss_total, acc_total

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

def draw_graph(data):
    plt.plot(data)
    plt.show()

def save_submission(pred):
    data = {
        "score" : pred
        }
    df = pd.DataFrame(data)
    df.to_csv('my_submission.csv', mode='w', index=False)

# if __name__ == '__main__':
#     gangnam_url = 'https://store.naver.com/restaurants/list?entry=pll&filterId=r09680&menu=3&query=%EA%B0%95%EB%82%A8%20%EB%A7%9B%EC%A7%91&sessionid=Blk7wlLaBsfwbYVRnNSEZA%3D%3D'
#     daejeon_url = 'https://store.naver.com/restaurants/list?entry=pll&filterId=r07&query=%EB%8C%80%EC%A0%84%20%EB%A7%9B%EC%A7%91&sessionid=4D695daw6rQJ75X8X%2Fquzg%3D%3D'
#     gumi_url = 'https://store.naver.com/restaurants/list?entry=pll&filterId=r04190&query=%EA%B5%AC%EB%AF%B8%20%EB%A7%9B%EC%A7%91&sessionid=RS7yQshQBb13KWdVZWq9FA%3D%3D'
#     gyeongju_url = 'https://store.naver.com/restaurants/list?entry=pll&filterId=r04130&query=%EA%B2%BD%EC%A3%BC%20%EB%A7%9B%EC%A7%91&sessionid=P9tedTr7MFK3abFskF6Tvw%3D%3D'
#
#     # read_review(gangnam_url, './dataset_gangnam.txt')
#     # read_review(daejeon_url, './dataset_daejeon.txt')
#     # read_review(gumi_url, './dataset_gumi.txt')
#     # read_review(gyeongju_url, './dataset_gyeongju.txt')
#
#     # correct_spacing('./dataset_daejeon.txt', './cor_dataset_deajeon.txt')
#     # correct_spacing('./dataset_gangnam.txt', './cor_dataset_gangnam.txt')
#     # correct_spacing('./dataset_gyeongju.txt', './cor_dataset_gumi.txt')
#     # correct_spacing('./gyeongju_dataset.txt', './cor_dataset_gyeongju.txt')
#
#     # change_tsv('all_dataset.txt')
#
#     train_path = 'all_dataset.tsv'
#     vocab_path = 'vocab.txt'
#     train_data = pd.read_csv(train_path, encoding='utf-8', sep='\t')
#     vocab = make_vocab(vocab_path, train_data)
#
#     max_len = 50
#     input_size = len(vocab)
#     embed_size = 50
#     hidden_size = 120
#     output_size = 6
#     batch_size = 1024
#     epochs = 20
#     lr = 0.001
#
#     model = torch.load('model.out')
#
#     x_train, y_train = read_data(train_data, vocab, max_len)
#
#     # model, loss_total, acc_total = train(x_train, y_train, input_size, embed_size, hidden_size, output_size, batch_size, epochs, lr, model)
#     # model, loss_total, acc_total = train(x_train, y_train, input_size, embed_size, hidden_size, output_size, batch_size,epochs, lr)
#     predict = test(model, x_train, batch_size)
#     save_submission(predict)

