from aiogram.fsm.state import State, StatesGroup


class SketchCatalogState(StatesGroup):
    choosing_style = State()
    choosing_sketch = State()
    sketch_selected = State()
    chat_with_master = State()


class AppointmentState(StatesGroup):
    choosing_date = State()
    choosing_time = State()
    waiting_comment = State()
    confirming = State()


class MyAppointmentsState(StatesGroup):
    choosing_appointment = State()
    viewing_appointment = State()


class ClientCalendarState(StatesGroup):
    viewing_month = State()


class AdminAppointmentState(StatesGroup):
    choosing_filter = State()
    choosing_appointment = State()
    viewing_appointment = State()


class AdminCalendarState(StatesGroup):
    viewing_month = State()
    viewing_day = State()
    choosing_day_off_type = State()
    choosing_slot = State()
    viewing_appointment = State()


class AdminSketchState(StatesGroup):
    choosing_style = State()
    waiting_new_style_name = State()
    waiting_name = State()
    waiting_description = State()
    waiting_price = State()
    waiting_photo = State()
    waiting_status = State()
    waiting_views = State()
    confirming = State()
