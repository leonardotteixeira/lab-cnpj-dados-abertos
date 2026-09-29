# lab-cnpj-dados-abertos

Scripts para procurar, nos **dados abertos do CNPJ** da Receita Federal, empresas em que um nome aparece como
sócio, MEI ou empresário individual. Pensado para um levantamento sobre **a própria pessoa, com autorização dela**.

> **Este repositório contém só código e documentação. Nunca versione CPF, nomes, o `.env`, os arquivos baixados
> nem os resultados.** O `.gitignore` bloqueia tudo, exceto scripts, este README e o `.env.example`.
> Mantenha o repositório **privado**.

Estado: **pausado**. O método funciona para a parte de empresas; a parte de processos judiciais não foi feita.

## Método

1. Baixar `Socios*.zip` e `Empresas*.zip` dos dados abertos do CNPJ (mês desejado).
2. Filtrar **localmente**. O CPF completo nunca sai da máquina.
3. Para os candidatos, consultar dados públicos da empresa **só pelo CNPJ** (etapa não implementada).
4. Marcar cada achado como confirmado ou "a confirmar" e listar as limitações no relatório.

## Como funciona cada tabela

| Tabela | Quem aparece | Como identificar a pessoa |
|---|---|---|
| **Sócios** | Sócios de empresas com sócios (ME, EPP, Ltda...) | Nome + **6 dígitos do meio do CPF** (formato `***DDDDDD**`, validado nos dados) |
| **Empresas**, natureza jurídica **2135** | MEI e empresário individual (**não têm sócios**) | Depende do formato da razão social, abaixo |

Formatos da razão social do empresário individual (validados em setembro de 2026):

| Formato | Volume | O que dá para concluir |
|---|---|---|
| `NOME + 11 dígitos` | ~18,8 milhões | Os 11 dígitos são **CPF válido** (99,9997% passam no cálculo dos dígitos verificadores). Comparar com o CPF confirma ou descarta a identidade. |
| `12.345.678 NOME` | ~16,3 milhões | O número é o **CNPJ básico da própria empresa**, não a pessoa. Só o nome identifica: risco de homônimo. |
| Outros (só o nome) | ~10,4 milhões | Só o nome identifica. |

## Como usar

Requisitos: Python 3.11+ e ~2 GB livres.

```bash
cp .env.example .env            # preencha CPF_DA_CLIENTE (11 dígitos) e NOME_COMPLETO
cd scripts
./baixar_tabela.sh Socios 2026-09
./baixar_tabela.sh Empresas 2026-09
cd ..
python scripts/filtrar_socios.py 2026-09
python scripts/filtrar_empresas.py formato 2026-09    # só o formato, sem nomes reais
python scripts/filtrar_empresas.py filtrar 2026-09
```

Os scripts **nunca imprimem o CPF nem o nome**, só contagens. O resultado detalhado vai para `resultados/`.

## Limitações (devem constar em qualquer relatório)

- **É a foto de um mês.** Empresa aberta depois da data do arquivo não aparece.
- **Cruzamento parcial nos Sócios:** nome + 6 dígitos não prova identidade.
- **MEI sem CPF na razão social:** só o nome identifica, e nomes parecidos (mesmo primeiro e último nome)
  ficam sem resolução com dados abertos.
- **Ausência nos dados não prova que não existe.** A confirmação segura vem da própria pessoa, no gov.br e no
  Portal do Empreendedor.
- **Não cobre processos judiciais.** Isso exige certidões dos tribunais e do CNJ.
- **Não cobre** empresas em que a pessoa aparece só como administradora ou representante, nem empresas no exterior.

## Onde estão os dados

Compartilhamento público de arquivos da Receita Federal: `arquivos.receitafederal.gov.br`, pasta
`Dados/Cadastros/CNPJ/AAAA-MM/`, acessada por WebDAV. O endereço antigo (`dadosabertos.rfb.gov.br`) saiu do ar.
Confira os termos de uso e o layout na documentação oficial antes de redistribuir.

## Aspectos legais

Tratar dados pessoais, mesmo os públicos, exige finalidade, necessidade e base legal (LGPD). Use com
autorização da pessoa, guarde o mínimo, com segurança, e apague ao final. Interpretar processos e dar
conclusão jurídica é papel de advogado.
