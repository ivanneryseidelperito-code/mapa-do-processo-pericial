# mapa-do-processo-pericial

Arquivos de apoio da skill "Mapa do Processo" (Ivan Nery Seidel – Perito Contábil).

- `modelo_mapa.docx` – modelo em branco (Processos Cíveis)
- `indexar_autos.py` – indexa autos em PDF (eproc/PJe)
- `preencher_mapa.py` – preenche o modelo a partir de `dados.json`

## proposta-honorarios-periciais

Skill "Proposta de Honorários Periciais" (método CLARA — fase 1), acionada após o Mapa do Processo.

- `proposta-honorarios-periciais/SKILL.md` – instruções da skill
- `proposta-honorarios-periciais/modelo/modelo_proposta_honorarios.docx` – layout tipográfico do perito, com marcadores `{{...}}`
- `proposta-honorarios-periciais/scripts/gerar_proposta.py` – preenche o modelo a partir de `dados.json` (tabela de etapas, subtotal, desconto, total e extenso)
- `proposta-honorarios-periciais/exemplo_dados.json` – exemplo de entrada (valor-hora e link da fonte obrigatórios)

### Layout do modelo de proposta

- A4; margens sup. 3 cm, esq. 3 cm, inf. 2 cm, dir. 2 cm; cabeçalho com logotipo "Ivan Seidel — Perito Contábil e Financeiro"; rodapé verde com contatos e paginação "Pág. x-y".
- Corpo em Dupincel Text; títulos de seção em Segoe UI negrito 13 pt; quadro de partes em negrito itálico; caixa cinza com valor e extenso; tabela de etapas em 10 pt; alíneas a), b)… automáticas; controles de conteúdo vinculados às propriedades do documento (processo, partes, cidade).
- Estrutura (NBC PP 01 R2): Endereçamento → Processo/Autor/Réu → Qualificação do perito → I – Da Nomeação (aceite, item 19; impedimento/suspeição, CPC 144, 145 e 148, itens 14 e 16; Certidão de Regularidade Profissional, item 5) → II – Dos Honorários (17 fatores do item 32; alíneas a–d; fonte do valor-hora, item 33; caixa de valor; planejamento até a homologação, item 34, com um parágrafo por etapa e quadro-resumo; nota de rodapé do valor-hora) → ressalvas de quesitos suplementares (CPC 469; item 37) e despesas (item 35) → prazo (CPC 465 e 476; itens 24 e 27) → III – Dos Pedidos (homologação, CPC 465 §3º; depósito, CPC 82 e 95; levantamento de 50%, CPC 465 §4º e item 38; fixação do prazo) → fecho, local/data, assinatura.
- `proposta-honorarios-periciais/APRENDIZADO.md` – histórico das regras aprendidas (fora da SKILL.md para economizar tokens)

```
python3 proposta-honorarios-periciais/scripts/gerar_proposta.py dados.json Proposta.docx
```
