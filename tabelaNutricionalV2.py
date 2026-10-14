"""Calculadora nutricional baseada na TACO 4a edicao.

- Base com 597 alimentos da Tabela 1 da TACO.
- Os valores nutricionais da TACO sao por 100 g de parte comestivel.
- O programa usa UMA LISTA para cada informacao, conforme o exercicio.
- NPU/proteina liquida = proteina consumida * fator de utilizacao proteica.

Fatores usados no exercicio:
    animal  = 0.7  (70%)
    vegetal = 0.5  (50%)
    cereal  = 0.4  (40%)

Importante: 0.7, 0.5 e 0.4 sao fatores/proporcoes, nao gramas.
Exemplo: 10 g de proteina animal x 0.7 = 7 g de proteina liquida.

Observacao importante:
A classificacao de NPU para alimentos mistos/preparados e uma aproximacao
para fins didaticos. A TACO nao fornece NPU pronto.
"""

import csv
import os
import re
import unicodedata
from difflib import SequenceMatcher


NPU_FATORES = {
    "animal": 0.7,
    "vegetal": 0.5,
    "cereal": 0.4,
}

# O CSV deve ficar na mesma pasta deste arquivo .py
ARQUIVO_DADOS = os.path.join(os.path.dirname(__file__), "alimentos_taco_597.csv")


# ---------------------------------------------------------------------
# LISTAS PEDIDAS NO EXERCICIO
# ---------------------------------------------------------------------
alimento = []
carb = []
proteina = []
lip = []
sodio = []
npu = []
qtd = []

# Listas extras para deixar o programa mais completo.
grupo = []
energia = []
fibra = []
calcio = []
ferro = []
magnesio = []
potassio = []
categoria = []


# Registra os alimentos realmente escolhidos pelo usuario.
itens_escolhidos = []


def normalizar(texto):
    """Remove acentos e pontuacao para facilitar a busca."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caractere for caractere in texto
        if not unicodedata.combining(caractere)
    )
    return re.sub(r"[^a-z0-9]+", " ", texto.lower()).strip()


def numero(valor):
    """Converte os valores da TACO em float.

    Tr = traco/quantidade muito pequena -> 0 para esta calculadora.
    NA, vazio e * = sem valor utilizavel -> 0 para esta calculadora.
    """
    valor = str(valor).strip()
    if valor in {"", "NA", "Tr", "*"}:
        return 0.0

    # Remove letras de notas da tabela, como 18b ou 20a.
    valor = re.sub(r"(?<=\d)[a-zA-Z]+$", "", valor)
    valor = valor.replace(",", ".")

    try:
        return float(valor)
    except ValueError:
        return 0.0


def carregar_dados():
    """Le o CSV e preenche uma lista para cada informacao."""
    if not os.path.exists(ARQUIVO_DADOS):
        raise FileNotFoundError(
            "Nao encontrei 'alimentos_taco_597.csv'. "
            "Deixe o CSV na mesma pasta do programa."
        )

    with open(ARQUIVO_DADOS, encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)

        for linha in leitor:
            alimento.append(linha["alimento"])
            carb.append(numero(linha["carboidratos_g"]))
            proteina.append(numero(linha["proteina_g"]))
            lip.append(numero(linha["lipideos_g"]))
            sodio.append(numero(linha["sodio_mg"]))

            categoria_alimento = linha["categoria_npu"]
            categoria.append(categoria_alimento)
            npu.append(NPU_FATORES[categoria_alimento])

            grupo.append(linha["grupo"])
            energia.append(numero(linha["energia_kcal"]))
            fibra.append(numero(linha["fibra_g"]))
            calcio.append(numero(linha["calcio_mg"]))
            ferro.append(numero(linha["ferro_mg"]))
            magnesio.append(numero(linha["magnesio_mg"]))
            potassio.append(numero(linha["potassio_mg"]))


carregar_dados()

# Indice para busca exata sem acentos.
_INDICE_ALIMENTOS = {
    normalizar(nome): indice
    for indice, nome in enumerate(alimento)
}


def _palavras_uteis(texto):
    """Remove palavras que quase nao ajudam a identificar o alimento."""
    ignorar = {
        "de", "da", "do", "das", "dos", "com", "sem", "em", "para",
        "e", "a", "o", "as", "os"
    }
    return [p for p in normalizar(texto).split() if p not in ignorar]


def _pontuar_busca(texto, nome):
    """Da uma nota de relevancia para um alimento em relacao a busca."""
    busca = normalizar(texto)
    alvo = normalizar(nome)

    if not busca:
        return 0.0
    if busca == alvo:
        return 1000.0

    palavras_busca = _palavras_uteis(busca)
    palavras_alvo = _palavras_uteis(alvo)
    conjunto_alvo = set(palavras_alvo)

    if not palavras_busca:
        return 0.0

    score = 0.0
    acertadas = 0

    for palavra in palavras_busca:
        if palavra in conjunto_alvo:
            score += 18
            acertadas += 1
        elif any(p.startswith(palavra) or palavra.startswith(p) for p in palavras_alvo):
            score += 12
            acertadas += 1
        else:
            melhor = max(
                (SequenceMatcher(None, palavra, p, autojunk=False).ratio() for p in palavras_alvo),
                default=0.0
            )
            if melhor >= 0.72:
                score += melhor * 8
                acertadas += 1

    # Favorece nomes que contenham todas as palavras importantes digitadas.
    if acertadas == len(palavras_busca):
        score += 25

    # Favorece a ordem/frase parecida e penaliza nomes enormes quando a busca e curta.
    score += SequenceMatcher(None, busca, alvo, autojunk=False).ratio() * 20
    score -= max(0, len(palavras_alvo) - len(palavras_busca)) * 0.7

    # Se nenhuma palavra bateu de forma razoavel, nao vale mostrar.
    if acertadas == 0:
        return 0.0

    return score


def buscar_alimentos(texto, limite=12):
    """Busca inteligente: ignora conectivos, aceita abreviacoes e pequenos erros."""
    busca = normalizar(texto)
    if not busca:
        return []

    if busca in _INDICE_ALIMENTOS:
        return [_INDICE_ALIMENTOS[busca]]

    candidatos = []
    for indice, nome in enumerate(alimento):
        score = _pontuar_busca(texto, nome)
        if score >= 24:
            candidatos.append((score, indice))

    candidatos.sort(key=lambda item: item[0], reverse=True)
    return [indice for _, indice in candidatos[:limite]]


def localizar_alimento(nome):
    """Localiza um alimento e permite escolher uma opcao pelo numero."""
    encontrados = buscar_alimentos(nome)

    if len(encontrados) == 1:
        return encontrados[0]

    if len(encontrados) == 0:
        raise ValueError(f"Alimento nao encontrado: {nome}")

    print("\nEncontrei estas opcoes (mais provaveis primeiro):")
    for numero_opcao, indice in enumerate(encontrados, start=1):
        print(f"{numero_opcao:2}. {alimento[indice]}")

    while True:
        escolha = input("Escolha o numero (0 cancela): ").strip()
        if escolha == "0":
            raise ValueError("Busca cancelada")
        if escolha.isdigit():
            numero_escolhido = int(escolha)
            if 1 <= numero_escolhido <= len(encontrados):
                return encontrados[numero_escolhido - 1]
        print("Opcao invalida. Digite um numero da lista.")

def adicionar_item(nome, quantidade):
    """Adiciona um alimento e sua quantidade em gramas."""
    if quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")

    indice = localizar_alimento(nome)

    # qtd e uma lista separada, como pedido no exercicio.
    qtd.append(quantidade)
    itens_escolhidos.append(indice)

    return indice


def calcular_totais():
    """Soma carboidrato, proteina, lipideos, NPU e sodio."""
    total_carb = 0.0
    total_proteina = 0.0
    total_lip = 0.0
    total_npu = 0.0
    total_sodio = 0.0

    detalhes = []

    for posicao in range(len(itens_escolhidos)):
        indice = itens_escolhidos[posicao]
        quantidade = qtd[posicao]
        fator_quantidade = quantidade / 100.0

        carb_consumido = carb[indice] * fator_quantidade
        proteina_consumida = proteina[indice] * fator_quantidade
        lip_consumido = lip[indice] * fator_quantidade
        sodio_consumido = sodio[indice] * fator_quantidade

        # CORRECAO PRINCIPAL:
        # NPU/proteina liquida: aplica-se o fator de utilizacao sobre
        # a quantidade de proteina realmente consumida na porcao.
        # Ex.: 1.66 g de proteina de cereal x 0.4 = 0.664 g.
        npu_consumido = proteina_consumida * npu[indice]

        total_carb += carb_consumido
        total_proteina += proteina_consumida
        total_lip += lip_consumido
        total_npu += npu_consumido
        total_sodio += sodio_consumido

        detalhes.append({
            "alimento": alimento[indice],
            "quantidade": quantidade,
            "categoria": categoria[indice],
            "fator_npu": npu[indice],
            "carb": carb_consumido,
            "proteina": proteina_consumida,
            "lip": lip_consumido,
            "npu": npu_consumido,
            "sodio": sodio_consumido,
        })

    totais = {
        "carb": total_carb,
        "proteina": total_proteina,
        "lip": total_lip,
        "npu": total_npu,
        "sodio": total_sodio,
    }

    return totais, detalhes


def mostrar_alimento(indice):
    """Mostra informacoes extras disponiveis para 100 g do alimento."""
    print(f"\n{alimento[indice]} - valores por 100 g")
    print(f"Grupo:         {grupo[indice]}")
    print(f"Categoria NPU: {categoria[indice]} ({npu[indice]:.1f})")
    print(f"Energia:       {energia[indice]:.1f} kcal")
    print(f"Carboidratos:  {carb[indice]:.1f} g")
    print(f"Proteinas:     {proteina[indice]:.1f} g")
    print(f"Lipideos:      {lip[indice]:.1f} g")
    print(f"Fibra:         {fibra[indice]:.1f} g")
    print(f"Sodio:         {sodio[indice]:.1f} mg")
    print(f"Potassio:      {potassio[indice]:.1f} mg")
    print(f"Calcio:        {calcio[indice]:.1f} mg")
    print(f"Ferro:         {ferro[indice]:.1f} mg")
    print(f"Magnesio:      {magnesio[indice]:.1f} mg")


def imprimir_resultado(totais, detalhes):
    print("\n" + "=" * 62)
    print("ITENS INFORMADOS")
    print("=" * 62)

    for item in detalhes:
        print(f"\n- {item['alimento']}: {item['quantidade']:g} g")
        print(
            f"  Carb: {item['carb']:.2f} g | "
            f"Prot: {item['proteina']:.2f} g | "
            f"Lip: {item['lip']:.2f} g"
        )
        print(
            f"  Fator NPU: {item['fator_npu']:.2f} "
            f"({item['fator_npu'] * 100:.0f}% - {item['categoria']})"
        )
        print(
            f"  Proteina liquida (NPU aplicado): "
            f"{item['proteina']:.2f} x {item['fator_npu']:.2f} = "
            f"{item['npu']:.2f} g | Sodio: {item['sodio']:.2f} mg"
        )

    print("\n" + "=" * 62)
    print("TOTAL")
    print("=" * 62)
    print(f"Carboidratos: {totais['carb']:.2f} g")
    print(f"Proteinas:    {totais['proteina']:.2f} g")
    print(f"Lipideos:     {totais['lip']:.2f} g")
    print(f"Proteina liquida (NPU): {totais['npu']:.2f} g")
    if totais["proteina"] > 0:
        npu_medio = totais["npu"] / totais["proteina"]
        print(f"Fator NPU medio:          {npu_medio:.2f} ({npu_medio * 100:.1f}%)")
    print(f"Sodio:        {totais['sodio']:.2f} mg")


def main():
    print("Calculadora nutricional - TACO 4a edicao")
    print(f"Base carregada: {len(alimento)} alimentos.")
    print("Valores da TACO por 100 g.")
    print("Digite 'fim' para calcular ou 'info' para consultar um alimento.\n")

    while True:
        nome = input("Alimento: ").strip()

        if normalizar(nome) in {"fim", "sair", "quit"}:
            break

        if normalizar(nome) == "info":
            consulta = input("Nome para consultar: ").strip()
            try:
                indice = localizar_alimento(consulta)
                mostrar_alimento(indice)
            except ValueError as erro:
                print(f"Erro: {erro}")
            print()
            continue

        try:
            # Primeiro resolve qual alimento e. So depois pergunta a quantidade.
            indice = localizar_alimento(nome)
            quantidade = float(input("Quantidade (g): ").replace(",", "."))
            if quantidade <= 0:
                raise ValueError("A quantidade deve ser maior que zero.")

            qtd.append(quantidade)
            itens_escolhidos.append(indice)
            print(f"Adicionado: {alimento[indice]} ({quantidade:g} g)\n")
        except ValueError as erro:
            print(f"Erro: {erro}")
            print()

    if not itens_escolhidos:
        print("Nenhum alimento informado.")
        return

    totais, detalhes = calcular_totais()
    imprimir_resultado(totais, detalhes)

    print("\nFonte dos dados nutricionais: TACO 4a edicao, NEPA/UNICAMP (2011).")
    print("NPU: proteina da porcao x fator de utilizacao proteica.")
    print("Os fatores 0.7, 0.5 e 0.4 equivalem a 70%, 50% e 40%.")
    print("Para alimentos mistos/preparados, a categoria continua sendo uma aproximacao didatica.")


if __name__ == "__main__":
    main()
