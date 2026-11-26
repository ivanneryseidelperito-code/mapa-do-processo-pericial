---
name: "mapa-do-processo-pericial"
description: "Preenche o modelo \"Mapa do Processo\" (Processos Cíveis) do perito a partir dos autos em PDF (eproc/PJe). Use quando pedirem para preencher, montar, corrigir ou atualizar o mapa de um processo."
---

# Mapa do Processo — preenchimento a partir dos autos

Gera o Mapa (modelo DOCX de Ivan Nery Seidel: QUANTO AO PROCESSO, QUANTO À PERÍCIA, HISTÓRICO). Todo dado tem origem identificável (Ev./Id. e folha do PDF). Nada é presumido.

## Fluxo

1. Copiar os anexos para pasta de trabalho (não editar o original). Mais de um PDF: indexar cada um.
2. Baixar scripts e modelo (só executar, não ler os scripts):
   ```bash
   B=https://raw.githubusercontent.com/ivanneryseidelperito-code/mapa-do-processo-pericial/main; mkdir -p s; for f in indexar_autos.py preencher_mapa.py modelo_mapa.docx; do curl -fsSL "$B/$f" -o s/$f || echo FALHA $f; done
   ```
   Falha → pedir os três arquivos ao usuário. Modelo anexado pelo usuário prevalece; se o script abortar por layout divergente, ajustar coordenadas no script, nunca forçar.
3. `python3 s/indexar_autos.py autos.pdf idx > idx/listagem.txt`; ler `idx/listagem.txt` e `idx/capa.json`.
4. Ler integralmente, em `idx/autos_paginado.txt`, as peças-chave da tabela de fontes. Páginas listadas em `idx/paginas_sem_texto.txt` com dado necessário (mandado, procuração, contrato, fichas, contracheques): `pdftoppm -f N -l N -r 100 -png` ou página de separação/certidão.
5. Montar `dados.json` (esquema abaixo).
6. `python3 s/preencher_mapa.py s/modelo_mapa.docx dados.json "<nº processo> - Mapa.docx"` (o script trata células de Citação/Trânsito, Prazo, Quesitos Juízo, coluna Fl. e linhas vazias). Em textos corridos, espaço não separável em "Id. N – fl. X".
7. Conferência: `soffice --headless --convert-to pdf`, renderizar e verificar; reconferir cada data, evento e folha na página-fonte.
8. Entregar o DOCX como arquivo (não artefato) e listar, curto, campos não localizados e divergências.

## Referência às peças

- eproc "Ev. N – fl. X"; PJe "Id. N – fl. X"; intervalo "fl. X-Y". Histórico: "Ev. N\nfl. X".
- "fl." = página do PDF unificado (em regra `pdf_ini`; trecho específico → folha do trecho), nunca a numeração interna da peça.
- Peça em imagem datada pela separação: evento + primeira folha da peça.

## Campos

| Campo | Fonte | Conteúdo |
|---|---|---|
| Processo Principal | Capa | Só nº CNJ |
| Processo Relacionado | Inicial, decisões, certidões (apensos, origem, conexão, execução individual de coletiva, agravo) | Nº(s) CNJ separados por "; "; sem: branco |
| Vara | Capa/última decisão | Vara e comarca ("Vara Única da Comarca de Manga/MG") |
| Classe | Capa | Atual, simplificada, sem código |
| Assuntos | Capa | Assunto + objeto material resumido |
| Partes | Capa | "NOME – CPF ..." / "NOME – CNPJ ..." |
| Valor da Causa | Capa/inicial | R$ |
| Fase | Momento da determinação da perícia | Antes da sentença = instrucao; liquidação/cumprimento = liquidacao |
| Ajuizamento | Autuação/inicial | "dd/mm/aaaa – Ev. N – fl. X" |
| Citação | Mandado/AR cumprido, certidão, ciência | Data do cumprimento/ciência (não da expedição) + ref. |
| AJG? | Decisão de gratuidade | "Sim/Não – Ev. N – fl. X"; sem decisão: "Não apreciada" |
| Sentença, Acórdão, STJ | Decisões | Só ref.; inexistente: "Não houve" |
| Embargos (3 linhas) | ED contra aquela decisão | Ref. (petição e julgamento separados por "; "); sem: "Não houve"; ED contra interlocutória não entram |
| Trânsito em julgado | Certidão | Data certificada + ref. |
| Deferimento | Decisão que determinou a perícia | Só ref. |
| Requisitante | Petição que pediu a perícia | "Exequente – Ev. N – fl. X"; ambas: "Exequente e Executado – Ev. N – fl. X; Ev. M – fl. Y"; de ofício: "Juízo, de ofício – Ev. N – fl. X" |
| Objeto | Título/decisão de deferimento | O que calcular/examinar, com parâmetros do título |
| Objetivo | Controvérsia | Valores de cada parte (com eventos) e critérios de atualização do título |
| Quesitos (partes, Juízo) | Petições de quesitos; decisão com quesitos do juiz | Qtde = nº de quesitos numerados; Fls "Ev. N – fl. X-Y"; não apresentados: branco |
| Nomeação, Prazo | Ato de nomeação; ato que fixa prazo | Só ref. |
| Honorários arbitrados | Decisão sobre honorários | Fls: folha do trecho; Valor: só o fixado, ou branco |
| Outros peritos | Nomeações de outros profissionais | Omitir se não houver |
| Advogados | Capa, procurações, substabelecimentos, contrato, assinaturas, timbres | Um por parte (regra abaixo) |

**Sempre em branco** (do perito), mesmo com dado nos autos: Aceite, Proposta de Honorários (Fls./Valor), Início e Fim da perícia. Linha "Ivan:" só se o usuário indicar.

## Regras de redação

- Identificação e referência: só o conteúdo da tabela, sem resultado de julgamento nem observações.
- Rótulos (`rotulo_autor`, `rotulo_reu`): denominação da capa/última peça, com dois-pontos e no gênero dos autos (Exequente/Executado, Autor/Réu, Requerente/Requerido, Reclamante/Reclamado, Embargante/Embargado, Impetrante/Impetrado; "Executada:" se assim constar). Replicar em Quesitos e Advogados; em Requisitante e Histórico, sem dois-pontos.
- Advogado: entre os constituídos com OAB identificada (excluir estagiários, intimados sem OAB e quem saiu por substabelecimento sem reserva), o de menor nº de inscrição principal; sem OAB: nome "Não consta". Nome sem cargo; OAB "OAB/UF 00.000". E-mail e telefone são prioridade: timbre, rodapé, assinatura, procuração, substabelecimento, contrato, capa. Contato na qualificação da parte é da parte. Procurador público: contato institucional da Procuradoria vale. Ausente nos autos: só fonte pública oficial (site do escritório/órgão, cadastro OAB) com nome + OAB inequívocos; agregadores não. Persistindo: "Não consta".
- Datas dd/mm/aaaa; R$ no padrão brasileiro. Texto impessoal, técnico, conciso; sem opinião, conclusão antecipada ou qualificação de teses.
- Não localizado: "Não consta" (salvo campos em branco). Ato inexistente: "Não houve". Nunca inferir datas, eventos, folhas, valores, OAB ou contatos.
- Divergência entre fontes: usar a peça judicial mais recente e informar na entrega; se for documento do Histórico, registrar também na linha.

## Histórico

Roteiro de leitura do perito: só o necessário à perícia, em ordem cronológica (no mesmo evento, petição antes dos anexos).

**Incluir:** (1) petições vitais: inicial, contestação, réplica, tréplica, pedido de liquidação/cumprimento, impugnação e resposta, embargos à execução e resposta, manifestações sobre cálculos, critérios, marcos ou cumprimento da obrigação; (2) suporte: fichas financeiras, contracheques, contratos, extratos, tabelas de vencimentos, normas juntadas, planilhas/memórias de cálculo, laudos/pareceres anteriores, Contadoria — cada anexo relevante em linha própria com intervalo de folhas; (3) despachos/decisões que definam ou alterem objeto, parâmetros, marcos, rubricas, documentos a exibir ou a condução da perícia.

**Excluir:** o que já está nos campos superiores e valores/critérios já em Objeto/Objetivo (inicial e contestação constam sempre); atos procedimentais (conclusões, intimações, publicações, decursos, certidões de rotina, redistribuição, retificação de classe, arquivamento, migração, mera ciência, procurações e documentos pessoais isolados, incidentes da perícia sem reflexo no cálculo).

**Linha:** Fl. "Ev. N\nfl. X"; Tipo: Petição, Documento, Despacho, Decisão, Certidão, Laudo ou Parecer; Movimento: "dd/mm/aaaa – síntese útil à perícia" (anexos: data de juntada e intervalo de folhas), parte pelo rótulo, sem valores já no Objetivo.

## dados.json

```json
{"processo_principal":"","processo_relacionado":"","vara":"","classe":"","assuntos":"",
 "rotulo_autor":"Exequente:","rotulo_reu":"Executado:","autor":"NOME – CPF ...","reu":"NOME – CNPJ ...","valor_causa":"",
 "fase":"instrucao | liquidacao",
 "ajuizamento":"","citacao":"","ajg":"","transito_julgado":"",
 "sentenca":"","embargos_sentenca":"","acordao":"","embargos_acordao":"","stj":"","embargos_stj":"",
 "deferimento":"","requisitante":"","objeto":"","objetivo":"",
 "quesitos_autor":{"qtde":"","fls":""},"quesitos_reu":{"qtde":"","fls":""},"quesitos_juizo":{"qtde":"","fls":""},
 "ivan":["","",""],"nomeacao":"","aceite":"","prazo":"","proposta_fls":"","proposta_valor":"",
 "arbitrados_fls":"","arbitrados_valor":"","inicio_pericia":"","fim_pericia":"",
 "outros_peritos":[{"nomeacao":"","nome":"","especialidade":"","proposta":""}],
 "advogados":[{"parte":"Exequente:","nome":"","oab":"","telefone":"","email":""},{"parte":"Executado:","nome":"","oab":"","telefone":"","email":""}],
 "historico":[{"fl":"Ev. 1\nfl. 3","tipo":"Petição","movimento":"dd/mm/aaaa – ..."}],
 "tamanho_fonte_meio_pontos":18}
```

Omitido/`null` mantém o modelo; "" deixa em branco; `\n` quebra linha. `advogados`: um item por parte; lado 1 reconhecido por autor/exequente/requerente/reclamante/embargante/impetrante/promovente ou pelo `rotulo_autor`. Exemplo validado de preenchimento: `EXEMPLO.md` do repositório (consultar só em dúvida de formato).

## Correções do usuário

Ao apontar erro, omissão, excesso ou preferência de formato: (1) corrigir e reentregar o Mapa; (2) identificar a causa (regra ausente/ambígua, fonte, leitura, script); (3) generalizar em regra válida para qualquer processo, reescrevendo a conflitante; (4) na mesma resposta, ler este SKILL.md e chamar `propose_skills` (`kind: "improvement"`, `target: "mapa-do-processo-pericial"`) na seção pertinente, sem perguntar antes; causa no script → corrigir, testar no processo em curso e enviar ao repositório `ivanneryseidelperito-code/mapa-do-processo-pericial` ou, sem acesso, entregar o arquivo ao usuário; (5) informar em uma linha a regra criada/alterada. Não virar regra: instrução pontual, dado do caso, nada contrário ao CPC, à NBC TP 01/NBC PP 01 ou que leve a dado não extraído dos autos. Na dúvida, aplicar no Mapa e propor informando a dúvida.
