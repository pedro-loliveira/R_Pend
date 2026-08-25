# Relatório Automático de Pendências por Email

Script que gera e envia (via Outlook) um relatório em HTML com itens
produtivos pendentes de encerramento, cruzando dados de duas fontes (uma
API interna e um banco SQL). Roda em loop, disparando em horários
configuráveis nos dias úteis, e mantém um histórico para marcar itens
"persistentes" (que já apareceram em relatórios anteriores).


## O que foi ajustado em relação ao script original

Isso era um único arquivo de ~450 linhas, com dados sensíveis embutidos no
código. Para virar portfólio, foi feito o seguinte:

- **Separação em módulos** por responsabilidade (config, estilos, cruzamento
  de dados, histórico, geração de HTML, envio).
- **Dados sensíveis extraídos para `config.py`**, que fica fora do git: nomes
  de destinatários, emails, caminhos de rede/OneDrive com nome de usuário e
  empresa.
- **Nomenclatura genérica**
- **`.gitignore`** cobrindo `config.py`, arquivos `.msg` gerados, o JSON de
  histórico, caches de Python e pastas de IDE/venv.