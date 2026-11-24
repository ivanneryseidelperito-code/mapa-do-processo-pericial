#!/usr/bin/env python3
"""Preenche o modelo 'Mapa do Processo' (Processos Cíveis) a partir de um JSON de dados.

Uso: python3 preencher_mapa.py <modelo_mapa.docx> <dados.json> <saida.docx>

O script valida os rótulos do modelo antes de escrever (aborta se o layout mudou),
preserva a formatação (Courier 9 pt) e os controles de conteúdo, marca as caixas
Instrução/Liquidação, troca os rótulos das partes, cria a linha "Quesitos Juízo",
preenche um advogado por parte e acrescenta linhas em Histórico/Outros peritos quando necessário.
"""
import copy, json, re, shutil, sys, tempfile, unicodedata, zipfile
from docx import Document
from docx.oxml.ns import qn

modelo, dados_path, saida = sys.argv[1], sys.argv[2], sys.argv[3]
D = json.load(open(dados_path, encoding='utf-8'))
doc = Document(modelo)
T = doc.tables
W14 = 'http://schemas.microsoft.com/office/word/2010/wordml'

def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z]', '', s)

def tcs(t, r):
    return t.rows[r]._tr.findall(qn('w:tc'))

def tc_text(tc):
    return ''.join(x.text or '' for x in tc.iter(qn('w:t')))

def check(ti, r, c, esperado):
    got = norm(tc_text(tcs(T[ti], r)[c]))
    if not got.startswith(norm(esperado)):
        sys.exit(f'ERRO: modelo diferente do esperado na tabela {ti}, linha {r}, célula {c}: '
                 f'esperado "{esperado}", encontrado "{tc_text(tcs(T[ti], r)[c])}"')

def set_tc(tc, valor, negrito=False):
    if valor is None:
        return
    valor = str(valor)
    ps = tc.findall(qn('w:p'))
    p = ps[0]
    for extra in ps[1:]:
        tc.remove(extra)
    for ch in list(p):
        if ch.tag != qn('w:pPr'):
            p.remove(ch)
    ppr = p.find(qn('w:pPr'))
    base = ppr.find(qn('w:rPr')) if ppr is not None else None
    rpr = copy.deepcopy(base) if base is not None else None
    if rpr is not None:
        rpr.tag = qn('w:rPr')
        for b in rpr.findall(qn('w:b')) + rpr.findall(qn('w:bCs')):
            rpr.remove(b)
        if negrito:
            rpr.insert(1, rpr.makeelement(qn('w:b'), {}))
        # padroniza o corpo em 9 pt (o modelo tem células com 7 pt residuais)
        for tag in ('w:sz', 'w:szCs'):
            el = rpr.find(qn(tag))
            if el is None:
                el = rpr.makeelement(qn(tag), {}); rpr.append(el)
            el.set(qn('w:val'), str(TAMANHO))
    for i, linha in enumerate(valor.split('\n')):
        r = p.makeelement(qn('w:r'), {})
        if rpr is not None:
            r.append(copy.deepcopy(rpr))
        if i:
            r.append(r.makeelement(qn('w:br'), {}))
        t = r.makeelement(qn('w:t'), {})
        t.text = linha
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        r.append(t)
        p.append(r)

def set_cell(ti, r, c, valor, rotulo=None, rot_c=None):
    if rotulo:
        check(ti, r, rot_c if rot_c is not None else c - 1, rotulo)
    set_tc(tcs(T[ti], r)[c], valor)

g = D.get
TAMANHO = int(D.get('tamanho_fonte_meio_pontos', 18))

# ---------- QUANTO AO PROCESSO ----------
for r, (rot, k) in enumerate([('Processo Principal', 'processo_principal'),
                              ('Processo Relacionado', 'processo_relacionado'),
                              ('Vara', 'vara'), ('Classe', 'classe'), ('Assuntos', 'assuntos')]):
    set_cell(0, r, 1, g(k), rot)
set_cell(0, 5, 1, g('autor'))
set_cell(0, 6, 1, g('reu'))
set_cell(0, 7, 1, g('valor_causa'), 'Valor da Causa')

# caixas de seleção (1ª = Instrução, 2ª = Liquidação)
boxes = [s for s in doc.element.body.iter(qn('w:sdt'))
         if s.find(qn('w:sdtPr')).find('{%s}checkbox' % W14) is not None]
fase = (g('fase') or '').lower()
for i, sdt in enumerate(boxes[:2]):
    marcar = (i == 0 and fase.startswith('instr')) or (i == 1 and fase.startswith('liquid'))
    sdt.find(qn('w:sdtPr')).find('{%s}checkbox' % W14).find('{%s}checked' % W14).set('{%s}val' % W14, '1' if marcar else '0')
    for t in sdt.iter(qn('w:t')):
        t.text = '☒' if marcar else '☐'

def merge_from(ti, r, c):
    """Une a célula c às seguintes da mesma linha (valores estreitos de Citação/Trânsito)."""
    cells = tcs(T[ti], r)
    if len(cells) <= c + 1:
        return
    span = 0
    for x in cells[c:]:
        pr = x.find(qn('w:tcPr'))
        gs = pr.find(qn('w:gridSpan')) if pr is not None else None
        span += int(gs.get(qn('w:val'))) if gs is not None else 1
    tcpr = cells[c].find(qn('w:tcPr'))
    gs = tcpr.find(qn('w:gridSpan'))
    if gs is None:
        gs = tcpr.makeelement(qn('w:gridSpan'), {}); tcpr.insert(1, gs)
    gs.set(qn('w:val'), str(span))
    for x in cells[c + 1:]:
        x.getparent().remove(x)

merge_from(2, 0, 3)
merge_from(2, 1, 3)

pares = [('Ajuizamento', 'ajuizamento', 'Citação', 'citacao'),
         ('AJG', 'ajg', 'Trânsito em julgado', 'transito_julgado'),
         ('Sentença', 'sentenca', 'Embargos', 'embargos_sentenca'),
         ('Acórdão', 'acordao', 'Embargos', 'embargos_acordao'),
         ('STJ', 'stj', 'Embargos', 'embargos_stj')]
for r, (r1, k1, r2, k2) in enumerate(pares):
    set_cell(2, r, 1, g(k1), r1)
    set_cell(2, r, 3, g(k2), r2)

# ---------- QUANTO À PERÍCIA ----------
set_cell(3, 0, 1, g('deferimento'), 'Deferimento')
set_cell(3, 0, 3, g('requisitante'), 'Requisitante')
set_cell(3, 1, 1, g('objeto'), 'Objeto')
set_cell(3, 2, 1, g('objetivo'), 'Objetivo')
for r, k in [(4, 'quesitos_autor'), (5, 'quesitos_reu')]:
    q = g(k) or {}
    set_cell(3, r, 2, q.get('qtde'), 'Qtde')
    set_cell(3, r, 4, q.get('fls'), 'Fls')
check(3, 7, 0, 'Ivan')
for c, v in zip((1, 2, 3), g('ivan') or []):
    set_tc(tcs(T[3], 7)[c], v)
set_cell(3, 8, 1, g('nomeacao'), 'Nomeação')
set_cell(3, 8, 3, g('aceite'), 'Aceite')
if len(tcs(T[3], 8)) > 5:
    set_cell(3, 8, 5, g('prazo'), 'Prazo')
elif g('prazo') is not None:  # modelo sem etiqueta "Prazo": usa a célula livre da linha
    set_tc(tcs(T[3], 8)[4], ('Prazo: ' + g('prazo')) if g('prazo') else 'Prazo:')
set_cell(3, 10, 1, g('proposta_fls'), 'Fls')
set_cell(3, 10, 3, g('arbitrados_fls'), 'Fls')
set_cell(3, 11, 1, g('proposta_valor'), 'Valor')
set_cell(3, 11, 3, g('arbitrados_valor'), 'Valor')
set_cell(3, 12, 1, g('inicio_pericia'), 'Data/Hora início')
set_cell(3, 12, 3, g('fim_pericia'), 'Fim pericia')

# linha "Quesitos Juízo:" logo abaixo das linhas de quesitos das partes (criada se o modelo não tiver)
rows3 = T[3].rows
if not norm(tc_text(tcs(T[3], 6)[0])).startswith('quesitos'):
    nova = copy.deepcopy(rows3[5]._tr)
    rows3[5]._tr.addnext(nova)
    cel = nova.findall(qn('w:tc'))
    set_tc(cel[0], 'Quesitos Juízo:', negrito=True)
    for c in (2, 4):
        set_tc(cel[c], '')
qj = g('quesitos_juizo') or {}
set_cell(3, 6, 2, qj.get('qtde'), 'Qtde')
set_cell(3, 6, 4, qj.get('fls'), 'Fls')

def linhas_tabela(t, primeira, itens, campos, modelo_idx):
    """Preenche linhas a partir de 'primeira'; cria novas copiando a linha 'modelo_idx'."""
    base = t.rows[modelo_idx]._tr
    for i, item in enumerate(itens):
        idx = primeira + i
        if idx < len(t.rows):
            tr = t.rows[idx]._tr
        else:
            tr = copy.deepcopy(base)
            for b in list(tr.iter(qn('w:b'))):
                b.getparent().remove(b)
            t._tbl.append(tr)
        cells = tr.findall(qn('w:tc'))
        for c, campo in enumerate(campos):
            if campo is not None:
                set_tc(cells[c], item.get(campo, ''))

# Outros peritos (tabela 4: linha 0 título, linha 1 cabeçalho)
op = g('outros_peritos') or []
if op:
    linhas_tabela(T[4], 2, op, ['nomeacao', 'nome', 'especialidade', 'proposta'], 1)

# Advogados (tabela 5: linha 2 = parte 01, linha 3 = parte 02; um advogado por parte)
adv = g('advogados') or []
if adv:
    lado1 = ('autor', 'exequente', 'requerente', 'reclamante', 'embargante', 'impetrante', 'promovente')
    rot_a_norm = norm(g('rotulo_autor') or '')
    autor = [a for a in adv if norm(a.get('parte', '')).startswith(lado1)
             or (rot_a_norm and norm(a.get('parte', '')) == rot_a_norm)]
    reu = [a for a in adv if a not in autor]
    for r, a in ((2, autor[:1]), (3, reu[:1])):
        if a:
            cells = tcs(T[5], r)
            for c, k in enumerate(['nome', 'oab', 'telefone', 'email'], 1):
                set_tc(cells[c], a[0].get(k, ''))

# Histórico (tabela 6: linha 0 cabeçalho)
hist = g('historico') or []
if hist:
    linhas_tabela(T[6], 1, hist, ['fl', 'tipo', 'movimento'], len(T[6].rows) - 1)

# Histórico: coluna "Fl." alargada (comporta "Id. N" do PJe) e linhas vazias finais removidas
tblh = T[6]._tbl
larg = ['1300', '1192', '8082']
for gc, v in zip(tblh.find(qn('w:tblGrid')).findall(qn('w:gridCol')), larg):
    gc.set(qn('w:w'), v)
for tr in tblh.findall(qn('w:tr')):
    for tc, v in zip(tr.findall(qn('w:tc')), larg):
        tcw = tc.find(qn('w:tcPr')).find(qn('w:tcW'))
        if tcw is not None:
            tcw.set(qn('w:w'), v)
for tr in reversed(tblh.findall(qn('w:tr'))[1:]):
    if ''.join(x.text or '' for x in tr.iter(qn('w:t'))).strip():
        break
    tblh.remove(tr)

# rótulos vinculados (Parte 01 / Parte 02): troca no corpo e nas propriedades do documento
rot_a, rot_r = g('rotulo_autor'), g('rotulo_reu')
for sdt in doc.element.body.iter(qn('w:sdt')):
    al = sdt.find(qn('w:sdtPr')).find(qn('w:alias'))
    if al is None:
        continue
    novo = rot_a if al.get(qn('w:val')) == 'Parte 01' else rot_r if al.get(qn('w:val')) == 'Parte 02' else None
    if novo:
        ts = list(sdt.iter(qn('w:t')))
        if ts:
            ts[0].text = novo
            for t in ts[1:]:
                t.text = ''
if rot_a:
    doc.core_properties.author = rot_a
doc.save(saida)

if rot_r:  # Parte 02 está vinculada a docProps/app.xml <Manager>
    tmp = tempfile.mktemp(suffix='.docx')
    with zipfile.ZipFile(saida) as zi, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            data = zi.read(it.filename)
            if it.filename == 'docProps/app.xml':
                x = data.decode('utf-8')
                x = re.sub(r'<Manager>.*?</Manager>', f'<Manager>{rot_r}</Manager>', x) if '<Manager>' in x \
                    else x.replace('</Properties>', f'<Manager>{rot_r}</Manager></Properties>')
                data = x.encode('utf-8')
            zo.writestr(it, data)
    shutil.move(tmp, saida)
print('OK ->', saida)
