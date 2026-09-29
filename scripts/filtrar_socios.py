"""Procura, nos Socios dos dados abertos do CNPJ, registros que batem com o CPF e o nome da cliente.

Como o arquivo publico traz o CPF do socio MASCARADO (so os 6 digitos do meio), o cruzamento e por
nome + esses 6 digitos. O resultado sao CANDIDATOS a confirmar, nunca prova.

Le CPF_DA_CLIENTE e NOME_COMPLETO do .env. NUNCA imprime o CPF nem o nome: so contagens.
Grava resultados/candidatos.csv (fora do Git).

Uso: python scripts/filtrar_socios.py 2026-09
"""

import csv
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MES = sys.argv[1] if len(sys.argv) > 1 else "2026-09"


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento).strip().upper()


env = dict(l.strip().split("=", 1) for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines() if "=" in l)
cpf = re.sub(r"\D", "", env.get("CPF_DA_CLIENTE", ""))
nome = normalizar(env.get("NOME_COMPLETO", ""))
if len(cpf) != 11 or len(nome.split()) < 2:
    raise SystemExit("Preencha CPF_DA_CLIENTE (11 digitos) e NOME_COMPLETO no .env")

mascara = f"***{cpf[3:9]}**"  # formato do CPF mascarado nos dados abertos
partes = nome.split()
primeiro, ultimo = partes[0], partes[-1]

# Layout dos Socios (sem cabecalho, separador ';', latin-1):
# 0 cnpj_basico | 1 tipo (1=PJ, 2=PF, 3=estrangeiro) | 2 nome | 3 cpf/cnpj mascarado | 4 qualificacao |
# 5 data_entrada | 6 pais | 7 rep_legal | 8 nome_rep | 9 qualif_rep | 10 faixa_etaria
pasta = RAIZ / "dados" / MES
arquivos = sorted(pasta.glob("Socios*.zip"))
if not arquivos:
    raise SystemExit(f"Nenhum Socios*.zip em {pasta}")

candidatos = []
linhas_lidas = 0
for arq in arquivos:
    with zipfile.ZipFile(arq) as z:
        for membro in z.namelist():
            with z.open(membro) as f:
                leitor = csv.reader((l.decode("latin-1") for l in f), delimiter=";")
                for linha in leitor:
                    linhas_lidas += 1
                    if len(linha) < 6 or linha[1] != "2" or linha[3] != mascara:
                        continue
                    nome_reg = normalizar(linha[2])
                    if nome_reg == nome:
                        nivel = "A - nome exato + 6 digitos do CPF"
                    elif nome_reg.split()[:1] == [primeiro] and nome_reg.split()[-1:] == [ultimo]:
                        nivel = "B - primeiro e ultimo nome + 6 digitos do CPF"
                    else:
                        continue
                    candidatos.append(
                        {
                            "cnpj_basico": linha[0],
                            "nivel": nivel,
                            "nome_no_registro": linha[2],
                            "qualificacao_codigo": linha[4],
                            "data_entrada_sociedade": linha[5],
                        }
                    )

saida = RAIZ / "resultados" / "candidatos.csv"
saida.parent.mkdir(exist_ok=True)
with saida.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(
        f, fieldnames=["cnpj_basico", "nivel", "nome_no_registro", "qualificacao_codigo", "data_entrada_sociedade"]
    )
    w.writeheader()
    w.writerows(candidatos)

print(f"Mes: {MES} | arquivos: {len(arquivos)} | linhas lidas: {linhas_lidas:,}")
print(f"Candidatos nivel A: {sum(c['nivel'].startswith('A') for c in candidatos)}")
print(f"Candidatos nivel B: {sum(c['nivel'].startswith('B') for c in candidatos)}")
print(f"Gravado em: {saida}")
