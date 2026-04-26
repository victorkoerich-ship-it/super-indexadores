# Próximos passos — Deploy em nuvem (grátis)

## Stack escolhida

- **Hospedagem**: Streamlit Community Cloud (grátis, repo público no GitHub, sem sleep, redeploy automático a cada push)
- **Atualização automática**: GitHub Actions em cron mensal (grátis em repo público)
- **Entrada manual do CUB-SC**: formulário no próprio app, sem senha (valor é público)

## Por que não Google Apps Script

Dá pra buscar dados, mas não hospeda app Python e precisaria de token do GitHub pra atualizar o CSV do repo — duas plataformas pra manter quando uma resolve.

## Fontes de dados

| Indexador | Fonte | Como obter |
|---|---|---|
| SELIC | Bacen SGS | `https://api.bcb.gov.br/dados/serie/bcdata.sgs.4390/dados` |
| USD/PTAX | Bacen SGS | SGS código 3698 (ou PTAX diário agregado mensal) |
| IGP-M | Bacen SGS | SGS código 189 |
| INCC-M | Bacen SGS | SGS código 192 |
| IPCA | IBGE SIDRA | API SIDRA tabela 1737 |
| INPC | IBGE SIDRA | API SIDRA tabela 1736 |
| **CUB-SC** | Sinduscon-SC | **Entrada manual no app** (R$/m²) |

## Passos de implementação

### 1. Preparar o repositório
- [ ] Criar repo público no GitHub (ex.: `indexadores`)
- [ ] Adicionar `requirements.txt` com: `streamlit`, `pandas`, `numpy`, `plotly`, `requests`, `PyGithub`
- [ ] Commitar `app_indexadores.py`, `indexadores_mensal.csv`, `CLAUDE.md`

### 2. Script de coleta (`scripts/atualizar_dados.py`)
- [ ] Função por fonte (Bacen, SIDRA) que retorna a variação % do mês anterior
- [ ] Lê `indexadores_mensal.csv`, insere nova linha do mês com dados de API e **CUB_SC vazio (NaN)**
- [ ] Idempotente: se a linha do mês já existe, não duplica
- [ ] Grava de volta no CSV

### 3. Workflow do GitHub Actions (`.github/workflows/atualizar.yml`)
```yaml
on:
  schedule:
    - cron: '0 12 1-5 * *'  # 09:00 BRT, dias 1 a 5
  workflow_dispatch:        # permite rodar manualmente
```
- [ ] Job: checkout → setup-python → `pip install -r requirements.txt` → `python scripts/atualizar_dados.py`
- [ ] Se CSV mudou: `git commit` + `git push` com token padrão `GITHUB_TOKEN`
- [ ] Rodar manualmente uma vez (`workflow_dispatch`) pra validar antes do cron

### 4. UI de entrada manual do CUB-SC no app
- [ ] No topo do app, detectar se existe linha do mês com `CUB_SC = NaN`
- [ ] Mostrar formulário: "Informe o CUB-SC de MM/YYYY (R$/m²):" + campo numérico + botão salvar
- [ ] No submit: calcular variação % vs. mês anterior e atualizar CSV
- [ ] Commitar via API do GitHub usando `PyGithub` + token em `st.secrets["github_token"]`
- [ ] Limpar o cache do `@st.cache_data` após salvar (`load_data.clear()`)

### 5. (Opcional) Guardar CUB absoluto
- [ ] Criar `cub_sc_absoluto.csv` com colunas `Data, valor_rs_m2`
- [ ] Adicionar gráfico "CUB-SC em R$/m² ao longo do tempo" no dashboard
- [ ] Facilita leitura pra quem é da construção

### 6. Deploy no Streamlit Community Cloud
- [ ] Login em https://share.streamlit.io com a conta GitHub
- [ ] "New app" → selecionar repo → branch `main` → arquivo `app_indexadores.py`
- [ ] Em "Advanced settings → Secrets", colar:
  ```toml
  github_token = "ghp_..."
  repo = "seu-usuario/indexadores"
  ```
- [ ] Gerar token em https://github.com/settings/tokens (fine-grained, apenas `Contents: write` no repo)
- [ ] Deploy e testar URL pública

## Pontos de atenção

- **Token do GitHub**: usar fine-grained com escopo mínimo (só `Contents: write` no repo específico). Se vazar, revogar e gerar outro.
- **Race condition**: se o Actions e o usuário commitarem ao mesmo tempo, o push do app pode falhar. Tratar com retry ou `pull --rebase` no código de commit.
- **Cache do Streamlit**: `@st.cache_data` persiste entre sessões na mesma instância. Chamar `load_data.clear()` depois de atualizar o CSV.
- **Feriado no dia 1º**: o cron roda dias 1-5 de propósito pra cobrir. O script é idempotente, então rodar várias vezes não cria problema.
- **CUB-SC do mês em aberto**: o Sinduscon divulga entre dia 5 e 10 do mês seguinte. O formulário no app pode aparecer por alguns dias até alguém preencher — é esperado.
