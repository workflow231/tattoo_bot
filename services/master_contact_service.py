import os


class MasterContactService:
    def get_contact_text(self) -> str:
        contact = os.getenv("MASTER_CONTACT", "").strip()

        if not contact:
            return (
                "Контакт мастера пока не указан.\n\n"
                "Попробуйте написать позже или дождитесь ответа по заявке."
            )

        return f"Связаться с мастером:\n\n{contact}"
