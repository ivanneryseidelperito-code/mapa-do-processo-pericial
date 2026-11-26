---
name: "mapa-do-processo-pericial"
description: "Preenche o modelo \"Mapa do Processo\" (Processos Cíveis) do perito a partir dos autos em PDF (eproc/PJe). Use quando pedirem para preencher, montar, corrigir ou atualizar o mapa de um processo."
---

# Mapa do Processo — preenchimento a partir dos autos

Gera o "Mapa do Processo" (modelo DOCX de Ivan Nery Seidel: QUANTO AO PROCESSO, QUANTO À PERÍCIA, HISTÓRICO) com dados extraídos dos autos. Todo dado preenchido tem origem identificável (Ev./Id. e folha do PDF). Nada é presumido.

## Fluxo

1. Copiar os anexos para pasta de trabalho própria (não editar o original). Autos em PDF unificado; havendo mais de um PDF, indexar cada um.
2. Baixar scripts e modelo (não ler o conteúdo dos scripts; apenas executar):
   ```bash
   B=https://raw.githubusercontent.com/ivanneryseidelperito-code/mapa-do-processo-pericial/main; mkdir -p s; for f in indexar_autos.py preencher_mapa.py modelo_mapa.docx; do curl -fsSL "$B/$f" -o s/$f || echo FALHA $f; done
   ```
   Se o download falhar, pedir ao usuário que anexe os três arquivos do repositório. Se o usuário anexar outro modelo, usá-lo; o script valida o layout e aborta se divergir (ajustar coordenadas no script, nunca forçar).
3. Indexar: `python3 s/indexar_autos.py autos.pdf idx > idx/listagem.txt`. Ler `idx/listagem.txt` (eventos, datas, páginas) e `idx/capa.json`.
4. Ler integralmente, em `idx/autos_paginado.txt`, as peças-chave da tabela de fontes. Páginas de `idx/paginas_sem_texto.txt` são imagem: se contiverem dado necessário (mandado, procuração, contrato, fichas financeiras, contracheques), renderizar (`pdftoppm -f N -l N -r 100 -png`) ou usar a página de separação/certidão correspondente.
5. Montar `dados.json` (esquema abaixo).
6. Preencher: `python3 s/preencher_mapa.py s/modelo_mapa.docx dados.json "<nº processo> - Mapa.docx"`. O script une células de Citação/Trânsito, grava "Prazo: ..." na célula livre da linha Nomeação, cria "Quesitos Juízo", alarga a coluna Fl. e remove linhas vazias. Em textos corridos (Objeto, Objetivo, Histórico), usar espaço não separável em "Id. N – fl. X".
7. Conferência obrigatória: `soffice --headless --convert-to pdf`, renderizar e verificar visualmente; reconferir cada data, evento e folha contra a página-fonte.
8. Entregar o DOCX como arquivo (não artefato) e listar, de forma curta, campos não localizados e divergências entre fontes.

## Referência às peças

- eproc "Ev. N – fl. X"; PJe "Id. N – fl. X"; intervalo "fl. X-Y".
- "fl." = página do PDF unificado (em regra `pdf_ini`; quando o campo pede trecho específico, a folha do trecho). Nunca a numeração interna da peça.
- Coluna Fl. do Histórico: "Ev. N\nfl. X" (PJe "Id. N\nfl. X").
- Peça em imagem datada pela página de separação: citar o evento e a primeira folha da peça.

## Fontes e conteúdo de cada campo

| Campo | Fonte | Conteúdo |
|---|---|---|
| Processo Principal | Capa/cabeçalho | Só o nº CNJ |
| Processo Relacionado | Inicial, decisões, certidões (apensos, origem, conexão, execução individual de coletiva, agravo) | Só nº(s) CNJ, separados por "; "; sem relacionado: branco |
| Vara | Capa/última decisão | Vara e comarca (ex.: "Vara Única da Comarca de Manga/MG") |
| Classe | Capa | Classe atual simplificada, sem código |
| Assuntos | Capa | Assunto + objeto material resumido |
| Partes | Capa | "NOME – CPF ..." ou "NOME – CNPJ ..." |
| Valor da Causa | Capa/inicial | R$ |
| Fase | Momento da determinação da perícia | Antes da sentença = instrucao; liquidação/cumprimento = liquidacao |
| Ajuizamento | Autuação/inicial | "dd/mm/aaaa – Ev. N – fl. X" |
| Citação | Mandado/AR cumprido, certidão, ciência | Data do cumprimento/ciência (não da expedição) + ref. |
| AJG? | Decisão sobre gratuidade | "Sim/Não – Ev. N – fl. X"; sem decisão: "Não apreciada" |
| Sentença, Acórdão, STJ | Decisões | Só "Ev. N – fl. X"; inexistente: "Não houve" |
| Embargos (3 linhas) | ED contra aquela decisão | "Ev. N – fl. X" (petição e julgamento separados por "; "); sem ED: "Não houve". ED contra interlocutória não entram |
| Trânsito em julgado | Certidão | Data certificada + ref. |
| Deferimento | Decisão que determinou a perícia | Só ref. |
| Requisitante | Petição que pediu a perícia | "Exequente – Ev. N – fl. X"; ambas: "Exequente e Executado – Ev. N – fl. X; Ev. M – fl. Y"; de ofício: "Juízo, de ofício – Ev. N – fl. X" |
| Objeto | Título / decisão de deferimento | O que calcular/examinar, com parâmetros do título |
| Objetivo | Controvérsia | Valores de cada parte (com eventos) e critérios de atualização do título |
| Quesitos (parte 1, parte 2, Juízo) | Petições de quesitos; decisão com quesitos do juiz | Qtde = nº de quesitos numerados; Fls "Ev. N – fl. X-Y"; não apresentados: branco |
| Nomeação, Prazo | Ato de nomeação; ato que fixa prazo | Só ref. |
| Honorários arbitrados | Decisão que trata dos honorários | Fls: folha do trecho sobre honorários; Valor: só o fixado, ou branco |
| Outros peritos | Nomeações de outros profissionais | Omitir se não houver |
| Advogados | Capa, procurações, substabelecimentos, contrato, assinaturas, timbres | Um por parte (regra abaixo) |

**Sempre em branco** (reservados ao perito), mesmo havendo dado nos autos: Aceite, Proposta de Honorários (Fls./Valor), Início e Fim da perícia. Linha "Ivan:" só se o usuário indicar.

## Regras de redação

- Campos de identificação e de referência levam apenas o conteúdo da tabela, sem resultado de julgamento nem observações.
- Rótulos das partes (`rotulo_autor`, `rotulo_reu`): denominação da capa/última peça, com dois-pontos e no gênero dos autos (Exequente/Executado, Autor/Réu, Requerente/Requerido, Reclamante/Reclamado, Embargante/Embargado, Impetrante/Impetrado; "Executada:" se assim constar). Replicam-se em Quesitos e Advogados. Em Requisitante e Histórico, mesmo rótulo sem dois-pontos.
- Advogado (um por parte): entre os constituídos com OAB identificada (excluir estagiários, destinatários de intimação sem OAB e quem saiu por substabelecimento sem reserva), escolher o de menor nº de inscrição principal. Sem OAB identificada: nome "Não consta". Nome sem cargo ou observação; OAB "OAB/UF 00.000". E-mail e telefone têm prioridade: buscar em timbre, rodapé, assinatura, procuração, substabelecimento, contrato e capa. Contato na qualificação da parte é da parte. Procurador público: contato institucional da Procuradoria é válido. Se ausente nos autos, só fonte pública oficial (site do escritório/órgão, cadastro OAB) com identidade inequívoca (nome + OAB); agregadores não servem. Persistindo: "Não consta".
- Datas dd/mm/aaaa; valores em R$ no padrão brasileiro.
- Texto impessoal, técnico e conciso; sem opinião, sem antecipar conclusão, sem qualificar teses.
- Dado não localizado: "Não consta" (salvo campos que ficam em branco). Ato inexistente: "Não houve". Nunca inferir datas, eventos, folhas, valores, OAB ou contatos.
- Divergência entre fontes: usar a peça judicial mais recente e informar na entrega; se no documento do Histórico, registrar também na linha dele.

## Histórico

Roteiro de leitura do perito: só documentos necessários à perícia, em ordem cronológica (no mesmo evento, petição antes dos anexos).

**Incluir:** (1) petições vitais: inicial, contestação, réplica, tréplica, pedido de liquidação/cumprimento, impugnação e resposta, embargos à execução e resposta, manifestações sobre cálculos, critérios, marcos ou cumprimento da obrigação; (2) documentos de suporte: fichas financeiras, contracheques, contratos, extratos, tabelas de vencimentos, normas juntadas, planilhas e memórias de cálculo, laudos/pareceres anteriores, Contadoria — cada anexo relevante em linha própria com intervalo de folhas; (3) despachos/decisões que definam ou alterem objeto, parâmetros, marcos, rubricas, documentos a exibir ou a condução da perícia.

**Excluir:** o que já consta nos campos superiores (sentença, acórdãos, ED, citação, AJG, trânsito, deferimento, quesitos, nomeação, prazo, honorários) e valores/critérios já em Objeto/Objetivo — exceto a inicial e a contestação, que constam sempre; atos procedimentais (conclusões, intimações, publicações, decursos, certidões de rotina, redistribuição, retificação de classe, arquivamento, migração, mera ciência, procurações e documentos pessoais isolados, incidentes sobre a realização da perícia sem reflexo no cálculo).

**Linha:** Fl. "Ev. N\nfl. X"; Tipo: Petição, Documento, Despacho, Decisão, Certidão, Laudo ou Parecer; Movimento: "dd/mm/aaaa – síntese útil à perícia" (anexos: data de juntada e intervalo de folhas), com a parte identificada pelo rótulo e sem valores já constantes do Objetivo.

## Esquema do dados.json

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

Campo omitido ou `null` mantém o modelo; "" deixa em branco; `\n` quebra linha na célula. `advogados`: um item por parte; o lado 1 é reconhecido por autor/exequente/requerente/reclamante/embargante/impetrante/promovente ou pelo `rotulo_autor`.

## Correções do usuário

Quando o usuário apontar erro, omissão, excesso ou preferência de formato: (1) corrigir e reentregar o Mapa; (2) identificar a causa (regra ausente/ambígua, fonte errada, leitura, script); (3) generalizar em regra válida para qualquer processo, reescrevendo a regra conflitante; (4) na mesma resposta, ler este SKILL.md e chamar `propose_skills` (`kind: "improvement"`, `target: "mapa-do-processo-pericial"`) alterando a seção pertinente — sem perguntar antes; se a causa for o script, corrigi-lo, testá-lo no processo em curso e enviá-lo ao repositório `ivanneryseidelperito-code/mapa-do-processo-pericial` (GitHub conectado) ou, se não houver acesso, entregar o arquivo ao usuário para substituição; (5) informar em uma linha a regra criada/alterada. Não converter em regra: instrução pontual, dado do caso concreto, nem nada contrário ao CPC, à NBC TP 01/NBC PP 01 ou que leve a dado não extraído dos autos. Na dúvida, aplicar no Mapa e propor informando a dúvida.

## Exemplo validado (eproc, TJMG, cumprimento de sentença contra município)

Classe "Cumprimento de Sentença"; rótulos Exequente/Executado; fase Liquidação. Ajuizamento "25/01/2024 – Ev. 1 – fl. 3"; Citação "05/02/2024 – Ev. 9 – fl. 86" (mandado em imagem, data da separação); AJG "Sim – Ev. 5 – fl. 75"; Trânsito "21/11/2024 – Ev. 32 – fl. 137"; Sentença "Ev. 28 – fl. 122"; ED/Acórdão/STJ "Não houve". Deferimento e Requisitante "Juízo, de ofício – Ev. 104 – fl. 288". Quesitos do exequente 18, "Ev. 115 – fl. 320-322"; executado e Juízo em branco. Nomeação "Ev. 118 – fl. 329"; Prazo "Ev. 116 – fl. 326". Honorários: Fls. "Ev. 104 – fl. 288", Valor em branco. Advogado do exequente sem contato nos autos (telefone da procuração era da parte); procuradora municipal com e-mail institucional. Histórico com 17 linhas (inicial e anexos, petições sobre marco inicial, pedido de cumprimento, impugnação — com nº de processo divergente registrado na linha —, resposta, Contadoria, decisão que remeteu critérios à perícia).