---
marp: true
theme: pyobliqua-ufrgs
paginate: true
math: katex
footer: "Pyobliqua | Formulação baseada em Campos Filho (2014)"
---

<!-- _class: lead -->

# Flexão composta Oblíqua no Estado Limite Último

## Dimensionamento e verificação de seções poligonais

### Apresentação do programa: Pyobliqua

Metodologia de Américo Campos Filho (2014) e implementação atual em Python  
UFRGS | Engenharia Civil

---

## Objetivos

Ao final dessa aula você deve conseguir:

- explicar como $x$ e $\alpha$ definem o campo de deformações;
- relacionar deformações, tensões e esforços resistentes;
- distinguir dimensionamento de verificação por $\lambda$;
- reconhecer o papel do `least_squares` no Pyobliqua;
- interpretar resultados sem confundir convergência com validação.

---

## Sequência do cálculo

A flexão composta oblíqua, segue o seguinte roteiro de cálculo:

$$
\textbf{geometria} \longrightarrow \textbf{deformações} \longrightarrow
\textbf{tensões} \longrightarrow \textbf{esforços resistentes}
\longrightarrow \textbf{equilíbrio}
$$

> Cada etapa usa a saída da anterior. O solver atua no final, ajustando as incógnitas do problema para reduzir o desequilíbrio entre ações e resistências.

---

## Flexão composta oblíqua

<div class="duas-colunas">

<div>

Na flexão composta atuam simultaneamente força normal e momentos fletores.

$$
\mathbf S_d = (N_{sd},M_{sdx},M_{sdy})
$$

A flexão é **oblíqua** quando a orientação da linha neutra não é conhecida a priori.

A análise precisa encontrar a profundidade $x$ e a inclinação $\alpha$ compatíveis com o equilíbrio.

</div>

<div>

![alt text](fig1.png)

</div>

</div>

---

## Geometria poligonal

<div class="duas-colunas">

<div>

Para se ter generalidade, a seção é representada por contornos fechados:

- o contorno externo é orientado no sentido anti-horário;
- os contornos dos furos são orientados no sentido horário;
- cada barra tem posição sua área $A_s$ em caso de o dimensionamento ou uma fração da área total $\rho$ em caso de verificação.

A representação por contornos permite tratar seções vazadas e assimétricas sem mudar a formulação resistente.

</div>

<div>

![alt text](image.png)

</div>

---

## Sistema global $(X,Y)$ e sistema local $(x,y)$

<div class="duas-colunas">

<div>

As coordenadas geométricas definem a seção no sistema global $(X,Y)$. Calculam-se área e centroide e transfere-se a origem para o centroide:

$$
x=X-X_C, \qquad y=Y-Y_C
$$

Os esforços resistentes são então referidos aos eixos centroidais locais. Manter a convenção de eixos e sinais consistente é essencial para comparar solicitação e resistência.

</div>

<div>

![alt text](image-1.png)

</div>

---

## Hipótese de deformações planas e sistema local $(\xi,\eta)$

<div class="duas-colunas">

<div>

Adota-se que as **seções planas permanecem planas**, ou seja, a deformação longitudinal varia linearmente ao longo da seção.

O **estado de deformações** passa a ser definido pela **profundidade** $x$ da linha neutra e pela **orientação** $\alpha$, de modo que para cada ponto $(x,y)$, correspondem ao par $(\xi,\eta)$ no sistema local, dado por:

$$
\xi=x\cos\alpha+y\sin\alpha
$$

$$
\eta=-x\sin\alpha+y\cos\alpha
$$

</div>

![alt text](image-2.png)

</div>

---

<div class="duas-colunas">

<div>

O campo de deformações passa a ser:

$$
\varepsilon(\eta)=b\eta+c
$$

E dessa forma a deformação de qualquer ponto $P$ é obtida por sua coordenada local:

$$
\varepsilon_P=b\eta_P+c
$$

A linha neutra corresponde ao conjunto de pontos em que $\varepsilon=0$.


</div>

<div>

![alt text](image-3.png)

</div>

</div>

---

## Domínios de deformação no ELU

Os domínios representam configurações-limite de deformação da seção:


![alt text](image-4.png)

---

| Domínio | Situação física predominante |
|---|---|
| reta a | Tração uniforme, ruptura por deformação plástica excessiva da armadura |
| 1 | Tração não uniforme, sem compressão, ruptura por deformação plástica excessiva da armadura inferior |
| 2 | Flexão simples ou composta sem ruptura à compressão do concreto com o máximo alongamento permitido da armadura |
| 3 | Flexão simples ou composta sem ruptura com ruptura do concreto e escoamento da armadura |
| 4 | Flexão simples ou composta com ruptura à compressão do concreto e aço sem escoamento |
| 4a | Flexão composta com armaduras comprimidas |
| 5 | Compressão não uniforme, sem tração |
| reta b | Compressão uniforme |

---

Os limites de $x$, $\varepsilon_s$ e $\varepsilon_i$ dependem de $d$, $h$, $\varepsilon_{c2}$ e $\varepsilon_{cu}$.

![alt text](image-5.png)

---

<div class="duas-colunas">

<div>

Para cada orientação $\alpha$, a geometria fornece as fibras extremas e a altura útil $d$. A Tabela 2.1 relaciona $x$ às deformações-limite em cada domínio.

Os domínios 1–2, 4a e 5 usam relações próprias, também apresentadas na Tabela 2.1.

**Exemplo nos domínios 3–4**, com compressão negativa:

$$
\varepsilon_s=-\varepsilon_{cu}
$$

$$
\varepsilon_i=\varepsilon_{cu}\frac{d-x}{x}
$$

</div>

<div>

![alt text](image-6.png)

</div>

</div>

---

Conhecidas as deformações nos pontos extremos $(\eta_s,\varepsilon_s)$ e $(\eta_i,\varepsilon_i)$:

$$
b=\frac{\varepsilon_s-\varepsilon_i}{\eta_s-\eta_i}, \qquad
c=\varepsilon_s-b\eta_s
$$

Logo, para qualquer ponto $P$, inclusive uma barra:

$$
\varepsilon_P=b\eta_P+c
$$

Essa etapa é a compatibilidade cinemática que conecta a posição da linha neutra à resposta dos materiais.

---

## Concreto no ELU

<div class="duas-colunas">

<div>

A resistência à tração do concreto é desprezada. Adota-se compressão negativa e a lei parábola-retângulo. A expressão usa os limites $\varepsilon_{c2}$ e $\varepsilon_{cu}$ e os coeficientes $a_1$ e $a_2$.

$$
\sigma_c(\varepsilon)=
\begin{cases}
0, & \varepsilon\geq 0 \\
\sigma_{cd}(a_2\varepsilon^2+a_1\varepsilon), & -\varepsilon_{c2}\leq\varepsilon<0 \\
-\sigma_{cd}, & -\varepsilon_{cu}\leq\varepsilon< -\varepsilon_{c2}
\end{cases}
$$

$$
f_{cd}=\frac{f_{ck}}{\gamma_c}, \qquad \sigma_{cd}=0{,}85f_{cd}
$$

Os coeficientes $a_1$ e $a_2$ aproximam o diagrama do concreto por uma parábola, dessa forma, mantém-se o esquema de integração.

</div>

![alt text](image-7.png)

<div>

</div>

</div>

---

<div class="duas-colunas">

<div>

A tabela abaixo mostra os coeficientes que aproximam o trecho parabólico.

| Classe | $a_2$ | $a_1$ |
|---:|---:|---:|
| $f_{ck}<50$ MPa | 250000 | 1000 |
| C60 | 120101 | 720,64 |
| C70 | 81458 | 620,29 |
| C80 | 69363 | 581,26 |
| C90 | 64545 | 561,34 |

$$
\sigma_c(\varepsilon)=
\begin{cases}
0, & \varepsilon\geq 0 \\
\sigma_{cd}(a_2\varepsilon^2+a_1\varepsilon), & -\varepsilon_{c2}\leq\varepsilon<0 \\
-\sigma_{cd}, & -\varepsilon_{cu}\leq\varepsilon< -\varepsilon_{c2}
\end{cases}
$$

</div>

<div>

![alt text](image-7.png)

</div>

</div>

---

<div class="duas-colunas">

<div>

As deformações limites para **Concretos até C50**:

$$
\varepsilon_{c2}=2{,}0\,‰, \qquad \varepsilon_{cu}=3{,}5\,‰
$$

E para **Concretos entre C50 e C90** os limites de deformação variam com $f_{ck}$:

$$
\varepsilon_{c2}=2{,}0\,‰+0{,}085\,‰(f_{ck}-50)^{0{,}53}
$$

$$
\varepsilon_{cu}=2{,}6\,‰+35\,‰\left(\frac{90-f_{ck}}{100}\right)^4
$$

</div>

<div>

![alt text](image-7.png)

</div>

</div>

---

## Aço da armadura

<div class="duas-colunas">

<div>

Para cada barra, calcula-se a deformação no seu ponto. A lei constitutiva bilinear usa a tensão de escoamento de cálculo e a deformação correspondente.

Cada barra contribui com tensão e área. No dimensionamento, a área de cada barra pode ser representada como fração da área total $A_s$.

$$
f_{yd}=\frac{f_{yk}}{\gamma_s}, \qquad
\varepsilon_{yd}=\frac{f_{yd}}{E_s}
$$

$$
\sigma_s(\varepsilon)=
\begin{cases}
E_s\varepsilon, & |\varepsilon|<\varepsilon_{yd} \\
\operatorname{sgn}(\varepsilon)f_{yd}, & |\varepsilon|\geq\varepsilon_{yd}
\end{cases}
$$

</div>

<div>

![alt text](image-8.png)

</div>

</div>

---

## Regiões de integração do concreto

<div class="duas-colunas">

<div>

O campo de deformações divide a seção em três regiões:

| Região | Faixa de deformação | Contribuição |
|---|---|---|
| 0 | $\varepsilon\geq0$ | Concreto sem tensão resistente |
| I | $-\varepsilon_{c2}\leq\varepsilon<0$ | Tensão parabólica |
| II | $-\varepsilon_{cu}\leq\varepsilon< -\varepsilon_{c2}$ | Tensão constante |

Os contornos são recortados nas transições $\varepsilon=0$ e $\varepsilon=-\varepsilon_{c2}$. Isso permite integrar cada lei na região geométrica correta.

</div>

<div>

![alt text](image-9.png)

</div>

---

## Integração pelo teorema de Green

<div class="duas-colunas">

<div>

As integrais de área são convertidas em integrais de contorno. Cada aresta do polígono é reta, então sua contribuição pode ser calculada analiticamente.

As contribuições do contorno externo e dos furos são somadas com sinais definidos pela orientação dos vértices. Para um monômio:
$$
\iint_A \xi^p\eta^q\,dA
=\oint_{\partial A}\frac{\xi^{p+1}\eta^q}{p+1}\,d\eta
$$

</div>

<div>

![alt text](image-10.png)

</div>

</div>

---

## Integrais exigidas pela lei parabólica

Substituindo $\varepsilon=b\eta+c$ na tensão parabólica, resulta um polinômio em $\eta$:

$$
\sigma_c=\sigma_{cd}(D_0+D_1\eta+D_2\eta^2)
$$

$$
D_0=a_1c+a_2c^2, \quad
D_1=a_1b+2a_2bc, \quad D_2=a_2b^2
$$

Os esforços do concreto exigem integrais de monômios até ordens suficientes para integrar $\sigma_c$, $\sigma_c\eta$ e $\sigma_c\xi$. A rotina de Green calcula essas parcelas ao longo dos segmentos recortados.

---

## Resultantes resistentes

<div class="duas-colunas">

<div>

No sistema rotacionado $(\xi,\eta)$, integram-se tensões sobre o concreto e somam-se as contribuições discretas das barras. O sinal do momento depende da convenção dos eixos e dos esforços definida para a seção. 

As barras entram como parcelas discretas. Para cada barra $j$, o cálculo usa posição, deformação, tensão e área $A_{sj}$.

</div>

<div>

$$
N_R=\int_{A_c}\sigma_c\,dA+\sum_j A_{sj}\sigma_{sj}
$$

$$
M_{R\xi}=\int_{A_c}\sigma_c\eta\,dA+\sum_j A_{sj}\sigma_{sj}\eta_j
$$

$$
M_{R\eta}=-\int_{A_c}\sigma_c\xi\,dA-\sum_j A_{sj}\sigma_{sj}\xi_j
$$

</div>

</div>



---

## Transformação dos momentos

Os momentos são transformados para os eixos locais $(x,y)$ antes da comparação com $M_{sdx}$ e $M_{sdy}$.

$$
M_{Rx}=M_{R\xi}\cos\alpha-M_{R\eta}\sin\alpha
$$
$$
M_{Ry}=M_{R\xi}\sin\alpha+M_{R\eta}\cos\alpha
$$

A força normal não depende da rotação dos eixos. A transformação mantém os momentos resistentes no mesmo referencial das solicitações.

---

## Condição de equilíbrio


O estado resistente deve satisfazer simultaneamente o equilíbrio da força normal e dos dois momentos fletores, ou seja:

$$
N_R=N_{sd}, \qquad M_{Rx}=M_{sdx}, \qquad M_{Ry}=M_{sdy}
$$

Definindo $\mathbf r=\mathbf R-\mathbf S_d$:

$$
\mathbf r=\begin{bmatrix}
N_R-N_{sd} \\
M_{Rx}-M_{sdx} \\
M_{Ry}-M_{sdy}
\end{bmatrix}=\mathbf 0
$$


---

## Dimensionamento: incógnitas $x,\alpha,A_s$

Conhecidas a geometria, as posições das barras e suas proporções, procura-se a área total de aço. Cada tentativa define deformações, tensões e resultantes. O resultado deve respeitar equilíbrio, admissibilidade das variáveis e coerência das entradas.

$$
\mathbf u_d=(x,\alpha,A_s)
$$

O dimensionamento ajusta três incógnitas para atender às três equações de equilíbrio.

---

## Verificação: incógnitas $x,\alpha,\lambda$

Com $A_s$ conhecida, a verificação procura o estado resistente e o fator de reserva. Força normal e momentos resistentes ficam proporcionais às solicitações.

$$
\mathbf u_v=(x,\alpha,\lambda)
$$

$$
\mathbf R(x,\alpha,A_s)=\lambda\mathbf S_d
$$

O programa resolve três equações para $x$, $\alpha$ e $\lambda$.

---

Na verificação, para uma solução válida do equilíbrio proporcional tem-se:

| Resultado | Interpretação radial |
| :---: | --- |
| $\lambda<1$ | A resistência calculada é inferior à solicitação aplicada |
| $\lambda=1$ | Resistência e solicitação coincidem |
| $\lambda>1$ | A resistência calculada excede a solicitação ao longo do raio adotado |

Essa leitura depende da solução, das convenções de sinal e da hipótese de proporcionalidade. $\lambda$ não substitui verificações normativas ou a análise completa do elemento estrutural.

---

## Da raiz exata à minimização dos resíduos

**Campos Filho (2014)**

A apostila desenvolve o método de Newton–Raphson, que usa a Jacobiana para atualizar a estimativa das incógnitas.

**Pyobliqua**

O programa usa `scipy.optimize.least_squares` para minimizar a função objetivo formada pelos resíduos de equilíbrio:

$$
\min_{\mathbf u}\;\frac{1}{2}\lVert\widetilde{\mathbf r}(\mathbf u)\rVert_2^2
$$

A parada do otimizador, por si só, não garante resíduos suficientemente pequenos.

---

## Escalas, limites e estimativas iniciais

As três equações têm unidades e magnitudes diferentes. O programa normaliza os resíduos de força e momentos antes da minimização.

$$
\widetilde r_i=\frac{R_i-S_i}{s_i}
$$

Limites para as incógnitas e estimativas iniciais ajudam a manter a busca em uma faixa numérica definida.

Conferir `success` e mensagem do solver, norma dos resíduos e tolerância de equilíbrio, além da plausibilidade de $x$, $\alpha$, $A_s$ ou $\lambda$.

</div>

</div>

---

## Newton–Raphson e `least_squares`

| Campos Filho (2014) | Pyobliqua |
|---|---|
| Linearização local do sistema não linear | Minimização da norma dos resíduos |
| Atualização usando a matriz Jacobiana | Jacobiana estimada pelo algoritmo do SciPy, salvo configuração diferente |
| Procura satisfazer diretamente $\mathbf r=0$ | Procura reduzir $\lVert\widetilde{\mathbf r}\rVert$ |
| Convergência depende da estimativa e da regularidade local | Convergência também depende da estimativa, escalas, limites e tolerâncias |

A formulação mecânica é preservada. Muda o procedimento numérico usado para encontrar as incógnitas.

---

## Fluxo computacional do Pyobliqua

1. Ler geometria, barras, materiais e solicitações.
2. Formar o estado de deformação para $(x,\alpha)$.
3. Calcular tensões do concreto e do aço.
4. Integrar as parcelas e transformar os esforços.
5. Avaliar os resíduos normalizados.
6. Atualizar incógnitas até a parada do solver.
7. Verificar equilíbrio e apresentar resultado e visualização.

As etapas de 2 a 6 são repetidas para cada tentativa do solver.

---

## Organização funcional do programa

| Camada | Responsabilidade |
|---|---|
| Geometria | Polígonos, furos, propriedades e barras |
| Materiais | Leis constitutivas do concreto e do aço |
| Análise | Deformações, integração, esforços, equilíbrio e verificação |
| Interação | Estados resistentes para o diagrama $M_x$–$M_y$ |
| Interface | Entradas Tkinter, resultados e visualizações Matplotlib |

A separação permite entender a cadeia de cálculo e localizar cada operação no programa.

---

## Dados e unidades na interface

A interface apresenta dimensões e propriedades geométricas em cm, cm² e cm⁴. Internamente, os módulos de análise usam mm e mm², com tensões em MPa e esforços em N e N·mm.

$$
1\,\text{cm}=10\,\text{mm}, \qquad
1\,\text{cm}^2=100\,\text{mm}^2
$$

Uma conversão incorreta afeta tanto as deformações quanto os braços de alavanca e os esforços.

---

![alt text](image-16.png)

---

## Visualização da seção e do estado resistente

A janela principal associa o resultado numérico à geometria analisada:

- contorno externo e furos;
- posição das barras;
- orientação da linha neutra;
- distribuição de deformações;
- esforços solicitantes e resistentes, quando disponíveis.

O desenho ajuda a detectar erros de entrada e a interpretar o estado de deformação. Ele não substitui a conferência numérica dos resíduos.

---

## Saída do dimensionamento

O modo dimensionamento informa a área total de aço calculada e o estado resistente associado. Itens para apresentar na demonstração:

- geometria e propriedades da seção;
- $x$, $\alpha$ e $A_s$;
- deformações extremas e domínio;
- esforços resistentes e resíduos de equilíbrio;
- visualização da seção.

Uma mensagem de convergência deve ser lida junto da norma dos resíduos e dos dados de entrada.

---

## Saída da verificação

O modo verificação recebe $A_s$ fixa e apresenta $x$, $\alpha$ e $\lambda$.

Na demonstração, destacar:

- armadura fornecida;
- resultantes para o estado calculado;
- fator de reserva;
- norma dos resíduos e estado de convergência;
- interpretação limitada ao equilíbrio proporcional da seção.

---

![alt text](image-15.png)

---

## Diagrama de interação $M_x$–$M_y$

Para $N_{sd}$ e $A_s$ fixos, o programa amostra estados resistentes em orientações da linha neutra.

Na configuração atual da interface, a busca usa 72 orientações angulares e até 100 profundidades por orientação. Os pontos encontrados são mostrados no plano $(M_x,M_y)$, junto da solicitação.

O resultado é uma amostragem numérica. A própria interface alerta que o gráfico não é uma envoltória resistente certificada e que a posição do ponto solicitante não comprova segurança estrutural.

**Captura neste slide (slide 34):** inserir o diagrama $M_x$–$M_y$, destacando a solicitação e os estados resistentes encontrados.

---

## Interpolação radial e seus limites

O programa pode estimar $\lambda$ por interpolação radial entre estados amostrados e o vetor de momentos solicitantes.

Essa estimativa depende da cobertura angular e dos estados encontrados. Se não houver pontos adequados, o programa pode não determinar $\lambda$ por interpolação.

O gráfico e a estimativa são recursos de análise e visualização. Não constituem validação independente nem verificação normativa completa.

---

## Exemplo 5.1: dimensionamento

O exemplo 5.1 da apostila apresenta um caso de dimensionamento. Ele permite percorrer os dados de entrada e acompanhar a saída do programa.

| Dado de entrada | O que acompanhar |
|---|---|
| Geometria e solicitações | Contornos, posição das barras e sinais |
| Armadura proporcional | Conversão das proporções para a área total $A_s$ |
| Resultado | Estado de deformação, equilíbrio e área calculada |

Reproduzir o exemplo é uma comparação com a referência, mas não substitui uma validação numérica independente.

**Figura neste slide (slide 36):** inserir a Fig. 5.1 da apostila, com a seção do exemplo de dimensionamento.

---

## Exemplo 5.2: verificação

O exemplo 5.2 verifica uma seção com área de armadura conhecida. No Pyobliqua, a demonstração acompanha a busca de $x$, $\alpha$ e $\lambda$.

| Dado de entrada | O que acompanhar |
|---|---|
| Geometria e armadura | Posição das barras e área total conhecida |
| Solicitações | Componentes $N_{sd}$, $M_{sdx}$ e $M_{sdy}$ |
| Resultado | Equilíbrio proporcional e fator de reserva |

A comparação ajuda a conferir a implementação do procedimento. Ela não constitui validação independente.

**Figura neste slide (slide 37):** inserir a Fig. 5.2 da apostila, com a seção do exemplo de verificação.

---

## O que a convergência informa

Convergência informa que o procedimento numérico atingiu seus critérios de parada. Para avaliar o resultado, também se observam:

- resíduos nas três equações de equilíbrio;
- tolerância usada para aceitá-los;
- domínio de deformação e limites dos materiais;
- dados e unidades da geometria, armadura e solicitações.

Um otimizador pode parar sem que o equilíbrio esteja atendido. O Pyobliqua separa o estado do SciPy da aceitação baseada nos resíduos.

---

## Estado da validação

**A validação numérica independente ainda não foi realizada.**

Portanto, esta apresentação descreve a formulação, a implementação e o comportamento observado do programa. Não declara o Pyobliqua integralmente validado nem recomenda usar seus resultados sem as verificações técnicas pertinentes.

Próxima etapa de validação: comparar casos selecionados com cálculos independentes, referências publicadas ou soluções de outro procedimento, documentando tolerâncias e diferenças.

---

## Figuras úteis da apostila

| Slides | Assunto | Figura ou tabela de Campos Filho (2014) |
|---:|---|---|
| 4 | Flexão composta oblíqua | Fig. 1.1 |
| 5 | Geometria e furos | Fig. 2.1 |
| 6 | Esforços atuantes | Fig. 2.2 |
| 8 e 10 | Eixos rotacionados e linha neutra | Figs. 2.3 e 2.5 |
| 9 e 10 | Domínios no ELU | Fig. 2.4 e Tabela 2.1 |
| 12, 14, 15 e 16 | Concreto, parâmetros, aço e integração | Figs. 2.6, Tabela 2.2, Fig. 2.7 e Fig. 2.8 |
| 36 e 37 | Exemplos de cálculo | Figs. 5.1 e 5.2 |

As figuras devem ser identificadas com a referência completa e a página correspondente.

---

## Referências e escopo

CAMPOS FILHO, Américo. *Dimensionamento e verificação de seções poligonais de concreto armado submetidas à flexão composta oblíqua*. UFRGS, 2014. Capítulos 1–5 e Anexo A.

ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. *ABNT NBR 6118:2014: Projeto de estruturas de concreto*.

O conteúdo normativo desta apresentação segue a referência de 2014. O programa é apresentado como ferramenta acadêmica em desenvolvimento, com validação numérica independente pendente.
