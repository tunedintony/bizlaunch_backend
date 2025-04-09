import csv
from io import StringIO
from typing import Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from bizlaunch.funnels.chains.models import ClientContext, DFYFunnel, QAPair
from bizlaunch.funnels.chains.prompts import HUMAN_PROMPT, SYSTEM_PROMPT


def clean_text(text: str) -> str:
    """Basic text cleaning preserving essential formatting"""
    return (
        text.replace("\u2028", "\n")  # Replace line separators
        .replace("\u00a0", " ")  # Replace non-breaking spaces
        .replace("\ufeff", "")  # Remove BOM
        .strip()
    )


def process_client_csv(csv_content: bytes) -> ClientContext:
    """Process CSV while preserving original Q/A structure"""
    # Decode and clean BOM if present
    content = csv_content.decode("utf-8-sig")

    # Read CSV using DictReader
    reader = csv.DictReader(StringIO(content))
    row = next(reader)  # Get first row

    # Filter out metadata columns
    ignore_columns = {
        "Created By",
        "Created On",
        "Updated By",
        "Updated On",
        "Need Help on This Form?",
        "▶️ Tutorial Video",
        "Task Name",
        "Due Date",
        "Assignees",
    }

    # Collect Q/A pairs
    qa_pairs = []
    for header in reader.fieldnames:
        if header not in ignore_columns and header.strip() != "":
            answer = row.get(header, "").strip()
            if answer:
                qa_pairs.append(
                    QAPair(question=header.strip(), answer=clean_text(answer))
                )

    return ClientContext(qa_pairs=qa_pairs)


def format_components(funnel_data: Dict) -> str:
    """Structure funnel components with hierarchy"""
    components_by_page = {}
    for page in funnel_data["pages"]:
        components = []
        for image in page["images"]:
            for comp in image["components"]:
                components.append(
                    f"▸ {comp['section']} » {comp['component']}\n"
                    f"   - Purpose: {comp['description']}"
                )
        components_by_page[page["name"]] = "\n".join(components)

    return "\n\n".join(
        f"**{page_name} Components**\n{comps}"
        for page_name, comps in components_by_page.items()
    )


def format_qa(qa_pairs: List[Dict]) -> str:
    """Structure Q/A pairs for context"""
    return "\n".join(f"🔹 **{qa['question']}**\n{qa['answer']}\n" for qa in qa_pairs)


def build_prompt(funnel_data: Dict, qa_pairs: List[Dict], format_instructions: str):
    """Construct multimodal prompt with images"""
    system_msg = SystemMessage(content=SYSTEM_PROMPT)

    formatted_human = HUMAN_PROMPT.format(
        qa_pairs=qa_pairs,
        funnel_name=funnel_data["name"],
        funnel_description=funnel_data["description"],
        funnel_components=format_components(funnel_data),
        format_instructions=format_instructions,  # Add format instructions
    )

    messages = [{"type": "text", "text": formatted_human}]

    for page in funnel_data["pages"]:
        messages.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{page['images'][0]['image_content']}",
                    "detail": "high",
                },
            }
        )

    return ChatPromptTemplate.from_messages(
        [system_msg, HumanMessage(content=messages)]
    )
