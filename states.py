from aiogram.fsm.state import StatesGroup, State

class TransactionStates(StatesGroup):
    choosing_category = State()
    entering_product = State()
    entering_date = State()
    entering_amount = State()

class ParseStates(StatesGroup):
    waiting_for_input = State()

class DeleteStates(StatesGroup):
    delete_id = State()

class UpdateStates(StatesGroup):
    update_id = State()
    update_field = State()
    updated_field = State()