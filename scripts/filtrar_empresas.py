"""Procura MEI / empresario individual pelo nome da cliente na tabela de Empresas dos dados abertos do CNPJ.

Layout das Empresas (sem cabecalho, ';', latin-1):
0 cnpj_basico | 1 razao_social | 2 natureza_juridica | 3 qualificacao_responsavel | 4 capital_social |
5 porte | 6 ente_federativo

Empresario individual (inclui MEI) tem natureza juridica 2135. A razao social costuma ser o nome da pessoa,
as vezes seguido de numeros (formato deve ser verificado nos dados).

Modos:
  formato  -> mostra so o FORMATO das razoes sociais de natureza 2135 (letras -> X, digitos -> D), sem nomes reais
  filtrar  -> procura o nome da cliente; grava resultados/candidatos_ei.csv
NUNCA imprime o nome nem o CPF da cliente: so contagens.

Uso: python scripts/filtrar_empresas.py formato 2026-09
     python scripts/filtrar_empresas.py filtrar 2026-09
"""

import csv
import re
import sys
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MODO = sys.argv[1] if len(sys.argv) > 1 else "formato"
MES = sys.argv[2] if len(sys.argv) > 2 else "2026-09"
NATUREZA_EI = "2135"


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento).strip().upper()


def linhas_empresas():
    arquivos = sorted((RAIZ / "dados" / MES).glob("Empresas*.zip"))
    if not arquivos:
        raise SystemExit("Nenhum Empresas*.zip encontrado")
    for arq in arquivos:
        with zipfile.ZipFile(arq) as z:
            for membro in z.namelist():
                with z.open(membro) as f:
                    for linha in csv.reader((l.decode("latin-1") for l in f), delimiter=";"):
                        if len(linha) >= 3:
                            yield linha


if MODO == "formato":
    formatos, total = Counter(), 0
    for linha in linhas_empresas():
        if linha[2] == NATUREZA_EI:
            total += 1
            # digitos primeiro (viram "#n" com o tamanho), depois palavras de letras (viram "A")
            forma = re.sub(r"\d+", lambda m: f"#{len(m.group())}", normalizar(linha[1]))
            formatos[re.sub(r"[A-Z]+", "A", forma)] += 1
    print(f"Empresarios individuais (natureza {NATUREZA_EI}): {total:,}")
    print("Formatos mais comuns da razao social (A = palavra, #n = numero de n digitos):")
    for forma, qtd in formatos.most_common(6):
        print(f"  {forma!r}: {qtd:,}")
    sys.exit()

env = dict(l.strip().split("=", 1) for l in (RAIZ / ".env").read_text(encoding="utf-8").splitlines() if "=" in l)
nome = normalizar(env.get("NOME_COMPLETO", ""))
cpf = re.sub(r"\D", "", env.get("CPF_DA_CLIENTE", ""))
if len(nome.split()) < 2:
    raise SystemExit("Preencha NOME_COMPLETO no .env")
partes = nome.split()
achados = []
descartados_por_cpf_diferente = 0
for linha in linhas_empresas():
    if linha[2] != NATUREZA_EI:
        continue
    razao = normalizar(linha[1])
    # Formato 1: "NOME 12345678901" (11 digitos no fim). Formato 2: "12.345.678 NOME" (numero no inicio).
    m_fim = re.search(r"\s(\d{11})$", razao)
    so_nome = re.sub(r"^\d{2}\.\d{3}\.\d{3}\s+", "", razao)
    so_nome = re.sub(r"[\d\*\.\-\s]+$", "", so_nome).strip()
    mesmo_nome = so_nome == nome
    mesmos_extremos = so_nome.split()[:1] == partes[:1] and so_nome.split()[-1:] == partes[-1:]
    if not (mesmo_nome or mesmos_extremos):
        continue
    if m_fim:
        if m_fim.group(1) == cpf:
            nivel = "A+ - CPF completo confere na razao social (identidade confirmada)"
        else:
            descartados_por_cpf_diferente += 1  # outra pessoa (homonimo): nao entra no relatorio
            continue
    elif mesmo_nome:
        nivel = "A - nome exato, sem CPF na razao social (a confirmar)"
    else:
        nivel = "B - primeiro e ultimo nome, sem CPF na razao social (a confirmar)"
    achados.append({"cnpj_basico": linha[0], "nivel": nivel, "razao_social": linha[1], "capital_social": linha[4]})

saida = RAIZ / "resultados" / "candidatos_ei.csv"
saida.parent.mkdir(exist_ok=True)
with saida.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["cnpj_basico", "nivel", "razao_social", "capital_social"])
    w.writeheader()
    w.writerows(achados)

print(f"A+ (CPF completo confere): {sum(a['nivel'].startswith('A+') for a in achados)}")
print(f"A  (nome exato, sem CPF):  {sum(a['nivel'].startswith('A -') for a in achados)}")
print(f"B  (primeiro/ultimo nome): {sum(a['nivel'].startswith('B') for a in achados)}")
print(f"Homonimos descartados (mesmo nome, CPF diferente): {descartados_por_cpf_diferente}")
print(f"Gravado em: {saida}")
