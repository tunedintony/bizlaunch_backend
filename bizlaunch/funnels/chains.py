import base64

from decouple import config
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI

from bizlaunch.funnels.models import PageImage

api_key = config("OPENAI_API_KEY")


def create_adcopy_chain():
    # System prompt template
    SYSTEM_PROMPT = """You are an expert advertising copywriter. Analyze the provided webpage image and user instructions to generate compelling ad copy.

    Output Format:
    - Return the copy in clear sections using markdown-style headers
    - Each section should address a specific component from the page
    - Include both textual and visual analysis insights
    - Maintain brand voice specified in the instructions

    Example Response:
    ### Main Headline
    Experience the Future of Fitness

    ### Hero Section
    Our state-of-the-art equipment and personalized training programs are designed to help you achieve your goals faster.

    ### Call-to-Action
    Join us today and transform your fitness journey. Click below to get started."""

    def prepare_messages(data: dict):
        return [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": f"User Instructions:\n{data['instructions']}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{data['image_base64']}",
                            "detail": "auto",
                        },
                    },
                ]
            ),
        ]

    # Chain construction
    # prompt = ChatPromptTemplate.from_messages(
    #     [
    #         ("system", SYSTEM_PROMPT),
    #         (
    #             "human",
    #             [
    #                 {"type": "text", "text": "User Instructions:\n{instructions}"},
    #                 {
    #                     "type": "image_url",
    #                     "image_url": "{image_data}",
    #                 },
    #             ],
    #         ),
    #     ]
    # )

    return (
        RunnableLambda(prepare_messages)
        | ChatOpenAI(model="gpt-4o", api_key=api_key)
        | StrOutputParser()
    )


# def generate_ad_copy(context):
#     image_bytes = context.get("image", "")
#     client_data = context.get("client_data", "")

#     image_base64 = base64.b64encode(image_bytes).decode("utf-8")

#     chain = create_adcopy_chain()
#     return chain.invoke(
#         {
#             "image_base64": image_base64,
#             "instructions": client_data,
#         }
#     )


def generate_ad_copy(instructions: str, file_content=None):
    """Generate ad copy from image file and instructions"""
    try:
        chain = create_adcopy_chain()
        return chain.invoke(
            {"image_base64": file_content, "instructions": instructions}
        )

    except Exception as e:
        import traceback

        traceback.print_exc
        return f"Error processing image: {str(e)}"


def main():
    # file_path = "fixtures/funnels/digital_product_launchpad/optin.png"
    pages = PageImage.objects.all().order_by("order")
    instructions = "Client is a premium yoga studio targeting working professionals. Use calm, rejuvenating tone."

    for page in pages:
        result = generate_ad_copy(instructions, file_content=page.image_content)
        print(result)


if __name__ == "__main__":
    main()
