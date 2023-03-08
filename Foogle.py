from pathlib import Path
import re
import math
import numpy as np
import cachetools.func



class Vector:
    def __init__(self,array):
        self.array=array
    def len(self):
        res=0
        for e in self.array:
            res+=e**2
        return res**0.5
    def __mul__(self, other):
        res=0
        for i in range(len(self.array)):
            res+=self.array[i]*other.array[i]
        return res
    def cos(self, other):
        try:
            return self*other/(self.len()*other.len())
        except:
            return 1.0

class FileManager:
    @cachetools.func.ttl_cache(maxsize=128, ttl=10 * 60)
    def __init__(self,path):
        self.codings=['ascii', 'utf_8', 'utf_16', 'cp1251', 'big5', 'big5hkscs', 'cp037', 'cp273', 'cp424', 'cp437', 'cp500', 'cp720',
                     'cp737', 'cp775', 'cp850', 'cp852', 'cp855', 'cp856', 'cp857', 'cp858', 'cp860', 'cp861',
                     'cp862', 'cp863', 'cp864', 'cp865', 'cp866', 'cp869', 'cp874', 'cp875', 'cp932', 'cp949',
                     'cp950', 'cp1006', 'cp1026', 'cp1125', 'cp1140', 'cp1250', 'cp1252', 'cp1253',
                     'cp1254', 'cp1255', 'cp1256', 'cp1257', 'cp1258', 'cp65001', 'euc_jp', 'euc_jis_2004',
                     'euc_jisx0213', 'euc_kr', 'gb2312', 'gbk', 'gb18030', 'hz', 'iso2022_jp', 'iso2022_jp_1',
                     'iso2022_jp_2', 'iso2022_jp_2004', 'iso2022_jp_3', 'iso2022_jp_ext', 'iso2022_kr', 'latin_1',
                     'iso8859_2', 'iso8859_3', 'iso8859_4', 'iso8859_5', 'iso8859_6', 'iso8859_7', 'iso8859_8',
                     'iso8859_9', 'iso8859_10', 'iso8859_11', 'iso8859_13', 'iso8859_14', 'iso8859_15', 'iso8859_16',
                     'johab', 'koi8_r', 'koi8_t', 'koi8_u', 'kz1048', 'mac_cyrillic', 'mac_greek', 'mac_iceland',
                     'mac_latin2', 'mac_roman', 'mac_turkish', 'ptcp154', 'shift_jis', 'shift_jis_2004',
                     'shift_jisx0213', 'utf_32', 'utf_32_be', 'utf_32_le', 'utf_16_be', 'utf_16_le',
                     'utf_7',  'utf_8_sig']
        self.files=[]
        self.path=path
        self.get_files(self.path)
        self.invertedIndex=None
        self.tf = {}
        self.len_files={}
        self.df={}
        self.N=len(self.files)
        self.make_reverse_index()

    def get_files(self,path):
        files=[]
        try:
            files = list(path.iterdir())
        except:
            exit()
        for file in files:
            f = Path(str(path), file)
            if f.is_dir():
                self.get_files(f)
            else:
                if f.suffix==".txt":
                    self.files.append(str(f))

    def split_files_into_words(self):
        file_to_words = {}
        pattern = re.compile('[\W_]+')
        for file in self.files:
            read=False
            for coding in self.codings:
                try:
                    with open(file, 'r',encoding=coding) as f:

                        file_to_words[file] = pattern.sub(' ', f.read().lower())
                        re.sub(r'[\W_]+', '', file_to_words[file])
                        file_to_words[file] = file_to_words[file].split()
                        self.len_files[file]=len(file_to_words[file])
                    read=True
                    break
                except:
                    pass
            if not read:
                print(f"Фаил {file} невозможно прочитать ни одной из известных программе кодировок")
                print("Он не будет учитываться при поиске")
        return file_to_words

    def index_one_file(self,words):
        fileIndex = {}
        for index, word in enumerate(words):
            if word in fileIndex.keys():
                fileIndex[word].append(index)
            else:
                fileIndex[word] = [index]
        return fileIndex

    def make_indices(self,fails_to_words):
        total = {}
        for filename in fails_to_words.keys():
            total[filename] = self.index_one_file(fails_to_words[filename])
        return total

    def reverse_Index(self,direct_index):
        total_index = {}
        for filename in direct_index.keys():
            self.tf[filename] = {}
            for word in direct_index[filename].keys():
                self.tf[filename][word] = len(direct_index[filename][word])/self.len_files[filename]
                if word not in self.df.keys():
                    self.df[word]=1
                else:
                    self.df[word]+=1
                if word in total_index.keys():
                    if filename in total_index[word].keys():
                        total_index[word][filename].extend(direct_index[filename][word][:])
                    else:
                        total_index[word][filename] = direct_index[filename][word]
                else:
                    total_index[word] = {filename: direct_index[filename][word]}
        return total_index

    def make_reverse_index(self):
        self.invertedIndex=self.reverse_Index(self.make_indices(self.split_files_into_words()))

    def phrase_query(self, string):
        pattern = re.compile('[\W_]+')
        string = pattern.sub(' ', string)
        listOfLists, result = [], []
        for word in string.split():
            listOfLists.append(self.one_word_query(word))
        setted = set(listOfLists[0]).intersection(*listOfLists)
        for filename in setted:
            temp = []
            for word in string.split():
                temp.append(self.invertedIndex[word][filename][:])
            for i in range(len(temp)):
                for ind in range(len(temp[i])):
                    temp[i][ind] -= i
            if set(temp[0]).intersection(*temp):
                result.append(filename)
        if len(result)==0:
            print( "Не нашлось результатов")
            return
        if len(result)==1:
            print( result[0])
            return
        res=self.rankResults(result, string.split())
        for r in res:
            print(r)

    def one_word_query(self, word):
        pattern = re.compile('[\W_]+')
        word = pattern.sub(' ', word)
        if word in self.invertedIndex.keys():
            return [filename for filename in self.invertedIndex[word].keys()]
        else:
            return []
    def rankResults(self,result,string):
        words=list(set(string))
        count_word_in_string={}
        answer=[]
        for word in string:
            if word not in count_word_in_string.keys():
                count_word_in_string[word]=1
            else:
                count_word_in_string[word] += 1
        request_vector = [0] * len(words)
        for i in range(len(words)):
            tf=count_word_in_string[words[i]]/len(string)
            df=self.N / self.df[words[i]]
            idf=math.log10(df)
            request_vector[i]=tf*idf
        r_vector=Vector(request_vector)
        for file in result:
            vector=[0]*len(words)
            for i in range(len(words)):
                idf = math.log10(self.N / self.df[words[i]])
                vector[i] = self.tf[file][words[i]] * idf
            f_vector=Vector(vector)
            deviation=r_vector.cos(f_vector)
            answer.append((file,deviation))
        answer.sort(key=lambda x:-x[1])
        return [ans[0] for ans in answer]


def main():
    dir=Path(input())
    phrase = input()
    if not dir.is_dir():
        exit()
    fileManager=FileManager(dir)
    fileManager.phrase_query(phrase.lower())


if __name__ == '__main__':
    main()