"""Benchmark nâng cao (World Bank "Viet Nam Rising", 248 trang). Gold do người làm bài đối chiếu TRỰC TIẾP trên ảnh trang gốc
(không dựa vào mô tả do model sinh). Số trang = số trang PDF (1..248), KHÔNG phải số in trên trang.

category: table | image (sơ đồ/bản đồ/ảnh) | chart | multihop | text | absent.
gold[]: {page, kind(text|table|chart|diagram), region, evidence}. Với text: evidence là đoạn nguyên văn (kiểm tra tự động).
Với table/chart/diagram: evidence mô tả ô/hàng/cột/vùng đã đọc trên ảnh gốc. multihop: gold có >=2 phần tử thuộc >=2 trang, đều bắt buộc.
Hit retrieval (trang): chunk thuộc đúng trang gold. Dev và test không dùng chung trang gold."""
import json, re, sys
from pathlib import Path

W = Path(__file__).resolve().parent / "work"
P = {}
for l in open(W / "pages.jsonl", encoding="utf8"):
    x = json.loads(l); P[x["page"]] = re.sub(r"\s+", " ", x["text"])


def G(page, kind, region, evidence):
    return {"page": page, "kind": kind, "region": region, "evidence": evidence}


Q = []
def add(id, split, cat, q, ans, gold, note=""):
    Q.append({"id": id, "split": split, "category": cat, "question": q, "expected_answer": ans, "answerable": True, "gold": gold, **({"note": note} if note else {})})

# ---------------- TEST (24 có đáp án) ----------------
# Bảng (6)
add("t01", "test", "table", "According to the table on marginal contribution and cost-effectiveness of inequality reduction by tax and spending, what is the budget (% of GDP) and cost-effectiveness of VAT?",
    "Budget 8.0% of GDP; cost-effectiveness 0.03.", [G(234, "table", "Table 15, row VAT", "VAT: marginal contribution 0.1, budget 8.0, cost effectiveness 0.03")])
add("t02", "test", "table", "In the simulation of cash-transfer expansion, what are the marginal contribution (MC) and fiscal impact (% of GDP) when targeting is improved to the Q3 cost-effectiveness level and social assistance spending is doubled?",
    "MC 2.1; fiscal impact -0.7% of GDP.", [G(237, "table", "Table 16, 'Improved targeting, double SA' / Q3 CE", "Q3 CE: %GDP 1.4, CE 1.4, MC 2.1, change 1.7, fiscal impact -0.7")])
add("t03", "test", "table", "By how many percentage points does social pension coverage of people aged 60+ rise between the 2019 baseline and the 2030 reform scenario?",
    "From 15.7% to 35.4%, i.e. +19.7 percentage points.", [G(239, "table", "Table 17, row Total 60+", "Total 60+: baseline coverage 15.7, reform scenario 2030 coverage 35.4")])
add("t04", "test", "table", "In the carbon-tax simulation table, what is the Gini effect and the effect at the US$6.85 poverty line of the 'Ambitious' scenario?",
    "Gini -0.09; US$6.85 poverty -1.7.", [G(240, "table", "Table 18, row Ambitious", "Ambitious: Gini -0.09, US$3.65 -0.5, US$3.65 gap -0.2, US$6.85 -1.7, US$6.85 gap -0.6")])
add("t05", "test", "table", "Which of the six strategic areas of the Viet Nam 2035 recommendations had the lowest share of recommendations included in policy documents, and what was that share?",
    "Managing urbanization for greater efficiency: 5% (1 of 19).", [G(68, "table", "Table 1, row 3", "Managing urbanization for greater efficiency: total 19, in policy docs 1, 5%")])
add("t06", "test", "table", "In the legal framework table for public investment management, at which stage is the Public Investment Law NOT ticked?",
    "Operations.", [G(200, "table", "Table 2, row Public Investment Law", "Public Investment Law ticked at strategic guidance, ex-ante evaluation, selection & budgeting, implementation & adjustment, ex post review; not Operations")])
# Sơ đồ / bản đồ (5)
add("t07", "test", "image", "In the diagram of the five policy packages, which package forms the base that supports the other packages?",
    "PP5: Modernizing institutions.", [G(33, "diagram", "Figure 0.10", "PP5 'Modernizing institution' at the bottom with arrows up to both the PP1-PP2 box and the PP3-PP4 box")])
add("t08", "test", "image", "According to the diagram organizing the report's chapters into four (five) parts, which chapters belong to the part on infrastructure and resources?",
    "Chapter 8 (spatial and digital connectivity), Chapter 9 (adapting to climate change), Chapter 10 (resource mobilization).", [G(60, "diagram", "Figure 11, Part 3", "Part 3: Infrastructure and resources - Chapter 8, Chapter 9, Chapter 10")])
add("t09", "test", "image", "In the integrated social protection information system diagram, which four external connections are shown along the top?",
    "VSS, MoET, MoH and MARD (Disaster Management).", [G(149, "diagram", "Figure 85, top row 'External Connections'", "VSS, MoET, MoH, MARD-Disaster Management")])
add("t10", "test", "image", "In the Mekong Delta salinity-intrusion map (present climate), how many classes does the legend have and what is the highest class?",
    "Four classes; the highest is 10 g/l for more than 6 months.", [G(224, "diagram", "Figure 146, Panel C legend", "<1 g/l for <1 month; 1-4 g/l for 1-3 months; 4-10 g/l for 4-6 months; 10 g/l for >6 months")])
add("t11", "test", "image", "In the 'Drivers of growth' framework diagram, which three elements feed into output and which element influences all of them from above?",
    "Capital, Labor and Productivity feed output; Institutions influence them (with Shocks acting from below).", [G(59, "diagram", "Figure 10", "Institutions box above Capital, Labor, Productivity -> OUTPUT; Shocks boxes below each")])
# Biểu đồ (5)
add("t12", "test", "chart", "In the chart on achieving high-income status by 2045, what was Viet Nam's GDP per capita in 2023 and what yearly growth rate is required from then to reach the 2045 level?",
    "US$4,347 in 2023; +6.0% per annum is required (vs +5.1% p.a. achieved 1986-2023).", [G(21, "chart", "Figure O.1", "682 (1986), 2310 (2010), 4347 (2023), 15584 (2045); +5.1% p.a. then +6.0% p.a.")],
    note="Cùng biểu đồ xuất hiện lại ở Figure 7 (trang PDF 56): trang 56 cũng là gold hợp lệ.")
add("t13", "test", "chart", "In the chart comparing due process and independence scores, which income group has the highest scores on both indicators?",
    "High-income countries (about 0.7 on both).", [G(47, "chart", "Figure 0.19", "High-Income bars highest (~0.7) for both series; Viet Nam ~0.45 and ~0.29")])
add("t14", "test", "chart", "In the chart of the share of US GNI per capita for selected countries, which country has risen to the highest share by 2023?",
    "China (about 26%).", [G(56, "chart", "Figure 8", "China line ends highest (~26) at 2023; upper middle income group ~13")])
add("t15", "test", "chart", "How many years does Viet Nam take to move from 7 to 14 percent of the population aged 65+, versus France?",
    "Viet Nam 15 years; France 115 years.", [G(130, "chart", "Figure 67", "Vietnam (15) ... France (115)")])
add("t16", "test", "chart", "In the chart of economic damages by channel, which channel accounts for the largest share and does its share rise or fall between 2030 and 2045?",
    "Heat stress (labor productivity); its share rises (about 63% in 2030 to about 77% in 2045).", [G(182, "chart", "Figure 109", "Heat stress dark-blue segment largest, increasing across 2030-2045")])
# Multi-hop (4)
add("t17", "test", "multihop", "By how much do climate impacts reduce Viet Nam's GDP level by 2045, and what yearly growth of GDP per capita is needed from 2023 to reach high-income status in 2045?",
    "GDP lower by 11.2% by 2045; growth of 6.0% per year is needed.",
    [G(182, "text", "text near Figure 108", "projected loss from 11.2 percent to 6.0 percent"), G(21, "chart", "Figure O.1", "+6.0% p.a. between 2023 and 2045")])
add("t18", "test", "multihop", "How does the current cost-effectiveness of cash transfers in Viet Nam compare with the global median cost-effectiveness of cash transfers?",
    "Viet Nam's cash transfers: 0.03; global median: 1.12 points (about 37 times higher).",
    [G(234, "table", "Table 15, row Cash transfers", "Cash transfers cost effectiveness 0.03"), G(237, "text", "text above Table 16", "median cost-effectiveness of cash transfers, for countries for which there is data, is 1.12 points")])
add("t19", "test", "multihop", "Which policy package is meant to ensure everyone gains from the high-income transition, and to which part and chapter of the report does it correspond?",
    "PP4 (Ensuring everyone gains from the HIC transition) corresponds to Part 5 on Equity, Chapter 12.",
    [G(33, "diagram", "Figure 0.10", "PP4: Ensuring everyone gains from the HIC transition"), G(60, "diagram", "Figure 11, Part 5", "Part 5: Equity - Chapter 12: Equity")])
add("t20", "test", "multihop", "What share of their budget do the poorest households spend directly on fossil fuels and electricity, and what is the effect of a carbon tax on the Gini index?",
    "About 12% for the poorest two deciles; the carbon tax changes Gini by -0.03.",
    [G(239, "text", "carbon taxes section", "slightly higher (12 percent) for the poorest two deciles"), G(240, "table", "Table 18, row Carbon tax", "Carbon tax: Gini -0.03")])
# Text (4)
add("t21", "test", "text", "How much did gross capital formation increase between 2000 and 2010?",
    "From 30 percent to 37 percent of GDP.", [G(60, "text", "section 1.5.1", "Between 2000 and 2010, gross capital formation (GCF) increased from 30 percent to 37 percent of GDP")])
add("t22", "test", "text", "By how many jobs could net employment increase in 2030 under decarbonization policies aimed at net zero by 2050?",
    "By 726,000 jobs in 2030.", [G(240, "text", "carbon transition paragraph", "net employment could increase by 726,000 jobs in 2030")])
add("t23", "test", "text", "If inequality stays at current levels, what share of Vietnamese would earn at or above the high-income level in 2045?",
    "38 percent (the remaining 62 percent would live on less).", [G(21, "text", "equitable prosperity paragraph", "only 38 percent of the population would earn at or above high-income level")])
add("t24", "test", "text", "By how many percentage points can adaptation measures reduce the projected climate-related GDP loss, and to what level?",
    "By 5.2 points: from 11.2 percent to 6.0 percent (an improvement of 46 percent).", [G(182, "text", "adaptation paragraph", "reducing the projected loss from 11.2 percent to 6.0 percent, an improvement of 46 percent")])

# ---------------- DEV (15 có đáp án) ----------------
add("d01", "dev", "table", "In the green growth reform agenda table, what moderate carbon tax level is recommended?",
    "A moderate carbon tax of US$7.5-15 per ton, by reforming the EPT fuel excise tax starting with coal.", [G(125, "table", "Table 5, first row", "Introduce a moderate carbon tax ($7.5-15/ton) by reforming the EPT fuel excise tax")])
add("d02", "dev", "table", "In the table of the objectives, policy pillars and programs of a social protection system, which pillar corresponds to the 'Promotion' objective?",
    "Labor Market.", [G(140, "table", "Table 7, row Promotion", "Promotion - Labor Market - employment services, labor market information systems, passive programs")])
add("d03", "dev", "table", "In the resource mobilization reform agenda, which tax instruments should be modernized first under the domestic revenue mobilization package?",
    "VAT exemptions, PIT, CIT and property taxes.", [G(196, "table", "Table 11, package 2", "Modernize major tax instruments, starting with VAT exemptions, PIT, CIT, and property taxes")])
add("d04", "dev", "table", "In the social protection reform agenda table, what medium-term funding target is set for social protection?",
    "6 percent of GDP.", [G(153, "table", "Table 8, package 4", "Increase social protection funding to 6 percent of GDP in the medium term")])
add("d05", "dev", "image", "In the social protection framework diagram (Resolution 15), what are the four components under Social Protection?",
    "Social Assistance; Social Insurance; Employment, Incomes and Poverty Reduction; Minimum Basic Social Services.", [G(141, "diagram", "Figure 73", "Social Assistance, Social Insurance, Employment Incomes and Poverty Reduction, Minimum Basic Social Services")])
add("d06", "dev", "image", "In the Mekong Delta maps of extreme heat for 1983-2016, what is the maximum number of days on the legend scale?",
    "40 days (Max. WBGT > 30C).", [G(181, "diagram", "Figure 107, Panel B legend", "legend Max. WBGT >30C: 0, 10, 20, 30, 40 days")])
add("d07", "dev", "image", "The two ASEAN maps of levelized cost of energy compare which two energy sources?",
    "Solar (PV) and wind.", [G(124, "diagram", "Figures 62 and 63", "Figure 62 LCOE of solar energy; Figure 63 wind energy, ASEAN countries")])
add("d08", "dev", "chart", "According to the PDP8 power-mix chart, what are the shares of solar power in 2022 and in 2050?",
    "21% in 2022 and 34% in 2050 (+13 points).", [G(122, "chart", "Figure 61", "2022: solar 21%; 2050: solar 34%")])
add("d09", "dev", "chart", "In which year did venture capital investments in Viet Nam peak?",
    "2021.", [G(115, "chart", "Figure 55", "VC investment bar highest in 2021 (~US$1.4 billion)")])
add("d10", "dev", "chart", "What was electricity demand (TWh) in 2023 and 2010 in the load growth chart, and how many times higher is it?",
    "251.3 TWh in 2023 vs 85.7 TWh in 2010, about 2.9 times.", [G(78, "chart", "Figure 25", "85.7 (2010), 143.5 (2015), 214.3 (2020), 251.3 (2023)")])
add("d11", "dev", "multihop", "How much was electricity demand in 2023 and what share of the power mix is planned for solar in 2050?",
    "251.3 TWh in 2023; solar 34% of the power mix by 2050.", [G(78, "chart", "Figure 25", "251.3 TWh in 2023"), G(122, "chart", "Figure 61", "2050 solar 34%")])
add("d12", "dev", "multihop", "How many main components does the social protection framework diagram show, and which pillar covers programs that promote people's movement out of poverty?",
    "Four components; the Labor Market pillar (Promotion objective).", [G(141, "diagram", "Figure 73", "four components under Social Protection"), G(140, "table", "Table 7, Promotion", "Promotion - Labor Market")])
add("d13", "dev", "text", "What current UMIC averages of GDP spending on social assistance and social insurance does the report cite as a financing target?",
    "2.0 percent of GDP on social assistance and 4.1 percent on social insurance.", [G(153, "text", "text above Table 8", "The current UMIC average of 2.0 percent of GDP on social assistance and 4.1 percent on social insurance")])
add("d14", "dev", "text", "By what year is a domestic carbon market under an emissions trading system planned to be developed?",
    "By 2028.", [G(122, "text", "carbon price paragraph", "roadmap for the development of a domestic carbon market by 2028")])
add("d15", "dev", "text", "How much installed power capacity did Viet Nam have in 2021, and how often must it be doubled?",
    "78 gigawatts in 2021; it must double every ten years.", [G(78, "text", "infrastructure bottlenecks", "doubling the existing installed capacity (78 gigawatts in 2021) every ten years")])

# ---------------- Thiếu bằng chứng: test 6, dev 3 ----------------
absent = [
    ("t25", "test", "What was Viet Nam's unemployment rate in 2023?", r"unemploy[a-z]* rate|rate of unemploy", "Báo cáo bàn về việc làm/kỹ năng nhưng không nêu tỷ lệ thất nghiệp."),
    ("t26", "test", "What is the total investment cost of the Ngoc Hoi station project in US dollars?", r"Ngoc Hoi[^.]{0,200}(\$|billion|cost)", "Box 4 mô tả quy hoạch (251 ha) nhưng không nêu chi phí đầu tư."),
    ("t27", "test", "How many unicorn companies does Viet Nam have?", r"unicorn", "Phần đổi mới sáng tạo/VC không nhắc unicorn."),
    ("t28", "test", "What is the average retail electricity price in Viet Nam in US cents per kWh?", r"tariff[^.]{0,60}(cents?|kWh)|cents? per kWh", "Phần năng lượng nói về feed-in tariff và chi phí LCOE, không nêu giá điện bán lẻ trung bình."),
    ("t29", "test", "How much FDI did Viet Nam disburse in 2024 in billions of US dollars?", r"FDI[^.]{0,60}\$ ?\d+(\.\d+)? billion|disbursed FDI", "Figure 112 chỉ so sánh FDI theo % GDP, không có giá trị giải ngân 2024."),
    ("t30", "test", "What is the average monthly salary of a worker in Viet Nam in VND?", r"average (monthly )?(wage|salary|income)[^.]{0,40}(VND|dong)", "Không có lương trung bình tuyệt đối bằng VND."),
    ("d16", "dev", "How many university students are enrolled in Viet Nam in 2023?", r"\d[\d,\.]* (million |thousand )?(university|tertiary|college) students", "Báo cáo nêu tỷ lệ nhập học, không nêu số lượng sinh viên."),
    ("d17", "dev", "How many million internet users does Viet Nam have?", r"\d+(\.\d+)? million (internet|smartphone|mobile) (users|subscribers)", "Chỉ có tỷ lệ % người dùng internet, không có số người dùng."),
    ("d18", "dev", "What is the ticket price of a Hanoi-Ho Chi Minh City train?", r"ticket (price|fare)|fare of", "Phần đường sắt nói mật độ km/triệu dân, không nêu giá vé."),
]
vis = ""
import glob
for f in glob.glob(str(W / "visual" / "*.json")):
    vis += " " + re.sub(r"\s+", " ", json.load(open(f, encoding="utf8"))["text"])
alltext = " ".join(P.values()) + vis
for id, split, q, pat, reason in absent:
    hits = [m.group(0) for m in re.finditer(pat, alltext, re.I)]
    print(id, "regex khớp:", len(hits), hits[:2])
    Q.append({"id": id, "split": split, "category": "absent", "question": q, "answerable": False, "expected_behavior": "search_and_abstain",
              "absence_reason": reason, "absence_check": f"regex {pat!r} trên text 248 trang + mô tả trực quan: {len(hits)} khớp"})

# kiểm tra tự động evidence dạng text nằm trong text gốc của đúng trang
bad = [(q["id"], g["page"]) for q in Q if q["answerable"] for g in q["gold"] if g["kind"] == "text" and g["evidence"] not in P[g["page"]]]
print("evidence text không khớp:", bad)
pages = {s: {g["page"] for q in Q if q["split"] == s and q["answerable"] for g in q["gold"]} for s in ("dev", "test")}
print("trang dùng chung dev/test:", sorted(pages["dev"] & pages["test"]))
from collections import Counter
print(Counter((q["split"], q["category"]) for q in Q))
json.dump(Q, open(Path(__file__).resolve().parent / "benchmark.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
