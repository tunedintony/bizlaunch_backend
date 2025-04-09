import logging

from celery import shared_task
from django.db import transaction
from langchain_core.output_parsers import PydanticOutputParser

from bizlaunch.funnels.chains.lcel_chain import create_ad_copy_chain
from bizlaunch.funnels.chains.models import DFYFunnel
from bizlaunch.funnels.chains.utils import build_prompt, process_client_csv
from bizlaunch.funnels.models import (
    AdCopy,
    CopyJob,
    FunnelTemplate,
    Project,
    Status,
    SystemFunnelAssociation,
    SystemTemplate,
)

logger = logging.getLogger(__name__)

PARSER_MAP = {
    "digital_product_launchpad": DFYFunnel,
}


def get_funnel_data_for_system(system: SystemTemplate) -> list[dict]:
    """
    Gather all data related to the funnels for a given system and return a list of dictionaries.
    Each dictionary contains funnel-specific data, including pages and their images.

    Args:
        system (SystemTemplate): The system for which to gather funnel data.

    Returns:
        list[dict]: A list of dictionaries containing funnel data.
    """
    funnel_associations = (
        SystemFunnelAssociation.objects.filter(system=system)
        .select_related("funnel")
        .order_by("order_in_system")
    )

    funnel_data_list = []

    for association in funnel_associations:
        funnel = association.funnel

        # Build funnel-specific data
        funnel_data = {
            "name": funnel.name,
            "description": funnel.description,
            "pages": [],
        }

        # Get pages with prefetched images
        pages = funnel.pages.prefetch_related("images").all()
        for page in pages:
            page_data = {
                "uuid": str(page.uuid),
                "name": page.name,
                "description": page.description,
                "layout": page.layout,
                "images": [],
            }

            for image in page.images.all():
                page_data["images"].append(
                    {
                        "uuid": str(image.uuid),
                        "image_content": image.image_content,
                        "components": image.components,
                        "order": image.order,
                    }
                )

            funnel_data["pages"].append(page_data)

        funnel_data_list.append(funnel_data)

    return funnel_data_list


@shared_task
def process_copy_job_task(project_uuid: str):
    """
    Task to process a copy job for a given project. This function handles error handling,
    invokes the chain for ad copy generation, and updates the copy job status.

    Args:
        project_uuid (str): The UUID of the project to process.
    """
    try:
        with transaction.atomic():
            project = Project.objects.select_related("copy_job").get(uuid=project_uuid)
            copy_job = project.copy_job

            copy_job.status = Status.PROCESSING
            copy_job.save(update_fields=["status"])

            # Process client data
            if copy_job.client_file:
                csv_content = copy_job.client_file.read()
                client_context = process_client_csv(csv_content)
                copy_job.client_data = client_context.model_dump()
                copy_job.save(update_fields=["client_data"])

            # Get system and its funnels data
            system = copy_job.system
            funnel_data_list = get_funnel_data_for_system(system)

            # Get parser model for the system
            parser_model = PARSER_MAP.get(
                system.name.lower().replace(" ", "_"), DFYFunnel
            )
            parser = PydanticOutputParser(pydantic_object=parser_model)

            # Process each funnel separately
            for funnel_data in funnel_data_list:
                try:
                    # Create and run chain for this funnel
                    chain = create_ad_copy_chain(parser)
                    result = chain.invoke(
                        {
                            "funnel_data": funnel_data,
                            "qa_pairs": copy_job.client_data.get("qa_pairs", []),
                        }
                    )

                    # Save the generated ad copy
                    AdCopy.objects.create(
                        copy_job=copy_job,
                        funnel=FunnelTemplate.objects.filter(
                            name=funnel_data["name"]
                        ).first(),
                        copy_json=result.model_dump_json(),
                    )
                except Exception as e:
                    logger.error(
                        f"Error processing funnel {funnel_data['name']}: {str(e)}"
                    )
                    continue  # Skip to the next funnel

            # Update copy job status to completed
            copy_job.status = Status.COMPLETED
            copy_job.save(update_fields=["status"])

    except Exception as e:
        logger.error(f"Error processing copy job {project_uuid}: {str(e)}")
        copy_job.status = Status.FAILED
        copy_job.save(update_fields=["status"])
        raise
