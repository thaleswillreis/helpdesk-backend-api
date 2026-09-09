"""Motor de cálculo de tempo útil (minutos dentro do expediente configurado)."""

from datetime import datetime, time, timedelta

from app.models.team_schedule import TeamSchedule

WeeklyWindows = dict[int, list[tuple[time, time]]]

_MAX_DAYS_LOOKAHEAD = 3650  # ~10 anos: limite de segurança contra loop infinito

# Sentinela: representa "até a meia-noite do dia seguinte" para turnos que
# cruzam a virada do dia (ex.: 18h às 6h). Não é um horário literal do mesmo
# dia — é resolvido para a meia-noite seguinte no momento do cálculo, evitando
# perda de precisão de 1 microssegundo que um valor como 23:59:59.999999 causaria.
_END_OF_DAY = time(23, 59, 59, 999999)


def expand_schedule(entries: list[TeamSchedule]) -> WeeklyWindows | None:
    """Converte as janelas de expediente cadastradas em um mapa por dia da semana.

    Retorna None se a lista estiver vazia — convenção: equipe sem expediente
    cadastrado funciona 24/7 (sem pausa de SLA).
    Turnos que cruzam a meia-noite (end_time <= start_time) são divididos em
    duas janelas: uma no dia atual (até a meia-noite seguinte) e outra no dia seguinte.
    """
    if not entries:
        return None

    windows: WeeklyWindows = {i: [] for i in range(7)}
    for entry in entries:
        if entry.end_time > entry.start_time:
            windows[entry.weekday].append((entry.start_time, entry.end_time))
        else:
            windows[entry.weekday].append((entry.start_time, _END_OF_DAY))
            next_day = (entry.weekday + 1) % 7
            windows[next_day].append((time(0, 0), entry.end_time))

    for day_windows in windows.values():
        day_windows.sort()

    return windows


def _window_bounds(current_day, w_start: time, w_end: time, tzinfo) -> tuple[datetime, datetime]:
    """Resolve os limites reais de uma janela, tratando o sentinela de fim de dia."""
    window_start = datetime.combine(current_day, w_start, tzinfo=tzinfo)
    if w_end == _END_OF_DAY:
        window_end = datetime.combine(current_day + timedelta(days=1), time.min, tzinfo=tzinfo)
    else:
        window_end = datetime.combine(current_day, w_end, tzinfo=tzinfo)
    return window_start, window_end


def business_minutes_between(start: datetime, end: datetime, windows: WeeklyWindows | None) -> float:
    """Calcula quantos minutos úteis existem entre start e end (windows=None -> 24/7)."""
    if end <= start:
        return 0.0
    if windows is None:
        return (end - start).total_seconds() / 60

    total_seconds = 0.0
    current_day = start.date()
    last_day = end.date()

    while current_day <= last_day:
        weekday = current_day.weekday()
        for w_start, w_end in windows.get(weekday, []):
            window_start, window_end = _window_bounds(current_day, w_start, w_end, start.tzinfo)
            seg_start = max(start, window_start)
            seg_end = min(end, window_end)
            if seg_end > seg_start:
                total_seconds += (seg_end - seg_start).total_seconds()
        current_day += timedelta(days=1)

    return total_seconds / 60


def add_business_minutes(start: datetime, minutes: float, windows: WeeklyWindows | None) -> datetime:
    """Projeta `start` para frente em `minutes` minutos úteis (windows=None -> 24/7)."""
    if minutes <= 0:
        return start
    if windows is None:
        return start + timedelta(minutes=minutes)

    remaining_seconds = minutes * 60
    current_day = start.date()
    cursor = start

    for _ in range(_MAX_DAYS_LOOKAHEAD):
        weekday = current_day.weekday()
        for w_start, w_end in windows.get(weekday, []):
            window_start, window_end = _window_bounds(current_day, w_start, w_end, start.tzinfo)
            seg_start = max(cursor, window_start)
            if seg_start >= window_end:
                continue
            seg_seconds = (window_end - seg_start).total_seconds()
            if seg_seconds >= remaining_seconds:
                return seg_start + timedelta(seconds=remaining_seconds)
            remaining_seconds -= seg_seconds
            cursor = window_end

        current_day += timedelta(days=1)
        cursor = datetime.combine(current_day, time.min, tzinfo=start.tzinfo)

    raise RuntimeError(
        "Não foi possível calcular o prazo: equipe sem nenhuma janela de expediente válida."
    )