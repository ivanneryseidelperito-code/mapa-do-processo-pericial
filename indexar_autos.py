#!/usr/bin/env python3
"""Indexa os autos (PDF unificado eproc/PJe) para preenchimento do Mapa do Processo.

Uso: python3 indexar_autos.py <autos.pdf> <pasta_saida>

Gera em <pasta_saida>:
  autos_paginado.txt  - texto integral, cada página precedida de
                        '=== PDF p.N | Ev. X | TAG p.k ===' (eproc) ou '=== PDF p.N | Num. ID ===' (PJe)
  eventos.json        - lista de eventos/documentos com data, descrição e páginas do PDF
  capa.json           - dados da capa do processo (quando houver)
  paginas_sem_texto.txt - páginas sem camada de texto (exigem leitura visual/OCR)
"""
import json, re, subprocess, sys, os

pdf, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
txt = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
pages = txt.split('\f')
if pages and not pages[-1].strip():
    pages = pages[:-1]

def norm(s):
    return re.sub(r'[ \t]+', ' ', s).strip()

RX_EPROC = re.compile(r'Evento (\d+), ([A-Z0-9_]+), P[áa]gina (\d+)')
RX_PJE = re.compile(r'Num\.\s*(\d+)\s*-\s*P[áa]g\.\s*(\d+)')
RX_SEP = re.compile(r'P[ÁA]GINA DE SEPARA[ÇC][ÃA]O')

eventos, atual, sem_texto, linhas = {}, None, [], []
sistema = 'desconhecido'
for n, p in enumerate(pages, 1):
    flat = ' '.join(p.split())
    corpo = RX_PJE.sub('', re.sub(r'Processo [\d\.\-]+/\w+, Evento \d+, [A-Z0-9_]+, P[áa]gina \d+', '', flat))
    if len(corpo.strip()) < 40:
        sem_texto.append(n)
    if RX_SEP.search(flat):
        sistema = 'eproc'
        ev = re.search(r'Evento (\d+)', flat)
        dt = re.search(r'Data:\s*(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2}))?', flat)
        desc = re.search(r'Evento:\s*(.*?)\s*Data:', flat)
        if ev:
            k = int(ev.group(1))
            d = (desc.group(1) if desc else '')
            d = re.sub(r'^JUNTADOA\s+', '', d)
            d = re.sub(r'\s*ID NO PJE \d+', '', d)
            d = re.sub(r'(\s+[A-Z]+\d+)+$', '', d)
            eventos.setdefault(k, {'evento': k, 'data': dt.group(1) if dt else '',
                                   'hora': (dt.group(2) or '') if dt else '',
                                   'descricao': d.strip(), 'pag_separacao': n, 'docs': []})
            atual = k
        linhas.append(f'=== PDF p.{n} | SEPARAÇÃO Ev. {ev.group(1) if ev else "?"} ===')
        linhas.append(p)
        continue
    m = RX_EPROC.search(flat)
    if m:
        sistema = 'eproc'
        k, tag, pg = int(m.group(1)), m.group(2), int(m.group(3))
        e = eventos.setdefault(k, {'evento': k, 'data': '', 'hora': '', 'descricao': '',
                                   'pag_separacao': None, 'docs': []})
        if not e['docs'] or e['docs'][-1]['tag'] != tag:
            e['docs'].append({'tag': tag, 'pdf_ini': n, 'pdf_fim': n})
        else:
            e['docs'][-1]['pdf_fim'] = n
        linhas.append(f'=== PDF p.{n} | Ev. {k} | {tag} p.{pg} ===')
    else:
        m2 = RX_PJE.search(flat)
        if m2:
            sistema = 'pje' if sistema == 'desconhecido' else sistema
            idd = m2.group(1)
            dt = re.search(r'Assinado eletronicamente por:\s*(.*?)\s*-\s*(\d{2}/\d{2}/\d{4})', flat)
            e = eventos.setdefault(idd, {'evento': idd, 'data': dt.group(2) if dt else '', 'hora': '',
                                         'descricao': '', 'assinante': dt.group(1) if dt else '',
                                         'pag_separacao': None, 'docs': [{'tag': 'Num.' + idd, 'pdf_ini': n, 'pdf_fim': n}]})
            e['docs'][-1]['pdf_fim'] = n
            linhas.append(f'=== PDF p.{n} | Num. {idd} pág. {m2.group(2)} ===')
        else:
            linhas.append(f'=== PDF p.{n} ===')
    linhas.append(p)

# primeira linha útil de cada documento (ajuda a identificar petições sem descrição)
for e in eventos.values():
    for d in e['docs']:
        corpo = pages[d['pdf_ini'] - 1]
        corpo = RX_EPROC.sub('', corpo)
        ls = [norm(l) for l in corpo.splitlines() if len(norm(l)) > 3]
        ls = [l for l in ls if not re.match(r'(PODER JUDICI|Justiça de Primeira|Comarca de|Avenida|Poder Judici|Tribunal de Justi)', l)]
        d['inicio'] = ' '.join(ls[:4])[:220]

# capa (eproc)
capa = {}
cap = ' '.join(' '.join(pages[:3]).split())
for chave, rx in [('numero', r'N[ºo] do processo\s*([\d\.\-]+)'),
                  ('classe', r'Classe da a[çc][ãa]o:\s*(.*?)\s*Compet'),
                  ('competencia', r'Compet[êe]ncia\s*(.*?)\s*Data de autua'),
                  ('autuacao', r'Data de autua[çc][ãa]o:\s*([\d/]+)'),
                  ('orgao_julgador', r'[ÓO]rg[ãa]o Julgador:\s*(.*?)\s*Juiz'),
                  ('juiz', r'Juiz\(a\):\s*(.*?)\s*Assuntos'),
                  ('valor_causa', r'Valor da Causa:\s*(R\$\s*[\d\.,]+)'),
                  ('justica_gratuita', r'Justi[çc]a Gratuita:\s*(\w+)'),
                  ('assuntos_bruto', r'Assuntos\s*(.*?)\s*Partes e Representantes'),
                  ('partes_bruto', r'Partes e Representantes\s*(.*?)\s*Informa[çc][õo]es Adicionais')]:
    m = re.search(rx, cap)
    if m:
        capa[chave] = m.group(1).strip()

# evento 1 (petição inicial) não tem página de separação no eproc: usa a data de autuação
m = re.search(r'Data de autua[çc][ãa]o:\s*([\d/]+)', ' '.join(' '.join(pages[:3]).split()))
for e in eventos.values():
    if e['evento'] == 1 and not e['data'] and m:
        e['data'] = m.group(1); e['descricao'] = e['descricao'] or 'PETIÇÃO INICIAL (data de autuação)'

lista = sorted(eventos.values(), key=lambda e: (isinstance(e['evento'], str), e['evento']))
open(os.path.join(out, 'autos_paginado.txt'), 'w').write('\n'.join(linhas))
json.dump(lista, open(os.path.join(out, 'eventos.json'), 'w'), ensure_ascii=False, indent=1)
json.dump(capa, open(os.path.join(out, 'capa.json'), 'w'), ensure_ascii=False, indent=1)
open(os.path.join(out, 'paginas_sem_texto.txt'), 'w').write(' '.join(map(str, sem_texto)))
print(f'sistema={sistema} paginas={len(pages)} eventos={len(lista)} sem_texto={len(sem_texto)}')
for e in lista:
    docs = ', '.join(f"{d['tag']}(p.{d['pdf_ini']}-{d['pdf_fim']})" for d in e['docs'])
    print(f"Ev.{e['evento']} | {e['data']} | {e['descricao'][:90]} | {docs}")
