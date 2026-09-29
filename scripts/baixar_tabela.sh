#!/bin/bash
# Baixa os 10 arquivos de uma tabela dos dados abertos do CNPJ (ex.: Socios, Empresas) para o mes indicado.
# Uso: ./baixar_tabela.sh Empresas 2026-09
TABELA="${1:?informe a tabela (Socios, Empresas)}"
MES="${2:-2026-09}"
T=gn672Ad4CF8N6TK
B="https://arquivos.receitafederal.gov.br/public.php/webdav/Dados/Cadastros/CNPJ/$MES"
mkdir -p "../dados/$MES" && cd "../dados/$MES" || exit 1
for i in 0 1 2 3 4 5 6 7 8 9; do
  echo "$TABELA$i.zip"
  curl -s -f -C - --retry 3 -u "$T:" -o "$TABELA$i.zip" "$B/$TABELA$i.zip" || echo "FALHOU $TABELA$i"
done
echo "FIM"
