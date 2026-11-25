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

```
python3 proposta-honorarios-periciais/scripts/gerar_proposta.py dados.json Proposta.docx
```
