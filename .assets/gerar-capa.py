#!/usr/bin/env python3
"""
Capa do perfil: foto virada em arte ASCII colorida, ao lado de um painel
estilo neofetch. Saida em PNG, que e o formato que o GitHub renderiza
sem depender de servico de terceiro.

uso: python3 .assets/gerar-capa.py <foto.jpg> [saida.png]
"""
import sys
import json
import urllib.request

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTE_NEGRITO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

FUNDO = (13, 17, 23)          # mesmo tom do GitHub no escuro
TEXTO = (201, 209, 217)
APAGADO = (110, 118, 129)
DESTAQUE = (88, 166, 255)
TITULO = (210, 168, 255)
VERDE = (63, 185, 80)

# do mais escuro ao mais claro; o fundo e escuro, entao brilho alto = glifo cheio
RAMPA = " .+#@"

# Foto precisa de bem mais celulas que um logo para continuar reconhecivel.
# Menos colunas = caractere maior. Abaixo de ~70 a figura deixa de ser
# reconhecivel: fotografia nao sobrevive em baixa resolucao como um logo.
COLUNAS = 32
LINHAS = 30
CORPO = 13                     # altura da fonte do painel
CELULA_L, CELULA_A = 12, 20    # tamanho da celula da arte
FONTE_ARTE = 20

# Abaixo deste ponto a celula vira fundo vazio. E o que separa a figura do
# ceu e da agua; sem isso, caractere grande vira mancha.
CORTE = 0.50


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
    img = ImageOps.autocontrast(img, cutoff=1)

    # Com celula grande sobra pouca resolucao; suavizar antes de reduzir tira
    # o chiado das ondas, que senao disputa atencao com a figura.
    img = img.filter(ImageFilter.GaussianBlur(10))


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
            escuro = 1 - brilho
            densidade = 0.0 if escuro < CORTE else (escuro - CORTE) / (1 - CORTE)
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
        # A arte tem a mesma altura do painel; a largura sai da proporcao do
        # recorte, para nao esticar a foto.
        l, a = recorte[2] - recorte[0], recorte[3] - recorte[1]
        LINHAS = round(len(linhas_painel) * 18 / CELULA_A)
        COLUNAS = round(LINHAS / ((a / l) * (CELULA_L / CELULA_A)))
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
    py = margem
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


def buscar_stats():
    """
    Numeros do GitHub na hora de gerar, para o cartao nao envelhecer.
    Sem rede, cai nos ultimos valores conhecidos.
    """
    conhecidos = {"repos": 2, "seguidores": 5, "stars": 0, "commits": 123, "loc": 37115}
    try:
        def pega(url, cabecalho=None):
            req = urllib.request.Request(url, headers=cabecalho or {"User-Agent": "capa"})
            return json.load(urllib.request.urlopen(req, timeout=15))

        u = pega("https://api.github.com/users/cspatric")
        repos = pega("https://api.github.com/users/cspatric/repos?per_page=100")
        commits = pega(
            "https://api.github.com/search/commits?q=author:cspatric&per_page=1",
            {"User-Agent": "capa", "Accept": "application/vnd.github.cloak-preview+json"},
        )
        return {
            "repos": u["public_repos"],
            "seguidores": u["followers"],
            "stars": sum(r.get("stargazers_count", 0) for r in repos),
            "commits": commits.get("total_count", conhecidos["commits"]),
            "loc": conhecidos["loc"],  # contado clonando os repos; nao vem da API
        }
    except Exception:
        return conhecidos


def montar_painel():
    g = buscar_stats()
    return [
        ("titulo", "patric@meetpatric", ""),
        ("linha", "OS:", "Ubuntu 24.04 LTS"),
        ("linha", "Editor:", "VS Code"),
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
        ("linha", "Portfolio.Link:", "meetpatric.dev"),
        ("linha", "Email.Work:", "patricsilva4cs@gmail.com"),
        ("linha", "GitHub:", "github.com/cspatric"),
        ("vazio", "", ""),
        ("secao", "GitHub Stats", ""),
        ("linha", "Repos:", f"{g['repos']}   |   Stars:  {g['stars']}"),
        ("linha", "Commits:", f"{g['commits']}   |   Followers:  {g['seguidores']}"),
        ("linha", "GitHub LOC:", f"{g['loc']:,}"),
    ]


PAINEL_ANTIGO = [
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
    RECORTE = (950, 195, 1450, 775)
    montar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ".assets/capa.png", montar_painel(), RECORTE)
