from collections import defaultdict
import re

def _natural_sort_key(s: str):
    m = re.match(r'([^\d]*)(\d+)$', s)
    if m:
        return (m.group(1), int(m.group(2)))
    return (s, 0)

def _make_circle_lines(label: str, double: bool=False):
    """
    Retorna 5 linhas representando um "círculo" ASCII/Unicode com label centrado dentro.
    Se double=True, desenha um anel interno para indicar estado final.
    """
    L = len(label)
    W = max(7, L + 6)   # largura mínima
    inner = W - 4
    if inner < L:
        inner = L
        W = inner + 4

    if not double:
        line0 = " " + "." + "-"*(inner) + "." + " "
        line1 = " /" + " "*(inner) + "\\ "
        line2 = "| " + label.center(inner) + " |"
        line3 = " \\" + " "*(inner) + "/ "
        line4 = " " + "`" + "-"*(inner) + "'" + " "
    else:
        inner2 = max(L, inner - 4)
        # outer top
        line0 = " " + "." + "-"*(inner) + "." + " "
        # inner top
        pad = inner - inner2
        leftpad = pad // 2
        rightpad = pad - leftpad
        line1 = "/" + " " * leftpad + "." + "-"*(inner2) + "." + " " * rightpad + "\\"
        label_center = label.center(inner2)
        line2 = "| " + "(" + label_center + ")" + " |"
        line3 = "\\" + " " * leftpad + "`" + "-"*(inner2) + "'" + " " * rightpad + "/"
        line4 = " " + "`" + "-"*(inner) + "'" + " "
    return [line0, line1, line2, line3, line4]

def _ensure_canvas_size(canvas, r, c):
    # garante que canvas tem pelo menos r+1 linhas e c+1 colunas
    if r < 0 or c < 0:
        return False
    # linhas
    while r >= len(canvas):
        # estende com mesma largura das linhas existentes ou largura 0
        width = len(canvas[0]) if canvas else 0
        canvas.append(list(" " * width))
    # colunas
    if not canvas:
        canvas.append(list(" " * (c+1)))
    if c >= len(canvas[0]):
        neww = c + 1
        for i in range(len(canvas)):
            canvas[i].extend([" "] * (neww - len(canvas[i])))
    return True

def _cell_empty(canvas, r, c):
    if r < 0 or c < 0:
        return False
    if r >= len(canvas) or c >= len(canvas[r]):
        return True
    return canvas[r][c] == " "

def _write_char_safe(canvas, r, c, ch):
    """
    Escreve ch em (r,c) apenas se a célula atual for ' ' (espaço).
    Se a célula estiver ocupada, retorna False e não sobrescreve.
    Garante expansão do canvas.
    """
    _ensure_canvas_size(canvas, r, c)
    if canvas[r][c] == " ":
        canvas[r][c] = ch
        return True
    return False

def _write_str_safe(canvas, r, c, text):
    """
    Tenta escrever text em (r,c) respeitando células ocupadas.
    Se encontrar ocupação, falha e retorna False (não faz escrita parcial).
    Garante expansão.
    """
    if r < 0:
        return False
    # garanta espaço
    _ensure_canvas_size(canvas, r, c + len(text) - 1)
    # checa se todas células estão vazias
    for i, ch in enumerate(text):
        if canvas[r][c + i] != " ":
            return False
    # escreve
    for i, ch in enumerate(text):
        canvas[r][c + i] = ch
    return True

def _place_label_freely(canvas, start_row, preferred_col, text, min_row=0, max_row=None):
    """
    Tenta colocar text começando na preferred_col dentro das linhas start_row, start_row-1, ...
    até min_row (subindo) e tenta deslocar horizontalmente se necessário.
    Retorna (row,col) se conseguiu e escreve no canvas, senão None.
    Esta função tenta preservar já-desenhado.
    """
    if max_row is None:
        max_row = len(canvas) - 1
    #tentativa vertical: start_row, start_row-1, ..., min_row
    for r in range(start_row, min_row - 1, -1):
        # tentativa direta
        if _write_str_safe(canvas, r, preferred_col, text):
            return (r, preferred_col)
        # tente deslocar esquerda / direita dentro de uma faixa
        max_shift = 10
        for shift in range(1, max_shift+1):
            for dir in (-1, 1):
                c = preferred_col + dir * shift
                if c < 0:
                    continue
                if _write_str_safe(canvas, r, c, text):
                    return (r, c)
    return None

def render_automaton_unicode(automaton):
    """
    Desenha autômato com círculos multilinha com rótulo dentro.
    Setas entre estados evitam sobrepor os blocos dos estados.
    Rótulos na forma (read,pop,push).
    """
    # ordena estados naturalmente
    try:
        states = sorted(list(automaton.states), key=_natural_sort_key)
    except Exception:
        states = sorted(list(automaton.states))

    # gerar arte de cada estado
    state_art = {}
    widths = {}
    for s in states:
        is_final = s in automaton.final_states
        lines = _make_circle_lines(s, double=is_final)
        state_art[s] = lines
        widths[s] = len(lines[0])

    # offsets horizontais (coluna inicial de cada bloco)
    spacing = 6
    offsets = {}
    cur = 0
    for s in states:
        offsets[s] = cur
        cur += widths[s] + spacing
    total_width = max(cur - spacing, 0) if states else 0
    total_height = 5  # altura do bloco do círculo

    # canvas com linhas extras acima para loops/labels
    extra_top = 6
    canvas_height = extra_top + total_height + 2
    canvas = [list(" " * max(total_width, 40)) for _ in range(canvas_height)]

    top_row = extra_top  # onde começa o bloco do círculo

    # desenha blocos dos estados
    for s in states:
        off = offsets[s]
        lines = state_art[s]
        for r, ln in enumerate(lines):
            for c, ch in enumerate(ln):
                _ensure_canvas_size(canvas, top_row + r, off + c)
                # escreve direto (é a arte base)
                canvas[top_row + r][off + c] = ch

    # centros e boundaries dos blocos (colunas)
    centers = {}
    boundaries = {}
    for s in states:
        off = offsets[s]
        W = widths[s]
        left = off
        right = off + W - 1
        center_col = off + W // 2
        center_row = top_row + 2
        centers[s] = (center_col, center_row)
        boundaries[s] = (left, right)

    # agrupa transições por (from,to)
    groups = defaultdict(list)
    for t in automaton.transitions:
        push_str = "".join(t.push) if t.push else "ε"
        label = f"({t.read},{t.pop},{push_str})"
        groups[(t.from_state, t.to_state)].append(label)

    # desenha transições
    # processa self-loops separadamente para reservar posições
    # primeiro desenha todos loops, depois as setas entre estados
    # isso reduz colisões entre loop-labels e arrow-labels
    # --- loops ---
    for (frm, to), labels in groups.items():
        if frm == to:
            if frm not in centers:
                continue
            frm_col, frm_row = centers[frm]
            lbl = " | ".join(labels)
            loop_text = "↶" + lbl
            # posição preferida: linha logo acima do bloco
            preferred_row = top_row - 1
            preferred_col = frm_col - len(loop_text)//2
            # tenta colocar sem sobrescrever
            placed = _place_label_freely(canvas, preferred_row, preferred_col, loop_text, min_row=0)
            if not placed:
                # fallback: escreve nos limites (pode sobrepor)
                r = max(0, preferred_row)
                c = max(0, preferred_col)
                _ensure_canvas_size(canvas, r, c + len(loop_text) - 1)
                for i,ch in enumerate(loop_text):
                    # força escrita (pior caso)
                    canvas[r][c+i] = ch
            # marcador vertical acima do círculo (somente se célula vazia)
            _write_char_safe(canvas, top_row - 0, frm_col, "│")

    # --- arrows entre diferentes estados ---
    for (frm, to), labels in groups.items():
        if frm == to:
            continue
        if frm not in centers or to not in centers:
            continue
        frm_col, frm_row = centers[frm]
        to_col, to_row = centers[to]
        lbl = " | ".join(labels)

        left_bound, right_bound = boundaries[frm]
        left2, right2 = boundaries[to]

        if right_bound + 1 <= left2 - 1:
            start = right_bound + 1
            end = left2 - 1
            arrow_dir = "right"
        elif right2 + 1 <= left_bound - 1:

            start = left2 + 1
            end = right_bound - 1
            arrow_dir = "left"
        else:
            if frm_col < to_col:
                start = right_bound + 1
                end = to_col - 1
                arrow_dir = "right"
            else:
                start = to_col + 1
                end = left_bound - 1
                arrow_dir = "left"

        if arrow_dir == "right":
            for c in range(start, end):
                _write_char_safe(canvas, frm_row, c, "─")
            _write_char_safe(canvas, frm_row, end, "▶")
        else:
            for c in range(start, end):
                _write_char_safe(canvas, frm_row, c, "─")
            _write_char_safe(canvas, frm_row, start, "◀")

        mid = (start + end) // 2
        label_row_preferred = top_row - 1
        label_col_preferred = max(0, mid - len(lbl)//2)
        placed = _place_label_freely(canvas, label_row_preferred, label_col_preferred, lbl, min_row=0)
        if not placed:
            # tentar deslocar horizontalmente com pequenos deslocamentos
            success = False
            for shift in range(1, 12):
                for dir in (-1, 1):
                    c = label_col_preferred + dir * shift
                    if c < 0:
                        continue
                    if _write_str_safe(canvas, label_row_preferred, c, lbl):
                        success = True
                        break
                if success:
                    break
            if not success:
                # fallback: sobrescrever numa linha ainda mais acima
                r = max(0, label_row_preferred - 2)
                c = label_col_preferred
                _ensure_canvas_size(canvas, r, c + len(lbl) - 1)
                for i,ch in enumerate(lbl):
                    canvas[r][c+i] = ch

    # converte canvas em linhas de string removendo espaços finais
    lines_out = ["".join(row).rstrip() for row in canvas]
    header = []
    header.append("== Autômato (desenho) ==")
    header.append(f"Estados (ordem): {', '.join(states)}")
    header.append(f"Inicial: {automaton.initial_state}   Finais: {', '.join(sorted(automaton.final_states))}")
    header.append("")
    return "\n".join(header + lines_out)
