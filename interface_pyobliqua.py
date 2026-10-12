"""Interface gráfica do Pyobliqua (Tkinter + Matplotlib).

Execute na raiz do projeto: python interface_pyobliqua.py
Dependências: numpy, scipy, matplotlib; tkinter da instalação Python.
Unidades de entrada: cm, MPa, kN, kN.m e cm².
Internamente os módulos de cálculo continuam usando mm e mm².
"""
import json
import webbrowser
from pathlib import Path
import math
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.ticker import FuncFormatter
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from secao.secao import Secao
from secao.barra import Barra
from materiais.concreto import Concreto
from materiais.aco import Aco
from analise.estado_deformacao import EstadoDeformacao
from analise.esforcos import esforcos_resistentes
from analise.equilibrio import resolver_equilibrio
from analise.verificacao import resolver_verificacao
from visualizacao.desenho_secao import desenhar_secao
from analise.interacao import calcular_diagrama_interacao, estimar_aproveitamento_radial
from visualizacao.diagrama_interacao import desenhar_diagrama_interacao


def numero(texto, descricao):
    """Converte texto numérico para um valor real finito.

    Args:
        texto: Texto ou valor conversível para float; aceita vírgula decimal.
        descricao (str): Identificação do campo para mensagens de erro.

    Returns:
        float: Número convertido.

    Raises:
        ValueError: Se o valor não for numérico ou finito.
    
    """
    try:
        valor = float(str(texto).strip().replace(',', '.'))
    except (ValueError, TypeError) as exc:
        raise ValueError(f'{descricao}: informe um número válido.') from exc
    if not math.isfinite(valor):
        raise ValueError(f'{descricao}: o valor deve ser finito.')
    return valor


class Tabela(ttk.Frame):
    """Widget de tabela editável baseado em ttk.Treeview.

    Permite adicionar, excluir e ler linhas. A edição de uma célula é
    iniciada por duplo clique; Enter confirma e Escape cancela.

    Attributes:
        colunas: Identificadores das colunas.
        grade: Treeview usado para exibir os dados.
    
    """
    def __init__(self, master, colunas, larguras=None, altura=7):
        """Inicializa a tabela e seus controles.
    
            Args:
                master: Widget Tkinter pai.
                colunas: Sequência de nomes das colunas.
                larguras (list[int] | None): Larguras das colunas em pixels.
                altura (int): Número de linhas visíveis.
            
        """
        super().__init__(master)
        self.colunas = colunas
        self.grade = ttk.Treeview(self, columns=colunas, show='headings', height=altura,
                                  selectmode='extended')
        for i, nome in enumerate(colunas):
            self.grade.heading(nome, text=nome)
            self.grade.column(nome, width=(larguras[i] if larguras else 100), anchor='center')
        scroll = ttk.Scrollbar(self, orient='vertical', command=self.grade.yview)
        self.grade.configure(yscrollcommand=scroll.set)
        self.grade.grid(row=0, column=0, sticky='nsew')
        scroll.grid(row=0, column=1, sticky='ns')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        botoes = ttk.Frame(self)
        botoes.grid(row=1, column=0, columnspan=2, sticky='w', pady=3)
        ttk.Button(botoes, text='+ Linha', command=self.adicionar).pack(side='left', padx=2)
        ttk.Button(botoes, text='− Excluir', command=self.excluir).pack(side='left', padx=2)
        self.grade.bind('<Double-1>', self.editar)
        self._editor = None

    def adicionar(self, valores=None):
        """Adiciona uma linha ao final da tabela.
    
            Args:
                valores (sequence | None): Valores das células; se omitido,
                    cria uma linha vazia.
            
        """
        self.grade.insert('', 'end', values=valores or [''] * len(self.colunas))

    def excluir(self):
        """Exclui as linhas atualmente selecionadas.
        """
        for item in self.grade.selection():
            self.grade.delete(item)

    def limpar(self):
        """Remove todas as linhas da tabela.
        """
        for item in self.grade.get_children():
            self.grade.delete(item)

    def linhas(self):
        """Obtém os valores de todas as linhas na ordem exibida.
    
            Returns:
                list[list[str]]: Conteúdo das células como textos.
            
        """
        return [list(self.grade.item(i, 'values')) for i in self.grade.get_children()]

    def editar(self, evento):
        """Abre um editor temporário sobre a célula clicada.
    
            Args:
                evento: Evento de duplo clique do Tkinter.
            
        """
        item = self.grade.identify_row(evento.y)
        coluna = self.grade.identify_column(evento.x)
        if not item or not coluna:
            return
        indice = int(coluna[1:]) - 1
        if indice < 0 or indice >= len(self.colunas):
            return
        x, y, w, h = self.grade.bbox(item, coluna)
        if self._editor is not None:
            self._editor.destroy()
        entrada = ttk.Entry(self.grade)
        entrada.insert(0, self.grade.set(item, self.colunas[indice]))
        entrada.place(x=x, y=y, width=w, height=h)
        entrada.focus_set()
        entrada.select_range(0, 'end')
        self._editor = entrada

        def fechar(gravar=True):
            if self._editor is not entrada:
                return
            if gravar:
                self.grade.set(item, self.colunas[indice], entrada.get())
            self._editor = None
            entrada.destroy()

        entrada.bind('<Return>', lambda e: fechar())
        entrada.bind('<FocusOut>', lambda e: fechar())
        entrada.bind('<Escape>', lambda e: fechar(False))


def desenhar_diagramas_deformacoes_tensoes(ax, secao, estado, concreto):
    """Diagramas ao lado da seção, com eixo longitudinal normal à linha neutra.

    O diagrama de tensões representa somente o concreto (tração desprezada).
    Deformações negativas indicam compressão. Não modifica o cálculo.
    """
    import numpy as np
    from math import sin, cos

    alfa = estado.alfa
    n = np.array([-sin(alfa), cos(alfa)])  # direção eta: normal à LN
    t = np.array([cos(alfa), sin(alfa)])   # direção paralela à LN
    pontos = np.array([(v.x, v.y) for v in secao.contorno.vertices], dtype=float)
    origem = np.array([secao.xc, secao.yc], dtype=float)
    proj_t = (pontos - origem) @ t
    proj_n = (pontos - origem) @ n
    eta_min, eta_max = float(min(proj_n)), float(max(proj_n))
    dim = max(np.ptp(pontos[:, 0]), np.ptp(pontos[:, 1]), 1.0)
    h = eta_max - eta_min
    etas = np.linspace(eta_min, eta_max, 180)
    deformacoes = np.array([estado.deformacao(float(eta)) for eta in etas])
    # Limite de precisão numérica próximo ao patamar de -3,5‰.
    tensoes = np.array([concreto.tensao(max(float(eps), -0.0035)) for eps in deformacoes])

    def plotar_diagrama(indice, valores, cor, nome, unidade):
        # Baselines paralelas à normal da LN; valores plotados paralelos à LN.
        deslocamento = max(proj_t) + (0.27 + 0.69 * indice) * dim
        base = origem + np.outer(etas, n) + deslocamento * t
        maximo = max(float(np.max(np.abs(valores))), 1e-12)
        amplitude = 0.43 * dim
        perfil = base + np.outer(-valores / maximo * amplitude, t)
        ax.plot(base[:, 0], base[:, 1], color='#64748b', lw=1.1, ls='--', zorder=13)
        ax.plot(perfil[:, 0], perfil[:, 1], color=cor, lw=2, zorder=14)
        ax.fill(np.r_[base[:, 0], perfil[::-1, 0]],
                np.r_[base[:, 1], perfil[::-1, 1]], color=cor, alpha=.14, zorder=12)
        for eta, valor in ((etas[0], valores[0]), (etas[-1], valores[-1])):
            ponto = origem + eta * n + (deslocamento - valor / maximo * amplitude) * t
            ax.annotate(f'{valor:+.2f} {unidade}', xy=ponto, xytext=(4, 4),
                        textcoords='offset points', fontsize=7, color=cor, zorder=15)
        cabecalho = origem + (eta_max + .13 * max(h, dim)) * n + deslocamento * t
        ax.text(*cabecalho, nome, fontsize=9, color=cor, fontweight='bold',
                ha='center', va='center', zorder=15)
        return np.vstack([base, perfil, cabecalho])

    # Destaca as deformações das armaduras extremas no perfil linear.
    etas_barras = [(np.array([b.posicao.x, b.posicao.y]) - origem) @ n
                   for b in secao.barras]
    if etas_barras:
        for titulo_barra, eta_barra, marcador in (
            ('Armadura superior', max(etas_barras), 'o'),
            ('Armadura inferior', min(etas_barras), 's'),
        ):
            eps_barra = estado.deformacao(float(eta_barra)) * 1000
            max_eps = max(float(np.max(np.abs(deformacoes * 1000))), 1e-12)
            deslocamento = max(proj_t) + .27 * dim
            ponto = origem + eta_barra * n + (deslocamento - eps_barra / max_eps * .43 * dim) * t
            ax.scatter([ponto[0]], [ponto[1]], marker=marcador, s=45,
                       facecolor='white', edgecolor='#14532d', linewidth=1.6, zorder=20)
            ax.annotate(f'{titulo_barra}: {eps_barra:+.3f} ‰', xy=ponto,
                        xytext=(8, -12 if marcador == 'o' else 12),
                        textcoords='offset points', fontsize=8, color='#14532d', zorder=21,
                        bbox=dict(facecolor='white', alpha=.82, edgecolor='none', pad=1))

    pts_eps = plotar_diagrama(0, deformacoes * 1000, '#15803d', 'Deformações', '‰')
    pts_sig = plotar_diagrama(1, tensoes, '#b91c1c', 'Tensões no concreto', 'MPa')
    conjunto = np.vstack([pontos, pts_eps, pts_sig])
    borda = .16 * dim
    ax.set_xlim(min(conjunto[:, 0]) - borda, max(conjunto[:, 0]) + borda)
    ax.set_ylim(min(conjunto[:, 1]) - borda, max(conjunto[:, 1]) + borda)


class Interface(tk.Tk):
    """Janela principal da aplicação Pyobliqua.

    Reúne entrada de materiais, solicitações, geometria e armaduras,
    dimensionamento, verificação e visualização Matplotlib embutida.
    As rotinas de cálculo são executadas em thread auxiliar; a atualização
    da interface é agendada por ``after``.
    
    """
    def __init__(self):
        """Inicializa a janela, o estado da interface e o exemplo 5.1.
        """
        super().__init__()
        self.title('Pyobliqua — Dimensionamento e verificação de seções')
        self.geometry('1450x850')
        self.minsize(1100, 670)
        self.modo = tk.StringVar(value='dimensionamento')
        self.campos = {}
        self._ocupado = False
        self.mostrar_diagramas = tk.BooleanVar(value=True)
        self.mostrar_interacao = tk.BooleanVar(value=False)
        self._ultimo = None
        self._ultimo_interacao = None
        self._montar()
        self._montar_menu()
        self.carregar_exemplo_51()

    def _montar_menu(self):
        """Acrescenta a barra de menus sem alterar os painéis existentes."""
        menu_principal = tk.Menu(self)
        menu_arquivo = tk.Menu(menu_principal, tearoff=False)
        menu_arquivo.add_command(label='Novo', command=self.novo_arquivo)
        menu_arquivo.add_command(label='Abrir', command=self.abrir_dados)
        menu_arquivo.add_command(label='Salvar', command=self.salvar_dados)
        menu_arquivo.add_separator()
        menu_arquivo.add_command(label='Fechar', command=self.fechar_programa)
        menu_principal.add_cascade(label='Arquivo', menu=menu_arquivo)

        menu_principal.add_command(label='Sobre', command=self.mostrar_sobre)
        self.config(menu=menu_principal)
        self.protocol('WM_DELETE_WINDOW', self.fechar_programa)

    def _entradas_atuais(self):
        """Obtém somente os dados digitados, sem resultados ou gráficos.

        Returns:
            dict: Modo, campos de entrada e linhas das três tabelas.
        """
        return {
            'formato': 'Pyobliqua-DAD',
            'versao': 1,
            'unidades_geometria': 'cm',
            'modo': self.modo.get(),
            'mostrar_interacao': self.mostrar_interacao.get(),
            'campos': {nome: var.get() for nome, var in self.campos.items()},
            'contorno': self.contorno.linhas(),
            'furos': self.furos.linhas(),
            'barras': self.barras.linhas(),
        }

    def _aplicar_entradas(self, dados):
        """Preenche os controles com entradas previamente verificadas."""
        self.modo.set('verificacao' if dados['modo'] == 'interacao' else dados['modo'])
        self.mostrar_interacao.set(bool(dados.get('mostrar_interacao', dados['modo'] == 'interacao')))
        self.atualizar_modo()
        self._definir(**dados['campos'])
        # Arquivos antigos .dad (sem marcador) armazenavam mm e mm².
        # Converte apenas na leitura; novos arquivos são salvos em cm e cm².
        antigo = dados.get('unidades_geometria', 'mm') == 'mm'
        def adaptar(linhas, indices, indice_area=None):
            if not antigo:
                return linhas
            saida = []
            for linha in linhas:
                nova = list(linha)
                for i in indices:
                    nova[i] = f'{numero(nova[i], "coordenada") / 10:.12g}'
                if indice_area is not None:
                    nova[indice_area] = f'{numero(nova[indice_area], "área") / 100:.12g}'
                saida.append(nova)
            return saida
        self._preencher(self.contorno, adaptar(dados['contorno'], (0, 1)))
        self._preencher(self.furos, adaptar(dados['furos'], (1, 2)))
        self._preencher(self.barras, adaptar(dados['barras'], (0, 1),
                        2 if dados['modo'] != 'dimensionamento' else None))
        self._ultimo = None
        self._ultimo_interacao = None
        self.eixo_figura.clear()
        self.canvas_figura.draw_idle()
        self._escrever('Dados de entrada carregados. Execute o cálculo para obter resultados.\n')

    @staticmethod
    def _validar_arquivo_dad(dados):
        """Confere a estrutura do arquivo antes de modificar a interface."""
        if not isinstance(dados, dict) or dados.get('formato') != 'Pyobliqua-DAD' or dados.get('versao') != 1:
            raise ValueError('Arquivo .dad incompatível com o formato do Pyobliqua.')
        if dados.get('modo') not in ('dimensionamento', 'verificacao', 'interacao'):
            raise ValueError('Modo de análise inválido no arquivo.')
        if dados.get('unidades_geometria', 'mm') not in ('mm', 'cm'):
            raise ValueError('Unidades geométricas inválidas no arquivo.')
        campos = dados.get('campos')
        esperados = {'fck (MPa)', 'fyk (MPa)', 'Es (MPa)', 'γc', 'γs',
                     'Nad (kN)', 'Maxd (kN·m)', 'Mayd (kN·m)'}
        if not isinstance(campos, dict) or set(campos) != esperados or not all(isinstance(v, str) for v in campos.values()):
            raise ValueError('Campos de entrada inválidos no arquivo.')
        for nome, quantidade in (('contorno', 2), ('furos', 3), ('barras', 3)):
            linhas = dados.get(nome)
            if not isinstance(linhas, list) or not all(
                isinstance(linha, list) and len(linha) == quantidade
                and all(isinstance(v, str) for v in linha)
                for linha in linhas
            ):
                raise ValueError(f'Tabela {nome} inválida no arquivo.')

    def novo_arquivo(self):
        """Limpa somente os dados de entrada para iniciar outro projeto."""
        if self._ocupado:
            messagebox.showwarning('Cálculo em andamento', 'Aguarde o término do cálculo.')
            return
        if not messagebox.askyesno('Novo', 'Limpar os dados atuais e iniciar um novo projeto?'):
            return
        self.modo.set('dimensionamento')
        self.atualizar_modo()
        for var in self.campos.values():
            var.set('')
        for tabela in (self.contorno, self.furos, self.barras):
            tabela.limpar()
        self._ultimo = None
        self._ultimo_interacao = None
        self.eixo_figura.clear()
        self.canvas_figura.draw_idle()
        self._escrever('Novo projeto. Preencha os dados de entrada.\n')
        self.status.set('Pronto.')

    def salvar_dados(self):
        """Salva exclusivamente as entradas em arquivo de texto .dad (UTF-8)."""
        if self._ocupado:
            messagebox.showwarning('Cálculo em andamento', 'Aguarde o término do cálculo.')
            return
        caminho = filedialog.asksaveasfilename(
            title='Salvar dados de entrada', defaultextension='.dad',
            filetypes=[('Dados do Pyobliqua', '*.dad')])
        if not caminho:
            return
        try:
            with open(caminho, 'w', encoding='utf-8') as arquivo:
                json.dump(self._entradas_atuais(), arquivo, ensure_ascii=False, indent=2)
                arquivo.write('\n')
        except OSError as exc:
            messagebox.showerror('Erro ao salvar', str(exc))
            return
        self.status.set('Dados de entrada salvos.')

    def abrir_dados(self):
        """Abre um .dad e restaura apenas os campos e tabelas de entrada."""
        if self._ocupado:
            messagebox.showwarning('Cálculo em andamento', 'Aguarde o término do cálculo.')
            return
        caminho = filedialog.askopenfilename(
            title='Abrir dados de entrada',
            filetypes=[('Dados do Pyobliqua', '*.dad')])
        if not caminho:
            return
        try:
            with open(caminho, 'r', encoding='utf-8') as arquivo:
                dados = json.load(arquivo)
            self._validar_arquivo_dad(dados)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            messagebox.showerror('Erro ao abrir', str(exc))
            return
        self._aplicar_entradas(dados)
        self.status.set('Dados de entrada carregados.')

    def fechar_programa(self):
        """Fecha a janela principal, sem alterar os dados salvos."""
        if self._ocupado:
            messagebox.showwarning('Cálculo em andamento', 'Aguarde o término do cálculo.')
            return
        self.destroy()

    def mostrar_sobre(self):
        """Exibe informações, logotipo e aviso acadêmico somente para leitura."""
        if getattr(self, '_janela_sobre', None) is not None:
            try:
                if self._janela_sobre.winfo_exists():
                    self._janela_sobre.lift()
                    self._janela_sobre.focus_set()
                    return
            except tk.TclError:
                pass

        janela = tk.Toplevel(self)
        self._janela_sobre = janela
        janela.title('Sobre')
        janela.resizable(False, False)
        janela.transient(self)
        janela.geometry('760x430')

        conteudo = ttk.Frame(janela, padding=20)
        conteudo.pack(fill='both', expand=True)
        principal = ttk.Frame(conteudo)
        principal.pack(fill='both', expand=True)

        espaco_logo = ttk.Frame(principal, width=220, height=250,
                                relief='groove', borderwidth=1)
        espaco_logo.pack(side='left', fill='y', padx=(0, 20))
        espaco_logo.pack_propagate(False)
        caminho_logo = Path(__file__).resolve().parent / 'logo_ufrgs.png'
        try:
            imagem = tk.PhotoImage(file=str(caminho_logo))
            fator = max(1, math.ceil(imagem.width() / 200),
                        math.ceil(imagem.height() / 220))
            if fator > 1:
                imagem = imagem.subsample(fator, fator)
            rotulo_logo = ttk.Label(espaco_logo, image=imagem)
            rotulo_logo.image = imagem
            rotulo_logo.pack(expand=True)
        except (tk.TclError, OSError):
            ttk.Label(espaco_logo, text='Logo da UFRGS',
                      anchor='center', justify='center',
                      wraplength=180).pack(fill='both', expand=True)

        informacoes = ttk.Frame(principal)
        informacoes.pack(side='left', fill='both', expand=True)
        ttk.Label(informacoes, text='Pyobliqua',
                  font=('Arial', 16, 'bold')).pack(anchor='w', pady=(0, 8))
        ttk.Label(informacoes, text='Versão 2026.1').pack(anchor='w', pady=2)
        ttk.Label(informacoes, text='Desenvolvedor: Prof. Felipe Quevedo').pack(anchor='w', pady=2)

        email = 'motta.quevedo@ufrgs.br'
        link = tk.Label(informacoes, text=f'Email: {email}', fg='#155eaa',
                        cursor='hand2', font=('Arial', 10, 'underline'))
        link.pack(anchor='w', pady=(2, 12))
        link.bind('<Button-1>', lambda evento: webbrowser.open(f'mailto:{email}'))

        ttk.Label(informacoes, text='Mensagem:').pack(anchor='w')
        aviso = (
            'O Pyobliqua foi desenvolvido com base na apostila '
            '“Dimensionamento de Seções Poligonais de Concreto Armado à '
            'Flexão Composta Oblíqua”, de Américo Campos Filho (UFRGS, 2000).\n\n'
            'O software destina-se exclusivamente ao uso acadêmico, didático '
            'e de pesquisa. Seus resultados não substituem a análise crítica '
            'por profissional habilitado nem a aplicação das normas técnicas '
            'vigentes.\n\n'
            'O desenvolvedor não se responsabiliza por decisões de projeto, '
            'erros, danos ou prejuízos decorrentes da utilização do programa '
            'ou de seus resultados.'
        )
        self.mensagem_sobre = tk.Text(
            informacoes, height=10, wrap='word', font=('Arial', 10),
            relief='flat', background=janela.cget('background'),
            padx=2, pady=2, cursor='arrow', takefocus=0,
        )
        self.mensagem_sobre.insert('1.0', aviso)
        self.mensagem_sobre.configure(state='disabled')
        self.mensagem_sobre.pack(fill='both', expand=True, pady=(4, 0))

        ttk.Button(conteudo, text='Fechar', command=janela.destroy).pack(
            anchor='e', pady=(14, 0))
        janela.focus_set()

    def _campo(self, parent, rotulo, valor, linha, coluna, largura=12):
        """Cria um campo rotulado e armazena sua StringVar.
    
            Args:
                parent: Widget pai.
                rotulo (str): Identificador do campo.
                valor: Valor inicial exibido.
                linha (int): Linha da grade.
                coluna (int): Posição lógica do par rótulo/campo.
                largura (int): Largura da entrada em caracteres.
    
            Returns:
                tk.StringVar: Variável associada ao campo.
            
        """
        ttk.Label(parent, text=rotulo).grid(row=linha, column=coluna * 2, sticky='w', padx=(8, 2), pady=4)
        var = tk.StringVar(value=str(valor))
        ttk.Entry(parent, textvariable=var, width=largura).grid(
            row=linha, column=coluna * 2 + 1, sticky='ew', padx=(0, 9), pady=4)
        self.campos[rotulo] = var
        return var

    def _montar(self):
        """Constrói os painéis, controles, tabelas e gráfico incorporado.
        """
        estilo = ttk.Style(self)
        if 'clam' in estilo.theme_names():
            estilo.theme_use('clam')
        corpo = ttk.Frame(self, padding=8)
        corpo.pack(fill='both', expand=True)

        cabecalho = ttk.Frame(corpo)
        cabecalho.pack(fill='x')
        ttk.Label(cabecalho, text='Pyobliqua', font=('Arial', 17, 'bold')).pack(side='left')
        ttk.Label(cabecalho, text='cm | MPa | kN | kN·m | cm²').pack(side='left', padx=12)
        ttk.Button(cabecalho, text='Carregar exemplo 5.1', command=self.carregar_exemplo_51).pack(side='right', padx=3)
        ttk.Button(cabecalho, text='Carregar exemplo 5.2', command=self.carregar_exemplo_52).pack(side='right', padx=3)

        superior = ttk.Frame(corpo)
        superior.pack(fill='x', pady=(5, 5))
        modo_frame = ttk.LabelFrame(superior, text='Tipo de análise', padding=4)
        modo_frame.pack(side='left', fill='y', padx=(0, 6))
        ttk.Radiobutton(modo_frame, text='Dimensionamento', variable=self.modo,
                        value='dimensionamento', command=self.atualizar_modo).pack(side='left', padx=5)
        ttk.Radiobutton(modo_frame, text='Verificação', variable=self.modo,
                        value='verificacao', command=self.atualizar_modo).pack(side='left', padx=5)
        dados = ttk.LabelFrame(superior, text='Materiais e esforços solicitantes', padding=3)
        dados.pack(side='left', fill='both', expand=True)
        for i, (rotulo, valor) in enumerate([
            ('fck (MPa)', 20), ('fyk (MPa)', 500), ('Es (MPa)', 210000),
            ('γc', 1.4), ('γs', 1.15), ('Nad (kN)', -200),
            ('Maxd (kN·m)', -500), ('Mayd (kN·m)', 500),
        ]):
            self._campo(dados, rotulo, valor, i // 4, i % 4, largura=10)
        for i in range(8):
            dados.columnconfigure(i, weight=1)

        # Painéis lado a lado, ambos filhos do MESMO PanedWindow.
        # A figura nunca é aberta em uma janela independente.
        paineis = ttk.Panedwindow(corpo, orient='horizontal')
        paineis.pack(fill='both', expand=True)
        esquerdo = ttk.Frame(paineis)
        direito = ttk.Frame(paineis)
        paineis.add(esquerdo, weight=1)
        paineis.add(direito, weight=2)

        tabelas = ttk.Notebook(esquerdo)
        tabelas.pack(fill='both', expand=True)
        cont = ttk.Frame(tabelas, padding=4)
        fur = ttk.Frame(tabelas, padding=4)
        arm = ttk.Frame(tabelas, padding=4)
        tabelas.add(cont, text='Contorno externo')
        tabelas.add(fur, text='Furos')
        tabelas.add(arm, text='Armadura')
        self.contorno = Tabela(cont, ('x (cm)', 'y (cm)'), altura=12)
        self.contorno.pack(fill='both', expand=True)
        ttk.Label(cont, text='Não repita o primeiro vértice.', foreground='#555').pack(anchor='w')
        self.furos = Tabela(fur, ('Furo nº', 'x (cm)', 'y (cm)'), altura=12,
                           larguras=[65, 100, 100])
        self.furos.pack(fill='both', expand=True)
        ttk.Label(fur, text='Use o mesmo número para os vértices de um furo.',
                  foreground='#555').pack(anchor='w')
        self.barras = Tabela(arm, ('x (cm)', 'y (cm)', 'ρ ou As'), altura=12,
                            larguras=[95, 95, 100])
        self.barras.pack(fill='both', expand=True)
        self.aviso_barras = ttk.Label(arm, text='', foreground='#555')
        self.aviso_barras.pack(anchor='w')

        acoes = ttk.Frame(esquerdo)
        acoes.pack(fill='x', pady=5)
        self.botao_calcular = ttk.Button(acoes, text='Calcular e desenhar', command=self.calcular)
        self.botao_calcular.pack(side='left', padx=2)
        ttk.Button(acoes, text='Visualizar seção', command=self.visualizar).pack(side='left', padx=2)
        ttk.Button(acoes, text='Salvar imagem...', command=self.salvar_imagem).pack(side='left', padx=2)
        ttk.Checkbutton(acoes, text='Exibir diagramas', variable=self.mostrar_diagramas,
                        command=self._atualizar_diagramas).pack(side='left', padx=(10, 2))
        ttk.Checkbutton(acoes, text='Diagrama Mx–My', variable=self.mostrar_interacao,
                        command=self._alternar_interacao).pack(side='left', padx=(10, 2))
        resultado = ttk.LabelFrame(esquerdo, text='Resultados', padding=4)
        resultado.pack(fill='both', expand=False)
        self.saida = tk.Text(resultado, height=16, wrap='word', font=('Consolas', 9))
        scroll_resultados = ttk.Scrollbar(resultado, orient='vertical', command=self.saida.yview)
        self.saida.configure(yscrollcommand=scroll_resultados.set)
        self.saida.pack(side='left', fill='both', expand=True)
        scroll_resultados.pack(side='right', fill='y')
        self.status = tk.StringVar(value='Pronto.')
        ttk.Label(esquerdo, textvariable=self.status).pack(anchor='w', pady=3)

        grafico = ttk.LabelFrame(direito, text='Visualização da seção transversal', padding=4)
        grafico.pack(fill='both', expand=True)
        self.figura = Figure(figsize=(7, 6), dpi=100)
        self.eixo_figura = self.figura.add_subplot(111)
        self.canvas_figura = FigureCanvasTkAgg(self.figura, master=grafico)
        self.canvas_figura.get_tk_widget().pack(fill='both', expand=True)
        barra = ttk.Frame(grafico)
        barra.pack(fill='x')
        self.toolbar = NavigationToolbar2Tk(self.canvas_figura, barra, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side='left', fill='x')
        self.atualizar_modo()
        self.after(150, lambda: paineis.sashpos(0, max(420, int(paineis.winfo_width()*0.42))))

    def atualizar_modo(self):
        """Atualiza a instrução sobre áreas conforme o modo selecionado.
    
            No dimensionamento, a última coluna das barras contém proporções
            cuja soma deve ser 1. Na verificação, contém áreas individuais em mm².
            
        """
        if self.modo.get() == 'dimensionamento':
            self.aviso_barras.configure(text='ρ = fração da área total; soma das proporções = 1.')
        else:
            self.aviso_barras.configure(text='As individual de cada barra, em cm².')

    def _definir(self, **kwargs):
        """Atribui valores aos campos identificados pelos seus rótulos.
    
            Args:
                **kwargs: Mapeamento de rótulos para valores.
            
        """
        for k, v in kwargs.items():
            self.campos[k].set(str(v))

    def _preencher(self, tabela, linhas):
        """Substitui o conteúdo de uma tabela por linhas fornecidas.
    
            Args:
                tabela (Tabela): Widget a atualizar.
                linhas: Sequência de linhas.
            
        """
        tabela.limpar()
        for linha in linhas:
            tabela.adicionar(linha)

    def carregar_exemplo_51(self):
        """Carrega o exemplo 5.1 no modo dimensionamento.
    
            Preenche seção vazada, vinte barras com proporções de área,
            materiais e esforços solicitantes.
            
        """
        self.modo.set('dimensionamento')
        self.atualizar_modo()
        self._definir(**{'fck (MPa)': 20, 'fyk (MPa)': 500, 'Es (MPa)': 210000,
                         'γc': 1.4, 'γs': 1.15, 'Nad (kN)': -200,
                         'Maxd (kN·m)': -500, 'Mayd (kN·m)': 500})
        self._preencher(self.contorno, [(0, 0), (85, 0), (85, 85), (0, 85)])
        self._preencher(self.furos, [(1, 30, 30), (1, 55, 30), (1, 55, 55), (1, 30, 55)])
        coords = [(5,5),(20,5),(35,5),(50,5),(65,5),(80,5),
                  (5,20),(5,35),(5,50),(5,65),(5,80),
                  (80,20),(80,35),(80,50),(80,65),(80,80),
                  (20,80),(35,80),(50,80),(65,80)]
        self._preencher(self.barras, [(x,y,0.05) for x,y in coords])
        self._escrever('Exemplo 5.1 carregado: dimensionamento, 20 barras, seção vazada.\n')

    def carregar_exemplo_52(self):
        """Carrega o exemplo 5.2 no modo verificação.
    
            Preenche seção poligonal e armaduras com áreas individuais.
            
        """
        self.modo.set('verificacao')
        self.atualizar_modo()
        self._definir(**{'fck (MPa)': 20, 'fyk (MPa)': 500, 'Es (MPa)': 210000,
                         'γc': 1.4, 'γs': 1.15, 'Nad (kN)': 0,
                         'Maxd (kN·m)': -1000, 'Mayd (kN·m)': 0})
        vertices = [(22.5,0),(47.5,0),(47.5,10),(42.5,15),(42.5,95),
                    (70,110),(70,120),(0,120),(0,110),(27.5,95),
                    (27.5,15),(22.5,10)]
        coords = [(27.5,5),(32.5,5),(37.5,5),(42.5,5),
                  (27.5,8),(32.5,8),(37.5,8),(42.5,8),
                  (32.5,11),(37.5,11),
                  (5,115),(20,115),(35,115),(50,115),(65,115)]
        self._preencher(self.contorno, [(x,y) for x,y in vertices])
        self.furos.limpar()
        self._preencher(self.barras, [(x,y,2) for x,y in coords])
        self._escrever('Exemplo 5.2 carregado: verificação, As total = 30 cm².\n')

    def _escrever(self, texto):
        """Substitui o texto do painel de resultados.
    
            Args:
                texto (str): Mensagem a exibir.
            
        """
        self.saida.delete('1.0', 'end')
        self.saida.insert('end', texto)

    def _ler_linhas(self, tabela, n, nome):
        """Lê e valida as linhas preenchidas de uma tabela.
    
            Args:
                tabela (Tabela): Tabela de origem.
                n (int): Quantidade esperada de colunas.
                nome (str): Nome da tabela para mensagens de erro.
    
            Returns:
                list[list[float]]: Linhas completas convertidas para números.
    
            Raises:
                ValueError: Se uma linha estiver incompleta ou contiver
                    valores não numéricos.
            
        """
        linhas = []
        for i, linha in enumerate(tabela.linhas(), 1):
            if not any(str(v).strip() for v in linha):
                continue
            if len(linha) != n or any(not str(v).strip() for v in linha):
                raise ValueError(f'{nome}, linha {i}: preencha todas as colunas.')
            linhas.append([numero(v, f'{nome}, linha {i}') for v in linha])
        return linhas

    def _dados(self):
        """Valida os campos e constrói os objetos da análise.
    
            Converte solicitações de kN e kN·m para N e N·mm. No modo
            dimensionamento, as barras usam proporções; na verificação,
            suas áreas individuais são convertidas em proporções da área total.
    
            Returns:
                tuple: ``(secao, concreto, aco, esforcos, As, modo)``, onde
                ``esforcos`` é ``(N, Mx, My)`` em N e N·mm, ``As`` está em
                mm² ou é None no dimensionamento, e ``modo`` é uma string.
    
            Raises:
                ValueError: Se materiais, vértices, furos, barras ou
                    proporções de armadura forem inválidos.
            
        """
        valores = {k: numero(v.get(), k) for k,v in self.campos.items()}
        for chave in ('fck (MPa)', 'fyk (MPa)', 'Es (MPa)', 'γc', 'γs'):
            if valores[chave] <= 0:
                raise ValueError(f'{chave} deve ser positivo.')
        contorno = self._ler_linhas(self.contorno, 2, 'Contorno')
        contorno = [[10*x, 10*y] for x, y in contorno]  # cm -> mm
        if len(contorno) < 3:
            raise ValueError('O contorno deve ter pelo menos três vértices.')
        furos = {}
        for i, linha in enumerate(self._ler_linhas(self.furos, 3, 'Furos'), 1):
            numero_furo, x, y = linha
            if numero_furo <= 0 or not numero_furo.is_integer():
                raise ValueError(f'Furos, linha {i}: número do furo deve ser inteiro positivo.')
            furos.setdefault(int(numero_furo), []).append((10*x, 10*y))
        for indice, vertices in furos.items():
            if len(vertices) < 3:
                raise ValueError(f'Furo {indice}: são necessários pelo menos três vértices.')
        dados_barras = self._ler_linhas(self.barras, 3, 'Armadura')
        dados_barras = [(10*x, 10*y, a if self.modo.get() == 'dimensionamento' else 100*a)
                        for x, y, a in dados_barras]  # cm -> mm; cm² -> mm²
        if not dados_barras:
            raise ValueError('Informe pelo menos uma barra de armadura.')
        if any(a <= 0 for _,_,a in dados_barras):
            raise ValueError('Proporções e áreas de armadura devem ser positivas.')
        modo = self.modo.get()
        if modo == 'dimensionamento':
            proporcoes = [a for _,_,a in dados_barras]
            if not math.isclose(sum(proporcoes), 1.0, rel_tol=1e-6, abs_tol=1e-6):
                raise ValueError(f'A soma das proporções ρ deve ser 1,0; encontrada {sum(proporcoes):.8f}.')
            barras = [Barra(x,y,proporcao=a) for x,y,a in dados_barras]
            As = None
        else:
            As = sum(a for _,_,a in dados_barras)
            barras = [Barra(x,y,proporcao=a/As) for x,y,a in dados_barras]
        secao = Secao(contorno=[tuple(p) for p in contorno],
                      furos=list(furos.values()), barras=barras)
        concreto = Concreto(fck=valores['fck (MPa)'], gamma_c=valores['γc'])
        aco = Aco(fyk=valores['fyk (MPa)'], gamma_s=valores['γs'],
                  es=valores['Es (MPa)'])
        esforcos = (valores['Nad (kN)']*1e3,
                    valores['Maxd (kN·m)']*1e6,
                    valores['Mayd (kN·m)']*1e6)
        return secao, concreto, aco, esforcos, As, modo

    def _atualizar_diagramas(self):
        """Redesenha a última seção sem executar novamente o cálculo."""
        self._mostrar_ultima_visualizacao()

    def _mostrar_ultima_visualizacao(self):
        """Alterna entre a seção e a interação já calculadas."""
        if self.mostrar_interacao.get() and self._ultimo_interacao is not None:
            self._desenhar_interacao(*self._ultimo_interacao)
        elif self._ultimo is not None:
            self._desenhar(*self._ultimo)

    def _alternar_interacao(self):
        """Ativa a curva; se ainda não existe, recalcula o estado resistente."""
        if self._ocupado:
            return
        if self.mostrar_interacao.get() and self._ultimo_interacao is None:
            self.calcular()
        else:
            self._mostrar_ultima_visualizacao()

    def _desenhar(self, secao, As, estado, esforcos, tipo, titulo, concreto=None, salvar_em=None):
        """Atualiza a visualização da seção no eixo Matplotlib embutido.
    
            Args:
                secao: Geometria e armaduras.
                As (float | None): Área total de armadura em mm².
                estado: Estado de deformação ou None.
                esforcos (tuple | None): Resultantes em N e N·mm.
                tipo (str): ``solicitantes`` ou ``resistentes``.
                titulo (str): Título da figura.
                salvar_em (str | None): Caminho opcional para salvar a figura.
            
        """
        self.eixo_figura.clear()
        desenhar_secao(secao, area_total=As, estado=estado, esforcos=esforcos,
                       tipo_esforcos=tipo, titulo=titulo, salvar_em=salvar_em,
                       numerar_barras=True, ax=self.eixo_figura, mostrar=False)
        if self.mostrar_diagramas.get() and estado is not None and concreto is not None:
            desenhar_diagramas_deformacoes_tensoes(self.eixo_figura, secao, estado, concreto)
        # Coloca a legenda fora da área de dados, evitando cobrir a seção.
        legenda = self.eixo_figura.get_legend()
        if legenda is not None:
            alcas, rotulos = self.eixo_figura.get_legend_handles_labels()
            legenda.remove()
            if alcas:
                self.eixo_figura.legend(alcas, rotulos, loc='upper center',
                    bbox_to_anchor=(0.5, -0.09), ncol=2, fontsize=8,
                    frameon=True, borderaxespad=0.4)
        # Apenas os rótulos dos eixos mudam: o desenho permanece em mm.
        self.eixo_figura.xaxis.set_major_formatter(FuncFormatter(lambda valor, _: f'{valor/10:g}'))
        self.eixo_figura.yaxis.set_major_formatter(FuncFormatter(lambda valor, _: f'{valor/10:g}'))
        self.eixo_figura.set_xlabel('x (cm)')
        self.eixo_figura.set_ylabel('y (cm)')
        self.figura.subplots_adjust(bottom=0.23)
        self.canvas_figura.draw_idle()

    def visualizar(self):
        """Exibe geometria e esforços solicitantes sem resolver o equilíbrio.
    
            Erros de entrada são apresentados em uma caixa de diálogo.
            
        """
        try:
            secao, _, _, esforcos, As, modo = self._dados()
            self._ultimo_interacao = None
            self._ultimo = (secao, As, None, esforcos, 'solicitantes', 'Geometria e esforços solicitantes', None)
            self._desenhar(*self._ultimo)
        except Exception as exc:
            messagebox.showerror('Dados inválidos', str(exc))

    def salvar_imagem(self):
        """Salva a figura atual em PNG ou PDF após escolha do caminho.
        """
        if self._ultimo is None and self._ultimo_interacao is None:
            messagebox.showinfo('Imagem', 'Calcule ou visualize a seção antes de salvar.')
            return
        caminho = filedialog.asksaveasfilename(defaultextension='.png',
                     filetypes=[('Imagem PNG','*.png'),('Documento PDF','*.pdf')])
        if caminho:
            try:
                self.figura.savefig(caminho, dpi=200, bbox_inches='tight')
            except Exception as exc:
                messagebox.showerror('Erro ao salvar', str(exc))

    def calcular(self):
        """Valida os dados e inicia o cálculo em uma thread auxiliar.
    
            Impede cálculos simultâneos, desativa o botão e mantém a
            interface responsiva durante a otimização.
            
        """
        if self._ocupado:
            return
        try:
            dados = self._dados()
        except Exception as exc:
            messagebox.showerror('Dados inválidos', str(exc))
            return
        self._ocupado = True
        self.botao_calcular.configure(state='disabled')
        self.status.set('Calculando...')
        self.update_idletasks()
        # Cálculo em thread para manter a interface responsiva.
        threading.Thread(target=self._calcular_worker, args=(dados,), daemon=True).start()

    def _calcular_worker(self, dados):
        """Executa o dimensionamento ou a verificação fora da thread da GUI.
    
            Args:
                dados (tuple): Resultado de ``_dados()``.
    
            Notes:
                Apenas agenda a atualização gráfica por ``self.after``.
                Se o equilíbrio falhar, conserva a representação geométrica
                sem mostrar linha neutra ou esforços resistentes não validados.
            
        """
        secao, concreto, aco, esforcos, As, modo = dados
        try:
            N, Mx, My = esforcos
            if modo == 'dimensionamento':
                r = resolver_equilibrio(secao, concreto, aco, N, Mx, My,
                        x0=0.4*secao.altura(0), alfa0=0.0,
                        As0=0.01*secao.area, multiplas_tentativas=True)
                x, alfa, As_resultado = r.x
                lam = None
            else:
                r = resolver_verificacao(secao, concreto, aco, As=As,
                        Nsd=N, Msdx=Mx, Msdy=My,
                        x0=0.4*secao.altura(0), alfa0=0.0,
                        lambda0=1.0, multiplas_tentativas=True)
                x, alfa, lam = r.x
                As_resultado = As
            sucesso = bool(r.success)
            if sucesso:
                estado = EstadoDeformacao(secao, x, alfa)
                resistentes = esforcos_resistentes(secao, estado, concreto, aco,
                                                  area_total=As_resultado)
                plot_esforcos = esforcos if modo == 'dimensionamento' else resistentes
                tipo = 'solicitantes' if modo == 'dimensionamento' else 'resistentes'
                titulo = 'Dimensionamento — convergência alcançada' if modo == 'dimensionamento' else 'Verificação — convergência alcançada'
            else:
                estado = None
                plot_esforcos = esforcos if modo == 'dimensionamento' else None
                tipo = 'solicitantes' if modo == 'dimensionamento' else 'resistentes'
                titulo = 'NÃO HOUVE CONVERGÊNCIA'
            linhas = [
                f'Modo: {modo}',
                f'Convergência: {"SIM" if sucesso else "NÃO"}',
                '',
                'PROPRIEDADES GEOMÉTRICAS',
                f'Área geométrica: {secao.area/100:.3f} cm²',
                f'Centroide: xc = {secao.xc/10:.3f} cm; yc = {secao.yc/10:.3f} cm',
                f'Ix central = {secao.Ix/1e4:.6e} cm⁴',
                f'Iy central = {secao.Iy/1e4:.6e} cm⁴',
                f'Ixy central = {secao.Ixy/1e4:.6e} cm⁴',
                f'Número de barras: {len(secao.barras)}',
            ]
            if sucesso:
                linhas.extend([f'x = {x/10:.6f} cm', f'α = {math.degrees(alfa):.6f}°',
                               f'As total = {As_resultado/100:.6f} cm²'])
                etas_barras = [secao.coordenadas_rotacionadas(barra.posicao, alfa)[1]
                               for barra in secao.barras]
                linhas.extend([
                    '', 'DEFORMAÇÕES LONGITUDINAIS (‰)',
                    f'Fibra superior do concreto: {estado.epsilon_s*1000:+.6f}',
                    f'Armadura superior: {estado.deformacao(max(etas_barras))*1000:+.6f}',
                    f'Armadura inferior: {estado.deformacao(min(etas_barras))*1000:+.6f}',
                    f'Fibra inferior do concreto: {estado.epsilon_concreto_inferior*1000:+.6f}',
                    f'Domínio de deformação: {estado.dominio}',
                ])
                if lam is not None:
                    linhas.append(f'λ = {lam:.8f} — {"reserva inferior a 1" if lam < 1 else "reserva não inferior a 1"}')
                linhas.extend([f'Nr = {resistentes[0]/1e3:+.6f} kN',
                               f'Mrx = {resistentes[1]/1e6:+.6f} kN·m',
                               f'Mry = {resistentes[2]/1e6:+.6f} kN·m'])
            else:
                linhas.append('Sem linha neutra nem esforços resistentes validados.')
            linhas.append(f'Norma dos resíduos = {getattr(r,"norma_residuos",float("nan")):.3e}')
            desenho = (secao, As_resultado if sucesso else As, estado,
                       plot_esforcos, tipo, titulo, concreto)
            if sucesso and self.mostrar_interacao.get():
                try:
                    curva = calcular_diagrama_interacao(
                        secao, concreto, aco, As=As_resultado, Nsd=N,
                        n_angulos=72, n_profundidades=100)
                    self.after(0, lambda: self._finalizar_com_interacao(
                        '\n'.join(linhas), desenho, curva, esforcos, As_resultado))
                except Exception as exc:
                    aviso = f'\n\nDiagrama Mx–My não calculado: {exc}'
                    self.after(0, lambda: self._finalizar('\n'.join(linhas)+aviso, desenho))
            else:
                self.after(0, lambda: self._finalizar('\n'.join(linhas), desenho))
        except Exception as exc:
            erro = str(exc)
            # Se o cálculo falhar, ainda apresentar geometria e armadura.
            tipo = 'solicitantes' if modo == 'dimensionamento' else 'resistentes'
            plot_esforcos = esforcos if modo == 'dimensionamento' else None
            self.after(0, lambda: self._finalizar('NÃO HOUVE CONVERGÊNCIA\n'+erro,
                    (secao, As, None, plot_esforcos, tipo, 'NÃO HOUVE CONVERGÊNCIA', None)))


    def _finalizar_com_interacao(self, texto, desenho, resultado, esforcos, As):
        """Mantém o resultado principal e a curva para alternância pelo checkbox."""
        self._finalizar(texto, desenho)
        self._ultimo_interacao = (resultado, esforcos, As)
        self._mostrar_ultima_visualizacao()

    def _calcular_interacao_worker(self, secao, concreto, aco, esforcos, As):
        """Calcula estados resistentes usando exclusivamente analise.interacao."""
        try:
            resultado = calcular_diagrama_interacao(
                secao, concreto, aco, As=As, Nsd=esforcos[0],
                n_angulos=72, n_profundidades=100)
            self.after(0, lambda: self._finalizar_interacao(
                resultado, esforcos, As, secao))
        except Exception as exc:
            erro = str(exc)
            self.after(0, lambda: self._finalizar_erro_interacao(erro))

    def _desenhar_interacao(self, resultado, esforcos, As):
        """Delega a visualização ao módulo visualizacao.diagrama_interacao."""
        estimativa = estimar_aproveitamento_radial(resultado, esforcos[1], esforcos[2])
        desenhar_diagrama_interacao(
            self.eixo_figura, resultado,
            momento_solicitante=(esforcos[1], esforcos[2]),
            aproveitamento=estimativa)
        self.figura.subplots_adjust(bottom=.22)
        self.canvas_figura.draw_idle()

    def _finalizar_interacao(self, resultado, esforcos, As, secao):
        self._ocupado = False
        self.botao_calcular.configure(state='normal')
        n_pontos = len(resultado.pontos)
        self.status.set('Diagrama calculado.' if n_pontos else 'Nenhum estado encontrado.')
        linhas = [
            'DIAGRAMA DE INTERAÇÃO Mx–My',
            f'N fixo = {esforcos[0]/1e3:+.3f} kN',
            f'As total = {As/100:.3f} cm²',
            f'Mx solicitante = {esforcos[1]/1e6:+.3f} kN·m',
            f'My solicitante = {esforcos[2]/1e6:+.3f} kN·m',
            f'Área geométrica = {secao.area/100:.3f} cm²',
            f'Centroide = ({secao.xc/10:.3f}; {secao.yc/10:.3f}) cm',
            f'Estados resistentes encontrados = {n_pontos}',
            f'Orientações sem raiz detectada = {len(resultado.angulos_sem_solucao)}',
            '',
            'ESTIMATIVA RADIAL (INTERPOLAÇÃO)',
        ]
        estimativa = estimar_aproveitamento_radial(resultado, esforcos[1], esforcos[2])
        if estimativa.confiavel_para_interpolacao:
            linhas.extend([
                f'λ estimado = {estimativa.lambda_estimado:.6f}',
                f'Mrx interpolado = {estimativa.Mx_resistente/1e6:+.3f} kN·m',
                f'Mry interpolado = {estimativa.My_resistente/1e6:+.3f} kN·m',
            ])
        else:
            linhas.append('λ não determinado pela interpolação radial.')
        linhas.extend([
            estimativa.observacao,
            '',
            'ATENÇÃO: pontos de equilíbrio normal amostrados.',
            'O gráfico não é uma envoltória resistente certificada.',
            'A posição da solicitação não comprova segurança estrutural.',
        ])
        if not n_pontos:
            linhas.append('Nenhuma raiz encontrada; tente ampliar a busca numérica.')
        self._escrever('\n'.join(linhas))
        self._ultimo = None
        self._ultimo_interacao = (resultado, esforcos, As)
        self._desenhar_interacao(*self._ultimo_interacao)

    def _finalizar_erro_interacao(self, erro):
        self._ocupado = False
        self.botao_calcular.configure(state='normal')
        self.status.set('Erro no diagrama de interação.')
        self._escrever('Erro ao calcular o diagrama Mx–My:\n' + erro)
        self._ultimo_interacao = None

    def _finalizar(self, texto, desenho):
        """Reativa os controles e apresenta os resultados do cálculo.
    
            Args:
                texto (str): Relatório a exibir.
                desenho (tuple): Argumentos para ``_desenhar``.
    
            Notes:
                Deve ser executado na thread da interface Tkinter.
            
        """
        self._ocupado = False
        self.botao_calcular.configure(state='normal')
        self.status.set('Cálculo concluído.')
        self._escrever(texto)
        self._ultimo = desenho
        self._ultimo_interacao = None
        try:
            self._desenhar(*desenho)
        except Exception as exc:
            messagebox.showerror('Erro de visualização', str(exc))


if __name__ == '__main__':
    Interface().mainloop()
