# -*- coding: utf-8 -*-
"""
Created on Tue Sep 26 12:04:38 2023

@author: newton
"""

import io
import requests
import re
import pandas as pd
from PyPDF2 import PdfReader
headers = {'User-Agent': 'Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'}

#%% Prova Objetiva
url = 'https://cdn.cebraspe.org.br/concursos/SERPRO_23/arquivos/ED_3_SERPRO_RES_FIN_OBJ_CONV_PRAT.PDF'
response = requests.get(url=url, headers=headers, timeout=120)
on_fly_mem_obj = io.BytesIO(response.content)
pdf_file = PdfReader(on_fly_mem_obj)

file_content = ''

for page_num in range(pdf_file.numPages):
    page = pdf_file.pages[page_num]
    page_content = page.extract_text().replace('\n', '')
    file_content = file_content + re.sub('^...', '', page_content)

file_content = re.sub('\.  2 DA PROVA DE CONHECIMENTOS.*', ' /', file_content)


#%% Manipula os candidatos

# pattern para identificar cada candidato
regex_candidato = re.compile(r'(\d{8})([^/]*)')
# pattern para recuperar o nome
regex_nome_candidato = re.compile('\n?,\n? \n?([^,]*)\n?,\n?')
# pattern para recuperar a nota final
regex_nota_candidato = re.compile(', {,5}(\d ?\d?) {,4}$')

lista_candidatos = []
candidatos = re.finditer(regex_candidato, file_content)
for candidato in candidatos:
    matricula = candidato.group(1)
    if (matricula == '10020676'):
        break
    nome = re.search(regex_nome_candidato, candidato.group(2)).group(1)
    nome = nome.replace('\n', '')
    nota = re.search(regex_nota_candidato, candidato.group(2)).group(1)
    nota = nota.replace(' ', '').replace('\n', '').replace('\t', '')
    lista_candidatos.append([candidato.group(1), nome, nota])

ranking = pd.DataFrame(lista_candidatos, columns=['matricula', 'nome', 'nota_obj'])
ranking['nota_obj'] = ranking['nota_obj'].astype(float)
ranking = ranking.drop_duplicates(subset=['matricula'])
rank_obj = ranking.sort_values(by=['nota_obj'], ascending=False)
rank_obj = rank_obj.reset_index(drop=True)

print(rank_obj)


#%% Prova de Conhecimentos Aplicados
url = 'https://cdn.cebraspe.org.br/concursos/SERPRO_23/arquivos/ED_5_SERPRO_RES_PROV_PROVA_PRATICA.PDF'
response = requests.get(url=url, headers=headers, timeout=120)
on_fly_mem_obj = io.BytesIO(response.content)
pdf_file = PdfReader(on_fly_mem_obj)

# pattern para identificar cada candidato
regex_candidato = re.compile(r'(\d{8})\n?,\n? \n?([^,]*)\n?,\n? \n?(\d{1,2}\.\d{2})')
lista_candidatos = []

for page_num in range(pdf_file.numPages):
    page = pdf_file.pages[page_num]
    candidatos = re.finditer(regex_candidato, page.extract_text())
    for candidato in candidatos:
        nome = candidato.group(2).replace('\n', '')
        lista_candidatos.append([candidato.group(1), candidato.group(3)])

ranking = pd.DataFrame(lista_candidatos, columns=['matricula', 'nota_apl'])
ranking['nota_apl'] = ranking['nota_apl'].astype(float)
ranking = ranking.drop_duplicates(subset=['matricula'])
rank_apl = ranking.sort_values(by=['nota_apl'], ascending=False)
rank_apl = rank_apl.reset_index(drop=True)

print(rank_apl)


#%% Realiza o Merge das duas provas pra gerar o ranking final

fn_rank = pd.merge(rank_obj, rank_apl, on='matricula', how='outer')
fn_rank['nota_apl'] = fn_rank['nota_apl'].fillna(0)
fn_rank['nota_final'] = fn_rank['nota_apl'] + fn_rank['nota_obj']
fn_rank = fn_rank.sort_values(by=['nota_final'], ascending=False)
fn_rank = fn_rank.reset_index(drop=True)
fn_rank.to_csv('resultado_prova_conhecimentos_aplicados.csv')
