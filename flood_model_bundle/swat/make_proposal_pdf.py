# -*- coding: utf-8 -*-
"""Project Completion Proposal PDF (forward-looking / to-be-built framing)."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                HRFlowable, ListFlowable, ListItem, Table, TableStyle)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

OUT = r"C:\Users\bube\Documents\projects\flood-risk-portal\Project_Completion_Proposal.pdf"
NAVY=colors.HexColor("#0f2b46"); BLUE=colors.HexColor("#0e4a6e"); GREY=colors.HexColor("#475569")
ss=getSampleStyleSheet()
def St(n,**k): base=k.pop("parent",ss["Normal"]); return ParagraphStyle(n,parent=base,**k)
title=St("t",parent=ss["Title"],fontSize=20,textColor=NAVY,spaceAfter=4,leading=24,alignment=TA_CENTER)
sub  =St("s",fontSize=12,textColor=BLUE,alignment=TA_CENTER,spaceAfter=3,leading=15)
meta =St("m",fontSize=10.5,textColor=GREY,alignment=TA_CENTER,spaceAfter=1)
h1   =St("h1",fontSize=13.5,textColor=colors.white,backColor=NAVY,borderPadding=6,spaceBefore=14,spaceAfter=8,fontName="Helvetica-Bold",leading=17)
h2   =St("h2",fontSize=11.5,textColor=NAVY,spaceBefore=9,spaceAfter=4,fontName="Helvetica-Bold",leading=14)
body =St("b",fontSize=10.3,textColor=colors.HexColor("#1e293b"),leading=15,spaceAfter=6,alignment=TA_JUSTIFY)
chs  =St("ch",fontSize=8.8,textColor=colors.white,fontName="Helvetica-Bold",leading=11)
cl   =St("cl",fontSize=8.8,textColor=colors.HexColor("#1e293b"),leading=11.5)
clb  =St("clb",fontSize=8.8,textColor=colors.HexColor("#1e293b"),leading=11.5,fontName="Helvetica-Bold")
def bl(x): return ListFlowable([ListItem(Paragraph(i,body)) for i in x],bulletType="bullet",leftIndent=13)
def tbl(rows,w):
    t=Table(rows,colWidths=w,repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f1f5f9')]),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    return t

story=[]; sp=lambda h=8: story.append(Spacer(1,h))

# COVER
sp(30)
story.append(Paragraph("PROJECT COMPLETION PROPOSAL", title))
sp(4)
story.append(Paragraph("An Interactive Web-GIS Portal for Flood Risk Analysis and Visualization", sub))
story.append(Paragraph("in Lagos State, Nigeria", sub))
sp(18)
story.append(HRFlowable(width="60%",thickness=0.8,color=colors.HexColor("#cbd5e1"),spaceAfter=12,hAlign="CENTER"))
story.append(Paragraph("<b>Student:</b> Attah Gbubemi David", meta))
story.append(Paragraph("<b>Matriculation Number:</b> 190402060", meta))
story.append(Paragraph("Department of Civil &amp; Environmental Engineering, University of Lagos", meta))
story.append(Paragraph("<b>Supervisor:</b> Dr. Echeta Odinakachukwu", meta))
story.append(Paragraph("Date: 5 July 2026", meta))
sp(18)
story.append(HRFlowable(width="60%",thickness=0.8,color=colors.HexColor("#cbd5e1"),spaceAfter=12,hAlign="CENTER"))
story.append(Paragraph("This document outlines the current standing of the project, a detailed three-week "
 "schedule for its completion, anticipated edge cases and their resolution, and the approach to presenting "
 "results in a form that end users can readily understand.", St("cabs",parent=body,alignment=TA_CENTER)))

story.append(PageBreak())

# 1. INTRO
story.append(Paragraph("1.&nbsp; Project Aim and Objectives", h1))
story.append(Paragraph("The project will deliver an interactive web-GIS portal that (a) maps where flooding "
 "is likely across Lagos State (flood susceptibility and risk) and (b) simulates river flow in the "
 "Ogun River catchment &#8212; the principal fluvial input to the Lagos Lagoon &#8212; using a calibrated "
 "SWAT+ hydrological model. The five objectives are to: (i) assemble a harmonised geospatial data stack; "
 "(ii) build and calibrate a SWAT+ model to NSE&#8805;0.50, R&#178;&#8805;0.60 and PBIAS within &#177;25%, "
 "with three rainfall scenarios; (iii) produce a flood-susceptibility and risk map via AHP multi-criteria "
 "analysis; (iv) develop the interactive web portal; and (v) validate all outputs against defined "
 "thresholds.", body))

# 2. STATUS
story.append(Paragraph("2.&nbsp; Current Standing of the Project", h1))
story.append(Paragraph("The project is completing its preparatory phase. The data sources have been "
 "identified and are being acquired, the methodology has been defined, the modelling tools have been "
 "selected and set up, and the flood-susceptibility mapping approach has been designed. The hydrological "
 "(SWAT+) modelling, calibration and validation, scenario analysis, portal integration, and output "
 "validation remain to be executed over the coming three weeks. The table below states the standing of each "
 "objective.", body))
rows=[[Paragraph("Objective",chs),Paragraph("Standing",chs),Paragraph("Note",chs)]]
for a,b,c in [
 ("(i) Harmonised data stack","In progress","Datasets identified (terrain, land use, soil, rainfall, temperature, rivers); acquisition and harmonisation to a common grid underway."),
 ("(ii) SWAT+ model + 3 scenarios","To be completed (Weeks 1&ndash;2)","Model to be built and calibrated to the targets NSE&#8805;0.50, R&#178;&#8805;0.60, PBIAS within &#177;25%, with baseline, extreme and climate-sensitivity scenarios."),
 ("(iii) AHP susceptibility map","In progress","Multi-criteria approach designed; map to be finalised and validated."),
 ("(iv) Interactive web portal","In progress","Interface under development; to be completed and integrated with the model outputs."),
 ("(v) Validation to thresholds","Pending (Week 2)","SWAT+ (NSE&#8805;0.50) and susceptibility-map (AUC-ROC&#8805;0.75; &#8805;70% of flood points in High/Very-High zones) validation to be performed."),
]:
    rows.append([Paragraph(a,clb),Paragraph(b,cl),Paragraph(c,cl)])
story.append(tbl(rows,[3.5*cm,3.2*cm,9.7*cm]))
sp(4)
story.append(Paragraph("<b>In short:</b> the groundwork is in place and the path to completion is clear. "
 "The three-week schedule below delivers the hydrological model together with its calibration and "
 "validation, the susceptibility-map validation, the end-user presentation layer, and the written report.", body))

# 3. SCHEDULE
story.append(Paragraph("3.&nbsp; Detailed Completion Schedule (Three Weeks)", h1))

story.append(Paragraph("Week 1 &mdash; Assessment, Data Acquisition and Planning (5&ndash;10 July)", h2))
rows=[[Paragraph("Task",chs),Paragraph("Deliverable",chs)]]
for a,b in [
 ("Assess exactly where the project stands; finalise the data inventory and acquire all remaining model inputs (terrain/DEM, daily rainfall, temperature, soil, land use, river network) into a spatially consistent grid.","Complete data stack"),
 ("Install and configure the modelling tools (QGIS + SWAT+); verify the workflow on a short test run.","Configured, tested tools"),
 ("Contact the relevant agencies (LASEMA, NIHSA, NEMA) for a river-flow reference and a flood-location inventory to be used for validation.","Flood-inventory dataset (&#8805;25 points)"),
 ("Write the concrete execution plan: model set-up steps, calibration strategy, and the validation method (overlay analysis, AUC-ROC, confusion matrix).","Written execution plan"),
]:
    rows.append([Paragraph(a,cl),Paragraph(b,clb)])
story.append(tbl(rows,[11.6*cm,4.8*cm]))

story.append(Paragraph("Week 2 &mdash; Core Execution and Development (12&ndash;17 July)", h2))
rows=[[Paragraph("Task",chs),Paragraph("Deliverable",chs)]]
for a,b in [
 ("Delineate the Ogun catchment and its sub-basins from the terrain; define the Hydrologic Response Units (land use &#215; soil &#215; slope).","Delineated catchment + HRUs"),
 ("Load the daily weather and run the SWAT+ model over the study period; sanity-check the water balance.","Baseline model run"),
 ("Calibrate and validate the model to the acceptance thresholds (NSE&#8805;0.50, R&#178;&#8805;0.60, PBIAS &#177;25%) using a split calibration/validation period.","Calibrated + validated model"),
 ("Run the three required rainfall scenarios (baseline, extreme historical, climate sensitivity).","Scenario results"),
 ("Validate the susceptibility map: overlay the flood inventory and compute AUC-ROC, sensitivity/specificity, and % of flood points in High/Very-High zones &#8594; closes Objective (v).","Validated map + metrics"),
 ("Integrate the model outputs into the portal and build the end-user presentation layer (Section 5).","Integrated portal"),
]:
    rows.append([Paragraph(a,cl),Paragraph(b,clb)])
story.append(tbl(rows,[11.6*cm,4.8*cm]))

story.append(Paragraph("Week 3 &mdash; Report Writing and Typesetting (19&ndash;24 July)", h2))
rows=[[Paragraph("Task",chs),Paragraph("Deliverable",chs)]]
for a,b in [
 ("Write Chapter 4 (Results &amp; Discussion): SWAT+ performance, susceptibility-map validation, and scenario outcomes.","Chapter 4"),
 ("Write Chapter 5 (Conclusion &amp; Recommendations).","Chapter 5"),
 ("Typeset and format the full report; final proofread and consistency check across chapters, figures and references.","Complete final report"),
]:
    rows.append([Paragraph(a,cl),Paragraph(b,clb)])
story.append(tbl(rows,[11.6*cm,4.8*cm]))

# 4. EDGE CASES
story.append(Paragraph("4.&nbsp; Anticipated Edge Cases and Resolution Strategies", h1))
story.append(Paragraph("The following edge cases have been anticipated, each with a clear resolution:", body))
rows=[[Paragraph("Edge case / risk",chs),Paragraph("Resolution",chs)]]
for a,b in [
 ("Observed river-discharge data for the Ogun is scarce or gappy (common in Nigeria).","Adopt a recognised data-scarce strategy: calibrate/validate against a trusted modelled/reanalysis river-flow reference and, where obtainable, partial agency records; report performance at the monthly step per Moriasi et al. (2007)."),
 ("Flood-location inventory is sparse or hard to obtain.","Compile from several public sources (NEMA/DTM 2024, LASEMA, NIHSA Outlook, verified media); if fewer than 30 points, supplement with the 2022 flood-extent footprint and report the sample size transparently as a limitation."),
 ("Dry-season / dam-regulated flows are hard to reproduce.","Document as a limitation: the Oyan Dam and tidal backwater are not modelled; calibration targets the rainfall-driven regime."),
 ("Satellite rainfall may be biased versus gauge data.","Bias-check the satellite rainfall against the NiMet monthly record and report the bias magnitude."),
 ("Flat coastal terrain causes delineation errors.","Burn the real river network (HydroRIVERS) into the terrain so the catchment routes correctly; cross-check the basin area against literature."),
 ("Model must be reproducible / not reliant on opaque tools.","Use only free, open-source software and keep a full step-by-step log so the model can be rebuilt and every choice explained independently."),
 ("Portal misread as a dated flood forecast.","Display a prominent disclaimer that the tool is decision-support (where flooding is likely + what-if scenarios), not a forecast of when a flood will occur."),
]:
    rows.append([Paragraph(a,clb),Paragraph(b,cl)])
story.append(tbl(rows,[5.4*cm,11.0*cm]))

# 5. RESULTS PRESENTATION
story.append(Paragraph("5.&nbsp; Communicating Results to End Users", h1))
story.append(Paragraph("A key requirement is that results are understandable to end users (planners, "
 "emergency agencies and the public), not only as raw tables and charts. The following intuitive "
 "presentation methods will be delivered:", body))
story.append(bl([
 "<b>Interactive click-to-query map:</b> a user clicks any location and receives a plain-language risk "
 "statement (e.g. &#8216;High hazard zone &#8212; low elevation, close to a waterway&#8217;), not a table.",
 "<b>Traffic-light risk badges:</b> every location and LGA shown as Low / Moderate / High / Very-High with "
 "intuitive colour coding, so meaning is grasped at a glance.",
 "<b>LGA &#8216;report cards&#8217;:</b> a one-page downloadable summary per Local Government Area &#8212; "
 "its flood-risk class distribution, the extent of its High/Very-High zones, scenario impact and "
 "suggested priority actions.",
 "<b>Plain-language scenario outcomes:</b> the rainfall control states results in words &#8212; e.g. "
 "&#8216;a 20% wetter year expands the High-risk area of this LGA by about Y%&#8217;.",
 "<b>A summary story-map / infographic</b> for non-technical stakeholders (e.g. LASEMA), and an accessible "
 "plain-English explanation of the methodology for transparency.",
]))
story.append(Paragraph("Together these turn the analysis into a decision-support experience rather than a "
 "set of technical outputs, directly satisfying the requirement for end-user clarity.", body))

# 6. OWNERSHIP
story.append(Paragraph("6.&nbsp; Project Ownership and Reproducibility", h1))
story.append(Paragraph("In line with the expectation that the project be genuinely owned rather than reliant "
 "on other people or opaque software:", body))
story.append(bl([
 "<b>Open, transparent tools only:</b> the entire workflow will use free, open-source software (QGIS, "
 "SWAT+, Python) &#8212; no black-box paid tool; every calculation can be inspected and re-run.",
 "<b>Fully reproducible:</b> a complete step-by-step log of every command, file and parameter will be "
 "maintained, so the model can be rebuilt independently from raw data.",
 "<b>Command of the model, not a black box:</b> calibration will be carried out by adjusting "
 "physically-interpretable parameters (percolation, evapotranspiration, groundwater recession) and "
 "re-running the model, so each choice can be explained and justified in the defence.",
 "<b>Demonstrable understanding:</b> a plain-language walkthrough and a live demonstration of the "
 "QGIS + SWAT+ workflow will be prepared, evidencing hands-on mastery of every step.",
]))

# 7. MILESTONES
story.append(Paragraph("7.&nbsp; Summary of Milestones", h1))
rows=[[Paragraph("Milestone",chs),Paragraph("Target date",chs),Paragraph("Phase",chs)]]
for a,b,c in [
 ("Complete data stack + tools configured","10 July","Week 1"),
 ("Flood inventory compiled","10 July","Week 1"),
 ("Catchment delineated + HRUs defined","14 July","Week 2"),
 ("SWAT+ model calibrated &amp; validated","17 July","Week 2"),
 ("Susceptibility map validated (Objective v closed)","17 July","Week 2"),
 ("Portal integrated + end-user presentation delivered","17 July","Week 2"),
 ("Chapters 4 &amp; 5 written; report typeset","24 July","Week 3"),
]:
    rows.append([Paragraph(a,clb),Paragraph(b,cl),Paragraph(c,cl)])
story.append(tbl(rows,[9.4*cm,3.5*cm,3.5*cm]))

SimpleDocTemplate(OUT,pagesize=A4,topMargin=1.6*cm,bottomMargin=1.5*cm,leftMargin=1.8*cm,rightMargin=1.8*cm,
    title="Project Completion Proposal",author="Attah Gbubemi David").build(story)
print("WROTE",OUT)
