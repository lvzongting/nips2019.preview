#!/usr/bin/env python
#-*- coding: utf-8 -*-

import pandas as pd
import arxiv
import re
import os
from pathlib import Path
from time import sleep

get_word         = lambda s:" ".join((re.findall(r'\w+', s)))
get_lower_word   = lambda s:" ".join((re.findall(r'\w+', s))).lower()
get_letter       = lambda s: "".join((re.findall(r'\w+', s)))
get_lower_letter = lambda s: "".join((re.findall(r'\w+', s))).lower()

####Query arxiv####
print('-----------------------------')
print('Start arxiv querying...')

if os.path.isfile('paper_query_arxiv.pkl'):

    print('Found! Cache file for querying...')
    df_paper = pd.read_pickle('paper_query_arxiv.pkl')
    print('Load file!')
    print('If you want to start a new querying, please remove/rename file: paper_query_arxiv.pkl')

else:

    df_paper = pd.read_csv("paper.list",names=['paper_name'],sep='=')
    
    for idx,name in enumerate(df_paper['paper_name']):
        search_name = get_word(name)
        print(idx,"\npaper_name:\n",name)
        print("search_name:\n",search_name)
        paper = arxiv.query(query="ti:"+search_name,max_results=1)
        if len(paper) < 1:
            print("paper not found!")
            continue
        paper = paper[0]
        #df_paper['arxiv'][idx]=paper
        df_arxiv = pd.DataFrame([paper])
        df_arxiv.index = [idx]
        try:
            df_paper = df_paper.combine_first(df_arxiv)
        except:
            #col_paper_set = set(df_paper.columns)
            #col_arxiv_set = set(df_arxiv.columns)
            #unique_paper_set = set(df_paper.columns) - set(df_arxiv.columns)
            unique_arxiv_set = set(df_arxiv.columns) - set(df_paper.columns)
            df_paper = df_paper.join(df_arxiv[unique_arxiv_set]) 
        print("arxiv_title:\n",df_paper['title'][idx])
        print("----------------")
        #print(df_paper.iloc[idx])
        #input() 
        
    df_paper.to_csv('paper_query_arxiv.csv')
    df_paper.to_pickle('paper_query_arxiv.pkl')
    #df_paper = pd.read_csv('paper_query_arxiv.csv')
    #df_paper = pd.read_pickle('paper_query_arxiv.pkl')


####Check Match####
print('-----------------------------')
print('Start paper title checking...')

from difflib import SequenceMatcher    #difflib is a built-in function
#difflib.SequenceMatcher(None, 'hello world', 'hello').ratio()
#import Levenshtein                    #Levenshtein is not built-in
#Levenshtein.ratio('hello world', 'hello')

#df_paper['name_title_match'] = 0 
df_paper['name_title_match'] = False
df_paper['name_title_match_ratio'] = 0

for idx in df_paper.index:

    if pd.isna(df_paper['title'][idx]):
        #df_paper.loc[idx,'name_title_match'] = -1
        df_paper.loc[idx,'name_title_match_ratio'] = -1
        continue

    name  = get_lower_word(df_paper['paper_name'][idx])
    title = get_lower_word(df_paper['title'     ][idx])
    ##version diff distance
    df_paper.loc[idx,'name_title_match_ratio'] = SequenceMatcher(None, name, title).ratio()
#   ##version boolean
#    if name == title:
#        df_paper.loc[idx,'name_title_match'] = 1
#    else:
#        df_paper.loc[idx,'name_title_match'] = 0

df_paper_sort = df_paper.sort_values(by='name_title_match_ratio',ascending=False) 
df_threshold  = df_paper_sort[(df_paper_sort['name_title_match_ratio']>0.86) & (df_paper_sort['name_title_match_ratio']<1) ][ ['paper_name','title','name_title_match_ratio','id'] ] 
print(df_threshold)
match_ratio_threshold = 0.92

##wait 10s for modify match_ratio_threshold##
print('match_ratio_threshold=', match_ratio_threshold,'(default)')
print('Waiting new match_ratio_threshold input in 10 seconds! (Hit Ctrl-C to start)')
try:
    for i in range(0,10):
        sleep(1)
        print('wait',10-i,'s',end='\r',flush=True)
except KeyboardInterrupt:
    temp = input('match_ratio_threshold=') 
    try:
        temp = float(temp) 
    except:
        temp = 0.0
    if (temp > 0.0) & (temp <1.0):
        match_ratio_threshold = temp
#######

print('set match_ratio_threshold=', match_ratio_threshold)

df_paper.loc[df_paper['name_title_match_ratio']>match_ratio_threshold ,'name_title_match'] = True
print("tabulate of name_title_match:")
print(df_paper['name_title_match'].value_counts()) 


####Download####
print('-----------------------------')
print('Start downloading...')

download_method = 'wget'
print('download_method: ',download_method)

if download_method == 'wget':
    #version wget
    
    df_paper[df_paper['name_title_match']]['pdf_url'].to_csv('pdf.list',index=None,header=None) 
    os.system('wget -c -U definitely-not-wget -P ../ -i pdf.list')

    ##rename 
    #for filename in Path('../').glob('*.pdf'):
    for filename in Path('../').glob('????.?????v?'):    #eg: 1908.11314v2
        query_id    = filename.name
        query_id    = 'http://arxiv.org/abs/'+query_id    
        arxiv_title = df_paper[df_paper['id']==query_id]['title'].to_list()
        if len(arxiv_title) == 0:
            continue
        arxiv_title = arxiv_title[0] 
        arxiv_title = get_word(arxiv_title)
        filename.rename(filename.with_name(arxiv_title+'.pdf'))

if download_method == 'arxiv':
    #version arxiv download
    get_arxiv_filename = lambda obj:get_word(obj['title'])
    df_match = df_paper[df_paper['name_title_match']]
    
    for idx in df_match.index:
    
        arxiv_paper = df_match.loc[idx].to_dict()
        
        print(idx,'downloading...')
        arxiv.download(arxiv_paper, slugify=get_arxiv_filename, dirpath = '../') 
        print(get_arxiv_filename(arxiv_paper))

