#!/usr/bin/env python3
"""
Capa do perfil: foto virada em arte ASCII colorida, ao lado de um painel
estilo neofetch. Saida em PNG, que e o formato que o GitHub renderiza
sem depender de servico de terceiro.

uso: python3 .assets/gerar-capa.py <foto.jpg> [saida.png]
"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTE_NEGRITO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

FUNDO = (13, 17, 23)          # mesmo tom do GitHub no escuro
TEXTO = (201, 209, 217)
APAGADO = (110, 118, 129)
DESTAQUE = (88, 166, 255)
TITULO = (210, 168, 255)
VERDE = (63, 185, 80)

# do mais escuro ao mais claro; o fundo e escuro, entao brilho alto = glifo cheio
RAMPA = " .:-=+*#%@"

# Foto precisa de bem mais celulas que um logo para continuar reconhecivel.
COLUNAS = 121
LINHAS = 104
CORPO = 13                     # altura da fonte do painel
CELULA_L, CELULA_A = 3, 5      # tamanho da celula da arte
FONTE_ARTE = 5


def virar_ascii(caminho: str, recorte=None):
    """Devolve uma grade de (caractere, cor) amostrada da foto."""
    img = Image.open(caminho).convert("RGB")

    if recorte:
        img = img.crop(recorte)
    else:
        l, a = img.size
        lado = min(l, a)
        img = img.crop(((l - lado) // 2, (a - lado) // 2, (l + lado) // 2, (a + lado) // 2))

    # sem esticar o contraste, ceu e agua viram uma mancha unica de cinza
    img = ImageOps.autocontrast(img, cutoff=2)

    # o caractere e mais alto que largo, entao a grade compensa a proporcao
    pequena = img.resize((COLUNAS, LINHAS), Image.LANCZOS)

    grade = []
    for y in range(LINHAS):
        linha = []
        for x in range(COLUNAS):
            r, g, b = pequena.getpixel((x, y))
            brilho = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255

            # O sujeito e escuro contra vela e ceu claros. Sem inverter, a vela
            # vira um bloco solido e a pessoa desaparece.
            densidade = (1 - brilho) ** 1.3
            glifo = RAMPA[min(int(densidade * len(RAMPA)), len(RAMPA) - 1)]

            # Levanta a exposicao sem normalizar pixel a pixel: normalizar
            # amplifica ruido nos escuros e a foto vira neon.
            cor = tuple(min(255, int(((c / 255) ** 0.50) * 255 * 1.35)) for c in (r, g, b))

            linha.append((glifo, cor))
        grade.append(linha)
    return grade


def montar(foto: str, saida: str, linhas_painel, recorte=None):
    global COLUNAS, LINHAS
    if recorte:
        # altura da arte fixa; a largura sai da proporcao do recorte
        l, a = recorte[2] - recorte[0], recorte[3] - recorte[1]
        COLUNAS = int(LINHAS / ((a / l) * (CELULA_L / CELULA_A)))
    arte = virar_ascii(foto, recorte)

    margem = 26
    largura_arte = COLUNAS * CELULA_L
    largura_painel = 600
    L = margem * 2 + largura_arte + 30 + largura_painel
    A = margem * 2 + max(LINHAS * CELULA_A, len(linhas_painel) * 18)

    tela = Image.new("RGB", (L, A), FUNDO)
    d = ImageDraw.Draw(tela)
    mono = ImageFont.truetype(FONTE, FONTE_ARTE)
    painel = ImageFont.truetype(FONTE, CORPO)
    painel_negrito = ImageFont.truetype(FONTE_NEGRITO, CORPO)

    # arte, caractere a caractere para manter a cor de cada celula
    for y, linha in enumerate(arte):
        for x, (glifo, cor) in enumerate(linha):
            if glifo != " ":
                d.text((margem + x * CELULA_L, margem + y * CELULA_A), glifo, font=mono, fill=cor)

    # painel, centralizado na vertical contra a arte
    px = margem + largura_arte + 34
    py = margem + max(0, (LINHAS * CELULA_A - len(linhas_painel) * 18) // 2)
    for tipo, esquerda, direita in linhas_painel:
        if tipo == "titulo":
            d.text((px, py), esquerda, font=painel_negrito, fill=VERDE)
            traco = "-" * max(0, (largura_painel - len(esquerda) * 8 - 10) // 8)
            d.text((px + len(esquerda) * 8 + 8, py), traco, font=painel, fill=APAGADO)
        elif tipo == "secao":
            d.text((px, py), "- " + esquerda + " ", font=painel_negrito, fill=TITULO)
            traco = "-" * max(0, (largura_painel - (len(esquerda) + 3) * 8) // 8)
            d.text((px + (len(esquerda) + 3) * 8, py), traco, font=painel, fill=APAGADO)
        elif tipo == "vazio":
            pass
        else:
            d.text((px, py), ".", font=painel, fill=APAGADO)
            d.text((px + 14, py), esquerda, font=painel_negrito, fill=DESTAQUE)
            # pontilhado ligando rotulo e valor, como no neofetch
            inicio = px + 14 + len(esquerda) * 8 + 6
            fim = px + largura_painel - len(direita) * 8 - 6
            if fim > inicio:
                d.text((inicio, py), "." * ((fim - inicio) // 8), font=painel, fill=(48, 54, 61))
            d.text((px + largura_painel - len(direita) * 8, py), direita, font=painel, fill=TEXTO)
        py += 18

    tela.save(saida)
    print(f"{saida}  {L}x{A}")


PAINEL = [
    ("titulo", "patric@meetpatric", ""),
    ("linha", "OS:", "Ubuntu 24.04 LTS"),
    ("linha", "Editor:", "VS Code"),
    ("linha", "Role:", "Back-End Software Engineer"),
    ("linha", "Company:", "IGMA  ·  Worda"),
    ("linha", "Education:", "B.Sc. Software Engineering"),
    ("linha", "Certifications:", "Meta Back-End  ·  Meta Front-End"),
    ("vazio", "", ""),
    ("linha", "Languages.Server:", "Python, PHP, Node.js"),
    ("linha", "Languages.Client:", "TypeScript, React, React Native"),
    ("linha", "Languages.Spoken:", "Portuguese (native), English (C1)"),
    ("vazio", "", ""),
    ("linha", "Focus.Backend:", "APIs, DDD, Integrations"),
    ("linha", "Focus.Automation:", "RPA, Data Pipelines"),
    ("linha", "Focus.AI:", "LLM Applications"),
    ("vazio", "", ""),
    ("secao", "Contact", ""),
    ("linha", "Portfolio:", "meetpatric.dev"),
    ("linha", "Email:", "patricsilva4cs@gmail.com"),
    ("linha", "GitHub:", "github.com/cspatric"),
]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("uso: gerar-capa.py <foto.jpg> [saida.png]")
    # recorte em volta da pessoa; o centro da foto e so vela e agua
    RECORTE = (900, 170, 1480, 1000)
    montar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ".assets/capa.png", PAINEL, RECORTE)
