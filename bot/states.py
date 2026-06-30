from aiogram.fsm.state import State, StatesGroup

class SketchCatalogState(StatesGroup):
    choosing_style = State()
    choosing_sketch = State()
    chat_with_master = State()