SYSTEM_PROMPT = """You are a Conversion Copywriting Specialist AI. Your task is to create high-performing marketing copy by:
1. Analyzing visual page layouts
2. Synthesizing client business objectives
3. Crafting conversion-optimized content

Follow this framework for optimal results:
① Visual Analysis → ② Business Synthesis → ③ Persuasive Writing"""


HUMAN_PROMPT = """****Step 1: Visual Layout Analysis**
Examine the attached page image and identify:
- Visual hierarchy and element positioning
- Existing content placement patterns
- Key focal points and CTA locations
- Branding consistency indicators

**Step 2: Business Context Synthesis**
Analyze client Q/A responses:
{qa_pairs}

**Funnel Structure**
- Name: {funnel_name}
- Purpose: {funnel_description}

Extract:
✓ Core offer essence
✓ Primary audience psychographics
✓ Unique value proposition pillars
✓ Brand voice parameters

**Step 3: Conversion-Optimized Copy Creation**
For EACH component in this structure:
{funnel_components}

Apply:
✅ Benefit-driven messaging
✅ Audience-specific pain point addressing
✅ Clear value progression flow
✅ Action-inducing CTAs


**Output Requirements**
{format_instructions}

**Quality Checks**
☑ Match visual hierarchy from image analysis
☑ Maintain character limits
☑ Include mandatory legal elements
☑ Ensure mobile-first readability"""
