"""
FedRAMP Interdependency Diagram Generator
Produces:
  fedramp_diagram.dot  — Graphviz source (import into any Graphviz tool / yEd)
  fedramp_diagram.html — Interactive vis.js network (open in any browser)

Source: FedRAMP CSP/Agency Playbooks v4.1-4.2, ConMon Playbook v1.0,
        Pen Test Guidance v3, Security Controls Baseline (Rev5 Apr 2026),
        Boundary Guidance — all Nov 2025 / Apr 2026 versions.
Notes: Nodes marked * are referenced by FedRAMP docs but not in local KB.
       Bold/darker nodes are locally available.
"""

# ============================================================
# DATA DEFINITIONS
# ============================================================

# Groups: 0=Policy*, 1=NIST-in-KB, 2=NIST-not-KB, 3=Actors,
#         4=Baselines, 5=Infra, 6=States, 7=Phase1, 8=Phase2,
#         9=ConMon, 10=Escalation, 11=PenTest, 12=Container

NODES = [
    # ---- Upstream Policy (not in local KB) ----
    {"id": "FISMA",     "label": "FISMA *\n(statute)",                          "group": 0, "level": 0,
     "tip": "Federal Information Security Modernization Act — legal basis for federal info security. NOT in local KB."},
    {"id": "OMB_A130",  "label": "OMB A-130 *\n(fed info mgmt)",               "group": 0, "level": 0,
     "tip": "OMB Circular A-130: defines 'federal information' and 'authorization boundary'. Governs FedRAMP boundary scoping. NOT in local KB."},
    {"id": "OMB_MEMO",  "label": "OMB FedRAMP\nMandate Memo *",                "group": 0, "level": 0,
     "tip": "OMB memo mandating FedRAMP for cloud services storing/processing/transmitting federal information. NOT in local KB."},
    {"id": "FIPS_199",  "label": "FIPS 199 *\n(security categorization)",      "group": 0, "level": 0,
     "tip": "FIPS 199: Federal standard for security categorization (Low/Moderate/High). AO uses FIPS 199 Categorization Template to determine impact level. NOT in local KB."},
    {"id": "FIPS_140",  "label": "FIPS 140 *\n(crypto validation)",            "group": 0, "level": 0,
     "tip": "FIPS 140: Standard for cryptographic module validation. Missing FIPS 140-validated encryption is a common SSP barrier. NOT in local KB."},

    # ---- NIST Standards — IN local KB ----
    {"id": "SP_800_53", "label": "NIST SP 800-53r5\n(control catalog: 1,000+ controls)", "group": 1, "level": 1,
     "tip": "IN LOCAL KB. Source catalog for all FedRAMP baselines. 20 families. FedRAMP adds mandatory parameter values (filling 'organization-defined' placeholders) and additional requirements."},
    {"id": "SP_800_115","label": "NIST SP 800-115\n(pen test methodology)",    "group": 1, "level": 1,
     "tip": "IN LOCAL KB. Technical guide to security testing. FedRAMP pen test guidance is built on this methodology."},
    {"id": "SP_800_61", "label": "NIST SP 800-61r3\n(incident response)",      "group": 1, "level": 1,
     "tip": "IN LOCAL KB. Incident response lifecycle (Prepare/Detect/Analyze/Contain/Eradicate/Recover). IR-6 references 800-61 timelines for 1-hour CISA reporting window."},
    {"id": "SP_800_190","label": "NIST SP 800-190\n(container security)",      "group": 1, "level": 1,
     "tip": "IN LOCAL KB. Container/Docker/Kubernetes risks. Source for FedRAMP container requirement risk profile (ephemeral instances, registry poisoning, etc.)."},
    {"id": "ATT_CK",    "label": "MITRE ATT&CK\n(enterprise + cloud matrix)",  "group": 1, "level": 1,
     "tip": "IN LOCAL KB (design philosophy + CISA practices). Required attack model framework for FedRAMP pen tests. All 14 enterprise tactics must inform test narrative."},

    # ---- NIST Standards — NOT in local KB ----
    {"id": "SP_800_37", "label": "NIST SP 800-37 *\n(RMF — parent framework)", "group": 2, "level": 1,
     "tip": "NOT in local KB. Risk Management Framework. FedRAMP is a federal implementation of RMF steps. The phases Prepare→Categorize→Select→Implement→Assess→Authorize→Monitor map directly to FedRAMP phases."},
    {"id": "SP_800_53A","label": "NIST SP 800-53A *\n(assessment procedures)", "group": 2, "level": 1,
     "tip": "NOT in local KB. Building effective assessment plans. Governing standard for 3PAO SAP development alongside 800-115."},
    {"id": "SP_800_145","label": "NIST SP 800-145 *\n(cloud definition)",      "group": 2, "level": 1,
     "tip": "NOT in local KB. NIST definition of cloud computing. SaaS/PaaS/IaaS taxonomy used throughout FedRAMP pen test guidance to determine attack vector scope."},
    {"id": "SP_800_70", "label": "NIST SP 800-70 *\n(hardening benchmarks)",   "group": 2, "level": 1,
     "tip": "NOT in local KB. National Checklist Program (SCAP). Container images must be hardened per these benchmarks. 3PAO validates hardening against CM-6, SC-2/3/4."},

    # ---- Actors ----
    {"id": "CSP",  "label": "Cloud Service\nProvider (CSP)",              "group": 3, "level": 2,
     "tip": "Builds and maintains the CSO. Develops SSP. Hires 3PAO. Manages POA&M and ConMon deliverables. Responsible for boundary definition."},
    {"id": "AO",   "label": "Agency Authorizing\nOfficial (AO)",          "group": 3, "level": 2,
     "tip": "Reviews authorization package. Issues ATO letter. Accepts risk. Oversees ongoing ConMon. Approves deviation requests and SCRs. Each agency issues their own ATO — not a government-wide authorization."},
    {"id": "PAO3", "label": "3PAO\n(FedRAMP-recognized assessor)",        "group": 3, "level": 2,
     "tip": "Independent third-party assessor recognized by FedRAMP. Develops SAP and SAR. Validates controls. Performs pen test. Conducts annual assessments. Team lead must hold OSCP/GPEN/CEH equivalent credential."},
    {"id": "PMO",  "label": "FedRAMP PMO\n(GSA)",                         "group": 3, "level": 2,
     "tip": "Program Management Office (housed at GSA). Stewards the program. Performs quality/risk review post-ATO. Grants FedRAMP Authorized designation. Manages secure repository for Low/Moderate CSOs."},
    {"id": "CISA", "label": "CISA",                                        "group": 3, "level": 2,
     "tip": "Cybersecurity and Infrastructure Security Agency. Issues Binding Operational Directives and Emergency Directives. Provides incident handling assistance. Coordinates on confirmed attack vectors."},
    {"id": "ISSO", "label": "Agency ISSO /\nFedRAMP Liaison",              "group": 3, "level": 2,
     "tip": "Agency ISSO and/or FedRAMP Liaison. Bridges agency and FedRAMP PMO. Monitors ConMon on behalf of AO. Can be delegated AO review responsibilities for monthly deliverables."},

    # ---- FedRAMP Baselines ----
    {"id": "B_LI",  "label": "LI-SaaS Baseline\n(attest/doc/assess only)",              "group": 4, "level": 3,
     "tip": "Low-Impact SaaS: Lightest tier. Three dispositions per control: Attest, Document and Assess, Document Only. Only for systems with no PII beyond login credentials (name, email, username/password)."},
    {"id": "B_LOW", "label": "Low Baseline\n157 controls / 18 families",                "group": 4, "level": 3,
     "tip": "Low Baseline: 157 controls. Loss would have limited adverse effect on agency operations. ~10% of FedRAMP market. Policy review every 3 years. Annual account review."},
    {"id": "B_MOD", "label": "Moderate Baseline\n324 controls / 18 families\n~80% of CSOs", "group": 4, "level": 3,
     "tip": "Moderate Baseline: 324 controls. Default floor. Serious adverse effect. ~80% of market. Adds full least-privilege suite, remote access, wireless, SIEM/IDS, pen testing (CA-8). Policy review every 3 years. Quarterly privileged account review."},
    {"id": "B_HIGH","label": "High Baseline\n411 controls / 18 families\nsevere/catastrophic systems", "group": 4, "level": 3,
     "tip": "High Baseline: 411 controls. Severe/catastrophic systems (law enforcement, health, financial). Key additions: non-repudiation (AU-10), security function isolation (SC-3), fail in known state (SC-24), insider threat program (IR-4(6)), in-person identity proofing (IA-12(4)), developer screening (SA-21). Annual policy review."},

    # ---- FedRAMP Infrastructure ----
    {"id": "MARKETPLACE","label": "FedRAMP Marketplace",                   "group": 5, "level": 3,
     "tip": "Public registry showing all CSOs at Ready / In Process / Authorized / Suspended / Revoked states. Agencies use it to find reusable authorizations."},
    {"id": "REPO_LM",   "label": "Secure Repository\n(Low/Mod: USDA Connect.gov)", "group": 5, "level": 3,
     "tip": "FedRAMP-managed secure repository for Low and Moderate CSOs hosted on USDA Connect.gov. Monthly ConMon packages uploaded here. Agencies access packages via FedRAMP Package Access Request Form."},
    {"id": "REPO_H",    "label": "CSP Repository\n(High: CSP-managed, FedRAMP-authorized)", "group": 5, "level": 3,
     "tip": "High-impact CSOs must maintain their own FedRAMP-authorized secure repository. Not hosted by FedRAMP PMO."},

    # ---- Authorization States ----
    {"id": "S_READY",  "label": "FedRAMP\nREADY",      "group": 6, "level": 4,
     "tip": "FedRAMP Ready: 3PAO attests CSP is technically capable; RAR reviewed and approved by PMO. Posted on Marketplace. Optional but recommended — signals readiness to agency partners."},
    {"id": "S_INPROC", "label": "FedRAMP\nIN PROCESS", "group": 6, "level": 4,
     "tip": "FedRAMP In Process: CSP and agency submitted WBS+IPR to PMO. PMO lists the CSO on Marketplace. Active authorization underway."},
    {"id": "S_AUTH",   "label": "FedRAMP\nAUTHORIZED", "group": 6, "level": 4,
     "tip": "FedRAMP Authorized: PMO granted designation post-ATO quality review. Package available for government-wide reuse — but each agency must issue their own ATO. The only designation that satisfies the OMB mandate."},

    # ---- Phase 1: Preparation ----
    {"id": "P_CSP_FORM","label": "CSP Information Form\n(→ generates FedRAMP ID)", "group": 7, "level": 5,
     "tip": "Required before partnership is formalized. Generates a FedRAMP ID that follows the CSO for life. Submitted to FedRAMP PMO."},
    {"id": "P_RAR",     "label": "Readiness Assessment\nReport (RAR)",         "group": 7, "level": 5,
     "tip": "Produced by 3PAO after Readiness Assessment. Documents technical capability gaps (not documentation). Optional but recommended for Moderate/High. PMO reviews and approves. Required for FedRAMP Ready designation."},
    {"id": "P_IMPACT",  "label": "Impact Level\nDetermination\n(FIPS 199 template)", "group": 7, "level": 5,
     "tip": "AO determines Low/Moderate/High using FIPS 199 Categorization Template. CSP must confirm with agency partner. Impact level drives the entire control baseline, ConMon burden, and repository requirements."},
    {"id": "P_WBS_IPR", "label": "WBS + In-Process\nRequest (IPR)",            "group": 7, "level": 5,
     "tip": "Work Breakdown Structure + In-Process Request submitted to intake@fedramp.gov. Triggers In Process designation on Marketplace. CSP and Agency co-submit."},
    {"id": "P_KICKOFF", "label": "Kickoff Meeting\n(boundary · data flows\ngaps · customer controls)", "group": 7, "level": 5,
     "tip": "CSP, 3PAO, and Agency AO align on: authorization boundary definition, data flows, known gaps, agency-specific requirements, customer-responsible controls, and risk acceptance areas."},

    # ---- Phase 2: Authorization ----
    {"id": "A_SSP",      "label": "System Security Plan (SSP)\n+ Appendices A–Q\n'security blueprint'", "group": 8, "level": 6,
     "tip": "The core authorization document. Must be Clear, Complete, Concise, Consistent. Common failures: imprecise boundary, EOL software, missing FIPS 140 crypto, external services at lower impact level, poor MFA, vague control narratives. Key appendices: E(Digital Identity), G(ISCP), I(IRP), M(Inventory), O(POA&M), P(SCRMP)."},
    {"id": "A_SAP",      "label": "Security Assessment\nPlan (SAP)",             "group": 8, "level": 6,
     "tip": "Developed by 3PAO using FedRAMP template. CSP reviews and signs. AO approves before testing begins (Just-In-Time approach). Governs scope, methodology, and schedule for the full security assessment."},
    {"id": "A_FULL",     "label": "Full Security Assessment\n(system frozen during test)", "group": 8, "level": 6,
     "tip": "3PAO validates controls, conducts vulnerability scans and pen test. System must be completely frozen during testing — no changes to the CSO during this period."},
    {"id": "A_SAR",      "label": "Security Assessment\nReport (SAR)\n(contains pen test report)", "group": 8, "level": 6,
     "tip": "Developed by 3PAO. Documents all findings, vulnerabilities (each unique vuln as separate POA&M item), and authorization recommendation. Pen test report embedded — no standalone pen test template."},
    {"id": "A_POAM",     "label": "POA&M\n(plan of action & milestones)\n30/90/180-day timelines", "group": 8, "level": 6,
     "tip": "CSP develops from SAR findings. Remediation timelines: Critical/High = 30 days, Moderate = 90 days, Low = 180 days. Deviation request types: Risk Adjustment (RA), False Positive (FP), Operational Requirement (OR), Vendor Dependency (VD)."},
    {"id": "A_ATO",      "label": "ATO Letter\n(Agency AO → CSP\n+ ato-letter@fedramp.gov)", "group": 8, "level": 6,
     "tip": "Authorization to Operate. Signed by Agency AO. Sent to CSP and ato-letter@fedramp.gov. NOT government-wide — every agency using the same CSO must issue their own ATO."},
    {"id": "A_CHECKLIST","label": "Initial Authorization\nPackage Checklist",   "group": 8, "level": 6,
     "tip": "CSP submits post-ATO. Enables FedRAMP PMO quality and risk review. Required before PMO grants FedRAMP Authorized designation on Marketplace."},

    # ---- Phase 3: Continuous Monitoring ----
    {"id": "CM_MONTHLY", "label": "Monthly Deliverables Package\n(POA&M · inventory · scan files\nDRs · SCRs · incident reports)", "group": 9, "level": 7,
     "tip": "Core ConMon obligation. Uploaded to secure repository monthly. Contents: updated POA&M, updated system inventory, raw vulnerability scan files, deviation requests, significant change requests, incident reports."},
    {"id": "CM_VULN",    "label": "Vulnerability Scanning\n(OS+Web/API+DB: monthly\nauth required: Mod+High\n30-day container window)", "group": 9, "level": 7,
     "tip": "Monthly scanning of OS/infrastructure, web applications (including APIs), and databases. Authenticated scanning required for Moderate/High (RA-5(5)). CVSSv3 scoring. Machine-readable output. 100% inventory coverage or approved sampling. Container images must be scanned within 30-day window from registry deploy."},
    {"id": "CM_ANNUAL",  "label": "Annual Assessment\n(3PAO; CA-2)\n+ annual pen test (CA-8)", "group": 9, "level": 7,
     "tip": "Required annually by CA-2. Scope: FedRAMP-selected core controls, CSP-selected controls for system changes, closed POA&M validation, N/A control validation, controls not assessed in past 3 years. Annual pen test required by CA-8 (every 12 months in ConMon)."},
    {"id": "CM_DEV_REQ", "label": "Deviation Requests\n(RA · FP · OR · VD)\n(AO approves RA/FP/OR)", "group": 9, "level": 7,
     "tip": "RA=Risk Adjustment (reduce scanner severity; AO approval), FP=False Positive (AO approval if not 3PAO-validated), OR=Operational Requirement (can't remediate; AO approval; PMO won't approve OR for High vulns), VD=Vendor Dependency (no approval; track monthly; High VDs must be mitigated to Moderate within 30 days)."},
    {"id": "CM_SIGCHG",  "label": "Significant Change Process\nRoutine / Adaptive / Transformative", "group": 9, "level": 7,
     "tip": "Routine Recurring: no AO approval (patching, firewall rules, capacity, token refresh). Adaptive: AO approval + 3PAO (breaking-change OS update, crypto module swap, multi-week feature deploy). Transformative: AO approval + 3PAO (IaaS replacement, datacenter migration, adding AI capability touching federal data)."},
    {"id": "CM_INCIDENT","label": "Incident Communications\n1-hr notify: customers · CISA\nFedRAMP · AO POCs", "group": 9, "level": 7,
     "tip": "Within 1 hour of CSP identification: notify affected customers (via FedRAMP repo folder), CISA (cisa.gov/forms/report when attack vector confirmed), FedRAMP (fedramp_security@gsa.gov), Agency AOs/ISSOs. Daily updates until Recovery complete. Final post-incident report required (root cause, response, lessons learned)."},
    {"id": "CM_COLLAB",  "label": "Collaborative ConMon\n(required: >1 active ATO/ATU\nCA-7 driven)", "group": 9, "level": 7,
     "tip": "Required when CSP has more than one active ATO or ATU on file. Charter required: member contacts, monthly meeting schedule, agenda, deliverable timing, decision-making process, agency-specific requirements. Agencies share oversight responsibility but each still does individual due diligence."},

    # ---- Escalation ----
    {"id": "ESC_SATISF","label": "Satisfactory",               "group": 10, "level": 8,
     "tip": "Passing ConMon — CSP meeting all requirements. No formal escalation."},
    {"id": "ESC_DFR",   "label": "DFR\n(Detailed Finding Review)", "group": 10, "level": 8,
     "tip": "Triggers: vuln count increases ≥20% from ATO baseline OR ≥10 new unique vulns; OR unauthenticated scans ≥10% of submission (first incident in 6 months). AO requests CSP assess deficiency, provide root cause and remedy within agreed timeframe."},
    {"id": "ESC_CAP",   "label": "CAP\n(Corrective Action Plan)",  "group": 10, "level": 8,
     "tip": "Triggers: unauthenticated scans ≥10% — second/subsequent incident in 6 months; OR unresolved DFR. AO requests formal root-cause analysis and remediation plan. System owner must sign. AO approves plan. CAP letter uploaded to secure repository."},
    {"id": "ESC_SUSP",  "label": "Suspension\n(ATO temporarily revoked)", "group": 10, "level": 8,
     "tip": "AO temporarily suspends ATO(s). Agency may suspend use of the CSO. CSP must resolve or face revocation. AO must notify FedRAMP PMO at info@fedramp.gov."},
    {"id": "ESC_REVOKE","label": "Revocation\n(agency migrates data out)", "group": 10, "level": 8,
     "tip": "AO revokes ATO. Agency must migrate data to another CSO. AO must notify FedRAMP PMO. PMO updates Marketplace status. Most severe ConMon failure outcome."},

    # ---- Pen Testing ----
    {"id": "PT_ROE","label": "Rules of Engagement\n(ROE)\n(AO must approve before test)", "group": 11, "level": 7,
     "tip": "AO must approve ROE before testing begins. Contents: approach/constraints/methodology per attack, detailed schedule, technical POCs with backups, IR procedures if event occurs during test, physical penetration constraints, social engineering pretexts (fully worked out before signing), third-party agreements."},
    {"id": "PT_AV1","label": "AV1: External→Corporate\n(phishing all users)", "group": 11, "level": 8,
     "tip": "Email phishing against ALL users with CSP management/system/support access including privileged admins. Must be allowlisted through all security systems. 3PAO provides/approves templates. 3PAO destroys harvested credentials after test. Alternate: run untrusted script for RCE proof."},
    {"id": "PT_AV2","label": "AV2: External→CSP System\n(all endpoints; WAF bypassed)", "group": 11, "level": 8,
     "tip": "Public internet attack against all external endpoints. All blocking security devices (WAF, software controls) bypassed for testing. IaaS: originate from internet against exterior IPs/VPNs/site-to-site. PaaS/SaaS: against exterior IPs and within application/database."},
    {"id": "PT_AV3","label": "AV3: Tenant→CSP Mgmt\n(highest perms; prod required)", "group": 11, "level": 8,
     "tip": "Full application test using highest-level customer permissions. Attempts access via misconfiguration, design flaws, abuse of intended function, low/no-code tools, CLI. Production environment required — dev/test not accepted."},
    {"id": "PT_AV4","label": "AV4: Tenant→Tenant\n(2 prod tenants required)", "group": 11, "level": 8,
     "tip": "Cross-tenant compromise. 3PAO must be provisioned with two full production customer tenants. Tests authentication, data access, user permissions, session management."},
    {"id": "PT_AV5","label": "AV5: Mobile App\n(N/A if no mobile)", "group": 11, "level": 8,
     "tip": "Mobile user attempting access to CSP target or management system. Emulated on representative mobile device. Mark N/A with SAR justification if no mobile application is part of the CSO."},
    {"id": "PT_AV6","label": "AV6: Client-side App\n(agents, thick clients)", "group": 11, "level": 8,
     "tip": "Client-side components (software apps, servers, appliances, browser extensions, thick clients, agents) essential for customer use. Controls the customer cannot remediate (encryption, SW development) must be in SSP and assessed by 3PAO."},

    # ---- Container Security ----
    {"id": "CT_IMG", "label": "Hardened Images\n(SP 800-70; no general-purpose\nimages in boundary)", "group": 12, "level": 7,
     "tip": "CSP must only use containers with hardened images per NIST SP 800-70 National Checklist Program benchmarks. General-purpose and non-hardened images prohibited within boundary. 3PAO validates against CM-6, SC-2, SC-3, SC-4, SC-6, SC-28, SC-39."},
    {"id": "CT_PIPE","label": "Automated Pipeline\n(build→test→deploy\nblock non-compliant)", "group": 12, "level": 7,
     "tip": "CSP must use automated orchestration tools to build, test, and deploy containers. Pipeline must include mechanism to block non-compliant containers from deploying. Left of production registry may reside outside authorization boundary. 3PAO validates against CA-2, CM-2, CM-3, SC-28, SI-3, SI-7."},
    {"id": "CT_REG", "label": "Production Container Registry\n(boundary demarcation point\n30-day scan clock starts here)", "group": 12, "level": 8,
     "tip": "The boundary demarcation line. Left of registry (dev/test/CI pipeline) may be outside authorization boundary. Registry and everything to the right is in-scope. 30-day scanning window clock starts when image deployed to production registry."},
    {"id": "CT_SENS","label": "Security Sensors\n(optional: enables vuln sampling)", "group": 12, "level": 8,
     "tip": "Optional independent sensors deployed alongside production containers. Must run with sufficient privileges. When used, may enable vulnerability scan sampling instead of 100% scanning."},
    {"id": "CT_INV", "label": "Image-Based Inventory\n(CM-8; unique ID per image class)", "group": 12, "level": 8,
     "tip": "Unique asset identifier per class of image. Tracked in FedRAMP Integrated Inventory Workbook. Individual container instances tracked internally; only in FedRAMP inventory if directly targeted by security sensor scan."},
]

EDGES = [
    # ---- Upstream Policy ----
    ("FISMA",    "OMB_A130",  "mandates",                  "#E65100", False),
    ("FISMA",    "OMB_MEMO",  "enables",                   "#E65100", False),
    ("OMB_A130", "FIPS_199",  "incorporates",              "#E65100", False),
    ("OMB_A130", "A_SSP",    "'federal information'\ndefinition", "#E65100", True),
    ("OMB_MEMO", "PMO",       "establishes FedRAMP mandate\n(agencies must use FedRAMP)", "#E65100", False),
    ("FIPS_199", "P_IMPACT",  "categorization template",   "#E65100", False),
    ("FIPS_140", "A_SSP",    "FIPS 140-validated\ncrypto required", "#E65100", True),

    # ---- NIST Standards → FedRAMP ----
    ("SP_800_37",  "PMO",      "FedRAMP implements RMF",   "#2E7D32", True),
    ("SP_800_53",  "B_LI",    "source catalog",            "#2E7D32", False),
    ("SP_800_53",  "B_LOW",   "source catalog",            "#2E7D32", False),
    ("SP_800_53",  "B_MOD",   "source catalog",            "#2E7D32", False),
    ("SP_800_53",  "B_HIGH",  "source catalog",            "#2E7D32", False),
    ("SP_800_53A", "A_SAP",   "assessment procedures",     "#2E7D32", True),
    ("SP_800_115", "PT_ROE",  "pen test methodology",      "#2E7D32", False),
    ("SP_800_61",  "CM_INCIDENT","IR lifecycle / 1-hr notify", "#2E7D32", False),
    ("SP_800_145", "A_FULL",  "SaaS/PaaS/IaaS taxonomy",  "#2E7D32", True),
    ("SP_800_190", "CT_PIPE", "container risk profile",    "#2E7D32", False),
    ("SP_800_190", "CT_IMG",  "container risk profile",    "#2E7D32", False),
    ("SP_800_70",  "CT_IMG",  "hardening benchmarks",      "#2E7D32", False),
    ("ATT_CK",     "PT_ROE",  "required attack model\n(14 enterprise tactics)", "#2E7D32", False),

    # ---- Baseline hierarchy ----
    ("B_LOW", "B_MOD",  "+167 controls",  "#F57F17", False),
    ("B_MOD", "B_HIGH", "+87 controls",   "#F57F17", False),

    # ---- Phase 1: Preparation ----
    ("CSP",       "P_CSP_FORM", "completes",                        "#1565C0", False),
    ("P_CSP_FORM","PMO",        "submits → generates FedRAMP ID",   "#1565C0", False),
    ("CSP",       "PAO3",       "hires (FedRAMP-recognized)",        "#1565C0", False),
    ("PAO3",      "P_RAR",      "produces RAR\n(readiness assessment)", "#1565C0", False),
    ("P_RAR",     "PMO",        "PMO reviews & approves",           "#1565C0", False),
    ("P_RAR",     "S_READY",    "achieves designation",             "#1565C0", False),
    ("S_READY",   "MARKETPLACE","posted to",                         "#6A1B9A", False),
    ("CSP",       "P_IMPACT",   "confirms with agency",             "#1565C0", False),
    ("AO",        "P_IMPACT",   "determines (FIPS 199 template)",   "#1565C0", False),
    ("P_IMPACT",  "B_LI",       "selects",                          "#1565C0", False),
    ("P_IMPACT",  "B_LOW",      "selects",                          "#1565C0", False),
    ("P_IMPACT",  "B_MOD",      "selects (most common)",            "#1565C0", False),
    ("P_IMPACT",  "B_HIGH",     "selects",                          "#1565C0", False),
    ("CSP",       "P_WBS_IPR",  "co-submits with agency",           "#1565C0", False),
    ("AO",        "P_WBS_IPR",  "co-submits with CSP",              "#1565C0", False),
    ("P_WBS_IPR", "PMO",        "→ intake@fedramp.gov",             "#1565C0", False),
    ("PMO",       "S_INPROC",   "grants In Process designation",    "#6A1B9A", False),
    ("S_INPROC",  "MARKETPLACE","posted to",                         "#6A1B9A", False),
    ("P_WBS_IPR", "P_KICKOFF",  "triggers",                         "#1565C0", False),
    ("CSP",       "P_KICKOFF",  "attends",                          "#1565C0", False),
    ("AO",        "P_KICKOFF",  "attends",                          "#1565C0", False),
    ("PAO3",      "P_KICKOFF",  "attends",                          "#1565C0", False),

    # ---- Phase 2: Authorization ----
    ("CSP",       "A_SSP",      "develops (FedRAMP template)",      "#00695C", False),
    ("B_LI",      "A_SSP",      "controls drive SSP content",       "#00695C", False),
    ("B_LOW",     "A_SSP",      "controls drive SSP content",       "#00695C", False),
    ("B_MOD",     "A_SSP",      "controls drive SSP content",       "#00695C", False),
    ("B_HIGH",    "A_SSP",      "controls drive SSP content",       "#00695C", False),
    ("PAO3",      "A_SAP",      "develops (FedRAMP template)",      "#00695C", False),
    ("AO",        "A_SAP",      "approves before testing begins",   "#00695C", False),
    ("A_SAP",     "A_FULL",     "governs scope",                    "#00695C", False),
    ("A_SSP",     "A_FULL",     "boundary + controls in scope",     "#00695C", False),
    ("PAO3",      "A_FULL",     "conducts (vuln scan + pen test)",  "#00695C", False),
    ("CSP",       "A_FULL",     "system frozen during testing",     "#00695C", False),
    ("A_FULL",    "PT_ROE",     "requires ROE (AO approves)",       "#00695C", False),
    ("PT_ROE",    "PT_AV1",     "scopes",                           "#558B2F", False),
    ("PT_ROE",    "PT_AV2",     "scopes",                           "#558B2F", False),
    ("PT_ROE",    "PT_AV3",     "scopes",                           "#558B2F", False),
    ("PT_ROE",    "PT_AV4",     "scopes",                           "#558B2F", False),
    ("PT_ROE",    "PT_AV5",     "scopes (N/A if no mobile)",        "#558B2F", False),
    ("PT_ROE",    "PT_AV6",     "scopes",                           "#558B2F", False),
    ("PT_AV1",    "A_SAR",      "results → embedded in SAR",        "#558B2F", False),
    ("PT_AV2",    "A_SAR",      "results → embedded in SAR",        "#558B2F", False),
    ("PT_AV3",    "A_SAR",      "results → embedded in SAR",        "#558B2F", False),
    ("PT_AV4",    "A_SAR",      "results → embedded in SAR",        "#558B2F", False),
    ("PT_AV5",    "A_SAR",      "results → embedded in SAR",        "#558B2F", False),
    ("PT_AV6",    "A_SAR",      "results → embedded in SAR",        "#558B2F", False),
    ("A_FULL",    "A_SAR",      "produces",                         "#00695C", False),
    ("A_SAR",     "A_POAM",     "CSP develops POA&M from findings", "#00695C", False),
    ("AO",        "A_SAR",      "reviews at SAR Debrief",           "#00695C", False),
    ("AO",        "A_SSP",      "reviews",                          "#00695C", False),
    ("AO",        "A_POAM",     "reviews",                          "#00695C", False),
    ("AO",        "A_ATO",      "issues when satisfied",            "#00695C", False),
    ("A_ATO",     "CSP",        "delivered to",                     "#00695C", False),
    ("A_ATO",     "PMO",        "→ ato-letter@fedramp.gov",         "#00695C", False),
    ("CSP",       "A_CHECKLIST","submits post-ATO",                  "#00695C", False),
    ("CSP",       "REPO_LM",   "uploads package (Low/Moderate)",    "#00695C", False),
    ("CSP",       "REPO_H",    "maintains own repo (High only)",    "#00695C", False),
    ("A_ATO",     "PMO",        "triggers PMO quality review",      "#00695C", False),
    ("A_CHECKLIST","PMO",       "enables PMO quality review",       "#00695C", False),
    ("PMO",       "S_AUTH",     "grants FedRAMP Authorized",        "#6A1B9A", False),
    ("S_AUTH",    "MARKETPLACE","posted to",                         "#6A1B9A", False),
    ("S_AUTH",    "REPO_LM",   "package available for reuse\n(all agencies)", "#6A1B9A", True),
    ("S_AUTH",    "AO",         "each agency issues own ATO\n(reuse model)", "#6A1B9A", True),

    # ---- Phase 3: Continuous Monitoring ----
    ("S_AUTH",    "CM_MONTHLY", "triggers ongoing ConMon obligation","#F9A825", False),
    ("CSP",       "CM_MONTHLY", "executes monthly",                  "#F9A825", False),
    ("CM_MONTHLY","REPO_LM",   "uploaded monthly",                   "#F9A825", False),
    ("AO",        "CM_MONTHLY", "reviews deliverables",              "#F9A825", False),
    ("ISSO",      "CM_MONTHLY", "monitors on behalf of AO",          "#F9A825", False),
    ("CM_MONTHLY","CM_VULN",   "includes",                           "#F9A825", False),
    ("CM_MONTHLY","CM_DEV_REQ","includes (if applicable)",           "#F9A825", False),
    ("CM_MONTHLY","CM_SIGCHG", "includes SCRs (if applicable)",      "#F9A825", False),
    ("CM_MONTHLY","CM_INCIDENT","triggers if incident occurs",       "#F9A825", False),
    ("PAO3",      "CM_ANNUAL",  "conducts annually (CA-2 + CA-8)",   "#F9A825", False),
    ("CM_ANNUAL", "A_SAR",      "updates SAR",                       "#F9A825", False),
    ("CM_ANNUAL", "A_POAM",     "updates POA&M",                     "#F9A825", False),
    ("CM_ANNUAL", "PT_ROE",     "annual pen test (CA-8)\nevery 12 months", "#F9A825", False),
    ("AO",        "CM_DEV_REQ", "approves RA / FP / OR",             "#F9A825", False),
    ("AO",        "CM_SIGCHG",  "approves Adaptive &\nTransformative SCRs", "#F9A825", False),
    ("PAO3",      "CM_SIGCHG",  "assesses Adaptive &\nTransformative SCRs", "#F9A825", False),
    ("S_AUTH",    "CM_COLLAB",  "required when >1 active ATO/ATU",   "#F9A825", True),
    ("CM_COLLAB", "AO",         "shared agency forum (CA-7)",         "#F9A825", False),
    ("CM_INCIDENT","CISA",      "notify within 1 hour\n(confirmed attack vector)", "#E65100", False),
    ("CM_INCIDENT","PMO",       "notify: fedramp_security@gsa.gov",   "#E65100", False),
    ("CM_INCIDENT","AO",        "notify POCs within 1 hour",          "#E65100", False),
    ("CISA",      "CSP",        "BODs/EDs: CSP must respond\nwithin specified timeline", "#E65100", True),

    # ---- Escalation ----
    ("CM_MONTHLY","ESC_SATISF", "passing ConMon",                    "#4CAF50", False),
    ("CM_MONTHLY","ESC_DFR",   "ConMon deficiency triggers DFR",     "#C62828", False),
    ("ESC_DFR",   "ESC_CAP",   "unresolved → escalates",            "#C62828", False),
    ("ESC_CAP",   "ESC_SUSP",  "failure → escalates",               "#C62828", False),
    ("ESC_SUSP",  "ESC_REVOKE","unresolved → escalates",            "#C62828", False),
    ("ESC_SUSP",  "PMO",        "AO notifies info@fedramp.gov",      "#C62828", False),
    ("ESC_REVOKE","PMO",        "AO notifies info@fedramp.gov",      "#C62828", False),
    ("ESC_REVOKE","MARKETPLACE","PMO updates Marketplace status",     "#C62828", False),

    # ---- Container ----
    ("CT_IMG",  "CT_PIPE",    "images enter pipeline",              "#006064", False),
    ("CT_PIPE", "CT_REG",     "delivers to registry\n(boundary line)", "#006064", False),
    ("CT_REG",  "CM_VULN",   "30-day scan clock\n(images must be scanned ≤30 days)", "#006064", False),
    ("CT_SENS", "CT_REG",    "monitors registry\n(enables sampling)", "#006064", False),
    ("CT_REG",  "CT_INV",    "inventory tracked from registry",      "#006064", False),
    ("CT_INV",  "CM_MONTHLY","feeds inventory report",               "#006064", False),
    ("PAO3",    "CT_IMG",    "validates: CM-6, SC-2/3/4",            "#006064", False),
    ("PAO3",    "CT_PIPE",   "validates: CA-2, CM-2/3",              "#006064", False),
]


# ============================================================
# GENERATE DOT FILE
# ============================================================

def group_dot_attrs(g):
    """Return fillcolor and shape defaults for DOT by group."""
    attrs = {
        0:  ('filled', '#FFE082', 'box'),
        1:  ('filled,bold', '#81C784', 'box'),
        2:  ('filled', '#C8E6C9', 'box'),
        3:  ('filled', '#90CAF9', 'ellipse'),
        4:  ('filled', '#FFCC80', 'box'),
        5:  ('filled', '#F48FB1', 'cylinder'),
        6:  ('filled', '#CE93D8', 'diamond'),
        7:  ('filled', '#C5CAE9', 'box'),
        8:  ('filled', '#B2DFDB', 'box'),
        9:  ('filled', '#FFF176', 'box'),
        10: ('filled', '#FFCDD2', 'box'),
        11: ('filled', '#DCEDC8', 'box'),
        12: ('filled', '#B2EBF2', 'box'),
    }
    return attrs.get(g, ('filled', '#EEEEEE', 'box'))

CLUSTER_LABELS = {
    0: 'Upstream Policy & Statute  (* = NOT in local KB)',
    1: 'NIST Standards — IN local KB',
    2: 'NIST Standards — NOT in local KB (*)',
    3: 'Actors',
    4: 'FedRAMP Baselines (from NIST SP 800-53r5)',
    5: 'FedRAMP Program Infrastructure',
    6: 'CSO Authorization States',
    7: 'Phase 1: Preparation',
    8: 'Phase 2: Authorization',
    9: 'Phase 3: Continuous Monitoring (ConMon)',
    10: 'ConMon Escalation Path',
    11: 'Penetration Testing (mandatory attack vectors)',
    12: 'Container Security (supplemental ConMon)',
}

CLUSTER_COLORS = {
    0: '#F57C00', 1: '#388E3C', 2: '#2E7D32', 3: '#1565C0',
    4: '#E65100', 5: '#880E4F', 6: '#6A1B9A', 7: '#283593',
    8: '#00695C', 9: '#F9A825', 10: '#C62828', 11: '#558B2F', 12: '#006064',
}

CLUSTER_BG = {
    0: '#FFF8E1', 1: '#E8F5E9', 2: '#F1F8E9', 3: '#E3F2FD',
    4: '#FFF3E0', 5: '#FCE4EC', 6: '#F3E5F5', 7: '#E8EAF6',
    8: '#E0F2F1', 9: '#FFFDE7', 10: '#FFEBEE', 11: '#F9FBE7', 12: '#E0F7FA',
}

def generate_dot(nodes, edges):
    from collections import defaultdict
    by_group = defaultdict(list)
    for n in nodes:
        by_group[n['group']].append(n)

    lines = []
    lines.append('digraph FedRAMP_Interdependencies {')
    lines.append('    graph [')
    lines.append('        rankdir=TB')
    lines.append('        fontname="Helvetica Neue"')
    lines.append('        fontsize=10')
    lines.append('        compound=true')
    lines.append('        nodesep=0.4')
    lines.append('        ranksep=0.6')
    lines.append('        splines=curved')
    lines.append('        bgcolor="#F5F5F5"')
    lines.append('        label="FedRAMP Interdependency Map  |  Rev5, Nov 2025–Apr 2026\\n'
                 'Source: CSP/Agency Playbooks, ConMon Playbook, Pen Test Guidance, Baselines, Boundary Guidance\\n'
                 'Nodes marked * are referenced but NOT in local knowledgebase"')
    lines.append('        labelloc=t')
    lines.append('        labeljust=c')
    lines.append('    ]')
    lines.append('    node [fontname="Helvetica Neue" fontsize=8 margin="0.12,0.06"]')
    lines.append('    edge [fontname="Helvetica Neue" fontsize=7]')
    lines.append('')

    for g in sorted(by_group.keys()):
        group_nodes = by_group[g]
        color = CLUSTER_COLORS.get(g, '#555555')
        bg = CLUSTER_BG.get(g, '#FAFAFA')
        label = CLUSTER_LABELS.get(g, f'Group {g}')
        lines.append(f'    subgraph cluster_{g} {{')
        lines.append(f'        label="{label}"')
        lines.append(f'        style=filled')
        lines.append(f'        fillcolor="{bg}"')
        lines.append(f'        color="{color}"')
        lines.append(f'        penwidth=2')
        lines.append(f'        fontname="Helvetica Neue"')
        lines.append(f'        fontsize=9')
        for n in group_nodes:
            style, fill, shape = group_dot_attrs(n['group'])
            escaped_label = n['label'].replace('\n', '\\n')
            escaped_tip = n['tip'].replace('"', '\\"').replace('\n', ' ')
            lines.append(f'        {n["id"]} [label="{escaped_label}" shape={shape} style="{style}" fillcolor="{fill}" tooltip="{escaped_tip}"]')
        lines.append('    }')
        lines.append('')

    lines.append('    // Edges')
    for (src, dst, lbl, color, dashed) in edges:
        escaped_lbl = lbl.replace('\n', '\\n')
        style = 'dashed' if dashed else 'solid'
        lines.append(f'    {src} -> {dst} [label="{escaped_lbl}" color="{color}" style={style}]')

    lines.append('}')
    return '\n'.join(lines)


# ============================================================
# GENERATE HTML (vis.js)
# ============================================================

GROUP_COLORS = {
    0:  {'background': '#FFE082', 'border': '#F57C00', 'highlight': {'background': '#FFCA28', 'border': '#E65100'}, 'font': {'color': '#4E342E'}},
    1:  {'background': '#81C784', 'border': '#388E3C', 'highlight': {'background': '#66BB6A', 'border': '#2E7D32'}, 'font': {'color': '#1B5E20'}},
    2:  {'background': '#C8E6C9', 'border': '#2E7D32', 'highlight': {'background': '#A5D6A7', 'border': '#1B5E20'}, 'font': {'color': '#1B5E20'}},
    3:  {'background': '#90CAF9', 'border': '#1565C0', 'highlight': {'background': '#64B5F6', 'border': '#0D47A1'}, 'font': {'color': '#0D47A1'}},
    4:  {'background': '#FFCC80', 'border': '#E65100', 'highlight': {'background': '#FFA726', 'border': '#BF360C'}, 'font': {'color': '#4E342E'}},
    5:  {'background': '#F48FB1', 'border': '#880E4F', 'highlight': {'background': '#F06292', 'border': '#6A1B9A'}, 'font': {'color': '#4A148C'}},
    6:  {'background': '#CE93D8', 'border': '#6A1B9A', 'highlight': {'background': '#AB47BC', 'border': '#4A148C'}, 'font': {'color': '#4A148C'}},
    7:  {'background': '#C5CAE9', 'border': '#283593', 'highlight': {'background': '#9FA8DA', 'border': '#1A237E'}, 'font': {'color': '#1A237E'}},
    8:  {'background': '#B2DFDB', 'border': '#00695C', 'highlight': {'background': '#80CBC4', 'border': '#004D40'}, 'font': {'color': '#004D40'}},
    9:  {'background': '#FFF176', 'border': '#F9A825', 'highlight': {'background': '#FFEE58', 'border': '#F57F17'}, 'font': {'color': '#4E342E'}},
    10: {'background': '#FFCDD2', 'border': '#C62828', 'highlight': {'background': '#EF9A9A', 'border': '#B71C1C'}, 'font': {'color': '#B71C1C'}},
    11: {'background': '#DCEDC8', 'border': '#558B2F', 'highlight': {'background': '#C5E1A5', 'border': '#33691E'}, 'font': {'color': '#33691E'}},
    12: {'background': '#B2EBF2', 'border': '#006064', 'highlight': {'background': '#80DEEA', 'border': '#004D40'}, 'font': {'color': '#006064'}},
}

NODE_SHAPES = {
    3: 'ellipse',
    5: 'database',
    6: 'diamond',
}

def generate_html(nodes, edges):
    import json

    vis_nodes = []
    for n in nodes:
        gc = GROUP_COLORS.get(n['group'], {})
        shape = NODE_SHAPES.get(n['group'], 'box')
        vis_nodes.append({
            "id": n["id"],
            "label": n["label"],
            "title": n["tip"],
            "group": n["group"],
            "level": n["level"],
            "shape": shape,
            "color": gc,
            "font": {"face": "Arial", "size": 11, **gc.get("font", {})},
            "margin": 10,
            "widthConstraint": {"minimum": 120, "maximum": 200},
        })

    vis_edges = []
    for i, (src, dst, lbl, color, dashed) in enumerate(edges):
        e = {
            "id": i,
            "from": src,
            "to": dst,
            "label": lbl,
            "color": {"color": color, "highlight": color, "hover": color},
            "font": {"size": 9, "color": "#333333", "align": "middle"},
            "arrows": {"to": {"enabled": True, "scaleFactor": 0.7}},
            "smooth": {"type": "curvedCW", "roundness": 0.1},
        }
        if dashed:
            e["dashes"] = True
        vis_edges.append(e)

    nodes_json = json.dumps(vis_nodes, indent=2)
    edges_json = json.dumps(vis_edges, indent=2)

    legend_items = [
        (GROUP_COLORS[0]['background'], GROUP_COLORS[0]['border'], "Upstream Policy / Statute (* = not in local KB)"),
        (GROUP_COLORS[1]['background'], GROUP_COLORS[1]['border'], "NIST Standards — IN local KB"),
        (GROUP_COLORS[2]['background'], GROUP_COLORS[2]['border'], "NIST Standards — NOT in local KB (*)"),
        (GROUP_COLORS[3]['background'], GROUP_COLORS[3]['border'], "Actors (CSP, AO, 3PAO, PMO, CISA, ISSO)"),
        (GROUP_COLORS[4]['background'], GROUP_COLORS[4]['border'], "FedRAMP Baselines (Low/Moderate/High/LI-SaaS)"),
        (GROUP_COLORS[5]['background'], GROUP_COLORS[5]['border'], "FedRAMP Program Infrastructure"),
        (GROUP_COLORS[6]['background'], GROUP_COLORS[6]['border'], "CSO Authorization States"),
        (GROUP_COLORS[7]['background'], GROUP_COLORS[7]['border'], "Phase 1: Preparation"),
        (GROUP_COLORS[8]['background'], GROUP_COLORS[8]['border'], "Phase 2: Authorization"),
        (GROUP_COLORS[9]['background'], GROUP_COLORS[9]['border'], "Phase 3: Continuous Monitoring"),
        (GROUP_COLORS[10]['background'], GROUP_COLORS[10]['border'], "ConMon Escalation Path"),
        (GROUP_COLORS[11]['background'], GROUP_COLORS[11]['border'], "Penetration Testing (AV1–AV6)"),
        (GROUP_COLORS[12]['background'], GROUP_COLORS[12]['border'], "Container Security"),
    ]
    legend_html = ''.join(
        f'<div class="legend-item"><span class="legend-swatch" style="background:{bg};border-color:{bd}"></span>{txt}</div>'
        for bg, bd, txt in legend_items
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FedRAMP Interdependency Map — Rev5 2025–2026</title>
<script src="https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js"></script>
<link href="https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.css" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: Arial, sans-serif; background: #F5F5F5; }}
  #header {{
    background: #1A237E; color: white; padding: 12px 20px;
    display: flex; align-items: center; justify-content: space-between;
  }}
  #header h1 {{ font-size: 16px; font-weight: bold; }}
  #header p {{ font-size: 11px; opacity: 0.8; margin-top: 2px; }}
  #controls {{
    background: #E8EAF6; border-bottom: 1px solid #C5CAE9;
    padding: 8px 16px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap;
  }}
  #controls label {{ font-size: 12px; color: #283593; font-weight: bold; }}
  #controls input, #controls select {{
    font-size: 12px; padding: 4px 8px; border: 1px solid #9FA8DA;
    border-radius: 4px; background: white;
  }}
  #controls button {{
    font-size: 12px; padding: 4px 10px; border: none; border-radius: 4px;
    cursor: pointer; background: #3949AB; color: white;
  }}
  #controls button:hover {{ background: #283593; }}
  #main {{ display: flex; height: calc(100vh - 100px); }}
  #network {{ flex: 1; }}
  #sidebar {{
    width: 280px; background: white; border-left: 1px solid #E0E0E0;
    display: flex; flex-direction: column; overflow: hidden;
  }}
  #sidebar h2 {{ font-size: 13px; padding: 10px 12px; background: #E8EAF6; color: #283593; border-bottom: 1px solid #C5CAE9; }}
  #legend {{ padding: 8px 12px; overflow-y: auto; flex: 1; }}
  .legend-item {{ display: flex; align-items: center; margin-bottom: 6px; font-size: 11px; color: #333; }}
  .legend-swatch {{
    width: 16px; height: 16px; border-radius: 3px; border: 2px solid; flex-shrink: 0;
    margin-right: 8px;
  }}
  #info-panel {{
    border-top: 1px solid #E0E0E0; padding: 10px 12px;
    background: #FAFAFA; font-size: 11px; min-height: 80px; max-height: 180px; overflow-y: auto;
  }}
  #info-panel h3 {{ color: #283593; font-size: 12px; margin-bottom: 4px; }}
  #info-panel p {{ color: #555; line-height: 1.4; }}
  #tooltip-hint {{ color: #888; font-style: italic; }}
</style>
</head>
<body>
<div id="header">
  <div>
    <h1>FedRAMP Interdependency Map</h1>
    <p>Rev5 &nbsp;|&nbsp; Sources: CSP/Agency Playbooks v4.1–4.2, ConMon Playbook v1.0, Pen Test Guidance v3, Security Controls Baseline (Apr 2026), Boundary Guidance &nbsp;|&nbsp; Nodes marked * are referenced but not in local KB</p>
  </div>
</div>
<div id="controls">
  <label>Search node:</label>
  <input type="text" id="search" placeholder="Type node name..." style="width:180px">
  <button onclick="doSearch()">Find</button>
  <label>Layout:</label>
  <select id="layout-select" onchange="changeLayout()">
    <option value="hierarchical">Hierarchical (UD)</option>
    <option value="physics">Physics / Force-directed</option>
  </select>
  <button onclick="network.fit()">Fit All</button>
  <button onclick="resetHighlight()">Clear Highlight</button>
  <span style="font-size:11px;color:#555;margin-left:8px">Scroll to zoom &bull; Drag to pan &bull; Click node for details</span>
</div>
<div id="main">
  <div id="network"></div>
  <div id="sidebar">
    <h2>Legend — Node Groups</h2>
    <div id="legend">{legend_html}</div>
    <div id="info-panel">
      <p id="tooltip-hint">Click a node to see its description here.</p>
    </div>
  </div>
</div>
<script>
const nodesData = {nodes_json};
const edgesData = {edges_json};

const container = document.getElementById('network');
const nodes = new vis.DataSet(nodesData);
const edges = new vis.DataSet(edgesData);
const data = {{ nodes, edges }};

const hierarchicalOptions = {{
  layout: {{
    hierarchical: {{
      enabled: true,
      direction: 'UD',
      sortMethod: 'directed',
      levelSeparation: 130,
      nodeSpacing: 150,
      treeSpacing: 200,
      blockShifting: true,
      edgeMinimization: true,
      parentCentralization: true,
    }}
  }},
  physics: {{ enabled: false }},
  interaction: {{
    hover: true,
    tooltipDelay: 150,
    zoomView: true,
    dragView: true,
    multiselect: false,
  }},
  edges: {{
    smooth: {{ type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.4 }},
    font: {{ size: 9, align: 'middle', strokeWidth: 2, strokeColor: '#FFFFFF' }},
    width: 1.5,
    selectionWidth: 3,
  }},
  nodes: {{
    borderWidth: 2,
    borderWidthSelected: 4,
    shadow: {{ enabled: true, size: 5, x: 2, y: 2, color: 'rgba(0,0,0,0.12)' }},
  }},
}};

const physicsOptions = {{
  layout: {{ hierarchical: {{ enabled: false }} }},
  physics: {{
    enabled: true,
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {{ gravitationalConstant: -80, springLength: 150, springConstant: 0.04 }},
    stabilization: {{ iterations: 200 }},
  }},
  interaction: {{ hover: true, tooltipDelay: 150, zoomView: true, dragView: true }},
  edges: {{
    smooth: {{ type: 'dynamic' }},
    font: {{ size: 9, align: 'middle', strokeWidth: 2, strokeColor: '#FFFFFF' }},
    width: 1.5,
  }},
  nodes: {{
    borderWidth: 2,
    shadow: {{ enabled: true, size: 5, x: 2, y: 2, color: 'rgba(0,0,0,0.12)' }},
  }},
}};

const network = new vis.Network(container, data, hierarchicalOptions);

network.on('click', function(params) {{
  const infoPanel = document.getElementById('info-panel');
  if (params.nodes.length > 0) {{
    const nodeId = params.nodes[0];
    const node = nodes.get(nodeId);
    infoPanel.innerHTML = '<h3>' + node.label.replace(/\\n/g, ' ') + '</h3><p>' + (node.title || 'No description.') + '</p>';
    // Highlight neighbors
    const connectedEdges = network.getConnectedEdges(nodeId);
    const connectedNodes = network.getConnectedNodes(nodeId);
    nodes.update(nodesData.map(n => ({{
      id: n.id,
      opacity: (n.id === nodeId || connectedNodes.includes(n.id)) ? 1.0 : 0.25
    }})));
    edges.update(edgesData.map(e => ({{
      id: e.id,
      opacity: connectedEdges.includes(e.id) ? 1.0 : 0.1
    }})));
  }} else {{
    resetHighlight();
  }}
}});

function resetHighlight() {{
  nodes.update(nodesData.map(n => ({{ id: n.id, opacity: 1.0 }})));
  edges.update(edgesData.map(e => ({{ id: e.id, opacity: 1.0 }})));
  document.getElementById('info-panel').innerHTML = '<p id="tooltip-hint">Click a node to see its description here.</p>';
}}

function doSearch() {{
  const q = document.getElementById('search').value.toLowerCase().trim();
  if (!q) {{ resetHighlight(); return; }}
  const matched = nodesData.filter(n => n.label.toLowerCase().includes(q) || (n.title||'').toLowerCase().includes(q));
  if (matched.length === 0) {{ alert('No matching nodes found.'); return; }}
  const matchIds = matched.map(n => n.id);
  nodes.update(nodesData.map(n => ({{ id: n.id, opacity: matchIds.includes(n.id) ? 1.0 : 0.2 }})));
  if (matched.length === 1) network.focus(matched[0].id, {{ scale: 1.5, animation: true }});
  else network.fit({{ nodes: matchIds, animation: true }});
}}

function changeLayout() {{
  const v = document.getElementById('layout-select').value;
  if (v === 'hierarchical') network.setOptions(hierarchicalOptions);
  else network.setOptions(physicsOptions);
}}

document.getElementById('search').addEventListener('keydown', e => {{ if (e.key === 'Enter') doSearch(); }});
</script>
</body>
</html>"""
    return html


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    import os
    import argparse
    parser = argparse.ArgumentParser(description="Generate FedRAMP interdependency diagram.")
    parser.add_argument("--output-dir", default=None,
                        help="Directory for output files (default: current working directory)")
    args = parser.parse_args()
    out_dir = os.path.abspath(args.output_dir) if args.output_dir else os.getcwd()
    os.makedirs(out_dir, exist_ok=True)

    dot_path = os.path.join(out_dir, 'fedramp_diagram.dot')
    html_path = os.path.join(out_dir, 'fedramp_diagram.html')

    dot_src = generate_dot(NODES, EDGES)
    with open(dot_path, 'w', encoding='utf-8') as f:
        f.write(dot_src)
    print(f"Written: {dot_path}")

    html_src = generate_html(NODES, EDGES)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_src)
    print(f"Written: {html_path}")

    print(f"\nSummary: {len(NODES)} nodes, {len(EDGES)} edges")
    print("To view: open fedramp_diagram.html in any browser")
    print("To render DOT: dot -Tpdf fedramp_diagram.dot -o fedramp_diagram.pdf")
    print("              (requires Graphviz — install from graphviz.org)")
