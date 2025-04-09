from typing import List, Optional, Tuple

from pydantic import BaseModel, Field


class QAPair(BaseModel):
    question: str
    answer: str


class ClientContext(BaseModel):
    qa_pairs: List[QAPair] = Field(
        description="Raw list of questions and answers from the submission form"
    )


# -------------------------------
# Models for the "Optin Page"
# -------------------------------


class HeroSectionOptin(BaseModel):
    Main_Headline: str = Field(..., alias="Main Headline")
    Subheadline: str
    Call_to_Action: str = Field(..., alias="Call to Action")


class LeadSubsection(BaseModel):
    Subheading: str
    Headline: str
    Body_Text: str = Field(..., alias="Body Text")
    Call_to_Action: str = Field(..., alias="Call to Action")


class OptinPage(BaseModel):
    Announcement_Bar: str = Field(..., alias="Announcement Bar")
    Hero_Section: HeroSectionOptin = Field(..., alias="Hero Section")
    Lead_Subsection: LeadSubsection = Field(..., alias="Lead Subsection")
    Footer_Legal: str = Field(..., alias="Footer Legal")


# -------------------------------
# Models for the "VSL Page"
# -------------------------------


class HeroSectionVSL(BaseModel):
    Headline: str
    Subheadline: str
    Video_Placeholder: str = Field(..., alias="Video Placeholder")
    Call_to_Action: str = Field(..., alias="Call to Action")


class FormSurveySection(BaseModel):
    Subheading: str
    Form_Fields: str = Field(..., alias="Form Fields")
    Call_to_Action: str = Field(..., alias="Call to Action")


class ProfessionalSection(BaseModel):
    Illustration: str
    Heading: str
    Body_Text: str = Field(..., alias="Body Text")
    Call_to_Action: str = Field(..., alias="Call to Action")


class TestimonialGrid(BaseModel):
    Section_Headline: str = Field(..., alias="Section Headline")
    Section_Subheadline: str = Field(..., alias="Section Subheadline")
    Testimonial_Placeholders: str = Field(..., alias="Testimonial Placeholders")


class NegotiationSkillsSection(BaseModel):
    Heading: str
    Body_Text: str = Field(..., alias="Body Text")
    Call_to_Action: str = Field(..., alias="Call to Action")


class FeatureGrid(BaseModel):
    Headline: str
    Feature_Boxes: List[str] = Field(..., alias="Feature Boxes")
    Call_to_Action: str = Field(..., alias="Call to Action")


class FinalCTASection(BaseModel):
    Headline: str
    Body_Text: str = Field(..., alias="Body Text")
    Illustration: str
    Call_to_Action: str = Field(..., alias="Call to Action")


class VSLPage(BaseModel):
    Hero_Section: HeroSectionVSL = Field(..., alias="Hero Section")
    Form_Survey_Section: Optional[FormSurveySection] = Field(
        None, alias="Form/Survey Section"
    )
    Professional_Section: Optional[ProfessionalSection] = Field(
        None, alias="Professional Section"
    )
    Testimonial_Grid: Optional[TestimonialGrid] = Field(None, alias="Testimonial Grid")
    Negotiation_Skills_Section: Optional[NegotiationSkillsSection] = Field(
        None, alias="Negotiation/Skills Section"
    )
    Feature_Grid: Optional[FeatureGrid] = Field(None, alias="Feature Grid")
    Final_CTA_Section: Optional[FinalCTASection] = Field(
        None, alias="Final CTA Section"
    )
    Footer_Legal: str = Field(..., alias="Footer Legal")


# -------------------------------
# Models for the "Calendar Page"
# -------------------------------


class HeadlineSectionCalendar(BaseModel):
    Main_Headline: str = Field(..., alias="Main Headline")
    Subheadline: str


class CalendarSection(BaseModel):
    Scheduling_Title: str = Field(..., alias="Scheduling Title")
    Select_a_Date_and_Time_Label: str = Field(..., alias="Select a Date & Time Label")
    Bullet_Points: List[str] = Field(..., alias="Bullet Points")


class CalendarPage(BaseModel):
    Announcement_Bar: str = Field(..., alias="Announcement Bar")
    Headline_Section: HeadlineSectionCalendar = Field(..., alias="Headline Section")
    Calendar_Section: CalendarSection = Field(..., alias="Calendar Section")
    Footer_Legal: str = Field(..., alias="Footer Legal")


# -------------------------------
# Models for the "TY Booked" page
# -------------------------------


class AppointmentConfirmationSection(BaseModel):
    Main_Heading: str = Field(..., alias="Main Heading")
    Supportive_Subheading: str = Field(..., alias="Supportive Subheading")


class VideoSection(BaseModel):
    Video_Placeholder: str = Field(..., alias="Video Placeholder")


class LearningSection(BaseModel):
    Section_Headline: str = Field(..., alias="Section Headline")
    Body_Text: str = Field(..., alias="Body Text")
    Warning_Note: str = Field(..., alias="Warning Note")


class TYBookedPage(BaseModel):
    Appointment_Confirmation_Section: AppointmentConfirmationSection = Field(
        ..., alias="Appointment Confirmation Section"
    )
    Video_Section: VideoSection = Field(..., alias="Video Section")
    Learning_Section: LearningSection = Field(..., alias="Learning Section")
    Footer_Legal: str = Field(..., alias="Footer Legal")


# -------------------------------
# Done For You Top-Level Ad Copy Model
# -------------------------------


class DFYFunnel(BaseModel):
    Optin_Page: OptinPage = Field(..., alias="Optin Page")
    VSL_Page: VSLPage = Field(..., alias="VSL Page")
    Calendar_Page: CalendarPage = Field(..., alias="Calendar Page")
    TY_Booked: TYBookedPage = Field(..., alias="TY Booked")
