# Pyobliqua

**Dimensionamento e verificação de seções de concreto armado submetidas à flexão composta oblíqua.**

O **Pyobliqua** é um programa desenvolvido em Python para aplicações acadêmicas, com duas formas de utilização: **interface gráfica** e **scripts Python**.

## Funcionalidades

- Dimensionamento da área de armadura de seções poligonais de concreto armado.
- Verificação de seções com armadura conhecida.
- Seções com contornos poligonais, furos e barras de aço.
- Visualização da seção, linha neutra, deformações e tensões.
- Representação do diagrama de interação **Mx–My**.

## 1. Abrir a interface gráfica

Com o projeto configurado no ambiente Python, abra um terminal na pasta do projeto e execute:

```powershell
python -m pyobliqua
```

Na interface, selecione **Dimensionamento** ou **Verificação**, informe a geometria, os materiais, as armaduras e os esforços solicitantes e execute o cálculo. É possível visualizar os resultados e os diagramas e trabalhar com arquivos `.dad`.

## 2. Utilizar por script Python

O projeto inclui o arquivo `src/pyobliqua/main.py`, com dois exemplos de utilização do núcleo de cálculo:

- **Exemplo 5.1 — Dimensionamento:** seção quadrada vazada de 85 × 85 cm.
- **Exemplo 5.2 — Verificação:** seção poligonal com armadura conhecida.

Para executar os exemplos, utilize:

```powershell
python -m pyobliqua.main
```

O script calcula os resultados e apresenta gráficos das seções e dos estados de deformação e tensão.

### Criar seus próprios scripts

O pacote também disponibiliza uma API para utilizar os cálculos em outros programas:

```python
from pyobliqua import Modelo, Unidades

modelo = Modelo(
    Unidades(forca="kN", momento="kN.m", tensao="MPa")
)

# Defina a seção e os materiais conforme os exemplos do projeto.
# Em seguida, utilize:
# resultado = modelo.dimensionar(secao, concreto, aco, Nsd, Msdx, Msdy)
# resultado = modelo.verificar(secao, concreto, aco, As=As, Nsd=Nsd, Msdx=Msdx, Msdy=Msdy)
```

Para consultar a construção completa da geometria, a definição dos materiais e a interpretação dos resultados, veja **`src/pyobliqua/main.py`**.

## 3. Estrutura principal

```text
Pyobliqua/
├── README.md
├── pyproject.toml
├── src/
│   └── pyobliqua/
│       ├── __main__.py       # Inicialização da interface
│       ├── main.py           # Exemplos de cálculo por script
│       ├── api.py            # API Python
│       ├── analise/
│       ├── materiais/
│       ├── secao/
│       ├── interface/
│       └── visualizacao/
└── tests/
```

## Referência

A metodologia de cálculo tem como referência os trabalhos de **Américo Campos Filho** sobre dimensionamento de seções de concreto armado à flexão composta oblíqua.

## Autoria e uso

**Felipe Quevedo** — desenvolvimento do Pyobliqua.

O programa destina-se ao **ensino e à pesquisa**. Os resultados devem ser verificados independentemente e não substituem as normas técnicas aplicáveis. Consulte o arquivo [LICENSE](LICENSE) para as condições de uso.

> As instruções para instalação do programa no Windows serão acrescentadas quando o instalador com **Inno Setup** estiver disponível.
