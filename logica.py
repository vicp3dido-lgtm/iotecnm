"""Lógica de Investigación de Operaciones: costo mínimo y ruta crítica (CPM)."""
from collections import deque

EPS = 1e-9


def fmt(x: float) -> str:
    """40.0 -> '40'   2.5 -> '2.50'"""
    if abs(x - round(x)) < 1e-9 and abs(x) < 1e15:
        return str(int(round(x)))
    return f"{x:.2f}"


# --------------------------------------------------------------------------
# COSTO MÍNIMO
# --------------------------------------------------------------------------
class ProblemaNoBalanceado(ValueError):
    def __init__(self, oferta_total, demanda_total):
        super().__init__(
            f"El problema no está balanceado: oferta total = {fmt(oferta_total)}, "
            f"demanda total = {fmt(demanda_total)}."
        )


def costo_minimo(costos, oferta, demanda, balancear=False):
    """Solución inicial factible por el método de costo mínimo.

    1. Se elige la celda activa de menor costo (empate: la que permita asignar más).
    2. Se asigna min(oferta, demanda) y se actualizan oferta y demanda.
    3. Se cierra la fila (oferta 0) o la columna (demanda 0).
    4. Degeneración (ambas llegan a 0): se cierra SOLO una para conservar m+n-1 celdas básicas.
    """
    if not costos or not costos[0]:
        raise ValueError("Debe haber al menos un origen y un destino.")
    m0, n0 = len(costos), len(costos[0])
    if len(oferta) != m0 or len(demanda) != n0 or any(len(f) != n0 for f in costos):
        raise ValueError("Las dimensiones de los datos no coinciden.")
    if any(c < 0 for f in costos for c in f):
        raise ValueError("Los costos deben ser mayores o iguales a 0.")
    if any(v < 0 for v in list(oferta) + list(demanda)):
        raise ValueError("La oferta y la demanda deben ser mayores o iguales a 0.")

    total_o, total_d = sum(oferta), sum(demanda)
    filas = [f"O{i + 1}" for i in range(m0)]
    cols = [f"D{j + 1}" for j in range(n0)]
    cost = [list(map(float, f)) for f in costos]
    of = list(map(float, oferta))
    de = list(map(float, demanda))
    aviso = None

    if abs(total_o - total_d) > EPS:
        if not balancear:
            raise ProblemaNoBalanceado(total_o, total_d)
        if total_o > total_d:
            dif = total_o - total_d
            de.append(dif)
            for f in cost:
                f.append(0.0)
            cols.append("D*")
            aviso = f"Se agregó el destino ficticio D* con demanda {fmt(dif)} y costo 0."
        else:
            dif = total_d - total_o
            of.append(dif)
            cost.append([0.0] * n0)
            filas.append("O*")
            aviso = f"Se agregó el origen ficticio O* con oferta {fmt(dif)} y costo 0."

    m, n = len(of), len(de)
    asign = [[0.0] * n for _ in range(m)]
    basica = [[False] * n for _ in range(m)]
    fila_act = [True] * m
    col_act = [True] * n
    pasos = []
    total = 0.0

    while any(fila_act) and any(col_act):
        bf = bc = -1
        mejor_c, mejor_q = float("inf"), -1.0
        for i in range(m):
            if not fila_act[i]:
                continue
            for j in range(n):
                if not col_act[j]:
                    continue
                q = min(of[i], de[j])
                c = cost[i][j]
                if bf == -1 or c < mejor_c - EPS or (abs(c - mejor_c) <= EPS and q > mejor_q + EPS):
                    bf, bc, mejor_c, mejor_q = i, j, c, q

        q = min(of[bf], de[bc])
        asign[bf][bc] = q
        basica[bf][bc] = True
        total += q * cost[bf][bc]
        of[bf] -= q
        de[bc] -= q

        of_cero, de_cero = of[bf] <= EPS, de[bc] <= EPS
        n_f, n_c = sum(fila_act), sum(col_act)
        if of_cero and de_cero:
            if n_f > 1:
                fila_act[bf] = False
                nota = (f"Oferta y demanda se agotan a la vez (degeneración): se cierra "
                        f"{filas[bf]} y {cols[bc]} queda activo con 0.")
            elif n_c > 1:
                col_act[bc] = False
                nota = (f"Oferta y demanda se agotan a la vez (degeneración): se cierra "
                        f"{cols[bc]} y {filas[bf]} queda activo con 0.")
            else:
                fila_act[bf] = col_act[bc] = False
                nota = "Última asignación."
        elif of_cero:
            fila_act[bf] = False
            nota = f"Se agota la oferta de {filas[bf]}."
        else:
            col_act[bc] = False
            nota = f"Se satisface la demanda de {cols[bc]}."
        pasos.append({
            "paso": len(pasos) + 1, "origen": filas[bf], "destino": cols[bc],
            "costo": cost[bf][bc], "cantidad": q, "nota": nota,
        })

    return {
        "asignacion": asign, "basica": basica, "costos": cost,
        "filas": filas, "columnas": cols, "costo_total": total, "pasos": pasos,
        "celdas_basicas": sum(sum(f) for f in basica), "celdas_esperadas": m + n - 1,
        "aviso": aviso,
    }


# --------------------------------------------------------------------------
# RUTA CRÍTICA (CPM)
# --------------------------------------------------------------------------
def ruta_critica(actividades):
    """actividades: lista de (id, duracion, [predecesoras]).

    IT = máx(FT de predecesoras)   FT = IT + duración
    FTa = mín(ITa de sucesoras)    ITa = FTa − duración     Holgura = ITa − IT
    """
    if not actividades:
        raise ValueError("Agrega al menos una actividad.")
    n = len(actividades)
    ids = [str(a[0]).strip() for a in actividades]
    for i in ids:
        if not i:
            raise ValueError("Hay una actividad sin identificador.")
    indice = {}
    for k, i in enumerate(ids):
        if i.upper() in indice:
            raise ValueError(f"El identificador '{i}' está repetido.")
        indice[i.upper()] = k
    dur = [float(a[1]) for a in actividades]
    for k, d in enumerate(dur):
        if d < 0 or d != d or d == float("inf"):
            raise ValueError(f"La duración de '{ids[k]}' debe ser un número mayor o igual a 0.")

    pred = [[] for _ in range(n)]
    suc = [[] for _ in range(n)]
    for i, a in enumerate(actividades):
        for p in [str(x).strip() for x in a[2] if str(x).strip()]:
            j = indice.get(p.upper())
            if j is None:
                raise ValueError(f"La actividad '{ids[i]}' tiene una predecesora que no existe: '{p}'.")
            if j == i:
                raise ValueError(f"La actividad '{ids[i]}' no puede ser predecesora de sí misma.")
            if j not in pred[i]:
                pred[i].append(j)
                suc[j].append(i)

    # Orden topológico (Kahn) y detección de ciclos
    grado = [len(pred[i]) for i in range(n)]
    cola = deque(i for i in range(n) if grado[i] == 0)
    orden = []
    while cola:
        u = cola.popleft()
        orden.append(u)
        for v in suc[u]:
            grado[v] -= 1
            if grado[v] == 0:
                cola.append(v)
    if len(orden) < n:
        en_ciclo = [ids[i] for i in range(n) if grado[i] > 0]
        raise ValueError(f"Existen ciclos en las dependencias (revisa: {', '.join(en_ciclo)}).")

    it = [0.0] * n
    ft = [0.0] * n
    for u in orden:
        it[u] = max((ft[p] for p in pred[u]), default=0.0)
        ft[u] = it[u] + dur[u]
    total = max(ft)

    ita = [0.0] * n
    fta = [0.0] * n
    for u in reversed(orden):
        fta[u] = min((ita[s] for s in suc[u]), default=total)
        ita[u] = fta[u] - dur[u]

    holg = [ita[i] - it[i] for i in range(n)]
    crit = [abs(h) < 1e-6 for h in holg]

    def enlazadas(u, v):
        return crit[u] and crit[v] and abs(ft[u] - it[v]) < 1e-6

    rutas = []

    def dfs(u, camino):
        if len(rutas) >= 100:
            return
        camino.append(ids[u])
        sig = [s for s in suc[u] if enlazadas(u, s)]
        if not sig:
            if abs(ft[u] - total) < 1e-6:
                rutas.append(list(camino))
        else:
            for s in sig:
                dfs(s, camino)
        camino.pop()

    for u in orden:
        if crit[u] and abs(it[u]) < 1e-6 and not any(enlazadas(p, u) for p in pred[u]):
            dfs(u, [])

    filas = [{
        "Actividad": ids[i], "Duración": dur[i], "IT": it[i], "FT": ft[i],
        "ITa": ita[i], "FTa": fta[i], "Holgura": holg[i], "Crítica": crit[i],
    } for i in range(n)]
    aristas = [(ids[p], ids[i]) for i in range(n) for p in pred[i]]
    return {
        "filas": filas, "duracion": total, "rutas": rutas,
        "orden": [ids[i] for i in orden], "aristas": aristas,
    }