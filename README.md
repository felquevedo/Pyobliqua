# Pyobliqua

**Análise de seções poligonais de concreto armado à flexão composta oblíqua — projeto acadêmico em Python.**

O Pyobliqua é um programa desenvolvido para fins de **ensino, estudo e pesquisa**. Permite estudar o comportamento resistente de seções poligonais de concreto armado submetidas à força normal e a momentos fletores em duas direções.

> **Aviso importante:** o Pyobliqua não é autorizado para dimensionamento ou verificação de estruturas em projetos profissionais. Os resultados devem ser conferidos de forma independente e não substituem a aplicação das normas técnicas vigentes. O programa é fornecido sem garantia, nos limites da legislação aplicável. Consulte o arquivo [LICENSE](LICENSE).

## Funcionalidades

- **Dimensionamento:** determinação da área total de armadura necessária para esforços normais e momentos fletores prescritos.
- **Verificação:** avaliação de uma seção com armadura definida, incluindo o fator de reserva de resistência (λ).
- **Geometria:** seções poligonais, incluindo contornos com furos, e posicionamento individual das barras.
- **Visualização:** representação da seção, da linha neutra e de diagramas de deformação e tensão.
- **Diagrama Mx–My:** cálculo e apresentação de estados resistentes para força normal constante e armadura conhecida ou dimensionada, com indicação dos momentos solicitantes.
- **Uso por código:** execução dos exemplos 5.1 e 5.2 sem a interface gráfica.

**Atenção:** a curva Mx–My é obtida numericamente por amostragem de orientações da linha neutra. Sua representação gráfica e a interpolação radial não substituem a verificação numérica completa, nem garantem a identificação de todos os ramos resistentes em situações gerais.

## Organização do projeto

O código-fonte fica em `src/pyobliqua/`, separado em `analise`, `materiais`, `secao`, `visualizacao` e `interface`. Os casos `.dad` estão em `examples/casos_dad/`; a apresentação Marp, em `docs/apresentacao/`. Veja [docs/ORGANIZACAO.md](docs/ORGANIZACAO.md).

## Requisitos

- Python 3.10 ou superior (recomendado).
- Bibliotecas Python: `numpy`, `scipy` e `matplotlib`.
- `tkinter` para a interface gráfica (normalmente incluído na instalação do Python para Windows).

Instale as dependências na pasta do projeto:

```bash
python -m pip install -e .
```

## Execução

### Interface gráfica

```bash
python -m pyobliqua
```

Na interface, selecione **Dimensionamento** ou **Verificação**, informe a geometria, as armaduras, os materiais e os esforços. O diagrama **Mx–My** pode ser habilitado por uma caixa de seleção nos dois modos. No dimensionamento, o diagrama usa a área de aço calculada; na verificação, usa a área de aço informada.

### Exemplos pelo terminal

```bash
python -m pyobliqua.main                 # Exemplos 5.1 e 5.2
python -m pyobliqua.main --exemplo 5.1   # Dimensionamento
python -m pyobliqua.main --exemplo 5.2   # Verificação
python -m pyobliqua.main --diagrama      # Exemplos com diagrama Mx–My
```

O **exemplo 5.1** demonstra o dimensionamento de uma seção vazada de 85 × 85 cm com 20 barras. O **exemplo 5.2** demonstra a verificação de uma seção assimétrica com 15 barras e área total de aço de 30 cm². Ambos são casos de estudo associados à referência acadêmica indicada abaixo.

### Convenções de unidades

Os módulos de cálculo trabalham internamente com **N, mm, N·mm, mm² e MPa**. A interface pode apresentar dados em **kN, kN·m, cm, cm² e cm⁴**. Observe as conversões ao usar diretamente as funções Python.

## Referência técnica

CAMPOS FILHO, Américo. *Dimensionamento de seções poligonais de concreto armado à flexão composta oblíqua*. Apostila, Universidade Federal do Rio Grande do Sul (UFRGS), 2000.

O programa foi desenvolvido com base em conceitos e procedimentos apresentados nessa apostila. A referência é anterior às versões atuais das normas de concreto; **não se deve presumir conformidade automática com a ABNT NBR 6118 vigente**.

A referência à UFRGS identifica o contexto acadêmico da obra utilizada e **não implica homologação ou garantia institucional do software**.

## Licença e condições de uso

O código-fonte é disponibilizado para **consulta e uso acadêmico não comercial**, sob as condições do arquivo [LICENSE](LICENSE). São permitidos estudos e modificações privadas; redistribuição de versões modificadas e usos comerciais exigem autorização prévia do titular.

**Este projeto não é distribuído sob uma licença de software livre ou open source**, pois contém restrições de finalidade e redistribuição.

## Autoria

**Felipe Quevedo** — desenvolvimento do Pyobliqua.

© 2026 Felipe Quevedo. Todos os direitos reservados.

## Testes e distribuição

Instale os extras de teste e execute:

```powershell
python -m pip install -e ".[test]"
python -m pytest
```

No Windows, execute `scripts\gerar_executavel.bat` para gerar `dist\Pyobliqua.exe` com PyInstaller. O ponto de entrada da interface é `src/pyobliqua/__main__.py`; o PyInstaller utiliza `scripts/entrypoint.py`. O executável deve ser testado em Windows.

**Nota:** os testes automatizados incluídos verificam a preservação dos resultados dos exemplos 5.1 e 5.2; não constituem validação numérica independente.
