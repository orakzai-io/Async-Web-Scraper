from .models import ParsedData, LlmExtraction
from .database import SessionLocal
import json


class DataStore:
    def save_parsed_data(self, content: str) -> ParsedData:
        with SessionLocal() as session:
            parsed = ParsedData(Content=content)
            session.add(parsed)
            session.commit()
            session.refresh(parsed)
            return parsed

    def save_llm_extraction(
        self, parsed_data_id: int, json_data: dict, source_url: str
    ) -> LlmExtraction:
        with SessionLocal() as session:
            extraction = LlmExtraction(
                parsed_data_id=parsed_data_id,
                json_data=json.dumps(json_data),
                source_url=source_url,
            )
            session.add(extraction)
            session.commit()
            session.refresh(extraction)
            return extraction

    def get_parsed_data(self, id: int) -> ParsedData | None:
        with SessionLocal() as session:
            return session.get(ParsedData, id)

    def get_all_parsed_data(self) -> list[ParsedData]:
        with SessionLocal() as session:
            return session.query(ParsedData).all()

    def get_llm_extractions_for_parsed(
        self, parsed_data_id: int
    ) -> list[LlmExtraction]:
        with SessionLocal() as session:
            return (
                session.query(LlmExtraction)
                .filter_by(parsed_data_id=parsed_data_id)
                .all()
            )
