from unittest.mock import AsyncMock
from datetime import date, time

import pytest
from sqlalchemy.exc import IntegrityError

from services.admin_appointment_service import AdminAppointmentService


@pytest.mark.anyio
async def test_reject_appointment_rejects_only_pending(monkeypatch) -> None:
    appointment = _appointment(status="confirmed")

    async def fake_find_appointment_by_id(session, appointment_id):
        return appointment

    change_status = AsyncMock()
    monkeypatch.setattr(
        "services.admin_appointment_service.find_appointment_by_id",
        fake_find_appointment_by_id,
    )
    monkeypatch.setattr(
        "services.admin_appointment_service.change_appointment_status",
        change_status,
    )

    result = await AdminAppointmentService(session=None).reject_appointment(
        appointment_id=appointment.id,
    )

    assert result.status == "invalid_status"
    assert "ждёт подтверждения" in result.admin_message
    change_status.assert_not_awaited()


@pytest.mark.anyio
async def test_confirm_appointment_handles_unique_slot_violation(monkeypatch) -> None:
    appointment = _appointment(status="pending")

    async def fake_find_appointment_by_id(session, appointment_id):
        return appointment

    async def fake_exists_confirmed_appointment_for_slot(session, appointment):
        return False

    async def fake_change_appointment_status(session, appointment_id, status):
        raise IntegrityError("statement", {}, Exception("unique"))

    monkeypatch.setattr(
        "services.admin_appointment_service.find_appointment_by_id",
        fake_find_appointment_by_id,
    )
    monkeypatch.setattr(
        "services.admin_appointment_service.exists_confirmed_appointment_for_slot",
        fake_exists_confirmed_appointment_for_slot,
    )
    monkeypatch.setattr(
        "services.admin_appointment_service.change_appointment_status",
        fake_change_appointment_status,
    )

    result = await AdminAppointmentService(session=None).confirm_appointment(
        appointment_id=appointment.id,
    )

    assert result.status == "slot_busy"
    assert result.admin_message == "Этот слот уже занят другой подтверждённой заявкой."


def test_admin_card_formats_custom_sketch_request() -> None:
    appointment = _appointment(status="pending")
    appointment.request_type = "custom_sketch"

    card_text = AdminAppointmentService(session=None).build_admin_card_text(appointment)

    assert "Эскиз: Мой эскиз — цена договорная" in card_text


def _appointment(status: str):
    return type(
        "AppointmentStub",
        (),
        {
            "id": 1,
            "status": status,
            "user": None,
            "sketch": None,
            "request_type": "catalog_sketch",
            "client_sketch_photo_file_id": None,
            "appointment_date": date(2026, 7, 13),
            "appointment_time": time(12, 0),
            "client_comment": None,
        },
    )()
