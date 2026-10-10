"""Interface gráfica do Pyobliqua (Tkinter + Matplotlib).

Execute na raiz do projeto: python interface_pyobliqua.py
Dependências: numpy, scipy, matplotlib; tkinter da instalação Python.
Unidades de entrada: mm, MPa, kN, kN.m e mm².
"""
import math
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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


def numero(texto, descricao):
    try:
        valor = float(str(texto).strip().replace(',', '.'))
    except (ValueError, TypeError) as exc:
        raise ValueError(f'{descricao}: informe um número válido.') from exc
    if not math.isfinite(valor):
        raise ValueError(f'{descricao}: o valor deve ser finito.')
    return valor


class Tabela(ttk.Frame):
    """Tabela tipo planilha: duplo clique edita a célula; Inserir/Excluir linhas."""
    def __init__(self, master, colunas, larguras=None, altura=7):
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
        self.grade.insert('', 'end', values=valores or [''] * len(self.colunas))

    def excluir(self):
        for item in self.grade.selection():
            self.grade.delete(item)

    def limpar(self):
        for item in self.grade.get_children():
            self.grade.delete(item)

    def linhas(self):
        return [list(self.grade.item(i, 'values')) for i in self.grade.get_children()]

    def editar(self, evento):
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


class Interface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Pyobliqua — Dimensionamento e verificação de seções')
        self.geometry('1450x850')
        self.minsize(1100, 670)
        self.modo = tk.StringVar(value='dimensionamento')
        self.campos = {}
        self._ocupado = False
        self._ultimo = None
        self._montar()
        self.carregar_exemplo_51()

    def _campo(self, parent, rotulo, valor, linha, coluna, largura=12):
        ttk.Label(parent, text=rotulo).grid(row=linha, column=coluna * 2, sticky='w', padx=(8, 2), pady=4)
        var = tk.StringVar(value=str(valor))
        ttk.Entry(parent, textvariable=var, width=largura).grid(
            row=linha, column=coluna * 2 + 1, sticky='ew', padx=(0, 9), pady=4)
        self.campos[rotulo] = var
        return var

    def _montar(self):
        estilo = ttk.Style(self)
        if 'clam' in estilo.theme_names():
            estilo.theme_use('clam')
        corpo = ttk.Frame(self, padding=8)
        corpo.pack(fill='both', expand=True)

        cabecalho = ttk.Frame(corpo)
        cabecalho.pack(fill='x')
        ttk.Label(cabecalho, text='Pyobliqua', font=('Arial', 17, 'bold')).pack(side='left')
        ttk.Label(cabecalho, text='mm | MPa | kN | kN·m | mm²').pack(side='left', padx=12)
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
        self.contorno = Tabela(cont, ('x (mm)', 'y (mm)'), altura=12)
        self.contorno.pack(fill='both', expand=True)
        ttk.Label(cont, text='Não repita o primeiro vértice.', foreground='#555').pack(anchor='w')
        self.furos = Tabela(fur, ('Furo nº', 'x (mm)', 'y (mm)'), altura=12,
                           larguras=[65, 100, 100])
        self.furos.pack(fill='both', expand=True)
        ttk.Label(fur, text='Use o mesmo número para os vértices de um furo.',
                  foreground='#555').pack(anchor='w')
        self.barras = Tabela(arm, ('x (mm)', 'y (mm)', 'ρ ou As'), altura=12,
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
        resultado = ttk.LabelFrame(esquerdo, text='Resultados', padding=4)
        resultado.pack(fill='both', expand=False)
        self.saida = tk.Text(resultado, height=11, wrap='word', font=('Consolas', 9))
        self.saida.pack(fill='both', expand=True)
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
        if self.modo.get() == 'dimensionamento':
            self.aviso_barras.configure(text='ρ = fração da área total; soma das proporções = 1.')
        else:
            self.aviso_barras.configure(text='As individual de cada barra, em mm².')

    def _definir(self, **kwargs):
        for k, v in kwargs.items():
            self.campos[k].set(str(v))

    def _preencher(self, tabela, linhas):
        tabela.limpar()
        for linha in linhas:
            tabela.adicionar(linha)

    def carregar_exemplo_51(self):
        self.modo.set('dimensionamento')
        self.atualizar_modo()
        self._definir(**{'fck (MPa)': 20, 'fyk (MPa)': 500, 'Es (MPa)': 210000,
                         'γc': 1.4, 'γs': 1.15, 'Nad (kN)': -200,
                         'Maxd (kN·m)': -500, 'Mayd (kN·m)': 500})
        self._preencher(self.contorno, [(0, 0), (850, 0), (850, 850), (0, 850)])
        self._preencher(self.furos, [(1, 300, 300), (1, 550, 300), (1, 550, 550), (1, 300, 550)])
        coords = [(5,5),(20,5),(35,5),(50,5),(65,5),(80,5),
                  (5,20),(5,35),(5,50),(5,65),(5,80),
                  (80,20),(80,35),(80,50),(80,65),(80,80),
                  (20,80),(35,80),(50,80),(65,80)]
        self._preencher(self.barras, [(x*10,y*10,0.05) for x,y in coords])
        self._escrever('Exemplo 5.1 carregado: dimensionamento, 20 barras, seção vazada.\n')

    def carregar_exemplo_52(self):
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
        self._preencher(self.contorno, [(10*x,10*y) for x,y in vertices])
        self.furos.limpar()
        self._preencher(self.barras, [(10*x,10*y,200) for x,y in coords])
        self._escrever('Exemplo 5.2 carregado: verificação, As total = 3000 mm².\n')

    def _escrever(self, texto):
        self.saida.delete('1.0', 'end')
        self.saida.insert('end', texto)

    def _ler_linhas(self, tabela, n, nome):
        linhas = []
        for i, linha in enumerate(tabela.linhas(), 1):
            if not any(str(v).strip() for v in linha):
                continue
            if len(linha) != n or any(not str(v).strip() for v in linha):
                raise ValueError(f'{nome}, linha {i}: preencha todas as colunas.')
            linhas.append([numero(v, f'{nome}, linha {i}') for v in linha])
        return linhas

    def _dados(self):
        valores = {k: numero(v.get(), k) for k,v in self.campos.items()}
        for chave in ('fck (MPa)', 'fyk (MPa)', 'Es (MPa)', 'γc', 'γs'):
            if valores[chave] <= 0:
                raise ValueError(f'{chave} deve ser positivo.')
        contorno = self._ler_linhas(self.contorno, 2, 'Contorno')
        if len(contorno) < 3:
            raise ValueError('O contorno deve ter pelo menos três vértices.')
        furos = {}
        for i, linha in enumerate(self._ler_linhas(self.furos, 3, 'Furos'), 1):
            numero_furo, x, y = linha
            if numero_furo <= 0 or not numero_furo.is_integer():
                raise ValueError(f'Furos, linha {i}: número do furo deve ser inteiro positivo.')
            furos.setdefault(int(numero_furo), []).append((x,y))
        for indice, vertices in furos.items():
            if len(vertices) < 3:
                raise ValueError(f'Furo {indice}: são necessários pelo menos três vértices.')
        dados_barras = self._ler_linhas(self.barras, 3, 'Armadura')
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

    def _desenhar(self, secao, As, estado, esforcos, tipo, titulo, salvar_em=None):
        self.eixo_figura.clear()
        desenhar_secao(secao, area_total=As, estado=estado, esforcos=esforcos,
                       tipo_esforcos=tipo, titulo=titulo, salvar_em=salvar_em,
                       numerar_barras=True, ax=self.eixo_figura, mostrar=False)
        self.canvas_figura.draw_idle()

    def visualizar(self):
        try:
            secao, _, _, esforcos, As, modo = self._dados()
            self._ultimo = (secao, As, None, esforcos, 'solicitantes', 'Geometria e esforços solicitantes')
            self._desenhar(*self._ultimo)
        except Exception as exc:
            messagebox.showerror('Dados inválidos', str(exc))

    def salvar_imagem(self):
        if self._ultimo is None:
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
            linhas = [f'Modo: {modo}', f'Convergência: {"SIM" if sucesso else "NÃO"}',
                      f'Área geométrica: {secao.area:.3f} mm²',
                      f'Centroide: ({secao.xc:.3f}; {secao.yc:.3f}) mm',
                      f'Número de barras: {len(secao.barras)}']
            if sucesso:
                linhas.extend([f'x = {x:.6f} mm', f'α = {math.degrees(alfa):.6f}°',
                               f'As total = {As_resultado:.6f} mm² ({As_resultado/100:.6f} cm²)'])
                linhas.extend([
                    f'ε superior (fibra superior da seção) = {estado.epsilon_s*1000:+.6f} ‰',
                    f'ε inferior (fibra inferior da seção) = {estado.epsilon_concreto_inferior*1000:+.6f} ‰',
                    f'Domínio de deformação = {estado.dominio}',
                ])
                if lam is not None:
                    linhas.append(f'λ = {lam:.8f} — {"reserva inferior a 1" if lam < 1 else "reserva não inferior a 1"}')
                linhas.extend([f'Nr = {resistentes[0]/1e3:+.6f} kN',
                               f'Mrx = {resistentes[1]/1e6:+.6f} kN·m',
                               f'Mry = {resistentes[2]/1e6:+.6f} kN·m'])
            else:
                linhas.append('Sem linha neutra nem esforços resistentes validados.')
            linhas.append(f'Norma dos resíduos = {getattr(r,"norma_residuos",float("nan")):.3e}')
            self.after(0, lambda: self._finalizar('\n'.join(linhas),
                    (secao, As_resultado if sucesso else As, estado, plot_esforcos, tipo, titulo)))
        except Exception as exc:
            erro = str(exc)
            # Se o cálculo falhar, ainda apresentar geometria e armadura.
            tipo = 'solicitantes' if modo == 'dimensionamento' else 'resistentes'
            plot_esforcos = esforcos if modo == 'dimensionamento' else None
            self.after(0, lambda: self._finalizar('NÃO HOUVE CONVERGÊNCIA\n'+erro,
                    (secao, As, None, plot_esforcos, tipo, 'NÃO HOUVE CONVERGÊNCIA')))

    def _finalizar(self, texto, desenho):
        self._ocupado = False
        self.botao_calcular.configure(state='normal')
        self.status.set('Cálculo concluído.')
        self._escrever(texto)
        self._ultimo = desenho
        try:
            self._desenhar(*desenho)
        except Exception as exc:
            messagebox.showerror('Erro de visualização', str(exc))


if __name__ == '__main__':
    Interface().mainloop()
