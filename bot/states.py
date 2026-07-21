from aiogram.fsm.state import State, StatesGroup


class SketchCatalogState(StatesGroup):
    choosing_style = State()
    choosing_sketch = State()
    sketch_selected = State()
    chat_with_master = State()


class BookingState(StatesGroup):
    choosing_action = State()
    choosing_custom_sketch_action = State()
    waiting_custom_sketch_photo = State()


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


class AdminWorkingHoursState(StatesGroup):
    choosing_action = State()
    choosing_weekday = State()
    waiting_date = State()
    waiting_start_time = State()
    waiting_end_time = State()
    waiting_slot_step = State()


class AdminSketchState(StatesGroup):
    choosing_action = State()
    choosing_style_to_delete = State()
    confirming_style_delete = State()
    choosing_style_to_edit = State()
    waiting_style_name = State()
    choosing_sketch_to_delete = State()
    confirming_sketch_delete = State()
    choosing_sketch_to_edit = State()
    choosing_sketch_field = State()
    choosing_sketch_style = State()
    choosing_style = State()
    waiting_new_style_name = State()
    waiting_name = State()
    waiting_description = State()
    waiting_price = State()
    waiting_photo = State()
    waiting_status = State()
    waiting_edit_sketch_name = State()
    waiting_edit_sketch_description = State()
    waiting_edit_sketch_price = State()
    waiting_edit_sketch_photo = State()
    waiting_edit_sketch_status = State()
    confirming = State()
