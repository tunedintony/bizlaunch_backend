from decouple import config
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai.chat_models import ChatOpenAI
from pydantic import BaseModel

from bizlaunch.funnels.chains.utils import build_prompt


def create_ad_copy_chain(parser: BaseModel):
    model = ChatOpenAI(
        model="gpt-4o", temperature=0.2, api_key=config("OPENAI_API_KEY")
    )
    # Get format instructions once during chain creation
    format_instructions = parser.get_format_instructions()

    chain = (
        RunnableLambda(
            lambda x: build_prompt(
                x["funnel_data"],
                x["qa_pairs"],
                format_instructions,
            )
        )
        | model
        | parser
    )
    return chain
