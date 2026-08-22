# -*- coding: utf-8 -*-
"""Builds a detailed, illustrated, simple-English explainer PDF (with screenshots + technical detail)."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                HRFlowable, ListFlowable, ListItem, Image as RLImage,
                                KeepTogether, Table, TableStyle)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from PIL import Image as PILImage

OUT = r"C:\Users\bube\Documents\projects\flood-risk-portal\flood_model_bundle\How_I_Built_The_Model_Explained.pdf"
SHOTDIR = r"C:\Users\bube\Pictures\Screenshots"
TMP = r"C:\SWAT_Ogun\pdf_imgs"
os.makedirs(TMP, exist_ok=True)

def shot(num):
    src = os.path.join(SHOTDIR, f"Screenshot ({num}).png")
    im = PILImage.open(src).convert("RGB"); w, h = im.size
    tw = 1200; im.resize((tw, int(h*tw/w))).save(os.path.join(TMP, f"s{num}.jpg"), "JPEG", quality=80)
    dw = 16*cm; return RLImage(os.path.join(TMP, f"s{num}.jpg"), width=dw, height=dw*h/w)

NAVY=colors.HexColor("#0f2b46"); BLUE=colors.HexColor("#0e7490"); GREY=colors.HexColor("#475569")
GREEN=colors.HexColor("#166534"); AMBER=colors.HexColor("#92400e")
ss=getSampleStyleSheet()
def St(n,**k): base=k.pop("parent",ss["Normal"]); return ParagraphStyle(n,parent=base,**k)
title=St("t",parent=ss["Title"],fontSize=24,textColor=NAVY,spaceAfter=6,leading=28)
subt =St("st",fontSize=12.5,textColor=BLUE,alignment=TA_CENTER,spaceAfter=2)
byl  =St("by",fontSize=11,textColor=GREY,alignment=TA_CENTER,spaceAfter=14)
h1   =St("h1",fontSize=15.5,textColor=NAVY,spaceBefore=14,spaceAfter=5,leading=19,fontName="Helvetica-Bold")
step =St("step",fontSize=12.5,textColor=colors.white,backColor=BLUE,borderPadding=6,spaceBefore=12,spaceAfter=6,fontName="Helvetica-Bold",leading=16)
body =St("b",fontSize=10.6,textColor=colors.HexColor("#1e293b"),leading=15.5,spaceAfter=6)
cap  =St("cap",fontSize=9,textColor=GREY,alignment=TA_CENTER,spaceBefore=2,spaceAfter=10,fontName="Helvetica-Oblique")
kid  =St("kid",fontSize=10.2,textColor=colors.HexColor("#0b3d2e"),leading=14.5,spaceAfter=8,backColor=colors.HexColor("#e9f9ef"),borderColor=colors.HexColor("#7fd6a0"),borderWidth=1,borderPadding=7)
demo =St("demo",fontSize=10.2,textColor=colors.HexColor("#7c2d12"),leading=14.5,spaceAfter=8,backColor=colors.HexColor("#fff7ed"),borderColor=colors.HexColor("#fdba74"),borderWidth=1,borderPadding=7)
glo  =St("glo",fontSize=10.2,textColor=colors.HexColor("#1e293b"),leading=14.5,spaceAfter=4)
mono =St("mono",fontName="Courier",fontSize=8.6,textColor=colors.HexColor("#0f172a"),leading=12,backColor=colors.HexColor("#f1f5f9"),borderPadding=6,spaceAfter=8)
cellh=St("ch",fontSize=8.6,textColor=colors.white,fontName="Helvetica-Bold",leading=10.5)
cell =St("cl",fontSize=8.6,textColor=colors.HexColor("#1e293b"),leading=10.8)
cellu=St("cu",fontName="Courier",fontSize=8,textColor=BLUE,leading=10.5)

def K(t): return Paragraph("<b>In simple words:</b> "+t, kid)
def bullets(x): return ListFlowable([ListItem(Paragraph(i,body)) for i in x],bulletType="bullet",leftIndent=14)
def figure(num,c): return KeepTogether([shot(num),Paragraph("My screenshot: "+c,cap)])
def table(rows,widths):
    t=Table(rows,colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f1f5f9')]),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    return t

story=[]; sp=lambda h=8: story.append(Spacer(1,h))

# ===== COVER =====
sp(24)
story.append(Paragraph("How I Built the Lagos Flood Model", title))
story.append(Paragraph("A Detailed, Step-by-Step Explanation (with my own screenshots)", subt))
story.append(Paragraph("simple enough for a 10-year-old, complete enough for my supervisor", subt))
sp(10)
story.append(Paragraph("Attah Gbubemi David &nbsp;•&nbsp; University of Lagos", byl))
story.append(HRFlowable(width="100%",thickness=0.8,color=colors.HexColor("#cbd5e1"),spaceAfter=8))
story.append(Paragraph("This document explains, in plain English, exactly how I built the river-flow model "
 "(the SWAT+ part) and put it in the flood website. It also lists <b>where every piece of data came "
 "from</b> (with free web links you can open live), <b>exactly how the tuning was done</b>, "
 "<b>how the accuracy scores are calculated by hand</b>, and <b>how Python and the website were made</b>. "
 "Every big word is explained, with a dictionary at the end.", body))
story.append(Paragraph("Contents: 1) Big picture &nbsp; 2) The 9 build steps (with screenshots) &nbsp; "
 "3) Where the data came from (+ live demos) &nbsp; 4) The calibration in detail &nbsp; 5) How to "
 "check my scores with a calculator &nbsp; 6) How Python &amp; the website were built &nbsp; 7) Results "
 "&nbsp; 8) A practical example to show your teacher &nbsp; 9) Dictionary.",
 St("toc",parent=body,fontSize=9.8,textColor=GREY)))

# ===== PART 1 =====
story.append(Paragraph("Part 1 — What is this project, and why two models?", h1))
story.append(Paragraph("Lagos floods badly almost every year. My project explains that flooding using "
 "<b>two tools</b> inside <b>one website</b>:", body))
story.append(bullets([
 "<b>A flood map</b> — shows <b>WHERE</b> in Lagos flooding is likely (whole state).",
 "<b>A river model</b> — shows <b>HOW MUCH</b> water flows in the <b>Ogun River</b>, the big river that "
 "carries floodwater into Lagos. <b>This river model is the part I built.</b>"]))
story.append(K("The map is a weather-lady pointing at wet areas. The river model is a smart "
 "water-calculator that says how much water rolls down the river. I built the calculator, proved it "
 "matches the real river, and joined it to the map on one website."))

story.append(PageBreak())
# ===== PART 2: STEPS =====
story.append(Paragraph("Part 2 — Building the river model, step by step", h1))

story.append(Paragraph("Step 1 &nbsp;•&nbsp; Install the free software", step))
story.append(Paragraph("I installed <b>QGIS</b> (a powerful, editable map program) and <b>SWAT+</b> "
 "(the river-model add-on that plugs into QGIS). Both are 100% free. Here is QGIS when it first opened.", body))
story.append(figure(1621,"a fresh, empty QGIS right after installing."))

story.append(Paragraph("Step 2 &nbsp;•&nbsp; Collect the ingredients (data)", step))
story.append(Paragraph("The calculator needs to know the land and weather. I gathered <b>land height, "
 "rivers, daily rain, temperature, soil, and land-cover</b>. Most of the rain and temperature I pulled "
 "with <b>Google Earth Engine</b> (a giant free online satellite library). "
 "The exact sources and free links are listed in <b>Part 3</b>.", body))
story.append(figure(1644,"Google Earth Engine, where I fetched 14 years of rain and temperature."))
story.append(K("A cake needs flour, eggs and sugar. My model needs land-height, rain, soil and "
 "land-cover. Part 3 is my full shopping list with the shops (web links)."))

story.append(Paragraph("Step 3 &nbsp;•&nbsp; Draw the river's catchment", step))
story.append(Paragraph("All the rain over a huge area rolls downhill into one river; that area is the "
 "<b>catchment</b>. The computer found the streams (blue), let me place the <b>outlet</b> (where the "
 "river leaves, near Lagos), then drew the boundary and split it into <b>23 sub-basins</b> (red). Because "
 "the Lagos end is very flat, I gave it the map of real rivers to follow ('burning in' — the purple "
 "lines) so it drew the correct area: about <b>19,915 km²</b>.", body))
story.append(figure(1635,"the finished Ogun catchment — blue = rivers found, red = 23 sub-basins, "
 "purple = the real-river map it followed."))

story.append(Paragraph("Step 4 &nbsp;•&nbsp; Cut the land into small matching pieces (HRUs)", step))
story.append(Paragraph("The computer cut each sub-basin into pieces where <b>soil + land-cover + "
 "steepness are the same</b>. Each piece is an <b>HRU</b>. Keeping only pieces bigger than 10% gave "
 "<b>243 HRUs</b>; the model does its water maths on each one.", body))
story.append(figure(1640,"the 'Create HRUs' window, filtering land pieces by land-use, soil and slope."))

story.append(Paragraph("Step 5 &nbsp;•&nbsp; Feed it the weather", step))
story.append(Paragraph("Two parts: a <b>weather generator</b> (fills in sun, wind, humidity I didn't "
 "measure) plus my <b>real daily rain and temperature</b> — one station per sub-basin. Below, the "
 "generator loaded with 60 nearby weather points.", body))
story.append(figure(1650,"the Weather Generator with 60 weather points around the Ogun basin."))

story.append(Paragraph("Step 6 &nbsp;•&nbsp; Run the model", step))
story.append(Paragraph("I set it to run <b>14 years (2010–2023)</b> and pressed Run. It simulated the "
 "river day by day in about one minute and reported <b>no errors</b>.", body))
story.append(figure(1653,"'All selected tasks have completed' — the model ran successfully."))

story.append(Paragraph("Step 7 &nbsp;•&nbsp; Tune it to match the real river (calibration)", step))
story.append(Paragraph("I compared my model against a trusted real river-flow record (<b>GEOGLOWS</b>) "
 "and adjusted 6 settings until they matched. The <b>full detail is in Part 4</b>, and how the scores "
 "are calculated is in <b>Part 5</b>. Final scores: <b>NSE 0.51, R² 0.61, PBIAS +1.6%</b> — all pass.", body))

story.append(Paragraph("Step 8 &nbsp;•&nbsp; Ask 'what if?' (rainfall scenarios)", step))
story.append(Paragraph("With a working model I asked: what if it rains 10/20/30% more? River water rose "
 "even faster than the rain (10% more rain → ~15% more water; 30% → ~48%) — exactly how real floods behave.", body))

story.append(Paragraph("Step 9 &nbsp;•&nbsp; Put it in the website", step))
story.append(Paragraph("I saved the results and added them to the portal as a new <b>'Hydrology (SWAT+)'</b> "
 "tab. Here is the finished website (note the 7 tabs across the top).", body))
story.append(figure(1661,"the finished 'Lagos Flood Hazard Explorer' — my name and all 7 tabs."))
story.append(figure(1664,"the Exposure page: which Lagos LGAs have the most people in flood zones."))

story.append(PageBreak())
# ===== PART 3: DATA SOURCES =====
story.append(Paragraph("Part 3 — Where I got each dataset (all free) + live demos", h1))
story.append(Paragraph("Every dataset below is <b>free and public</b>. The last column is a web address "
 "you can open to prove it. All the rain/temperature came through <b>Google Earth Engine</b> "
 "(code.earthengine.google.com), a free satellite-data website.", body))
rows=[[Paragraph("Ingredient",cellh),Paragraph("Dataset (the real name)",cellh),Paragraph("Where to get it — free",cellh)]]
for a,b,c in [
 ("Land height (DEM)","Copernicus GLO-30 (30 m)","opentopography.org  (draw a box, download)"),
 ("Rivers","HydroRIVERS / HydroSHEDS","hydrosheds.org"),
 ("Daily rain","CHIRPS  (UCSB-CHG/CHIRPS/DAILY)","via Google Earth Engine  •  data.chc.ucsb.edu"),
 ("Temperature","ERA5-Land  (ECMWF/ERA5_LAND/DAILY_AGGR)","via Google Earth Engine  •  cds.climate.copernicus.eu"),
 ("Soil","SoilGrids 250 m (ISRIC)","soilgrids.org  •  files.isric.org"),
 ("Land cover","ESA WorldCover 10 m","esa-worldcover.org  (has a map viewer)"),
 ("Weather generator","Global SWAT+ WGN (CFSR)","one-click inside SWAT+ Editor  (swat.tamu.edu)"),
 ("Real river flow (to check my model)","GEOGLOWS ECMWF, reach 140585128","geoglows.ecmwf.int  (see live demo below)"),
]:
    rows.append([Paragraph(a,cell),Paragraph(b,cell),Paragraph(c,cellu)])
story.append(table(rows,[3.3*cm,5.0*cm,8.4*cm]))
sp(6)
story.append(Paragraph("<b>Easy live example you can show your supervisor</b> (takes 5 seconds, no login): "
 "open a web browser and type this address —", demo))
story.append(Paragraph("https://geoglows.ecmwf.int/api/v2/retrospective/140585128?format=csv", mono))
story.append(Paragraph("It instantly downloads the <b>real recorded flow of the Ogun River</b> "
 "(daily, from 1940 to today) as a spreadsheet — this is the exact data I checked my model against. "
 "Two more visual demos: open <b>soilgrids.org</b> and click on Lagos to see the soil; open "
 "<b>esa-worldcover.org</b> to see Lagos land-cover.", demo))

# ===== PART 4: CALIBRATION DETAIL =====
story.append(Paragraph("Part 4 — How I did the calibration (the tuning), in detail", h1))
story.append(Paragraph("When the model first ran it was wrong in two ways: it made about <b>30% too much "
 "river water</b>, and in the dry season the river dried to almost nothing (the real river keeps "
 "flowing). To find WHY, I looked at the model's <b>water balance</b> and saw the model was <b>not "
 "evaporating enough</b> — too much rain was becoming river water instead of going back into the air.", body))
story.append(Paragraph("SWAT+ has a settings file called <b>calibration.cal</b>. I changed <b>6 settings</b> "
 "(out of 221 possible) and re-ran until the model matched. Here is exactly what I changed and why:", body))
rows=[[Paragraph("Setting",cellh),Paragraph("What it controls (plain English)",cellh),Paragraph("Change",cellh),Paragraph("Why",cellh)]]
for a,b,c,d in [
 ("perco","How much soil water sinks deep underground","0.90 → 0.30","Keep water near the surface so the sun can evaporate it (cut the extra water)"),
 ("petco","How strongly the sun + plants evaporate water","1.00 → 1.20","Remove the leftover extra water — this fixed the ~30% too-much problem"),
 ("canmx","Rain caught on leaves and evaporated","1 → 12 mm","Trim the wet-season flood peaks a little"),
 ("alpha","How slowly underground water trickles into the river","→ 0.022","Keep the river flowing in the dry season instead of drying up"),
 ("flo_min","How much underground water builds up before feeding the river","→ 10","Store water underground, release slowly (dry-season flow)"),
 ("bf_max","The top speed underground water can feed the river","1.0 → 0.55","Stop the wet-season peaks from being too high"),
]:
    rows.append([Paragraph(a,cellu),Paragraph(b,cell),Paragraph(c,cell),Paragraph(d,cell)])
story.append(table(rows,[1.8*cm,5.6*cm,2.3*cm,7.0*cm]))
sp(6)
story.append(Paragraph("<b>The process (about 10 rounds):</b> change a setting → run the model → measure "
 "the score → decide what to change next. The key discoveries were: (1) surface runoff was tiny — the "
 "flow was almost all underground, so the famous 'curve number' knob did nothing here; (2) <b>perco</b> "
 "was the big lever for the total amount of water; (3) <b>petco</b> (evaporation) fixed the last of the "
 "excess; (4) the underground (<b>alpha, flo_min, bf_max</b>) settings brought the dry-season river back "
 "to life. After the last round: <b>NSE 0.51, R² 0.61, PBIAS +1.6%</b>.", body))
story.append(K("Calibration is like adjusting a stew: too watery, so I let more steam off (evaporate) and "
 "stopped so much draining away; too dry later, so I kept a slow simmer going underneath. Taste, adjust, "
 "taste again — 10 times — until it's right."))

# ===== PART 5: SCORES BY HAND =====
story.append(Paragraph("Part 5 — How the accuracy scores are calculated (by hand)", h1))
story.append(Paragraph("A supervisor can check these with a calculator. For each month you need two "
 "numbers: <b>obs</b> = the real river flow, <b>sim</b> = my model's flow. 'Mean' means average.", body))
story.append(Paragraph("<b>1) PBIAS — is the TOTAL water right?</b>  Add up all the (obs − sim), divide by "
 "the total obs, times 100:", body))
story.append(Paragraph("PBIAS = 100 &#215; (sum of [obs − sim]) &#247; (sum of obs)", mono))
story.append(Paragraph("Near 0% is perfect. Mine was <b>+1.6%</b> — the total water is almost exactly "
 "right. (Under ±25% is the pass mark.)", body))
story.append(Paragraph("<b>2) NSE — how good is the match, month by month?</b>  Compare the model's errors "
 "against simply guessing the average every time:", body))
story.append(Paragraph("NSE = 1 &#8722; (sum of [obs − sim]&#178;) &#247; (sum of [obs − mean-of-obs]&#178;)", mono))
story.append(Paragraph("1.0 = perfect; 0 = no better than always guessing the average; above 0.5 = good. "
 "Mine was <b>0.51</b>.", body))
story.append(Paragraph("<b>Worked example</b> (3 months, so you can do it on a calculator):", body))
story.append(Paragraph(
 "obs = 40, 300, 60   •   sim = 55, 280, 50   •   mean-of-obs = (40+300+60)/3 = 133.3<br/>"
 "top   = (40&#8722;55)&#178; + (300&#8722;280)&#178; + (60&#8722;50)&#178; = 225 + 400 + 100 = 725<br/>"
 "bottom = (40&#8722;133.3)&#178; + (300&#8722;133.3)&#178; + (60&#8722;133.3)&#178; = 8705 + 27789 + 5373 = 41867<br/>"
 "NSE = 1 &#8722; (725 &#247; 41867) = 1 &#8722; 0.017 = <b>0.98</b>", mono))
story.append(Paragraph("<b>3) R² — does the model follow the ups and downs?</b>  This is the square of the "
 "correlation between obs and sim (1.0 = they rise and fall perfectly together). Mine was <b>0.61</b>. "
 "A calculator or Excel's <font face='Courier'>=RSQ(sim, obs)</font> gives it instantly.", body))
story.append(K("NSE asks: 'is my model better than just guessing the average?' (0.98 in the little "
 "example = much better). PBIAS asks: 'is my total right?' R² asks: 'do we go up and down together?' "
 "You can check all three in Excel in two minutes."))

story.append(PageBreak())
# ===== PART 6: PYTHON + WEBSITE =====
story.append(Paragraph("Part 6 — How the model and website were built with Python", h1))
story.append(Paragraph("<b>Was the model 'written in Python'?</b>  Not exactly. SWAT+ is a scientific "
 "program (the river-physics engine) written by researchers. <b>I used Python to CONTROL it "
 "automatically</b>, which is why I could tune it so fast. Instead of clicking 'Run' by hand 10 times, "
 "I wrote a small Python script that does the whole loop:", body))
story.append(bullets([
 "<b>1.</b> write the 6 settings into <font face='Courier'>calibration.cal</font>,",
 "<b>2.</b> run the SWAT+ engine (the <font face='Courier'>.exe</font>) on the model,",
 "<b>3.</b> read the results file and pull out the river flow,",
 "<b>4.</b> calculate NSE, PBIAS and R² against the real river,",
 "<b>5.</b> print the score, so I could decide the next change."]))
story.append(Paragraph("That script is <font face='Courier'>calib.py</font>. A second script, "
 "<font face='Courier'>scenario.py</font>, multiplied the rainfall by 1.1 / 1.2 / 1.3 and re-ran to "
 "measure the 'what-if' floods. Other small Python helpers joined the height-map tiles, sorted the soil "
 "into texture types, built the soil database, and pulled the river data. The weather was fetched by a "
 "short script in Google Earth Engine (<font face='Courier'>gee_weather.js</font>).", body))
story.append(Paragraph("<b>How the website was made.</b>  The website is built with <b>Streamlit</b> — a "
 "free tool that turns a Python script straight into a web page (no separate web-design needed). Two "
 "files do it:", body))
story.append(bullets([
 "<font face='Courier'>model_api.py</font> — the <b>engine</b>. It loads every result (the flood map, "
 "the population numbers, and my SWAT river results saved in <font face='Courier'>swat_results.json</font>) "
 "and hands them out when the page asks.",
 "<font face='Courier'>app.py</font> — the <b>web page</b> itself (~1,160 lines). It lays out the 7 tabs, "
 "draws the maps and charts, and calls the engine for numbers."]))
story.append(Paragraph("To start the website you run one command and it opens in the browser:", body))
story.append(Paragraph("streamlit run app.py        →        opens at  http://localhost:8501", mono))
story.append(K("SWAT+ is the calculator; my Python script is the fast robot hand that presses its buttons "
 "10 times and reads the answers. Streamlit is a tool that turns a plain Python file into a real website "
 "— that is how the 7-tab portal was made."))

# ===== PART 7: RESULTS =====
story.append(Paragraph("Part 7 — Did it work? (results in plain numbers)", h1))
story.append(bullets([
 "<b>NSE = 0.51</b> (target 0.50+) — <b>passed.</b> The model matches the real river.",
 "<b>Fair-test NSE = 0.57</b> on years I did NOT tune on — <b>passed, even better.</b> Not overfit.",
 "<b>PBIAS = +1.6%</b> — total water almost exactly right (target within ±25%).",
 "<b>R² = 0.61</b> — the seasonal pattern is captured well (target 0.60)."]))
story.append(Paragraph("<b>All three targets my project set were met.</b> The river model is calibrated, "
 "validated, and lives in the website beside the flood map.", body))

# ===== PART 8: PRACTICAL DEMO =====
story.append(PageBreak())
story.append(Paragraph("Part 8 — A practical example to show your teacher (exact files &amp; numbers)", h1))
story.append(Paragraph("If your teacher wants to watch you actually <b>use QGIS and SWAT+</b>, here are "
 "two ready-made demos. <b>Everything is already prepared and saved on your computer</b> — you only open "
 "files and click. Below are the exact files to load and exact numbers to type.", body))

story.append(Paragraph("The files you will need (all already on your PC):", St("lab",parent=body,fontName="Helvetica-Bold")))
rows=[[Paragraph("What it is",cellh),Paragraph("File to open  (or table to pick)",cellh)]]
for a,b in [
 ("Height map (DEM)","C:\\SWAT_Ogun\\DEM\\ogun_dem_90m_clip.tif"),
 ("Rivers to 'burn in'","C:\\SWAT_Ogun\\gis\\ogun_rivers_burn.shp"),
 ("Outlet point","C:\\SWAT_Ogun\\gis\\ogun_outlet2.shp"),
 ("Land-use map","C:\\SWAT_Ogun\\landuse\\ogun_landuse_90m.tif"),
 ("Land-use lookup (table)","worldcover_landuses"),
 ("Soil map","C:\\SWAT_Ogun\\soil\\ogun_soil_90m.tif"),
 ("Soil lookup (table)","texture_soils"),
 ("Soil properties (usersoil table)","texture_usersoil"),
 ("The finished project","C:\\SWAT_Ogun\\OgunModel2\\OgunModel2.qgs"),
]:
    rows.append([Paragraph(a,cell),Paragraph(b,cellu)])
story.append(table(rows,[5.4*cm,11.0*cm]))
sp(6)
story.append(Paragraph("The numbers to type:", St("lab2",parent=body,fontName="Helvetica-Bold")))
rows=[[Paragraph("Setting (where it appears)",cellh),Paragraph("Type this",cellh)]]
for a,b in [
 ("Channel threshold (Delineate window)","150 sq km"),
 ("Snap threshold (Delineate window)","500"),
 ("Number of processes (Delineate window)","0"),
 ("HRU filter — Landuse %","10"),
 ("HRU filter — Soil %","10"),
 ("Simulation period (Run window)","2010  to  2023"),
 ("The 6 tuned calibration values","perco 0.30 · petco 1.20 · canmx 12 · alpha 0.022 · flo_min 10 · bf_max 0.55"),
]:
    rows.append([Paragraph(a,cell),Paragraph(b,cellu)])
story.append(table(rows,[7.0*cm,9.4*cm]))
sp(8)

story.append(Paragraph("First, what the QSWAT+ main window buttons mean (and what each one produces):",
 St("lab3",parent=body,fontName="Helvetica-Bold")))
rows=[[Paragraph("Button (Main Steps)",cellh),Paragraph("What it does — and what you get",cellh)]]
for a,b in [
 ("1. Delineate Watershed","Draws the river catchment and splits it into sub-basins from the height map. "
  "When it shows <b>&#8216;Done&#8217;</b>, you have the blue-and-red basin map (23 sub-basins)."),
 ("2. Create HRUs","Cuts each sub-basin into the small same-soil / same-cover / same-slope pieces the model "
  "calculates on. <b>&#8216;Done&#8217;</b> = your 243 HRUs are ready."),
 ("3. Edit Inputs and Run SWAT+","Opens the <b>SWAT+ Editor</b> — where the weather is loaded and the model "
  "is actually <b>RUN</b>. This is the step that calculates the river water for all 14 years."),
 ("4. Visualise","Shows the results as coloured maps and charts inside QGIS after a run."),
 ("Reports / Export Table","&#8216;Select report to view&#8217; shows summary reports (areas, land use, soils); "
  "Export Table saves those tables to a file."),
]:
    rows.append([Paragraph(a,cell),Paragraph(b,cell)])
story.append(table(rows,[4.7*cm,11.7*cm]))
sp(4)
story.append(Paragraph("The word <b>&#8216;Done&#8217;</b> next to a step simply means that step is "
 "finished. In your own project you can see <b>Delineate Watershed = Done</b> and <b>Create HRUs = Done</b> "
 "&#8212; so the next thing to press is <b>Step 3, Edit Inputs and Run SWAT+</b>, which runs the model.", body))
sp(8)

story.append(Paragraph("Demo A — the fast, safe one (~3 minutes): open the finished model and run it", step))
story.append(Paragraph("Best for a live class — nothing can break because it is already built.", body))
story.append(ListFlowable([ListItem(Paragraph(x,body)) for x in [
 "Open <b>QGIS</b>. Click the <b>S+</b> icon (top toolbar) → <b>Existing Project</b> → open "
 "<font face='Courier'>C:\\SWAT_Ogun\\OgunModel2\\OgunModel2.qgs</font>. The Ogun catchment appears.",
 "Point out: <b>'This is the Ogun River catchment I built — 23 sub-basins and 243 HRUs.'</b>",
 "Click <b>Step 3 → Edit Inputs and Run SWAT+</b>. The SWAT+ Editor opens.",
 "Click the <b>Run (▶)</b> icon → <b>Save Settings &amp; Run Selected</b> → wait ~1 minute → "
 "<b>'All selected tasks have completed.'</b>",
 "Open the website: run <font face='Courier'>streamlit run app.py</font> (or it may already be open) "
 "→ click the <b>Hydrology (SWAT+)</b> tab → show the score <b>NSE 0.51</b>.",
]],bulletType="1",leftIndent=16))

story.append(Paragraph("Demo B — build a catchment from scratch (~6 minutes): shows the real skill", step))
story.append(Paragraph("Use this if the teacher wants to see you build, not just open.", body))
story.append(ListFlowable([ListItem(Paragraph(x,body)) for x in [
 "QGIS → <b>S+</b> icon → <b>New Project</b> → location <font face='Courier'>C:\\SWAT_Ogun</font>, "
 "name it <b>DemoModel</b>.",
 "Click <b>Delineate Watershed</b>. Set: <b>DEM</b> = <font face='Courier'>ogun_dem_90m_clip.tif</font>; "
 "tick <b>Burn in existing stream network</b> = <font face='Courier'>ogun_rivers_burn.shp</font>; "
 "<b>Channel threshold</b> = <b>150</b>; tick <b>Use inlets/outlets shapefile</b> = "
 "<font face='Courier'>ogun_outlet2.shp</font>; <b>Snap</b> = <b>500</b>; <b>Processes</b> = <b>0</b>.",
 "Click <b>Create streams</b> (~2 min) → <b>Review snapped</b> (shows '1 snapped') → "
 "<b>Create watershed</b> → <b>OK</b>. You now see the 23-sub-basin Ogun catchment.",
 "(Optional) Click <b>Create HRUs</b>: land-use = <font face='Courier'>ogun_landuse_90m.tif</font> + "
 "table <b>worldcover_landuses</b>; soil = <font face='Courier'>ogun_soil_90m.tif</font>, usersoil "
 "<b>texture_usersoil</b>, lookup <b>texture_soils</b>; <b>Read</b> → filter <b>10 / 10</b> → "
 "<b>Create HRUs</b> → 243 HRUs.",
]],bulletType="1",leftIndent=16))
story.append(K("Demo A is the safe choice to show your teacher: open the finished project, press Run, "
 "show the 0.51 score on the website. Demo B proves you can build it from scratch. All the files and "
 "numbers above are already on your computer — nothing new to download."))

# ===== PART 9: GLOSSARY =====
story.append(Paragraph("Part 9 — Dictionary of the big words", h1))
for term,mean in [
 ("SWAT+","A program that turns rain into river water using real physics. The model I built."),
 ("QGIS","A free, editable map program where I ran SWAT+."),
 ("AHP flood map","The other model: scores every spot by adding 8 clues. Shows WHERE, not HOW MUCH."),
 ("DEM","A 'height map' of the land — tells the computer which way water flows."),
 ("Google Earth Engine","A giant free online satellite-data library; I used it for rain and temperature."),
 ("Catchment / Watershed","The whole area whose rain drains into one river (like a bathtub to one drain)."),
 ("Sub-basin","One slice of the catchment. I had 23."),
 ("HRU","A tiny piece of land with the same soil, cover and steepness. I had 243."),
 ("CHIRPS","Free satellite rainfall data — how much rain fell each day."),
 ("ERA5-Land","Free weather data I used for daily temperature."),
 ("Weather generator","A helper that fills in sun, wind and humidity I didn't measure."),
 ("Calibration","Adjusting the model's settings until it matches the real river."),
 ("Validation","Testing the tuned model on years it never saw, to prove it truly works."),
 ("GEOGLOWS","A trusted global river-flow dataset I compared against (Nigeria has few gauges)."),
 ("NSE","Score for how well the model matches reality: 1.0 perfect, above 0.5 good."),
 ("PBIAS","How far off the TOTAL water is, in percent. Near 0 is best."),
 ("R-squared (R²)","How well the model follows the seasonal ups and downs. 1.0 perfect."),
 ("Streamlit","A free tool that turns a Python script into a website. It made the portal."),
 ("calibration.cal","The SWAT+ settings file where I wrote my 6 tuned values."),
]:
    story.append(Paragraph(f"<b>{term}:</b> {mean}", glo))
sp(6)
story.append(HRFlowable(width="100%",thickness=0.7,color=colors.HexColor("#cbd5e1"),spaceAfter=6))
story.append(Paragraph("<b>Note for my supervisor:</b> every step was carried out by me in QGIS and the "
 "SWAT+ Editor; the tuning and scenarios were driven by my Python scripts. Every command, file, exact "
 "setting and web link is recorded in the technical log <i>METHODOLOGY_LOG.md</i>, so the entire build "
 "can be repeated exactly.", St("note",parent=body,fontSize=10,textColor=GREEN)))

SimpleDocTemplate(OUT,pagesize=A4,topMargin=1.5*cm,bottomMargin=1.4*cm,leftMargin=1.7*cm,rightMargin=1.7*cm,
    title="How I Built the Lagos Flood Model",author="Attah Gbubemi David").build(story)
print("WROTE",OUT)
