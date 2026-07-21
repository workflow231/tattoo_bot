import os

from services.client_text_service import ClientTextService


class MasterContactService:
    def get_contact_text(self) -> str:
        contact = os.getenv("MASTER_CONTACT", "").strip()
        client_texts = ClientTextService()

        if not contact:
            return client_texts.master_contact_missing()

        return client_texts.master_contact(contact=contact)
