# Organização do Pyobliqua

- `src/pyobliqua/secao`: geometria, barras e seções.
- `src/pyobliqua/materiais`: modelos constitutivos.
- `src/pyobliqua/analise`: deformações, esforços, integração, equilíbrio, verificação e interação.
- `src/pyobliqua/visualizacao`: gráficos Matplotlib.
- `src/pyobliqua/interface`: interface Tkinter.
- `examples/casos_dad`: arquivos de entrada `.dad` originais.
- `docs/apresentacao`: apresentação Marp original e recursos.
- `tests`: testes automatizados de regressão dos exemplos 5.1 e 5.2.
- `scripts`: geração de executável Windows.

A reorganização alterou apenas caminhos de importação e a localização do logotipo. A formulação matemática foi preservada.

O arquivo `src/pyobliqua/main.py` continua sendo o módulo de demonstração em linha de comando. O arquivo `src/pyobliqua/__main__.py` abre a interface.
