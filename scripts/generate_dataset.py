"""Gera a base rotulada usada para treinar o classificador de documentos.

Os textos são sintéticos: partem de modelos de documentos judiciais reais, com nomes, números,
varas, cabeçalhos e ruído de OCR aleatórios. Cada linha guarda o id do modelo (template) para
que a avaliação use modelos que o classificador não viu no treino.
"""
import argparse
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FIRST_NAMES = ["Maria", "José", "Ana", "João", "Francisca", "Antônio", "Juliana", "Carlos", "Patrícia",
               "Paulo", "Aline", "Marcos", "Fernanda", "Raimundo", "Luciana", "Pedro", "Camila", "Rafael"]
LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
              "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Moura"]
COURTS = ["1ª Vara Federal de Cuiabá/MT", "19ª Vara Federal - Sobral/CE", "3ª Vara Cível de São Paulo/SP",
          "2ª Vara da Fazenda Pública de Recife/PE", "Juizado Especial Federal de Fortaleza/CE",
          "5ª Vara Federal de Porto Alegre/RS", "Vara Única de Sorriso/MT", "7ª Vara Cível de Belo Horizonte/MG"]
DEFENDANTS = ["Instituto Nacional do Seguro Social - INSS", "União Federal", "Estado de Mato Grosso",
              "Município de Cuiabá", "Caixa Econômica Federal", "Banco do Brasil S.A."]
SUBJECTS = ["aposentadoria por invalidez", "auxílio-doença", "benefício assistencial (LOAS)",
            "revisão de benefício previdenciário", "diferenças salariais de servidor público",
            "repetição de indébito tributário", "indenização por danos morais", "pensão por morte"]
HEADERS = ["PODER JUDICIÁRIO", "JUSTIÇA FEDERAL", "TRIBUNAL DE JUSTIÇA DO ESTADO", "Seção Judiciária",
           "Processo Judicial Eletrônico - PJe", "Documento assinado eletronicamente"]
FOOTERS = ["Assinado eletronicamente por servidor da secretaria.", "Este documento pode ser verificado no endereço do tribunal.",
           "Intimem-se as partes.", "Cumpra-se.", "Publique-se. Registre-se. Intimem-se."]


def person(rng):
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)} {rng.choice(LAST_NAMES)}"


def money(rng, low=300, high=180000):
    value = rng.uniform(low, high)
    whole, cents = f"{value:.2f}".split(".")
    whole = f"{int(whole):,}".replace(",", ".")
    return f"R$ {whole},{cents}"


def case_number(rng):
    segment = rng.choice(["4", "8", "4", "8", "5"])
    return (f"{rng.randint(0, 9999999):07d}-{rng.randint(10, 99)}.{rng.randint(2015, 2024)}."
            f"{segment}.{rng.randint(1, 27):02d}.{rng.randint(1, 9999):04d}")


def date(rng):
    return f"{rng.randint(1, 28):02d}/{rng.randint(1, 12):02d}/{rng.randint(2018, 2025)}"


TEMPLATES = {
    "certidao_transito_julgado": [
        "CERTIDÃO. Certifico, para os devidos fins, que a sentença proferida nos autos do processo {num} transitou em julgado em {date}, sem interposição de recurso pelas partes.",
        "Certidão de trânsito em julgado. Certifico que o acórdão de fls. transitou em julgado em {date}. Nada mais. {court}.",
        "CERTIFICO E DOU FÉ que decorreu o prazo legal sem manifestação das partes, tendo a decisão transitado em julgado na data de {date}.",
        "Certifico o trânsito em julgado da sentença em {date}. Os autos seguem conclusos para início do cumprimento de sentença.",
        "Certidão. Em cumprimento ao despacho, certifico que o v. acórdão transitou em julgado para ambas as partes em {date}.",
        "TRÂNSITO EM JULGADO. Certifico que a decisão proferida em favor de {plaintiff} transitou em julgado, conforme consulta ao sistema em {date}.",
    ],
    "sentenca": [
        "SENTENÇA. Trata-se de ação ajuizada por {plaintiff} em face de {defendant}, objetivando {subject}. É o relatório. Decido. Ante o exposto, JULGO PROCEDENTE o pedido e condeno o réu ao pagamento das parcelas vencidas. Após o trânsito em julgado, arquivem-se.",
        "Vistos. {plaintiff} propôs a presente ação contra {defendant} pleiteando {subject}. Fundamentação. Diante do exposto, julgo parcialmente procedente o pedido, resolvendo o mérito nos termos do art. 487, I, do CPC.",
        "SENTENÇA TIPO A. Relatório dispensado. Passo a decidir. O conjunto probatório demonstra o direito da parte autora a {subject}. Dispositivo: JULGO PROCEDENTE o pedido. Condeno o réu em honorários advocatícios de 10% sobre o valor da condenação.",
        "Ante o exposto, JULGO IMPROCEDENTE o pedido formulado por {plaintiff}, extinguindo o processo com resolução do mérito. Sem custas. Sentença registrada eletronicamente.",
        "Sentença. A parte autora, {plaintiff}, requer {subject}. Presentes os requisitos legais, acolho o pedido. Julgo procedente e condeno {defendant} a implantar o benefício e pagar os atrasados corrigidos.",
        "Dispositivo. Pelo exposto, resolvo o mérito e JULGO PROCEDENTES os pedidos para condenar {defendant} ao pagamento de {money}, com correção monetária e juros de mora.",
    ],
    "acordao": [
        "ACÓRDÃO. Vistos, relatados e discutidos estes autos, acordam os Desembargadores da Turma, por unanimidade, NEGAR PROVIMENTO à apelação de {defendant}, nos termos do voto do Relator.",
        "EMENTA: PREVIDENCIÁRIO. {subject}. Apelação desprovida. ACÓRDÃO: A Turma, por unanimidade, negou provimento ao recurso, mantendo a sentença.",
        "Acórdão. A Primeira Turma Recursal, por maioria, deu parcial provimento ao recurso inominado interposto por {defendant}, nos termos do voto do juiz relator.",
        "ACORDAM os integrantes da Câmara, à unanimidade, em conhecer e dar provimento ao recurso de {plaintiff}. Relator: Des. {judge}.",
        "Recurso de apelação. Voto do relator acolhido. A Turma decidiu, por unanimidade, manter a condenação de {defendant} quanto a {subject}. Acórdão publicado em {date}.",
    ],
    "calculos": [
        "PLANILHA DE CÁLCULOS. Exequente: {plaintiff}. Executado: {defendant}. Principal corrigido: {money}. Juros de mora: {money2}. Total geral atualizado até {date}: {money3}.",
        "Memória de cálculo. Parcelas vencidas de {date} a {date2}. Índice de correção: IPCA-E. Valor total da condenação: {money3}. Honorários sucumbenciais: {money2}.",
        "Demonstrativo de débito judicial. Competência / valor devido / correção / juros. Total devido: {money3}. Cálculo elaborado pela contadoria judicial.",
        "CÁLCULOS DE LIQUIDAÇÃO. Valor principal {money} acrescido de juros de {money2}, totalizando {money3}. Atualizado em {date}.",
        "Planilha de atualização do débito. Base de cálculo conforme sentença. Valor atualizado: {money3}. Honorários advocatícios contratuais de 30%: {money2}.",
        "Contadoria Judicial. Apuramos o montante de {money3} devido a {plaintiff}, já incluídos correção monetária e juros, posicionado em {date}.",
    ],
    "substabelecimento": [
        "SUBSTABELECIMENTO. Pelo presente instrumento, substabeleço, COM RESERVA DE IGUAIS PODERES, ao Dr. {lawyer}, OAB nº {oab}, os poderes que me foram conferidos por {plaintiff}.",
        "Substabelecimento sem reserva de poderes. Eu, {lawyer2}, advogado, substabeleço SEM RESERVA DE PODERES ao Dr. {lawyer}, OAB {oab}, os poderes outorgados por {plaintiff}.",
        "Substabeleço, com reservas, ao colega {lawyer}, inscrito na OAB sob nº {oab}, para atuar nos autos do processo {num}.",
        "Instrumento de substabelecimento. O advogado {lawyer2} transfere ao Dr. {lawyer}, sem reserva, todos os poderes da procuração outorgada por {plaintiff}.",
        "SUBSTABELECIMENTO. Fica substabelecido, com reserva de iguais poderes, o mandato conferido por {plaintiff}, em favor de {lawyer}.",
    ],
    "certidao_obito": [
        "CERTIDÃO DE ÓBITO. Certifico que no livro de registros consta o óbito de {plaintiff}, ocorrido em {date}, na cidade de {city}. Causa da morte: insuficiência cardíaca.",
        "Registro Civil das Pessoas Naturais. Certidão de óbito de {plaintiff}. Data do falecimento: {date}. Declarante: {person}.",
        "Óbito. Nome do falecido: {plaintiff}. Data: {date}. Local: hospital municipal de {city}. Sepultamento no cemitério local.",
        "Certidão de óbito. Faleceu em {date} o(a) Sr(a). {plaintiff}, deixando filhos maiores. Registro feito por {person}.",
        "Cartório de Registro Civil de {city}. Certifico o falecimento de {plaintiff} em {date}, conforme declaração médica anexa.",
    ],
    "procuracao": [
        "PROCURAÇÃO AD JUDICIA. Outorgante: {plaintiff}. Outorgado: Dr. {lawyer}, OAB {oab}. Poderes para o foro em geral, podendo receber e dar quitação.",
        "Procuração. Por este instrumento particular, {plaintiff} nomeia e constitui seu procurador o advogado {lawyer}, com poderes da cláusula ad judicia et extra.",
        "Instrumento de mandato. O outorgante {plaintiff} confere ao Dr. {lawyer} poderes para propor ação contra {defendant}, transigir, desistir e receber valores.",
        "PROCURAÇÃO. Outorgo ao advogado {lawyer}, inscrito na OAB sob nº {oab}, amplos poderes para representar-me em juízo em ação referente a {subject}.",
        "Mandato judicial. {plaintiff}, residente em {city}, constitui como procurador {lawyer}, com poderes especiais para firmar acordo e levantar alvarás.",
    ],
    "peticao": [
        "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DA {court}. {plaintiff}, por seu advogado, vem propor AÇÃO em face de {defendant}, pelos fatos e fundamentos a seguir expostos, requerendo {subject}.",
        "Petição. {plaintiff}, já qualificada nos autos, vem requerer a juntada da planilha de cálculos e o início do cumprimento de sentença, após o trânsito em julgado.",
        "Requerimento. A parte autora requer a expedição de requisição de pequeno valor (RPV) em seu favor, conforme cálculos homologados.",
        "MM. Juiz, {plaintiff} vem informar a juntada de substabelecimento e requerer que as intimações sejam feitas em nome do Dr. {lawyer}.",
        "Petição intermediária. A exequente manifesta concordância com os cálculos apresentados por {defendant} e requer a homologação.",
        "Manifestação. A parte autora informa que não há notícia de óbito e requer o prosseguimento do feito, com a expedição do precatório.",
    ],
    "despacho": [
        "DESPACHO. Intime-se a parte autora para, no prazo de 15 dias, apresentar planilha de cálculos atualizada. Cumpra-se.",
        "Vistos. Certifique a secretaria o trânsito em julgado. Após, intime-se o executado nos termos do art. 535 do CPC.",
        "Despacho. Defiro o pedido de justiça gratuita. Cite-se {defendant} para contestar no prazo legal.",
        "Considerando a juntada do substabelecimento, anote-se o nome do novo procurador. Após, conclusos.",
        "Decisão interlocutória. Indefiro, por ora, o pedido de tutela de urgência. Intimem-se.",
        "Despacho. Manifestem-se as partes sobre os cálculos da contadoria no prazo comum de 10 dias.",
    ],
}


def fill(template, rng):
    return template.format(
        num=case_number(rng), date=date(rng), date2=date(rng), court=rng.choice(COURTS).upper(),
        plaintiff=person(rng), person=person(rng), defendant=rng.choice(DEFENDANTS),
        subject=rng.choice(SUBJECTS), money=money(rng), money2=money(rng, 100, 20000),
        money3=money(rng, 500, 250000), judge=person(rng), lawyer=person(rng), lawyer2=person(rng),
        oab=f"{rng.choice(['MT', 'SP', 'CE', 'PE', 'RS', 'MG'])} {rng.randint(1000, 99999)}",
        city=rng.choice(["Cuiabá", "Sobral", "Recife", "São Paulo", "Porto Alegre", "Sorriso"]),
    )


def add_noise(text, rng, rate):
    chars = list(text)
    for i in range(len(chars)):
        roll = rng.random()
        if roll < rate / 3:
            chars[i] = ""
        elif roll < 2 * rate / 3 and chars[i].isalpha():
            chars[i] = rng.choice("aeioulrnst")
        elif roll < rate:
            chars[i] = chars[i] + " "
    return "".join(chars)


def build_text(label, template_id, rng):
    parts = []
    if rng.random() < 0.6:
        parts.append(rng.choice(HEADERS))
    if rng.random() < 0.5:
        parts.append(f"Processo nº {case_number(rng)}")
    parts.append(fill(TEMPLATES[label][template_id], rng))
    if rng.random() < 0.5:
        parts.append(rng.choice(FOOTERS))
    text = " ".join(parts)
    if rng.random() < 0.35:
        text = add_noise(text, rng, rate=rng.uniform(0.01, 0.04))
    if rng.random() < 0.15:
        text = text[: max(60, int(len(text) * rng.uniform(0.5, 0.9)))]
    return text


def generate(per_class: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for label, templates in TEMPLATES.items():
        for i in range(per_class):
            template_id = i % len(templates)
            rows.append({
                "label": label,
                "template": f"{label}#{template_id}",
                "text": build_text(label, template_id, rng),
            })
    rng.shuffle(rows)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-class", type=int, default=150)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "documents.csv")
    args = parser.parse_args()

    rows = generate(args.per_class, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["label", "template", "text"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} documents written to {args.output}")


if __name__ == "__main__":
    main()
