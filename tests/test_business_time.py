"""Testes do motor de cálculo de tempo útil (Tarefa 4.2)."""

from datetime import UTC, datetime, time

from app.services.business_time import add_business_minutes, business_minutes_between, expand_schedule


def test_24_7_counts_calendar_time_directly() -> None:
    """Sem expediente cadastrado (windows=None), o tempo é corrido (24/7)."""
    start = datetime(2026, 9, 7, 10, 0, tzinfo=UTC)  # segunda-feira
    end = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)

    assert business_minutes_between(start, end, None) == 120


def test_business_hours_excludes_time_outside_window() -> None:
    """Expediente 08h-18h: intervalo que ultrapassa o fim do expediente é cortado."""
    windows = expand_schedule([_schedule_entry(weekday=0, start=time(8, 0), end=time(18, 0))])

    start = datetime(2026, 9, 7, 17, 0, tzinfo=UTC)  # segunda, 17h
    end = datetime(2026, 9, 7, 20, 0, tzinfo=UTC)  # segunda, 20h (fora do expediente)

    assert business_minutes_between(start, end, windows) == 60  # só 17h-18h conta


def test_business_hours_skips_weekend() -> None:
    """Expediente só de segunda a sexta: fim de semana não conta."""
    windows = expand_schedule(
        [_schedule_entry(weekday=i, start=time(8, 0), end=time(18, 0)) for i in range(5)]
    )

    friday_17h = datetime(2026, 9, 11, 17, 0, tzinfo=UTC)
    monday_9h = datetime(2026, 9, 14, 9, 0, tzinfo=UTC)

    # sexta 17h-18h (1h) + segunda 8h-9h (1h) = 2h, sábado/domingo não contam
    assert business_minutes_between(friday_17h, monday_9h, windows) == 120


def test_add_business_minutes_skips_to_next_day() -> None:
    """Projetar prazo além do fim do expediente deve pular para o próximo dia útil."""
    windows = expand_schedule([_schedule_entry(weekday=0, start=time(8, 0), end=time(18, 0))])

    start = datetime(2026, 9, 7, 17, 0, tzinfo=UTC)  # segunda, 17h, 1h antes de fechar

    # Pedindo 3h úteis: 1h ainda hoje (17h-18h) + 2h no dia seguinte (mas segunda é
    # weekday=0 e só cadastramos expediente pra segunda, então cai no próximo weekday=0 = próxima segunda)
    result = add_business_minutes(start, 180, windows)

    assert result == datetime(2026, 9, 14, 10, 0, tzinfo=UTC)  # próxima segunda, 10h


def test_overnight_shift_is_split_across_two_days() -> None:
    """Turno 18h-06h (cruza meia-noite) deve contar corretamente nos dois dias."""
    windows = expand_schedule([_schedule_entry(weekday=0, start=time(18, 0), end=time(6, 0))])

    start = datetime(2026, 9, 7, 23, 0, tzinfo=UTC)  # segunda 23h
    end = datetime(2026, 9, 8, 2, 0, tzinfo=UTC)  # terça 2h

    assert business_minutes_between(start, end, windows) == 180  # 23h-02h = 3h


def _schedule_entry(weekday: int, start: time, end: time):
    from app.models.team_schedule import TeamSchedule

    return TeamSchedule(team_id=1, weekday=weekday, start_time=start, end_time=end)