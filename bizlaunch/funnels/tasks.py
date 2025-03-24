from celery import shared_task

from .chains import generate_ad_copy, main  # Your LLM integration function
from .models import (
    AdCopy,
    CopyJob,
    PageImage,
    PageTemplate,
    Status,
    SystemFunnelAssociation,
)


@shared_task(bind=True)
def process_copy_job(job_uuid):
    try:
        print(f"Starting processing for CopyJob with UUID: {job_uuid}")
        job = CopyJob.objects.get(uuid=job_uuid)
        print(f"Found CopyJob: {job}")
        job.status = Status.PROCESSING
        job.save()

        # # Get all funnels in the system with their order
        # system_funnels = (
        #     SystemFunnelAssociation.objects.filter(system=job.system)
        #     .select_related("funnel")
        #     .order_by("order_in_system")
        # )
        # print(f"Found {len(system_funnels)} system funnels for system: {job.system}")

        # # Loop through each funnel template in the system
        # for sf in system_funnels:
        #     print(f"Processing funnel: {sf.funnel.name}")
        #     funnel_template = sf.funnel

        #     # Get all pages in the funnel template
        #     pages = funnel_template.pages.order_by("order_in_funnel")
        #     print(f"Found {len(pages)} pages in funnel: {funnel_template.name}")

        #     # Loop through each page in the funnel
        #     for page in pages:
        #         print(f"Processing page: {page.name}")

        #         # Get all images associated with the page
        #         images = page.images.order_by("order")
        #         print(f"Found {len(images)} images for page: {page.name}")

        #         # Process each image
        #         for image in images:
        #             if not image.image_content:
        #                 print(f"Skipping image for page {page.name} as it has no content.")
        #                 continue

        #             # Send image content and client data to the ad copy function
        #             print(f"Generating ad copy for image in page: {page.name}")
        #             result_text = generate_ad_copy(image.image_content, job.client_data)
        pages = PageImage.objects.all().order_by("order")
        instructions = "Client is a premium yoga studio targeting working professionals. Use calm, rejuvenating tone."

        for page in pages:
            result = generate_ad_copy(instructions, file_content=page.image_content)
            print(result)
            # Save the generated text in the AdCopy model
            AdCopy.objects.create(
                copy_job=job,
                page=page.page,  # Use the related PageTemplate instance via reverse lookup
                copy_text=result,  # Save the text received from the function
            )
            print(f"Saved ad copy for image in page: {page.page.name}")

            # Update job status to partially completed after processing each page
            job.status = Status.PARTIALLY_COMPLETED
            job.save()

        # Mark the job as completed after processing all funnels
        job.status = Status.COMPLETED
        job.save()
        print(f"CopyJob {job_uuid} completed successfully.")

    except Exception as e:
        print(f"Error processing CopyJob {job_uuid}: {str(e)}")
        job.status = Status.FAILED
        job.save()
        raise e
