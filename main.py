from math import radians

from secao.secao import Secao
from secao.barra import Barra

from analise.estado_deformacao import EstadoDeformacao

from materiais.aco import Aco
from materiais.concreto import Concreto


contorno = [
    (0, 0),
    (400, 0),
    (400, 600),
    (0, 600)
]


barras = [
    Barra(40, 40, proporcao=0.25),
    Barra(360, 40, proporcao=0.25),
    Barra(360, 560, proporcao=0.25),
    Barra(40, 560, proporcao=0.25),
]


secao = Secao(
    contorno=contorno,
    barras=barras
)


print(f"A = {secao.area:.2f} mm²")

print(
    f"Centroide = "
    f"({secao.xc:.2f}, {secao.yc:.2f}) mm"
)

print(f"Ix = {secao.Ix:.3e} mm⁴")
print(f"Iy = {secao.Iy:.3e} mm⁴")
print(f"Ixy = {secao.Ixy:.3e} mm⁴")


alfa = radians(30)


print("\nCoordenadas das barras:")

for barra in secao.barras:

    xi, eta = secao.coordenadas_rotacionadas(
        barra.posicao,
        alfa
    )

    print(
        f"ξ = {xi:8.2f} mm   "
        f"η = {eta:8.2f} mm"
    )


estado = EstadoDeformacao(
    secao=secao,
    x=300.0,
    alfa=radians(0)
)


print(f"h = {estado.h:.2f} mm")
print(f"d = {estado.d:.2f} mm")

print(f"Domínio = {estado.dominio}")

print(
    f"εS = {estado.epsilon_s * 1000:.4f} ‰"
)

print(
    f"εI = {estado.epsilon_i * 1000:.4f} ‰"
)


print("\nArmaduras:")

for i, barra in enumerate(
    secao.barras,
    start=1
):
    epsilon = estado.deformacao_barra(barra)

    print(
        f"Barra {i}: "
        f"ε = {epsilon * 1000:.4f} ‰"
    )


concreto = Concreto(fck=30)

deformacoes = [
    0.001,
    0.0,
    -0.001,
    -0.002,
    -0.003,
    -0.0035
]

for epsilon in deformacoes:
    sigma = concreto.tensao(epsilon)

    print(
        f"ε = {epsilon * 1000:6.2f} ‰ "
        f"→ σ = {sigma:8.3f} MPa"
    )

print(concreto.fcd)
print(concreto.sigma_cd)

aco = Aco(fyk=500)

for i, barra in enumerate(
    secao.barras,
    start=1
):
    epsilon = estado.deformacao_barra(barra)

    sigma = aco.tensao(epsilon)

    print(
        f"Barra {i}: "
        f"ε = {epsilon * 1000:.4f} ‰   "
        f"σ = {sigma:.2f} MPa"
    )
    
    from analise.integracao import segmentos_rotacionados


segmentos = segmentos_rotacionados(
    secao,
    secao.contorno,
    estado
)


for i, (p1, p2, regiao) in enumerate(
    segmentos,
    start=1
):

    print(
        f"Segmento {i}: "
        f"{p1} -> {p2} | "
        f"{regiao.name}"
    )

estado = EstadoDeformacao(
    secao,
    x=300,
    alfa=radians(30)
)

from analise.integracao import G


vertices = [
    (0, 0),
    (400, 0),
    (400, 600),
    (0, 600)
]


def integral_poligono(p, q, vertices):

    resultado = 0.0
    n = len(vertices)

    for i in range(n):

        p1 = vertices[i]
        p2 = vertices[(i + 1) % n]

        resultado += G(p, q, p1, p2)

    return resultado


for p, q in [
    (0, 0),
    (1, 0),
    (0, 1),
    (2, 0),
    (0, 2),
    (1, 1)
]:
    print(
        f"G({p},{q}) = "
        f"{integral_poligono(p, q, vertices):.4e}"
    )
    
    
    from math import radians

from analise.estado_deformacao import EstadoDeformacao
from analise.integracao import separar_regioes, integrar_poligono


estado = EstadoDeformacao(
    secao=secao,
    x=300.0,
    alfa=radians(0)
)

vertices = [
    secao.coordenadas_rotacionadas(p, estado.alfa)
    for p in secao.contorno.vertices
]

regiao_I, regiao_II = separar_regioes(
    vertices,
    estado
)

area_I = integrar_poligono(regiao_I, 0, 0)
area_II = integrar_poligono(regiao_II, 0, 0)

print(f"Área região I = {area_I:.2f} mm²")
print(f"Área região II = {area_II:.2f} mm²")
print(f"Área comprimida = {area_I + area_II:.2f} mm²")
    
    
from math import radians, cos, sin

alfa = radians(30)

Mr_xi = 100.0
Mr_eta = 50.0

Mrx = Mr_xi * cos(alfa) - Mr_eta * sin(alfa)
Mry = Mr_xi * sin(alfa) + Mr_eta * cos(alfa)

print(f"Mrx = {Mrx:.3f} kN.m")
print(f"Mry = {Mry:.3f} kN.m")


from math import radians, degrees

from analise.equilibrio import resolver_equilibrio


# Esforços solicitantes
Nsd = -1000e3       # N
Msdx = 150e6        # N.mm
Msdy = 80e6         # N.mm

# Estimativas iniciais
x0 = 300.0
alfa0 = radians(30)
As0 = 2000.0

resultado = resolver_equilibrio(
    secao=secao,
    concreto=concreto,
    aco=aco,
    Nsd=Nsd,
    Msdx=Msdx,
    Msdy=Msdy,
    x0=x0,
    alfa0=alfa0,
    As0=As0
)


from math import degrees
import numpy as np

print("\n--- Resultado da otimização ---")

print("Convergência:", resultado.success)
print("Mensagem:", resultado.message)

x, alfa, As = resultado.x

print(f"x = {x:.4f} mm")
print(f"alfa = {degrees(alfa):.4f}°")
print(f"As = {As:.4f} mm²")

print("\nResíduos normalizados:")
print(resultado.fun)

print(
    "Norma dos resíduos:",
    np.linalg.norm(resultado.fun)
)

print("Número de avaliações:", resultado.nfev)







#if resultado.success:
#
#    x, alfa, As = resultado.x
#
#    print(f"x = {x:.2f} mm")
#    print(f"alfa = {degrees(alfa):.2f}°")
#    print(f"As = {As:.2f} mm²")
#
#else:
#    print("Não houve convergência.")
#    print(resultado.message)